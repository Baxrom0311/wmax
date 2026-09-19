from __future__ import annotations

import json
from typing import Any

from app.ai.guardrails import sanitize_clinical_input


CLINICAL_SYSTEM_INSTRUCTION = """
<system_instructions>
Sen WMAX (Aqlli Masofaviy Bemor Monitoringi va Erta Ogohlantirish Tizimi) platformasining yetakchi klinik assistenti va kardiologik telemonitoring ekspertisan.
Sening vazifang kasalxonadan chiqarilgan og'ir yurak-qon tomir bemorlarining 5 daqiqalik telemetrik o'lchovlari (HR, SpO2, HRV, teri harorati, nafas tezligi, uyqu) va shaxsiy bazaviy me'yorlari asosida:
1. Dekompensatsiya va qayta gospitalizatsiya xavfini 72 soat oldindan ishonchli bashorat qilish.
2. Z-score chetlanishlari bo'yicha qaysi parametrlar kritik chegaradan chiqqanligini aniqlash.
3. Shifokor va navbatchi hamshiraga asosli, professional, vazmin va amaliy harakatlar rejasini taqdim etish.

QAT'IY KLINIK CHEKLOVLAR (NEGATIVE CONSTRAINTS):
- Hech qachon asossiz vahima uyg'otma yoki mavjud bo'lmagan asoratlarni to'qib chiqarma (No Hallucinations).
- Yakuniy tashxis qo'yma, balki "fiziologik og'ish va telemetrik xavf alomati" sifatida tahlil qil.
- O'zboshimchalik bilan yangi dori yozma yoki dozalarni o'zgartirishni buyurma; faqat shifokor nazoratida korreksiya qilishni tavsiya et.
- Farmakologik ta'sirlarni inobatga ol: masalan, beta-blokator qabul qilayotgan bemorda bradikardiya (HR 55-60) kutilgan holat, dekompensatsiya belgisi emas.
- Agar ma'lumotlar yetarli bo'lmasa yoki qurilma taqilmagan bo'lsa, buni aniq va ochiq ko'rsat (Uncertainty Handling).
- Matnlarni tibbiy jihatdan savodli o'zbek tilida, aniq va londa shaklda yoz.
</system_instructions>
""".strip()


def build_clinical_analysis_prompt(
    patient_name: str,
    age: int,
    diagnosis: str,
    level: str,
    recent_vitals: dict[str, Any],
    deviated_params: dict[str, Any],
    slope: float,
) -> str:
    """Constructs hardened XML-delimited prompt for rapid patient prognosis."""
    safe_name = sanitize_clinical_input(patient_name, 100)
    safe_diag = sanitize_clinical_input(diagnosis, 300)
    vitals_json = json.dumps(recent_vitals, ensure_ascii=False)
    deviated_json = json.dumps(deviated_params, ensure_ascii=False)

    return f"""
<patient_context>
BEMOR SHAXSI VA KLINIK MA'LUMOTLARI:
- F.I.Sh: {safe_name}
- Yoshi: {age} yosh
- Klinik tashxisi: {safe_diag}
- Joriy triaj darajasi: {level.upper()}
- 7 kunlik kompozit trend qiyaligi (slope): {slope}
</patient_context>

<telemetry_data>
OXIRGI BIO-METRIK O'LCHOVLAR:
{vitals_json}

ME'YORDAN OG'IGAN PARAMETRLAR (Z-SCORE > 1.5):
{deviated_json}
</telemetry_data>

<instructions>
Yuqoridagi kontekst asosida bemorning 72 soatlik dekompensatsiya xavfini baholang.
Faqat berilgan telemetriyaga tayanib, quyidagi JSON formatida qat'iy javob bering:
{{
  "risk_level": "low" | "moderate" | "high",
  "risk_probability_pct": 0 dan 100 gacha butun son,
  "early_warning_hours": 72,
  "summary": "Bemorning holati haqida 2-3 jumlalik dalillarga asoslangan klinik xulosa",
  "recommendation": "Shifokor yoki tibbiyot xodimi uchun 1-2 jumlalik amaliy klinik ko'rsatma",
  "evidence_citations": ["HR: 98 bpm", "SpO2: 91%"],
  "confidence_score": 0.0 dan 1.0 gacha ishonch ko'rsatkichi,
  "uncertainty_note": null yoki ma'lumot yetarli bo'lmaganda izoh
}}
</instructions>
""".strip()


