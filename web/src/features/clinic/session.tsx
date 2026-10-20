import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  clearTokens,
  fetchActiveSos,
  fetchPatients,
  getStoredToken,
  getStoredUser,
  isDemoSession,
  loginDoctor,
  setDemoSession,
  startDemoDoctorSession,
} from "@/lib/clinic-api";
import type { PatientSummary, SosEventItem, TokenPair } from "@/lib/types";

// ---------------------------------------------------------------------------
// Session: who is signed in to the clinic workstation (doctor / nurse / admin).
// ---------------------------------------------------------------------------

interface ClinicSession {
  user: TokenPair | null;
  isDemo: boolean;
  login: (phone: string, password: string) => Promise<TokenPair>;
  launchDemo: (role?: "doctor" | "nurse") => TokenPair;
  logout: () => void;
}

const SessionContext = createContext<ClinicSession | null>(null);

function initialUser(): { user: TokenPair | null; isDemo: boolean } {
  // A shared "/doctor?demo=true" link opens the synthetic demo workstation directly.
  const wantsDemo = new URLSearchParams(window.location.search).get("demo") === "true" && !getStoredToken();
  if (wantsDemo) return { user: startDemoDoctorSession("doctor"), isDemo: true };
  return { user: getStoredToken() ? getStoredUser() : null, isDemo: isDemoSession() };
}

export const ClinicSessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState(initialUser);

  const login = useCallback(async (phone: string, password: string) => {
    const pair = await loginDoctor(phone, password);
    setState({ user: pair, isDemo: false });
    return pair;
  }, []);

  const launchDemo = useCallback((role: "doctor" | "nurse" = "doctor") => {
    const pair = startDemoDoctorSession(role);
    setState({ user: pair, isDemo: true });
    return pair;
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setDemoSession(false);
    setState({ user: null, isDemo: false });
  }, []);

  const value = useMemo(() => ({ ...state, login, launchDemo, logout }), [state, login, launchDemo, logout]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
};

// oxlint-disable-next-line react/only-export-components -- hook lives beside its provider
export function useClinicSession(): ClinicSession {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useClinicSession must be used inside ClinicSessionProvider");
  return ctx;
}

// ---------------------------------------------------------------------------
// Live data shared by every clinic screen: worklist, SOS queue, realtime ticks.
// ---------------------------------------------------------------------------

interface ClinicData {
  patients: PatientSummary[];
  patientsLoaded: boolean;
  patientsError: string | null;
  reloadPatients: (silent?: boolean) => Promise<void>;
  /** Unresolved SOS events (raised / acknowledged / dispatched_103). */
  activeSos: SosEventItem[];
  /** True when the last SOS poll failed: the queue on screen may be stale. */
  sosStale: boolean;
  reloadSos: () => Promise<void>;
  /** Increments on every realtime event so open screens can refetch. */
  revision: number;
  realtime: "live" | "polling" | "demo";
}

const DataContext = createContext<ClinicData | null>(null);

const UNRESOLVED = new Set(["raised", "acknowledged", "dispatched_103"]);

export const ClinicDataProvider: React.FC<{ children: React.ReactNode; onUnauthorized: () => void }> = ({
  children,
  onUnauthorized,
}) => {
  const { isDemo, user } = useClinicSession();
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [patientsLoaded, setPatientsLoaded] = useState(false);
  const [patientsError, setPatientsError] = useState<string | null>(null);
  const [activeSos, setActiveSos] = useState<SosEventItem[]>([]);
  const [sosStale, setSosStale] = useState(false);
  const [revision, setRevision] = useState(0);
  const [realtime, setRealtime] = useState<ClinicData["realtime"]>(isDemo ? "demo" : "polling");
  const unauthorizedRef = useRef(onUnauthorized);
  useEffect(() => {
    unauthorizedRef.current = onUnauthorized;
  }, [onUnauthorized]);

  const handleError = useCallback((err: unknown): string | null => {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg === "UNAUTHORIZED") {
      unauthorizedRef.current();
      return null;
    }
    return msg;
  }, []);

  const reloadPatients = useCallback(
    async (silent = false) => {
      if (!silent) setPatientsError(null);
      try {
        const data = await fetchPatients(isDemo);
        setPatients(data);
        setPatientsError(null);
      } catch (err) {
        const msg = handleError(err);
        if (msg !== null) setPatientsError(msg);
      } finally {
        setPatientsLoaded(true);
      }
    },
    [isDemo, handleError],
  );

  const reloadSos = useCallback(async () => {
    try {
      const events = await fetchActiveSos(isDemo);
      setActiveSos(events.filter((e) => UNRESOLVED.has(e.status)));
      setSosStale(false);
    } catch (err) {
      // Keep the last known queue and say it may be stale; never show "no emergencies" on failure.
      if (handleError(err) !== null) setSosStale(true);
    }
  }, [isDemo, handleError]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- worklist hydrates from the API on sign-in
    void reloadPatients();
  }, [reloadPatients, user?.access_token]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- SOS queue is polled independently of realtime
    void reloadSos();
    const id = window.setInterval(reloadSos, 8000);
    return () => window.clearInterval(id);
  }, [reloadSos]);

  // Realtime push with exponential reconnect; polling fallback while the socket is down.
  useEffect(() => {
    if (isDemo || !user) return;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let reconnectDelay = 1000;
    let disposed = false;

    const bump = () => {
      setRevision((r) => r + 1);
      void reloadPatients(true);
    };

    const connect = () => {
      if (disposed) return;
      const token = getStoredToken() ?? user.access_token;
      const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
      try {
        socket = new WebSocket(`${scheme}//${window.location.host}/api/v1/realtime/ws?topic=*`, ["wmax", `bearer.${token}`]);
      } catch {
        setRealtime("polling");
        return;
      }
      socket.onopen = () => {
        reconnectDelay = 1000;
        setRealtime("live");
        bump();
      };
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as { topic?: string };
          const topic = event.topic ?? "";
          if (topic === "reading.accepted" || topic === "alert.created" || topic.startsWith("task.") || topic.startsWith("sos.")) {
            bump();
            if (topic.startsWith("sos.")) void reloadSos();
          }
        } catch {
          // ignore malformed frames
        }
      };
      socket.onclose = () => {
        if (disposed) return;
        setRealtime("polling");
        reconnectTimer = window.setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    const fallback = window.setInterval(() => {
      if (socket?.readyState !== WebSocket.OPEN) bump();
    }, 60000);
    return () => {
      disposed = true;
      window.clearInterval(fallback);
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [isDemo, user, reloadPatients, reloadSos]);

  const value = useMemo(
    () => ({
      patients,
      patientsLoaded,
      patientsError,
      reloadPatients,
      activeSos,
      sosStale,
      reloadSos,
      revision,
      realtime: isDemo ? ("demo" as const) : realtime,
    }),
    [patients, patientsLoaded, patientsError, reloadPatients, activeSos, sosStale, reloadSos, revision, realtime, isDemo],
  );
  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

// oxlint-disable-next-line react/only-export-components -- hook lives beside its provider
export function useClinicData(): ClinicData {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error("useClinicData must be used inside ClinicDataProvider");
  return ctx;
}
