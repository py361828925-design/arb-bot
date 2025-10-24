from libs.db.models import PositionGroup, PositionLeg, PositionEvent
from datetime import datetime, timezone
from typing import Dict, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from libs.db.models import PositionGroup, PositionLeg


async def fetch_open_groups(session: AsyncSession) -> Iterable[PositionGroup]:
    stmt = (
        select(PositionGroup)
        .options(selectinload(PositionGroup.legs))
        .where(PositionGroup.status == "OPEN")
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def close_group(
    session: AsyncSession,
    group: PositionGroup,
    reason: str,
    close_prices: Dict[str, float],
) -> None:
    now = datetime.now(timezone.utc)
    group.status = "CLOSED"
    group.close_reason = reason
    group.closed_at = now

    total_pnl = 0.0
    returns: Dict[str, float] = {}

    for leg in group.legs:
        entry = leg.entry_price or 1.0
        mark = close_prices.get(leg.exchange, entry)
        leg.exit_price = mark

        if leg.side.upper() == "LONG":
            pnl_pct = (mark - entry) / entry
        else:
            pnl_pct = (entry - mark) / entry

        leg.pnl = pnl_pct * leg.notional
        leg.status = "CLOSED"
        leg.closed_at = now
        returns[leg.exchange] = pnl_pct
        total_pnl += leg.pnl

    current_diff = close_prices.get("__current_diff__")
    if current_diff is not None:
        group.funding_diff = current_diff

    group.realized_pnl = total_pnl
    if group.notional_per_leg:
        group.expected_rate8h = total_pnl / (group.notional_per_leg * 2)

    session.add(
        PositionEvent(
            group_id=group.group_id,
            symbol=group.symbol,
            event_type="CLOSE",
            logic_reason=reason,
            realized_pnl=total_pnl,
            data={
                "close_prices": close_prices,
                "returns": returns,
                "notional_per_leg": group.notional_per_leg,
            },
        )
    )
    await session.commit()
