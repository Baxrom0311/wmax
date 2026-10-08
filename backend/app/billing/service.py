from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.entitlements import PLAN_DETAILS
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.tenant import Tenant

PATIENT_PLANS = {"free", "premium", "premium_doc"}


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_tenant_for_user(
        self,
        user_id: uuid.UUID,
        phone: str,
        name: str = "Oilaviy Kabinet",
        kind: str = "household",
    ) -> Tenant:
        """Finds or creates a clinic tenant during the transition to patient billing."""
        stmt = select(Tenant).where(Tenant.name == name)
        res = await self.session.execute(stmt)
        tenant = res.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                name=name,
                kind=kind if kind in {"ovabmu", "polyclinic", "hospital", "network"} else "polyclinic",
                region="Xorazm",
                district="Urganch",
                is_active=True,
            )
            added = self.session.add(tenant)
            if inspect.isawaitable(added):
                await added
            await self.session.flush()

        return tenant

    async def get_subscription(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        return await self.get_patient_subscription(tenant_id)

    async def get_patient_subscription(self, patient_id: uuid.UUID) -> dict[str, Any]:
        """Returns subscription details and active feature entitlements."""
        stmt = select(Subscription).where(Subscription.patient_id == patient_id)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        if not sub:
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=14)
            sub = Subscription(
                patient_id=patient_id,
                plan="free",
                status="trialing",
                trial_ends_at=trial_end,
                period_end=None,
            )
            added = self.session.add(sub)
            if inspect.isawaitable(added):
                await added
            await self.session.flush()

        plan_meta = PLAN_DETAILS.get(sub.plan, PLAN_DETAILS["free"])
        now = datetime.now(timezone.utc)
        trial_days_left = 0
        if sub.trial_ends_at and sub.status == "trialing":
            delta = sub.trial_ends_at - now
            trial_days_left = max(0, delta.days)

        return {
            "subscription_id": str(sub.id),
            "patient_id": str(sub.patient_id),
            "plan": sub.plan,
            "plan_name": plan_meta["name"],
            "status": sub.status,
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "trial_days_left": trial_days_left,
            "current_period_end": sub.period_end.isoformat() if sub.period_end else None,
            "seats_included": 1,
            "price_uzs": plan_meta["price_uzs"],
            "features": plan_meta["features"],
            "is_trial": sub.status == "trialing",
            "is_active": sub.status in ("trialing", "active"),
        }

    async def upgrade_plan(
        self,
        tenant_id: uuid.UUID,
        new_plan: str,
        provider: str = "payme",
        card_token: str | None = None,
    ) -> dict[str, Any]:
        return await self.upgrade_patient_plan(
            patient_id=tenant_id,
            new_plan=new_plan,
            provider=provider,
            card_token=card_token,
        )

    async def upgrade_patient_plan(
        self,
        patient_id: uuid.UUID,
        new_plan: str,
        provider: str = "payme",
        card_token: str | None = None,
    ) -> dict[str, Any]:
        """Upgrades or changes subscription plan."""
        if new_plan not in PLAN_DETAILS:
            raise ValueError(f"Noto'g'ri tarif kodi: {new_plan}")
        if new_plan not in PATIENT_PLANS:
            raise ValueError("clinic tarifi tenant licence orqali rasmiylashtiriladi")

        stmt = select(Subscription).where(Subscription.patient_id == patient_id)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        plan_meta = PLAN_DETAILS[new_plan]

        if not sub:
            sub = Subscription(
                patient_id=patient_id,
                plan=new_plan,
                status="past_due" if new_plan != "free" else "trialing",
                period_end=None,
                provider=provider,
            )
            self.session.add(sub)
        else:
            sub.plan = new_plan
            sub.status = "past_due" if new_plan != "free" else "trialing"
            sub.period_end = None
            sub.provider = provider

        await self.session.flush()

        if plan_meta["price_uzs"] > 0:
            payment = Payment(
                patient_subscription_id=sub.id,
                provider=provider,
                provider_ref=f"checkout_{uuid.uuid4().hex[:12]}",
                amount_uzs=plan_meta["price_uzs"],
                status="pending",
                raw_payload={"plan": new_plan, "timestamp": now.isoformat()},
            )
            added = self.session.add(payment)
            if inspect.isawaitable(added):
                await added
            await self.session.flush()

        await self.session.commit()
        result = await self.get_patient_subscription(patient_id)
        result["checkout_required"] = plan_meta["price_uzs"] > 0
        return result

    async def list_invoices(self, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        """Returns billing invoices history for tenant."""
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id).order_by(Invoice.issued_at.desc())
        res = await self.session.execute(stmt)
        invoices = res.scalars().all()
        return [
            {
                "id": str(inv.id),
                "period_start": inv.period_start.isoformat(),
                "period_end": inv.period_end.isoformat(),
                "active_patients": inv.patient_days_total,
                "amount_uzs": inv.amount_uzs,
                "status": inv.status,
                "due_at": inv.issued_at.isoformat(),
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "created_at": inv.issued_at.isoformat(),
            }
            for inv in invoices
        ]
