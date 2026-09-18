import type { RelativePatientItem, RelativeView } from "./types";

export const MOCK_RELATIVE_PATIENTS: RelativePatientItem[] = [
  {
    id: "p-001-red",
    full_name: "Otabek Rahimov",
    relationship: "Otam",
    access_token: "token_otabek_123",
    level: "amber",
    diagnosis: "Surunkali yurak yetishmovchiligi (IIIB)",
    age: 68,
    last_reading_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
  },
  {
    id: "p-002-green",
    full_name: "Salomat Rahamova",
    relationship: "Onam",
    access_token: "token_salomat_456",
    level: "green",
    diagnosis: "Arterial gipertenziya I",
    age: 64,
    last_reading_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },
];

const now = Date.now();

// Generate 7-day hourly points for parametric series
function generateSeriesPoints(base: number, variance: number, anomalyTrend = 0) {
  const pts = [];
  for (let i = 42; i >= 0; i--) {
    const ts = new Date(now - i * 4 * 3600 * 1000).toISOString();
    const noise = Math.sin(i / 2) * variance;
    const trendEffect = i < 12 ? (12 - i) * anomalyTrend : 0;
    pts.push({
      ts,
      value: Number((base + noise + trendEffect).toFixed(1)),
    });
  }
  return pts;
}

export const MOCK_RELATIVE_VIEW_PRO: RelativeView = {
  patient_id: "p-001-red",
  patient_name: "Otabek Rahimov",
  relationship: "Otam (68 yosh)",
  level: "amber",
  level_word_key: "state.attention",
  composite_score: 2.8,
  last_reading_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
  trend: {
    slope: 0.22,
    direction: "worsening",
    recommendation_key: "rec.visit_within_3_days",
    days_used: 7,
  },
  prognosis: {
    risk_level: "moderate",
    risk_probability_pct: 68,
    early_warning_hours: 48,
    summary: "Oxirgi 48 soatda kislorod to'yinishi (SpO2) pasayib, tungi tinch holatdagi puls ko'tarilgan. Salbiy tendensiya kuzatilmoqda.",
    recommendation: "Shifokor bilan bog'lanib, qabul qilinayotgan dorilar dozasini qayta ko'rib chiqish tavsiya etiladi.",
  },
  problems: [
    {
      param: "spo2",
      label: "Qondagi kislorod (SpO₂)",
      deviation: "-4.2% me'yordan past",
      current_value: 92.4,
      baseline_range: "96.0% - 98.5%",
      severity: "moderate",
      explanation: "Bemorning kislorod darajasi odatdagidan pastroq. Chuqur tinch nafas olish va xonani shamollatish zarur.",
    },
    {
      param: "hr_mean",
      label: "Tungi yurak urishi (Puls)",
      deviation: "+14 bpm me'yordan yuqori",
      current_value: 86.0,
      baseline_range: "68 - 74 bpm",
      severity: "moderate",
      explanation: "Uyqu paytida pulsning ortishi yurakning ortiqcha zo'riqishi belgisidir.",
    },
    {
      param: "skin_temp",
      label: "Teri harorati",
      deviation: "Normada",
      current_value: 36.6,
      baseline_range: "36.2°C - 36.9°C",
      severity: "mild",
      explanation: "Harorat barqaror, yallig'lanish belgilari yo'q.",
    },
  ],
  sparkline: [0.35, 0.42, 0.48, 0.58, 0.68, 0.76, 0.82],
  vitals: {
    hr: 86,
    spo2: 92,
    sleep_hours: 5.4,
    skin_temp: 36.6,
    rr: 19.2,
    steps: 1840,
  },
  doctor_contact: {
    name: "Dr. Bahrom Alimov (Kardiolog)",
    phone: "+998901234567",
  },
  series: [
    {
      param: "spo2",
      points: generateSeriesPoints(96.5, 0.8, -0.4),
      baseline_median: 97.0,
      baseline_low: 95.5,
      baseline_high: 98.8,
      deviated_ranges: [{ from: new Date(now - 24 * 3600 * 1000).toISOString(), to: new Date().toISOString() }],
    },
    {
      param: "hr_mean",
      points: generateSeriesPoints(71, 3.5, 1.4),
      baseline_median: 72.0,
      baseline_low: 66.0,
      baseline_high: 76.0,
      deviated_ranges: [{ from: new Date(now - 36 * 3600 * 1000).toISOString(), to: new Date().toISOString() }],
    },
    {
      param: "skin_temp",
      points: generateSeriesPoints(36.5, 0.2),
      baseline_median: 36.5,
      baseline_low: 36.1,
      baseline_high: 36.9,
      deviated_ranges: [],
    },
    {
      param: "rmssd",
      points: generateSeriesPoints(38, 4.0, -1.2),
      baseline_median: 40.0,
      baseline_low: 32.0,
      baseline_high: 48.0,
      deviated_ranges: [],
    },
  ],
  alerts: [
    {
      id: 201,
      ts: new Date(now - 3 * 3600 * 1000).toISOString(),
      level: "amber",
      composite_score: 2.8,
      triggered_params: { spo2: 92, hr_mean: 86 },
      anomaly_score: 0.65,
      reason: "SpO2 pasayishi va tinch holatdagi puls ortishi",
    },
  ],
  tasks: [
    {
      id: 301,
      patient_id: "p-001-red",
      type: "active_call",
      status: "sent",
      created_at: new Date(now - 8 * 3600 * 1000).toISOString(),
      due_at: new Date(now + 16 * 3600 * 1000).toISOString(),
      confirmed_at: null,
      note: null,
    },
  ],
};

export const MOCK_RELATIVE_VIEW_STABLE: RelativeView = {
  ...MOCK_RELATIVE_VIEW_PRO,
  patient_id: "p-002-green",
  patient_name: "Salomat Rahamova",
  relationship: "Onam (64 yosh)",
  level: "green",
  level_word_key: "state.good",
  composite_score: 0.6,
  trend: {
    slope: -0.18,
    direction: "improving",
    recommendation_key: "rec.continue_monitoring",
    days_used: 7,
  },
  prognosis: {
    risk_level: "low",
    risk_probability_pct: 12,
    early_warning_hours: 0,
    summary: "Barcha ko'rsatkichlar shaxsiy me'yor koridorida barqaror.",
    recommendation: "Rejali kundalik rejimni davom ettiring.",
  },
  problems: [],
  sparkline: [0.72, 0.65, 0.54, 0.48, 0.42, 0.35, 0.28],
  vitals: {
    hr: 68,
    spo2: 98,
    sleep_hours: 7.2,
    skin_temp: 36.4,
    rr: 15.8,
    steps: 4200,
  },
  series: [
    {
      param: "spo2",
      points: generateSeriesPoints(98.0, 0.4),
      baseline_median: 98.0,
      baseline_low: 96.5,
      baseline_high: 99.2,
      deviated_ranges: [],
    },
    {
      param: "hr_mean",
      points: generateSeriesPoints(68, 2.5),
      baseline_median: 68.0,
      baseline_low: 62.0,
      baseline_high: 74.0,
      deviated_ranges: [],
    },
  ],
  tasks: [],
};

export const MOCK_RELATIVE_VIEW_NODATA: RelativeView = {
  ...MOCK_RELATIVE_VIEW_PRO,
  level: "no_data",
  level_word_key: "state.no_data",
  last_reading_at: new Date(now - 55 * 60 * 1000).toISOString(),
  vitals: {
    hr: null,
    spo2: null,
    sleep_hours: null,
    skin_temp: null,
    rr: null,
    steps: null,
  },
};