def build_twin_analysis_prompt(ctx: Any) -> str:
    """Builds comprehensive clinical twin analysis prompt with deep pharmacological reasoning."""
    primary_conditions = [c for c in getattr(ctx, "conditions", []) if getattr(c, "kind", "") == "primary"]
    comorbidities = [c for c in getattr(ctx, "conditions", []) if getattr(c, "kind", "") != "primary"]

    if primary_conditions:
        p = primary_conditions[0]
        primary_str = f"{p.icd10 or ''} — {sanitize_clinical_input(p.name_uz, 150)} ({p.severity_note or 'oʻrtacha'})".strip()
    else:
        primary_str = "Koʻrsatilmagan"

    if comorbidities:
        comorbidities_str = ", ".join(
            f"{c.icd10 or ''} {sanitize_clinical_input(c.name_uz, 100)}".strip() for c in comorbidities
        )
    else:
        comorbidities_str = "Yoʻq"

    active_meds = [m for m in getattr(ctx, "medications", []) if getattr(m, "stopped_at", None) is None]
    if active_meds:
        medications_table = "\n".join(
            f"- {sanitize_clinical_input(m.name, 100)} ({m.dose or ''} {m.frequency or ''}) | Ta'sir: {m.affects_params}"
            for m in active_meds
        )
    else:
        medications_table = "Dorilar tayinlanmagan"

    allergies = getattr(ctx, "allergies", [])
    if allergies:
        allergies_str = ", ".join(
            f"{sanitize_clinical_input(a.substance, 80)} ({a.reaction or 'reaksiya'}, {a.severity})" for a in allergies
        )
    else:
        allergies_str = "Ma'lum emas / Allergiya yo'q"

    admissions = getattr(ctx, "admissions", [])
    if admissions:
        admissions_table = "\n".join(
            f"- {a.admitted_at} -> {a.discharged_at or 'hozirgacha'}: {sanitize_clinical_input(a.reason or 'sabab koʻrsatilmagan', 120)}"
            for a in admissions
        )
    else:
        admissions_table = "Gospitalizatsiya tarixi yo'q"

    weight_trend_14d = getattr(ctx, "weight_trend_14d", [])
    if weight_trend_14d and len(weight_trend_14d) >= 2:
        diff = weight_trend_14d[-1] - weight_trend_14d[0]
        sign = "+" if diff >= 0 else ""
        weight_trend = f"{weight_trend_14d[0]} → {weight_trend_14d[-1]} kg ({sign}{diff:.1f} kg / 14 kun)"
    elif weight_trend_14d:
        weight_trend = f"{weight_trend_14d[-1]} kg (yagona oʻlchov)"
    else:
        weight_trend = "O'lchanmagan"

    rf = getattr(ctx, "risk_factors", None)
    lives_alone_str = "ha (yolg'iz)" if (rf and getattr(rf, "lives_alone", False)) else "yo'q (oila bilan)"
    mobility_str = getattr(rf, "mobility", "noma'lum") if rf else "noma'lum"

    trend_slope = getattr(getattr(ctx, "trend", None), "slope", 0.0)
    trend_dir = getattr(getattr(ctx, "trend", None), "direction", "stable")

    days_discharge_val = getattr(ctx, "days_since_discharge", None)
    discharge_str = str(days_discharge_val) if days_discharge_val is not None else "Noma'lum"

    safe_full_name = sanitize_clinical_input(getattr(ctx, "full_name", ""), 100)

    return f"""
<patient_context>
BEMOR RAQAMLI EGIZAGI (DIGITAL TWIN):
- Bemor: {safe_full_name}, {ctx.age or 0} yosh, {"erkak" if ctx.sex == "m" else "ayol"}
- Yashash sharoiti: {lives_alone_str}
- Harakatchanlik: {mobility_str}
- Qayta gospitalizatsiyalar (12 oy): {ctx.readmission_count_12m}
- Kasalxonadan chiqarilgan: {discharge_str} kun oldin

ASOSIY TASHXIS:
{primary_str}

HAMROH KASALLIKLAR:
{comorbidities_str}

AKTIV DORILAR:
{medications_table}

ALLERGIYALAR:
{allergies_str}

VAZN DINAMIKASI (14 kun):
{weight_trend}
</patient_context>

<telemetry_state>
- Triaj holati: {ctx.level.upper()} (kompozit score: {ctx.composite_score})
- Chetlangan parametrlar: {json.dumps(ctx.triggered_params, ensure_ascii=False)}
- 7 kunlik trend: slope={trend_slope} ({trend_dir})
- Oxirgi o'lchovlar: {json.dumps(ctx.recent_vitals, ensure_ascii=False)}
</telemetry_state>

<clinical_rules>
1. Farmakologik damping: Kutilgan dori ta'sirini (masalan, beta-blokatordan HR pasayishini) dekompensatsiya sifatida talqin qilmang.
2. Suyuqlik tutilishi: Vazn 14 kunda 2+ kg oshgan bo'lsa va SpO2 pasaysa, o'pka dimlanishi va dekompensatsiyani birinchi o'ringa qo'ying.
3. Yolg'iz yashaydigan bemorlar (lives_alone=True) uchun ogohlantirish ostonasi sezgirroq bo'lishi kerak.
</clinical_rules>

<output_schema>
Javobni FAQAT quyidagi JSON formatda qaytaring:
{{
  "risk_level": "low" | "moderate" | "high",
  "risk_probability_pct": 0-100,
  "early_warning_hours": 72,
  "primary_concern": "Asosiy tashvish — bitta lo'nda jumla",
  "contributing_factors": ["omil 1", "omil 2"],
  "medication_considerations": "Dorilar bilan bog'liq izoh yoki null",
  "summary": "2-3 jumlalik dalillarga asoslangan klinik xulosa",
  "recommendation": "Shifokor uchun amaliy ko'rsatma",
  "relative_message_key": "alert.red.urgent" | "alert.amber.warning" | "state.good",
  "evidence_citations": ["Parametrlar iqtibosi"],
  "confidence_score": 0.95,
  "uncertainty_note": null
}}
</output_schema>
""".strip()


