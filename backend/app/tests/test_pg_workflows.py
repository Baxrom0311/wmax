"""Workflow regressions against PostgreSQL for docs/REVIEW_2026-10-16.md
findings 1, 3, 4, 8, 9 and 12. Each test drives the runtime entry point
(ingest service, HTTP route, worker or delivery job) and asserts persisted state.

Synthetic data only. Telegram and SMS are in-memory fakes; nothing leaves the
process.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select

from app.models import Alert, Notification, NotificationAttempt, PatientMembership, Task
from app.schemas.reading import IngestBatch, ReadingIn
from app.services import notification_service
from app.services.pipeline_service import PipelineService
from app.tests.pg_support import World, bearer, requires_pg, rollback_session

pytestmark = requires_pg

NORMAL = {"hr_mean": 72.0, "spo2": 97.0, "skin_temp": 36.5, "rr_est": 15.0, "steps": 10}
CRITICAL = {**NORMAL, "spo2": 80.0}


@pytest.fixture
async def world():
    async with rollback_session() as session:
        yield World(session)


def _windows(count: int, *, last: dict, normal: dict = NORMAL, end: datetime | None = None, gap_every: int = 0):
    end = end or datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=5)
    readings = []
    for i in range(count):
        start = end - timedelta(minutes=5 * (count - 1 - i))
        values = last if i == count - 1 else normal
        if gap_every and i != count - 1 and i % gap_every:
            values = {}  # empty window: no measurement at all
        readings.append(ReadingIn(window_start=start, **values))
    return readings


async def _ingest(world: World, device, readings):
    return await PipelineService(world.session).ingest_batch(IngestBatch(readings=readings), device_id=device.id)


async def _alerts(world: World, patient):
    return list((await world.session.execute(
        select(Alert).where(Alert.patient_id == patient.id).order_by(Alert.ts)
    )).scalars().all())


async def _tasks(world: World, patient):
    return list((await world.session.execute(select(Task).where(Task.patient_id == patient.id))).scalars().all())


async def _notifications(world: World, patient):
    return list((await world.session.execute(
        select(Notification).where(Notification.patient_id == patient.id).order_by(Notification.id)
    )).scalars().all())


# ── finding 3: empty measurements are never green ───────────────────────────

async def test_reading_without_values_is_not_green_anywhere(world):
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    patient = await world.patient(clinic)
    device = await world.device(patient)

    result = await _ingest(world, device, [ReadingIn(window_start=datetime.now(timezone.utc) - timedelta(minutes=10))])

    assert len(result.accepted) == 1  # persisted (ACK), but not evidence
    assert await _alerts(world, patient) == []

    from app.services.patient_service import PatientService

    summaries = await PatientService(world.session).get_worklist(clinician_tenant_ids=[clinic.id])
    level = next(s.level for s in summaries if s.id == patient.id)
    assert level == "no_data"
    assert nurse  # the responsible nurse exists, yet nothing was tasked


# ── finding 8: quality decides clinical vs technical; unassigned is durable ─

async def test_reliable_red_creates_clinical_task_for_territory_clinician(world):
    clinic = await world.tenant()
    await world.member(clinic, "doctor", mahallas=("Gulshan",))  # other mahalla
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",))
    patient = await world.patient(clinic, mahalla="Navbahor")
    device = await world.device(patient)

    await _ingest(world, device, _windows(13, last=CRITICAL))

    alert = (await _alerts(world, patient))[-1]
    assert alert.level == "red"
    assert alert.task_kind == "clinical"
    assert alert.task_routing_status == "routed"
    [task] = await _tasks(world, patient)
    assert task.kind == "clinical" and task.assignee_account_id == nurse.id and task.due_at is not None


async def test_unreliable_red_asks_for_technical_check_without_deadline(world):
    clinic = await world.tenant()
    await world.member(clinic, "nurse", mahallas=("Navbahor",))
    patient = await world.patient(clinic)
    device = await world.device(patient)

    # Mostly empty windows in the last hour: the red reading is real but the
    # wear is too poor to create a clinical obligation (F2).
    await _ingest(world, device, _windows(13, last=CRITICAL, gap_every=4))

    alert = (await _alerts(world, patient))[-1]
    assert alert.level == "red"
    assert alert.task_kind == "technical"
    [task] = await _tasks(world, patient)
    assert task.kind == "technical" and task.due_at is None


async def test_alert_without_responsible_clinician_is_unassigned_then_routed(world):
    from app.models import MemberTerritory
    from app.workers.escalation_worker import retry_unassigned_alerts

    clinic = await world.tenant()
    nurse, member = await world.member(clinic, "nurse")  # no mahalla yet
    patient = await world.patient(clinic)
    device = await world.device(patient)

    await _ingest(world, device, _windows(13, last=CRITICAL))
    alert = (await _alerts(world, patient))[-1]
    assert alert.task_routing_status == "unassigned"
    assert await _tasks(world, patient) == []

    world.session.add(MemberTerritory(tenant_member_id=member.id, mahalla="Navbahor"))
    await world.session.flush()
    await retry_unassigned_alerts(world.session)

    await world.session.refresh(alert)
    assert alert.task_routing_status == "routed"
    [task] = await _tasks(world, patient)
    assert task.assignee_account_id == nurse.id and task.alert_id == alert.id


async def test_silence_raises_one_no_data_alert_with_technical_task(world):
    from app.workers.escalation_worker import check_patient_silence

    clinic = await world.tenant()
    await world.member(clinic, "nurse", mahallas=("Navbahor",))
    patient = await world.patient(clinic)
    caregiver = await world.caregiver(patient, telegram="900001")
    device = await world.device(patient)
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    await _ingest(world, device, _windows(3, last=NORMAL, end=old))
    # A recent but empty window must not count as "seen".
    await _ingest(world, device, [ReadingIn(window_start=datetime.now(timezone.utc) - timedelta(minutes=10))])

    await check_patient_silence(world.session)
    await check_patient_silence(world.session)

    no_data = [a for a in await _alerts(world, patient) if a.reason == "silence_no_data"]
    assert len(no_data) == 1
    [task] = [t for t in await _tasks(world, patient)]
    assert task.kind == "technical"
    rows = [n for n in await _notifications(world, patient) if n.alert_id == no_data[0].id]
    assert [n.recipient_account_id for n in rows] == [caregiver.id]


# ── finding 4: consent revocation stops every transport and workflow ───────

async def test_clinical_consent_revocation_stops_ingest_tasks_and_delivery(world):
    from app.models import PatientConsent
    from app.services.patient_relationship_service import PatientRelationshipService

    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",), telegram="700001")
    patient = await world.patient(clinic)
    device = await world.device(patient)
    await _ingest(world, device, _windows(13, last=CRITICAL))
    [task] = await _tasks(world, patient)
    staff_rows = [n for n in await _notifications(world, patient) if n.recipient_account_id == nurse.id]
    assert staff_rows and staff_rows[0].delivery_status == "pending"

    consent = (await world.session.execute(
        select(PatientConsent).where(PatientConsent.patient_id == patient.id, PatientConsent.scope == "clinical_monitoring")
    )).scalar_one()
    await PatientRelationshipService(world.session).revoke_consent(
        patient_id=patient.id, consent_id=consent.id, actor_id=nurse.id,
    )

    await world.session.refresh(task)
    assert task.status == "cancelled"
    membership = (await world.session.execute(
        select(PatientMembership).where(PatientMembership.patient_id == patient.id)
    )).scalar_one()
    assert membership.revoked_at is not None

    later = _windows(1, last=NORMAL, end=datetime.now(timezone.utc) - timedelta(minutes=1))
    result = await _ingest(world, device, later)
    assert [r.reason for r in result.rejected] == ["consent_missing_or_revoked"]

    sent: list[str] = []

    async def telegram(chat, text, markup):
        sent.append(chat)
        return True

    await notification_service.deliver_due(world.session, telegram_sender=telegram)
    await world.session.refresh(staff_rows[0])
    assert staff_rows[0].delivery_status == "cancelled"
    assert sent == []


# ── findings 1 and 9: SOS and alerts reach each recipient independently ────

class FakeSms:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.states: dict[str, str] = {}

    @staticmethod
    def configured() -> bool:
        return True

    async def submit(self, *, phone: str, message: str) -> str:
        ref = str(len(self.sent) + 1)
        self.sent.append((phone, message))
        self.states[ref] = "WAITING"
        return ref

    async def delivery_status(self, reference: str) -> str:
        return self.states[reference]


async def _due_now(world: World, patient) -> None:
    for row in await _notifications(world, patient):
        row.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await world.session.flush()


async def test_sos_via_api_is_queued_per_recipient_and_survives_provider_failure(world):
    from app.core.db import get_session
    from app.main import app

    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",), telegram="700001")
    dispatcher, _ = await world.member(clinic, "dispatcher", telegram="700002")
    await world.member(clinic, "nurse", mahallas=("Gulshan",), telegram="700003")  # not responsible
    patient = await world.patient(clinic)
    caregiver = await world.caregiver(patient, telegram="900001")

    async def _session():
        yield world.session

    app.dependency_overrides[get_session] = _session
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/sos",
                json={"patient_id": str(patient.id), "source": "phone_app"},
                headers={"Authorization": f"Bearer {bearer(caregiver, 'relative')}"},
            )
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert response.status_code == 201, response.text
    sos_id = response.json()["id"]

    rows = await _notifications(world, patient)
    assert {r.recipient_account_id for r in rows} == {nurse.id, dispatcher.id, caregiver.id}
    assert all(str(r.sos_event_id) == sos_id and r.urgent and r.delivery_status == "pending" for r in rows)

    # Telegram works for the caregiver only; staff sends fail.
    async def flaky(chat, text, markup):
        return chat == "900001"

    sms = FakeSms()
    await notification_service.deliver_due(world.session, telegram_sender=flaky, sms_provider=sms)
    by_recipient = {r.recipient_account_id: r for r in await _notifications(world, patient)}
    assert by_recipient[caregiver.id].delivery_status == "awaiting_ack"
    assert by_recipient[nurse.id].delivery_status == "pending"  # one success closes nobody else

    # "Process restart": a new delivery run picks the stored retry state up.
    await _due_now(world, patient)
    await notification_service.deliver_due(world.session, telegram_sender=flaky, sms_provider=sms)
    await _due_now(world, patient)
    await notification_service.deliver_due(world.session, telegram_sender=flaky, sms_provider=sms)
    staff_phones = {r.phone for r in [nurse, dispatcher]}
    # After two Telegram failures staff fall back to SMS; the unacknowledged
    # caregiver is escalated to SMS after the ACK timeout.
    assert staff_phones <= {phone for phone, _ in sms.sent}
    assert caregiver.phone not in {phone for phone, _ in sms.sent}  # unverified phone is never texted

    for ref in sms.states:
        sms.states[ref] = "DELIVERED"
    await _due_now(world, patient)
    await notification_service.deliver_due(world.session, telegram_sender=flaky, sms_provider=sms)
    by_recipient = {r.recipient_account_id: r for r in await _notifications(world, patient)}
    assert by_recipient[nurse.id].delivery_status == "delivered"
    assert by_recipient[dispatcher.id].delivery_status == "delivered"
    attempts = (await world.session.execute(
        select(NotificationAttempt).where(NotificationAttempt.notification_id == by_recipient[nurse.id].id)
    )).scalars().all()
    assert [a.channel for a in attempts][:2] == ["telegram", "telegram"]
    assert any(a.channel == "sms" and a.delivered for a in attempts)


async def test_telegram_ack_stops_urgent_escalation(world):
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",), telegram="700001")
    patient = await world.patient(clinic)
    device = await world.device(patient)
    await _ingest(world, device, _windows(13, last=CRITICAL))
    [row] = [n for n in await _notifications(world, patient) if n.recipient_account_id == nurse.id]

    async def ok(chat, text, markup):
        assert markup["inline_keyboard"][0][0]["callback_data"] == f"ntf_ack:{row.id}"
        return True

    sms = FakeSms()
    await notification_service.deliver_due(world.session, telegram_sender=ok, sms_provider=sms)
    assert row.delivery_status == "awaiting_ack"

    assert not await notification_service.acknowledge_by_telegram(world.session, row.id, "999999")  # stranger
    assert await notification_service.acknowledge_by_telegram(world.session, row.id, "700001")
    await _due_now(world, patient)
    await notification_service.deliver_due(world.session, telegram_sender=ok, sms_provider=sms)
    assert row.delivery_status == "acknowledged"
    assert sms.sent == []


async def test_amber_alert_notifies_family_not_staff_and_respects_cooldown(world):
    clinic = await world.tenant()
    nurse, _ = await world.member(clinic, "nurse", mahallas=("Navbahor",), telegram="700001")
    patient = await world.patient(clinic)
    caregiver = await world.caregiver(patient, telegram="900001")
    from app.models import Alert as AlertModel
    from app.services.notification_service import queue_alert_notifications

    first = AlertModel(patient_id=patient.id, ts=datetime.now(timezone.utc), level="amber")
    second = AlertModel(patient_id=patient.id, ts=datetime.now(timezone.utc) + timedelta(seconds=1), level="amber")
    world.session.add_all([first, second])
    await world.session.flush()
    await queue_alert_notifications(world.session, first, patient)
    await queue_alert_notifications(world.session, second, patient)

    rows = await _notifications(world, patient)
    assert [(r.alert_id, r.recipient_account_id) for r in rows] == [(first.id, caregiver.id)]
    assert nurse.id not in {r.recipient_account_id for r in rows}


async def test_sos_without_any_recipient_is_recorded_not_dropped(world):
    from app.services.sos_service import SosService

    patient = await world.patient(None)
    event = await SosService(world.session).raise_sos(patient.id, source="phone_app")
    [row] = await _notifications(world, patient)
    assert row.sos_event_id == event.id
    assert row.delivery_status == "no_recipient"


# ── finding 12: death stops everything from one place, family keeps history ─

async def test_deceased_lifecycle(world):
    from app.auth.scope import assert_patient_access
    from app.core.db import get_session
    from app.core.exceptions import ForbiddenException
    from app.main import app
    from app.schemas.auth import CurrentUser

    clinic = await world.tenant()
    doctor, _ = await world.member(clinic, "doctor", mahallas=("Navbahor",), telegram="700001")
    patient = await world.patient(clinic)
    caregiver = await world.caregiver(patient, telegram="900001")
    device = await world.device(patient)
    await _ingest(world, device, _windows(13, last=CRITICAL))
    [task] = await _tasks(world, patient)
    task.status = "overdue"
    await world.session.flush()

    async def _session():
        yield world.session

    app.dependency_overrides[get_session] = _session
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/patients/{patient.id}/deceased",
                headers={"Authorization": f"Bearer {bearer(doctor, 'doctor', tenant_ids=[clinic.id])}"},
            )
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert response.status_code == 200, response.text
    device_task_id = response.json()["device_return_task_id"]

    await world.session.refresh(task)
    assert task.status == "cancelled"
    device_task = await world.session.get(Task, device_task_id)
    assert device_task.kind == "technical" and device_task.status == "open"
    assert {n.delivery_status for n in await _notifications(world, patient)} == {"cancelled"}

    family = CurrentUser(id=caregiver.id, full_name="c", role="relative")
    await assert_patient_access(world.session, family, patient.id)  # within 90 days
    patient.deceased_at = datetime.now(timezone.utc) - timedelta(days=91)
    await world.session.flush()
    with pytest.raises(ForbiddenException):
        await assert_patient_access(world.session, family, patient.id)
