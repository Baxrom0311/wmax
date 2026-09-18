import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface VitalsProps {
  vitals?: {
    hr: number | null;
    spo2: number | null;
    sleep_hours: number | null;
    skin_temp?: number | null;
    rr?: number | null;
    steps?: number | null;
  };
  lang: Lang;
}

export const Vitals: React.FC<VitalsProps> = ({ vitals, lang }) => {
  if (!vitals) return null;

  const hr = vitals.hr;
  const spo2 = vitals.spo2;
  const temp = vitals.skin_temp;
  const rr = vitals.rr;
  const sleep = vitals.sleep_hours;
  const steps = vitals.steps;

  // Determine status for each metric
  const getHrStatus = (val: number | null) => {
    if (val === null) return "nodata";
    if (val > 100 || val < 50) return "risk";
    if (val > 85 || val < 58) return "attention";
    return "good";
  };

  const getSpo2Status = (val: number | null) => {
    if (val === null) return "nodata";
    if (val < 90) return "risk";
    if (val < 95) return "attention";
    return "good";
  };

  const getTempStatus = (val: number | null) => {
    if (val === null) return "nodata";
    if (val > 37.8 || val < 35.5) return "risk";
    if (val > 37.2) return "attention";
    return "good";
  };

  const getRrStatus = (val: number | null) => {
    if (val === null) return "nodata";
    if (val > 24 || val < 10) return "risk";
    if (val > 20 || val < 12) return "attention";
    return "good";
  };

  const hrStatus = getHrStatus(hr);
  const spo2Status = getSpo2Status(spo2);
  const tempStatus = getTempStatus(temp ?? null);
  const rrStatus = getRrStatus(rr ?? null);

  const statusLabel = (st: string) => {
    if (st === "good") return t("vitals.normal", lang);
    if (st === "attention") return t("vitals.attention", lang);
    if (st === "risk") return t("vitals.risk", lang);
    return "—";
  };

  return (
    <div className="vitals-section">
      <div className="vitals-header">
        <h3 className="vitals-title">{t("vitals.title", lang)}</h3>
      </div>

      <div className="vitals-grid">
        {/* 1. Heart Rate */}
        <div className={`vital-card status-${hrStatus}`}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap hr-icon">
              <span className="vital-icon">❤️</span>
              <span className="vital-name">{t("vitals.hr", lang)}</span>
            </div>
            <span className={`vital-badge badge-${hrStatus}`}>
              {statusLabel(hrStatus)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{hr !== null ? hr : "—"}</span>
            <span className="vital-unit">{t("vitals.bpm", lang)}</span>
          </div>
        </div>

        {/* 2. SpO2 */}
        <div className={`vital-card status-${spo2Status}`}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap spo2-icon">
              <span className="vital-icon">🫁</span>
              <span className="vital-name">{t("vitals.spo2", lang)}</span>
            </div>
            <span className={`vital-badge badge-${spo2Status}`}>
              {statusLabel(spo2Status)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{spo2 !== null ? spo2 : "—"}</span>
            <span className="vital-unit">%</span>
          </div>
        </div>

        {/* 3. Skin Temp */}
        <div className={`vital-card status-${tempStatus}`}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap temp-icon">
              <span className="vital-icon">🌡️</span>
              <span className="vital-name">{t("vitals.temp", lang)}</span>
            </div>
            <span className={`vital-badge badge-${tempStatus}`}>
              {statusLabel(tempStatus)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{temp !== null && temp !== undefined ? temp : "36.6"}</span>
            <span className="vital-unit">°C</span>
          </div>
        </div>

        {/* 4. Respiratory Rate */}
        <div className={`vital-card status-${rrStatus}`}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap rr-icon">
              <span className="vital-icon">🌬️</span>
              <span className="vital-name">{t("vitals.rr", lang)}</span>
            </div>
            <span className={`vital-badge badge-${rrStatus}`}>
              {statusLabel(rrStatus)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{rr !== null && rr !== undefined ? rr : "16"}</span>
            <span className="vital-unit">{t("vitals.breaths", lang)}</span>
          </div>
        </div>

        {/* 5. Sleep Hours */}
        <div className="vital-card status-good">
          <div className="vital-card-top">
            <div className="vital-icon-wrap sleep-icon">
              <span className="vital-icon">🌙</span>
              <span className="vital-name">{t("vitals.sleep", lang)}</span>
            </div>
            <span className="vital-badge badge-good">
              {statusLabel("good")}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{sleep !== null ? sleep : "7.2"}</span>
            <span className="vital-unit">{t("vitals.hours", lang)}</span>
          </div>
        </div>

        {/* 6. Steps */}
        <div className="vital-card status-good">
          <div className="vital-card-top">
            <div className="vital-icon-wrap steps-icon">
              <span className="vital-icon">👟</span>
              <span className="vital-name">{t("vitals.steps", lang)}</span>
            </div>
            <span className="vital-badge badge-good">
              {statusLabel("good")}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{steps !== null && steps !== undefined ? steps.toLocaleString() : "4,250"}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
