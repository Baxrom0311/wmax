from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.billing.entitlements import (
    Feature,
    PLAN_DETAILS,
    check_entitlement,
    is_entitled,
)
from app.billing.service import BillingService
from app.models.subscription import Subscription
from app.models.tenant import Tenant


def test_safety_features_never_blocked():
    """R4: Critical alerts and SOS must never be behind paywalls."""
    assert is_entitled("free", Feature.CRITICAL_ALERT) is True
    assert is_entitled("free", Feature.SOS_BUTTON) is True
    assert is_entitled("free", Feature.STATUS_COLOR) is True
    assert is_entitled("free", Feature.VITALS) is True


def test_premium_features_restricted_on_free():
    """Advanced analytics require Premium."""
    assert is_entitled("free", Feature.AI_PROGNOSIS) is False
    assert is_entitled("free", Feature.MEDICATION_RESPONSE) is False
    assert is_entitled("free", Feature.UNLIMITED_HISTORY) is False
    assert is_entitled("free", Feature.PDF_REPORT) is False

    assert is_entitled("premium", Feature.AI_PROGNOSIS) is True
    assert is_entitled("premium", Feature.PDF_REPORT) is True


def test_doctor_on_call_feature_restricted():
    """On-call doctor is exclusive to premium_doc tier."""
    assert is_entitled("free", Feature.ON_CALL_DOCTOR) is False
    assert is_entitled("premium", Feature.ON_CALL_DOCTOR) is False
    assert is_entitled("premium_doc", Feature.ON_CALL_DOCTOR) is True


def test_check_entitlement_raises_402():
    with pytest.raises(HTTPException) as exc_info:
        check_entitlement("free", Feature.AI_PROGNOSIS)
    assert exc_info.value.status_code == 402


def test_plan_pricing_structure():
    assert PLAN_DETAILS["free"]["price_uzs"] == 0
    assert PLAN_DETAILS["premium"]["price_uzs"] == 59_000
    assert PLAN_DETAILS["premium_doc"]["price_uzs"] == 249_000
    assert PLAN_DETAILS["clinic"]["price_uzs"] == 85_000


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_billing_get_or_create_tenant_with_trial(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    service = BillingService(mock_session)
    user_id = uuid.uuid4()
    tenant = await service.get_or_create_tenant_for_user(
        user_id=user_id,
        phone="+998901234567",
        name="Test Household",
    )

    assert tenant.name == "Test Household"
    assert tenant.owner_phone == "+998901234567"
    assert mock_session.add.call_count >= 2  # tenant + subscription
    assert mock_session.flush.await_count >= 2


@pytest.mark.asyncio
async def test_billing_upgrade_plan_creates_invoice(mock_session):
    tenant_id = uuid.uuid4()
    existing_sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        plan="free",
        status="free",
        seats_included=1,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_session.execute.return_value = mock_result

    service = BillingService(mock_session)
    updated = await service.upgrade_plan(
        tenant_id=tenant_id,
        new_plan="premium",
        provider="payme",
    )

    assert updated["plan"] == "premium"
    assert updated["price_uzs"] == 59_000
    assert mock_session.commit.await_count >= 1
