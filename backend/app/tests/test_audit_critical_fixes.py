from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.dialects import postgresql

from app.ai.prompts import build_clinical_analysis_prompt, build_nurse_sbar_prompt
from app.core.security import hash_password
from app.core.exceptions import ForbiddenException
from app.auth.scope import assert_patient_access
from app.auth.service import AuthService
from app.models import (
    Account,
    Alert,
    DeviceAssignment,
    Patient,
    PatientAccess,
    TenantMember,
)
from app.schemas.auth import RelativeLoginRequest
from app.schemas.health_data import HealthDataBatch, HealthSampleIn
from app.services.health_data_service import HealthDataIngestService
from app.services.pipeline_service import PipelineService
from app.services.sos_service import SosService


# ==============================================================================
# TEST 1: Wear/HealthSample -> 5-min Reading -> Clinical Pipeline Alert
# ==============================================================================
@pytest.mark.asyncio
async def test_health_sample_aggregates_into_reading_and_triggers_pipeline():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()

    device_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    now = datetime(2026, 10, 7, 10, 2, 0, tzinfo=timezone.utc)

    assignment = DeviceAssignment(
        id=assignment_id,
        device_id=device_id,
        patient_id=patient_id,
        assigned_at=now - timedelta(days=1),
        released_at=None,
    )
    assignment_result = MagicMock()
    assignment_result.scalars.return_value.all.return_value = [assignment]
    consent_result = MagicMock()
    consent_result.scalars.return_value.all.return_value = [patient_id]

    service = HealthDataIngestService(session)
    batch = HealthDataBatch(
        batch_id=uuid.uuid4(),
        source="wear_health_services",
        samples=[
            HealthSampleIn(
                metric="heart_rate_bpm",
                value_num=165.0,
                unit="bpm",
                recorded_at=now,
            ),
            HealthSampleIn(
                metric="oxygen_saturation_pct",
                value_num=86.0,
                unit="%",
                recorded_at=now,
            ),
        ],
    )
    sample_keys = [
        service._key(
            device_id=device_id,
            source=batch.source,
            source_record_id=None,
            kind="sample",
            natural=f"{sample.metric}:{sample.recorded_at.isoformat()}",
        )
        for sample in batch.samples
    ]
    session.execute.side_effect = [
        assignment_result,  # assignment query
        consent_result,  # current clinical-monitoring consent
        _returned_keys(sample_keys),  # newly inserted HealthSample idempotency keys
        MagicMock(rowcount=1),  # insert Reading
        MagicMock(rowcount=0),  # insert Sleep
        MagicMock(rowcount=0),  # insert Exercise
        MagicMock(rowcount=1),  # insert SyncEvent
    ]

    with patch.object(PipelineService, "evaluate_patient", new_callable=AsyncMock) as mock_eval:
        result = await service.ingest_device_batch(batch, device_id=device_id)
        assert result.accepted == 2
        reading_insert = session.execute.call_args_list[3].args[0]
        reading = reading_insert.compile(dialect=postgresql.dialect()).params
        assert 165.0 in reading.values()
        assert 86.0 in reading.values()
        assert True in reading.values()
        mock_eval.assert_awaited_once_with(patient_id)


@pytest.mark.asyncio
async def test_unreliable_health_sample_does_not_create_clinical_reading():
    session = AsyncMock()
    patient_id, device_id = uuid.uuid4(), uuid.uuid4()
    service = HealthDataIngestService(session)
    with patch.object(PipelineService, "evaluate_patient", new_callable=AsyncMock) as evaluate:
        await service._aggregate_samples_to_readings([{
            "patient_id": patient_id,
            "device_id": device_id,
            "recorded_at": datetime(2026, 10, 7, 10, 2, tzinfo=timezone.utc),
            "metric": "heart_rate_bpm",
            "value_num": 170,
            "quality": 0.2,
            "metadata_json": {"ingest_quality_flags": ["unexpected_unit"]},
        }])
    session.execute.assert_not_awaited()
    evaluate.assert_not_awaited()


