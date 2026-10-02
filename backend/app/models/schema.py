from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


LangEnum = ENUM("uz", "ru", "en", name="lang_code", create_type=False)
TenantKindEnum = ENUM("ovabmu", "polyclinic", "hospital", "network", name="tenant_kind", create_type=False)
TenantRoleEnum = ENUM("nurse", "doctor", "head_doctor", "admin", "dispatcher", name="tenant_role", create_type=False)
MembershipKindEnum = ENUM("care", name="membership_kind", create_type=False)
AccessRoleEnum = ENUM("payer", "caregiver", name="access_role", create_type=False)
ConsentScopeEnum = ENUM("family_access", "clinical_monitoring", name="consent_scope", create_type=False)
ConsentMethodEnum = ENUM("sms", "in_app", "verbal_by_clinician", name="consent_method", create_type=False)
DeviceStatusEnum = ENUM("in_stock", "assigned", "maintenance", "lost", "retired", name="device_status", create_type=False)
DeviceProvenanceEnum = ENUM("clinic_issued", "self_purchased", "unknown", name="device_provenance", create_type=False)
AlertLevelEnum = ENUM("green", "amber", "red", "no_data", name="alert_level", create_type=False)
TaskKindEnum = ENUM("clinical", "technical", name="task_kind", create_type=False)
TaskStatusEnum = ENUM("open", "acknowledged", "done", "overdue", "cancelled", name="task_status", create_type=False)
SubPlanEnum = ENUM("free", "premium", "premium_doc", name="sub_plan", create_type=False)
SubStatusEnum = ENUM("trialing", "active", "past_due", "lapsed", name="sub_status", create_type=False)
NotifyChannelEnum = ENUM("push", "telegram", "sms", "voice", name="notify_channel", create_type=False)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = uuid_pk()
    phone: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_lang: Mapped[Literal["uz", "ru", "en"]] = mapped_column(LangEnum, nullable=False, server_default="uz")
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default="Asia/Tashkent")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    password_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AccountIdentity(Base):
    __tablename__ = "account_identities"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_identity"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("sex IS NULL OR sex IN ('m','f')", name="chk_patient_sex"),
        Index("idx_patients_phone", "phone", postgresql_where=text("phone IS NOT NULL")),
        Index("idx_patients_alive", "id", postgresql_where=text("deceased_at IS NULL")),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    sex: Mapped[str | None] = mapped_column(CHAR(1))
    phone: Mapped[str | None] = mapped_column(Text)
    jshshir: Mapped[str | None] = mapped_column(Text)
    preferred_lang: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz")
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    district: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    phase: Mapped[str] = mapped_column(Text, nullable=False, server_default="calib")
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    primary_icd10: Mapped[str | None] = mapped_column(Text)
    blood_group: Mapped[str | None] = mapped_column(Text)
    rh: Mapped[str | None] = mapped_column(Text)
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discharge_date: Mapped[date | None] = mapped_column(Date)
    baseline_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    baseline_approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    device_id: Mapped[str | None] = mapped_column(Text)
    pin_hash: Mapped[str | None] = mapped_column(Text)
    deceased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deceased_marked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    deceased_confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    @property
    def age(self) -> int:
        if hasattr(self, "_age"):
            return self._age
        if not self.birth_date:
            return 0
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @age.setter
    def age(self, value: int) -> None:
        self._age = value


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    kind: Mapped[str] = mapped_column(TenantKindEnum, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    legal_name: Mapped[str | None] = mapped_column(Text)
    tax_id: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TenantMember(Base):
    __tablename__ = "tenant_members"
    __table_args__ = (UniqueConstraint("tenant_id", "account_id", name="uq_member"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(TenantRoleEnum, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemberTerritory(Base):
    __tablename__ = "member_territories"
    __table_args__ = (UniqueConstraint("tenant_member_id", "mahalla", name="uq_member_mahalla"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant_members.id", ondelete="CASCADE"), nullable=False)
    mahalla: Mapped[str] = mapped_column(Text, nullable=False)


class PatientMembership(Base):
    __tablename__ = "patient_memberships"
    __table_args__ = (
        Index("idx_one_care_owner", "patient_id", unique=True, postgresql_where=text("kind = 'care' AND revoked_at IS NULL")),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(MembershipKindEnum, nullable=False, server_default="care")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)
    baseline_decision: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PatientAccess(Base):
    __tablename__ = "patient_access"
    __table_args__ = (
        UniqueConstraint("patient_id", "account_id", name="uq_access"),
        Index("idx_access_active", "account_id", postgresql_where=text("revoked_at IS NULL")),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(AccessRoleEnum, nullable=False, server_default="caregiver")
    relation: Mapped[str | None] = mapped_column(Text)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PatientConsent(Base):
    __tablename__ = "patient_consents"
    __table_args__ = (Index("idx_consents_patient", "patient_id", "scope"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(ConsentScopeEnum, nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    method: Mapped[str] = mapped_column(ConsentMethodEnum, nullable=False)
    witnessed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    target_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    target_tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(Text)


class PatientAddress(Base):
    __tablename__ = "patient_addresses"
    __table_args__ = (Index("idx_one_primary_address", "patient_id", unique=True, postgresql_where=text("is_primary")),)

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    region: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(Text, nullable=False)
    mahalla: Mapped[str | None] = mapped_column(Text)
    street: Mapped[str | None] = mapped_column(Text)
    house: Mapped[str | None] = mapped_column(Text)
    flat: Mapped[str | None] = mapped_column(Text)
    landmark: Mapped[str | None] = mapped_column(Text)
    entrance_note: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (CheckConstraint("num_nonnulls(owner_tenant_id, owner_patient_id) <= 1", name="chk_single_owner"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    serial: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False, server_default="tier1_wearos")
    ownership: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(DeviceStatusEnum, nullable=False, server_default="in_stock")
    owner_tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"))
    owner_patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"))
    battery_health_pct: Mapped[int | None] = mapped_column(SmallInteger)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bound_phone_node_id: Mapped[str | None] = mapped_column(Text)
    bound_phone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @property
    def serial_number(self) -> str:
        return self.serial

    @serial_number.setter
    def serial_number(self, value: str) -> None:
        self.serial = value

    @property
    def model_name(self) -> str:
        return self.model

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model = value


class DeviceCredential(Base):
    __tablename__ = "device_credentials"
    __table_args__ = (
        Index(
            "uq_device_credentials_active_device",
            "device_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    secret_hash: Mapped[str] = mapped_column(Text, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeviceEnrollmentCode(Base):
    __tablename__ = "device_enrollment_codes"

    id: Mapped[uuid.UUID] = uuid_pk()
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    code_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DeviceAssignment(Base):
    __tablename__ = "device_assignments"
    __table_args__ = (Index("idx_assignment_window", "device_id", "assigned_at", "released_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    provenance: Mapped[str] = mapped_column(DeviceProvenanceEnum, nullable=False, server_default="unknown")
    supervised: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    deposit_uzs: Mapped[int | None] = mapped_column(BigInteger)
    rental_uzs_month: Mapped[int | None] = mapped_column(BigInteger)
    due_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    return_notes: Mapped[str | None] = mapped_column(Text)
    deposit_refunded: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrphanReading(Base):
    __tablename__ = "orphan_readings"
    __table_args__ = (
        UniqueConstraint("device_id", "window_start", name="uq_orphan_key"),
        Index("idx_orphan_unresolved", "device_id", "window_start", postgresql_where=text("resolved_at IS NULL")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    resolved_to_patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("device_id", "window_start", name="uq_reading_key"),
        {"postgresql_partition_by": "RANGE (window_start)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    device_assignment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("device_assignments.id"))
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hr_mean: Mapped[float | None] = mapped_column(Float)
    hr_min: Mapped[float | None] = mapped_column(Float)
    hr_max: Mapped[float | None] = mapped_column(Float)
    rmssd: Mapped[float | None] = mapped_column(Float)
    sdnn: Mapped[float | None] = mapped_column(Float)
    spo2: Mapped[float | None] = mapped_column(Float)
    skin_temp: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    rr_est: Mapped[float | None] = mapped_column(Float)
    sleep_frag: Mapped[float | None] = mapped_column(Float)
    worn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    worn_pct: Mapped[int | None] = mapped_column(SmallInteger)
    samples_n: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    battery: Mapped[int | None] = mapped_column(SmallInteger)
    device_clock_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clock_offset_ms: Mapped[int | None] = mapped_column(Integer)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    provenance: Mapped[str] = mapped_column(DeviceProvenanceEnum, nullable=False, server_default="unknown")
    attributed_by: Mapped[str | None] = mapped_column(Text)

    @property
    def ts(self) -> datetime:
        return self.window_start


class HealthSample(Base):
    __tablename__ = "health_samples"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_health_sample_idempotency"),
        Index("idx_health_samples_patient_metric_time", "patient_id", "metric", "recorded_at"),
        Index("idx_health_samples_device_time", "device_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    device_assignment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("device_assignments.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    metric: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(Text)
    value_num: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quality: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_sleep_session_idempotency"),
        Index("idx_sleep_sessions_patient_start", "patient_id", "start_time"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stages: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_exercise_session_idempotency"),
        Index("idx_exercise_sessions_patient_start", "patient_id", "start_time"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    exercise_type: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    route: Mapped[list | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DeviceSyncEvent(Base):
    __tablename__ = "device_sync_events"
    __table_args__ = (
        UniqueConstraint("device_id", "source", "batch_id", name="uq_device_sync_batch"),
        Index("idx_device_sync_events_device_time", "device_id", "received_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    batch_id: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int | None] = mapped_column(BigInteger)
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Baseline(Base):
    __tablename__ = "baselines"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    param: Mapped[str] = mapped_column(Text, primary_key=True)
    time_window: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    median: Mapped[float] = mapped_column(Float, nullable=False)
    mad: Mapped[float] = mapped_column(Float, nullable=False)
    n_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    includes_attributed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("patient_id", "ts", name="uq_alert"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(AlertLevelEnum, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    triggered_params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    anomaly_score: Mapped[float | None] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(Text)
    data_quality: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (CheckConstraint("assignee_account_id IS NOT NULL", name="chk_assignee"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    assignee_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    kind: Mapped[str] = mapped_column(TaskKindEnum, nullable=False)
    status: Mapped[str] = mapped_column(TaskStatusEnum, nullable=False, server_default="open")
    alert_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("alerts.id", ondelete="SET NULL"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @property
    def type(self) -> str:
        return self.kind

    @type.setter
    def type(self, value: str) -> None:
        self.kind = "clinical" if value in {"active_call", "red_alert"} else value

    @property
    def confirmed_at(self) -> datetime | None:
        return self.done_at

    @confirmed_at.setter
    def confirmed_at(self, value: datetime | None) -> None:
        self.done_at = value

class PatientSubscription(Base):
    __tablename__ = "patient_subscriptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(SubPlanEnum, nullable=False, server_default="free")
    status: Mapped[str] = mapped_column(SubStatusEnum, nullable=False, server_default="trialing")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_paid_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    provider: Mapped[str | None] = mapped_column(Text)
    provider_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class TenantLicence(Base):
    __tablename__ = "tenant_licences"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    device_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    min_days_per_device: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    price_per_patient_day_uzs: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")
    intake_blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BillingDay(Base):
    __tablename__ = "billing_days"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    had_data: Mapped[bool] = mapped_column(Boolean, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    patient_days_total: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_days_with_data: Mapped[int] = mapped_column(Integer, nullable=False)
    min_commitment: Mapped[int] = mapped_column(Integer, nullable=False)
    billed_days: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_uzs: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="open")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("provider", "provider_ref", name="uq_payment_provider_ref"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"))
    patient_subscription_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_subscriptions.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    provider_ref: Mapped[str] = mapped_column(Text, nullable=False)
    amount_uzs: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    recipient_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    alert_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("alerts.id", ondelete="SET NULL"))
    level: Mapped[str | None] = mapped_column(AlertLevelEnum)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NotificationAttempt(Base):
    __tablename__ = "notification_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(NotifyChannelEnum, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    error: Mapped[str | None] = mapped_column(Text)


class RealtimeEventOutbox(Base):
    __tablename__ = "realtime_events"
    __table_args__ = (
        Index("idx_realtime_events_topic_id", "topic", "id"),
        Index("idx_realtime_events_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    icd10: Mapped[str | None] = mapped_column(Text)
    name_uz: Mapped[str] = mapped_column(Text, nullable=False)
    name_ru: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(Text)
    severity_note: Mapped[str | None] = mapped_column(Text)
    diagnosed_at: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PatientMedication(Base):
    __tablename__ = "patient_medications"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    dose: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[date | None] = mapped_column(Date)
    stopped_at: Mapped[date | None] = mapped_column(Date)
    affects_params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    prescribed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MedicationResponse(Base):
    __tablename__ = "medication_responses"

    id: Mapped[uuid.UUID] = uuid_pk()
    medication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_medications.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    baseline_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    baseline_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_effects: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    verdict: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PatientOutcome(Base):
    __tablename__ = "patient_outcomes"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    icd10: Mapped[str | None] = mapped_column(Text)
    predicted_by_alert_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("alerts.id", ondelete="SET NULL"))
    source: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    questions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = uuid_pk()
    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    substance: Mapped[str] = mapped_column(Text, nullable=False)
    reaction: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default="moderate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PatientMeasurement(Base):
    __tablename__ = "patient_measurements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    sbp_mmhg: Mapped[int | None] = mapped_column(SmallInteger)
    dbp_mmhg: Mapped[int | None] = mapped_column(SmallInteger)
    source: Mapped[str | None] = mapped_column(Text)


class PatientRiskFactor(Base):
    __tablename__ = "patient_risk_factors"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    smoking: Mapped[str | None] = mapped_column(Text)
    smoking_pack_years: Mapped[float | None] = mapped_column(Float)
    alcohol: Mapped[str | None] = mapped_column(Text)
    diabetes: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    hypertension: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    ckd: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    physical_activity: Mapped[str | None] = mapped_column(Text)
    lives_alone: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    mobility: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SosEvent(Base):
    __tablename__ = "sos_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SosNotification(Base):
    __tablename__ = "sos_notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    sos_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(account_id, relative_id, patient_id) = 1",
            name="chk_refresh_token_owner",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"))
    relative_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_access.id", ondelete="CASCADE"))
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ProfileAudit(Base):
    __tablename__ = "profile_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    actor_kind: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    request_id: Mapped[str | None] = mapped_column(Text)


class TwinSnapshot(Base):
    __tablename__ = "twin_snapshots"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


# Backward-compatible import names while services are rewritten.
User = Account
Relative = PatientAccess
Subscription = PatientSubscription
PatientAdmission = PatientOutcome
