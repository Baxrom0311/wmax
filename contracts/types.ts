// =====================================================================
// NAZORAT — frontend contract. FROZEN.
// Mirrors contracts/openapi.yaml. A3 (web-doctor) and A4 (web-relative)
// COPY this file into their own src/ (no cross-folder imports) and must
// not change the shapes.
// =====================================================================

export type AlertLevel = "green" | "amber" | "red" | "no_data";
export type Phase = "calib" | "learning" | "full";
export type TrendDirection = "improving" | "stable" | "worsening";
export type TaskStatus = "created" | "sent" | "seen" | "done" | "overdue";
export type Role = "doctor" | "nurse" | "admin";

// ---- design tokens (identical in both apps) ----
export const COLORS = {
  good:     "#2E7D5B",
  attention:"#C77A0A",
  risk:     "#B3261E",
  nodata:   "#8A8780",
  bg:       "#FAFAF8",
  text:     "#1C1B1F",
  line:     "#D8D6D0",
} as const;

export const LEVEL_COLOR: Record<AlertLevel, string> = {
  green:   COLORS.good,
  amber:   COLORS.attention,
  red:     COLORS.risk,
  no_data: COLORS.nodata,
};

// ---- i18n keys the BACKEND emits. Both apps must translate all of them. ----
export const I18N_KEYS = [
  "state.good", "state.attention", "state.risk", "state.no_data",
  "rec.contact_today", "rec.visit_within_3_days",
  "rec.routine_followup", "rec.continue_monitoring",
  "trend.improving", "trend.stable", "trend.worsening",
] as const;
export type I18nKey = (typeof I18N_KEYS)[number];

export const LEVEL_WORD_KEY: Record<AlertLevel, I18nKey> = {
  green:   "state.good",
  amber:   "state.attention",
  red:     "state.risk",
  no_data: "state.no_data",
};

export interface Trend {
  slope: number;
  direction: TrendDirection;
  recommendation_key: I18nKey;
  days_used: number;
}

export interface Task {
  id: number;
  patient_id: string;
  type: "active_call" | "red_alert";
  status: TaskStatus;
  created_at: string;
  due_at: string;
  confirmed_at: string | null;
  note: string | null;
}

export interface PatientSummary {
  id: string;
  full_name: string;
  age: number;
  sex: "m" | "f";
  diagnosis: string;
  district: string;
  phase: Phase;
  level: AlertLevel;
  composite_score: number;
  triggered_params: Record<string, number>;
  trend: Trend;
  last_reading_at: string | null;
  open_task: Task | null;
}

export interface SeriesPoint { ts: string; value: number | null }

export interface ParamSeries {
  param: string;
  points: SeriesPoint[];
  baseline_median: number | null;
  baseline_low: number | null;
  baseline_high: number | null;
  deviated_ranges: { from: string; to: string }[];
}

export interface Alert {
  id: number;
  ts: string;
  level: AlertLevel;
  composite_score: number;
  triggered_params: Record<string, number>;
  /** ADVISORY ONLY — display as a secondary label; it never drives `level`. */
  anomaly_score: number | null;
  reason: string;
}

export interface ProblemItem {
  param: string;
  label: string;
  deviation: string;
  current_value: number;
  baseline_range: string;
  severity: "mild" | "moderate" | "severe";
  explanation: string;
}

export interface PrognosisInfo {
  risk_level: "low" | "moderate" | "high";
  risk_probability_pct: number;
  early_warning_hours: number;
  summary: string;
  recommendation: string;
}

export interface RelativePatientItem {
  id: string;
  full_name: string;
  relationship: string;
  access_token: string;
  level: AlertLevel;
  diagnosis: string;
  age: number;
  last_reading_at: string | null;
}

export interface PatientDetail extends PatientSummary {
  series: ParamSeries[];
  alerts: Alert[];
  tasks: Task[];
  baseline_approved: boolean;
  prognosis?: PrognosisInfo;
  problems?: ProblemItem[];
}

export interface RelativeView {
  patient_id: string;
  patient_name: string;
  relationship?: string;
  level: AlertLevel;
  level_word_key: I18nKey;
  composite_score: number;
  last_reading_at: string | null;
  trend: Trend;
  prognosis: PrognosisInfo;
  problems: ProblemItem[];
  series: ParamSeries[];
  alerts: Alert[];
  tasks: Task[];
  /** 7 daily values normalised 0..1 — a shape, not a chart. */
  sparkline: number[];
  vitals: {
    hr: number | null;
    spo2: number | null;
    sleep_hours: number | null;
    skin_temp?: number | null;
    rr?: number | null;
    steps?: number | null;
  };
  doctor_contact?: {
    name: string;
    phone: string;
  } | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  role: Role;
  full_name: string;
}

export interface RelativeLoginResponse extends TokenPair {
  patients: RelativePatientItem[];
}

export const API_BASE = "/api/v1";

