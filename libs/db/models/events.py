from datetime import datetime, timezone

from sqlalchemy import Numeric, Column, Date, DateTime, Integer, JSON, String, func

from libs.db.base import Base


class PositionEvent(Base):
    __tablename__ = "position_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(32), nullable=False)
    event_type = Column(String(16), nullable=False)  # OPEN / CLOSE
    logic_reason = Column(String(32), nullable=True)
    realized_pnl = Column(Numeric(18, 8), nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StatsSnapshot(Base):
    __tablename__ = "stats_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    total_open = Column(Numeric(18, 8), nullable=False, default=0)
    total_close = Column(Numeric(18, 8), nullable=False, default=0)
    logic1_amount = Column(Numeric(18, 8), nullable=False, default=0)
    logic2_amount = Column(Numeric(18, 8), nullable=False, default=0)
    logic3_amount = Column(Numeric(18, 8), nullable=False, default=0)
    logic4_amount = Column(Numeric(18, 8), nullable=False, default=0)
    logic5_amount = Column(Numeric(18, 8), nullable=False, default=0)
    net_profit = Column(Numeric(18, 8), nullable=False, default=0)
    raw_stats = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
