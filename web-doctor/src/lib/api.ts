import { getMockPatientDetail, MOCK_PATIENTS } from "./mock";
import type { PatientDetail, PatientSummary, TokenPair } from "./types";

const TOKEN_KEY = "nazorat_doctor_jwt";
const USER_KEY = "nazorat_doctor_user";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveTokens(tokens: TokenPair): void {
  localStorage.setItem(TOKEN_KEY, tokens.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(tokens));
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function loginDoctor(phone: string, pass: string): Promise<TokenPair> {
  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, password: pass }),
    });
    if (res.ok) {
      const data: TokenPair = await res.json();
      saveTokens(data);
      return data;
    }
  } catch {
    // backend offline fallback
  }

  // Demo fallback
  if ((phone === "+998901234567" || phone === "901234567") && pass === "nazorat123") {
    const demo: TokenPair = {
      access_token: "demo_doctor_token_jwt",
      refresh_token: "demo_refresh_token",
      expires_in: 3600,
      role: "doctor",
      full_name: "Dr. Alimov Bahrom",
    };
    saveTokens(demo);
    return demo;
  }

  throw new Error("Telefon yoki parol noto'g'ri");
}

export async function fetchPatients(): Promise<PatientSummary[]> {
  const token = getStoredToken();
  try {
    const res = await fetch("/api/v1/patients", {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback to mock
  }
  return MOCK_PATIENTS;
}

export async function fetchPatientDetail(id: string): Promise<PatientDetail> {
  const token = getStoredToken();
  try {
    const res = await fetch(`/api/v1/patients/${encodeURIComponent(id)}?days=7`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return getMockPatientDetail(id);
}

export async function confirmTask(taskId: number, note: string): Promise<void> {
  const token = getStoredToken();
  try {
    await fetch(`/api/v1/tasks/${taskId}/confirm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ note }),
    });
  } catch {
    // ignore in demo
  }
}

export async function approveBaseline(patientId: string): Promise<void> {
  const token = getStoredToken();
  try {
    await fetch(`/api/v1/patients/${encodeURIComponent(patientId)}/approve-baseline`, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch {
    // ignore in demo
  }
}
