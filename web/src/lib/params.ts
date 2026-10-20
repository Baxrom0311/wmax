import type { Lang } from "@/i18n";

export interface ParamMeta {
  title: Record<Lang, string>;
  short: string;
  unit: string;
  color: string;
}

/** Physiological parameters emitted by backend/algo; colours are chart series only. */
export const PARAMS: Record<string, ParamMeta> = {
  hr_mean: { title: { uz: "Yurak urishi (puls)", ru: "Частота пульса", en: "Heart rate" }, short: "HR", unit: "bpm", color: "#e11d48" },
  spo2: { title: { uz: "Qon kislorodi (SpO₂)", ru: "Сатурация (SpO₂)", en: "Blood oxygen (SpO₂)" }, short: "SpO₂", unit: "%", color: "#0d9488" },
  skin_temp: { title: { uz: "Teri harorati", ru: "Температура кожи", en: "Skin temperature" }, short: "T°", unit: "°C", color: "#d97706" },
  rmssd: { title: { uz: "Yurak ritmi variabelligi (RMSSD)", ru: "Вариабельность ритма (RMSSD)", en: "Heart rate variability (RMSSD)" }, short: "RMSSD", unit: "ms", color: "#0284c7" },
  sdnn: { title: { uz: "Sinus ritmi variabelligi (SDNN)", ru: "Вариабельность (SDNN)", en: "Variability (SDNN)" }, short: "SDNN", unit: "ms", color: "#6366f1" },
  rr_est: { title: { uz: "Nafas soni", ru: "Частота дыхания", en: "Respiratory rate" }, short: "RR", unit: "/min", color: "#0891b2" },
  rr: { title: { uz: "Nafas soni", ru: "Частота дыхания", en: "Respiratory rate" }, short: "RR", unit: "/min", color: "#0891b2" },
  steps: { title: { uz: "Kunlik qadamlar", ru: "Шаги за день", en: "Daily steps" }, short: "Steps", unit: "", color: "#16a34a" },
  sleep_frag: { title: { uz: "Uyqu uzilishi", ru: "Фрагментация сна", en: "Sleep fragmentation" }, short: "Sleep", unit: "%", color: "#9333ea" },
  sleep_hours: { title: { uz: "Uyqu davomiyligi", ru: "Длительность сна", en: "Sleep duration" }, short: "Sleep", unit: "h", color: "#9333ea" },
};

export function paramMeta(param: string): ParamMeta {
  return PARAMS[param] ?? { title: { uz: param, ru: param, en: param }, short: param, unit: "", color: "#0f766e" };
}
