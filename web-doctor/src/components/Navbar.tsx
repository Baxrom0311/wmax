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
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <span className="doc-logo-badge">CLINICAL</span>
        <span className="doc-logo-title">{t("app.doctor_panel", lang)}</span>
      </div>

      <div className="doc-header-right">
        {doctorName && <span className="user-info">{doctorName}</span>}

        <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
          <button
            type="button"
            className={`doc-lang-btn ${lang === "uz" ? "active" : ""}`}
            onClick={() => onLangChange("uz")}
          >
            UZ
          </button>
          <span style={{ color: "var(--color-line)" }}>|</span>
          <button
            type="button"
            className={`doc-lang-btn ${lang === "ru" ? "active" : ""}`}
            onClick={() => onLangChange("ru")}
          >
            RU
          </button>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="btn btn-outline"
          style={{ padding: "4px 10px", fontSize: "12px" }}
        >
          {t("logout", lang)}
        </button>
      </div>
    </header>
  );
};
