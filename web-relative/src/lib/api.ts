import type {
  AlertLevel,
  RelativeLoginResponse,
  RelativePatientItem,
  RelativeView,
  TokenPair,
} from "./types";

const ACCESS_TOKEN_KEY = "wmax_relative_token";
const REFRESH_TOKEN_KEY = "wmax_relative_refresh";
const PATIENTS_KEY = "wmax_relative_patients";
const DEMO_KEY = "wmax_relative_is_demo";

export function getStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function isRelativeDemoSession(): boolean {
  if (!import.meta.env.DEV) return false;
  return localStorage.getItem(DEMO_KEY) === "true";
}

export function setRelativeDemoSession(active: boolean): void {
  if (active && import.meta.env.DEV) {
    localStorage.setItem(DEMO_KEY, "true");
  } else {
    localStorage.removeItem(DEMO_KEY);
  }
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
  localStorage.removeItem(DEMO_KEY);
}

/**
 * Production Relative Login: Strictly authenticates with /api/v1/auth/relative/login.
 * Never falls back to mock data!
 */
export async function loginRelative(phone: string, pin: string): Promise<RelativeLoginResponse> {
  const res = await fetch("/api/v1/auth/relative/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, pin }),
  });

  if (!res.ok) {
    let errorDetail = "PIN-kod yoki telefon raqami noto'g'ri";
    try {
      const errJson = await res.json();
      if (errJson?.detail) errorDetail = errJson.detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(errorDetail);
  }

  const data: RelativeLoginResponse = await res.json();
  setRelativeDemoSession(false);
  saveTokens(data, data.patients);
  return data;
}

/**
 * Isolated Demo Session Generator: Only used when explicitly testing/demonstrating in DEV mode.
 */
export async function startDemoRelativeSession(): Promise<RelativeLoginResponse> {
  if (import.meta.env.DEV) {
    const { MOCK_RELATIVE_PATIENTS } = await import("./mock");
    const demoResponse: RelativeLoginResponse = {
      access_token: "demo_relative_token_test",
      refresh_token: "demo_refresh_token_112233",
      expires_in: 3600,
      role: "relative",
      full_name: "Farzand (Qarovchi)",
      patients: MOCK_RELATIVE_PATIENTS,
    };

    setRelativeDemoSession(true);
    saveTokens(demoResponse, demoResponse.patients);
    return demoResponse;
  }
  throw new Error("Demo rejimi faqat test va development muhitida mavjud");
}

/**
 * Fetch patient status view for caregivers in demo mode.
 */
export async function getDemoRelativeView(
  token?: string,
  demoState?: AlertLevel
): Promise<RelativeView> {
  if (import.meta.env.DEV) {
    const {
      MOCK_RELATIVE_VIEW_PRO,
      MOCK_RELATIVE_VIEW_STABLE,
      MOCK_RELATIVE_VIEW_NODATA,
    } = await import("./mock");

    if (demoState === "green") return MOCK_RELATIVE_VIEW_STABLE;
    if (demoState === "no_data") return MOCK_RELATIVE_VIEW_NODATA;
    if (demoState === "red") {
      return {
        ...MOCK_RELATIVE_VIEW_PRO,
        level: "red",
        level_word_key: "state.risk",
        composite_score: 4.6,
        prognosis: {
          ...MOCK_RELATIVE_VIEW_PRO.prognosis,
          risk_level: "high",
          risk_probability_pct: 88,
          summary: "SpO2 88% gacha pasaygan, taxikardiya 114 bpm. Zudlik bilan shifokor ko'rigi talab etiladi!",
        },
      };
    }
    if (demoState === "amber") return MOCK_RELATIVE_VIEW_PRO;

    if (token === "token_salomat_456") {
      return MOCK_RELATIVE_VIEW_STABLE;
    }
    return MOCK_RELATIVE_VIEW_PRO;
  }
  throw new Error("Demo rejimi faqat test va development muhitida mavjud");
}

/**
 * Fetch patient status view for caregivers.
 * In Production: Strictly queries /api/v1/relatives/{token}/view with Bearer authorization and throws on error.
 * In Demo: Generates isolated mock telemetry with optional state override for presentations.
 */
export async function fetchRelativeView(
  token: string,
  forceDemo?: boolean,
  demoState?: AlertLevel
): Promise<RelativeView> {
  if (import.meta.env.DEV && (forceDemo ?? isRelativeDemoSession())) {
    return await getDemoRelativeView(token, demoState);
  }

  const authToken = getStoredToken();
  if (!authToken) {
    clearTokens();
    throw new Error("UNAUTHORIZED");
  }

  const res = await fetch(`/api/v1/relatives/${encodeURIComponent(token)}/view`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  });

  if (res.status === 401) {
    clearTokens();
    throw new Error("UNAUTHORIZED");
  }

  if (!res.ok) {
    let msg = `Server xatoligi: ${res.status} ${res.statusText}`;
    try {
      const err = await res.json();
      if (err?.detail) msg = err.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }

  return await res.json();
}

/**
 * Patient Login: Authenticates patient with phone + PIN.
 */
export async function loginPatient(phone: string, pin: string): Promise<TokenPair> {
  const res = await fetch("/api/v1/auth/patient/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, pin }),
  });

  if (!res.ok) {
    let errorDetail = "PIN-kod yoki telefon raqami noto'g'ri";
    try {
      const errJson = await res.json();
      if (errJson?.detail) errorDetail = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  const data: TokenPair = await res.json();
  setRelativeDemoSession(false);
  saveTokens(data);
  return data;
}

/**
 * Record weight measurement (G7 fluid indicator).
 */
export async function recordPatientMeasurement(
  patientId: string,
  weightKg: number,
  systolicBp?: number,
  diastolicBp?: number
): Promise<void> {
  const authToken = getStoredToken();
  const res = await fetch(`/api/v1/patients/${encodeURIComponent(patientId)}/measurements`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: JSON.stringify({
      measured_at: new Date().toISOString(),
      weight_kg: weightKg,
      systolic_bp: systolicBp,
      diastolic_bp: diastolicBp,
      source: "relative",
    }),
  });

  if (!res.ok) {
    throw new Error(`Vazn saqlashda xatolik: ${res.status}`);
  }
}

/**
 * Update patient emergency landmark and address note.
 */
export async function updatePatientAddress(
  patientId: string,
  addressId: string,
  data: {
    landmark?: string;
    entrance_note?: string;
    street?: string;
    house?: string;
    flat?: string;
  }
): Promise<void> {
  const authToken = getStoredToken();
  const res = await fetch(`/api/v1/patients/${encodeURIComponent(patientId)}/addresses/${encodeURIComponent(addressId)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Manzilni yangilashda xatolik: ${res.status}`);
  }
}

/**
 * Patient / Relative Emergency SOS signal trigger.
 */
export async function triggerEmergencySos(patientId: string): Promise<void> {
  const authToken = getStoredToken();
  const res = await fetch("/api/v1/sos", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: JSON.stringify({
      patient_id: patientId,
      source: "relative_portal",
    }),
  });

  if (!res.ok) {
    throw new Error(`SOS yuborishda xatolik: ${res.status}`);
  }
}
