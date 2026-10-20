import type {
  DeviceEnrollResponse,
  DeviceItem,
  DeviceTier,
  NurseHandoverSBAR,
  PatientDetail,
  PatientFullProfile,
  PatientSummary,
  SosEventItem,
  Task,
  TaskStatus,
  TokenPair,
} from "./types";

const TOKEN_KEY = "wmax_doctor_jwt";
const USER_KEY = "wmax_doctor_user";
const DEMO_KEY = "wmax_doctor_is_demo";
const REFRESH_TOKEN_KEY = "wmax_doctor_refresh_jwt";

async function loadDoctorMocks() {
  return import("./clinic-mock");
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): TokenPair | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function isDemoSession(): boolean {
  return localStorage.getItem(DEMO_KEY) === "true";
}

export function setDemoSession(active: boolean): void {
  if (active) {
    localStorage.setItem(DEMO_KEY, "true");
  } else {
    localStorage.removeItem(DEMO_KEY);
  }
}

export function saveTokens(tokens: TokenPair): void {
  localStorage.setItem(TOKEN_KEY, tokens.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(tokens));
  if (tokens.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(DEMO_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Several pollers can hit 401 at once; the backend rotates refresh tokens, so
// only one refresh may be in flight or the later ones present a revoked token.
let refreshInFlight: Promise<string | null> | null = null;

function attemptRefresh(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = doRefresh().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

async function doRefresh(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh || refresh.startsWith("demo_")) return null;
  try {
    const res = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return null;
    const data: TokenPair = await res.json();
    saveTokens(data);
    return data.access_token;
  } catch {
    return null;
  }
}

/**
 * Authenticated fetch with automatic single retry on 401 using refresh token.
 */
async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const authHeader: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
  const baseHeaders = (options.headers as Record<string, string>) || {};
  const mergedHeaders: Record<string, string> = { ...baseHeaders, ...authHeader };

  let res = await fetch(url, { ...options, headers: mergedHeaders });

  if (res.status === 401) {
    const newToken = await attemptRefresh();
    if (newToken) {
      const retryHeaders = { ...mergedHeaders, Authorization: `Bearer ${newToken}` };
      res = await fetch(url, { ...options, headers: retryHeaders });
    }
    if (res.status === 401) {
      clearTokens();
      throw new Error("UNAUTHORIZED");
    }
  }

  return res;
}

/**
 * Production Login: Sends credentials strictly to the backend API.
 * Never falls back to mock data!
 */
export async function loginDoctor(phone: string, pass: string): Promise<TokenPair> {
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, password: pass }),
  });

  if (!res.ok) {
    let errorDetail = "Telefon yoki parol noto'g'ri";
    try {
      const errJson = await res.json();
      if (errJson?.detail) errorDetail = errJson.detail;
    } catch {
      // ignore parse error
    }
    throw new Error(errorDetail);
  }

  const data: TokenPair = await res.json();
  setDemoSession(false);
  saveTokens(data);
  return data;
}

/**
 * Isolated Demo Session Generator: only used after the user explicitly enters demo mode.
 * It never calls production APIs or mixes demo data with real patient data.
 */
export function startDemoDoctorSession(role: "doctor" | "nurse" = "doctor"): TokenPair {
  const demoPair: TokenPair =
    role === "nurse"
      ? {
          access_token: "demo_nurse_token_jwt",
          refresh_token: "demo_refresh_token",
          expires_in: 3600,
          role: "nurse",
          full_name: "Hamshira Dilnoza Otajonova",
        }
      : {
          access_token: "demo_doctor_token_jwt",
          refresh_token: "demo_refresh_token",
          expires_in: 3600,
          role: "doctor",
          full_name: "Dr. Bahrom Alimov",
        };

  setDemoSession(true);
  saveTokens(demoPair);
  return demoPair;
}

/**
 * Fetch patient worklist.
 * In Production: Strictly queries /api/v1/patients and throws on failure.
 * In Demo: Serves mock patients via dynamic import.
 */
