from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class DynamicStats(BaseModel):
    active_notional: float
    active_group_count: int
    total_open: float
    total_open_count: int
    total_close: float
    total_close_count: int
    logic1_amount: float
    logic1_count: int
    logic2_amount: float
    logic2_count: int
    logic3_amount: float
    logic3_count: int
    logic4_amount: float
    logic4_count: int
    logic5_amount: float
    logic5_count: int
    net_profit: float
    updated_at: datetime

    active_notional: float
    total_open: float
    total_close: float
    logic1_amount: float
    logic2_amount: float
    logic3_amount: float
    logic4_amount: float
    logic5_amount: float
    net_profit: float
    updated_at: datetime


class SnapshotStats(BaseModel):
    snapshot_date: date
    total_open: float
    total_close: float
    logic1_amount: float
    logic2_amount: float
    logic3_amount: float
    logic4_amount: float
    logic5_amount: float
    net_profit: float


class EventEntry(BaseModel):
    id: int
    group_id: str
    symbol: str
    event_type: str
    logic_reason: Optional[str]
    realized_pnl: Optional[float]
    created_at: datetime
    data: Optional[dict]


class PositionLegView(BaseModel):
    exchange: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: Optional[float]


class PositionGroupView(BaseModel):
    group_id: str
    symbol: str
    long_exchange: str
    short_exchange: str
    leverage: float
    margin_per_leg: float
    notional_per_leg: float
    opened_at: datetime
    duration_seconds: int
    current_countdown_secs: int
    long_return: float
    short_return: float
    total_return: float
    current_funding_diff: float
    legs: List[PositionLegView]
