from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel


class Opportunity(BaseModel):
    group_id: str
    symbol: str
    long_exchange: str
    short_exchange: str
    funding_diff: float
    expected_rate8h: float
    created_at: datetime

    @classmethod
    def create(
        cls,
        symbol: str,
        long_exchange: str,
        short_exchange: str,
        funding_diff: float,
        expected_rate8h: float,
    ) -> "Opportunity":
        now = datetime.now(timezone.utc)
        return cls(
            group_id=f"{symbol}-{now.strftime('%Y%m%d%H%M%S')}",
            symbol=symbol,
            long_exchange=long_exchange,
            short_exchange=short_exchange,
            funding_diff=funding_diff,
            expected_rate8h=expected_rate8h,
            created_at=now,
        )

    def to_stream_fields(self) -> Dict[str, str]:
        return {
            "group_id": self.group_id,
            "symbol": self.symbol,
            "long_exchange": self.long_exchange,
            "short_exchange": self.short_exchange,
            "funding_diff": f"{self.funding_diff}",
            "expected_rate8h": f"{self.expected_rate8h}",
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_stream(cls, fields: Dict[str, str]) -> "Opportunity":
        return cls(
            group_id=fields["group_id"],
            symbol=fields["symbol"],
            long_exchange=fields["long_exchange"],
            short_exchange=fields["short_exchange"],
            funding_diff=float(fields["funding_diff"]),
            expected_rate8h=float(fields["expected_rate8h"]),
            created_at=datetime.fromisoformat(fields["created_at"]),
        )
