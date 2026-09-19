// =====================================================================
// WMAX — frontend contract. FROZEN.
// Mirrors contracts/openapi.yaml. A3 (web-doctor) and A4 (web-relative)
// COPY this file into their own src/ (no cross-folder imports) and must
// not change the shapes.
// =====================================================================

export type AlertLevel = "green" | "amber" | "red" | "no_data";
export type Phase = "calib" | "learning" | "full";
export type TrendDirection = "improving" | "stable" | "worsening";
export type TaskStatus = "created" | "sent" | "seen" | "done" | "overdue";
export type Role = "doctor" | "nurse" | "admin" | "dispatcher";
export type AuthRole = Role | "relative" | "patient";

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
  evidence_citations?: string[];
  confidence_score?: number;
  uncertainty_note?: string | null;
}

export interface NurseChecklistItem {
  id: string;
  task: string;
  priority: "low" | "medium" | "high" | "critical";
  category: "vitals" | "medication" | "device" | "observation";
  completed: boolean;
}

export interface NurseHandoverSBAR {
  situation: string;
  background: string;
  assessment: string;
  recommendation: string;
  shift_checklist: NurseChecklistItem[];
  clinical_urgency: "routine" | "urgent" | "critical";
  vital_flags: string[];
  confidence_score: number;
  evidence_citations: string[];
  generated_at?: string | null;
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
  role: AuthRole;
  full_name: string;
}

export interface RelativeLoginResponse extends TokenPair {
  patients: RelativePatientItem[];
}

export const API_BASE = "/api/v1";

// =====================================================================
// V2 SOS & CLINICAL DOMAIN EXTENSIONS
// =====================================================================

export type SosStatus = "raised" | "acknowledged" | "dispatched_103" | "cancelled" | "resolved";
export type SosSource = "watch_button" | "phone_app" | "relative_portal" | "auto_critical";

export interface AddressItem {
  id: string;
  patient_id: string;
  kind: "home" | "temporary" | "work" | "other";
  region: string;
  district: string;
  mahalla?: string | null;
  street?: string | null;
  house?: string | null;
  flat?: string | null;
  landmark?: string | null;
  entrance_note?: string | null;
  lat?: number | null;
  lon?: number | null;
  geo_source?: "manual" | "device_gps" | "geocoded" | null;
  geo_accuracy_m?: number | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConditionItem {
  id: string;
  patient_id: string;
  icd10: string;
  name_uz: string;
  name_ru?: string | null;
  kind: "primary" | "comorbidity" | "past";
  severity_note?: string | null;
  diagnosed_at?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface MedicationItem {
  id: string;
  patient_id: string;
  name: string;
  dose?: string | null;
  frequency?: string | null;
  route?: string | null;
  affects_params: Record<string, "lowers" | "raises">;
  started_at?: string | null;
  stopped_at?: string | null;
  stop_reason?: string | null;
  prescribed_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AllergyItem {
  id: string;
  patient_id: string;
  substance: string;
  reaction?: string | null;
  severity: "mild" | "moderate" | "severe" | "life_threatening";
  created_at: string;
}

export interface MeasurementItem {
  id: string;
  patient_id: string;
  measured_at: string;
  weight_kg?: number | null;
  height_cm?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  waist_circ_cm?: number | null;
  source: "clinic" | "patient" | "relative" | "smart_scale";
  created_at: string;
}

export interface RiskFactorsItem {
  id?: string;
  patient_id: string;
  smoking: "never" | "former" | "current";
  alcohol: "none" | "occasional" | "heavy";
  diabetes: boolean;
  ckd: boolean;
  mobility: "independent" | "with_aid" | "bedridden";
  lives_alone: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AdmissionItem {
  id: string;
  patient_id: string;
  admitted_at: string;
  discharged_at?: string | null;
  facility?: string | null;
  department?: string | null;
  reason?: string | null;
  discharge_summary?: string | null;
  readmission_within_30d: boolean;
}

export interface SosEventItem {
  id: string;
  patient_id: string;
  patient_name?: string;
  raised_at: string;
  status: SosStatus;
  source: SosSource;
  address_snapshot: Record<string, any>;
  clinical_snapshot: Record<string, any>;
  vitals_snapshot?: Record<string, any> | null;
  device_lat?: number | null;
  device_lon?: number | null;
  dispatched_at?: string | null;
  dispatch_ref_103?: string | null;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  resolution_note?: string | null;
}

export interface PatientFullProfile {
  patient: PatientSummary;
  addresses: AddressItem[];
  conditions: ConditionItem[];
  medications: MedicationItem[];
  allergies: AllergyItem[];
  measurements: MeasurementItem[];
  risk_factors: RiskFactorsItem | null;
  admissions: AdmissionItem[];
}
