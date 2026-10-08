from __future__ import annotations

import uuid
from collections.abc import Iterable

from sqlalchemy import func, select
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
    """Sets request-scoped Postgres RLS variables using pure SQLAlchemy expressions."""
    tenant_value = ",".join(str(item) for item in tenant_ids)
    patient_value = ",".join(str(item) for item in patient_ids)
    await session.execute(select(func.set_config("wmax.account_id", str(account_id or ""), True)))
    await session.execute(select(func.set_config("wmax.tenant_ids", tenant_value, True)))
    await session.execute(select(func.set_config("wmax.patient_ids", patient_value, True)))
    await session.execute(select(func.set_config("wmax.device_id", str(device_id or ""), True)))
    await session.execute(select(func.set_config("wmax.bypass", "on" if bypass else "off", True)))
