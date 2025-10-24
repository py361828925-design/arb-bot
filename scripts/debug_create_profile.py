import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from services.config_service import crud
from services.config_service.deps import get_session


async def main() -> None:
    async for session in get_session():
        try:
            result = await crud.create_profile(
                session=session,
                thresholds={
                    "aa": 44.0,
                    "bb": 44.0,
                    "cc": 44.0,
                    "dd": 44,
                    "ee": 44.0,
                    "ff": 44.0,
                    "gg": 44.0,
                    "hh": 44.0,
                },
                risk_limits={
                    "group_max": 44,
                    "duplicate_max": 44,
                    "leverage_max": 44.0,
                    "margin_per_leg": 445.0,
                    "taker_fee": 44.0,
                    "maker_fee": 44.0,
                    "trade_fee": 0.04,
                },
                global_enable=True,
                scan_interval_seconds=50.0,
                close_interval_seconds=55.0,
                open_interval_seconds=5.0,
                actor="debug",
            )
            print("Success", result)
        finally:
            await session.close()
        break


if __name__ == "__main__":
    asyncio.run(main())