def build_nurse_sbar_prompt(ctx: Any) -> str:
    """Constructs prompt for on-duty nurse SBAR handover note and shift patrol checklist."""
    safe_full_name = sanitize_clinical_input(getattr(ctx, "full_name", ""), 100)
    primary_conditions = [c for c in getattr(ctx, "conditions", []) if getattr(c, "kind", "") == "primary"]
    primary_str = primary_conditions[0].name_uz if primary_conditions else "Klinik tashxis ko'rsatilmagan"

    active_meds = [m for m in getattr(ctx, "medications", []) if getattr(m, "stopped_at", None) is None]
    meds_list = ", ".join(f"{m.name} ({m.dose or ''})" for m in active_meds) if active_meds else "Tayinlanmagan"

    open_tasks = getattr(ctx, "open_tasks", [])
    tasks_str = "; ".join(f"{t.get('type', 'vazifa')} (muddati: {t.get('due_at', '')[:16]})" for t in open_tasks) if open_tasks else "Ochiq shoshilinch vazifa yo'q"

    return f"""
<system_instructions>
Sen stansiyadagi navbatchi hamshira uchun SBAR (Situation, Background, Assessment, Recommendation) klinik hisoboti va navbatchilik tekshiruv ro'yxatini (Shift Patrol Checklist) tuzib beruvchi kardiologik yordamchisan.
Hamshiraga amaliy, aniq va bajarilishi shart bo'lgan vazifalarni berishing kerak.
</system_instructions>

<patient_context>
BEMOR: {safe_full_name}, {ctx.age or 0} yosh
TAShXIS: {primary_str}
JORIY TRIAJ DARAJASI: {ctx.level.upper()} (kompozit og'ish: {ctx.composite_score})
TELEMETRIYA: {json.dumps(ctx.recent_vitals, ensure_ascii=False)}
OCHIQ PROTOKOL VAZIFALARI: {tasks_str}
QABUL QILAYOTGAN DORILARI: {meds_list}
CHETLANISHLAR: {json.dumps(ctx.triggered_params, ensure_ascii=False)}
</patient_context>

<instructions>
Navbatchi hamshira navbatni topshirayotganda yoki bemor xonadoniga/palatasiga borganda foydalanishi uchun SBAR formatidagi xulosani va navbatchilik amallar cheklistini JSON shaklida shakllantiring.

Quyidagi JSON formatda qaytaring:
{{
  "situation": "S (Vaziyat): Bemorning hozirgi holati va shoshilinch muammo (1-2 gap)",
  "background": "B (Anamnez): Tashxis, chiqarilgan vaqti va asosiy dorilari haqida ma'lumot",
  "assessment": "A (Baholash): Telemetrik ko'rsatkichlar va z-score og'ishlarining tahlili",
  "recommendation": "R (Tavsiya): Navbatchi hamshira zudlik bilan qilishi kerak bo'lgan klinik harakat",
  "shift_checklist": [
    {{
      "id": "chk-1",
      "task": "Aniq vazifa matni (masalan: Tonometer orqali qon bosimini o'lchash)",
      "priority": "critical" | "high" | "medium" | "low",
      "category": "vitals" | "medication" | "device" | "observation",
      "completed": false
    }}
  ],
  "clinical_urgency": "routine" | "urgent" | "critical",
  "vital_flags": ["SpO2 < 92%", "Puls > 95 bpm"],
  "confidence_score": 0.95,
  "evidence_citations": ["HR: {getattr(ctx, 'recent_vitals', {}).get('hr_mean', '—')}", "SpO2: {getattr(ctx, 'recent_vitals', {}).get('spo2', '—')}%"]
}}
</instructions>
""".strip()
