import asyncio
import contextlib
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI
from redis.asyncio import Redis

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from libs.bus import ConfigSubscriber
from libs.config import get_settings
from libs.db.session import AsyncSessionLocal
from libs.models import FundingSnapshot, Opportunity
from libs.runtime_config import apply_update, get_runtime_config, load_initial
from services.execution_gateway import repo

logger = logging.getLogger("execution-gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI()
settings = get_settings()

redis_client: Optional[Redis] = None
config_subscriber: Optional[ConfigSubscriber] = None
config_task: Optional[asyncio.Task] = None

STREAM_KEY = "funding_opportunities"
GROUP_NAME = "execution_gateway"
FUNDING_STREAM = "funding_snapshots"


def _entry_price(snapshot: Optional[FundingSnapshot]) -> float:
    if snapshot:
        if snapshot.mark_price is not None:
            return snapshot.mark_price
        if snapshot.index_price is not None:
            return snapshot.index_price
    return 1.0


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


async def ensure_consumer_group(client: Redis):
    try:
        await client.xgroup_create(STREAM_KEY, GROUP_NAME, id="0-0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def handle_opportunity(fields: Dict[str, str]) -> bool:
    opportunity = Opportunity.from_stream(fields)
    config = get_runtime_config()
    if not config.global_enable:
        logger.info("Global switch off, skip %s", opportunity.group_id)
        return True

    long_snapshot = await get_latest_snapshot(opportunity.long_exchange, opportunity.symbol)
    short_snapshot = await get_latest_snapshot(opportunity.short_exchange, opportunity.symbol)
    entry_price_long = _entry_price(long_snapshot)
    entry_price_short = _entry_price(short_snapshot)

    async with AsyncSessionLocal() as session:
        if await repo.group_exists(session, opportunity.group_id):
            logger.info("Group %s already exists, ack", opportunity.group_id)
            return True

        open_groups = await repo.count_open_groups(session)
        if open_groups >= config.risk_limits.group_max:
            logger.warning("group_max reached (%s)", config.risk_limits.group_max)
            return False

        symbol_open = await repo.count_open_groups_by_symbol(session, opportunity.symbol)
        if symbol_open >= config.risk_limits.duplicate_max:
            logger.warning("duplicate_max reached for %s", opportunity.symbol)
            return False

        leverage = config.risk_limits.leverage_max
        margin = config.risk_limits.margin_per_leg
        notional = margin * leverage

        await repo.create_position_group(
            session,
            group_id=opportunity.group_id,
            symbol=opportunity.symbol,
            long_exchange=opportunity.long_exchange,
            short_exchange=opportunity.short_exchange,
            leverage=leverage,
            margin_per_leg=margin,
            notional_per_leg=notional,
            funding_diff=opportunity.funding_diff,
            expected_rate8h=opportunity.expected_rate8h,
            entry_price_long=entry_price_long,
            entry_price_short=entry_price_short,
        )

    logger.info(
        "Created simulated group %s symbol=%s long=%s short=%s entry=(%.4f, %.4f)",
        opportunity.group_id,
        opportunity.symbol,
        opportunity.long_exchange,
        opportunity.short_exchange,
        entry_price_long,
        entry_price_short,
    )
    return True


async def consume_loop(consumer_name: str):
    assert redis_client
    await ensure_consumer_group(redis_client)
    while True:
        entries = await redis_client.xreadgroup(
            GROUP_NAME,
            consumer_name,
            streams={STREAM_KEY: ">"},
            count=20,
            block=5000,
        )
        if not entries:
            continue
        for stream_name, stream_entries in entries:
            for entry_id, fields in stream_entries:
                try:
                    success = await handle_opportunity(fields)
                    if success:
                        await redis_client.xack(STREAM_KEY, GROUP_NAME, entry_id)
                    else:
                        logger.info("Defer opportunity id=%s for retry", entry_id)
                except Exception as exc:  # pragma: no cover
                    logger.exception("Processing opportunity failed: %s", exc)


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
    consumer_name = f"executor-{id(app)}"
    asyncio.create_task(consume_loop(consumer_name))


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