export async function fetchPatients(forceDemo?: boolean): Promise<PatientSummary[]> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { MOCK_PATIENTS } = await loadDoctorMocks();
    return [...MOCK_PATIENTS];
  }

  const res = await apiFetch("/api/v1/patients");

  if (!res.ok) {
    throw new Error(`Server xatoligi: ${res.status} ${res.statusText}`);
  }

  return await res.json();
}

/**
 * Fetch full patient detail.
 * In Production: Strictly queries /api/v1/patients/{id}?days=7 and throws on failure.
 * In Demo: Serves isolated mock patient detail via dynamic import.
 */
export async function fetchPatientDetail(id: string, forceDemo?: boolean): Promise<PatientDetail> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { getMockPatientDetail } = await loadDoctorMocks();
    return getMockPatientDetail(id);
  }

  const res = await apiFetch(`/api/v1/patients/${encodeURIComponent(id)}?days=7`);

  if (!res.ok) {
    throw new Error(`Server xatoligi: ${res.status} ${res.statusText}`);
  }

  return await res.json();
}

/**
 * Confirm active patrol task.
 */
export async function confirmTask(taskId: number, note: string, forceDemo?: boolean): Promise<void> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    return;
  }

  const res = await apiFetch(`/api/v1/tasks/${taskId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });

  if (!res.ok) {
    throw new Error(`Vazifani tasdiqlashda xatolik: ${res.status}`);
  }
}

/**
 * Approve physiological baseline corridor.
 */
export async function approveBaseline(patientId: string, forceDemo?: boolean): Promise<void> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    return;
  }

  const res = await apiFetch(`/api/v1/patients/${encodeURIComponent(patientId)}/baseline/approve`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error(`Bazaviy koridorni tasdiqlashda xatolik: ${res.status}`);
  }
}

/**
 * Discharge patient from in-hospital care and schedule 24h active patrol order.
 */
export async function dischargePatient(patientId: string, forceDemo?: boolean): Promise<void> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    return;
  }

  const res = await apiFetch(`/api/v1/patients/${encodeURIComponent(patientId)}/discharge`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error(`Statsionardan chiqarishda xatolik: ${res.status}`);
  }
}

/**
 * Fetch active SOS emergency events.
 * Errors are thrown, never replaced by sample events: a dispatcher must be
 * able to tell "no emergencies" from "cannot reach the server".
 */
export async function fetchActiveSos(forceDemo?: boolean): Promise<SosEventItem[]> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { getMockActiveSos } = await loadDoctorMocks();
    return getMockActiveSos();
  }

  const res = await apiFetch("/api/v1/sos/active");
  if (!res.ok) {
    throw new Error(`SOS ro'yxatini yuklashda xatolik: ${res.status}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

/**
 * Acknowledge an active SOS signal.
 */
export async function acknowledgeSos(sosId: string, forceDemo?: boolean): Promise<SosEventItem> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { mockAcknowledgeSos } = await loadDoctorMocks();
    return mockAcknowledgeSos(sosId);
  }

  const res = await apiFetch(`/api/v1/sos/${encodeURIComponent(sosId)}/acknowledge`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error(`SOS qabul qilishda xatolik: ${res.status}`);
  }

  return await res.json();
}

/**
 * Dispatch emergency ambulance (103) for SOS.
 */
export async function dispatchSos103(
  sosId: string,
  payload?: { dispatch_method?: string; dispatch_ref?: string | null },
  forceDemo?: boolean,
): Promise<SosEventItem> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { mockDispatchSos103 } = await loadDoctorMocks();
    return mockDispatchSos103(sosId, payload?.dispatch_ref || undefined);
  }

  const res = await apiFetch(`/api/v1/sos/${encodeURIComponent(sosId)}/dispatch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || { dispatch_method: "manual_call_103" }),
  });

  if (!res.ok) {
    throw new Error(`103 ga jo'natishda xatolik: ${res.status}`);
  }

  return await res.json();
}

/**
 * Resolve an active SOS incident with a resolution note.
 */