@pytest.mark.asyncio
async def test_revoked_or_missing_clinical_consent_rejects_ingest():
    session = AsyncMock()
    device_id, patient_id = uuid.uuid4(), uuid.uuid4()
    now = datetime(2026, 10, 7, 10, 2, tzinfo=timezone.utc)
    assignment = DeviceAssignment(
        id=uuid.uuid4(), device_id=device_id, patient_id=patient_id,
        assigned_at=now - timedelta(days=1), released_at=None,
    )
    assignments = MagicMock()
    assignments.scalars.return_value.all.return_value = [assignment]
    no_consent = MagicMock()
    no_consent.scalars.return_value.all.return_value = []
    session.execute.side_effect = [assignments, no_consent, MagicMock()]
    batch = HealthDataBatch(
        batch_id=uuid.uuid4(),
        source="wear_health_services",
        samples=[HealthSampleIn(metric="heart_rate_bpm", value_num=90, unit="bpm", recorded_at=now)],
    )
    result = await HealthDataIngestService(session).ingest_device_batch(batch, device_id=device_id)
    assert result.accepted == 0
    assert result.rejected[0]["reason"] == "consent_missing_or_revoked"


@pytest.mark.asyncio
async def test_relative_claim_does_not_authorize_without_current_access_and_consent():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    principal = MagicMock(id=uuid.uuid4(), role="relative", patient_ids=[uuid.uuid4()])
    with pytest.raises(ForbiddenException):
        await assert_patient_access(session, principal, uuid.uuid4())


def _returned_keys(keys: list[str]):
    result = MagicMock()
    # These keys are the deterministic sample keys generated by the service.
    result.scalars.return_value.all.return_value = keys
    return result


# ==============================================================================
# TEST 2: SOS -> Emergency Contacts SMS Delivered Verification
# ==============================================================================
@pytest.mark.asyncio
async def test_sos_delivers_emergency_sms_to_contacts():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    patient_id = uuid.uuid4()
    event_id = uuid.uuid4()
    session.get = AsyncMock(return_value=Patient(id=patient_id, full_name="Test Patient"))

    mock_sos = MagicMock()
    mock_sos.id = event_id
    mock_sos.patient_id = patient_id
    mock_sos.status = "raised"

    with patch("app.services.sos_service.PatientContextBuilder") as mock_builder, \
         patch("app.services.sos_service.SosRepository") as mock_sos_repo, \
         patch("app.services.sos_service.send_sms_text", new_callable=AsyncMock) as mock_sms, \
         patch("app.services.sos_service.LiveEventService") as mock_live_event:

        mock_live_event.return_value.publish_sos = AsyncMock()
        contact = MagicMock()
        contact.phone = "+998901234567"
        contact.telegram_chat_id = None

        ctx = MagicMock()
        ctx.full_name = "Otabek Saidov"
        ctx.emergency_contacts = [contact]
        mock_builder.return_value.build = AsyncMock(return_value=ctx)

        mock_repo_inst = mock_sos_repo.return_value
        mock_repo_inst.create_event = AsyncMock(return_value=mock_sos)
        mock_repo_inst.count_active_for_patient = AsyncMock(return_value=0)
        mock_repo_inst.add_notification = AsyncMock()
        mock_sms.return_value = True

        sos_service = SosService(session)
        await sos_service.raise_sos(patient_id=patient_id, source="watch")

        # Verify SMS was sent with alert message
        mock_sms.assert_awaited_once()
        sent_phone = mock_sms.call_args.kwargs["phone"]
        assert sent_phone == "+998901234567"

        # Verify notification was saved as delivered=True
        mock_repo_inst.add_notification.assert_awaited_once()
        assert mock_repo_inst.add_notification.call_args.kwargs["delivered"] is True


