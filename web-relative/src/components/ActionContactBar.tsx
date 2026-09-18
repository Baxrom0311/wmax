import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { Task } from "../lib/types";

interface ActionContactBarProps {
  doctorContact?: { name: string; phone: string } | null;
  activeTask?: Task | null;
  recommendation?: string;
  lang: Lang;
}

export const ActionContactBar: React.FC<ActionContactBarProps> = ({
  doctorContact,
  activeTask,
  recommendation,
  lang,
}) => {
  return (
    <div className="action-contact-section">
      <h3 className="section-title">{t("actions.title", lang)}</h3>

      {/* Doctor card */}
      <div className="doctor-contact-card">
        <div className="doc-info-left">
          <span className="doc-avatar">👨‍⚕️</span>
          <div>
            <span className="doc-label">{t("actions.doctor_name", lang)}</span>
            <h4 className="doc-fullname">{doctorContact?.name || "Dr. Bahrom Alimov"}</h4>
            {recommendation && <p className="doc-rec-text">💬 {recommendation}</p>}
          </div>
        </div>

        <div className="doc-action-btns">
          <a
            href={`tel:${doctorContact?.phone || "+998901234567"}`}
            className="contact-btn call-btn"
          >
            📞 {t("actions.call_doctor", lang)}
          </a>
          <a
            href="https://t.me/nazorat_bot"
            target="_blank"
            rel="noreferrer"
            className="contact-btn telegram-btn"
          >
            ✈️ {t("actions.telegram", lang)}
          </a>
        </div>
      </div>

      {/* Active Call / Patronaj notice if present */}
      {activeTask && (
        <div className="relative-active-call-card">
          <span className="active-call-icon">📋</span>
          <div className="active-call-text">
            <strong>{t("actions.active_call_status", lang)}:</strong>
            <p>{t("actions.active_call_scheduled", lang)}</p>
          </div>
        </div>
      )}

      {/* Emergency 103 Call Button */}
      <a href="tel:103" className="emergency-call-bar">
        🚨 {t("actions.emergency", lang)}
      </a>
    </div>
  );
};
