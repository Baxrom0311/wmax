from __future__ import annotations

from app.domain.types import AlertLevel, PatientState, PromiseLevel, Target, TargetKind


def promise_level(state: PatientState) -> PromiseLevel:
    """C2: care owner raises the promise from awareness to accountability."""
    return "accountable" if state.care_owner is not None else "awareness"


def should_create_task(state: PatientState, level: AlertLevel) -> bool:
    """D5: no assignee means no task."""
    return state.care_owner is not None and level in {"amber", "red", "no_data"}


def notification_targets(state: PatientState, level: AlertLevel) -> tuple[Target, ...]:
    """D3: red alerts always have at least one notification target."""
    targets: list[Target] = []
    if state.care_owner is not None:
        targets.append(
            Target(
                kind=TargetKind.CLINICIAN,
                account_id=state.care_owner.account_id,
                tenant_id=state.care_owner.tenant_id,
                patient_id=state.patient_id,
            )
        )
        if state.subscription_active:
            targets.extend(_caregiver_targets(state))
    else:
        targets.extend(_caregiver_targets(state))

    if level == "red" and not targets:
        targets.append(Target(kind=TargetKind.EMERGENCY_QUEUE, patient_id=state.patient_id))
    return tuple(targets)


def _caregiver_targets(state: PatientState) -> list[Target]:
    return [
        Target(
            kind=TargetKind.CAREGIVER,
            account_id=caregiver.account_id,
            patient_id=state.patient_id,
        )
        for caregiver in state.caregivers
    ]
