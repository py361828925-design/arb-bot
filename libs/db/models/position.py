from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from libs.db.base import Base


class PositionGroup(Base):
    __tablename__ = "position_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(64), unique=True, nullable=False, index=True)
    symbol = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="OPEN")
    long_exchange = Column(String(32), nullable=False)
    short_exchange = Column(String(32), nullable=False)
    leverage = Column(Float, nullable=False)
    margin_per_leg = Column(Float, nullable=False)
    notional_per_leg = Column(Float, nullable=False)
    funding_diff = Column(Float, nullable=False)
    expected_rate8h = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    simulated = Column(Boolean, nullable=False, default=True)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    close_reason = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    legs = relationship("PositionLeg", back_populates="group", cascade="all, delete-orphan")


class PositionLeg(Base):
    __tablename__ = "position_legs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("position_groups.id", ondelete="CASCADE"))
    exchange = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    margin = Column(Float, nullable=False)
    notional = Column(Float, nullable=False)
    fee_rate = Column(Float, nullable=False)
    status = Column(String(16), nullable=False, default="OPEN")
    opened_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    pnl = Column(Float, nullable=True)

    group = relationship("PositionGroup", back_populates="legs")
