from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_principal, require_clinician
from app.billing.entitlements import PLAN_DETAILS
from app.billing.service import BillingService
from app.core.db import get_session
from app.core.exceptions import ForbiddenException
from app.models import BillingDay, Invoice, TenantLicence
from app.services.payment_webhook_service import PaymentWebhookService

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
contract_router = APIRouter(prefix="/api/v1", tags=["billing"])


class SubscribeRequest(BaseModel):
    plan: str = Field(..., description="Plan code: free | premium | premium_doc | clinic")
    provider: str = Field("payme", description="Payment provider: payme | click | uzum | stripe")
    card_token: str | None = Field(None, description="Optional card token for recurrent billing")


class PayInvoiceRequest(BaseModel):
    invoice_id: uuid.UUID
    provider: str = "payme"
    provider_txn: str | None = None


def _assert_patient_billing_scope(current_user: CurrentUser, patient_id: uuid.UUID) -> None:
    if current_user.role == "patient" and current_user.id != patient_id:
        raise ForbiddenException("Boshqa bemorning obunasini ko'rish mumkin emas")
    if current_user.role == "relative" and patient_id not in current_user.patient_ids:
        raise ForbiddenException("Bu bemor obunasiga ruxsat yo'q")


def _assert_tenant_billing_scope(current_user: CurrentUser, tenant_id: uuid.UUID) -> None:
    if current_user.role not in {"doctor", "nurse", "admin", "dispatcher"}:
        raise ForbiddenException("Klinika billing ma'lumotlariga ruxsat yo'q")
    if tenant_id not in current_user.tenant_ids:
        raise ForbiddenException("Bu klinika billing ma'lumotlariga ruxsat yo'q")


@router.get("/plans", summary="List all subscription plans and pricing")
async def get_plans() -> dict[str, Any]:
    return {"plans": PLAN_DETAILS}


@router.get("/subscription", summary="Get active subscription and feature entitlements for user's tenant")
async def get_subscription(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    if current_user.role == "patient":
        return await BillingService(session).get_patient_subscription(current_user.id)
    if current_user.role == "relative" and len(current_user.patient_ids) == 1:
        return await BillingService(session).get_patient_subscription(current_user.patient_ids[0])
    service = BillingService(session)
    tenant = await service.get_or_create_tenant_for_user(
        user_id=current_user.id,
        phone=current_user.phone or f"+99890{current_user.id.hex[:7]}",
        name=f"{current_user.full_name} Klinikasi",
        kind="polyclinic",
    )
    return {"tenant_id": str(tenant.id), "message": "Klinika billing /api/v1/tenants/{id}/licence orqali yuritiladi"}


@router.post("/subscribe", summary="Subscribe or change plan (Free, Premium, Premium+Doc, Clinic)")
async def subscribe_plan(
    req: SubscribeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    if current_user.role == "patient":
        patient_id = current_user.id
    elif current_user.role == "relative" and len(current_user.patient_ids) == 1:
        patient_id = current_user.patient_ids[0]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Klinika tarifi /api/v1/tenants/{id}/licence orqali boshqariladi",
        )
    service = BillingService(session)
    try:
        return await service.upgrade_patient_plan(
            patient_id=patient_id,
            new_plan=req.plan,
            provider=req.provider,
            card_token=req.card_token,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/invoices", summary="List billing invoices history")
async def list_invoices(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    if len(current_user.tenant_ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice olish uchun tenant_id ni /api/v1/tenants/{id}/invoices orqali yuboring",
        )
    service = BillingService(session)
    return await service.list_invoices(current_user.tenant_ids[0])


@contract_router.get("/patients/{id}/subscription", summary="Get patient subscription status")
async def get_patient_subscription(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    _assert_patient_billing_scope(current_user, id)
    service = BillingService(session)
    return await service.get_subscription(id)


@contract_router.post("/patients/{id}/subscription/checkout", summary="Start patient subscription checkout")
async def checkout_patient_subscription(
    id: uuid.UUID,
    req: SubscribeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    _assert_patient_billing_scope(current_user, id)
    service = BillingService(session)
    try:
        return await service.upgrade_patient_plan(
            patient_id=id,
            new_plan=req.plan,
            provider=req.provider,
            card_token=req.card_token,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@contract_router.post("/webhooks/payments/{provider}", summary="Payment provider webhook")
async def payment_webhook(
    provider: str,
    payload: dict[str, Any],
    request: Request,
    x_wmax_signature: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    service = PaymentWebhookService(session)
    service.verify_signature(body=await request.body(), signature=x_wmax_signature)
    return await service.record(provider=provider, payload=payload)


@contract_router.get("/tenants/{id}/licence", summary="Get tenant licence")
async def get_tenant_licence(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    _assert_tenant_billing_scope(current_user, id)
    licence = (await session.execute(select(TenantLicence).where(TenantLicence.tenant_id == id))).scalar_one_or_none()
    if not licence:
        return {"tenant_id": str(id), "status": "missing", "device_count": 0}
    return {
        "id": str(licence.id),
        "tenant_id": str(licence.tenant_id),
        "status": licence.status,
        "device_count": licence.device_count,
        "min_days_per_device": licence.min_days_per_device,
        "price_per_patient_day_uzs": licence.price_per_patient_day_uzs,
    }


@contract_router.get("/tenants/{id}/usage", summary="Tenant patient-day usage")
async def get_tenant_usage(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    _assert_tenant_billing_scope(current_user, id)
    rows = (await session.execute(select(BillingDay).where(BillingDay.tenant_id == id))).scalars().all()
    return {
        "tenant_id": str(id),
        "patient_days_total": len(rows),
        "patient_days_with_data": sum(1 for row in rows if row.had_data),
    }


@contract_router.get("/tenants/{id}/invoices", summary="Tenant invoices")
async def get_tenant_invoices(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> list[dict[str, Any]]:
    _assert_tenant_billing_scope(current_user, id)
    rows = (await session.execute(select(Invoice).where(Invoice.tenant_id == id).order_by(Invoice.issued_at.desc()))).scalars().all()
    return [
        {
            "id": str(row.id),
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "patient_days_total": row.patient_days_total,
            "patient_days_with_data": row.patient_days_with_data,
            "amount_uzs": row.amount_uzs,
            "status": row.status,
            "created_at": row.issued_at.isoformat(),
        }
        for row in rows
    ]