export async function resolveSos(sosId: string, note: string, forceDemo?: boolean): Promise<SosEventItem> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { mockResolveSos } = await loadDoctorMocks();
    return mockResolveSos(sosId, note);
  }

  const res = await apiFetch(`/api/v1/sos/${encodeURIComponent(sosId)}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resolution_note: note }),
  });

  if (!res.ok) {
    throw new Error(`SOS yakunlashda xatolik: ${res.status}`);
  }

  return await res.json();
}

/**
 * Fetch patient's complete clinical domain profile V2 (addresses, meds, allergies, weight trend, admissions).
 */
export async function fetchPatientFullProfile(patientId: string, forceDemo?: boolean): Promise<PatientFullProfile> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    const { getMockPatientDetail } = await loadDoctorMocks();
    const detail = getMockPatientDetail(patientId);
    return {
      patient: detail,
      addresses: [
        {
          id: "addr-1",
          patient_id: patientId,
          kind: "home",
          region: "Xorazm",
          district: detail.district,
          street: "Al-Xorazmiy ko'chasi 45",
          landmark: "GUM savdo markazi yonida",
          entrance_note: "2-kirish, domofon 14",
          is_primary: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      conditions: [
        {
          id: "cond-1",
          patient_id: patientId,
          icd10: "I25.1",
          name_uz: detail.diagnosis,
          kind: "primary",
          is_active: true,
          created_at: new Date().toISOString(),
        },
      ],
      medications: [
        {
          id: "med-1",
          patient_id: patientId,
          name: "Bisoprolol",
          dose: "5 mg",
          frequency: "kuniga 1 mahal (ertalab)",
          affects_params: { hr: "lowers" },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "med-2",
          patient_id: patientId,
          name: "Ramipril",
          dose: "2.5 mg",
          frequency: "kuniga 1 mahal (kechqurun)",
          affects_params: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      allergies: [
        {
          id: "all-1",
          patient_id: patientId,
          substance: "Penitsillin",
          reaction: "Teri toshmasi va qichishish",
          severity: "moderate",
          created_at: new Date().toISOString(),
        },
      ],
      measurements: [
        {
          id: "meas-1",
          patient_id: patientId,
          measured_at: new Date().toISOString(),
          weight_kg: 74.5,
          systolic_bp: 125,
          diastolic_bp: 82,
          source: "relative",
          created_at: new Date().toISOString(),
        },
      ],
      risk_factors: {
        patient_id: patientId,
        smoking: "former",
        alcohol: "none",
        diabetes: true,
        ckd: false,
        mobility: "independent",
        lives_alone: false,
      },
      admissions: [],
    };
  }

  const res = await apiFetch(`/api/v1/patients/${encodeURIComponent(patientId)}/profile`);

  if (!res.ok) {
    throw new Error(`Profil ma'lumotlarini yuklashda xatolik: ${res.status}`);
  }

  return await res.json();
}

/**
 * Fetch AI-powered nurse SBAR handover note and shift patrol checklist.
 */
