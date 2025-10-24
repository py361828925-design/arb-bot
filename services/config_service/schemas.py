from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from libs.config import RiskLimits, Thresholds


class ConfigResponse(BaseModel):
    version: int
    thresholds: Thresholds
    risk_limits: RiskLimits
    global_enable: bool
    created_by: str
    created_at: datetime


class ConfigUpdateRequest(BaseModel):
    thresholds: Optional[Thresholds] = None
    risk_limits: Optional[RiskLimits] = None
    global_enable: Optional[bool] = None
    operator: str = "console"
