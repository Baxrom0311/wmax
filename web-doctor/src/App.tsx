import React, { useCallback, useEffect, useState } from "react";
import { Navbar } from "./components/Navbar";
import type { NavTab } from "./components/Navbar";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import {
  clearTokens,
  fetchPatientDetail,
  fetchPatients,
  getStoredToken,
  getStoredUser,
  isDemoSession,
  loginDoctor,
  setDemoSession,
  startDemoDoctorSession,
} from "./lib/api";
import type { PatientDetail, PatientSummary, TokenPair } from "./lib/types";
import { PatientsList } from "./pages/PatientsList";
import { SosBanner } from "./components/SosBanner";

const HandoffsPage = React.lazy(() => import("./pages/HandoffsPage").then((module) => ({ default: module.HandoffsPage })));
const DeviceInventoryModal = React.lazy(() => import("./components/DeviceInventoryModal").then((module) => ({ default: module.DeviceInventoryModal })));
const PatientDetailPage = React.lazy(() => import("./pages/PatientDetail").then((module) => ({ default: module.PatientDetailPage })));
const SosDispatcher = React.lazy(() => import("./pages/SosDispatcher").then((module) => ({ default: module.SosDispatcher })));

export const App: React.FC = () => {
  const [lang, setLang] = useState<Lang>("uz");
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [user, setUser] = useState<TokenPair | null>(getStoredUser());
  const [activeTab, setActiveTab] = useState<NavTab>("patients");
  const [isSosDispatcherOpen, setIsSosDispatcherOpen] = useState<boolean>(false);
  const [isDemo, setIsDemo] = useState<boolean>(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("demo") === "true" || isDemoSession();
  });

  // Data states
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [detailPatient, setDetailPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Login form state
  const [selectedRole, setSelectedRole] = useState<"doctor" | "nurse">("doctor");
  const [phone, setPhone] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  const handleLogout = useCallback(() => {
    clearTokens();
    setDemoSession(false);
    setIsDemo(false);
    setToken(null);
    setUser(null);
    setSelectedPatientId(null);
    setDetailPatient(null);
    setPatients([]);
    setFetchError(null);
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadPatients = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setFetchError(null);
    try {
      const data = await fetchPatients(isDemo);
      setPatients(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg === "UNAUTHORIZED") {
        handleLogout();
        return;
      }
      setFetchError(t("error.server_connection", lang));
    } finally {
      if (!silent) setLoading(false);
    }
  }, [handleLogout, isDemo, lang]);

  const loadDetail = useCallback(async (id: string, silent = false) => {
    if (!silent) setLoading(true);
    setFetchError(null);
    try {
      const data = await fetchPatientDetail(id, isDemo);
      setDetailPatient(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg === "UNAUTHORIZED") {
        handleLogout();
        return;
      }
      setFetchError(t("error.server_connection", lang));
    } finally {
      if (!silent) setLoading(false);
    }
  }, [handleLogout, isDemo, lang]);

  // Initial load
  useEffect(() => {
    if (token) {
      // oxlint-disable-next-line react/set-state-in-effect -- authenticated data hydration belongs to this effect
      loadPatients();
    }
  }, [token, loadPatients]);

  // Periodic 15s auto-refresh polling (matches clinical workstation telemetry interval)
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(() => {
      if (selectedPatientId) {
        loadDetail(selectedPatientId, true);
      } else {
        loadPatients(true);
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [token, selectedPatientId, loadDetail, loadPatients]);


  useEffect(() => {
    if (selectedPatientId) {
      // oxlint-disable-next-line react/set-state-in-effect -- selection drives remote detail hydration
      loadDetail(selectedPatientId);
    }
  }, [selectedPatientId, loadDetail]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoggingIn(true);
    try {
      const pair = await loginDoctor(phone, password);
      setIsDemo(false);
      setToken(pair.access_token);
      setUser(pair);
      setFetchError(null);
      showToast(t("toast.login_success", lang));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t("login.error", lang);
      setLoginError(msg);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLaunchDemo = (role: "doctor" | "nurse" = "doctor") => {
    const demoPair = startDemoDoctorSession(role);
    setIsDemo(true);
    setToken(demoPair.access_token);
    setUser(demoPair);
    setFetchError(null);
    showToast(t("demo.banner_title", lang) + ": " + demoPair.full_name);
  };




  return (
    <>
      {/* Demo banner removed — no yellow banner shown */}

      {token && (
        <Navbar
          lang={lang}
          onLangChange={setLang}
          doctorName={user?.full_name || "WMAX klinik xodimi"}
          role={user?.role || "doctor"}
          onLogout={handleLogout}
          activeTab={activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            setSelectedPatientId(null);
          }}
        />
      )}

      {token && (
        <SosBanner
          onOpenDispatcher={() => setIsSosDispatcherOpen(true)}
          isDemo={isDemo}
        />
      )}

      {toastMessage && (
        <div className="doc-toast-notification">
          <span className="toast-icon">✓</span>
          <span>{toastMessage}</span>
        </div>
      )}

      <React.Suspense fallback={<div className="route-loading">{t("app.loading", lang)}</div>}>
      {isSosDispatcherOpen || activeTab === "sos" ? (
        <SosDispatcher
          onClose={() => {
            setIsSosDispatcherOpen(false);
            setActiveTab("patients");
          }}
          isDemo={isDemo}
        />
      ) : !token ? (
        <div className="doctor-login-wrapper">
          <div className="doctor-login-box">
            <div className="login-box-toolbar">
              <div className="login-brand" aria-label="WMAX">
                <span className="auth-shell-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.4">
                    <polyline points="2 12 6 12 9 4 14 20 17 12 22 12" />
                  </svg>
                </span>
                <span>WMAX</span>
              </div>
              <div className="official-lang-toggle" aria-label={t("app.language", lang)}>
                {(["uz", "ru", "en"] as const).map((item) => (
                  <button key={item} type="button" className={`lang-opt ${lang === item ? "active" : ""}`} onClick={() => setLang(item)}>
                    {item.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            <div className="login-portal-title">
              <div className="portal-emblem">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z" />
                  <line x1="12" y1="8" x2="12" y2="16" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
              </div>
              <div>
                <h2>{t("login.title", lang)}</h2>
                <p>{t("login.desc", lang)}</p>
              </div>
            </div>

            {/* Role Selector */}
            <div className="official-role-segmented">
              <button
                type="button"
                className={`role-tab ${selectedRole === "doctor" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("doctor");
                  setPhone("");
                  setPassword("");
                }}
              >
                <span className="role-tab-name">{t("login.role_doctor", lang)}</span>
              </button>
              <button
                type="button"
                className={`role-tab ${selectedRole === "nurse" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("nurse");
                  setPhone("");
                  setPassword("");
                }}
              >
                <span className="role-tab-name">{t("login.role_nurse", lang)}</span>
              </button>
            </div>

            {loginError && (
              <div className="login-error-alert">
                <span>{loginError}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="login-form-official">
              <div className="form-field">
                <label htmlFor="doctor-phone-input" className="form-label-official">
                  {t("login.phone_label", lang)}
                </label>
                <input
                  id="doctor-phone-input"
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="form-input-official"
                  placeholder="+998901234567"
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="doctor-password-input" className="form-label-official">
                  {t("login.password_label", lang)}
                </label>
                <input
                  id="doctor-password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input-official"
                  placeholder="••••••••"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn-official-submit"
                disabled={loggingIn}
              >
                {loggingIn ? t("login.loading", lang) : t("login.submit", lang)}
              </button>

              <div className="login-demo-divider">
                <span className="divider-line" />
                <span className="divider-label">{t("common.or", lang)}</span>
                <span className="divider-line" />
              </div>

              <button
                type="button"
                className="btn-launch-demo-isolated"
                onClick={() => handleLaunchDemo(selectedRole)}
              >
                <span>{t("demo.enter_demo", lang)}</span>
              </button>
            </form>
          </div>
        </div>
      ) : fetchError && patients.length === 0 && !detailPatient ? (
        <div className="doc-fetch-error-card">
          <div className="error-icon-circle">⚠️</div>
          <h3>{fetchError}</h3>
          <div className="error-actions-row">
            <button
              type="button"
              className="btn-error-retry"
              onClick={() => (selectedPatientId ? loadDetail(selectedPatientId) : loadPatients())}
            >
              🔄 {t("error.retry", lang)}
            </button>
            <button
              type="button"
              className="btn-error-switch-demo"
              onClick={() => handleLaunchDemo("doctor")}
            >
              🧪 {t("demo.enter_demo", lang)}
            </button>
          </div>
        </div>
      ) : loading && !detailPatient && patients.length === 0 ? (
        <div style={{ textAlign: "center", padding: "40px", color: "var(--color-muted)" }}>
          Yuklanmoqda...
        </div>
      ) : activeTab === "handoffs" ? (
        <HandoffsPage lang={lang} />
      ) : activeTab === "devices" ? (
        <DeviceInventoryModal
          isOpen
          onClose={() => setActiveTab("patients")}
          lang={lang}
        />
      ) : selectedPatientId && detailPatient ? (
        <PatientDetailPage
          patient={detailPatient}
          onBack={() => {
            setSelectedPatientId(null);
            setDetailPatient(null);
          }}
          onRefresh={() => loadDetail(selectedPatientId)}
          lang={lang}
        />
      ) : (
        <PatientsList
          patients={patients}
          onSelectPatient={(id) => {
            setDetailPatient(null);
            setSelectedPatientId(id);
          }}
          lang={lang}
        />
      )}
      </React.Suspense>
    </>
  );
};

export default App;
