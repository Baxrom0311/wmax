"""one-time device enrollment claim

Revision ID: device_enrollment_claim
Revises: health_data_streams
Create Date: 2026-10-01 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "device_enrollment_claim"
down_revision: Union[str, Sequence[str], None] = "health_data_streams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "device_credentials_device_id_key",
        "device_credentials",
        type_="unique",
    )
    op.create_index(
        "uq_device_credentials_active_device",
        "device_credentials",
        ["device_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.add_column(
        "device_enrollment_codes",
        sa.Column("attempts", sa.SmallInteger(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("device_enrollment_codes", "attempts")
    op.drop_index(
        "uq_device_credentials_active_device",
        table_name="device_credentials",
    )
    op.create_unique_constraint(
        "device_credentials_device_id_key",
        "device_credentials",
        ["device_id"],
    )
