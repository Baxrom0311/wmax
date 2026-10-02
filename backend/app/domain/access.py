from __future__ import annotations

from uuid import UUID

from app.domain.types import AccessScope, PlatformRole, TenantRole, ViewerContext


def visible_patients(viewer: ViewerContext) -> AccessScope:
    """B3/B6/H1/H2: compute patient visibility without touching DB."""
    if viewer.platform_role == PlatformRole.RESEARCH:
        return AccessScope(all_patients=True, anonymized=True)
    if viewer.platform_role == PlatformRole.SUPPORT:
        if not viewer.support_reason or not viewer.support_reason.strip():
            raise ValueError("platform_support requires a reason")
        return AccessScope(all_patients=True, support_reason=viewer.support_reason.strip())

    tenant_ids: set[UUID] = set()
    mahallas: set[str] = set()
    for membership in viewer.tenant_memberships:
        if membership.role in {TenantRole.HEAD_DOCTOR, TenantRole.ADMIN, TenantRole.DISPATCHER}:
            tenant_ids.add(membership.tenant_id)
        else:
            mahallas.update(membership.mahallas)

    return AccessScope(
        tenant_ids=frozenset(tenant_ids),
        mahallas=frozenset(mahallas),
        patient_ids=viewer.patient_access_ids,
    )


def requires_audit_log(viewer: ViewerContext, patient_id: UUID) -> bool:
    """H2: platform reads and cross-scope patient reads are audited."""
    if viewer.platform_role is not None:
        return True
    return patient_id not in viewer.patient_access_ids
