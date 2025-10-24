import asyncio
import httpx

BINANCE_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"
BITGET_URL = "https://api.bitget.com/api/v2/mix/market/current-fund-rate"

async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("Checking Binance funding endpoint...")
        try:
            resp = await client.get(BINANCE_URL, params={"symbol": "BTCUSDT"})
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                print(f"  status={resp.status_code}, items={len(data)}")
                if data:
                    first = data[0]
                    print(
                        "  first symbol=", first.get("symbol"),
                        "rate=", first.get("lastFundingRate"),
                        "nextFundingTime=", first.get("nextFundingTime"),
                    )
            elif isinstance(data, dict):
                print(
                    f"  status={resp.status_code}, symbol={data.get('symbol')} rate={data.get('lastFundingRate')}"
                )
            else:
                print(f"  status={resp.status_code}, unexpected payload type={type(data)!r}")
        except Exception as exc:
            print("  Binance error:", exc)

        print("Checking Bitget funding endpoint...")
        try:
            resp = await client.get(
                BITGET_URL,
                params={"symbol": "BTCUSDT", "productType": "USDT-FUTURES"},
            )
            resp.raise_for_status()
            data = resp.json()
            entries = data.get("data") or []
            print(f"  status={resp.status_code}, entries={len(entries)}")
            if entries:
                first = entries[0]
                print(
                    "  first symbol=", first.get("symbol"),
                    "rate=", first.get("fundingRate"),
                    "nextUpdate=", first.get("nextUpdate"),
                )
        except Exception as exc:
            print("  Bitget error:", exc)

if __name__ == "__main__":
    asyncio.run(main())
