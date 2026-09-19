from __future__ import annotations

import uuid
from contextvars import ContextVar

# Thread-local / async task-local context variable storing the active tenant_id
current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)


def set_tenant_context(tenant_id: uuid.UUID | None) -> None:
    current_tenant_id.set(tenant_id)


def get_tenant_context() -> uuid.UUID | None:
    return current_tenant_id.get()
