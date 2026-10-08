from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class ClinicalCohort(StrEnum):
    GENERAL = "general"
    HYPERTENSION = "hypertension"
    DIABETES = "diabetes"
    POST_STROKE = "post_stroke"


@dataclass(frozen=True)
class CohortProfile:
    cohort: ClinicalCohort
    title_uz: str
    weights: Mapping[str, float]
    amber_threshold: float
    red_threshold: float
    critical_hr_rest: float
    critical_spo2: float
    description: str


COHORT_PROFILES: dict[ClinicalCohort, CohortProfile] = {
    ClinicalCohort.GENERAL: CohortProfile(
        cohort=ClinicalCohort.GENERAL,
        title_uz="Umumiy profilaktika",
        weights={
            "hr_mean": 1.0,
            "spo2": 1.5,
            "skin_temp": 1.2,
            "rmssd": 0.8,
            "sleep_frag": 0.7,
            "steps": 0.6,
            "rr_est": 1.3,
        },
        amber_threshold=2.0,
        red_threshold=4.0,
        critical_hr_rest=130.0,
        critical_spo2=88.0,
        description="Standart monitoring profili",
    ),
    ClinicalCohort.HYPERTENSION: CohortProfile(
        cohort=ClinicalCohort.HYPERTENSION,
        title_uz="Arterial gipertoniya",
        weights={
            "hr_mean": 1.4,
            "rmssd": 1.2,
            "spo2": 1.2,
            "skin_temp": 1.0,
            "sleep_frag": 0.9,
            "steps": 0.5,
            "rr_est": 1.1,
        },
        amber_threshold=1.75,
        red_threshold=3.6,
        critical_hr_rest=120.0,
        critical_spo2=89.0,
        description="Puls tebranishi va vegetativ tonusga sezgir profil",
    ),
    ClinicalCohort.DIABETES: CohortProfile(
        cohort=ClinicalCohort.DIABETES,
        title_uz="Qandli diabet",
        weights={
            "skin_temp": 1.4,
            "sleep_frag": 1.2,
            "rmssd": 1.1,
            "hr_mean": 1.0,
            "spo2": 1.3,
            "steps": 0.8,
            "rr_est": 1.0,
        },
        amber_threshold=1.85,
        red_threshold=3.8,
        critical_hr_rest=125.0,
        critical_spo2=89.0,
        description="Harorat va periferik neyropatiya bilan bog'liq o'zgarishlar",
    ),
    ClinicalCohort.POST_STROKE: CohortProfile(
        cohort=ClinicalCohort.POST_STROKE,
        title_uz="Insultdan keyingi reabilitatsiya",
        weights={
            "hr_mean": 1.3,
            "spo2": 1.6,
            "rr_est": 1.4,
            "rmssd": 1.2,
            "skin_temp": 1.1,
            "sleep_frag": 1.0,
            "steps": 0.9,
        },
        amber_threshold=1.6,
        red_threshold=3.2,
        critical_hr_rest=115.0,
        critical_spo2=90.0,
        description="Yuqori hushyorlik va erta eskalatsiya talab etuvchi guruh",
    ),
}


def get_cohort_profile(cohort_str: str | None) -> CohortProfile:
    try:
        cohort = ClinicalCohort(str(cohort_str).lower()) if cohort_str else ClinicalCohort.GENERAL
    except ValueError:
        cohort = ClinicalCohort.GENERAL
    return COHORT_PROFILES[cohort]
