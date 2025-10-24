from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CloseDecision(BaseModel):
    group_id: str
    symbol: str
    reason: str
    triggered_at: datetime
    notes: Optional[str] = None
