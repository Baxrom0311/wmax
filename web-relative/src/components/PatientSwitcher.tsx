import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { RelativePatientItem } from "../lib/types";
import { LEVEL_COLOR } from "../lib/types";

interface PatientSwitcherProps {
  patients: RelativePatientItem[];
  activePatientId: string;
  onSelect: (patient: RelativePatientItem) => void;
  lang: Lang;
}

export const PatientSwitcher: React.FC<PatientSwitcherProps> = ({
  patients,
  activePatientId,
  onSelect,
  lang,
}) => {
  if (patients.length <= 1) return null;

  return (
    <div className="patient-switcher-container">
      <div className="switcher-header">
        <span className="switcher-title">{t("patients.title", lang)}:</span>
      </div>
      <div className="patient-cards-row">
        {patients.map((p) => {
          const isActive = p.id === activePatientId;
          const statusColor = LEVEL_COLOR[p.level];

          return (
            <button
              key={p.id}
              type="button"
              className={`patient-card-btn ${isActive ? "active" : ""}`}
              onClick={() => onSelect(p)}
            >
              <span
                className="patient-status-indicator"
                style={{ backgroundColor: statusColor }}
              />
              <div className="patient-btn-info">
                <span className="patient-rel-tag">{p.relationship || t("patients.select", lang)}</span>
                <span className="patient-btn-name">{p.full_name}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
