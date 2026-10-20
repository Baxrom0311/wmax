import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Lang } from "@/i18n";

type Theme = "light" | "dark";

interface Prefs {
  lang: Lang;
  setLang: (lang: Lang) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const PrefsContext = createContext<Prefs | null>(null);

const LANG_KEY = "wmax_lang";
const THEME_KEY = "wmax_theme";

function readLang(): Lang {
  try {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === "uz" || saved === "ru" || saved === "en") return saved;
  } catch {
    // storage blocked (private mode / Telegram webview)
  }
  return "uz";
}

function readTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_KEY) ?? localStorage.getItem("wmax_relative_theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    // ignore
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tg = (window as any).Telegram?.WebApp;
  if (tg?.colorScheme === "dark") return "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export const PrefsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Lang>(readLang);
  const [theme, setThemeState] = useState<Theme>(readTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme;
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // ignore
    }
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(LANG_KEY, next);
    } catch {
      // ignore
    }
  }, []);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggleTheme = useCallback(() => setThemeState((prev) => (prev === "dark" ? "light" : "dark")), []);

  const value = useMemo(() => ({ lang, setLang, theme, setTheme, toggleTheme }), [lang, setLang, theme, setTheme, toggleTheme]);
  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
};

// oxlint-disable-next-line react/only-export-components -- hook lives beside its provider
export function usePrefs(): Prefs {
  const ctx = useContext(PrefsContext);
  if (!ctx) throw new Error("usePrefs must be used inside PrefsProvider");
  return ctx;
}
