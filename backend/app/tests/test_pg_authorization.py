"""Authorization regressions against PostgreSQL: findings 2, 6 and 7 of
docs/REVIEW_2026-10-16.md. Requests go through the real FastAPI routes."""
from __future__ import annotations

import httpx
import pytest

from app.tests.pg_support import World, bearer, requires_pg, rollback_session

pytestmark = requires_pg


@pytest.fixture
async def ctx():
    from app.core.db import get_session
    from app.main import app

    async with rollback_session() as session:
        async def _session():
            yield session

        app.dependency_overrides[get_session] = _session
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield World(session), client
        app.dependency_overrides.pop(get_session, None)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_foreign_clinic_nurse_cannot_read_or_change_subscription(ctx):
    world, client = ctx
    clinic_a, clinic_b = await world.tenant("A"), await world.tenant("B")
    patient = await world.patient(clinic_a)
    nurse, _ = await world.member(clinic_b, "nurse", mahallas=("Navbahor",))
    token = bearer(nurse, "nurse", tenant_ids=[clinic_b.id])

    read = await client.get(f"/api/v1/patients/{patient.id}/subscription", headers=_auth(token))
    assert read.status_code in {403, 404}
    checkout = await client.post(
        f"/api/v1/patients/{patient.id}/subscription/checkout",
        json={"plan": "premium", "provider": "payme"},
        headers=_auth(token),
    )
    assert checkout.status_code in {403, 404}


async def test_doctor_role_in_one_clinic_does_not_apply_in_another(ctx):
    world, client = ctx
    clinic_a, clinic_b = await world.tenant("A"), await world.tenant("B")
    account, _ = await world.member(clinic_a, "doctor", mahallas=("Navbahor",))
    await world.member(clinic_b, "nurse", mahallas=("Navbahor",), account=account)
    patient_a = await world.patient(clinic_a)
    patient_b = await world.patient(clinic_b)
    # The signed token says "doctor" in both clinics; only clinic A's role counts.
    token = bearer(account, "doctor", tenant_ids=[clinic_a.id, clinic_b.id])

    denied = await client.post(f"/api/v1/patients/{patient_b.id}/baseline/approve", headers=_auth(token))
    assert denied.status_code in {403, 404}

    # Nurse-level read in clinic B still works.
    detail = await client.get(f"/api/v1/patients/{patient_b.id}/consents", headers=_auth(token))
    assert detail.status_code == 200

    allowed = await client.post(f"/api/v1/patients/{patient_a.id}/baseline/approve", headers=_auth(token))
    assert allowed.status_code not in {401, 403, 404}


async def test_demoted_or_removed_clinician_loses_access_before_token_expiry(ctx):
    from datetime import datetime, timezone

    world, client = ctx
    clinic = await world.tenant()
    account, member = await world.member(clinic, "doctor", mahallas=("Navbahor",))
    patient = await world.patient(clinic)
    token = bearer(account, "doctor", tenant_ids=[clinic.id])

    member.role = "nurse"
    await world.session.flush()
    demoted = await client.post(f"/api/v1/patients/{patient.id}/baseline/approve", headers=_auth(token))
    assert demoted.status_code == 403

    member.left_at = datetime.now(timezone.utc)
    await world.session.flush()
    removed = await client.get(f"/api/v1/patients/{patient.id}/consents", headers=_auth(token))
    assert removed.status_code == 401


async def test_refresh_recomputes_role_from_current_memberships(ctx):
    from app.auth.service import AuthService

    world, _client = ctx
    clinic = await world.tenant()
    account, member = await world.member(clinic, "doctor")
    service = AuthService(world.session)
    pair = await service._issue_token_pair(
        user_id=account.id, full_name=account.full_name, role="doctor", district=None, tenant_ids=[clinic.id],
    )
    member.role = "nurse"
    await world.session.flush()

    refreshed = await service.refresh_tokens(pair.refresh_token)
    assert refreshed.role == "nurse"


async def test_nurse_sees_only_patients_in_assigned_mahallas(ctx):
    world, client = ctx
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    head, _ = await world.member(clinic, "head_doctor")
    own = await world.patient(clinic, mahalla="Navbahor")
    other = await world.patient(clinic, mahalla="Gulshan")
    nurse_token = bearer(nurse, "nurse", tenant_ids=[clinic.id])

    worklist = await client.get("/api/v1/patients", headers=_auth(nurse_token))
    assert worklist.status_code == 200
    ids = {item["id"] for item in worklist.json()}
    assert str(own.id) in ids
    assert str(other.id) not in ids

    assert (await client.get(f"/api/v1/patients/{own.id}/consents", headers=_auth(nurse_token))).status_code == 200
    assert (await client.get(f"/api/v1/patients/{other.id}/consents", headers=_auth(nurse_token))).status_code in {403, 404}

    head_token = bearer(head, "doctor", tenant_ids=[clinic.id])
    head_ids = {item["id"] for item in (await client.get("/api/v1/patients", headers=_auth(head_token))).json()}
    assert {str(own.id), str(other.id)} <= head_ids


async def test_head_doctor_assigns_territory_and_nurse_then_sees_patient(ctx):
    world, client = ctx
    clinic = await world.tenant()
    head, _ = await world.member(clinic, "head_doctor")
    nurse, _ = await world.member(clinic, "nurse")
    patient = await world.patient(clinic, mahalla="Navbahor")
    nurse_token = bearer(nurse, "nurse", tenant_ids=[clinic.id])
    path = f"/api/v1/tenants/{clinic.id}/members/{nurse.id}/territories"

    # Nurses cannot widen their own scope.
    assert (await client.put(path, json={"mahallas": ["Navbahor"]}, headers=_auth(nurse_token))).status_code == 403
    assert (await client.get(f"/api/v1/patients/{patient.id}/consents", headers=_auth(nurse_token))).status_code in {403, 404}

    head_token = bearer(head, "doctor", tenant_ids=[clinic.id])
    put = await client.put(path, json={"mahallas": ["Navbahor", " "]}, headers=_auth(head_token))
    assert put.status_code == 200
    assert put.json() == {"mahallas": ["Navbahor"]}
    assert (await client.get(f"/api/v1/patients/{patient.id}/consents", headers=_auth(nurse_token))).status_code == 200


async def test_nurse_creates_patient_only_inside_own_mahalla(ctx):
    world, client = ctx
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    token = bearer(nurse, "nurse", tenant_ids=[clinic.id])

    outside = await client.post("/api/v1/patients", json={"full_name": "Synthetic X", "mahalla": "Gulshan"}, headers=_auth(token))
    assert outside.status_code == 422
    missing = await client.post("/api/v1/patients", json={"full_name": "Synthetic Y"}, headers=_auth(token))
    assert missing.status_code == 422

    created = await client.post("/api/v1/patients", json={"full_name": "Synthetic Z", "mahalla": "Navbahor"}, headers=_auth(token))
    assert created.status_code == 201
    patient_id = created.json()["id"]
    assert (await client.get(f"/api/v1/patients/{patient_id}/consents", headers=_auth(token))).status_code == 200
