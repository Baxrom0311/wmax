import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface VitalsProps {
  hr: number | null;
  spo2: number | null;
  sleepHours: number | null;
  lang: Lang;
}

export const Vitals: React.FC<VitalsProps> = ({ hr, spo2, sleepHours, lang }) => {
  return (
    <div className="vitals-row">
      <div className="vital-item">
        <span className="vital-label">{t("vitals.hr", lang)}</span>
        <span className="vital-val">
          {hr !== null ? `${hr}` : "—"}
          {hr !== null && <span className="vital-unit"> {t("vitals.bpm", lang)}</span>}
        </span>
      </div>

      <div className="vital-divider" />

      <div className="vital-item">
        <span className="vital-label">{t("vitals.spo2", lang)}</span>
        <span className="vital-val">
          {spo2 !== null ? `${spo2}` : "—"}
          {spo2 !== null && <span className="vital-unit">%</span>}
        </span>
      </div>

      <div className="vital-divider" />

      <div className="vital-item">
        <span className="vital-label">{t("vitals.sleep", lang)}</span>
        <span className="vital-val">
          {sleepHours !== null ? `${sleepHours}` : "—"}
          {sleepHours !== null && <span className="vital-unit"> {t("vitals.hours", lang)}</span>}
        </span>
      </div>
    </div>
  );
};
