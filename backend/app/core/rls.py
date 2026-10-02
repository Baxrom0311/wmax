from __future__ import annotations

import uuid
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_rls_context(
    session: AsyncSession,
    *,
    account_id: uuid.UUID | None = None,
    tenant_ids: Iterable[uuid.UUID] = (),
    patient_ids: Iterable[uuid.UUID] = (),
    device_id: uuid.UUID | None = None,
    bypass: bool = False,
) -> None:
    """Sets request-scoped Postgres RLS variables for the current transaction."""
    tenant_value = ",".join(str(item) for item in tenant_ids)
    patient_value = ",".join(str(item) for item in patient_ids)
    await session.execute(text("SET LOCAL wmax.account_id = :account_id"), {"account_id": str(account_id or "")})
    await session.execute(text("SET LOCAL wmax.tenant_ids = :tenant_ids"), {"tenant_ids": tenant_value})
    await session.execute(text("SET LOCAL wmax.patient_ids = :patient_ids"), {"patient_ids": patient_value})
    await session.execute(text("SET LOCAL wmax.device_id = :device_id"), {"device_id": str(device_id or "")})
    await session.execute(text("SET LOCAL wmax.bypass = :bypass"), {"bypass": "on" if bypass else "off"})
