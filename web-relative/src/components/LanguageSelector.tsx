import React from "react";
import type { Lang } from "../i18n";
import { cn } from "../lib/utils";

interface LanguageSelectorProps {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "UZ" },
  { code: "ru", label: "RU" },
  { code: "en", label: "EN" },
];

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ lang, onChange }) => {
  return (
    <div className="flex items-center gap-0.5 bg-slate-100 border border-slate-200 rounded-xl p-0.5">
      {LANGS.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => onChange(l.code)}
          className={cn(
            "text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all",
            lang === l.code
              ? "bg-white text-blue-700 shadow-sm"
              : "text-slate-400 hover:text-slate-600"
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
};
