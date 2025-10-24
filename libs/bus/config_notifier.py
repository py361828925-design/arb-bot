import json
from typing import Any, Dict, Optional

from redis.asyncio import Redis

from libs.db.models import ConfigProfile


class ConfigNotifier:
    CHANNEL = "config_updates"

    def __init__(self, redis_url: str):
        self._client = Redis.from_url(redis_url, decode_responses=True)

    async def publish_profile(self, profile: ConfigProfile):
        payload: Dict[str, Any] = {
            "version": profile.version,
            "thresholds": profile.thresholds,
            "risk_limits": profile.risk_limits,
            "global_enable": profile.global_enable,
        }
        await self._client.publish(self.CHANNEL, json.dumps(payload))

    async def close(self):
        await self._client.close()
