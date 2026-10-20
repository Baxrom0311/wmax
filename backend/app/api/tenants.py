from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import MemberTerritory, TenantMember

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

# Assigning territory changes who sees a patient and who gets tasks (B6), so
# only clinic-wide managers may do it.
TERRITORY_MANAGER_ROLES = {"admin", "head_doctor"}


class TerritoryUpdate(BaseModel):
    mahallas: list[str] = Field(default_factory=list, max_length=200)


async def _member(
    session: AsyncSession, current_user: CurrentUser, tenant_id: uuid.UUID, account_id: uuid.UUID,
) -> TenantMember:
    if current_user.tenant_roles.get(tenant_id) not in TERRITORY_MANAGER_ROLES:
        raise ForbiddenException("Mahallalarni faqat bosh shifokor yoki klinika administratori biriktiradi")
    member = (await session.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.account_id == account_id,
            TenantMember.left_at.is_(None),
        )
    )).scalar_one_or_none()
    if member is None:
        raise NotFoundException("Klinika xodimi", account_id)
    return member


async def _territories(session: AsyncSession, member: TenantMember) -> list[str]:
    rows = await session.execute(
        select(MemberTerritory.mahalla)
        .where(MemberTerritory.tenant_member_id == member.id)
        .order_by(MemberTerritory.mahalla)
    )
    return list(rows.scalars().all())


@router.get("/{tenant_id}/members/{account_id}/territories", summary="Staff member's assigned mahallas")
async def get_member_territories(
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, list[str]]:
    member = await _member(session, current_user, tenant_id, account_id)
    return {"mahallas": await _territories(session, member)}


@router.put("/{tenant_id}/members/{account_id}/territories", summary="Replace staff member's assigned mahallas")
async def put_member_territories(
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    req: TerritoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, list[str]]:
    member = await _member(session, current_user, tenant_id, account_id)
    mahallas = sorted({item.strip() for item in req.mahallas if item.strip()})
    await session.execute(delete(MemberTerritory).where(MemberTerritory.tenant_member_id == member.id))
    for mahalla in mahallas:
        session.add(MemberTerritory(tenant_member_id=member.id, mahalla=mahalla))
    await session.flush()
    await session.commit()
    return {"mahallas": mahallas}
