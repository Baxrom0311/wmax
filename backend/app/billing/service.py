from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.entitlements import PLAN_DETAILS, Feature, check_entitlement, is_entitled
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.tenant import Tenant


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
        """Finds or creates a default tenant for a user or household."""
        stmt = select(Tenant).where(Tenant.owner_phone == phone)
        res = await self.session.execute(stmt)
        tenant = res.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                name=name,
                kind=kind,
                owner_phone=phone,
                region="Xorazm",
                is_active=True,
            )
            self.session.add(tenant)
            await self.session.flush()

            # Create default 14-day trial subscription
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=14)
            sub = Subscription(
                tenant_id=tenant.id,
                plan="premium",  # 14-day trial gives full Premium access
                status="trialing",
                trial_ends_at=trial_end,
                current_period_end=trial_end,
                seats_included=1,
            )
            self.session.add(sub)
            await self.session.flush()

        return tenant

    async def get_subscription(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """Returns subscription details and active feature entitlements."""
        stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        if not sub:
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=14)
            sub = Subscription(
                tenant_id=tenant_id,
                plan="free",
                status="free",
                trial_ends_at=trial_end,
                current_period_end=None,
                seats_included=1,
            )
            self.session.add(sub)
            await self.session.flush()

        plan_meta = PLAN_DETAILS.get(sub.plan, PLAN_DETAILS["free"])
        now = datetime.now(timezone.utc)
        trial_days_left = 0
        if sub.trial_ends_at and sub.status == "trialing":
            delta = sub.trial_ends_at - now
            trial_days_left = max(0, delta.days)

        return {
            "subscription_id": str(sub.id),
            "tenant_id": str(sub.tenant_id),
            "plan": sub.plan,
            "plan_name": plan_meta["name"],
            "status": sub.status,
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "trial_days_left": trial_days_left,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "seats_included": sub.seats_included,
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
        """Upgrades or changes subscription plan."""
        if new_plan not in PLAN_DETAILS:
            raise ValueError(f"Noto'g'ri tarif kodi: {new_plan}")

        stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        plan_meta = PLAN_DETAILS[new_plan]

        if not sub:
            sub = Subscription(
                tenant_id=tenant_id,
                plan=new_plan,
                status="active" if new_plan != "free" else "free",
                current_period_end=now + timedelta(days=30) if new_plan != "free" else None,
                provider=provider,
                card_token=card_token,
            )
            self.session.add(sub)
        else:
            sub.plan = new_plan
            sub.status = "active" if new_plan != "free" else "free"
            sub.current_period_end = now + timedelta(days=30) if new_plan != "free" else None
            sub.provider = provider
            if card_token:
                sub.card_token = card_token

        await self.session.flush()

        # Generate invoice if paid
        if plan_meta["price_uzs"] > 0:
            today = date.today()
            invoice = Invoice(
                tenant_id=tenant_id,
                period_start=today,
                period_end=today + timedelta(days=30),
                active_patients=sub.seats_included,
                amount_uzs=plan_meta["price_uzs"],
                status="paid",
                due_at=now,
                paid_at=now,
            )
            self.session.add(invoice)
            await self.session.flush()

            # Record payment transaction
            payment = Payment(
                invoice_id=invoice.id,
                provider=provider,
                provider_txn=f"txn_{uuid.uuid4().hex[:12]}",
                amount_uzs=plan_meta["price_uzs"],
                status="succeeded",
                raw_payload={"plan": new_plan, "timestamp": now.isoformat()},
            )
            self.session.add(payment)
            await self.session.flush()

        await self.session.commit()
        return await self.get_subscription(tenant_id)

    async def list_invoices(self, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        """Returns billing invoices history for tenant."""
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id).order_by(Invoice.created_at.desc())
        res = await self.session.execute(stmt)
        invoices = res.scalars().all()
        return [
            {
                "id": str(inv.id),
                "period_start": inv.period_start.isoformat(),
                "period_end": inv.period_end.isoformat(),
                "active_patients": inv.active_patients,
                "amount_uzs": inv.amount_uzs,
                "status": inv.status,
                "due_at": inv.due_at.isoformat(),
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "created_at": inv.created_at.isoformat(),
            }
            for inv in invoices
        ]
