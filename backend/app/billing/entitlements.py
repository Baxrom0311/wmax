from __future__ import annotations

from enum import Enum
from fastapi import HTTPException, status


class Feature(str, Enum):
    VITALS = "vitals"
    BASELINE = "baseline"
    STATUS_COLOR = "status_color"
    CRITICAL_ALERT = "critical_alert"
    SOS_BUTTON = "sos_button"
    AI_PROGNOSIS = "ai_prognosis"
    MEDICATION_RESPONSE = "medication_response"
    UNLIMITED_HISTORY = "unlimited_history"
    PDF_REPORT = "pdf_report"
    ON_CALL_DOCTOR = "on_call_doctor"
    CLINIC_WORKLIST = "clinic_worklist"
    CLINIC_ESCALATION = "clinic_escalation"
    DEVICE_INVENTORY = "device_inventory"


# Immutable feature mapping for each subscription plan
PLAN_FEATURES: dict[str, set[Feature]] = {
    "free": {
        Feature.VITALS,
        Feature.BASELINE,
        Feature.STATUS_COLOR,
        Feature.CRITICAL_ALERT,
        Feature.SOS_BUTTON,
    },
    "premium": {
        Feature.VITALS,
        Feature.BASELINE,
        Feature.STATUS_COLOR,
        Feature.CRITICAL_ALERT,
        Feature.SOS_BUTTON,
        Feature.AI_PROGNOSIS,
        Feature.MEDICATION_RESPONSE,
        Feature.UNLIMITED_HISTORY,
        Feature.PDF_REPORT,
    },
    "premium_doc": {
        Feature.VITALS,
        Feature.BASELINE,
        Feature.STATUS_COLOR,
        Feature.CRITICAL_ALERT,
        Feature.SOS_BUTTON,
        Feature.AI_PROGNOSIS,
        Feature.MEDICATION_RESPONSE,
        Feature.UNLIMITED_HISTORY,
        Feature.PDF_REPORT,
        Feature.ON_CALL_DOCTOR,
    },
    "clinic": {
        Feature.VITALS,
        Feature.BASELINE,
        Feature.STATUS_COLOR,
        Feature.CRITICAL_ALERT,
        Feature.SOS_BUTTON,
        Feature.AI_PROGNOSIS,
        Feature.MEDICATION_RESPONSE,
        Feature.UNLIMITED_HISTORY,
        Feature.PDF_REPORT,
        Feature.CLINIC_WORKLIST,
        Feature.CLINIC_ESCALATION,
        Feature.DEVICE_INVENTORY,
    },
}

PLAN_DETAILS = {
    "free": {
        "name": "Free (Baza)",
        "price_uzs": 0,
        "price_usd": 0.0,
        "billing_period": "forever",
        "description_uz": "Asosiy fiziologik monitoring va kritik xabarnoma",
        "description_ru": "Базовый физиологический мониторинг и критические алерты",
        "features": [f.value for f in PLAN_FEATURES["free"]],
    },
    "premium": {
        "name": "Premium (Tahliliy)",
        "price_uzs": 59_000,
        "price_usd": 4.60,
        "billing_period": "monthly",
        "yearly_discount_uzs": 590_000,
        "description_uz": "AI 72-soatlik prognoz, dori ta'siri, cheksiz tarix va shifokor uchun PDF hisobot",
        "description_ru": "AI прогноз на 72ч, отклик на лекарства, безлимитная история и PDF отчет",
        "features": [f.value for f in PLAN_FEATURES["premium"]],
    },
    "premium_doc": {
        "name": "Premium + Shifokor (Telemeditsina)",
        "price_uzs": 249_000,
        "price_usd": 19.50,
        "billing_period": "monthly",
        "yearly_discount_uzs": 2_490_000,
        "description_uz": "Navbatchi kardiolog nazorati va qizil signalda 15 daqiqada shifokor qo'ng'irog'i",
        "description_ru": "Круглосуточный дежурный кардиолог и экстренный звонок врача при красном сигнале",
        "features": [f.value for f in PLAN_FEATURES["premium_doc"]],
    },
    "clinic": {
        "name": "Klinika / Litsenziya (B2B)",
        "price_uzs": 85_000,
        "price_usd": 6.65,
        "billing_period": "per_patient_month",
        "description_uz": "Davlat va xususiy statsionarlar uchun: Smart Triage, eskalatsiya va qurilmalar arendasi",
        "description_ru": "Для клиник и стационаров: смарт-триаж, эскалация и аренда устройств",
        "features": [f.value for f in PLAN_FEATURES["clinic"]],
    },
}


def is_entitled(plan: str, feature: Feature) -> bool:
    """Check if the given plan includes the feature.
    
    Safety features (critical alerts, SOS, status indicators) are never blocked.
    """
    if feature in {Feature.CRITICAL_ALERT, Feature.SOS_BUTTON, Feature.STATUS_COLOR, Feature.VITALS}:
        return True
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    return feature in features


def check_entitlement(plan: str, feature: Feature) -> None:
    """Raise 402 PAYMENT REQUIRED if the feature is not included in the plan."""
    if not is_entitled(plan, feature):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Ushbu funksiya ('{feature.value}') sizning '{plan}' tarifingizda mavjud emas. Davom etish uchun tarifingizni yangilang.",
        )
