from __future__ import annotations

from enum import StrEnum

from app.domain.types import PatientState


class Feature(StrEnum):
    CRITICAL_ALERT = "critical_alert"
    SOS = "sos"
    LIVE_STATUS = "live_status"
    ACTIVITY = "activity"
    TREND = "trend"
    HISTORY = "history"
    AI_SUMMARY = "ai_summary"
    PDF_REPORT = "pdf_report"


NEVER_PAYWALLED: frozenset[Feature] = frozenset(
    {
        Feature.CRITICAL_ALERT,
        Feature.SOS,
    }
)

SUBSCRIPTION_FEATURES: frozenset[Feature] = frozenset(
    {
        Feature.LIVE_STATUS,
        Feature.ACTIVITY,
        Feature.TREND,
        Feature.HISTORY,
        Feature.AI_SUMMARY,
        Feature.PDF_REPORT,
    }
)


def clinical_pipeline_enabled(state: PatientState) -> bool:
    """D2/C4: existing clinical monitoring follows the care owner, not family paywall."""
    return state.care_owner is not None


def family_features(state: PatientState) -> frozenset[Feature]:
    """E1/D4: safety features are always available; premium visibility needs subscription."""
    if state.subscription_active:
        return NEVER_PAYWALLED | SUBSCRIPTION_FEATURES
    return NEVER_PAYWALLED
