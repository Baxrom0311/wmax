from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.device import Device
from app.models.patient import Patient
from app.services.device_service import DeviceService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_register_device_sets_in_stock(mock_session):
    service = DeviceService(mock_session)
    device = await service.register_device(
        serial_number="GW5-TEST-998",
        model_name="Samsung Galaxy Watch 5",
        tier="tier1_wearos",
        battery_health_pct=98,
    )
    assert device.serial_number == "GW5-TEST-998"
    assert device.status == "in_stock"
    assert device.tier == "tier1_wearos"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_device_changes_status_and_resets_baseline_on_hardware_change(mock_session):
    device_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    fake_device = Device(
        id=device_id,
        serial_number="GW5-NEW-SERIAL",
        model_name="Galaxy Watch 5",
        status="in_stock",
    )
    fake_patient = Patient(
        id=patient_id,
        full_name="Temur Bek",
        age=65,
        sex="m",
        diagnosis="I50.0",
        district="Urganch",
        phase="full",  # Was previously fully calibrated on another device
        device_id="GW4-OLD-SERIAL",  # Old device
    )

    async def fake_get(model, pk):
        if model == Device:
            return fake_device
        if model == Patient:
            return fake_patient
        return None

    mock_session.get = AsyncMock(side_effect=fake_get)

    service = DeviceService(mock_session)
    res = await service.assign_device_to_patient(
        device_id=device_id,
        patient_id=patient_id,
        deposit_uzs=500_000,
        rental_uzs_month=180_000,
    )

    assert res["status"] == "assigned"
    assert fake_device.status == "assigned"
    assert fake_patient.device_id == "GW5-NEW-SERIAL"
    # Section 5.2 of BUSINESS_MODEL.md: device changed -> phase resets to calib
    assert fake_patient.phase == "calib"
    assert fake_patient.baseline_approved_by is None


@pytest.mark.asyncio
async def test_return_device_retires_if_battery_degraded(mock_session):
    device_id = uuid.uuid4()
    fake_device = Device(
        id=device_id,
        serial_number="GW5-BATTERY-TIRED",
        model_name="Galaxy Watch 5",
        status="assigned",
        battery_health_pct=90,
    )
    mock_session.get = AsyncMock(return_value=fake_device)

    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_exec_res

    service = DeviceService(mock_session)
    # Returning with 74% battery health (< 80% threshold)
    res = await service.return_device(
        device_id=device_id,
        battery_health_pct=74,
        return_notes="Battery degraded after 2 years of clinical circulation",
        refund_deposit=True,
    )

    assert res["status"] == "retired"
    assert fake_device.status == "retired"
    assert fake_device.battery_health_pct == 74
