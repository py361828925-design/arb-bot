import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from libs.db.base import Base
from libs.db.session import engine
from libs.config import get_settings


async def init_database() -> None:
    settings = get_settings()
    print(f"Initializing database at {settings.database_url}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_database())
