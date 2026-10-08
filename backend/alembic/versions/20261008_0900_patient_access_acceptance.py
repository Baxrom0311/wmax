"""Require caregivers to accept patient access invitations.

Revision ID: patient_access_acceptance
Revises: device_enrollment_claim
Create Date: 2026-10-08 09:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "patient_access_acceptance"
down_revision: Union[str, Sequence[str], None] = "device_enrollment_claim"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing grants remain pending until the caregiver explicitly accepts.
    op.add_column("patient_access", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("patient_access", "accepted_at")
