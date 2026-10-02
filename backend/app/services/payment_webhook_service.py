from __future__ import annotations

import hashlib
import hmac
import inspect
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ValidationException
from datetime import timedelta

from app.models import Invoice, PatientSubscription, Payment


PAID_STATUSES = {"paid", "succeeded", "success", "completed", "captured"}


class PaymentWebhookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def verify_signature(self, *, body: bytes, signature: str | None) -> None:
        secret = settings.PAYMENT_WEBHOOK_SECRET
        if not secret:
            return
        expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(expected, signature):
            raise AuthenticationException("Payment webhook imzosi noto'g'ri")

    async def record(self, *, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        provider_ref = self._provider_ref(payload)
        if not provider_ref:
            raise ValidationException("Webhook payload ichida provider_ref yo'q")

        existing = (
            await self.session.execute(
                select(Payment).where(
                    Payment.provider == provider,
                    Payment.provider_ref == provider_ref,
                )
            )
        ).scalar_one_or_none()
        if existing:
            return {
                "received": True,
                "provider": provider,
                "payment_id": str(existing.id),
                "duplicate": True,
            }

        invoice_id = self._optional_uuid(payload.get("invoice_id"))
        patient_subscription_id = self._optional_uuid(payload.get("patient_subscription_id"))
        status = str(payload.get("status") or "received").lower()
        payment = Payment(
            invoice_id=invoice_id,
            patient_subscription_id=patient_subscription_id,
            provider=provider,
            provider_ref=provider_ref,
            amount_uzs=int(payload.get("amount_uzs") or payload.get("amount") or 0),
            status=status,
            raw_payload=payload,
        )
        added = self.session.add(payment)
        if inspect.isawaitable(added):
            await added

        if invoice_id and status in PAID_STATUSES:
            invoice = await self.session.get(Invoice, invoice_id)
            if invoice:
                invoice.status = "paid"
                invoice.paid_at = datetime.now(timezone.utc)
        if patient_subscription_id and status in PAID_STATUSES:
            subscription = await self.session.get(PatientSubscription, patient_subscription_id)
            if subscription:
                subscription.status = "active"
                subscription.period_end = datetime.now(timezone.utc) + timedelta(days=30)
                subscription.provider = provider
                subscription.provider_ref = provider_ref

        await self.session.flush()
        await self.session.commit()
        return {
            "received": True,
            "provider": provider,
            "payment_id": str(payment.id),
            "duplicate": False,
        }

    def _provider_ref(self, payload: dict[str, Any]) -> str:
        value = payload.get("provider_ref") or payload.get("transaction_id") or payload.get("id")
        return str(value or "").strip()

    def _optional_uuid(self, value: object) -> uuid.UUID | None:
        if value in (None, ""):
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError as exc:
            raise ValidationException("invoice_id UUID formatida bo'lishi kerak") from exc
