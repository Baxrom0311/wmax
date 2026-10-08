from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.models import PatientMembership
from app.models.alert import Alert
from app.schemas.common import AlertLevel

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", summary="List clinical alerts with optional filters")
async def list_alerts(
    patient_id: uuid.UUID | None = Query(None),
    level: AlertLevel | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    stmt = select(Alert).order_by(Alert.ts.desc()).limit(limit)
    stmt = stmt.where(
        exists().where(
            PatientMembership.patient_id == Alert.patient_id,
            PatientMembership.tenant_id.in_(current_user.tenant_ids),
            PatientMembership.revoked_at.is_(None),
        )
    )
    if patient_id is not None:
        stmt = stmt.where(Alert.patient_id == patient_id)
    if level is not None:
        stmt = stmt.where(Alert.level == level)
    res = await session.execute(stmt)
    return [
        {
            "id": item.id,
            "patient_id": str(item.patient_id),
            "ts": item.ts.isoformat(),
            "level": item.level,
            "composite_score": item.composite_score,
            "triggered_params": item.triggered_params,
            "anomaly_score": item.anomaly_score,
            "reason": item.reason,
            "data_quality": item.data_quality,
        }
        for item in res.scalars().all()
    ]
