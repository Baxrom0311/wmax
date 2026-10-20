// Telegram Mini App bridge. The SDK script is only loaded when Telegram opened the page,
// which it signals by putting tgWebApp* parameters into the URL hash.

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: { start_param?: string };
  colorScheme?: "light" | "dark";
  ready: () => void;
  expand: () => void;
  enableClosingConfirmation?: () => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const SDK_URL = "https://telegram.org/js/telegram-web-app.js";
let loading: Promise<TelegramWebApp | null> | null = null;

export function openedFromTelegram(): boolean {
  return window.location.hash.includes("tgWebApp") || !!window.Telegram?.WebApp?.initData;
}

export function loadTelegram(): Promise<TelegramWebApp | null> {
  if (window.Telegram?.WebApp) return Promise.resolve(window.Telegram.WebApp);
  if (!openedFromTelegram()) return Promise.resolve(null);
  if (!loading) {
    loading = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = SDK_URL;
      script.async = true;
      const timer = window.setTimeout(() => resolve(null), 4000);
      script.onload = () => {
        window.clearTimeout(timer);
        resolve(window.Telegram?.WebApp ?? null);
      };
      script.onerror = () => {
        window.clearTimeout(timer);
        resolve(null);
      };
      document.head.appendChild(script);
    });
  }
  return loading;
}
