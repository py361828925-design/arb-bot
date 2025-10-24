import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
from typing import Dict, List, Optional

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from libs.db.models import PositionEvent, PositionGroup, StatsSnapshot
from libs.db.session import AsyncSessionLocal
from libs.models import FundingSnapshot
from services.stats_service.schemas import (
    DynamicStats,
    PositionGroupView,
    PositionLegView,
    SnapshotStats,
)


class StatsService:
    def __init__(self, redis_url: str):
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._dynamic_cache_key = "stats:dynamic"
        self._funding_stream = "funding_snapshots"

    async def close(self) -> None:
        await self._redis.close()

    async def get_dynamic_stats(self) -> DynamicStats:
        cached = await self._redis.get(self._dynamic_cache_key)
        if cached:
            payload = json.loads(cached)
            payload["updated_at"] = datetime.fromisoformat(payload["updated_at"])
            return DynamicStats(**payload)
        stats = await self._recompute_dynamic_stats()
        payload = stats.model_dump()
        payload["updated_at"] = payload["updated_at"].isoformat()
        await self._redis.set(self._dynamic_cache_key, json.dumps(payload), ex=10)
        return stats

    async def _recompute_dynamic_stats(self) -> DynamicStats:
        async with AsyncSessionLocal() as session:
            open_result = await session.execute(
                select(PositionGroup).where(PositionGroup.status == "OPEN")
            )
            open_groups = open_result.scalars().all()

            event_result = await session.execute(select(PositionEvent))
            events = event_result.scalars().all()

        active_notional = sum((group.margin_per_leg or 0) * 2 for group in open_groups)

        total_open = 0.0
        total_close = 0.0
        logic_amounts = {
            "logic1_amount": 0.0,
            "logic2_amount": 0.0,
            "logic3_amount": 0.0,
            "logic4_amount": 0.0,
            "logic5_amount": 0.0,
        }
        net_profit = 0.0

        for event in events:
            data = event.data or {}
            notional_per_leg = _to_float(data.get("notional_per_leg", 0))
            notional_total = notional_per_leg * 2

            if event.event_type == "OPEN":
                total_open += notional_total
            elif event.event_type == "CLOSE":
                total_close += notional_total
                reason = (event.logic_reason or "").lower()
                logic_key = f"{reason}_amount"
                if logic_key in logic_amounts:
                    logic_amounts[logic_key] += notional_total
                net_profit += _to_float(event.realized_pnl)

        return DynamicStats(
            active_notional=active_notional,
            total_open=total_open,
            total_close=total_close,
            logic1_amount=logic_amounts["logic1_amount"],
            logic2_amount=logic_amounts["logic2_amount"],
            logic3_amount=logic_amounts["logic3_amount"],
            logic4_amount=logic_amounts["logic4_amount"],
            logic5_amount=logic_amounts["logic5_amount"],
            net_profit=net_profit,
            updated_at=datetime.now(timezone.utc),
        )

    async def get_open_positions(self) -> List[PositionGroupView]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PositionGroup)
                .options(selectinload(PositionGroup.legs))
                .where(PositionGroup.status == "OPEN")
            )
            groups = result.scalars().all()

        views: List[PositionGroupView] = []
        for group in groups:
            view = await self._build_group_view(group)
            views.append(view)
        return views

    async def get_snapshot(self, snapshot_date: Optional[date]) -> Optional[SnapshotStats]:
        if snapshot_date is None:
            snapshot_date = date.today()
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(StatsSnapshot).where(StatsSnapshot.snapshot_date == snapshot_date)
            )
            snapshot = result.scalars().first()
        if not snapshot:
            return None
        return SnapshotStats(
            snapshot_date=snapshot.snapshot_date,
            total_open=_to_float(snapshot.total_open),
            total_close=_to_float(snapshot.total_close),
            logic1_amount=_to_float(snapshot.logic1_amount),
            logic2_amount=_to_float(snapshot.logic2_amount),
            logic3_amount=_to_float(snapshot.logic3_amount),
            logic4_amount=_to_float(snapshot.logic4_amount),
            logic5_amount=_to_float(snapshot.logic5_amount),
            net_profit=_to_float(snapshot.net_profit),
        )

    async def _build_group_view(self, group: PositionGroup) -> PositionGroupView:
        long_leg = next((leg for leg in group.legs if leg.side.upper() == "LONG"), None)
        short_leg = next((leg for leg in group.legs if leg.side.upper() == "SHORT"), None)

        long_snapshot = await self._get_latest_snapshot(group.long_exchange, group.symbol)
        short_snapshot = await self._get_latest_snapshot(group.short_exchange, group.symbol)

        long_return = _calc_leg_return(long_leg, long_snapshot, "LONG")
        short_return = _calc_leg_return(short_leg, short_snapshot, "SHORT")
        total_return = long_return + short_return

        if long_snapshot and short_snapshot:
            countdown_secs = min(
                long_snapshot.settle_countdown_secs,
                short_snapshot.settle_countdown_secs,
            )
            funding_diff = long_snapshot.rate8h - short_snapshot.rate8h
        else:
            countdown_secs = -1
            funding_diff = 0.0

        now = datetime.now(timezone.utc)
        duration_seconds = int((now - group.opened_at).total_seconds())

        legs = [
            PositionLegView(
                exchange=leg.exchange,
                side=leg.side.upper(),
                entry_price=leg.entry_price or 0.0,
                exit_price=leg.exit_price,
                quantity=leg.notional,
                pnl=leg.pnl,
            )
            for leg in group.legs
        ]

        return PositionGroupView(
            group_id=group.group_id,
            symbol=group.symbol,
            long_exchange=group.long_exchange,
            short_exchange=group.short_exchange,
            leverage=group.leverage,
            margin_per_leg=group.margin_per_leg,
            notional_per_leg=group.notional_per_leg,
            opened_at=group.opened_at,
            duration_seconds=duration_seconds,
            current_countdown_secs=countdown_secs,
            long_return=long_return,
            short_return=short_return,
            total_return=total_return,
            current_funding_diff=funding_diff,
            legs=legs,
        )

    async def _get_latest_snapshot(self, exchange: str, symbol: str) -> Optional[FundingSnapshot]:
        entries = await self._redis.xrevrange(self._funding_stream, "+", "-", count=200)
        for _, fields in entries:
            if fields.get("exchange") == exchange and fields.get("symbol") == symbol:
                try:
                    return FundingSnapshot.from_stream(fields)
                except Exception:
                    continue
        return None


def _to_float(value: Optional[Decimal | float | int]) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _calc_leg_return(leg, snapshot: Optional[FundingSnapshot], side: str) -> float:
    if not leg:
        return 0.0
    entry = leg.entry_price or 0.0
    if entry <= 0:
        return 0.0
    price = None
    if snapshot:
        price = snapshot.mark_price or snapshot.index_price
    if price is None:
        return 0.0
    if side.upper() == "LONG":
        return (price - entry) / entry
    return (entry - price) / entry
