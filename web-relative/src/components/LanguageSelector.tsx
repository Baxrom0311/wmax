import React from "react";
import type { Lang } from "../i18n";

interface LanguageSelectorProps {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ lang, onChange }) => {
  return (
    <div className="lang-selector">
      <button
        type="button"
        className={`lang-btn ${lang === "uz" ? "active" : ""}`}
        onClick={() => onChange("uz")}
      >
        UZ
      </button>
      <span className="lang-sep">|</span>
      <button
        type="button"
        className={`lang-btn ${lang === "ru" ? "active" : ""}`}
        onClick={() => onChange("ru")}
      >
        RU
      </button>
      <span className="lang-sep">|</span>
      <button
        type="button"
        className={`lang-btn ${lang === "en" ? "active" : ""}`}
        onClick={() => onChange("en")}
      >
        EN
      </button>
    </div>
  );
};
