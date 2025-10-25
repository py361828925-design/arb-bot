import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException

# 让 Python 能导入项目根目录下的 libs.*
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from libs.bus import FundingPublisher
from libs.config import get_settings
from libs.models.funding import FundingSnapshot

logger = logging.getLogger("market_feed")
logging.basicConfig(level=logging.INFO)

BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"
BITGET_CONTRACTS_URLS = [
    "https://api.bitget.com/api/v2/mix/market/contracts",
    "https://api.bitget.com/api/mix/v1/market/contracts",
]
BITGET_FUNDING_ENDPOINTS = [
    # (url, include_margin_coin_param)
    ("https://api.bitget.com/api/v2/mix/market/current-fund-rate", True),
    ("https://api.bitget.com/api/mix/v1/market/currentFundRate", False),
]


class FundingFeed:
    """定时抓取资金费率并推送到消息总线。"""

    def __init__(self, *, settings, publisher: FundingPublisher) -> None:
        self._settings = settings
        self._publisher = publisher
        self._client: Optional[httpx.AsyncClient] = None
        self._task: Optional[asyncio.Task] = None
        self._latest: Dict[str, List[FundingSnapshot]] = {
            "binance": [],
            "bitget": [],
        }
        self._interval = getattr(settings, "funding_refresh_interval_secs", 30)
        self._timeout = getattr(settings, "http_timeout_secs", 10)
        self._bitget_symbol_limit = getattr(settings, "bitget_symbol_limit", None)
        self._bitget_concurrency = getattr(settings, "bitget_concurrency", 5)

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        if self._task is None:
            self._task = asyncio.create_task(self._loop())
            logger.info("Funding feed loop started (interval=%ss)", self._interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Funding feed loop stopped")

    async def latest(self, exchange: str) -> List[FundingSnapshot]:
        return self._latest.get(exchange, [])

    async def _loop(self) -> None:
        while True:
            try:
                await self._refresh()
            except Exception as exc:
                logger.exception("refresh funding snapshot failed: %s", exc)
            await asyncio.sleep(self._interval)

    async def _refresh(self) -> None:
        binance = await self._fetch_binance()
        bitget = await self._fetch_bitget()
        if binance:
            self._latest["binance"] = binance
            await self._emit(binance)
        if bitget:
            self._latest["bitget"] = bitget
            await self._emit(bitget)

    async def _emit(self, snapshots: List[FundingSnapshot]) -> None:
        if not snapshots:
            return
        if hasattr(self._publisher, "publish_many"):
            await self._publisher.publish_many(snapshots)
        else:
            for snapshot in snapshots:
                await self._publisher.publish(snapshot)

    async def _fetch_binance(self) -> List[FundingSnapshot]:
        assert self._client is not None
        resp = await self._client.get(BINANCE_FUNDING_URL)
        resp.raise_for_status()
        payload = resp.json()

        snapshots: List[FundingSnapshot] = []
        for item in payload:
            try:
                snapshots.append(FundingSnapshot.from_binance(item))
            except Exception as exc:
                logger.warning(
                    "skip binance item %s because %s", item.get("symbol"), exc
                )
        logger.info("Fetched %d binance funding entries", len(snapshots))
        return snapshots

    async def _fetch_bitget(self) -> List[FundingSnapshot]:
        assert self._client is not None
        product_type_conf = getattr(self._settings, "bitget_product_type", "USDT-FUTURES")
        product_type_upper = product_type_conf.upper()

        contracts: List[dict] = []
        contract_margin: Dict[str, str] = {}

        for url in BITGET_CONTRACTS_URLS:
            try:
                resp = await self._client.get(url, params={"productType": product_type_upper})
                resp.raise_for_status()
                payload = resp.json()
                data = payload.get("data") or []
                if isinstance(data, dict):
                    data = data.get("symbols") or []
                if not isinstance(data, list):
                    data = []
                contracts = data
                logger.info("Fetched %d bitget contracts via %s", len(contracts), url)

                for contract in contracts:
                    if isinstance(contract, dict):
                        sym = contract.get("symbol")
                        margin_coin = contract.get("marginCoin") or contract.get("quoteCoin")
                        if sym and margin_coin:
                            contract_margin[sym] = margin_coin
                logger.info("Bitget margin sample: %s", list(contract_margin.items())[:5])

                break

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (400, 404):
                    logger.warning(
                        "Bitget contract endpoint %s unavailable (status %s)",
                        url,
                        exc.response.status_code,
                    )
                    continue
                raise
            except Exception as exc:
                logger.warning("Fetch bitget contracts failed (%s): %s", url, exc)
                continue

        if not contracts:
            return []

        if self._bitget_symbol_limit:
            contracts = contracts[: self._bitget_symbol_limit]

        snapshots: List[FundingSnapshot] = []
        semaphore = asyncio.Semaphore(max(1, int(self._bitget_concurrency)))

        async def fetch_one(contract_symbol: str) -> Optional[FundingSnapshot]:
            async with semaphore:
                params_base = {
                    "symbol": contract_symbol.split("_", 1)[0],
                    "productType": product_type_upper,
                    "marginCoin": contract_margin.get(contract_symbol, "USDT"),
                }

                for url, with_margin in BITGET_FUNDING_ENDPOINTS:
                    params = dict(params_base)
                    if not with_margin:
                        params.pop("marginCoin", None)
                    try:
                        resp = await self._client.get(url, params=params)
                        resp.raise_for_status()
                    except Exception as exc:
                        logger.debug("bitget funding request failed via %s: %s", url, exc)
                        continue

                    payload = resp.json()
                    data = payload.get("data")
                    if not data:
                        continue
                    if isinstance(data, dict):
                        # v1 接口返回 dict，资金费率位于 data["data"][0]
                        if "data" in data and isinstance(data["data"], list):
                            records = data["data"]
                        elif "list" in data and isinstance(data["list"], list):
                            records = data["list"]
                        else:
                            records = [data]
                    else:
                        records = data if isinstance(data, list) else []

                    if not records:
                        continue

                    snapshot_raw = dict(records[0])
                    snapshot_raw.setdefault("symbol", contract_symbol)
                    try:
                        return self._make_bitget_snapshot(snapshot_raw)
                    except Exception as exc:
                        logger.debug("normalize bitget funding failed (%s): %s", contract_symbol, exc)
                        return None

                return None

        tasks = []
        for contract in contracts:
            symbol = contract.get("symbol") if isinstance(contract, dict) else contract
            if not symbol:
                continue
            tasks.append(asyncio.create_task(fetch_one(symbol)))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=False)
        for snapshot in results:
            if snapshot:
                snapshots.append(snapshot)

        logger.info("Fetched %d bitget funding entries", len(snapshots))
        return snapshots

    @staticmethod
    def _normalize_bitget_symbol(symbol: str) -> str:
        if not symbol:
            return symbol
        if symbol.endswith("_UMCBL") or symbol.endswith("_DMCBL"):
            return symbol.split("_", 1)[0]
        return symbol

    @staticmethod
    def _make_bitget_snapshot(item: dict) -> FundingSnapshot:
        raw_rate = float(item.get("fundingRate", 0.0))
        settle_hours = float(item.get("fundingRateInterval", 8))
        next_time_ms = int(item.get("nextUpdate") or 0)

        symbol = item.get("symbol", "")
        normalized_symbol = FundingFeed._normalize_bitget_symbol(symbol)

        return FundingSnapshot(
            exchange="bitget",
            symbol=normalized_symbol,
            funding_rate_raw=raw_rate,
            settle_interval_hours=settle_hours,
            next_funding_time_ms=next_time_ms,
        )

    @staticmethod
    def _parse_interval(value: Optional[str]) -> int:
        if not value:
            return 8
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        return int(digits) if digits else 8


