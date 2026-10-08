from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class CalmState(StrEnum):
    PEACEFUL = "peaceful"      # Hammasi joyida, barqaror
    ATTENTION = "attention"    # E'tibor talab (kichik o'zgarishlar)
    ALERT = "alert"            # Zudlik bilan e'tibor (ogohlantirish)


@dataclass(frozen=True)
class PeaceOfMindIndex:
    score: int  # 0 to 100 (100 = to'liq xotirjamlik va barqarorlik)
    state: CalmState
    status_text_uz: str
    status_text_ru: str
    status_text_en: str
    device_worn: bool
    summary_hint_uz: str


def calculate_peace_of_mind(
    alert_level: Literal["green", "amber", "red", "no_data"],
    worn: bool,
    battery_pct: float | None = None,
    recent_sos: bool = False,
    recent_readings_count: int = 12,
) -> PeaceOfMindIndex:
    if recent_sos:
        return PeaceOfMindIndex(
            score=10,
            state=CalmState.ALERT,
            status_text_uz="Zudlik bilan e'tibor talab qilinadi (SOS signali)",
            status_text_ru="Требуется срочное внимание (Сигнал SOS)",
            status_text_en="Urgent attention required (SOS signal)",
            device_worn=worn,
            summary_hint_uz="Yaqiningiz yordam so'rash tugmasini bosgan",
        )

    if alert_level == "red":
        return PeaceOfMindIndex(
            score=25,
            state=CalmState.ALERT,
            status_text_uz="Ko'rsatkichlar me'yordan chetlashdi",
            status_text_ru="Показатели отклонились от нормы",
            status_text_en="Vitals deviate from normal",
            device_worn=worn,
            summary_hint_uz="Ko'rsatkichlar me'yordan sezilarli chetlashgan, holatni tekshirish tavsiya etiladi",
        )

    if not worn:
        return PeaceOfMindIndex(
            score=50,
            state=CalmState.ATTENTION,
            status_text_uz="Qurilma qo'lda emas",
            status_text_ru="Устройство снято",
            status_text_en="Device is not worn",
            device_worn=False,
            summary_hint_uz="Qurilma yechilgan, ma'lumotlar kelishi to'xtagan",
        )

    if alert_level == "amber":
        return PeaceOfMindIndex(
            score=70,
            state=CalmState.ATTENTION,
            status_text_uz="Biroz tebranishlar kuzatilmoqda",
            status_text_ru="Наблюдаются небольшие колебания",
            status_text_en="Minor fluctuations observed",
            device_worn=True,
            summary_hint_uz="O'lchovlarda tebranishlar bor, holatni kuzatish tavsiya etiladi",
        )

    if alert_level == "no_data" or recent_readings_count < 3:
        return PeaceOfMindIndex(
            score=60,
            state=CalmState.ATTENTION,
            status_text_uz="Ma'lumotlar yangilanmoqda",
            status_text_ru="Данные обновляются",
            status_text_en="Data updating",
            device_worn=True,
            summary_hint_uz="Aloqa tiklanmoqda, oxirgi o'lchovlar kutilmoqda",
        )

    # Yashil / Green
    base_score = 98
    if battery_pct is not None and battery_pct < 15:
        base_score = 88
        hint = "O'lchovlar me'yorda. Iltimos, soatni quvvatlashga qo'ying."
    else:
        hint = "O'lchangan barcha ko'rsatkichlar shaxsiy me'yorda."

    return PeaceOfMindIndex(
        score=base_score,
        state=CalmState.PEACEFUL,
        status_text_uz="Holati barqaror",
        status_text_ru="Состояние стабильное",
        status_text_en="Condition stable",
        device_worn=True,
        summary_hint_uz=hint,
    )
