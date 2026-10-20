"""Current clinical relationships, shared by HTTP, realtime and delivery.

IDEOLOGY B6: tenant isolation is not enough. Head doctors, clinic admins and
dispatchers see the whole clinic; doctors and nurses see patients whose primary
address lies in one of their assigned mahallas. The same rule decides who may
be given a task and who receives clinical notifications.

ORM criteria are installed on a request's session, including on repositories
which only receive that session. Core table aliases in the scope subquery avoid
recursive loader criteria. Workers deliberately have no request scope.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import and_, event, exists, or_, select
from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy.sql.elements import ColumnElement

from app.models.schema import Base, MemberTerritory, PatientAddress, PatientMembership, TenantMember

CLINIC_WIDE_ROLES = ("admin", "head_doctor", "dispatcher")
TERRITORY_ROLES = ("doctor", "nurse")

# Highest-privilege membership wins for the token's display role; head doctors
# carry doctor permissions. Authorization uses the per-tenant role instead.
_TENANT_ROLE_PRIORITY = ("admin", "head_doctor", "doctor", "dispatcher", "nurse")
_TENANT_ROLE_TO_TOKEN_ROLE = {"head_doctor": "doctor"}


def token_role(tenant_role: str) -> str:
    return _TENANT_ROLE_TO_TOKEN_ROLE.get(tenant_role, tenant_role)


def primary_clinician_role(tenant_roles: Iterable[Any]) -> str | None:
    roles = {member.role for member in tenant_roles}
    for candidate in _TENANT_ROLE_PRIORITY:
        if candidate in roles:
            return token_role(candidate)
    return None


def clinician_patient_ids(account_id: Any, tenant_ids: Any):
    """SELECT of patient ids the account may currently see in these tenants.

    `account_id` and `tenant_ids` may be values or correlated SQL columns (a
    single column for `tenant_ids`), so callers can ask "who may see this
    patient" with exactly the rule used for "what may this person see".
    """
    membership = PatientMembership.__table__.alias("scope_membership")
    member = TenantMember.__table__.alias("scope_member")
    address = PatientAddress.__table__.alias("scope_address")
    territory = MemberTerritory.__table__.alias("scope_territory")
    territory_match = exists(select(1).select_from(address.join(
        territory, territory.c.mahalla == address.c.mahalla,
    )).where(
        address.c.patient_id == membership.c.patient_id,
        address.c.is_primary.is_(True),
        territory.c.tenant_member_id == member.c.id,
    ))
    return select(membership.c.patient_id).select_from(membership.join(
        member, member.c.tenant_id == membership.c.tenant_id,
    )).where(
        membership.c.revoked_at.is_(None), member.c.left_at.is_(None),
        member.c.account_id == account_id, _tenant_filter(member.c.tenant_id, tenant_ids),
        or_(member.c.role.in_(CLINIC_WIDE_ROLES), territory_match),
    )


def _tenant_filter(column, tenant_ids):
    if hasattr(tenant_ids, "__clause_element__") or isinstance(tenant_ids, ColumnElement):
        return column == tenant_ids
    return column.in_(list(tenant_ids))


def install_clinical_scope(session: Any, account_id: uuid.UUID, tenant_ids: Iterable[uuid.UUID]) -> None:
    info = getattr(session, "info", None)
    if info is not None:
        info["clinical_scope"] = (account_id, tuple(tenant_ids))


def _patient_scoped_entities() -> list[tuple[type, str]]:
    entities = []
    for mapper in Base.registry.mappers:
        if mapper.local_table.name == "patients":
            entities.append((mapper.class_, "id"))
        elif "patient_id" in mapper.columns:
            entities.append((mapper.class_, "patient_id"))
    return entities


@event.listens_for(Session, "do_orm_execute")
def _scope_patient_queries(state) -> None:
    scope = state.session.info.get("clinical_scope")
    if scope is None or not (state.is_select or state.is_update or state.is_delete):
        return
    account_id, tenant_ids = scope
    ids = clinician_patient_ids(account_id, tenant_ids)
    # All patient-owned ORM entities share the same boundary. Relationship
    # tables used inside ids are Core aliases, so cannot recursively scope.
    for cls, column_name in _patient_scoped_entities():
        predicate = getattr(cls, column_name).in_(ids)
        if cls.__tablename__ == "tasks":
            predicate = and_(predicate, cls.tenant_id.in_(tenant_ids))
        state.statement = state.statement.options(with_loader_criteria(
            cls, predicate, include_aliases=True,
        ))
