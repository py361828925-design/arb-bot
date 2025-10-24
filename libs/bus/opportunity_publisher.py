from redis.asyncio import Redis

from libs.models import Opportunity


class OpportunityPublisher:
    STREAM_KEY = "funding_opportunities"

    def __init__(self, redis_url: str):
        self._client = Redis.from_url(redis_url, decode_responses=True)

    async def publish(self, opportunity: Opportunity) -> str:
        entry_id = await self._client.xadd(
            self.STREAM_KEY,
            opportunity.to_stream_fields(),
            maxlen=1000,
            approximate=True,
        )
        return entry_id

    async def close(self):
        await self._client.close()
