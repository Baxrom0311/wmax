import React from "react";
import { Sun, Moon } from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { cn } from "../lib/utils";

interface ThemeToggleProps {
  theme: "light" | "dark";
  onToggle: () => void;
  lang: Lang;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onToggle, lang }) => {
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        "relative flex items-center justify-center w-8 h-8 rounded-xl border transition-all duration-200 active:scale-95 cursor-pointer",
        isDark
          ? "bg-slate-800 border-slate-700 text-amber-300 hover:bg-slate-700"
          : "bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200"
      )}
      title={`${t("theme.toggle", lang)} (${isDark ? t("theme.dark", lang) : t("theme.light", lang)})`}
      aria-label={t("theme.toggle", lang)}
    >
      {isDark ? (
        <Moon size={15} className="transition-transform duration-300 rotate-0" />
      ) : (
        <Sun size={15} className="transition-transform duration-300 rotate-0 text-amber-500" />
      )}
    </button>
  );
};
