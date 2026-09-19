from __future__ import annotations

from typing import Any

from app.core.exceptions import ForbiddenException
from app.schemas.auth import CurrentUser

# Roles that may write any field on any table.
FULL_ACCESS_ROLES = frozenset({"doctor", "admin"})

# Sentinel meaning "every field on this table".
ALL_FIELDS = frozenset({"*"})

# Single source of truth for write authorization (docs/WMAX.md §6.2):
# table -> role -> writable fields.
#
# A role absent from a table's map cannot write that table at all. This is
# deliberately deny-by-omission: forgetting to list a role denies access rather
# than granting it, which is the failure direction a clinical system should have.
#
# Clinical truth — coded diagnoses, prescriptions, hospital records, care phase —
# belongs to clinicians. What the people at the bedside know better than the
# clinic (where the patient actually lives, today's weight) is writable by them,
# because stale data there is the failure mode that matters during an emergency.
FIELD_POLICY: dict[str, dict[str, frozenset[str]]] = {
    "patients": {
        # Contact details only — never diagnosis, phase or staff assignment.
        "nurse": frozenset({"phone", "telegram_chat_id", "preferred_lang"}),
        "relative": frozenset({"phone", "telegram_chat_id", "preferred_lang"}),
        "patient": frozenset({"phone", "telegram_chat_id", "preferred_lang"}),
    },
    # Coded diagnoses: doctors and admins only (empty map = nobody else).
    "patient_conditions": {},
    "patient_medications": {
        # Prescriptions are a clinical record. A caregiver who notices a
        # mismatch reports it; they do not silently rewrite the dose, because
        # the signal engine damps z-scores based on this table.
        "nurse": ALL_FIELDS,
    },
    "patient_allergies": {
        "nurse": ALL_FIELDS,
        "relative": ALL_FIELDS,
        "patient": ALL_FIELDS,
    },
    "patient_measurements": {
        "nurse": ALL_FIELDS,
        "relative": ALL_FIELDS,
        "patient": ALL_FIELDS,
    },
    "patient_addresses": {
        "nurse": ALL_FIELDS,
        "relative": ALL_FIELDS,
        # The patient may refine how to be found, but not relocate the record.
        "patient": frozenset({"landmark", "entrance_note", "lat", "lon"}),
    },
    "patient_risk_factors": {
        "relative": ALL_FIELDS,
        "patient": ALL_FIELDS,
    },
    "patient_admissions": {
        "nurse": ALL_FIELDS,
    },
    "relatives": {
        "relative": ALL_FIELDS,
        "patient": frozenset({"phone"}),
    },
}

# Shorthand used by route handlers, mapping a domain noun to its table.
ENTITY_TABLES: dict[str, str] = {
    "contact": "patients",
    "address": "patient_addresses",
    "condition": "patient_conditions",
    "medication": "patient_medications",
    "allergy": "patient_allergies",
    "measurement": "patient_measurements",
    "risk_factors": "patient_risk_factors",
    "admission": "patient_admissions",
    "relative": "relatives",
    "clinical_phase": "patients",
    "assignment": "patients",
}

# Entities only a doctor or admin may touch regardless of the field map, because
# their table is shared with fields others are allowed to write.
CLINICIAN_ONLY_ENTITIES = frozenset({"clinical_phase", "assignment"})


def can_edit_field(principal: CurrentUser, table: str, field: str) -> bool:
    """True when `principal` may write `field` on `table`."""
    if principal.role in FULL_ACCESS_ROLES:
        return True

    allowed = FIELD_POLICY.get(table, {}).get(principal.role)
    if allowed is None:
        return False
    return ALL_FIELDS.issubset(allowed) or field in allowed


def assert_can_edit(
    principal: CurrentUser, table: str, changes: dict[str, Any]
) -> None:
    """Raises 403 naming the first field the principal may not write.

    Naming the field matters: a blanket "forbidden" on a form with a dozen
    inputs tells the user nothing about which one to drop.
    """
    for field in changes:
        if not can_edit_field(principal, table, field):
            raise ForbiddenException(
                f"'{field}' maydonini o'zgartirish huquqingiz yo'q"
            )


def assert_can_edit_entity(entity: str, principal: CurrentUser) -> None:
    """Entity-level shorthand: may this role write anything on this entity?

    Route handlers call this to reject early, before parsing a request body.
    Per-field checks still run afterwards via `assert_can_edit`.
    """
    if principal.role in FULL_ACCESS_ROLES:
        return

    if entity in CLINICIAN_ONLY_ENTITIES:
        raise ForbiddenException(
            f"'{entity}' ma'lumotini o'zgartirish huquqingiz yo'q"
        )

    table = ENTITY_TABLES.get(entity)
    if table is None or not FIELD_POLICY.get(table, {}).get(principal.role):
        raise ForbiddenException(
            f"'{entity}' ma'lumotini o'zgartirish huquqingiz yo'q"
        )
