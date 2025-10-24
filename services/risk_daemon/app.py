import asyncio
import contextlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import FastAPI
from redis.asyncio import Redis

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from libs.bus import ConfigSubscriber
from libs.config import get_settings
from libs.db.session import AsyncSessionLocal
from libs.models import FundingSnapshot
from libs.runtime_config import apply_update, get_runtime_config, load_initial
from services.risk_daemon import repo, schemas

logger = logging.getLogger("risk-daemon")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI()
settings = get_settings()

redis_client: Optional[Redis] = None
config_subscriber: Optional[ConfigSubscriber] = None
config_task: Optional[asyncio.Task] = None

CHECK_INTERVAL_SECONDS = 10.0
FUNDING_STREAM = "funding_snapshots"


async def get_latest_snapshot(exchange: str, symbol: str) -> Optional[FundingSnapshot]:
    if not redis_client:
        return None
    entries = await redis_client.xrevrange(FUNDING_STREAM, "+", "-", count=200)
    for _, fields in entries:
        if fields.get("exchange") == exchange and fields.get("symbol") == symbol:
            try:
                return FundingSnapshot.from_stream(fields)
            except Exception as exc:  # pragma: no cover
                logger.warning("parse snapshot failed %s/%s: %s", exchange, symbol, exc)
                continue
    return None


async def evaluate_group(group, now: datetime) -> Optional[Tuple[schemas.CloseDecision, Dict[str, float]]]:
    cfg = get_runtime_config()
    thresholds = cfg.thresholds

    if not group.legs:
        return None

    long_leg = next((leg for leg in group.legs if leg.side.upper() == "LONG"), None)
    short_leg = next((leg for leg in group.legs if leg.side.upper() == "SHORT"), None)
    if not long_leg or not short_leg:
        return None

    long_snapshot = await get_latest_snapshot(long_leg.exchange, group.symbol)
    short_snapshot = await get_latest_snapshot(short_leg.exchange, group.symbol)
    if not long_snapshot or not short_snapshot:
        return None

    long_mark = long_snapshot.mark_price or long_snapshot.index_price
    short_mark = short_snapshot.mark_price or short_snapshot.index_price
    if long_mark is None or short_mark is None:
        return None

    long_entry = long_leg.entry_price or 1.0
    short_entry = short_leg.entry_price or 1.0

    long_return = (long_mark - long_entry) / long_entry
    short_return = (short_entry - short_mark) / short_entry
    total_return = long_return + short_return
    worst_return = min(long_return, short_return)

    current_diff = long_snapshot.rate8h - short_snapshot.rate8h
    diff_reversed = group.funding_diff * current_diff < 0
    countdown_secs = min(long_snapshot.settle_countdown_secs, short_snapshot.settle_countdown_secs)
    countdown_minutes = countdown_secs / 60

    reason = None
    if long_return <= -0.9 or short_return <= -0.9:
        reason = "logic5"
    elif total_return <= -thresholds.gg:
        reason = "logic4"
    elif total_return >= thresholds.ff:
        reason = "logic3"
    elif worst_return <= -thresholds.hh and total_return >= thresholds.ee:
        reason = "logic2"
    else:
        diff_ok = abs(current_diff) <= thresholds.bb
        if ((diff_ok or diff_reversed) and total_return >= thresholds.cc) or (
            countdown_minutes <= thresholds.dd and diff_ok
        ):
            reason = "logic1"

    if not reason:
        return None

    notes = (
        f"long={long_return:.6f}, short={short_return:.6f}, total={total_return:.6f}, "
        f"diff={current_diff:.6f}, countdown={countdown_minutes:.2f}m"
    )
    decision = schemas.CloseDecision(
        group_id=group.group_id,
        symbol=group.symbol,
        reason=reason,
        triggered_at=now,
        notes=notes,
    )
    close_prices = {
        long_leg.exchange: long_mark,
        short_leg.exchange: short_mark,
        "__current_diff__": current_diff,
    }
    return decision, close_prices


async def risk_loop():
    logger.info("Risk loop started, interval %.1fs", CHECK_INTERVAL_SECONDS)
    while True:
        now = datetime.now(timezone.utc)
        cfg = get_runtime_config()
        if not cfg.global_enable:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            continue

        async with AsyncSessionLocal() as session:
            groups = await repo.fetch_open_groups(session)
            for group in groups:
                result = await evaluate_group(group, now)
                if not result:
                    continue
                decision, close_prices = result
                await repo.close_group(session, group, decision.reason, close_prices)
                logger.info(
                    "Closed group %s (%s) reason=%s notes=%s",
                    decision.group_id,
                    decision.symbol,
                    decision.reason,
                    decision.notes,
                )
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _config_listener():
    subscriber = ConfigSubscriber(settings.redis_url)
    await subscriber.start(apply_update)
    return subscriber


@app.on_event("startup")
async def on_startup():
    global redis_client, config_subscriber, config_task
    await load_initial()
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    config_task = asyncio.create_task(_config_listener())
    asyncio.create_task(risk_loop())


@app.on_event("shutdown")
async def on_shutdown():
    global redis_client, config_subscriber, config_task
    if config_task:
        config_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await config_task
    if config_subscriber:
        await config_subscriber.stop()
    if redis_client:
        await redis_client.close()
