import logging
import os
import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def _notify_telegram(message: str) -> None:
    if not _TELEGRAM_TOKEN or not _TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{_TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": _TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)
    except Exception as exc:
        logger.warning("send telegram failed: %s", exc)


from libs.db.models import PositionGroup, PositionLeg, PositionEvent
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models import PositionGroup, PositionLeg


async def count_open_groups(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(PositionGroup).where(PositionGroup.status == "OPEN")
    result = await session.execute(stmt)
    return result.scalar_one()


async def count_open_groups_by_symbol(session: AsyncSession, symbol: str) -> int:
    stmt = (
        select(func.count())
        .select_from(PositionGroup)
        .where(PositionGroup.symbol == symbol, PositionGroup.status == "OPEN")
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def group_exists(session: AsyncSession, group_id: str) -> bool:
    stmt = select(PositionGroup.id).where(PositionGroup.group_id == group_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def create_position_group(
    session: AsyncSession,
    *,
    group_id: str,
    symbol: str,
    long_exchange: str,
    short_exchange: str,
    leverage: float,
    margin_per_leg: float,
    notional_per_leg: float,
    funding_diff: float,
    expected_rate8h: float,
    entry_price_long: float,
    entry_price_short: float,
):
    group = PositionGroup(
        group_id=group_id,
        symbol=symbol,
        long_exchange=long_exchange,
        short_exchange=short_exchange,
        leverage=leverage,
        margin_per_leg=margin_per_leg,
        notional_per_leg=notional_per_leg,
        funding_diff=funding_diff,
        expected_rate8h=expected_rate8h,
        simulated=True,
    )

    legs = [
        PositionLeg(
            exchange=long_exchange,
            side="LONG",
            quantity=notional_per_leg,
            entry_price=entry_price_long,
            exit_price=None,
            margin=margin_per_leg,
            notional=notional_per_leg,
            fee_rate=0.0,
            pnl=0.0,
        ),
        PositionLeg(
            exchange=short_exchange,
            side="SHORT",
            quantity=notional_per_leg,
            entry_price=entry_price_short,
            exit_price=None,
            margin=margin_per_leg,
            notional=notional_per_leg,
            fee_rate=0.0,
            pnl=0.0,
        ),
    ]

    group.legs.extend(legs)
    session.add(group)
    await session.commit()
    await session.refresh(group)

    session.add(
        PositionEvent(
            group_id=group.group_id,
            symbol=group.symbol,
            event_type="OPEN",
            realized_pnl=0,
            data={
                "entry_price_long": entry_price_long,
                "entry_price_short": entry_price_short,
                "notional_per_leg": notional_per_leg,
                "leverage": leverage,
            },
        )
    )
    await session.commit()
    message = (
        f"🚀 *开仓*\n"
        f"仓位组: `{group.group_id}`\n"
        f"币种: *{group.symbol}*\n"
        f"多: {group.long_exchange} / 空: {group.short_exchange}\n"
        f"名义金额: {notional_per_leg * 2:.2f} USDT"
    )
    await _notify_telegram(message)

    return group