app = FastAPI(title="Funding Feed Service", version="0.1.0")
_state: Dict[str, Optional[FundingFeed]] = {"feed": None}


@asynccontextmanager
async def lifespan(app_: FastAPI):
    settings = get_settings()
    publisher = FundingPublisher(settings=settings)
    feed = FundingFeed(settings=settings, publisher=publisher)

    if hasattr(publisher, "connect"):
        await publisher.connect()
    _state["feed"] = feed
    await feed.start()

    try:
        yield
    finally:
        if _state["feed"]:
            await _state["feed"].stop()
        _state["feed"] = None
        if hasattr(publisher, "close"):
            await publisher.close()


app.router.lifespan_context = lifespan


@app.get("/healthz")
async def healthz():
    feed = _state["feed"]
    if not feed:
        raise HTTPException(status_code=503, detail="feed not ready")
    binance = len(await feed.latest("binance"))
    bitget = len(await feed.latest("bitget"))
    return {"status": "ok", "binance": binance, "bitget": bitget}


@app.get("/funding/{exchange}")
async def read_funding(exchange: str):
    feed = _state["feed"]
    if not feed:
        raise HTTPException(status_code=503, detail="feed not ready")
    exchange = exchange.lower()
    if exchange not in {"binance", "bitget"}:
        raise HTTPException(status_code=404, detail="unsupported exchange")
    snapshots = await feed.latest(exchange)
    return [snapshot.model_dump() for snapshot in snapshots]
