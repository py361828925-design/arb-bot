from typing import Any

from redis.asyncio import Redis

from libs.models import FundingSnapshot


class FundingPublisher:
    STREAM_KEY = "funding_snapshots"

    def __init__(self, redis_url: str):
        self._client = Redis.from_url(redis_url, decode_responses=True)

    async def publish(self, snapshot: FundingSnapshot) -> str:
        payload: dict[str, Any] = snapshot.model_dump()
        payload["rate8h"] = snapshot.rate8h
        payload["settle_countdown_secs"] = snapshot.settle_countdown_secs
        payload = {k: "None" if v is None else str(v) for k, v in payload.items()}
        entry_id = await self._client.xadd(self.STREAM_KEY, payload, maxlen=1000, approximate=True)
        return entry_id

    async def close(self):
        await self._client.close()
