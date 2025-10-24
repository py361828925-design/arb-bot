import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from fastapi.testclient import TestClient
from services.config_service.app import app

client = TestClient(app)

payload = {
    "global_enable": True,
    "thresholds": {
        "aa": 44.0,
        "bb": 44.0,
        "cc": 44.0,
        "dd": 44,
        "ee": 44.0,
        "ff": 44.0,
        "gg": 44.0,
        "hh": 44.0,
    },
    "risk_limits": {
        "group_max": 44,
        "duplicate_max": 44,
        "leverage_max": 44.0,
        "margin_per_leg": 445.0,
        "taker_fee": 44.0,
        "maker_fee": 44.0,
        "trade_fee": 0.04,
    },
    "scan_interval_seconds": 50.0,
    "close_interval_seconds": 55.0,
    "open_interval_seconds": 5.0,
}

response = client.put("/config/current", json=payload)
print("status", response.status_code)
print(json.dumps(response.json(), indent=2))
