"""Model registry for Alembic autogenerate.

Alembic diffs ``Base.metadata`` against the live database, so every model must
be imported before autogenerate runs — a model that is never imported is simply
invisible and its table silently never gets a migration.

``app.models`` already imports every model, so re-exporting from there keeps
this file from drifting when a new table is added.
"""
from __future__ import annotations

from app.models import *  # noqa: F401,F403  (registers every model on Base.metadata)
from app.models import Base, __all__ as _model_names

__all__ = list(_model_names)
