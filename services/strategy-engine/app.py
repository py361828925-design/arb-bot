import asyncio
import contextlib
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI
from redis.asyncio import Redis

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from libs.bus import ConfigSubscriber, OpportunityPublisher
from libs.config import get_settings
from libs.models import FundingSnapshot, Opportunity
from libs.runtime_config import apply_update, get_runtime_config, load_initial

logger = logging.getLogger("strategy-engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI()
settings = get_settings()
redis_client: Optional[Redis] = None
config_subscriber: Optional[ConfigSubscriber] = None
config_task: Optional[asyncio.Task] = None
opportunity_publisher: Optional[OpportunityPublisher] = None
last_id = "0-0"

latest_rates: Dict[str, Dict[str, FundingSnapshot]] = defaultdict(dict)


async def evaluate_opportunity(snapshot: FundingSnapshot) -> None:
    config = get_runtime_config()
    if not config.global_enable:
        return

    exchange = snapshot.exchange
    symbol = snapshot.symbol
    latest_rates[exchange][symbol] = snapshot

    if "binance" not in latest_rates or "bitget" not in latest_rates:
        return

    other_exchange = "bitget" if exchange == "binance" else "binance"
    other_snapshot = latest_rates[other_exchange].get(symbol)
    if not other_snapshot:
        return

    funding_diff = snapshot.rate8h - other_snapshot.rate8h
    threshold = config.thresholds.aa

    if abs(funding_diff) < threshold:
        return

    if funding_diff > 0:
        long_exchange = other_exchange
        short_exchange = exchange
    else:
        long_exchange = exchange
        short_exchange = other_exchange

    opportunity = Opportunity.create(
        symbol=symbol,
        long_exchange=long_exchange,
        short_exchange=short_exchange,
        funding_diff=funding_diff,
        expected_rate8h=snapshot.rate8h,
    )
    logger.info(
        "Opportunity %s %s diff=%.6f long=%s short=%s (threshold %.6f)",
        opportunity.group_id,
        symbol,
        funding_diff,
        long_exchange,
        short_exchange,
        threshold,
    )
    if opportunity_publisher:
        entry_id = await opportunity_publisher.publish(opportunity)
        logger.info("Published opportunity entry_id=%s", entry_id)


async def process_entries(entries: List):
    global last_id
    for stream_name, stream_entries in entries:
        for entry_id, fields in stream_entries:
            snapshot = FundingSnapshot.from_stream(fields)
            await evaluate_opportunity(snapshot)
            last_id = entry_id


async def consumer_loop():
    global redis_client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("Strategy consumer started, listening from %s", last_id)
    try:
        while True:
            entries = await redis_client.xread(
                {"funding_snapshots": last_id},
                count=100,
                block=5000,
            )
            if entries:
                await process_entries(entries)
    finally:
        await redis_client.close()


async def _config_listener():
    subscriber = ConfigSubscriber(settings.redis_url)
    await subscriber.start(apply_update)
    return subscriber


@app.on_event("startup")
async def on_startup():
    global config_subscriber, config_task, opportunity_publisher
    await load_initial()
    config_task = asyncio.create_task(_config_listener())
    opportunity_publisher = OpportunityPublisher(settings.redis_url)
    asyncio.create_task(consumer_loop())


@app.on_event("shutdown")
async def on_shutdown():
    global config_subscriber, config_task, opportunity_publisher
    if config_task:
        config_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await config_task
    if config_subscriber:
        await config_subscriber.stop()
    if opportunity_publisher:
        await opportunity_publisher.close()
