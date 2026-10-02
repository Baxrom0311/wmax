from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.core.rls import set_rls_context


@pytest.mark.asyncio
async def test_set_rls_context_uses_set_local_only():
    calls: list[tuple[str, dict[str, str]]] = []

    class Session:
        async def execute(self, stmt, params):
            calls.append((str(stmt), params))

    account_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    device_id = uuid.uuid4()

    await set_rls_context(
        Session(),
        account_id=account_id,
        tenant_ids=[tenant_id],
        patient_ids=[tenant_id],
        device_id=device_id,
        bypass=False,
    )

    assert [sql for sql, _ in calls] == [
        "SET LOCAL wmax.account_id = :account_id",
        "SET LOCAL wmax.tenant_ids = :tenant_ids",
        "SET LOCAL wmax.patient_ids = :patient_ids",
        "SET LOCAL wmax.device_id = :device_id",
        "SET LOCAL wmax.bypass = :bypass",
    ]
    assert calls[0][1]["account_id"] == str(account_id)
    assert calls[1][1]["tenant_ids"] == str(tenant_id)
    assert calls[2][1]["patient_ids"] == str(tenant_id)
    assert calls[3][1]["device_id"] == str(device_id)
    assert calls[4][1]["bypass"] == "off"


def test_rls_migration_keeps_memberships_and_access_policy_free():
    migration = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/20260922_0359_c1057cb46015_architecture_base_schema.py"
    )
    sql = migration.read_text(encoding="utf-8")

    assert "ALTER TABLE patients ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY patients_scope ON patients" in sql
    assert "ALTER TABLE patient_memberships ENABLE ROW LEVEL SECURITY" not in sql
    assert "ALTER TABLE patient_access ENABLE ROW LEVEL SECURITY" not in sql