export async function fetchNurseHandover(
  patientId: string,
  forceDemo?: boolean,
): Promise<NurseHandoverSBAR | null> {
  const activeDemo = forceDemo ?? isDemoSession();
  if (activeDemo) {
    // DEV fallback — generate a deterministic stub so nurses see the panel
    const { getMockPatientDetail } = await loadDoctorMocks();
    const p = getMockPatientDetail(patientId);
    const urgency =
      p.level === "red" ? "critical" : p.level === "amber" ? "urgent" : "routine";
    return {
      situation: `Bemor ${p.full_name} (${p.age} yosh) — joriy triaj holati: ${p.level.toUpperCase()}.`,
      background: `Tashxis: ${p.diagnosis}. Kuzatuv bosqichi: ${p.phase}.`,
      assessment: `Kompozit og'ish ko'rsatkichi: ${p.composite_score}. Chetlangan parametrlar: ${Object.keys(p.triggered_params || {}).join(", ") || "yoʻq"}.`,
      recommendation:
        "Tonik qon bosimini o'lchash va bemorat holi bilan telefon orqali so'rashuv. Dori jadvalini tasdiqlash.",
      shift_checklist: [
        { id: "demo-1", task: "Qon bosimi va pulsni tonometr bilan o'lchash", priority: "high", category: "vitals", completed: false },
        { id: "demo-2", task: "Tayinlangan dorilar qabul qilinganligini tekshirish", priority: "high", category: "medication", completed: false },
        { id: "demo-3", task: "Aqlli soat taqilganligi va quvvati tekshirish", priority: "medium", category: "device", completed: false },
        { id: "demo-4", task: "Bemorning holati va shikoyatlari haqida so'rashuv", priority: "medium", category: "observation", completed: false },
      ],
      clinical_urgency: urgency,
      vital_flags: p.level === "red" ? ["HR yuqori", "SpO2 past"] : [],
      confidence_score: 0.92,
      evidence_citations: [`Level: ${p.level}`, `Score: ${p.composite_score}`],
      generated_at: new Date().toISOString(),
    };
  }

  const res = await apiFetch(`/api/v1/patients/${encodeURIComponent(patientId)}/nurse-handover`);
  // A missing AI note is not fatal for the panel; auth failures still throw.
  if (!res.ok) return null;
  return await res.json();
}

/** Pull FastAPI's `detail` (string or validation list) out of an error response. */
async function errorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) return String(body.detail[0].msg);
    if (typeof body?.message === "string") return body.message;
  } catch {
    // non-JSON body
  }
  return `${fallback}: ${res.status}`;
}

// =====================================================================
// Tasks (active-call patrol, red-alert follow-up) — /api/v1/tasks
// =====================================================================

let demoTasks: Task[] | null = null;

async function getDemoTasks(): Promise<Task[]> {
  if (!demoTasks) {
    const { MOCK_PATIENTS } = await loadDoctorMocks();
    demoTasks = MOCK_PATIENTS.flatMap((p) => (p.open_task ? [{ ...p.open_task }] : []));
  }
  return demoTasks;
}

export async function fetchTasks(status?: TaskStatus, forceDemo?: boolean): Promise<Task[]> {
  if (forceDemo ?? isDemoSession()) {
    const tasks = await getDemoTasks();
    return tasks.filter((t) => !status || t.status === status).map((t) => ({ ...t }));
  }
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await apiFetch(`/api/v1/tasks${query}`);
  if (!res.ok) throw new Error(await errorDetail(res, "Vazifalarni yuklashda xatolik"));
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function acknowledgeTask(taskId: number, forceDemo?: boolean): Promise<Task | null> {
  if (forceDemo ?? isDemoSession()) {
    const tasks = await getDemoTasks();
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      task.status = "seen";
      task.acknowledged_at = new Date().toISOString();
    }
    return task ? { ...task } : null;
  }
  const res = await apiFetch(`/api/v1/tasks/${taskId}/acknowledge`, { method: "POST" });
  if (!res.ok) throw new Error(await errorDetail(res, "Vazifani qabul qilishda xatolik"));
  return await res.json();
}

