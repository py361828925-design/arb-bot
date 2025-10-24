from functools import lru_cache
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field


class Thresholds(BaseModel):
    aa: float = 0.0005
    bb: float = 0.0002
    cc: float = 0.0001
    dd: int = 5
    ee: float = 0.0002
    ff: float = 0.0010
    gg: float = 0.0020
    hh: float = Field(0.001, description="逻辑2 单腿亏损触发阈值")




class RiskLimits(BaseModel):
    group_max: int = 20
    duplicate_max: int = 2
    leverage_max: float = 10.0
    margin_per_leg: float = 100.0
    taker_fee: float = 0.0006
    maker_fee: float = 0.0002
    trade_fee: float = 0.0006


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://arb_user:your_password@localhost:5432/arb_db"
    redis_url: str = "redis://localhost:6379/0"
    config_service_url: str = "http://localhost:8003"
    scan_interval_seconds: float = 10.0
    close_interval_seconds: float = 5.0
    open_interval_seconds: float = 5.0
    thresholds: Thresholds = Thresholds()
    risk_limits: RiskLimits = RiskLimits()
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
