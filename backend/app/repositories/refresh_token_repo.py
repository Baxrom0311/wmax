from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        token_hash: str,
        expires_at: datetime,
        user_id: uuid.UUID | None = None,
        relative_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
    ) -> RefreshToken:
        """Stores a refresh token against exactly one owner column."""
        token_entry = RefreshToken(
            token_hash=token_hash,
            expires_at=expires_at,
            account_id=user_id,
            relative_id=relative_id,
            patient_id=patient_id,
        )
        added = self.session.add(token_entry)
        if inspect.isawaitable(added):
            await added
        await self.session.flush()
        return token_entry

    async def get_valid(self, token_hash: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, token_hash: str) -> bool:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
