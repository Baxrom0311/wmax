from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.account_repo import AccountRepository


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts = AccountRepository(session)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.accounts.get_by_id(user_id)

    async def get_by_phone(self, phone: str) -> User | None:
        return await self.accounts.get_by_phone(phone)
