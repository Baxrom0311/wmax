import { create } from "zustand";
import type { Lang } from "../i18n";

type Theme = "light" | "dark" | "system";

interface UIState {
  theme: Theme;
  lang: Lang;
  isSidebarCollapsed: boolean;
  isCopilotOpen: boolean;
  isNotificationsOpen: boolean;
  unreadAlertCount: number;

  setTheme: (theme: Theme) => void;
  setLang: (lang: Lang) => void;
  toggleSidebar: () => void;
  setCopilotOpen: (open: boolean) => void;
  toggleCopilot: () => void;
  setNotificationsOpen: (open: boolean) => void;
  setUnreadAlertCount: (count: number) => void;
}

const THEME_KEY = "nazorat_theme";
const LANG_KEY = "nazorat_lang";

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY) as Theme | null;
  if (stored && ["light", "dark", "system"].includes(stored)) {
    return stored;
  }
  return "light";
}

function getInitialLang(): Lang {
  const stored = localStorage.getItem(LANG_KEY) as Lang | null;
  if (stored && ["uz", "ru"].includes(stored)) {
    return stored;
  }
  return "uz";
}

function applyTheme(theme: Theme) {
  let effectiveTheme = theme;
  if (theme === "system") {
    effectiveTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  if (effectiveTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

export const useUIStore = create<UIState>((set, get) => {
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  return {
    theme: initialTheme,
    lang: getInitialLang(),
    isSidebarCollapsed: false,
    isCopilotOpen: false,
    isNotificationsOpen: false,
    unreadAlertCount: 0,

    setTheme: (theme: Theme) => {
      localStorage.setItem(THEME_KEY, theme);
      applyTheme(theme);
      set({ theme });
    },
    setLang: (lang: Lang) => {
      localStorage.setItem(LANG_KEY, lang);
      set({ lang });
    },
    toggleSidebar: () => {
      set({ isSidebarCollapsed: !get().isSidebarCollapsed });
    },
    setCopilotOpen: (open: boolean) => {
      set({ isCopilotOpen: open });
    },
    toggleCopilot: () => {
      set({ isCopilotOpen: !get().isCopilotOpen });
    },
    setNotificationsOpen: (open: boolean) => {
      set({ isNotificationsOpen: open });
    },
    setUnreadAlertCount: (count: number) => {
      set({ unreadAlertCount: count });
    },
  };
});
