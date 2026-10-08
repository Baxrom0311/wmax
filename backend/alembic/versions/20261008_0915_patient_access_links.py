"""Persist random caregiver link selectors.

Revision ID: patient_access_links
Revises: patient_access_acceptance
Create Date: 2026-10-08 09:15:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "patient_access_links"
down_revision: Union[str, Sequence[str], None] = "patient_access_acceptance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patient_access", sa.Column("access_token", sa.Text(), nullable=True))
    op.add_column("patient_access", sa.Column("access_token_created_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_patient_access_link_token", "patient_access", ["access_token"])


def downgrade() -> None:
    op.drop_constraint("uq_patient_access_link_token", "patient_access", type_="unique")
    op.drop_column("patient_access", "access_token_created_at")
    op.drop_column("patient_access", "access_token")
