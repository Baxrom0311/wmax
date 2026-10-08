from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.core.rls import set_rls_context


@pytest.mark.asyncio
async def test_set_rls_context_uses_set_local_only():
    calls: list[tuple[str, dict[str, str]]] = []

    class Session:
        async def execute(self, stmt, params=None):
            calls.append(stmt)

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

    sql_calls = [str(stmt) for stmt in calls]
    assert len(sql_calls) == 5
    assert all("set_config" in sql for sql in sql_calls)


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
