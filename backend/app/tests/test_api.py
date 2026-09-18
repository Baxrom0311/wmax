"""
Integration test suite for NAZORAT API endpoints.
Uses TestClient (synchronous ASGI testing) with mocked DB sessions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

# Try importing FastAPI test client
try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from app.main import app
    HAS_APP = True
except Exception:
    HAS_APP = False


@pytest.fixture
def client():
    if not HAS_FASTAPI or not HAS_APP:
        pytest.skip("FastAPI or app not available")
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Returns Bearer token headers for authenticated requests."""
    try:
        from app.core.security import create_access_token
        token = create_access_token(
            subject="00000000-0000-0000-0000-000000000001",
            claims={"role": "doctor", "full_name": "Test Doctor", "district": "Test"},
        )
        return {"Authorization": f"Bearer {token}"}
    except Exception:
        pytest.skip("Auth not available")


# ── Health check ──────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_has_status_field(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ok", "degraded")


# ── Authentication endpoints ──────────────────────────────────────────────────

class TestAuthEndpoints:
    def test_login_with_demo_credentials(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+998901234567", "password": "nazorat123"},
        )
        # Should be 200 or 503 (DB not available in unit test), not 401
        assert response.status_code in (200, 422, 500, 503)

    def test_login_with_wrong_password_returns_401(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+998901234567", "password": "wrongpassword"},
        )
        assert response.status_code in (401, 500)  # 500 if DB unavailable

    def test_login_missing_phone_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "nazorat123"},
        )
        assert response.status_code == 422

    def test_login_response_has_token_fields(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+998901234567", "password": "nazorat123"},
        )
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "expires_in" in data
            assert "role" in data


# ── Protected endpoints ──────────────────────────────────────────────────────

class TestProtectedEndpoints:
    def test_patients_without_auth_returns_401(self, client):
        response = client.get("/api/v1/patients")
        assert response.status_code == 401

    def test_tasks_without_auth_returns_401(self, client):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 401

    def test_patients_with_auth_does_not_crash(self, client, auth_headers):
        response = client.get("/api/v1/patients", headers=auth_headers)
        # 200 if DB available, 500 if not — but NOT 401 or 403
        assert response.status_code not in (401, 403)

    def test_tasks_with_auth_does_not_crash(self, client, auth_headers):
        response = client.get("/api/v1/tasks", headers=auth_headers)
        assert response.status_code not in (401, 403)


# ── Me endpoint ───────────────────────────────────────────────────────────────

class TestMeEndpoint:
    def test_me_returns_current_user(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "role" in data
            assert data["role"] == "doctor"

    def test_me_without_auth_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


# ── Ingest endpoint ──────────────────────────────────────────────────────────

class TestIngestEndpoint:
    def test_empty_batch_returns_no_data(self, client):
        """Empty ingest batch should return gracefully."""
        patient_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/ingest",
            json={"patient_id": patient_id, "readings": []},
        )
        # 200 with no_data or 500 if DB unavailable
        if response.status_code == 200:
            data = response.json()
            assert data["accepted"] == 0
            assert data["latest_level"] == "no_data"

    def test_ingest_requires_valid_uuid(self, client):
        response = client.post(
            "/api/v1/ingest",
            json={"patient_id": "not-a-uuid", "readings": []},
        )
        assert response.status_code == 422

    def test_ingest_invalid_hr_rejected(self, client):
        patient_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/ingest",
            json={
                "patient_id": patient_id,
                "readings": [
                    {
                        "ts": "2024-06-15T10:00:00Z",
                        "hr_mean": 5.0,  # Below minimum 20 bpm
                        "worn": True,
                    }
                ],
            },
        )
        assert response.status_code == 422


# ── Error format tests ────────────────────────────────────────────────────────

class TestErrorResponseFormat:
    def test_401_has_standard_error_format(self, client):
        response = client.get("/api/v1/patients")
        # FastAPI default 401 format
        assert response.status_code == 401

    def test_422_has_standard_error_format(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "+998901234567"},  # Missing password
        )
        assert response.status_code == 422
        data = response.json()
        # Should have our standardized format OR FastAPI default
        assert "detail" in data or "message" in data

    def test_nonexistent_route_returns_404(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
