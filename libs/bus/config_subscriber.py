import asyncio
import json
from typing import Awaitable, Callable, Dict, Optional

from redis.asyncio import Redis


class ConfigSubscriber:
    CHANNEL = "config_updates"

    def __init__(self, redis_url: str):
        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._pubsub = self._client.pubsub(ignore_subscribe_messages=True)
        self._listen_task: Optional[asyncio.Task] = None

    async def start(self, handler: Callable[[Dict], Awaitable[None]]):
        await self._pubsub.subscribe(self.CHANNEL)

        async def _listen():
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                await handler(data)

        self._listen_task = asyncio.create_task(_listen())

    async def stop(self):
        if self._listen_task:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None
        await self._pubsub.unsubscribe()
        await self._pubsub.close()
        await self._client.close()
