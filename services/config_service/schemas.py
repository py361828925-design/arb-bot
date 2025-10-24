from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from libs.config import RiskLimits, Thresholds


class ConfigResponse(BaseModel):
    version: int
    thresholds: Thresholds
    risk_limits: RiskLimits
    global_enable: bool
    scan_interval_seconds: Optional[float] = None
    close_interval_seconds: Optional[float] = None
    open_interval_seconds: Optional[float] = None
    created_by: str
    created_at: datetime


class ConfigUpdateRequest(BaseModel):
    thresholds: Optional[Thresholds] = None
    risk_limits: Optional[RiskLimits] = None
    global_enable: Optional[bool] = None
    scan_interval_seconds: Optional[float] = None
    close_interval_seconds: Optional[float] = None
    open_interval_seconds: Optional[float] = None
    operator: str = "console"
