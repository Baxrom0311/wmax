from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.domain.access import requires_audit_log, visible_patients
from app.domain.attribution import attribute_reading, orphan_candidates
from app.domain.billing_calc import invoice_total, patient_days
from app.domain.device_assignment import assignment_covers_interval
from app.domain.entitlement import Feature, NEVER_PAYWALLED, clinical_pipeline_enabled, family_features
from app.domain.health_quality import is_worn_window
from app.domain.quality import task_kind
from app.domain.responsibility import notification_targets, promise_level, should_create_task
from app.domain.types import (
    AssignmentWindow,
    CareOwner,
    CaregiverRef,
    DataQuality,
    DateRange,
    Licence,
    Membership,
    PatientState,
    PlatformRole,
    TargetKind,
    TenantMembership,
    TenantRole,
    ViewerContext,
)


def uid(seed: int) -> uuid.UUID:
    return uuid.UUID(int=seed)


def ts(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 1, day, hour, tzinfo=timezone.utc)


def care_owner(active: bool = True) -> CareOwner:
    return CareOwner(tenant_id=uid(10), account_id=uid(11), name="Nurse", licence_active=active)


def test_responsibility_requires_care_owner_for_tasks():
    patient = PatientState(patient_id=uid(1), care_owner=None)
    assert promise_level(patient) == "awareness"
    assert should_create_task(patient, "red") is False

    owned = PatientState(patient_id=uid(1), care_owner=care_owner(active=False))
    assert promise_level(owned) == "accountable"
    assert should_create_task(owned, "red") is True
    assert should_create_task(owned, "green") is False


def test_red_notification_targets_are_never_empty():
    states = (
        PatientState(patient_id=uid(1), care_owner=None),
        PatientState(patient_id=uid(2), care_owner=None, caregivers=(CaregiverRef(uid(20)),)),
        PatientState(patient_id=uid(3), care_owner=care_owner(), subscription_active=False),
        PatientState(
            patient_id=uid(4),
            care_owner=care_owner(),
            caregivers=(CaregiverRef(uid(21)),),
            subscription_active=True,
        ),
    )
    for state in states:
        assert notification_targets(state, "red")


def test_notification_targets_follow_owner_and_subscription_rules():
    with_owner = PatientState(
        patient_id=uid(1),
        care_owner=care_owner(),
        caregivers=(CaregiverRef(uid(20)),),
        subscription_active=False,
    )
    assert [target.kind for target in notification_targets(with_owner, "amber")] == [TargetKind.CLINICIAN]

    without_owner = PatientState(patient_id=uid(1), care_owner=None, caregivers=(CaregiverRef(uid(20)),))
    assert [target.kind for target in notification_targets(without_owner, "amber")] == [TargetKind.CAREGIVER]


def test_entitlements_never_paywall_safety_features():
    free = PatientState(patient_id=uid(1), care_owner=None, subscription_active=False)
    paid = PatientState(patient_id=uid(1), care_owner=None, subscription_active=True)

    assert NEVER_PAYWALLED == {Feature.CRITICAL_ALERT, Feature.SOS}
    assert family_features(free) == NEVER_PAYWALLED
    assert Feature.PDF_REPORT in family_features(paid)
    assert clinical_pipeline_enabled(free) is False
    assert clinical_pipeline_enabled(PatientState(patient_id=uid(1), care_owner=care_owner(active=False))) is True


def test_access_scope_for_clinic_family_and_platform():
    nurse = ViewerContext(
        account_id=uid(1),
        tenant_memberships=(TenantMembership(uid(10), TenantRole.NURSE, frozenset({"Gulzor"})),),
        patient_access_ids=frozenset({uid(100)}),
    )
    nurse_scope = visible_patients(nurse)
    assert nurse_scope.mahallas == {"Gulzor"}
    assert nurse_scope.patient_ids == {uid(100)}

    head = ViewerContext(account_id=uid(2), tenant_memberships=(TenantMembership(uid(10), TenantRole.HEAD_DOCTOR),))
    assert visible_patients(head).tenant_ids == {uid(10)}

    research = visible_patients(ViewerContext(account_id=None, platform_role=PlatformRole.RESEARCH))
    assert research.all_patients is True
    assert research.anonymized is True


