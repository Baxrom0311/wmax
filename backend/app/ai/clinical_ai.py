from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini_provider import GeminiProvider
from app.ai.prompts import CLINICAL_SYSTEM_INSTRUCTION, build_clinical_analysis_prompt
from app.schemas.problem import PrognosisInfo

logger = logging.getLogger(__name__)


class ClinicalAIService:
    """High-level AI service providing AI-enhanced early warnings and natural language summaries."""

    def __init__(self, provider: GeminiProvider | None = None) -> None:
        self.provider = provider or GeminiProvider()

    async def generate_patient_prognosis(
        self,
        patient_name: str,
        age: int,
        diagnosis: str,
        level: str,
        recent_vitals: dict[str, Any],
        deviated_params: dict[str, Any],
        slope: float,
    ) -> PrognosisInfo:
        """Generates AI-powered 72-hour clinical prognosis via Gemini with local heuristic fallback."""
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
            return await self.provider.generate_structured(
                prompt=prompt,
                schema_class=PrognosisInfo,
                system_instruction=CLINICAL_SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            logger.warning(
                f"Gemini prognosis generation fell back to deterministic heuristic: {e}"
            )
            # Safe, deterministic clinical heuristic fallback
            if level == "red":
                return PrognosisInfo(
                    risk_level="high",
                    risk_probability_pct=78,
                    early_warning_hours=72,
                    summary="Oxirgi ko'rsatkichlar jiddiy fiziologik og'ishlarni ko'rsatmoqda. Re-gospitalizatsiya xavfi yuqori.",
                    recommendation="Shifokor bilan darhol bog'laning yoki favqulodda yordam ko'rsatilishini ta'minlang.",
                )
            elif level == "amber":
                return PrognosisInfo(
                    risk_level="moderate",
                    risk_probability_pct=42,
                    early_warning_hours=72,
                    summary="Holatda salbiy o'zgarishlar sezilmoqda. 72 soat ichida og'irlashuv ehtimoli mavjud.",
                    recommendation="Bemorning dam olishini ta'minlang, dori-darmonlar qabulini nazorat qiling.",
                )
            elif level == "no_data":
                return PrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=0,
                    early_warning_hours=72,
                    summary="Aqlli soatdan 45 daqiqadan beri ma'lumot kelmayapti.",
                    recommendation="Soat bemorning qo'liga to'g'ri taqilganligini tekshiring.",
                )
            else:
                return PrognosisInfo(
                    risk_level="low",
                    risk_probability_pct=8,
                    early_warning_hours=72,
                    summary="Barcha asosiy fiziologik ko'rsatkichlar bemorning shaxsiy normasi doirasida barqaror.",
                    recommendation="Muntazam monitoring va belgilangan rejimni davom ettiring.",
                )
