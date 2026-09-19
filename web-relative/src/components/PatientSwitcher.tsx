import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { RelativePatientItem } from "../lib/types";
import { LEVEL_COLOR, LEVEL_WORD_KEY } from "../lib/types";

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
        <span className="switcher-icon">👥</span>
        <span className="switcher-title">{t("patients.title", lang)}</span>
      </div>
      <div className="patient-cards-row">
        {patients.map((p) => {
          const isActive = p.id === activePatientId;
          const statusColor = LEVEL_COLOR[p.level];
          const initials = p.full_name
            .split(" ")
            .map((w) => w[0])
            .slice(0, 2)
            .join("");

          const handleCardClick = () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const tg = (window as any).Telegram?.WebApp?.HapticFeedback;
            if (tg) tg.selectionChanged();
            onSelect(p);
          };

          return (
            <button
              key={p.id}
              type="button"
              className={`patient-card-btn ${isActive ? "active" : ""}`}
              onClick={handleCardClick}
              style={isActive ? { borderColor: statusColor, boxShadow: `0 4px 14px ${statusColor}22` } : undefined}
            >
              <div
                className="patient-btn-avatar"
                style={{
                  backgroundColor: `${statusColor}18`,
                  color: statusColor,
                  border: `1.5px solid ${statusColor}40`,
                }}
              >
                {initials}
              </div>
              <div className="patient-btn-info">
                <div className="patient-btn-header-line">
                  <span className="patient-rel-tag">{p.relationship || t("patients.select", lang)}</span>
                  <span
                    className="patient-level-mini-badge"
                    style={{ color: statusColor, backgroundColor: `${statusColor}18` }}
                  >
                    {t(LEVEL_WORD_KEY[p.level], lang)}
                  </span>
                </div>
                <span className="patient-btn-name">{p.full_name}</span>
              </div>
              <span
                className={`patient-status-indicator pulse-${p.level}`}
                style={{ backgroundColor: statusColor }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
};
