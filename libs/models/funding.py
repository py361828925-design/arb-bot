from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel


class FundingSnapshot(BaseModel):
    exchange: str
    symbol: str
    funding_rate_raw: float
    settle_interval_hours: int
    next_funding_time_ms: int
    instrument: Optional[str] = None
    mark_price: Optional[float] = None
    index_price: Optional[float] = None
    captured_at_ms: int

    @property
    def rate8h(self) -> float:
        return self.funding_rate_raw * (8 / self.settle_interval_hours)

    @property
    def settle_countdown_secs(self) -> int:
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        return max(0, (self.next_funding_time_ms - now_ms) // 1000)

    @classmethod
    def from_binance(cls, data: dict) -> "FundingSnapshot":
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        return cls(
            exchange="binance",
            symbol=data["symbol"],
            funding_rate_raw=float(data["lastFundingRate"]),
            settle_interval_hours=8,
            next_funding_time_ms=int(data["nextFundingTime"]),
            instrument=data["symbol"],
            mark_price=float(data.get("markPrice")) if data.get("markPrice") else None,
            index_price=float(data.get("indexPrice")) if data.get("indexPrice") else None,
            captured_at_ms=now_ms,
        )

    @classmethod
    def from_bitget(cls, data: dict) -> "FundingSnapshot":
        raw_symbol = data.get("symbol", "")
        raw_funding = data.get("fundingRate") or data.get("fundingRate8h") or "0"
        next_time = data.get("nextSettleTime") or data.get("settleTime") or data.get("fundingTime")
        if next_time is None:
            next_funding_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000) + 8 * 3600 * 1000
        else:
            next_funding_ms = int(float(next_time))

        mark_price = data.get("markPrice")
        index_price = data.get("indexPrice")
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

        return cls(
            exchange="bitget",
            symbol=raw_symbol.split("_")[0],
            funding_rate_raw=float(raw_funding),
            settle_interval_hours=8,
            next_funding_time_ms=next_funding_ms,
            instrument=raw_symbol,
            mark_price=float(mark_price) if mark_price not in (None, "") else None,
            index_price=float(index_price) if index_price not in (None, "") else None,
            captured_at_ms=now_ms,
        )

    @classmethod
    def from_stream(cls, fields: Dict[str, str]) -> "FundingSnapshot":
        return cls(
            exchange=fields["exchange"],
            symbol=fields["symbol"],
            funding_rate_raw=float(fields["funding_rate_raw"]),
            settle_interval_hours=int(fields["settle_interval_hours"]),
            next_funding_time_ms=int(fields["next_funding_time_ms"]),
            instrument=fields.get("instrument"),
            mark_price=float(fields["mark_price"]) if fields.get("mark_price") not in (None, "", "None") else None,
            index_price=float(fields["index_price"]) if fields.get("index_price") not in (None, "", "None") else None,
            captured_at_ms=int(fields["captured_at_ms"]) if fields.get("captured_at_ms") else int(datetime.now(tz=timezone.utc).timestamp() * 1000),
        )
