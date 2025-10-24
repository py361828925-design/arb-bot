import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from services.stats_service.service import StatsService
from libs.config import get_settings


async def main() -> None:
    settings = get_settings()
    service = StatsService(settings.redis_url)
    result = await service.get_dynamic_stats()
    print(result.model_dump())
    await service.close()


if __name__ == "__main__":
    asyncio.run(main())
