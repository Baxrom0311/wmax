from __future__ import annotations

CLINICAL_SYSTEM_INSTRUCTION = """
Sen NAZORAT tizimining bosh kardiolog va klinik ma'lumotlar tahlilchisisan.
Sening vazifang kasalxonadan chiqarilgan og'ir bemorlarning 5 daqiqalik aqlli soat o'lchovlari (puls, SpO2, HRV, harorat, nafas tezligi, uyqu) va shaxsiy bazaviy me'yorlari asosida:
1. Dekommutatsiya va yomonlashuv xavfini 72 soat oldindan bashorat qilish.
2. Qaysi parametrlar aynan qancha og'ganligini aniqlash.
3. Shifokor va bemor yaqiniga professional, vazmin, tushunarli xulosa va tavsiya berish.
Hech qachon asossiz vahima uyg'otma. Tashxis qo'yma, balki "fiziologik og'ish alomati" sifatida tahlil qil.
Matnlarni o'zbek tilida, aniq va londa shaklda yoz.
"""

def build_clinical_analysis_prompt(
    patient_name: str,
    age: int,
    diagnosis: str,
    level: str,
    recent_vitals: dict,
    deviated_params: dict,
    slope: float,
) -> str:
    return f"""
BEMOR MA'LUMOTLARI:
- Ismi: {patient_name}
- Yoshi: {age} yosh
- Asosiy tashxisi: {diagnosis}
- Joriy ogohlantirish darajasi: {level}
- 7 kunlik trend qiyaligi (slope): {slope}

OXIRGI O'LCHASHLAR:
{recent_vitals}

ME'YORDAN OG'IGAN PARAMETRLAR (Z-SCORE):
{deviated_params}

Quyidagi JSON formatda strukturalangan tahlilni qaytaring:
{{
  "risk_level": "low" | "moderate" | "high",
  "risk_probability_pct": 0 dan 100 gacha butun son,
  "early_warning_hours": 72,
  "summary": "Bemorning holati haqida 2-3 jumlalik klinik xulosa",
  "recommendation": "Shifokor yoki qarovchi uchun 1-2 jumlalik amaliy tavsiya"
}}
"""
