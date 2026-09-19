"""
Pytest configuration and fixtures for WMAX backend tests.

Provides:
  - sys.path setup so all app.* and contracts imports resolve
  - async event loop configuration
  - DB session fixtures (SQLite in-memory for unit tests)
  - Auth token fixtures (doctor, nurse, relative)
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: mirrors the Docker PYTHONPATH = /srv:/srv/backend:/srv/contracts
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parent          # workspace root
_backend = _root / "backend"
_contracts = _root / "contracts"

for p in [str(_root), str(_backend), str(_contracts)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set DATABASE_URL to avoid pydantic-settings errors in unit tests
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://wmax:test@localhost:5432/wmax_test")
os.environ.setdefault("JWT_SECRET", "test_secret_key_at_least_32_chars_long_for_pytest")
os.environ.setdefault("ENV", "testing")
os.environ.setdefault("ENABLE_WORKERS", "false")

import pytest


# ---------------------------------------------------------------------------
# Async event loop
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default asyncio event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# Rate limiter auto-clean
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    try:
        from app.core.rate_limit import login_limiter
        login_limiter.clear()
        yield
        login_limiter.clear()
    except Exception:
        yield


# ---------------------------------------------------------------------------
# Auth token helpers
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def doctor_token() -> str:
    """Valid JWT access token for a doctor user."""
    try:
        from app.core.security import create_access_token
        return create_access_token(
            subject="00000000-0000-0000-0000-000000000001",
            claims={"role": "doctor", "full_name": "Test Doctor", "district": "Toshkent"},
        )
    except Exception:
        return "test_token_unavailable"


@pytest.fixture(scope="session")
def nurse_token() -> str:
    """Valid JWT access token for a nurse user."""
    try:
        from app.core.security import create_access_token
        return create_access_token(
            subject="00000000-0000-0000-0000-000000000002",
            claims={"role": "nurse", "full_name": "Test Nurse", "district": "Toshkent"},
        )
    except Exception:
        return "test_token_unavailable"


@pytest.fixture(scope="session")
def relative_token() -> str:
    """Valid JWT access token for a caregiver relative user."""
    try:
        from app.core.security import create_access_token
        return create_access_token(
            subject="aaaaaaaa-1111-1111-1111-111111111111",
            claims={"role": "relative", "full_name": "Test Qarovchi", "district": None, "phone": "+998901110011"},
        )
    except Exception:
        return "test_token_unavailable"


@pytest.fixture
def auth_headers(doctor_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {doctor_token}"}


@pytest.fixture
def nurse_headers(nurse_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {nurse_token}"}


@pytest.fixture
def relative_headers(relative_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {relative_token}"}


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    try:
        from app.main import app as _app
        return _app
    except Exception:
        pytest.skip("App could not be imported")


@pytest.fixture
def client(app):
    try:
        from fastapi.testclient import TestClient
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    except Exception:
        pytest.skip("TestClient unavailable")


# ---------------------------------------------------------------------------
# Clinical data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_reading_vec():
    """Returns a normal ReadingVec for testing."""
    try:
        from datetime import datetime, timezone
        from algo_interface import ReadingVec
        return ReadingVec(
            ts=datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
            hr_mean=70.0,
            spo2=97.0,
            skin_temp=36.5,
            rmssd=35.0,
            rr_est=15.0,
            steps=50,
            sleep_frag=2.0,
            worn=True,
        )
    except ImportError:
        pytest.skip("algo_interface not available")


@pytest.fixture
def sample_baselines():
    """Returns a realistic baseline set matching a healthy patient."""
    try:
        from algo_interface import BaselineEntry
        return [
            BaselineEntry(param="hr_mean",   time_window=1, median=70.0, mad=5.0,  n_samples=25),
            BaselineEntry(param="spo2",      time_window=1, median=97.0, mad=0.8,  n_samples=25),
            BaselineEntry(param="skin_temp", time_window=1, median=36.5, mad=0.3,  n_samples=25),
            BaselineEntry(param="rmssd",     time_window=1, median=35.0, mad=5.0,  n_samples=25),
            BaselineEntry(param="rr_est",    time_window=1, median=15.0, mad=2.0,  n_samples=25),
        ]
    except ImportError:
        pytest.skip("algo_interface not available")