# ==============================================================================
# TEST 3: Caregiver PIN Login with new Account / PatientAccess schema
# ==============================================================================
@pytest.mark.asyncio
async def test_relative_login_with_account_pin_hash():
    session = AsyncMock()
    session.execute.return_value.scalar_one_or_none.return_value = None
    account_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    phone = "+998901112233"
    pin = "445566"

    access = PatientAccess(
        id=uuid.uuid4(),
        account_id=account_id,
        patient_id=patient_id,
        relationship="son",
    )
    patient = Patient(id=patient_id, full_name="Karim Otaxonov")
    account = Account(
        id=account_id,
        phone=phone,
        full_name="Dilshod Karimov",
        password_hash=hash_password(pin),
    )

    auth_service = AuthService(session)
    setattr(access, "pin_hash", account.password_hash)
    setattr(access, "full_name", account.full_name)
    setattr(access, "account", account)

    auth_service.relative_repo.get_assigned_patients = AsyncMock(return_value=[(access, patient)])
    auth_service.token_repo.create_refresh_token = AsyncMock()

    with patch("app.auth.service.AlertRepository") as mock_alert_repo:
        mock_alert_repo.return_value.get_latest = AsyncMock(return_value=None)
        res = await auth_service.relative_login(
            RelativeLoginRequest(phone=phone, pin=pin)
        )

    assert res.role == "relative"
    assert res.access_token is not None
    assert len(res.patients) == 1
    assert res.patients[0].id == patient_id


# ==============================================================================
# TEST 4: Clinical Task Assignee Selection Priority
# ==============================================================================
@pytest.mark.asyncio
async def test_task_assignee_prioritizes_clinician_over_admin():
    session = AsyncMock()
    patient_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    patient = Patient(id=patient_id, full_name="Bemor Ali", doctor_id=None)
    doctor_member = TenantMember(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        account_id=doc_id,
        role="doctor",
        joined_at=datetime.now(timezone.utc),
    )

    with patch("app.services.pipeline_service.PatientRepository") as mock_pat_repo, \
         patch("app.services.pipeline_service.TaskRepository") as mock_task_repo:

        mock_pat_repo.return_value.get_by_id = AsyncMock(return_value=patient)

        membership_mock = MagicMock()
        membership_mock.scalar_one_or_none.return_value = MagicMock(tenant_id=tenant_id)

        clinician_mock = MagicMock()
        clinician_mock.scalar_one_or_none.return_value = doctor_member

        session.execute.side_effect = [
            membership_mock,  # membership lookup
            clinician_mock,   # clinician query
        ]

        task_repo_inst = mock_task_repo.return_value
        task_repo_inst.get_open_task = AsyncMock(return_value=None)
        task_repo_inst.create_task = AsyncMock()

        pipeline = PipelineService(session)
        alert = Alert(id=1, patient_id=patient_id, level="red")
        await pipeline._create_alert_task(patient, alert, MagicMock(level="red"))

        # Verifies doctor account is assigned
        task_repo_inst.create_task.assert_awaited_once()
        assigned = task_repo_inst.create_task.call_args.kwargs["assignee_account_id"]
        assert assigned == doc_id

        # The clinician lookup must rank doctors ahead of head doctors and nurses.
        clinician_query = session.execute.call_args_list[1].args[0]
        compiled = str(
            clinician_query.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        assert "CASE WHEN (tenant_members.role = 'doctor') THEN 0" in compiled
        assert "WHEN (tenant_members.role = 'head_doctor') THEN 1" in compiled
        assert "WHEN (tenant_members.role = 'nurse') THEN 2" in compiled


# ==============================================================================
# TEST 5: AI Prompt PHI Sanitization & Pseudonymization
# ==============================================================================
def test_ai_prompts_mask_patient_identity_and_hide_full_name():
    real_name = "Abdurahmon Toshmatov"
    diagnosis = "IBS, gipertoniya II daraja"

    # Clinical Analysis Prompt
    prompt = build_clinical_analysis_prompt(
        patient_name=real_name,
        age=68,
        diagnosis=diagnosis,
        level="red",
        recent_vitals={"hr_mean": 95},
        deviated_params={"hr_mean": 2.1},
        slope=0.2,
    )

    # Real name must NOT be leaked to third-party AI
    assert real_name not in prompt
    assert "Bemor A.T." in prompt

    # Nurse SBAR Handover Prompt
    ctx = MagicMock()
    ctx.full_name = real_name
    ctx.age = 68
    ctx.level = "amber"
    ctx.composite_score = 2.4
    ctx.conditions = []
    ctx.medications = []
    ctx.open_tasks = []
    ctx.recent_vitals = {}
    ctx.triggered_params = {}

    sbar_prompt = build_nurse_sbar_prompt(ctx)
    assert real_name not in sbar_prompt
    assert "Bemor A.T." in sbar_prompt
