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
    : "BA";

  return (
    <header className="doc-header">
      <div className="doc-header-brand">
        <div className="med-emblem">
          <svg
            viewBox="0 0 24 24"
            width="22"
            height="22"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: "drop-shadow(0 0 6px rgba(56, 189, 248, 0.8))" }}
          >
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        </div>
        <div className="brand-text-block">
          <div className="brand-primary-line">
            <span className="brand-name">NAZORAT</span>
            <span className="brand-divider">/</span>
            <span className="brand-dept">Kardiologiya Dispanseri</span>
            <span className="brand-badge-official">KLINIK STANSIYA</span>
          </div>
          <div className="brand-sub-line">
            <span className="telemetry-live-dot" />
            <span>Telemetriya faol · Sinxronizatsiya: 15s</span>
          </div>
        </div>
      </div>

      <div className="doc-header-controls">
        {doctorName && (
          <div className="physician-badge">
            <div className="physician-avatar">{initials}</div>
            <div className="physician-info">
              <span className="physician-name">{doctorName}</span>
              <span className="physician-post">Shifokor-kardiolog</span>
            </div>
          </div>
        )}

        <div className="official-lang-toggle">
          <button
            type="button"
            className={`lang-opt ${lang === "uz" ? "active" : ""}`}
            onClick={() => onLangChange("uz")}
          >
            O'ZB
          </button>
          <span className="lang-sep">|</span>
          <button
            type="button"
            className={`lang-opt ${lang === "ru" ? "active" : ""}`}
            onClick={() => onLangChange("ru")}
          >
            РУС
          </button>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="btn-official-logout"
          title={t("logout", lang)}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
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
