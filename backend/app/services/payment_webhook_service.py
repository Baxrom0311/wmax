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
SUPPORTED_PROVIDERS = {"payme", "click", "uzum", "stripe"}


class PaymentWebhookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def verify_signature(self, *, body: bytes, signature: str | None) -> None:
        secret = settings.PAYMENT_WEBHOOK_SECRET
        if not secret:
            raise AuthenticationException("Payment webhook secret sozlanmagan")
        if not signature:
            raise AuthenticationException("Payment webhook imzosi yo'q")
        expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise AuthenticationException("Payment webhook imzosi noto'g'ri")

    async def record(self, *, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        provider = provider.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise ValidationException("Payment provider qo'llab-quvvatlanmaydi")
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
        status = str(payload.get("status") or "received").lower()
        if status not in PAID_STATUSES | {"received", "pending", "created", "processing", "failed", "cancelled", "refunded"}:
            raise ValidationException("Payment status qo'llab-quvvatlanmaydi")
        currency = str(payload.get("currency") or "UZS").upper()
        if currency != "UZS":
            raise ValidationException("Faqat UZS to'lovlari qabul qilinadi")
        amount = payload.get("amount_uzs", payload.get("amount"))
        try:
            amount_uzs = int(amount)
        except (TypeError, ValueError) as exc:
            raise ValidationException("Webhook amount_uzs butun son bo'lishi kerak") from exc
        if amount_uzs <= 0:
            raise ValidationException("To'lov summasi musbat bo'lishi kerak")
        if existing:
            if existing.amount_uzs != amount_uzs:
                raise ValidationException("Provider transaction summasi o'zgargan")
            if existing.status in PAID_STATUSES or status not in PAID_STATUSES:
                return {
                    "received": True,
                    "provider": provider,
                    "payment_id": str(existing.id),
                    "duplicate": True,
                }
            # Transition existing pending payment to paid
            existing.status = status
            existing.raw_payload = payload
            payment = existing
            invoice_id = existing.invoice_id or self._optional_uuid(payload.get("invoice_id"))
            patient_subscription_id = existing.patient_subscription_id or self._optional_uuid(payload.get("patient_subscription_id"))
        else:
            invoice_id = self._optional_uuid(payload.get("invoice_id"))
            patient_subscription_id = self._optional_uuid(payload.get("patient_subscription_id"))
            if (invoice_id is None) == (patient_subscription_id is None):
                raise ValidationException("To'lov aynan bitta invoice yoki subscription bilan bog'lanishi kerak")
            payment = Payment(
                invoice_id=invoice_id,
                patient_subscription_id=patient_subscription_id,
                provider=provider,
                provider_ref=provider_ref,
                amount_uzs=amount_uzs,
                status=status,
                raw_payload=payload,
            )
            added = self.session.add(payment)
            if inspect.isawaitable(added):
                await added

        if invoice_id and status in PAID_STATUSES:
            invoice = await self.session.get(Invoice, invoice_id)
            if not invoice:
                raise ValidationException("Invoice topilmadi")
            if invoice.amount_uzs != amount_uzs:
                raise ValidationException("To'lov summasi invoice summasiga mos emas")
            invoice.status = "paid"
            invoice.paid_at = datetime.now(timezone.utc)
        if patient_subscription_id and status in PAID_STATUSES:
            subscription = await self.session.get(PatientSubscription, patient_subscription_id)
            if not subscription:
                raise ValidationException("Patient subscription topilmadi")
            from app.billing.entitlements import PLAN_DETAILS
            expected_amount = PLAN_DETAILS.get(subscription.plan, {}).get("price_uzs")
            if expected_amount is None or expected_amount != amount_uzs:
                raise ValidationException("To'lov summasi tarif narxiga mos emas")
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
