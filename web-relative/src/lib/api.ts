import {
  MOCK_RELATIVE_PATIENTS,
  MOCK_RELATIVE_VIEW_NODATA,
  MOCK_RELATIVE_VIEW_PRO,
  MOCK_RELATIVE_VIEW_STABLE,
} from "./mock";
import type {
  RelativeLoginResponse,
  RelativePatientItem,
  RelativeView,
  TokenPair,
} from "./types";

const ACCESS_TOKEN_KEY = "nazorat_relative_token";
const REFRESH_TOKEN_KEY = "nazorat_relative_refresh";
const PATIENTS_KEY = "nazorat_relative_patients";

export function getStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredPatients(): RelativePatientItem[] {
  try {
    const raw = localStorage.getItem(PATIENTS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveTokens(tokens: TokenPair, patients?: RelativePatientItem[]): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  if (patients) {
    localStorage.setItem(PATIENTS_KEY, JSON.stringify(patients));
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(PATIENTS_KEY);
}

export async function loginRelative(phone: string, pin: string): Promise<RelativeLoginResponse> {
  try {
    const res = await fetch("/api/v1/auth/relative/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, pin }),
    });
    if (res.ok) {
      const data: RelativeLoginResponse = await res.json();
      saveTokens(data, data.patients);
      return data;
    }
  } catch {
    // API not responding, fallback to demo
  }

  // Demo fallback: PIN 112233
  if (pin === "112233") {
    const demoResponse: RelativeLoginResponse = {
      access_token: "token_otabek_123",
      refresh_token: "demo_refresh_token_112233",
      expires_in: 3600,
      role: "doctor",
      full_name: "Farzand (Qarovchi)",
      patients: MOCK_RELATIVE_PATIENTS,
    };
    saveTokens(demoResponse, demoResponse.patients);
    return demoResponse;
  }

  throw new Error("PIN-kod noto'g'ri (Demo: 112233)");
}

export async function fetchRelativeView(token: string): Promise<RelativeView> {
  // Check for test mock query parameter ?state=green|amber|red|no_data
  const urlParams = new URLSearchParams(window.location.search);
  const stateOverride = urlParams.get("state");
  if (stateOverride === "green") return MOCK_RELATIVE_VIEW_STABLE;
  if (stateOverride === "no_data") return MOCK_RELATIVE_VIEW_NODATA;
  if (stateOverride === "amber" || stateOverride === "red") return MOCK_RELATIVE_VIEW_PRO;

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
    // fallback
  }

  // If token belongs to second patient (Salomat opa)
  if (token === "token_salomat_456") {
    return MOCK_RELATIVE_VIEW_STABLE;
  }

  return MOCK_RELATIVE_VIEW_PRO;
}
