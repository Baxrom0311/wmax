import type { PatientDetail, PatientSummary } from "./types";

export const MOCK_PATIENTS: PatientSummary[] = [
  {
    id: "p-001-red",
    full_name: "Otabek Rahimov",
    age: 68,
    sex: "m",
    diagnosis: "Surunkali yurak yetishmovchiligi (IIIB)",
    district: "Urganch",
    phase: "full",
    level: "red",
    composite_score: 4.8,
    triggered_params: { spo2: 87, hr_mean: 112, skin_temp: 37.4 },
    trend: {
      slope: 0.38,
      direction: "worsening",
      recommendation_key: "rec.contact_today",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    open_task: {
      id: 101,
      patient_id: "p-001-red",
      type: "active_call",
      status: "created",
      created_at: new Date(Date.now() - 6 * 3600 * 1000).toISOString(),
      due_at: new Date(Date.now() + 18 * 3600 * 1000).toISOString(),
      confirmed_at: null,
      note: null,
    },
  },
  {
    id: "p-002-amber",
    full_name: "Gulnora Matyoqubova",
    age: 72,
    sex: "f",
    diagnosis: "Arterial gipertenziya III, diabet",
    district: "Xiva",
    phase: "learning",
    level: "amber",
    composite_score: 2.6,
    triggered_params: { rmssd: 18.2, hr_mean: 94 },
    trend: {
      slope: 0.16,
      direction: "worsening",
      recommendation_key: "rec.visit_within_3_days",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
    open_task: {
      id: 102,
      patient_id: "p-002-amber",
      type: "active_call",
      status: "sent",
      created_at: new Date(Date.now() - 20 * 3600 * 1000).toISOString(),
      due_at: new Date(Date.now() + 4 * 3600 * 1000).toISOString(),
      confirmed_at: null,
      note: null,
    },
  },
  {
    id: "p-004-nodata",
    full_name: "Jumaniyoz Otajonov",
    age: 65,
    sex: "m",
    diagnosis: "O'pkaning surunkali obstruktiv kasalligi (O'SOK)",
    district: "Shovot",
    phase: "full",
    level: "no_data",
    composite_score: 0.0,
    triggered_params: {},
    trend: {
      slope: 0.0,
      direction: "stable",
      recommendation_key: "rec.continue_monitoring",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 55 * 60 * 1000).toISOString(),
    open_task: null,
  },
  {
    id: "p-003-green",
    full_name: "Rustam Karimov",
    age: 59,
    sex: "m",
    diagnosis: "Miokard infarktidan keyingi holat",
    district: "Xonqa",
    phase: "full",
    level: "green",
    composite_score: 0.8,
    triggered_params: {},
    trend: {
      slope: -0.22,
      direction: "improving",
      recommendation_key: "rec.routine_followup",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    open_task: null,
  },
];

export function getMockPatientDetail(id: string): PatientDetail {
  const summary = MOCK_PATIENTS.find((p) => p.id === id) || MOCK_PATIENTS[0];

  // Generate 7 days of hourly points
  const now = Date.now();
  const pointsHR = [];
  const pointsSPO2 = [];
  const pointsTemp = [];
  const pointsRMSSD = [];
  const pointsRR = [];
  const pointsSteps = [];

  for (let i = 42; i >= 0; i--) {
    const ts = new Date(now - i * 4 * 3600 * 1000).toISOString();
    const severityFactor = summary.level === "red" && i < 15 ? (15 - i) * 1.5 : 0;

    pointsHR.push({
      ts,
      value: Math.round(72 + Math.sin(i / 3) * 6 + severityFactor * 2.5),
    });
    pointsSPO2.push({
      ts,
      value: Math.max(84, Math.round(97 - Math.cos(i / 4) * 1.5 - severityFactor * 0.7)),
    });
    pointsTemp.push({
      ts,
      value: Number((36.4 + Math.sin(i / 5) * 0.3 + (severityFactor > 0 ? 0.8 : 0)).toFixed(1)),
    });
    pointsRMSSD.push({
      ts,
      value: Math.max(12, Math.round(34 - severityFactor * 1.2 + Math.sin(i / 2) * 4)),
    });
    pointsRR.push({
      ts,
      value: Math.round(16 + Math.sin(i / 4) * 2 + (severityFactor > 0 ? 4 : 0)),
    });
    pointsSteps.push({
      ts,
      value: Math.max(0, Math.round(450 + Math.sin(i / 2) * 350 - severityFactor * 20)),
    });
  }

  return {
    ...summary,
    baseline_approved: summary.phase === "full",
    prognosis: {
      risk_level: summary.level === "red" ? "high" : summary.level === "amber" ? "moderate" : "low",
      risk_probability_pct: summary.level === "red" ? 86 : summary.level === "amber" ? 64 : 14,
      early_warning_hours: 48,
      summary:
        summary.level === "red"
          ? "SpO2 pasayishi (-2.4σ) va tinch holatda yuqori yurak urishi (+3.1σ) kuzatilmoqda. 72 soat ichida gospitalizatsiya xavfi yuqori."
          : "Fiziologik parametrlar shaxsiy me'yor koridorida barqaror.",
      recommendation:
        summary.level === "red"
          ? "Bugun zudlik bilan bemor xonadoniga patronaj tashrifini amalga oshirish va dori dozasini qayta sozlash zarur."
          : "Rejali dispanser nazoratini davom ettirish.",
    },
    problems: [
      {
        param: "spo2",
        label: "Kislorod to'yinishi (SpO₂)",
        deviation: summary.level === "red" ? "-2.4σ me'yordan past" : "Normada",
        current_value: summary.level === "red" ? 87.0 : 97.5,
        baseline_range: "95.5% - 98.8%",
        severity: summary.level === "red" ? "severe" : "mild",
        explanation: "Gipoksemiya belgilari. O'pka va yurak yetishmovchiligi kuchayishi mumkin.",
      },
      {
        param: "hr_mean",
        label: "Tinch holatdagi puls",
        deviation: summary.level === "red" ? "+3.1σ me'yordan yuqori" : "Normada",
        current_value: summary.level === "red" ? 112.0 : 72.0,
        baseline_range: "66 - 76 bpm",
        severity: summary.level === "red" ? "severe" : "mild",
        explanation: "Kompensator taxikardiya. Gemodinamik barqarorsizlik xavfi.",
      },
    ],
    series: [
      {
        param: "hr_mean",
        points: pointsHR,
        baseline_median: 72,
        baseline_low: 66,
        baseline_high: 76,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsHR[pointsHR.length - 8].ts, to: pointsHR[pointsHR.length - 1].ts }]
            : [],
      },
      {
        param: "spo2",
        points: pointsSPO2,
        baseline_median: 97,
        baseline_low: 95.5,
        baseline_high: 98.8,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsSPO2[pointsSPO2.length - 6].ts, to: pointsSPO2[pointsSPO2.length - 1].ts }]
            : [],
      },
      {
        param: "skin_temp",
        points: pointsTemp,
        baseline_median: 36.5,
        baseline_low: 36.1,
        baseline_high: 36.9,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsTemp[pointsTemp.length - 5].ts, to: pointsTemp[pointsTemp.length - 1].ts }]
            : [],
      },
      {
        param: "rmssd",
        points: pointsRMSSD,
        baseline_median: 38,
        baseline_low: 32,
        baseline_high: 48,
        deviated_ranges: [],
      },
      {
        param: "rr_est",
        points: pointsRR,
        baseline_median: 16,
        baseline_low: 14,
        baseline_high: 18,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsRR[pointsRR.length - 4].ts, to: pointsRR[pointsRR.length - 1].ts }]
            : [],
      },
      {
        param: "steps",
        points: pointsSteps,
        baseline_median: 450,
        baseline_low: 200,
        baseline_high: 700,
        deviated_ranges: [],
      },
    ],
    alerts: [
      {
        id: 1,
        ts: new Date(now - 2 * 3600 * 1000).toISOString(),
        level: summary.level,
        composite_score: summary.composite_score,
        triggered_params: summary.triggered_params,
        anomaly_score: summary.level === "red" ? 0.84 : null,
        reason:
          summary.level === "red"
            ? "SpO2 pasayishi va taxikardiya aniqlandi"
            : "Barqaror parametrlar",
      },
    ],
    tasks: summary.open_task ? [summary.open_task] : [],
  };
}
