from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass
class ClinicalIntakeSummary:
    patient_id: UUID
    generated_at: datetime
    monitoring_days: int
    hr_avg: float
    hr_min: float
    hr_max: float
    spo2_avg: float
    spo2_min: float
    anomaly_events_count: int
    circadian_disruptions_count: int
    summary_text_uz: str
    summary_html: str


def generate_intake_summary(
    patient_id: UUID,
    patient_name: str,
    readings: list[dict[str, Any]],
    cohort_name: str = "Umumiy",
) -> ClinicalIntakeSummary:
    now = datetime.now(timezone.utc)
    if not readings:
        return ClinicalIntakeSummary(
            patient_id=patient_id,
            generated_at=now,
            monitoring_days=0,
            hr_avg=0.0,
            hr_min=0.0,
            hr_max=0.0,
            spo2_avg=0.0,
            spo2_min=0.0,
            anomaly_events_count=0,
            circadian_disruptions_count=0,
            summary_text_uz="So'nggi 14 kunda yetarli ma'lumot to'planmagan.",
            summary_html="<div>Ma'lumot mavjud emas</div>",
        )

    hrs = [r["hr_mean"] for r in readings if r.get("hr_mean") is not None]
    spo2s = [r["spo2"] for r in readings if r.get("spo2") is not None]

    hr_avg = round(sum(hrs) / len(hrs), 1) if hrs else 0.0
    hr_min = round(min(hrs), 1) if hrs else 0.0
    hr_max = round(max(hrs), 1) if hrs else 0.0

    spo2_avg = round(sum(spo2s) / len(spo2s), 1) if spo2s else 0.0
    spo2_min = round(min(spo2s), 1) if spo2s else 0.0

    anomalies = sum(1 for r in readings if r.get("alert_level") in ("amber", "red"))
    circadian_disruptions = sum(
        1 for r in readings if r.get("is_night") and (r.get("hr_mean") or 0) > (hr_avg + 15)
    )

    summary_text = (
        f"Bemor: {patient_name}. Profil: {cohort_name}. "
        f"14 kunlik o'rtacha yurak urishi: {hr_avg} bpm (min: {hr_min}, max: {hr_max}). "
        f"SpO2 o'rtacha: {spo2_avg}%. Aniqlangan anomaliyalar soni: {anomalies} ta."
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>14 Kunlik Qabul Xulosasi</title>
    <style>
      body {{ font-family: sans-serif; margin: 24px; color: #1e293b; }}
      .header {{ border-bottom: 2px solid #0284c7; padding-bottom: 8px; margin-bottom: 16px; }}
      .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }}
      .card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; }}
      .val {{ font-size: 20px; font-weight: bold; color: #0f172a; }}
      .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; background: #e0f2fe; color: #0369a1; }}
    </style>
    </head>
    <body>
      <div class="header">
        <h2>WMAX — Shifokor Qabul Xulosasi (14 Kun)</h2>
        <p><strong>Bemor:</strong> {patient_name} &bull; <strong>Klaster:</strong> <span class="badge">{cohort_name}</span> &bull; <strong>Sana:</strong> {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
      </div>
      <div class="grid">
        <div class="card"><div>O'rtacha Puls</div><div class="val">{hr_avg} bpm</div><small>Min: {hr_min} / Max: {hr_max}</small></div>
        <div class="card"><div>SpO2 To'yinganligi</div><div class="val">{spo2_avg}%</div><small>Minimal: {spo2_min}%</small></div>
        <div class="card"><div>Anomal Hodisalar</div><div class="val">{anomalies} ta</div><small>Tungi buzilishlar: {circadian_disruptions}</small></div>
      </div>
      <div>
        <h3>Klinik Xulosa va Tavsiya</h3>
        <p>{summary_text}</p>
      </div>
    </body>
    </html>
    """

    return ClinicalIntakeSummary(
        patient_id=patient_id,
        generated_at=now,
        monitoring_days=14,
        hr_avg=hr_avg,
        hr_min=hr_min,
        hr_max=hr_max,
        spo2_avg=spo2_avg,
        spo2_min=spo2_min,
        anomaly_events_count=anomalies,
        circadian_disruptions_count=circadian_disruptions,
        summary_text_uz=summary_text,
        summary_html=html.strip(),
    )
