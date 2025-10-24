from datetime import datetime
from pydantic import BaseModel


class PositionGroupSchema(BaseModel):
    group_id: str
    symbol: str
    long_exchange: str
    short_exchange: str
    leverage: float
    margin_per_leg: float
    notional_per_leg: float
    funding_diff: float
    expected_rate8h: float
    opened_at: datetime

    class Config:
        orm_mode = True
