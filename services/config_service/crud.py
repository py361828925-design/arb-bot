from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.config import get_settings
from libs.db.models import ConfigAuditLog, ConfigProfile
from libs.db.session import AsyncSessionLocal

settings = get_settings()


async def get_latest_profile(session: AsyncSession) -> ConfigProfile | None:
    stmt = select(ConfigProfile).order_by(ConfigProfile.version.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


async def ensure_initial_profile():
    async with AsyncSessionLocal() as session:
        existing = await get_latest_profile(session)
        if existing:
            return existing

        profile = ConfigProfile(
            version=1,
            thresholds=settings.thresholds.model_dump(),
            risk_limits=settings.risk_limits.model_dump(),
            global_enable=True,
            created_by="bootstrap",
        )
        session.add(profile)
        audit = ConfigAuditLog(
            version=profile.version,
            operator="bootstrap",
            action="INITIALIZE",
            detail={
                "thresholds": profile.thresholds,
                "risk_limits": profile.risk_limits,
                "global_enable": profile.global_enable,
            },
        )
        session.add(audit)
        await session.commit()
        return profile


async def create_new_profile(
    session: AsyncSession,
    *,
    thresholds,
    risk_limits,
    global_enable: bool,
    operator: str,
) -> ConfigProfile:
    latest = await get_latest_profile(session)
    new_version = latest.version + 1 if latest else 1

    profile = ConfigProfile(
        version=new_version,
        thresholds=thresholds,
        risk_limits=risk_limits,
        global_enable=global_enable,
        created_by=operator,
    )
    session.add(profile)

    audit = ConfigAuditLog(
        version=new_version,
        operator=operator,
        action="UPDATE",
        detail={
            "thresholds": thresholds,
            "risk_limits": risk_limits,
            "global_enable": global_enable,
        },
    )
    session.add(audit)

    await session.commit()
    await session.refresh(profile)
    return profile
async def create_profile(
    session: AsyncSession,
    *,
    payload=None,
    data=None,
    profile=None,
    thresholds=None,
    risk_limits=None,
    global_enable=None,
    actor: str | None = None,
    created_by: str | None = None,
    operator: str | None = None,
    user: str | None = None,
    **kwargs,
):
    """兼容 config_service.update_config 所需的入口。"""
    source = payload or data or profile

    def _extract(field_name, explicit):
        if explicit is not None:
            return explicit
        if source is None:
            return None
        value = getattr(source, field_name, None)
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value

    thresholds = _extract("thresholds", thresholds)
    risk_limits = _extract("risk_limits", risk_limits)
    global_enable = _extract(
        "global_enable",
        global_enable if global_enable is not None else getattr(source, "global_enable", True),
    )

    if thresholds is None or risk_limits is None:
        latest = await get_latest_profile(session)
        if latest:
            if thresholds is None:
                thresholds = latest.thresholds
            if risk_limits is None:
                risk_limits = latest.risk_limits

    operator = operator or created_by or user or actor or "console"

    return await create_new_profile(
        session=session,
        thresholds=thresholds,
        risk_limits=risk_limits,
        global_enable=global_enable,
        operator=operator,
    )
