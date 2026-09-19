from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.models.audit import ProfileAudit


class AuditedRepository:
    """Base repository providing automatic audit trail logging for entity updates and writes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_audit(
        self,
        patient_id: uuid.UUID,
        actor_kind: str,
        actor_id: uuid.UUID | None,
        entity: str,
        entity_id: str | None,
        action: str,
        changes: dict[str, Any],
        request_id: str | None = None,
    ) -> ProfileAudit:
        audit_entry = ProfileAudit(
            patient_id=patient_id,
            actor_kind=actor_kind,
            actor_id=actor_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            changes=changes,
            request_id=request_id,
        )
        self.session.add(audit_entry)
        return audit_entry

    async def update_with_audit(
        self,
        instance: Any,
        changes: dict[str, Any],
        principal: CurrentUser,
        patient_id: uuid.UUID,
        request_id: str | None = None,
    ) -> Any:
        diff: dict[str, Any] = {}
        for field, new_val in changes.items():
            if not hasattr(instance, field):
                continue
            old_val = getattr(instance, field)
            # Normalize dates/uuids for JSON serialization if needed
            old_str = str(old_val) if isinstance(old_val, (uuid.UUID)) else old_val
            new_str = str(new_val) if isinstance(new_val, (uuid.UUID)) else new_val
            if old_val != new_val:
                diff[field] = {"old": old_str, "new": new_str}
                setattr(instance, field, new_val)

        if diff:
            entity_name = getattr(instance, "__tablename__", type(instance).__name__)
            entity_id = str(getattr(instance, "id", ""))
            await self.record_audit(
                patient_id=patient_id,
                actor_kind=principal.role,
                actor_id=principal.id,
                entity=entity_name,
                entity_id=entity_id,
                action="update",
                changes=diff,
                request_id=request_id,
            )

        return instance
