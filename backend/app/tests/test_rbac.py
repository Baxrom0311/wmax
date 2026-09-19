import uuid
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.deps import (
    get_current_principal,
    get_current_relative,
    get_current_user,
    require_doctor,
    require_clinician,
)
from app.core.security import create_access_token


def _cred(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_relative_token_rejected_on_clinician_endpoints():
    rel_token = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "relative", "full_name": "Qarovchi Farzand"},
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=_cred(rel_token))
    # F2 + F3: A caregiver token must NEVER pass get_current_user
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_nurse_cannot_discharge_patient():
    nurse_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "nurse", "full_name": "Hamshira Dilnoza"},
    )
    nurse_user = await get_current_user(credentials=_cred(nurse_tok))
    assert nurse_user.role == "nurse"

    # require_doctor dependency must reject nurse
    with pytest.raises(HTTPException) as exc:
        await require_doctor(current_user=nurse_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_doctor_can_discharge_patient():
    doc_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "doctor", "full_name": "Dr. Bahrom"},
    )
    doc_user = await get_current_user(credentials=_cred(doc_tok))
    assert doc_user.role == "doctor"

    # require_doctor allows doctor
    res = await require_doctor(current_user=doc_user)
    assert res.role == "doctor"


@pytest.mark.asyncio
async def test_nurse_can_access_clinician_endpoints():
    nurse_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "nurse", "full_name": "Hamshira Dilnoza"},
    )
    nurse_user = await get_current_user(credentials=_cred(nurse_tok))
    res = await require_clinician(current_user=nurse_user)
    assert res.role == "nurse"


@pytest.mark.asyncio
async def test_caregiver_endpoint_requires_relative_role():
    doc_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "doctor", "full_name": "Dr. Bahrom"},
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_relative(credentials=_cred(doc_tok))
    assert exc.value.status_code == 403

    rel_tok = create_access_token(
        subject=str(uuid.uuid4()),
        claims={"role": "relative", "full_name": "Qarovchi"},
    )
    rel_user = await get_current_relative(credentials=_cred(rel_tok))
    assert rel_user.role == "relative"
