from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.cache import ai_cache
from app.ai.factory import build_ai_provider
from app.ai.provider import AIProvider
from app.schemas.problem import (
    NurseChecklistItem,
    NurseHandoverSBAR,
    PrognosisInfo,
    TwinPrognosisInfo,
)

if TYPE_CHECKING:
    from app.services.patient_context import PatientContext

logger = logging.getLogger(__name__)


def _observed_summary(level: str, vitals: dict[str, Any]) -> PrognosisInfo:
    """Describe the current signal without predicting an outcome or probability."""
    level_map = {"green": "low", "amber": "moderate", "red": "high", "no_data": "moderate"}
    if level == "no_data":
        summary = "Ma'lumot kelmayapti; bemorning holatini hozirgi telemetry bilan baholab bo'lmaydi."
        recommendation = "Bemor holatini boshqa usul bilan tekshiring va qurilma ulanishini ko'rib chiqing."
        uncertainty = "Ma'lumot yo'qligi sog'lom holatni anglatmaydi."
    elif level == "red":
        summary = "Kuzatilgan ko'rsatkichlarda yuqori darajadagi og'ish qayd etildi."
        recommendation = "O'lchovni tekshiring va klinik protokoldagi mas'ul xodimga murojaat qiling."
        uncertainty = "Bu tashxis yoki kasallik ehtimoli emas."
    elif level == "amber":
        summary = "Kuzatilgan ko'rsatkichlarda e'tibor talab qiluvchi og'ish qayd etildi."
        recommendation = "O'lchovlar va bemor holatini klinik mas'ul bilan ko'rib chiqing."
        uncertainty = "Bu tashxis yoki kelajakdagi holat prognozi emas."
    else:
        summary = "Mavjud ko'rsatkichlar tanlangan bazaviy diapazonga yaqin."
        recommendation = "Muntazam monitoringni davom ettiring; bu natija tashxis bermaydi."
        uncertainty = "Baholash faqat kelgan va ishonchli o'lchovlarga taalluqli."
    evidence = [f"{key}: {value}" for key, value in vitals.items() if value is not None]
    return PrognosisInfo(
        risk_level=level_map.get(level, "moderate"),
        summary=summary,
        recommendation=recommendation,
        evidence_citations=evidence,
        uncertainty_note=uncertainty,
    )


class ClinicalAIService:
    """High-level AI service providing AI-enhanced early warnings and natural language summaries.

    Features:
    - LRU TTL Caching (avoids duplicate LLM invocations on dashboard refreshes).
    - Clinical Input & Output Guardrails (factuality enforcement and hallucination clamping).
    - Multi-provider hot-swapping (Gemini, DeepSeek).
    - Nurse SBAR Handover generation & Shift patrol checklist.
    - Deterministic, statistically calibrated fallback heuristics.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider or build_ai_provider()

    async def generate_patient_prognosis(
        self,
        patient_name: str,
        age: int,
        diagnosis: str,
        level: str,
        recent_vitals: dict[str, Any],
        deviated_params: dict[str, Any],
        slope: float,
        patient_id: str | None = None,
    ) -> PrognosisInfo:
        """Return a current-signal summary; outcome prediction is not clinically validated."""
        # 1. Check LRU TTL Cache
        cache_id = patient_id or patient_name
        cache_key = ai_cache.generate_key(
            "prognosis",
            cache_id,
            {
                "level": level,
                "vitals": recent_vitals,
                "deviated": list(deviated_params.keys()),
                "slope": round(slope, 2),
            },
        )
        cached: PrognosisInfo | None = ai_cache.get(cache_key)
        if cached is not None:
            logger.debug("Prognosis cache hit for %s", cache_id)
            return cached
        result = _observed_summary(level, recent_vitals)
        if deviated_params:
            result.evidence_citations = [*result.evidence_citations, *[str(key) for key in deviated_params]]
        ai_cache.set(cache_key, result, ttl_seconds=120.0)
        return result

    async def generate_twin_prognosis(
        self,
        ctx: PatientContext,
        session: AsyncSession | None = None,
    ) -> TwinPrognosisInfo:
        """Return current observations, never unvalidated outcome predictions."""
        cache_key = ai_cache.generate_key(
            "twin_prognosis",
            str(ctx.patient_id),
            {
                "level": ctx.level,
                "composite": round(ctx.composite_score, 2),
                "vitals": ctx.recent_vitals,
                "open_alerts": len(ctx.open_alerts),
            },
        )
        cached: TwinPrognosisInfo | None = ai_cache.get(cache_key)
        if cached is not None:
            logger.debug("Twin prognosis cache hit for %s", ctx.patient_id)
            return cached

        base = _observed_summary(ctx.level, ctx.recent_vitals)
        res = TwinPrognosisInfo(
            **base.model_dump(),
            primary_concern=base.summary,
            contributing_factors=[str(key) for key in ctx.triggered_params],
        )
        ai_cache.set(cache_key, res)
        return res

    async def generate_nurse_handover(
        self,
        ctx: PatientContext,
        session: AsyncSession | None = None,
    ) -> NurseHandoverSBAR:
        """Build a structured handover from observed data without external inference."""
        cache_key = ai_cache.generate_key(
            "nurse_sbar",
            str(ctx.patient_id),
            {
                "level": ctx.level,
                "tasks": len(ctx.open_tasks),
                "vitals": ctx.recent_vitals,
            },
        )
        cached: NurseHandoverSBAR | None = ai_cache.get(cache_key)
        if cached is not None:
            logger.debug("Nurse SBAR cache hit for %s", ctx.patient_id)
            return cached

        level = ctx.level
        urgency = {"red": "critical", "amber": "urgent", "no_data": "urgent"}.get(level, "routine")
        vitals = ctx.recent_vitals
        observed = [
            f"{name}={vitals[key]} {unit}"
            for key, name, unit in (
                ("hr_mean", "Puls", "bpm"),
                ("spo2", "SpO₂", "%"),
                ("skin_temp", "Teri harorati", "°C"),
            )
            if vitals.get(key) is not None
        ]
        missing = level == "no_data"
        fallback = NurseHandoverSBAR(
            situation=f"Bemor {ctx.full_name} ({ctx.age} yosh). Kuzatilgan signal: {level.upper()}.",
            background=(
                ", ".join(condition.name_uz for condition in ctx.conditions)
                if ctx.conditions else "Qo'shimcha klinik ma'lumot kiritilmagan."
            ),
            assessment=(
                "Ma'lumot kelmayapti; hozirgi holatni telemetry bilan baholab bo'lmaydi."
                if missing else "Oxirgi mavjud o'lchovlar: " + (", ".join(observed) or "mavjud emas")
            ),
            recommendation="Bemorni klinik protokol bo'yicha baholang; bu xulosa tashxis yoki dori tavsiyasi emas.",
            shift_checklist=[
                NurseChecklistItem(
                    id="verify-observation",
                    task="Bemor holatini va mavjud o'lchovlarni klinik protokol bo'yicha tekshirish",
                    priority="critical" if level == "red" else "high" if level in {"amber", "no_data"} else "medium",
                    category="observation",
                ),
                NurseChecklistItem(
                    id="verify-device",
                    task="Qurilma ulanishi va ma'lumot kelish holatini tekshirish",
                    priority="high" if missing else "medium",
                    category="device",
                ),
            ],
            clinical_urgency=urgency,
            vital_flags=[*observed, *[str(key) for key in ctx.triggered_params]],
            evidence_citations=observed,
        )
        ai_cache.set(cache_key, fallback, ttl_seconds=180.0)
        return fallback
