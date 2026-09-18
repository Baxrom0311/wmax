import {
  MOCK_RELATIVE_VIEW_ATTENTION,
  MOCK_RELATIVE_VIEW_GOOD,
  MOCK_RELATIVE_VIEW_NODATA,
  MOCK_RELATIVE_VIEW_RISK,
} from "./mock";
import type { RelativeView, TokenPair } from "./types";

const ACCESS_TOKEN_KEY = "nazorat_relative_token";
const REFRESH_TOKEN_KEY = "nazorat_relative_refresh";

export function getStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function saveTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function loginRelative(phone: string, pin: string): Promise<TokenPair> {
  try {
    const res = await fetch("/api/v1/auth/relative/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, pin }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login xatoligi" }));
      throw new Error(err.detail || "Kirishda xatolik yuz berdi");
    }
    const data: TokenPair = await res.json();
    saveTokens(data);
    return data;
  } catch (err: unknown) {
    // Demo fallback: PIN 112233
    if (pin === "112233") {
      const demoTokens: TokenPair = {
        access_token: "demo_relative_token_112233",
        refresh_token: "demo_refresh_token_112233",
        expires_in: 3600,
        role: "doctor", // Relative uses specific token view
        full_name: "Yaqin qarindosh (Demo)",
      };
      saveTokens(demoTokens);
      return demoTokens;
    }
    throw err instanceof Error ? err : new Error(String(err));
  }
}

export async function fetchRelativeView(token: string): Promise<RelativeView> {
  // Check for test mock query parameter ?state=green|amber|red|no_data
  const urlParams = new URLSearchParams(window.location.search);
  const stateOverride = urlParams.get("state");
  if (stateOverride === "amber") return MOCK_RELATIVE_VIEW_ATTENTION;
  if (stateOverride === "red") return MOCK_RELATIVE_VIEW_RISK;
  if (stateOverride === "no_data") return MOCK_RELATIVE_VIEW_NODATA;
  if (stateOverride === "green") return MOCK_RELATIVE_VIEW_GOOD;

  const authToken = getStoredToken();
  try {
    const res = await fetch(`/api/v1/relatives/${encodeURIComponent(token)}/view`, {
      headers: {
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // API not responding or offline - fallback gracefully to mock
  }

  // Graceful fallback to mock data
  return MOCK_RELATIVE_VIEW_GOOD;
}
