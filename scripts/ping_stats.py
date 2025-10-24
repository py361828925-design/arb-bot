import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:8006/stats/dynamic")
        print(resp.status_code)
        print(resp.text)


if __name__ == "__main__":
    asyncio.run(main())
