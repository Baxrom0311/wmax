from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_principal
from app.billing.entitlements import PLAN_DETAILS
from app.billing.service import BillingService
from app.core.db import get_session

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class SubscribeRequest(BaseModel):
    plan: str = Field(..., description="Plan code: free | premium | premium_doc | clinic")
    provider: str = Field("payme", description="Payment provider: payme | click | uzum | stripe")
    card_token: str | None = Field(None, description="Optional card token for recurrent billing")


class PayInvoiceRequest(BaseModel):
    invoice_id: uuid.UUID
    provider: str = "payme"
    provider_txn: str | None = None


@router.get("/plans", summary="List all subscription plans and pricing")
async def get_plans() -> dict[str, Any]:
    return {"plans": PLAN_DETAILS}


@router.get("/subscription", summary="Get active subscription and feature entitlements for user's tenant")
async def get_subscription(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    service = BillingService(session)
    # Default tenant for household or clinician
    tenant = await service.get_or_create_tenant_for_user(
        user_id=current_user.id,
        phone=current_user.phone or f"+99890{current_user.id.hex[:7]}",
        name=f"{current_user.full_name} Oilaviy Kabineti",
        kind="clinic" if current_user.role in ("doctor", "nurse", "admin") else "household",
    )
    return await service.get_subscription(tenant.id)


@router.post("/subscribe", summary="Subscribe or change plan (Free, Premium, Premium+Doc, Clinic)")
async def subscribe_plan(
    req: SubscribeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    service = BillingService(session)
    tenant = await service.get_or_create_tenant_for_user(
        user_id=current_user.id,
        phone=current_user.phone or f"+99890{current_user.id.hex[:7]}",
        name=f"{current_user.full_name} Oilaviy Kabineti",
        kind="clinic" if current_user.role in ("doctor", "nurse", "admin") else "household",
    )
    try:
        return await service.upgrade_plan(
            tenant_id=tenant.id,
            new_plan=req.plan,
            provider=req.provider,
            card_token=req.card_token,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/invoices", summary="List billing invoices history")
async def list_invoices(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> list[dict[str, Any]]:
    service = BillingService(session)
    tenant = await service.get_or_create_tenant_for_user(
        user_id=current_user.id,
        phone=current_user.phone or f"+99890{current_user.id.hex[:7]}",
    )
    return await service.list_invoices(tenant.id)
