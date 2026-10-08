"""Persist task notification delivery acknowledgements.

Revision ID: durable_task_delivery
Revises: patient_access_links
Create Date: 2026-10-08 09:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "durable_task_delivery"
down_revision: Union[str, Sequence[str], None] = "patient_access_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("reminder_notified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("escalation_notified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "escalation_notified_at")
    op.drop_column("tasks", "reminder_notified_at")
