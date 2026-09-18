from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        try:
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_pre_ping=True,
                future=True,
            )
            logger.info("Initialized PostgreSQL async engine with connection pooling")
        except Exception as e:
            logger.warning(
                f"Failed to create PostgreSQL engine ({e}), falling back to SQLite in-memory for testing"
            )
            try:
                _engine = create_async_engine(
                    "sqlite+aiosqlite:///:memory:", echo=False, future=True
                )
            except Exception:
                _engine = create_async_engine(
                    "sqlite:///:memory:", echo=False, future=True
                )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def check_db_connection() -> bool:
    """Verifies that the database connection pool is alive."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            return res.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
