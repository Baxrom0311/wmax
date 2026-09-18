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
      <div className="section-header">
        <h3 className="section-title">
          <span>🩺</span> {t("actions.title", lang)}
        </h3>
      </div>

      {/* Doctor card */}
      <div className="doctor-contact-card">
        <div className="doc-info-left">
          <div className="doc-avatar-wrap">
            <span className="doc-avatar">👨‍⚕️</span>
            <span className="doc-online-dot" />
          </div>
          <div>
            <span className="doc-label">{t("actions.doctor_name", lang)}</span>
            <h4 className="doc-fullname">{doctorContact?.name || "Dr. Bahrom Alimov"}</h4>
            <span className="doc-specialty">{t("actions.doc_specialty", lang)}</span>
            {recommendation && <p className="doc-rec-text">💬 {recommendation}</p>}
          </div>
        </div>

        <div className="doc-action-btns">
          <a
            href={`tel:${doctorContact?.phone || "+998901234567"}`}
            className="contact-btn call-btn"
          >
            <span>📞</span>
            <span>{t("actions.call_doctor", lang)}</span>
          </a>
          <a
            href="https://t.me/WMAX_uz_bot"
            target="_blank"
            rel="noreferrer"
            className="contact-btn telegram-btn"
          >
            <span>✈️</span>
            <span>{t("actions.telegram", lang)}</span>
          </a>
        </div>
      </div>

      {/* Active Call / Patronaj notice if present */}
      {activeTask && (
        <div className="relative-active-call-card">
          <div className="active-call-pulse-badge">⏳</div>
          <div className="active-call-text">
            <strong>{t("actions.active_call_status", lang)}:</strong>
            <p>{t("actions.active_call_scheduled", lang)}</p>
          </div>
        </div>
      )}

      {/* Emergency 103 Call Button */}
      <a href="tel:103" className="emergency-call-bar">
        <span className="emergency-siren">🚨</span>
        <span className="emergency-text">{t("actions.emergency", lang)}</span>
        <span className="emergency-dial-badge">103</span>
      </a>
    </div>
  );
};
