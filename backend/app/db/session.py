from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session, get_sessionmaker


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for programmatic async transactions with automatic commit/rollback."""
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = ["get_session", "get_db_context"]
