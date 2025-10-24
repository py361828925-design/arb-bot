from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, func

from libs.db.base import Base


class ConfigProfile(Base):
    __tablename__ = "config_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, unique=True)
    thresholds = Column(JSON, nullable=False)
    risk_limits = Column(JSON, nullable=False)
    global_enable = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(64), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConfigAuditLog(Base):
    __tablename__ = "config_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False)
    operator = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
