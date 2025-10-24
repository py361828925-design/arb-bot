"""Basic smoke tests for config and stats services."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure project root in sys.path for modules that rely on relative imports
ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from libs.db.base import Base
from libs.db.session import engine
from services.config_service.app import app as config_app
from services.config_service.schemas import ConfigUpdateRequest
from services.stats_service.app import app as stats_app


async def _reset_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def _run_config_checks() -> None:
    payload = ConfigUpdateRequest(  # type: ignore[arg-type]
        global_enable=True,
        thresholds={
            "aa": 0.1,
            "bb": 0.2,
            "cc": 0.3,
            "dd": 1,
            "ee": 0.5,
            "ff": 0.6,
            "gg": 0.7,
            "hh": 0.8,
        },
        risk_limits={
            "group_max": 5,
            "duplicate_max": 2,
            "leverage_max": 5.0,
            "margin_per_leg": 100.0,
            "taker_fee": 0.001,
            "maker_fee": 0.0005,
            "trade_fee": 0.0008,
        },
        scan_interval_seconds=12.0,
        close_interval_seconds=6.0,
        open_interval_seconds=3.0,
    )

    with TestClient(config_app) as client:
        get_resp = client.get("/config/current")
        get_resp.raise_for_status()

        put_resp = client.put("/config/current", json=payload.model_dump())
        put_resp.raise_for_status()

        latest = put_resp.json()
        assert latest["thresholds"]["aa"] == 0.1


def _run_stats_checks() -> None:
    with TestClient(stats_app) as client:
        post_resp = client.post("/stats/snapshot")
        post_resp.raise_for_status()

        dynamic_resp = client.get("/stats/dynamic")
        dynamic_resp.raise_for_status()

        events_resp = client.get("/events/recent")
        events_resp.raise_for_status()


def main() -> None:
    asyncio.run(_reset_database())
    _run_config_checks()
    _run_stats_checks()


if __name__ == "__main__":
    main()
