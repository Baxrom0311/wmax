from __future__ import annotations

from datetime import date, datetime, time, timezone

from app.domain.types import AssignmentWindow, DateRange, InvoiceLines, Licence, Membership, PatientDayReport


def patient_days(
    memberships: tuple[Membership, ...],
    assignments: tuple[AssignmentWindow, ...],
    period: DateRange,
) -> PatientDayReport:
    """E5/E3: count days where membership and assignment overlap at least once."""
    counted: set[tuple[object, date]] = set()
    for day in _days(period):
        day_start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(day, time.max, tzinfo=timezone.utc)
        for membership in memberships:
            if not _window_overlaps(membership.granted_at, membership.revoked_at, day_start, day_end):
                continue
            if any(
                assignment.patient_id == membership.patient_id
                and _window_overlaps(assignment.assigned_at, assignment.released_at, day_start, day_end)
                for assignment in assignments
            ):
                counted.add((membership.patient_id, day))

    patient_day_set = frozenset(counted)
    return PatientDayReport(
        period=period,
        patient_days_total=len(patient_day_set),
        patient_days_with_data=0,
        patient_days=patient_day_set,
    )


def invoice_total(report: PatientDayReport, licence: Licence) -> InvoiceLines:
    """E2: minimum commitment is tied to device count."""
    min_commitment = licence.device_count * licence.min_days_per_device
    billed_days = max(report.patient_days_total, min_commitment)
    return InvoiceLines(
        patient_days_total=report.patient_days_total,
        patient_days_with_data=report.patient_days_with_data,
        min_commitment=min_commitment,
        billed_days=billed_days,
        amount_uzs=billed_days * licence.price_per_patient_day_uzs,
    )


def _days(period: DateRange) -> tuple[date, ...]:
    if period.end < period.start:
        raise ValueError("period end must be on or after start")
    return tuple(date.fromordinal(day) for day in range(period.start.toordinal(), period.end.toordinal() + 1))


def _window_overlaps(
    start: datetime,
    end: datetime | None,
    range_start: datetime,
    range_end: datetime,
) -> bool:
    effective_end = end or range_end
    return start <= range_end and effective_end >= range_start
