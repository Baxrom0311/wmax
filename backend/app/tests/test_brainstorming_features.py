from datetime import datetime, timedelta, timezone
from uuid import uuid4


from app.domain.clinical_cohorts import ClinicalCohort, get_cohort_profile
from app.domain.peace_of_mind import CalmState, calculate_peace_of_mind
from app.domain.monetization_saas import ClinicBedQuota, check_sla_breach
from app.services.clinical_intake_service import generate_intake_summary


def test_clinical_cohort_profiles():
    general = get_cohort_profile("general")
    hyper = get_cohort_profile("hypertension")
    stroke = get_cohort_profile("post_stroke")

    assert general.cohort == ClinicalCohort.GENERAL
    assert hyper.amber_threshold < general.amber_threshold  # More sensitive
    assert stroke.critical_spo2 > general.critical_spo2    # Higher vigilance threshold


def test_peace_of_mind_calculation():
    # Stable patient
    pom_green = calculate_peace_of_mind(alert_level="green", worn=True)
    assert pom_green.state == CalmState.PEACEFUL
    assert pom_green.score >= 90

    # Device not worn
    pom_unworn = calculate_peace_of_mind(alert_level="green", worn=False)
    assert pom_unworn.state == CalmState.ATTENTION
    assert pom_unworn.score == 50

    # SOS signal
    pom_sos = calculate_peace_of_mind(alert_level="red", worn=True, recent_sos=True)
    assert pom_sos.state == CalmState.ALERT
    assert pom_sos.score == 10


def test_clinic_bed_quota_and_sla():
    quota = ClinicBedQuota(
        tenant_id=uuid4(),
        active_beds_allowed=10,
        current_active_beds=9,
        is_active=True,
    )
    assert quota.can_assign_bed is True

    full_quota = ClinicBedQuota(
        tenant_id=uuid4(),
        active_beds_allowed=10,
        current_active_beds=10,
        is_active=True,
    )
    assert full_quota.can_assign_bed is False

    # Check SLA breach for RED alert
    now = datetime.now(timezone.utc)
    old = now - timedelta(minutes=20)
    breached, escalate = check_sla_breach("red", created_at=old, now=now)
    assert breached is True
    assert escalate is False

    old_escalated = now - timedelta(minutes=40)
    breached, escalate = check_sla_breach("red", created_at=old_escalated, now=now)
    assert breached is True
    assert escalate is True


def test_clinical_intake_summary_generator():
    patient_id = uuid4()
    readings = [
        {"hr_mean": 72.0, "spo2": 98.0, "alert_level": "green", "is_night": False},
        {"hr_mean": 75.0, "spo2": 97.0, "alert_level": "green", "is_night": False},
        {"hr_mean": 80.0, "spo2": 95.0, "alert_level": "amber", "is_night": True},
    ]
    summary = generate_intake_summary(
        patient_id=patient_id,
        patient_name="Aziz Rahimov",
        readings=readings,
        cohort_name="Arterial gipertoniya",
    )
    assert summary.patient_id == patient_id
    assert summary.monitoring_days == 14
    assert summary.hr_avg > 70
    assert summary.anomaly_events_count == 1
    assert "Aziz Rahimov" in summary.summary_html
