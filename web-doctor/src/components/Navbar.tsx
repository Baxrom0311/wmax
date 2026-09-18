import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface NavbarProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  doctorName?: string;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  lang,
  onLangChange,
  doctorName,
  onLogout,
}) => {
  const initials = doctorName
    ? doctorName
        .split(" ")
        .filter((w) => !w.startsWith("Dr."))
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "DR";

  return (
    <header className="doc-header">
      <div className="doc-logo">
        <div className="medical-pulse-logo">
          <svg className="ecg-svg" viewBox="0 0 32 32" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 16 9 16 12 7 16 25 19 12 22 18 25 16 29 16" />
          </svg>
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="doc-logo-title">NAZORAT</span>
            <span className="doc-logo-badge">WORKSTATION PRO</span>
          </div>
          <div className="live-status-sub">
            <span className="live-pulse-dot" />
            <span>{t("app.monitoring_active", lang)}</span>
          </div>
        </div>
      </div>

      <div className="doc-header-right">
        {doctorName && (
          <div className="doctor-profile-pill">
            <div className="doctor-avatar-circle">{initials || "MD"}</div>
            <div className="doctor-meta">
              <span className="doctor-name-text">{doctorName}</span>
              <span className="doctor-role-text">Shifokor-kardiolog</span>
            </div>
          </div>
        )}

        <div className="lang-pill-container">
          <button
            type="button"
            className={`lang-pill-btn ${lang === "uz" ? "active" : ""}`}
            onClick={() => onLangChange("uz")}
          >
            UZ
          </button>
          <button
            type="button"
            className={`lang-pill-btn ${lang === "ru" ? "active" : ""}`}
            onClick={() => onLangChange("ru")}
          >
            RU
          </button>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="logout-nav-btn"
          title={t("logout", lang)}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span>{t("logout", lang)}</span>
        </button>
      </div>
    </header>
  );
};
