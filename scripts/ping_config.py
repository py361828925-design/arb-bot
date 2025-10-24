import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8003/config/current")
        print(response.status_code)
        print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
