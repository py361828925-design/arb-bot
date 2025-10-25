from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Dict, Iterable, Optional, Union, Callable, Awaitable

from redis.asyncio import Redis


logger = logging.getLogger("bus")


# ---------------------------------------------------------------------------
# Funding publisher（行情服务用 Redis Stream 推送资金费率）
# ---------------------------------------------------------------------------
def _as_stream_fields(payload: Dict[str, Any]) -> Dict[str, str]:
    """把 Pydantic dict 转成 Redis Stream 需要的字符串字段。"""
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
    """把资金费率快照写入 Redis Stream 的发布器。"""

    def __init__(self, settings: Any) -> None:
        self._redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        # 默认改为与其余服务一致的命名，避免订阅端取不到数据
        self._stream_key = getattr(settings, "funding_stream_key", "funding_snapshots")
        self._maxlen = getattr(settings, "funding_stream_maxlen", 1000)
        self._redis: Optional[Redis] = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
                encoding="utf-8",
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
        """写入单条快照，返回 Redis Stream 生成的 entry id。"""
        if self._redis is None:
            raise RuntimeError("FundingPublisher not connected")
        payload = snapshot.model_dump()
        # 这些派生字段在消费者端很常用，直接落到 stream 里减少重复计算
        payload["rate8h"] = snapshot.rate8h
        payload["settle_countdown_secs"] = snapshot.settle_countdown_secs
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


# ---------------------------------------------------------------------------
# Config notifier（配置中心通过 Redis Pub/Sub 推送最新配置）
# ---------------------------------------------------------------------------
class ConfigNotifier:
    """把最新参数配置推送到 Redis 供其它服务订阅。"""

    def __init__(self, settings: Any) -> None:
        self._redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        self._channel_config = getattr(settings, "config_channel", "config:updates")
        self._channel_audit = getattr(settings, "config_audit_channel", "config:audit")
        self._redis: Optional[Redis] = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
                encoding="utf-8",
            )
            logger.info(
                "ConfigNotifier connected (redis=%s channel=%s)",
                self._redis_url,
                self._channel_config,
            )

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("ConfigNotifier connection closed")

    async def notify(self, profile: Union[Dict[str, Any], Any]) -> None:
        """发布配置变更，profile 可以是 Pydantic 模型或 dict。"""
        if self._redis is None:
            raise RuntimeError("ConfigNotifier not connected")

        if hasattr(profile, "model_dump"):
            payload = profile.model_dump()
        elif hasattr(profile, "dict"):
            payload = profile.dict()
        elif hasattr(profile, "__dict__"):
            payload = {
                key: value
                for key, value in profile.__dict__.items()
                if not key.startswith("_")
            }
        else:
            payload = dict(profile)

        payload_str = json.dumps(payload, default=str)
        await self._redis.publish(self._channel_config, payload_str)
        logger.debug("Published config update version=%s", payload.get("version"))

    async def publish_profile(self, profile: Union[Dict[str, Any], Any]) -> None:
        """兼容旧接口名称，实际调用 notify。"""
        await self.notify(profile)

    async def publish_audit(self, audit: Union[Dict[str, Any], Any]) -> None:
        """把配置修改记录发送到审计频道（若其他服务需要）。"""
        if self._redis is None:
            raise RuntimeError("ConfigNotifier not connected")

        if hasattr(audit, "model_dump"):
            payload = audit.model_dump()
        elif hasattr(audit, "dict"):
            payload = audit.dict()
        else:
            payload = dict(audit)

        payload_str = json.dumps(payload, default=str)
        await self._redis.publish(self._channel_audit, payload_str)
        logger.debug(
            "Published config audit version=%s", payload.get("version", "<unknown>")
        )

class ConfigSubscriber:
    """订阅 Redis Pub/Sub 中的配置更新事件。"""

    def __init__(self, settings: Any) -> None:
        self._redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        self._channel = getattr(settings, "config_channel", "config:updates")
        self._redis: Optional[Redis] = None
        self._pubsub = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
                encoding="utf-8",
            )
            self._pubsub = self._redis.pubsub()
        if self._pubsub:
            await self._pubsub.subscribe(self._channel)
            logger.info(
                "ConfigSubscriber listening (redis=%s channel=%s)",
                self._redis_url,
                self._channel,
            )

    async def close(self) -> None:
        if self._pubsub is not None:
            await self._pubsub.unsubscribe(self._channel)
            await self._pubsub.close()
            self._pubsub = None
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
        logger.info("ConfigSubscriber connection closed")

    async def listen(self):
        """异步迭代收到的配置消息。"""
        if self._pubsub is None:
            raise RuntimeError("ConfigSubscriber not connected")
        async for message in self._pubsub.listen():
            if message["type"] != "message":
                continue
            yield json.loads(message["data"])

    async def start(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        await self.connect()
        if self._pubsub is None:
            raise RuntimeError("ConfigSubscriber not connected")
        try:
            async for payload in self.listen():
                try:
                    await handler(payload)
                except Exception as exc:
                    logger.warning("apply config update failed: %s", exc)
        except asyncio.CancelledError:
            pass
