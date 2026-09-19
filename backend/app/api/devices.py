from __future__ import annotations

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.services.device_service import DeviceService

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


class DeviceCreateRequest(BaseModel):
    serial_number: str = Field(..., description="Serial or IMEI of smart watch / band")
    model_name: str = Field(..., description="E.g. Galaxy Watch 5, Xiaomi Watch 2, Medical Band")
    tier: Literal["tier1_wearos", "tier2_wearos_budget", "tier3_ble_band"] = "tier1_wearos"
    ownership: str = Field("owned", description="owned | leased | patient_owned")
    battery_health_pct: int = Field(100, ge=0, le=100)


class DeviceAssignRequest(BaseModel):
    patient_id: uuid.UUID
    deposit_uzs: int = Field(500_000, ge=0, description="Refundable security deposit")
    rental_uzs_month: int = Field(180_000, ge=0, description="Monthly rental fee")


class DeviceReturnRequest(BaseModel):
    battery_health_pct: int | None = Field(None, ge=0, le=100)
    return_notes: str | None = None
    refund_deposit: bool = True


@router.get("", summary="List device inventory with battery health and assignment status")
async def list_devices(
    status_filter: str | None = Query(None, alias="status", description="in_stock | assigned | active | maintenance | retired"),
    tier_filter: str | None = Query(None, alias="tier", description="tier1_wearos | tier2_wearos_budget | tier3_ble_band"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    service = DeviceService(session)
    return await service.list_devices(status=status_filter, tier=tier_filter)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Register a new device into clinic inventory")
async def register_device(
    req: DeviceCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    service = DeviceService(session)
    device = await service.register_device(
        serial_number=req.serial_number,
        model_name=req.model_name,
        tier=req.tier,
        ownership=req.ownership,
        battery_health_pct=req.battery_health_pct,
    )
    await session.commit()
    return {
        "id": str(device.id),
        "serial_number": device.serial_number,
        "model_name": device.model_name,
        "tier": device.tier,
        "status": device.status,
    }


@router.post("/{device_id}/assign", summary="Assign an in-stock device to a patient for rental monitoring")
async def assign_device(
    device_id: uuid.UUID,
    req: DeviceAssignRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    service = DeviceService(session)
    try:
        res = await service.assign_device_to_patient(
            device_id=device_id,
            patient_id=req.patient_id,
            assigned_by=current_user.id,
            deposit_uzs=req.deposit_uzs,
            rental_uzs_month=req.rental_uzs_month,
        )
        await session.commit()
        return res
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{device_id}/return", summary="Process device return from patient, inspect battery and refund deposit")
async def return_device(
    device_id: uuid.UUID,
    req: DeviceReturnRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    service = DeviceService(session)
    try:
        res = await service.return_device(
            device_id=device_id,
            battery_health_pct=req.battery_health_pct,
            return_notes=req.return_notes,
            refund_deposit=req.refund_deposit,
        )
        await session.commit()
        return res
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
