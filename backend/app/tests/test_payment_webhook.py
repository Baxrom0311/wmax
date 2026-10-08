from __future__ import annotations

import hashlib
import hmac
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AuthenticationException, ValidationException
from app.models import Invoice, PatientSubscription, Payment
from app.services.payment_webhook_service import PaymentWebhookService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _execute_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_payment_webhook_records_payment_and_marks_invoice_paid(mock_session):
    invoice_id = uuid.uuid4()
    invoice = Invoice(
        id=invoice_id,
        tenant_id=uuid.uuid4(),
        period_start="2026-09-01",
        period_end="2026-09-30",
        patient_days_total=30,
        patient_days_with_data=28,
        min_commitment=30,
        billed_days=30,
        amount_uzs=85000,
        status="open",
    )
    mock_session.execute.return_value = _execute_result(None)
    mock_session.get = AsyncMock(return_value=invoice)

    result = await PaymentWebhookService(mock_session).record(
        provider="payme",
        payload={
            "invoice_id": str(invoice_id),
            "provider_ref": "txn-1",
            "amount_uzs": 85000,
            "status": "succeeded",
        },
    )

    assert result["duplicate"] is False
    assert invoice.status == "paid"
    assert invoice.paid_at is not None
    added = mock_session.add.call_args.args[0]
    assert isinstance(added, Payment)
    assert added.provider_ref == "txn-1"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_payment_webhook_is_idempotent_for_duplicate_provider_ref(mock_session):
    existing = Payment(
        id=uuid.uuid4(),
        provider="payme",
        provider_ref="txn-1",
        amount_uzs=1000,
        status="succeeded",
    )
    mock_session.execute.return_value = _execute_result(existing)

    result = await PaymentWebhookService(mock_session).record(
        provider="payme",
        payload={"provider_ref": "txn-1", "amount_uzs": 1000, "status": "succeeded"},
    )

    assert result["duplicate"] is True
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_payment_webhook_requires_provider_ref(mock_session):
    with pytest.raises(ValidationException):
        await PaymentWebhookService(mock_session).record(provider="payme", payload={})


@pytest.mark.asyncio
async def test_payment_webhook_rejects_invoice_amount_mismatch(mock_session):
    invoice = Invoice(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), period_start="2026-09-01",
        period_end="2026-09-30", patient_days_total=30, patient_days_with_data=30,
        min_commitment=30, billed_days=30, amount_uzs=85000, status="open",
    )
    mock_session.execute.return_value = _execute_result(None)
    mock_session.get = AsyncMock(return_value=invoice)
    with pytest.raises(ValidationException, match="invoice summasiga mos emas"):
        await PaymentWebhookService(mock_session).record(
            provider="payme",
            payload={
                "provider_ref": "txn-mismatch",
                "invoice_id": str(invoice.id),
                "amount_uzs": 1,
                "status": "paid",
            },
        )
    assert invoice.status == "open"
    mock_session.commit.assert_not_awaited()


def test_payment_webhook_signature_validation(monkeypatch, mock_session):
    monkeypatch.setattr("app.services.payment_webhook_service.settings.PAYMENT_WEBHOOK_SECRET", "secret")
    body = b'{"provider_ref":"txn-1"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    service = PaymentWebhookService(mock_session)
    service.verify_signature(body=body, signature=signature)

    with pytest.raises(AuthenticationException):
        service.verify_signature(body=body, signature="wrong")


@pytest.mark.asyncio
async def test_payment_webhook_activates_patient_subscription(mock_session):
    subscription_id = uuid.uuid4()
    subscription = PatientSubscription(
        id=subscription_id,
        patient_id=uuid.uuid4(),
        plan="premium",
        status="past_due",
    )
    mock_session.execute.return_value = _execute_result(None)
    mock_session.get = AsyncMock(return_value=subscription)

    await PaymentWebhookService(mock_session).record(
        provider="payme",
        payload={
            "patient_subscription_id": str(subscription_id),
            "provider_ref": "txn-sub-1",
            "amount_uzs": 59000,
            "status": "succeeded",
        },
    )

    assert subscription.status == "active"
    assert subscription.period_end is not None
    assert subscription.provider_ref == "txn-sub-1"


@pytest.mark.asyncio
async def test_payment_webhook_pending_transition_to_paid(mock_session):
    invoice_id = uuid.uuid4()
    invoice = Invoice(
        id=invoice_id,
        tenant_id=uuid.uuid4(),
        period_start="2026-09-01",
        period_end="2026-09-30",
        patient_days_total=30,
        patient_days_with_data=28,
        min_commitment=30,
        billed_days=30,
        amount_uzs=50000,
        status="open",
    )
    existing_pending = Payment(
        id=123,
        invoice_id=invoice_id,
        provider="payme",
        provider_ref="txn-pending-1",
        amount_uzs=50000,
        status="pending",
    )
    mock_session.execute.return_value = _execute_result(existing_pending)
    mock_session.get = AsyncMock(return_value=invoice)

    result = await PaymentWebhookService(mock_session).record(
        provider="payme",
        payload={
            "invoice_id": str(invoice_id),
            "provider_ref": "txn-pending-1",
            "amount_uzs": 50000,
            "status": "paid",
        },
    )

    assert result["duplicate"] is False
    assert existing_pending.status == "paid"
    assert invoice.status == "paid"
