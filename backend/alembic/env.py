"""Alembic async migration environment.

Run from the backend/ directory:
    alembic upgrade head
    alembic revision --autogenerate -m "describe change"

PYTHONPATH must include /srv, /srv/backend, /srv/contracts (set in Docker via
Dockerfile ENV / docker-compose). When running locally, the sys.path block below
adds the backend/ directory so that ``from app.models import ...`` resolves.
"""
from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# ---------------------------------------------------------------------------
# Ensure "backend/" is on sys.path so that app.* imports resolve when Alembic
# is invoked locally (e.g. ``alembic upgrade head`` from the backend/ dir).
# Inside the Docker container PYTHONPATH already contains /srv/backend.
# ---------------------------------------------------------------------------
_backend_dir = Path(__file__).resolve().parent.parent  # backend/
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# ---------------------------------------------------------------------------
# Import Base with all models registered on its metadata.
# app/db/base.py explicitly imports every model so that Base.metadata is full.
# ---------------------------------------------------------------------------
from app.db.base import (  # noqa: E402  (import after sys.path manipulation)
    Alert,
    Base,
    Baseline,
    Notification,
    Patient,
    Reading,
    RefreshToken,
    Relative,
    Task,
    User,
)

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that autogenerate inspects.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Database URL — read from environment; never hard-coded.
# The asyncpg URL form is:  postgresql+asyncpg://user:pass@host:port/db
# ---------------------------------------------------------------------------
def _get_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Export it before running alembic, e.g.: "
            "export DATABASE_URL=postgresql+asyncpg://nazorat:pass@localhost:5432/nazorat"
        )
    # Ensure the driver is asyncpg (alembic needs it for async runs).
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection required — emits SQL to stdout)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine; calls to
    context.execute() emit the SQL directly.
    """
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async, uses asyncpg connection pool)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a sync-compatible wrapper."""
    connectable = create_async_engine(
        _get_url(),
        poolclass=pool.NullPool,  # one connection per migration run, no pooling
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online mode; drives the asyncio event loop."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Alembic calls this module-level code to dispatch offline vs online.
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
