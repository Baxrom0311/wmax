"""Current consent and lifecycle rules shared by ingest, tasks, delivery and auth.

Both ingest transports, the escalation worker and notification delivery use
these expressions so that a revoked consent or a death stops every workflow
from one place (IDEOLOGY B5, J2).
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import exists, func, or_, select

from app.models import Patient, PatientAccess, PatientConsent, PatientMembership

# IDEOLOGY J2: after death the family keeps read access to history for 90 days.
FAMILY_HISTORY_AFTER_DEATH = timedelta(days=90)


def clinical_consent(patient_id, tenant_id):
    """Active clinical_monitoring consent covering this clinic."""
    return exists(select(PatientConsent.id).where(
        PatientConsent.patient_id == patient_id,
        PatientConsent.scope == "clinical_monitoring",
        PatientConsent.granted.is_(True), PatientConsent.revoked_at.is_(None),
        or_(PatientConsent.target_tenant_id.is_(None), PatientConsent.target_tenant_id == tenant_id),
    ))


def family_consent(patient_id, account_id):
    """Accepted caregiver access backed by the patient's active family consent."""
    return exists(select(PatientAccess.id).join(
        PatientConsent, PatientConsent.patient_id == PatientAccess.patient_id,
    ).where(
        PatientAccess.patient_id == patient_id,
        PatientAccess.account_id == account_id,
        PatientAccess.accepted_at.is_not(None), PatientAccess.revoked_at.is_(None),
        PatientConsent.target_account_id == PatientAccess.account_id,
        PatientConsent.scope == "family_access", PatientConsent.granted.is_(True),
        PatientConsent.revoked_at.is_(None),
    ))


def monitoring_patient_ids():
    """Living patients with a consented clinic or a consented caregiver."""
    clinical = exists(select(PatientMembership.id).where(
        PatientMembership.patient_id == Patient.id,
        PatientMembership.kind == "care",
        PatientMembership.revoked_at.is_(None),
        clinical_consent(Patient.id, PatientMembership.tenant_id),
    ))
    family = exists(select(PatientAccess.id).where(
        PatientAccess.patient_id == Patient.id,
        family_consent(Patient.id, PatientAccess.account_id),
    ))
    return select(Patient.id).where(Patient.deceased_at.is_(None), or_(clinical, family))


async def monitoring_allowed(session, patient_id) -> bool:
    result = await session.execute(monitoring_patient_ids().where(Patient.id == patient_id))
    return result.scalar_one_or_none() is not None


def family_history_visible():
    """Patient is alive, or died within the family history window."""
    return or_(
        Patient.deceased_at.is_(None),
        Patient.deceased_at > func.now() - FAMILY_HISTORY_AFTER_DEATH,
    )
