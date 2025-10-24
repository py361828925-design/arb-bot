import json
import urllib.error
import urllib.request

def main() -> None:
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
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8003/config/current",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as response:
            print("Status:", response.status)
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print("HTTPError:", exc.code)
        print(exc.read().decode("utf-8", errors="ignore"))
    except Exception as exc:
        print("Error:", exc)


if __name__ == "__main__":
    main()