def test_platform_support_requires_reason_and_is_audited():
    with pytest.raises(ValueError):
        visible_patients(ViewerContext(account_id=uid(1), platform_role=PlatformRole.SUPPORT))

    viewer = ViewerContext(account_id=uid(1), platform_role=PlatformRole.SUPPORT, support_reason="ticket-7")
    assert visible_patients(viewer).support_reason == "ticket-7"
    assert requires_audit_log(viewer, uid(99)) is True


def test_patient_access_read_does_not_require_cross_scope_audit():
    viewer = ViewerContext(account_id=uid(1), patient_access_ids=frozenset({uid(99)}))
    assert requires_audit_log(viewer, uid(99)) is False
    assert requires_audit_log(viewer, uid(100)) is True


def test_quality_controls_task_kind_not_visibility():
    assert task_kind(DataQuality(score=0.9, days_with_data=6, days_total=7), "red") == "clinical"
    assert task_kind(DataQuality(score=0.6, days_with_data=6, days_total=7), "red") == "technical"
    assert task_kind(DataQuality(score=0.9, days_with_data=2, days_total=7), "amber") == "technical"
    assert task_kind(DataQuality(score=1.0, days_with_data=7, days_total=7), "no_data") == "technical"


def test_explicit_zero_wear_fraction_is_not_used_as_clinical_signal():
    assert is_worn_window(True, 0) is False
    assert is_worn_window(True, None) is True
    assert is_worn_window(True, 60) is True
    assert is_worn_window(False, 100) is False


def test_attribution_uses_historical_assignment_window():
    first_patient = uid(1)
    second_patient = uid(2)
    windows = (
        AssignmentWindow("watch-1", first_patient, ts(1), ts(5)),
        AssignmentWindow("watch-1", second_patient, ts(5), None),
    )
    assert attribute_reading(ts(4, 23), "watch-1", windows) == first_patient
    assert attribute_reading(ts(5), "watch-1", windows) == second_patient
    assert attribute_reading(ts(4), "watch-2", windows) is None


def test_assignment_must_cover_the_entire_measurement_interval():
    first_patient = SimpleNamespace(assigned_at=ts(1), released_at=ts(5))

    assert assignment_covers_interval(first_patient, ts(4), ts(5)) is True
    assert assignment_covers_interval(first_patient, ts(4), ts(6)) is False
    assert assignment_covers_interval(first_patient, ts(5), ts(5)) is False


def test_orphan_candidates_are_limited_to_same_device_and_range():
    windows = (
        AssignmentWindow("watch-1", uid(1), ts(1), ts(3)),
        AssignmentWindow("watch-1", uid(2), ts(4), ts(7)),
        AssignmentWindow("watch-2", uid(3), ts(4), ts(7)),
    )
    assert orphan_candidates("watch-1", (ts(2), ts(5)), windows) == (uid(1), uid(2))


def test_patient_days_count_membership_and_assignment_overlap_by_calendar_day():
    memberships = (Membership(patient_id=uid(1), tenant_id=uid(10), granted_at=ts(1, 10), revoked_at=ts(3, 8)),)
    assignments = (AssignmentWindow("watch-1", uid(1), ts(2, 23), ts(4)),)
    report = patient_days(memberships, assignments, DateRange(date(2026, 1, 1), date(2026, 1, 4)))

    assert report.patient_days == frozenset({(uid(1), date(2026, 1, 2)), (uid(1), date(2026, 1, 3))})
    assert report.patient_days_total == 2
    assert report.patient_days_with_data == 0


def test_invoice_total_uses_device_minimum_commitment():
    report = patient_days(
        (Membership(patient_id=uid(1), tenant_id=uid(10), granted_at=ts(1)),),
        (AssignmentWindow("watch-1", uid(1), ts(1)),),
        DateRange(date(2026, 1, 1), date(2026, 1, 3)),
    )
    invoice = invoice_total(report, Licence(device_count=2, min_days_per_device=10, price_per_patient_day_uzs=1000))
    assert invoice.patient_days_total == 3
    assert invoice.min_commitment == 20
    assert invoice.billed_days == 20
    assert invoice.amount_uzs == 20_000


def test_invalid_billing_period_is_rejected():
    with pytest.raises(ValueError):
        patient_days((), (), DateRange(date(2026, 1, 2), date(2026, 1, 1)))
