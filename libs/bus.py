from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

from redis.asyncio import Redis

logger = logging.getLogger("bus")


def _as_stream_fields(payload: Dict[str, Any]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, (int, float)):
            fields[key] = f"{value}"
        else:
            fields[key] = str(value)
    return fields


class FundingPublisher:
    def __init__(self, settings: Any) -> None:
        self._redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        self._stream_key = getattr(settings, "funding_stream_key", "funding:snapshots")
        self._maxlen = getattr(settings, "funding_stream_maxlen", 1000)
        self._redis: Optional[Redis] = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url, decode_responses=True, encoding="utf-8"
            )
            logger.info(
                "FundingPublisher connected (redis=%s stream=%s)",
                self._redis_url,
                self._stream_key,
            )

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("FundingPublisher connection closed")

    async def publish(self, snapshot) -> str:
        if self._redis is None:
            raise RuntimeError("FundingPublisher not connected")
        payload = snapshot.model_dump()
        fields = _as_stream_fields(payload)
        entry_id = await self._redis.xadd(
            self._stream_key,
            fields,
            maxlen=self._maxlen,
            approximate=True,
        )
        logger.debug(
            "Published funding snapshot exchange=%s symbol=%s entry=%s",
            payload.get("exchange"),
            payload.get("symbol"),
            entry_id,
        )
        return entry_id

    async def publish_many(self, snapshots: Iterable) -> None:
        for snapshot in snapshots:
            try:
                await self.publish(snapshot)
            except Exception as exc:
                logger.exception("Publish snapshot failed: %s", exc)
