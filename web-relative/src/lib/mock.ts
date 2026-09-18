import type { RelativeView } from "./types";

export const MOCK_RELATIVE_VIEW_GOOD: RelativeView = {
  patient_name: "Otabek Rahimov",
  level: "green",
  level_word_key: "state.good",
  last_reading_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
  trend: {
    slope: -0.25,
    direction: "improving",
    recommendation_key: "rec.continue_monitoring",
    days_used: 7,
  },
  sparkline: [0.78, 0.65, 0.59, 0.50, 0.42, 0.35, 0.22],
  vitals: {
    hr: 74,
    spo2: 98,
    sleep_hours: 6.8,
  },
};

export const MOCK_RELATIVE_VIEW_ATTENTION: RelativeView = {
  patient_name: "Gulnora Matyoqubova",
  level: "amber",
  level_word_key: "state.attention",
  last_reading_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  trend: {
    slope: 0.18,
    direction: "worsening",
    recommendation_key: "rec.visit_within_3_days",
    days_used: 7,
  },
  sparkline: [0.25, 0.30, 0.35, 0.48, 0.58, 0.65, 0.72],
  vitals: {
    hr: 88,
    spo2: 94,
    sleep_hours: 5.2,
  },
};

export const MOCK_RELATIVE_VIEW_RISK: RelativeView = {
  patient_name: "Rustam Karimov",
  level: "red",
  level_word_key: "state.risk",
  last_reading_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
  trend: {
    slope: 0.42,
    direction: "worsening",
    recommendation_key: "rec.contact_today",
    days_used: 7,
  },
  sparkline: [0.30, 0.42, 0.55, 0.68, 0.79, 0.88, 0.95],
  vitals: {
    hr: 114,
    spo2: 87,
    sleep_hours: 3.5,
  },
};

export const MOCK_RELATIVE_VIEW_NODATA: RelativeView = {
  patient_name: "Jumaniyoz Otajonov",
  level: "no_data",
  level_word_key: "state.no_data",
  last_reading_at: new Date(Date.now() - 52 * 60 * 1000).toISOString(),
  trend: {
    slope: 0.02,
    direction: "stable",
    recommendation_key: "rec.routine_followup",
    days_used: 7,
  },
  sparkline: [0.45, 0.42, 0.48, 0.46, 0.44, 0.45, 0.45],
  vitals: {
    hr: null,
    spo2: null,
    sleep_hours: null,
  },
};