export async function completeTask(taskId: number, note: string, forceDemo?: boolean): Promise<Task | null> {
  if (forceDemo ?? isDemoSession()) {
    const tasks = await getDemoTasks();
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      task.status = "done";
      task.confirmed_at = new Date().toISOString();
      task.note = note;
    }
    return task ? { ...task } : null;
  }
  const res = await apiFetch(`/api/v1/tasks/${taskId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Vazifani yakunlashda xatolik"));
  return await res.json();
}

// =====================================================================
// Device inventory — /api/v1/devices
// =====================================================================

let demoDevices: DeviceItem[] | null = null;

function getDemoDevices(): DeviceItem[] {
  if (!demoDevices) {
    const ago = (h: number) => new Date(Date.now() - h * 3600 * 1000).toISOString();
    demoDevices = [
      { id: "d1", serial_number: "SM-R910-8841", model_name: "Galaxy Watch 5 · 44mm", tier: "tier1_wearos", status: "assigned", ownership: "owned", battery_health_pct: 94, last_sync_at: ago(0.2), patient_name: "Otabek Rahimov" },
      { id: "d2", serial_number: "SM-R910-8842", model_name: "Galaxy Watch 5 · 40mm", tier: "tier1_wearos", status: "in_stock", ownership: "owned", battery_health_pct: 98, last_sync_at: null },
      { id: "d3", serial_number: "XW-M2-1029", model_name: "Xiaomi Watch 2", tier: "tier2_wearos_budget", status: "in_stock", ownership: "owned", battery_health_pct: 100, last_sync_at: null },
      { id: "d4", serial_number: "BLE-BAND-041", model_name: "Medical PPG Band", tier: "tier3_ble_band", status: "assigned", ownership: "leased", battery_health_pct: 91, last_sync_at: ago(1.5), patient_name: "Gulnora Matyoqubova" },
      { id: "d5", serial_number: "SM-R900-5120", model_name: "Galaxy Watch 4 Classic", tier: "tier1_wearos", status: "maintenance", ownership: "owned", battery_health_pct: 79, last_sync_at: ago(20) },
    ];
  }
  return demoDevices;
}

export async function fetchDevices(forceDemo?: boolean): Promise<DeviceItem[]> {
  if (forceDemo ?? isDemoSession()) return getDemoDevices().map((d) => ({ ...d }));
  const res = await apiFetch("/api/v1/devices");
  if (!res.ok) throw new Error(await errorDetail(res, "Qurilmalarni yuklashda xatolik"));
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function registerDevice(
  payload: { serial_number: string; model_name: string; tier: DeviceTier; ownership: string; battery_health_pct: number },
  forceDemo?: boolean,
): Promise<void> {
  if (forceDemo ?? isDemoSession()) {
    getDemoDevices().unshift({ id: `d${Date.now()}`, status: "in_stock", last_sync_at: null, ...payload });
    return;
  }
  const res = await apiFetch("/api/v1/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Qurilmani ro'yxatga olishda xatolik"));
}

export async function assignDevice(
  deviceId: string,
  payload: { patient_id: string; deposit_uzs: number; rental_uzs_month: number; patient_name?: string },
  forceDemo?: boolean,
): Promise<void> {
  if (forceDemo ?? isDemoSession()) {
    const device = getDemoDevices().find((d) => d.id === deviceId);
    if (device) {
      device.status = "assigned";
      device.patient_name = payload.patient_name;
    }
    return;
  }
  const res = await apiFetch(`/api/v1/devices/${encodeURIComponent(deviceId)}/assign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: payload.patient_id,
      deposit_uzs: payload.deposit_uzs,
      rental_uzs_month: payload.rental_uzs_month,
    }),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Qurilmani biriktirishda xatolik"));
}

export async function returnDevice(
  deviceId: string,
  payload: { battery_health_pct: number | null; return_notes: string | null; refund_deposit: boolean },
  forceDemo?: boolean,
): Promise<void> {
  if (forceDemo ?? isDemoSession()) {
    const device = getDemoDevices().find((d) => d.id === deviceId);
    if (device) {
      const battery = payload.battery_health_pct ?? device.battery_health_pct ?? 100;
      device.battery_health_pct = battery;
      device.status = battery < 80 ? "retired" : "in_stock";
      device.patient_name = undefined;
    }
    return;
  }
  const res = await apiFetch(`/api/v1/devices/${encodeURIComponent(deviceId)}/return`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Qurilmani qaytarishda xatolik"));
}

export async function createDeviceEnrollment(deviceId: string, forceDemo?: boolean): Promise<DeviceEnrollResponse> {
  if (forceDemo ?? isDemoSession()) {
    return {
      device_id: deviceId,
      enrollment_id: "demo-enrollment",
      code: String(Math.floor(100000 + Math.random() * 900000)),
      expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
    };
  }
  const res = await apiFetch("/api/v1/devices/enroll", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: deviceId, ttl_minutes: 10 }),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Ulanish kodini yaratishda xatolik"));
  return await res.json();
}
