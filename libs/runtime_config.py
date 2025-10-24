import asyncio
import json
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from libs.config import RiskLimits, Thresholds, get_settings

logger = logging.getLogger("runtime-config")


class RuntimeConfigState(BaseModel):
    version: int
    thresholds: Thresholds
    risk_limits: RiskLimits
    global_enable: bool

    class Config:
        arbitrary_types_allowed = True


_settings = get_settings()
_lock = asyncio.Lock()
_state = RuntimeConfigState(
    version=0,
    thresholds=_settings.thresholds,
    risk_limits=_settings.risk_limits,
    global_enable=True,
)


async def _set_state(data: Dict[str, Any]):
    global _state
    async with _lock:
        _state = RuntimeConfigState(
            version=data["version"],
            thresholds=Thresholds(**data["thresholds"]),
            risk_limits=RiskLimits(**data["risk_limits"]),
            global_enable=data.get("global_enable", True),
        )
        logger.info("Runtime config updated to version %s", _state.version)


async def load_initial(client: Optional[httpx.AsyncClient] = None):
    created_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=5.0)
        created_client = True
    try:
        resp = await client.get(f"{_settings.config_service_url}/config/current")
        resp.raise_for_status()
        await _set_state(resp.json())
    except Exception as exc:
        logger.warning("load_initial config failed: %s", exc)
    finally:
        if created_client:
            await client.aclose()


async def apply_update(payload: Dict[str, Any]):
    await _set_state(payload)


def get_runtime_config() -> RuntimeConfigState:
    return _state
