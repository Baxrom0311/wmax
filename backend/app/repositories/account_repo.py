from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, TenantMember


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        res = await self.session.execute(select(Account).where(Account.id == account_id))
        return res.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Account | None:
        res = await self.session.execute(
            select(Account).where(Account.phone == phone, Account.is_active == True)
        )
        return res.scalar_one_or_none()

    async def get_active_tenant_roles(self, account_id: uuid.UUID) -> list[TenantMember]:
        res = await self.session.execute(
            select(TenantMember).where(
                TenantMember.account_id == account_id,
                TenantMember.left_at.is_(None),
            )
        )
        return list(res.scalars().all())

