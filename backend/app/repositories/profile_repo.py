from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.models.address import PatientAddress
from app.models.admission import PatientAdmission
from app.models.allergy import PatientAllergy
from app.models.audit import ProfileAudit
from app.models.condition import PatientCondition
from app.models.measurement import PatientMeasurement
from app.models.medication import PatientMedication
from app.models.patient import Patient
from app.models.risk_factor import PatientRiskFactor
from app.repositories.audited_repo import AuditedRepository


class ProfileRepository(AuditedRepository):
    """Repository handling CRUD and audit logging for patient clinical profiles."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # Addresses
    async def list_addresses(self, patient_id: uuid.UUID) -> list[PatientAddress]:
        stmt = (
            select(PatientAddress)
            .where(PatientAddress.patient_id == patient_id)
            .order_by(desc(PatientAddress.is_primary), desc(PatientAddress.created_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_address(self, address_id: uuid.UUID, patient_id: uuid.UUID) -> PatientAddress | None:
        stmt = select(PatientAddress).where(
            PatientAddress.id == address_id,
            PatientAddress.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_address(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientAddress:
        is_primary = data.get("is_primary", False)
        if is_primary:
            # Clear previous primary
            curr = await self.list_addresses(patient_id)
            for addr in curr:
                if addr.is_primary:
                    addr.is_primary = False

        address = PatientAddress(patient_id=patient_id, **data)
        self.session.add(address)
        await self.session.flush()

        if is_primary:
            pat = await self.session.get(Patient, patient_id)
            if pat:
                pat.primary_address_id = address.id

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_addresses",
            entity_id=str(address.id),
            action="create",
            changes=data,
        )
        return address

    async def set_primary_address(
        self,
        address_id: uuid.UUID,
        patient_id: uuid.UUID,
        principal: CurrentUser,
    ) -> PatientAddress | None:
        address = await self.get_address(address_id, patient_id)
        if not address:
            return None

        # Reset all others
        addrs = await self.list_addresses(patient_id)
        for a in addrs:
            a.is_primary = (a.id == address_id)

        pat = await self.session.get(Patient, patient_id)
        if pat:
            pat.primary_address_id = address_id

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_addresses",
            entity_id=str(address.id),
            action="update",
            changes={"is_primary": {"old": False, "new": True}},
        )
        return address

    async def delete_address(
        self,
        address_id: uuid.UUID,
        patient_id: uuid.UUID,
        principal: CurrentUser,
    ) -> bool:
        address = await self.get_address(address_id, patient_id)
        if not address:
            return False

        pat = await self.session.get(Patient, patient_id)
        if pat and pat.primary_address_id == address_id:
            pat.primary_address_id = None

        await self.session.delete(address)
        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_addresses",
            entity_id=str(address_id),
            action="delete",
            changes={"deleted": True},
        )
        return True

    # Conditions
    async def list_conditions(self, patient_id: uuid.UUID) -> list[PatientCondition]:
        stmt = (
            select(PatientCondition)
            .where(PatientCondition.patient_id == patient_id)
            .order_by(desc(PatientCondition.is_active), desc(PatientCondition.created_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_condition(self, condition_id: uuid.UUID, patient_id: uuid.UUID) -> PatientCondition | None:
        stmt = select(PatientCondition).where(
            PatientCondition.id == condition_id,
            PatientCondition.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_condition(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientCondition:
        condition = PatientCondition(
            patient_id=patient_id,
            recorded_by=principal.id,
            **data,
        )
        self.session.add(condition)
        await self.session.flush()

        if data.get("kind") == "primary":
            pat = await self.session.get(Patient, patient_id)
            if pat:
                pat.primary_icd10 = condition.icd10

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_conditions",
            entity_id=str(condition.id),
            action="create",
            changes=data,
        )
        return condition

    # Medications
    async def list_medications(self, patient_id: uuid.UUID) -> list[PatientMedication]:
        stmt = (
            select(PatientMedication)
            .where(PatientMedication.patient_id == patient_id)
            .order_by(desc(PatientMedication.stopped_at.is_(None)), desc(PatientMedication.created_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_medication(self, med_id: uuid.UUID, patient_id: uuid.UUID) -> PatientMedication | None:
        stmt = select(PatientMedication).where(
            PatientMedication.id == med_id,
            PatientMedication.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_medication(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientMedication:
        med = PatientMedication(
            patient_id=patient_id,
            prescribed_by=principal.id,
            **data,
        )
        self.session.add(med)
        await self.session.flush()

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_medications",
            entity_id=str(med.id),
            action="create",
            changes=data,
        )
        return med

    # Allergies
    async def list_allergies(self, patient_id: uuid.UUID) -> list[PatientAllergy]:
        stmt = (
            select(PatientAllergy)
            .where(PatientAllergy.patient_id == patient_id)
            .order_by(desc(PatientAllergy.created_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_allergy(self, allergy_id: uuid.UUID, patient_id: uuid.UUID) -> PatientAllergy | None:
        stmt = select(PatientAllergy).where(
            PatientAllergy.id == allergy_id,
            PatientAllergy.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_allergy(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientAllergy:
        allergy = PatientAllergy(patient_id=patient_id, **data)
        self.session.add(allergy)
        await self.session.flush()

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_allergies",
            entity_id=str(allergy.id),
            action="create",
            changes=data,
        )
        return allergy

    # Measurements
    async def list_measurements(self, patient_id: uuid.UUID, limit: int = 50) -> list[PatientMeasurement]:
        stmt = (
            select(PatientMeasurement)
            .where(PatientMeasurement.patient_id == patient_id)
            .order_by(desc(PatientMeasurement.recorded_at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_measurement(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientMeasurement:
        measurement = PatientMeasurement(patient_id=patient_id, **data)
        self.session.add(measurement)
        await self.session.flush()

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_measurements",
            entity_id=str(measurement.id),
            action="create",
            changes=data,
        )
        return measurement

    # Risk factors
    async def get_risk_factors(self, patient_id: uuid.UUID) -> PatientRiskFactor | None:
        return await self.session.get(PatientRiskFactor, patient_id)

    async def upsert_risk_factors(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientRiskFactor:
        rf = await self.get_risk_factors(patient_id)
        if not rf:
            rf = PatientRiskFactor(patient_id=patient_id, **data)
            self.session.add(rf)
            await self.session.flush()
            await self.record_audit(
                patient_id=patient_id,
                actor_kind=principal.role,
                actor_id=principal.id,
                entity="patient_risk_factors",
                entity_id=str(patient_id),
                action="create",
                changes=data,
            )
        else:
            await self.update_with_audit(
                instance=rf,
                changes=data,
                principal=principal,
                patient_id=patient_id,
            )
        return rf

    # Admissions
    async def list_admissions(self, patient_id: uuid.UUID) -> list[PatientAdmission]:
        stmt = (
            select(PatientAdmission)
            .where(PatientAdmission.patient_id == patient_id)
            .order_by(desc(PatientAdmission.admitted_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_admission(
        self,
        patient_id: uuid.UUID,
        data: dict[str, Any],
        principal: CurrentUser,
    ) -> PatientAdmission:
        adm = PatientAdmission(patient_id=patient_id, **data)
        self.session.add(adm)
        await self.session.flush()

        await self.record_audit(
            patient_id=patient_id,
            actor_kind=principal.role,
            actor_id=principal.id,
            entity="patient_admissions",
            entity_id=str(adm.id),
            action="create",
            changes=data,
        )
        return adm

    # Audit list
    async def list_audit_entries(self, patient_id: uuid.UUID, limit: int = 100) -> list[ProfileAudit]:
        stmt = (
            select(ProfileAudit)
            .where(ProfileAudit.patient_id == patient_id)
            .order_by(desc(ProfileAudit.at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
