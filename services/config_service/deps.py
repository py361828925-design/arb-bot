from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import get_session as _db_get_session


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in _db_get_session():
        yield session
