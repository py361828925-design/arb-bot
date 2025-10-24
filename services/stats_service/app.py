import asyncio
import contextlib
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------
# 设置系统路径，确保可以引用 libs 和 services 下的模块
# ------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from libs.config import get_settings
from services.stats_service.schemas import (
    DynamicStats,
    SnapshotStats,
    PositionGroupView,
    EventEntry,
)
from services.stats_service.service import StatsService

# ------------------------------------------------------------------
# FastAPI 基础设置
# ------------------------------------------------------------------
logger = logging.getLogger("stats-service")
app = FastAPI(title="Stats Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
stats_service = StatsService(settings.redis_url)

# 给 snapshot 调度任务做个全局引用
config_task: Optional[asyncio.Task] = None


# ------------------------------------------------------------------
# 每日快照调度器
# ------------------------------------------------------------------
async def snapshot_scheduler() -> None:
    # 每天凌晨自动归档前一天的快照
    while True:
        now = datetime.now(timezone.utc)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_seconds = max(1.0, (next_midnight - now).total_seconds())
        try:
            await asyncio.sleep(sleep_seconds)
            snapshot_date = (next_midnight - timedelta(days=1)).date()
            snapshot = await stats_service.archive_snapshot(snapshot_date)
            logger.info(
                "Archived snapshot for %s (net_profit=%.4f total_close=%.4f)",
                snapshot_date,
                snapshot.net_profit,
                snapshot.total_close,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to archive snapshot: %s", exc)
            await asyncio.sleep(5.0)


# ------------------------------------------------------------------
# 启动 / 关闭事件
# ------------------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    global config_task
    if config_task:
        config_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await config_task
    config_task = asyncio.create_task(snapshot_scheduler())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global config_task
    if config_task:
        config_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await config_task
    config_task = None
    await stats_service.close()


# ------------------------------------------------------------------
# API 路由
# ------------------------------------------------------------------
@app.get("/stats/dynamic", response_model=DynamicStats)
async def read_dynamic_stats() -> DynamicStats:
    return await stats_service.get_dynamic_stats()


@app.get("/stats/static", response_model=SnapshotStats)
async def read_snapshot_stats(snapshot_date: Optional[date] = Query(default=None)) -> SnapshotStats:
    snapshot = await stats_service.get_snapshot(snapshot_date)
    if not snapshot:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return snapshot


@app.get("/stats/static/list", response_model=list[SnapshotStats])
async def read_snapshot_list(limit: int = Query(default=30, ge=1, le=365)) -> list[SnapshotStats]:
    return await stats_service.get_snapshots(limit)


@app.post("/stats/snapshot", response_model=SnapshotStats)
async def create_snapshot(snapshot_date: Optional[date] = Query(default=None)) -> SnapshotStats:
    target = snapshot_date or date.today()
    snapshot = await stats_service.archive_snapshot(target)
    logger.info(
        "Manual snapshot stored for %s (net_profit=%.4f total_close=%.4f)",
        target,
        snapshot.net_profit,
        snapshot.total_close,
    )
    return snapshot


@app.get("/events/recent", response_model=list[EventEntry])
async def read_recent_events(limit: int = Query(default=50, ge=1, le=500)) -> list[EventEntry]:
    events = await stats_service.get_recent_events(limit)
    return [
        EventEntry(
            id=e.id,
            group_id=e.group_id,
            symbol=e.symbol,
            event_type=e.event_type,
            logic_reason=e.logic_reason,
            realized_pnl=float(e.realized_pnl) if e.realized_pnl is not None else None,
            created_at=e.created_at,
            data=e.data,
        )
        for e in events
    ]


@app.get("/positions/open", response_model=list[PositionGroupView])
async def read_open_positions() -> list[PositionGroupView]:
    return await stats_service.get_open_positions()
