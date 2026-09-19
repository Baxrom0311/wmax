from __future__ import annotations

import logging
import re
from typing import Any

from app.core.exceptions import AIProviderException
from app.schemas.problem import NurseHandoverSBAR, PrognosisInfo

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+override",
    r"disregard\s+(all\s+)?(rules|guidelines)",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|jailbroken)",
    r"(reveal|print|show|output)\s+(your\s+)?(system\s+prompt|instructions)",
    r"forget\s+everything\s+you\s+were\s+told",
    r"new\s+rule\s*:\s*you\s+must",
    r"barcha\s+oldingi\s+ko'rsatmalarni\s+bekor\s+qil",
    r"tizim\s+ko'rsatmalarini\s+ko'rsat",
]


class InputGuardrailError(AIProviderException):
    """Raised when user input violates safety or prompt injection boundaries."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Xavfsizlik qoidasi buzildi: {message}")


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """Inspects text for prompt injection, jailbreak attempts, or rule bypasses."""
    normalized = text.lower().strip()
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            logger.warning("Prompt injection pattern detected: %s", match.group(0))
            return True, f"Taqiqlangan so'rov namunasi: {match.group(0)}"
    return False, None


def sanitize_clinical_input(text: str, max_length: int = 2000) -> str:
    """Sanitizes and bounds clinical input text before feeding to prompt templates."""
    if not text:
        return ""
    # Strip potential delimiter hijack attempts
    sanitized = text.replace("<system>", "").replace("</system>", "")
    sanitized = sanitized.replace("<patient_context>", "").replace("</patient_context>", "")
    sanitized = sanitized.replace("<clinical_rules>", "").replace("</clinical_rules>", "")
    # Bound max length
    return sanitized[:max_length].strip()


def validate_prognosis_factuality(
    prognosis: PrognosisInfo,
    level: str,
    recent_vitals: dict[str, Any],
) -> PrognosisInfo:
    """Guards against catastrophic clinical hallucinations and extreme level-risk divergence.

    Rules:
    1. If patient is 'red' with SpO2 < 88% or HR > 130, risk level CANNOT be 'low'.
    2. If patient is 'green' with all normal parameters, risk level CANNOT be 'high' without evidence.
    3. Guarantees evidence citations are extracted from physiological telemetry.
    """
    vitals_citations: list[str] = []

    hr = recent_vitals.get("hr") or recent_vitals.get("hr_mean")
    spo2 = recent_vitals.get("spo2")
    skin_temp = recent_vitals.get("skin_temp")

    if hr is not None:
        vitals_citations.append(f"HR: {hr} bpm")
    if spo2 is not None:
        vitals_citations.append(f"SpO2: {spo2}%")
    if skin_temp is not None:
        vitals_citations.append(f"Harorat: {skin_temp}°C")

    # Guard 1: Red level must not be evaluated as low risk
    if level == "red" and prognosis.risk_level == "low":
        logger.warning(
            "Guardrail tripped: LLM returned risk_level='low' for patient in 'red' alert state. Overriding to 'high'."
        )
        prognosis.risk_level = "high"
        prognosis.risk_probability_pct = max(75, prognosis.risk_probability_pct)
        prognosis.uncertainty_note = "Klinik ogohlantirish (Red) sababli xavf darajasi 'high' qilib to'g'rilandi."

    # Guard 2: Green level must not be evaluated as high risk
    if level == "green" and prognosis.risk_level == "high":
        logger.warning(
            "Guardrail tripped: LLM returned risk_level='high' for stable 'green' patient without trigger. Overriding to 'moderate'."
        )
        prognosis.risk_level = "moderate"
        prognosis.risk_probability_pct = min(40, prognosis.risk_probability_pct)
        prognosis.uncertainty_note = "Barqaror telemetriya fonida xavf darajasi ehtiyotkorlik bilan 'moderate' ga moslashtirildi."

    # Guard 3: Ensure citations are present
    if not prognosis.evidence_citations:
        prognosis.evidence_citations = vitals_citations

    # Guard 4: Bound confidence score
    if not (0.0 <= prognosis.confidence_score <= 1.0):
        prognosis.confidence_score = 0.90

    return prognosis


def validate_nurse_handover(
    handover: NurseHandoverSBAR,
    level: str,
) -> NurseHandoverSBAR:
    """Ensures SBAR nurse handover adheres to urgency constraints and clinical completeness."""
    if level == "red" and handover.clinical_urgency != "critical":
        handover.clinical_urgency = "critical"
    elif level == "amber" and handover.clinical_urgency == "routine":
        handover.clinical_urgency = "urgent"

    if not handover.shift_checklist:
        # Guarantee minimum safety checklist
        from app.schemas.problem import NurseChecklistItem

        handover.shift_checklist = [
            NurseChecklistItem(
                id="task-vitals-1",
                task="Arterial qon bosimi va pulsni qo'lda tekshirish",
                priority="high" if level in ("red", "amber") else "medium",
                category="vitals",
            ),
            NurseChecklistItem(
                id="task-device-2",
                task="Aqlli soat elektrodlari teriga tegib turganini va quvvatini tekshirish",
                priority="medium",
                category="device",
            ),
            NurseChecklistItem(
                id="task-med-3",
                task="Tayinlangan dorilar qabul qilinganligini bemor bilan tekshirish",
                priority="high",
                category="medication",
            ),
        ]

    return handover
