"""SOS lifecycle columns, per-recipient durable delivery, address fields.

Revision ID: durable_alert_sos_delivery
Revises: durable_task_delivery
Create Date: 2026-10-16 12:00:00

Additive only. Legacy rows get explicit values so the new workers do not
re-deliver or re-route history:
  * notifications created by the old notifier were written only after a send,
    so they become `delivered`;
  * alerts written before task routing was persisted become `not_required`;
  * SOS rows from before the lifecycle columns become `legacy`, which is not an
    active status, rather than being reported as resolved.
Patient addresses gain the fields the profile API and SOS snapshot already
read and write (kind, geo_source, geo_accuracy_m, updated_at).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "durable_alert_sos_delivery"
down_revision: Union[str, Sequence[str], None] = "durable_task_delivery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sos_events", sa.Column("status", sa.Text(), server_default="raised", nullable=False))
    op.add_column("sos_events", sa.Column("raised_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("sos_events", sa.Column("address_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False))
    op.add_column("sos_events", sa.Column("clinical_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False))
    op.add_column("sos_events", sa.Column("vitals_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("sos_events", sa.Column("device_lat", sa.Float(), nullable=True))
    op.add_column("sos_events", sa.Column("device_lon", sa.Float(), nullable=True))
    op.add_column("sos_events", sa.Column("device_accuracy_m", sa.Float(), nullable=True))
    op.add_column("sos_events", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sos_events", sa.Column("acknowledged_by", sa.UUID(), nullable=True))
    op.add_column("sos_events", sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sos_events", sa.Column("dispatch_method", sa.Text(), nullable=True))
    op.add_column("sos_events", sa.Column("dispatch_ref", sa.Text(), nullable=True))
    op.add_column("sos_events", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sos_events", sa.Column("resolved_by", sa.UUID(), nullable=True))
    op.add_column("sos_events", sa.Column("resolution_note", sa.Text(), nullable=True))
    op.add_column("sos_events", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_sos_events_acknowledged_by", "sos_events", "accounts", ["acknowledged_by"], ["id"])
    op.create_foreign_key("fk_sos_events_resolved_by", "sos_events", "accounts", ["resolved_by"], ["id"])
    op.execute("UPDATE sos_events SET status = 'legacy', raised_at = created_at, device_lat = lat, device_lon = lon")
    op.create_index(
        "idx_sos_events_active", "sos_events", ["raised_at"],
        postgresql_where=sa.text("status IN ('raised','acknowledged','dispatched')"),
    )

    op.add_column("alerts", sa.Column("task_kind", postgresql.ENUM(name="task_kind", create_type=False), nullable=True))
    op.add_column("alerts", sa.Column("task_routing_status", sa.Text(), server_default="not_required", nullable=False))
    op.add_column("alerts", sa.Column("task_routing_error", sa.Text(), nullable=True))

    op.add_column("notifications", sa.Column("sos_event_id", sa.UUID(), nullable=True))
    op.add_column("notifications", sa.Column("message", sa.Text(), nullable=True))
    op.add_column("notifications", sa.Column("delivery_status", sa.Text(), server_default="pending", nullable=False))
    op.add_column("notifications", sa.Column("attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("notifications", sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_foreign_key(
        "fk_notifications_sos_event_id", "notifications", "sos_events", ["sos_event_id"], ["id"], ondelete="CASCADE",
    )
    op.execute(
        "UPDATE notifications SET delivery_status = CASE WHEN acknowledged_at IS NULL "
        "THEN 'delivered' ELSE 'acknowledged' END"
    )
    op.create_index(
        "uq_notification_alert_recipient", "notifications", ["alert_id", "recipient_account_id"], unique=True,
        postgresql_where=sa.text("alert_id IS NOT NULL AND recipient_account_id IS NOT NULL"),
    )
    op.create_index(
        "uq_notification_sos_recipient", "notifications", ["sos_event_id", "recipient_account_id"], unique=True,
        postgresql_where=sa.text("sos_event_id IS NOT NULL AND recipient_account_id IS NOT NULL"),
    )
    op.create_index(
        "idx_notifications_due", "notifications", ["next_attempt_at"],
        postgresql_where=sa.text("delivery_status = 'pending'"),
    )

    op.add_column("notification_attempts", sa.Column("provider_ref", sa.Text(), nullable=True))

    op.add_column("patient_addresses", sa.Column("kind", sa.Text(), server_default="home", nullable=False))
    op.add_column("patient_addresses", sa.Column("geo_source", sa.Text(), nullable=True))
    op.add_column("patient_addresses", sa.Column("geo_accuracy_m", sa.Float(), nullable=True))
    op.add_column("patient_addresses", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.execute("UPDATE patient_addresses SET updated_at = created_at")


def downgrade() -> None:
    op.drop_column("patient_addresses", "updated_at")
    op.drop_column("patient_addresses", "geo_accuracy_m")
    op.drop_column("patient_addresses", "geo_source")
    op.drop_column("patient_addresses", "kind")

    op.drop_column("notification_attempts", "provider_ref")

    op.drop_index("idx_notifications_due", table_name="notifications", postgresql_where=sa.text("delivery_status = 'pending'"))
    op.drop_index("uq_notification_sos_recipient", table_name="notifications")
    op.drop_index("uq_notification_alert_recipient", table_name="notifications")
    op.drop_constraint("fk_notifications_sos_event_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "next_attempt_at")
    op.drop_column("notifications", "attempts")
    op.drop_column("notifications", "delivery_status")
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "sos_event_id")

    op.drop_column("alerts", "task_routing_error")
    op.drop_column("alerts", "task_routing_status")
    op.drop_column("alerts", "task_kind")

    op.drop_index("idx_sos_events_active", table_name="sos_events")
    op.drop_constraint("fk_sos_events_resolved_by", "sos_events", type_="foreignkey")
    op.drop_constraint("fk_sos_events_acknowledged_by", "sos_events", type_="foreignkey")
    for column in (
        "cancelled_at", "resolution_note", "resolved_by", "resolved_at", "dispatch_ref",
        "dispatch_method", "dispatched_at", "acknowledged_by", "acknowledged_at",
        "device_accuracy_m", "device_lon", "device_lat", "vitals_snapshot",
        "clinical_snapshot", "address_snapshot", "raised_at", "status",
    ):
        op.drop_column("sos_events", column)
