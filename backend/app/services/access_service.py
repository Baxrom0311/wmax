from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models import PatientAccess
from app.repositories.access_repo import PatientAccessRepository


class AccessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PatientAccessRepository(session)

    async def accept_invitation(
        self, *, access_id: uuid.UUID, account_id: uuid.UUID
    ) -> dict[str, Any]:
        access = await self.repo.get_by_id(access_id)
        if not access:
            raise NotFoundException("Ruxsat", access_id)
        if access.account_id != account_id:
            raise ForbiddenException("Bu ruxsat boshqa akkauntga tegishli")
        if access.revoked_at is not None:
            raise ValidationException("Ruxsat bekor qilingan")
        if access.accepted_at is None:
            from datetime import datetime, timezone
            access.accepted_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.commit()
        return self._access_dict(access)

    def _access_dict(self, access: PatientAccess) -> dict[str, Any]:
        return {
            "id": str(access.id),
            "patient_id": str(access.patient_id),
            "account_id": str(access.account_id),
            "role": access.role,
            "relation": access.relation,
            "accepted": access.accepted_at is not None,
            "granted_at": access.granted_at.isoformat() if access.granted_at else None,
        }
