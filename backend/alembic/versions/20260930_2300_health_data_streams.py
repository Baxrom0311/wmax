"""health data streams

Revision ID: health_data_streams
Revises: c1057cb46015
Create Date: 2026-09-30 23:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "health_data_streams"
down_revision: Union[str, Sequence[str], None] = "c1057cb46015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _execute_many(sql: str) -> None:
    for statement in (part.strip() for part in sql.split(";")):
        if statement:
            op.execute(statement)


def upgrade() -> None:
    op.create_table(
        "health_samples",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("device_assignment_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("value_num", sa.Float(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality", sa.Float(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_assignment_id"], ["device_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_health_sample_idempotency"),
    )
    op.create_index("idx_health_samples_device_time", "health_samples", ["device_id", "recorded_at"])
    op.create_index("idx_health_samples_patient_metric_time", "health_samples", ["patient_id", "metric", "recorded_at"])

    op.create_table(
        "sleep_sessions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stages", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_sleep_session_idempotency"),
    )
    op.create_index("idx_sleep_sessions_patient_start", "sleep_sessions", ["patient_id", "start_time"])

    op.create_table(
        "exercise_sessions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column("exercise_type", sa.Text(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("route", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_exercise_session_idempotency"),
    )
    op.create_index("idx_exercise_sessions_patient_start", "exercise_sessions", ["patient_id", "start_time"])

    op.create_table(
        "device_sync_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=True),
        sa.Column("accepted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "source", "batch_id", name="uq_device_sync_batch"),
    )
    op.create_index("idx_device_sync_events_device_time", "device_sync_events", ["device_id", "received_at"])

    _execute_many(
        """
        ALTER TABLE health_samples ENABLE ROW LEVEL SECURITY;
        ALTER TABLE health_samples FORCE ROW LEVEL SECURITY;
        CREATE POLICY health_samples_scope ON health_samples
        FOR ALL
        USING (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = health_samples.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        )
        WITH CHECK (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = health_samples.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        );

        ALTER TABLE sleep_sessions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE sleep_sessions FORCE ROW LEVEL SECURITY;
        CREATE POLICY sleep_sessions_scope ON sleep_sessions
        FOR ALL
        USING (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = sleep_sessions.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        )
        WITH CHECK (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = sleep_sessions.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        );

        ALTER TABLE exercise_sessions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE exercise_sessions FORCE ROW LEVEL SECURITY;
        CREATE POLICY exercise_sessions_scope ON exercise_sessions
        FOR ALL
        USING (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = exercise_sessions.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        )
        WITH CHECK (
            current_setting('wmax.bypass', true) = 'on'
            OR EXISTS (SELECT 1 FROM patients p WHERE p.id = exercise_sessions.patient_id)
            OR device_id::text = current_setting('wmax.device_id', true)
        );

        ALTER TABLE device_sync_events ENABLE ROW LEVEL SECURITY;
        ALTER TABLE device_sync_events FORCE ROW LEVEL SECURITY;
        CREATE POLICY device_sync_events_scope ON device_sync_events
        FOR ALL
        USING (
            current_setting('wmax.bypass', true) = 'on'
            OR device_id::text = current_setting('wmax.device_id', true)
        )
        WITH CHECK (
            current_setting('wmax.bypass', true) = 'on'
            OR device_id::text = current_setting('wmax.device_id', true)
        );
        """
    )


def downgrade() -> None:
    op.drop_index("idx_device_sync_events_device_time", table_name="device_sync_events")
    op.drop_table("device_sync_events")
    op.drop_index("idx_exercise_sessions_patient_start", table_name="exercise_sessions")
    op.drop_table("exercise_sessions")
    op.drop_index("idx_sleep_sessions_patient_start", table_name="sleep_sessions")
    op.drop_table("sleep_sessions")
    op.drop_index("idx_health_samples_patient_metric_time", table_name="health_samples")
    op.drop_index("idx_health_samples_device_time", table_name="health_samples")
    op.drop_table("health_samples")
