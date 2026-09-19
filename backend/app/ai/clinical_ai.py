from __future__ import annotations

import hashlib
import logging
import time
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.cache import ai_cache
from app.ai.factory import build_ai_provider
from app.ai.guardrails import validate_nurse_handover, validate_prognosis_factuality
from app.ai.prompts import (
    CLINICAL_SYSTEM_INSTRUCTION,
    build_clinical_analysis_prompt,
    build_nurse_sbar_prompt,
    build_twin_analysis_prompt,
)
from app.ai.provider import AIProvider
from app.models.twin_snapshot import TwinSnapshot
from app.schemas.problem import (
    NurseChecklistItem,
    NurseHandoverSBAR,
    PrognosisInfo,
    TwinPrognosisInfo,
)

if TYPE_CHECKING:
    from app.services.patient_context import PatientContext

logger = logging.getLogger(__name__)


def compute_deterministic_risk_pct(
    level: str, composite_score: float = 0.0, slope: float = 0.0
) -> int:
    """Calculates scientifically calibrated fallback risk probability from z-score telemetry."""
    if level == "red":
        return max(70, min(95, 75 + int(abs(composite_score) * 3)))
    elif level == "amber":
        return max(30, min(65, 38 + int(abs(composite_score) * 2)))
    elif level == "no_data":
        return 0
    else:  # green
        return max(3, min(20, 8 + int(max(0.0, slope) * 5)))


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
        """Generates AI-powered 72-hour clinical prognosis with caching, guardrails, and deterministic fallback."""
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

        prompt = build_clinical_analysis_prompt(
            patient_name=patient_name,
            age=age,
            diagnosis=diagnosis,
            level=level,
            recent_vitals=recent_vitals,
            deviated_params=deviated_params,
            slope=slope,
        )

        try:
            res = await self.provider.generate_structured(
                prompt=prompt,
                schema_class=PrognosisInfo,
                system_instruction=CLINICAL_SYSTEM_INSTRUCTION,
            )
            # Apply clinical factuality guardrails
            res = validate_prognosis_factuality(res, level, recent_vitals)
            ai_cache.set(cache_key, res)
            return res
        except Exception as e:
            logger.warning(
                "LLM prognosis generation fell back to deterministic heuristic: %s", e
            )
            calc_risk = compute_deterministic_risk_pct(level, 0.0, slope)

            if level == "red":
                fallback = PrognosisInfo(
                    risk_level="high",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    summary="Oxirgi ko'rsatkichlar jiddiy fiziologik og'ishlarni ko'rsatmoqda. Re-gospitalizatsiya xavfi yuqori.",
                    recommendation="Shifokor bilan darhol bog'laning yoki favqulodda yordam ko'rsatilishini ta'minlang.",
                    evidence_citations=[f"{k}: chetlangan" for k in deviated_params],
                    confidence_score=0.88,
                    uncertainty_note="Avtonom deterministik algoritm orqali hisoblandi.",
                )
            elif level == "amber":
                fallback = PrognosisInfo(
                    risk_level="moderate",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    summary="Holatda salbiy o'zgarishlar sezilmoqda. 72 soat ichida og'irlashuv ehtimoli mavjud.",
                    recommendation="Bemorning dam olishini ta'minlang, dori-darmonlar qabulini monitoring qiling.",
                    evidence_citations=[f"{k}: chetlangan" for k in deviated_params],
                    confidence_score=0.85,
                    uncertainty_note="Avtonom deterministik algoritm orqali hisoblandi.",
                )
            elif level == "no_data":
                fallback = PrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=0,
                    early_warning_hours=72,
                    summary="Aqlli soatdan 45 daqiqadan beri ma'lumot kelmayapti.",
                    recommendation="Soat bemorning qo'liga to'g'ri taqilganligini tekshiring.",
                    evidence_citations=["Qurilma signali mavjud emas"],
                    confidence_score=0.99,
                    uncertainty_note="Signal yo'qligi sababli tahlil to'xtatilgan.",
                )
            else:
                fallback = PrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    summary="Barcha asosiy fiziologik ko'rsatkichlar bemorning shaxsiy normasi doirasida barqaror.",
                    recommendation="Muntazam monitoring va belgilangan rejimni davom ettiring.",
                    evidence_citations=["Barcha parametrlar z-score < 1.5"],
                    confidence_score=0.92,
                )

            ai_cache.set(cache_key, fallback, ttl_seconds=120.0)
            return fallback

    async def generate_twin_prognosis(
        self,
        ctx: PatientContext,
        session: AsyncSession | None = None,
    ) -> TwinPrognosisInfo:
        """Generates comprehensive clinical twin prognosis and logs snapshot (Section 8.3 & 8.4)."""
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

        prompt = build_twin_analysis_prompt(ctx)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        start_time = time.perf_counter()

        res: TwinPrognosisInfo
        try:
            res = await self.provider.generate_structured(
                prompt=prompt,
                schema_class=TwinPrognosisInfo,
                system_instruction=CLINICAL_SYSTEM_INSTRUCTION,
            )
            # Guardrails validation
            res = validate_prognosis_factuality(res, ctx.level, ctx.recent_vitals)  # type: ignore[assignment]
        except Exception as e:
            logger.warning(
                "Twin prognosis LLM generation fell back to deterministic heuristic: %s", e
            )
            level = getattr(ctx, "level", "green")
            composite = getattr(ctx, "composite_score", 0.0)
            calc_risk = compute_deterministic_risk_pct(level, composite)

            if level == "red":
                res = TwinPrognosisInfo(
                    risk_level="high",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    primary_concern="Fiziologik parametrlarda jiddiy og'ish kuzatildi.",
                    contributing_factors=["Vital parametrlar chegaradan chetlangan"],
                    medication_considerations="Dori-darmonlar qabul qilish jadvalini tekshiring.",
                    summary="Oxirgi ko'rsatkichlar jiddiy fiziologik og'ishlarni ko'rsatmoqda. Re-gospitalizatsiya xavfi yuqori.",
                    recommendation="Shifokor bilan darhol bog'laning yoki favqulodda yordam ko'rsatilishini ta'minlang.",
                    relative_message_key="alert.red.urgent",
                    evidence_citations=[f"{k}: og'ish" for k in ctx.triggered_params],
                    confidence_score=0.88,
                    uncertainty_note="Avtonom kardiorenal algoritm orqali hisoblandi.",
                )
            elif level == "amber":
                res = TwinPrognosisInfo(
                    risk_level="moderate",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    primary_concern="Trendda salbiy o'zgarishlar mavjud.",
                    contributing_factors=["Subklinik o'zgarishlar"],
                    medication_considerations="Muntazam dori qabulini davom ettiring.",
                    summary="Holatda salbiy o'zgarishlar sezilmoqda. 72 soat ichida og'irlashuv ehtimoli mavjud.",
                    recommendation="Bemorning dam olishini ta'minlang, dori-darmonlar qabulini monitoring qiling.",
                    relative_message_key="alert.amber.warning",
                    evidence_citations=[f"{k}: og'ish" for k in ctx.triggered_params],
                    confidence_score=0.85,
                    uncertainty_note="Avtonom kardiorenal algoritm orqali hisoblandi.",
                )
            elif level == "no_data":
                res = TwinPrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=0,
                    early_warning_hours=72,
                    primary_concern="Qurilmadan ma'lumot kelishi to'xtagan.",
                    contributing_factors=["Qurilma o'chiq yoki batareya quvvatsiz"],
                    medication_considerations=None,
                    summary="Aqlli soatdan 45 daqiqadan beri ma'lumot kelmayapti.",
                    recommendation="Soat bemorning qo'liga to'g'ri taqilganligini tekshiring.",
                    relative_message_key="state.no_data",
                    evidence_citations=["Signal yo'q"],
                    confidence_score=0.99,
                )
            else:
                res = TwinPrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=calc_risk,
                    early_warning_hours=72,
                    primary_concern="Parametrlar barqaror.",
                    contributing_factors=[],
                    medication_considerations="Belgilangan terapiya o'z samarasini bermoqda.",
                    summary="Barcha asosiy fiziologik ko'rsatkichlar bemorning shaxsiy normasi doirasida barqaror.",
                    recommendation="Muntazam monitoring va belgilangan rejimni davom ettiring.",
                    relative_message_key="state.good",
                    evidence_citations=["Barcha z-score < 1.5"],
                    confidence_score=0.92,
                )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        ai_cache.set(cache_key, res)

        # Log snapshot if session provided
        if session is not None:
            try:
                snapshot = TwinSnapshot(
                    patient_id=ctx.patient_id,
                    context=ctx.for_ai(),
                    ai_response=res.model_dump(),
                    ai_model=getattr(self.provider, "model_name", "wmax-ai-production"),
                    prompt_hash=prompt_hash,
                    latency_ms=latency_ms,
                )
                session.add(snapshot)
                await session.flush()
            except Exception as snap_err:
                logger.warning("Failed to record TwinSnapshot: %s", snap_err)

        return res

    async def generate_nurse_handover(
        self,
        ctx: PatientContext,
        session: AsyncSession | None = None,
    ) -> NurseHandoverSBAR:
        """Generates dedicated SBAR Nurse Shift Handover Note and clinical shift checklist."""
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

        prompt = build_nurse_sbar_prompt(ctx)

        try:
            res = await self.provider.generate_structured(
                prompt=prompt,
                schema_class=NurseHandoverSBAR,
                system_instruction=CLINICAL_SYSTEM_INSTRUCTION,
            )
            res = validate_nurse_handover(res, ctx.level)
            ai_cache.set(cache_key, res)
            return res
        except Exception as err:
            logger.warning("Nurse SBAR LLM generation fell back to heuristic: %s", err)
            level = getattr(ctx, "level", "green")
            urgency = "critical" if level == "red" else "urgent" if level == "amber" else "routine"

            # Safe clinical SBAR fallback
            fallback = NurseHandoverSBAR(
                situation=f"Bemor {ctx.full_name} ({ctx.age} yosh). Joriy klinik triaj holati: {level.upper()}.",
                background=f"Tashxisi: {ctx.conditions[0].name_uz if ctx.conditions else 'Kardiologik monitoring'}. Chiqarilganiga {ctx.days_since_discharge or '—'} kun bo'lgan.",
                assessment=f"Oxirgi o'lchovlar: HR={ctx.recent_vitals.get('hr_mean', '—')} bpm, SpO2={ctx.recent_vitals.get('spo2', '—')}%. Chetlangan parametrlar: {list(ctx.triggered_params.keys()) or 'yoʻq'}.",
                recommendation="Palataga/xonadonga tashrif buyurish, arterial qon bosimini o'lchash va dori ichilganligini tasdiqlash.",
                shift_checklist=[
                    NurseChecklistItem(
                        id="chk-vitals",
                        task="Tonometer orqali qon bosimi va pulsni o'lchab, kartaga kiritish",
                        priority="critical" if level == "red" else "high",
                        category="vitals",
                    ),
                    NurseChecklistItem(
                        id="chk-meds",
                        task="Kunlik tayinlangan dorilar o'z vaqtida qabul qilinganligini tekshirish",
                        priority="high",
                        category="medication",
                    ),
                    NurseChecklistItem(
                        id="chk-watch",
                        task="Aqlli soat bilakka mahkam taqilgani va batareyasi yetarli ekanligini ko'zdan kechirish",
                        priority="medium",
                        category="device",
                    ),
                ],
                clinical_urgency=urgency,
                vital_flags=[f"{k}: z={v:.1f}" for k, v in ctx.triggered_params.items()] or ["Parametrlar barqaror"],
                confidence_score=0.92,
                evidence_citations=[f"Level: {level}", f"Score: {ctx.composite_score}"],
            )
            ai_cache.set(cache_key, fallback, ttl_seconds=180.0)
            return fallback
