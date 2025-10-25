
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import inspect
import logging
from typing import Any, Callable, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from libs.bus import ConfigNotifier
from libs.config import get_settings
from libs.db.base import Base
from libs.db.session import engine
from services.config_service import crud, schemas
from services.config_service.deps import get_session

logger = logging.getLogger("config_service")

app = FastAPI(
    title="Config Service",
    version="0.1.0",
    description="管理阈值与风控参数的配置中心",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "http://47.84.57.96:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://0.0.0.0:3001",
    "http://47.84.57.96:3001",
    "http://8.222.222.128:3000",  # 如果有其它前端域名或端口，在这里追加
]

public_origins = os.getenv("FRONTEND_ORIGINS")
if public_origins:
    for item in public_origins.split(","):
        origin = item.strip()
        if origin and origin not in origins:
            origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



_settings = get_settings()
_notifier: Optional[ConfigNotifier] = None

# -----------------------------------------------------------------------------
# 实用函数
# -----------------------------------------------------------------------------
def _select_schema(*names: str) -> type[Any]:
    for name in names:
        if hasattr(schemas, name):
            return getattr(schemas, name)
    raise RuntimeError(
        f"schemas 模块中找不到 {', '.join(names)} 中的任意一个类型，请确认 schemas.py 内容。"
    )


ConfigRead = _select_schema("ConfigResponse")
ConfigWrite = _select_schema("ConfigUpdateRequest")


async def _invoke_callable(func: Callable[..., Any], mapping: Dict[str, Any]) -> Any:
    """根据函数签名智能传参，兼容不同命名。"""
    sig = inspect.signature(func)
    kwargs: Dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in mapping:
            kwargs[name] = mapping[name]
    result = func(**kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result


def _actor_from_payload(payload: Any, default: str = "api") -> str:
    for attr in ("updated_by", "modified_by", "actor", "user", "created_by"):
        if hasattr(payload, attr):
            value = getattr(payload, attr)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return default


async def _publish_profile(profile: Any) -> None:
    if not _notifier:
        return
    try:
        if hasattr(_notifier, "publish_profile"):
            await _notifier.publish_profile(profile)
        elif hasattr(_notifier, "notify"):
            await _notifier.notify(profile)
    except Exception as exc:
        logger.warning("配置推送失败，将忽略此错误: %s", exc)


async def _publish_audit(audit: Any) -> None:
    if not _notifier:
        return
    try:
        if hasattr(_notifier, "publish_audit"):
            await _notifier.publish_audit(audit)
    except Exception as exc:
        logger.warning("审计推送失败，将忽略此错误: %s", exc)


async def _ensure_initial_profile(session: AsyncSession) -> None:
    ensure_fn = getattr(crud, "ensure_initial_profile", None)
    if ensure_fn:
        await _invoke_callable(
            ensure_fn,
            {
                "session": session,
                "settings": _settings,
                "actor": "bootstrap",
            },
        )
        return

    get_fn = getattr(crud, "get_latest_profile", None)
    if not get_fn:
        logger.warning("crud 模块缺少 get_latest_profile，无法检查初始配置。")
        return

    profile = await _invoke_callable(get_fn, {"session": session})
    if profile:
        return

    logger.info("未检测到配置记录，跳过自动创建；请通过 PUT /config/current 进行初始化。")


# -----------------------------------------------------------------------------
# 生命周期事件
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    global _notifier
    logger.info("启动 Config Service，准备初始化数据库并连接 Redis 通知通道。")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已确保存在。")
    try:
        _notifier = ConfigNotifier(settings=_settings)
        await _notifier.connect()
    except Exception as exc:
        logger.warning("初始化 Redis 通知通道失败，将以降级模式运行: %s", exc)
        _notifier = None

    async for session in get_session():
        try:
            logger.info("确保存在初始配置档案...")
            await _ensure_initial_profile(session)
        finally:
            await session.close()
        break


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if _notifier:
        await _notifier.close()
    logger.info("Config Service 已正常关闭。")


# -----------------------------------------------------------------------------
# 路由
# -----------------------------------------------------------------------------
@app.get(
    "/config/current",
    response_model=ConfigRead,
    summary="读取当前生效配置",
)
async def read_current_config(
    session: AsyncSession = Depends(get_session),
):
    get_fn = getattr(crud, "get_latest_profile", None)
    if not get_fn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部缺少 get_latest_profile 实现",
        )

    profile = await _invoke_callable(get_fn, {"session": session})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前没有配置档案，请先通过 PUT /config/current 上传配置。",
        )
    return profile


@app.put(
    "/config/current",
    response_model=ConfigRead,
    summary="创建新版本配置并发布",
)
async def update_config(
    payload: ConfigWrite,
    session: AsyncSession = Depends(get_session),
):
    create_fn = getattr(crud, "create_profile", None)
    if not create_fn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部缺少 create_profile 实现",
        )

    actor = _actor_from_payload(payload, default="api")
    result = await _invoke_callable(
        create_fn,
        {
            "session": session,
            "payload": payload,
            "data": payload,
            "profile": payload,
            "actor": actor,
            "created_by": actor,
            "user": actor,
        },
    )

    if isinstance(result, tuple) and len(result) == 2:
        profile, audit = result
    else:
        profile, audit = result, None

    await _publish_profile(profile)
    if audit:
        await _publish_audit(audit)

    return profile
