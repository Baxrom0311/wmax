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

type VitalStatus = "good" | "attention" | "risk" | "nodata";

export const Vitals: React.FC<VitalsProps> = ({ vitals, lang }) => {
  if (!vitals) return null;

  const hr = vitals.hr;
  const spo2 = vitals.spo2;
  const temp = vitals.skin_temp ?? null;
  const rr = vitals.rr ?? null;
  const sleep = vitals.sleep_hours;
  const steps = vitals.steps ?? null;

  // ---- Dynamic status functions for ALL metrics ----
  const getHrStatus = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val > 100 || val < 50) return "risk";
    if (val > 85 || val < 58) return "attention";
    return "good";
  };

  const getSpo2Status = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val < 90) return "risk";
    if (val < 95) return "attention";
    return "good";
  };

  const getTempStatus = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val > 37.8 || val < 35.5) return "risk";
    if (val > 37.2) return "attention";
    return "good";
  };

  const getRrStatus = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val > 24 || val < 10) return "risk";
    if (val > 20 || val < 12) return "attention";
    return "good";
  };

  const getSleepStatus = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val < 4) return "risk";
    if (val < 6) return "attention";
    return "good";
  };

  const getStepsStatus = (val: number | null): VitalStatus => {
    if (val === null) return "nodata";
    if (val < 500) return "risk";
    if (val < 2500) return "attention";
    return "good";
  };

  const hrStatus = getHrStatus(hr);
  const spo2Status = getSpo2Status(spo2);
  const tempStatus = getTempStatus(temp);
  const rrStatus = getRrStatus(rr);
  const sleepStatus = getSleepStatus(sleep);
  const stepsStatus = getStepsStatus(steps);

  const statusLabel = (st: VitalStatus) => {
    if (st === "good") return t("vitals.normal", lang);
    if (st === "attention") return t("vitals.attention", lang);
    if (st === "risk") return t("vitals.risk", lang);
    return "—";
  };

  const formatVal = (val: number | null, fallback = "—") =>
    val !== null && val !== undefined ? val : fallback;

  // Haptic feedback for Telegram Mini App
  const haptic = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const tg = (window as any).Telegram?.WebApp?.HapticFeedback;
    if (tg) tg.selectionChanged();
  };

  return (
    <div className="vitals-section">
      <div className="vitals-header">
        <div className="vitals-header-left">
          <span className="vitals-header-icon">🩺</span>
          <h3 className="vitals-title">{t("vitals.title", lang)}</h3>
        </div>
        <span className="vitals-live-pill">
          <span className="live-pill-dot" /> LIVE
        </span>
      </div>

      <div className="vitals-grid">
        {/* 1. Heart Rate */}
        <div className={`vital-card status-${hrStatus}`} onClick={haptic}>
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
            <span className="vital-number">{formatVal(hr)}</span>
            <span className="vital-unit">{t("vitals.bpm", lang)}</span>
            {hrStatus !== "good" && hr !== null && (
              <span className={`vital-trend-arrow ${hrStatus}`}>{hr > 85 ? "↑" : "↓"}</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.norm_prefix", lang)} {t("vitals.norm_hr", lang)}</span>
          </div>
        </div>

        {/* 2. SpO2 */}
        <div className={`vital-card status-${spo2Status}`} onClick={haptic}>
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
            <span className="vital-number">{formatVal(spo2)}</span>
            <span className="vital-unit">%</span>
            {spo2Status !== "good" && spo2 !== null && (
              <span className={`vital-trend-arrow ${spo2Status}`}>↓</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.norm_prefix", lang)} {t("vitals.norm_spo2", lang)}</span>
          </div>
        </div>

        {/* 3. Skin Temp */}
        <div className={`vital-card status-${tempStatus}`} onClick={haptic}>
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
            <span className="vital-number">{formatVal(temp)}</span>
            <span className="vital-unit">°C</span>
            {tempStatus !== "good" && temp !== null && (
              <span className={`vital-trend-arrow ${tempStatus}`}>{temp > 37.2 ? "↑" : "↓"}</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.norm_prefix", lang)} {t("vitals.norm_temp", lang)}</span>
          </div>
        </div>

        {/* 4. Respiratory Rate */}
        <div className={`vital-card status-${rrStatus}`} onClick={haptic}>
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
            <span className="vital-number">{formatVal(rr)}</span>
            <span className="vital-unit">{t("vitals.breaths", lang)}</span>
            {rrStatus !== "good" && rr !== null && (
              <span className={`vital-trend-arrow ${rrStatus}`}>{rr > 20 ? "↑" : "↓"}</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.norm_prefix", lang)} {t("vitals.norm_rr", lang)}</span>
          </div>
        </div>

        {/* 5. Sleep Hours — DYNAMIC STATUS */}
        <div className={`vital-card status-${sleepStatus}`} onClick={haptic}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap sleep-icon">
              <span className="vital-icon">🌙</span>
              <span className="vital-name">{t("vitals.sleep", lang)}</span>
            </div>
            <span className={`vital-badge badge-${sleepStatus}`}>
              {statusLabel(sleepStatus)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">{formatVal(sleep)}</span>
            <span className="vital-unit">{t("vitals.hours", lang)}</span>
            {sleepStatus !== "good" && sleep !== null && (
              <span className={`vital-trend-arrow ${sleepStatus}`}>↓</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.norm_prefix", lang)} {t("vitals.norm_sleep", lang)}</span>
          </div>
        </div>

        {/* 6. Steps — DYNAMIC STATUS */}
        <div className={`vital-card status-${stepsStatus}`} onClick={haptic}>
          <div className="vital-card-top">
            <div className="vital-icon-wrap steps-icon">
              <span className="vital-icon">👟</span>
              <span className="vital-name">{t("vitals.steps", lang)}</span>
            </div>
            <span className={`vital-badge badge-${stepsStatus}`}>
              {statusLabel(stepsStatus)}
            </span>
          </div>
          <div className="vital-val-row">
            <span className="vital-number">
              {steps !== null && steps !== undefined ? steps.toLocaleString() : "—"}
            </span>
            <span className="vital-unit">{t("vitals.steps_unit", lang)}</span>
            {stepsStatus !== "good" && steps !== null && (
              <span className={`vital-trend-arrow ${stepsStatus}`}>↓</span>
            )}
          </div>
          <div className="vital-sub-note">
            <span>{t("vitals.steps_target", lang)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
