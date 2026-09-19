import React, { useCallback, useEffect, useState } from "react";
import { ActionContactBar } from "./components/ActionContactBar";
import { HeroStatusPrognosis } from "./components/HeroStatusPrognosis";
import { LanguageSelector } from "./components/LanguageSelector";
import { PatientSwitcher } from "./components/PatientSwitcher";
import { ProblemBreakdown } from "./components/ProblemBreakdown";
import { PlanStatusCard } from "./components/PlanStatusCard";
import { Vitals } from "./components/Vitals";
import { V2ProfileActions } from "./components/V2ProfileActions";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import {
  clearTokens,
  fetchRelativeView,
  getDemoRelativeView,
  getStoredPatients,
  getStoredToken,
  isRelativeDemoSession,
  loginPatient,
  loginRelative,
  setRelativeDemoSession,
  startDemoRelativeSession,
} from "./lib/api";
import type { AlertLevel, RelativePatientItem, RelativeView } from "./lib/types";

const InteractiveMetrics = React.lazy(() => import("./components/InteractiveMetrics").then((module) => ({ default: module.InteractiveMetrics })));

export const App: React.FC = () => {
  const [lang, setLang] = useState<Lang>("uz");
  const [authToken, setAuthToken] = useState<string | null>(getStoredToken());
  const [viewToken, setViewToken] = useState<string | null>(null);
  const [patients, setPatients] = useState<RelativePatientItem[]>(getStoredPatients());
  const [activePatientId, setActivePatientId] = useState<string>(
    patients[0]?.id || "11111111-1111-1111-1111-111111111111"
  );
  const [viewData, setViewData] = useState<RelativeView | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [isDemo, setIsDemo] = useState<boolean>(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("demo") === "true" || isRelativeDemoSession();
  });

  // Login form state
  const [loginRole, setLoginRole] = useState<"relative" | "patient">("relative");
  const [phone, setPhone] = useState<string>("");
  const [pin, setPin] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tg] = useState(() => (window as any).Telegram?.WebApp);
  const isTMA = Boolean(tg?.initData);

  // Extract capability token from URL path if available (/r/:token) or query parameter / TMA start param
  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      try {
        tg.enableClosingConfirmation?.();
        tg.setHeaderColor?.("#ffffff");
        tg.setBackgroundColor?.("#f8fafc");
      } catch {
        /* older TMA versions */
      }
    }

    let deepLinkToken: string | null = null;
    const startParam = tg?.initDataUnsafe?.start_param;
    if (startParam) {
      deepLinkToken = startParam;
    }

    if (!deepLinkToken) {
      const searchToken = new URLSearchParams(window.location.search).get("t");
      if (searchToken) {
        deepLinkToken = searchToken;
      }
    }

    if (!deepLinkToken) {
      const pathParts = window.location.pathname.split("/").filter(Boolean);
      const rIndex = pathParts.indexOf("r");
      if (rIndex !== -1 && pathParts[rIndex + 1]) {
        deepLinkToken = pathParts[rIndex + 1];
      }
    }

    const currentAuth = getStoredToken();
    if (deepLinkToken) {
      if (currentAuth || isRelativeDemoSession()) {
        // oxlint-disable-next-line react/set-state-in-effect -- hydrate the capability selected by the URL/TMA launch context
        setViewToken(deepLinkToken);
      } else {
        sessionStorage.setItem("wmax_pending_token", deepLinkToken);
      }
    } else if (currentAuth) {
      const stored = getStoredPatients();
      if (stored.length > 0 && stored[0].access_token) {
        setViewToken(stored[0].access_token);
        setActivePatientId(stored[0].id);
      }
    }
  }, [tg]);

  const handleLogout = useCallback(() => {
    clearTokens();
    sessionStorage.removeItem("wmax_pending_token");
    setRelativeDemoSession(false);
    setIsDemo(false);
    setAuthToken(null);
    setViewToken(null);
    setPatients([]);
    setViewData(null);
    setLoadError(null);
  }, []);

  const loadData = useCallback(async (activeToken: string) => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchRelativeView(activeToken, isDemo);
      setViewData(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg === "UNAUTHORIZED") {
        handleLogout();
        return;
      }
      setLoadError(t("error.fetch_failed", lang));
      setViewData(null);
    } finally {
      setLoading(false);
    }
  }, [handleLogout, isDemo, lang]);

  useEffect(() => {
    if (authToken || isDemo) {
      if (viewToken) {
        // oxlint-disable-next-line react/set-state-in-effect -- session/token changes trigger remote view hydration
        loadData(viewToken);
      } else if (patients.length > 0 && patients[0].access_token) {
        setViewToken(patients[0].access_token);
      } else {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [authToken, viewToken, isDemo, loadData, patients]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoggingIn(true);
    try {
      if (loginRole === "patient") {
        const res = await loginPatient(phone, pin);
        setAuthToken(res.access_token);
        setIsDemo(false);
        const patView = await getDemoRelativeView("patient", "green");
        setViewData({
          ...patView,
          patient_name: res.full_name,
        });
        setLoading(false);
      } else {
        const res = await loginRelative(phone, pin);
        setAuthToken(res.access_token);
        setIsDemo(false);
        const resPatients = res.patients || [];
        setPatients(resPatients);

        const pendingToken = sessionStorage.getItem("wmax_pending_token");
        sessionStorage.removeItem("wmax_pending_token");

        let targetToken = pendingToken;
        if (pendingToken) {
          const matched = resPatients.find((p) => p.access_token === pendingToken);
          if (matched) {
            setActivePatientId(matched.id);
          } else if (resPatients.length > 0) {
            setActivePatientId(resPatients[0].id);
          }
        } else if (resPatients.length > 0) {
          targetToken = resPatients[0].access_token;
          setActivePatientId(resPatients[0].id);
        }

        if (targetToken) {
          setViewToken(targetToken);
          await loadData(targetToken);
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t("login.error", lang);
      setLoginError(message);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLaunchDemo = async () => {
    try {
      const demo = await startDemoRelativeSession();
      setIsDemo(true);
      setAuthToken(demo.access_token);
      const demoPatients = demo.patients || [];
      setPatients(demoPatients);
      if (demoPatients.length > 0) {
        setActivePatientId(demoPatients[0].id);
        setViewToken(demoPatients[0].access_token);
      }
      setLoadError(null);
      const demoData = await getDemoRelativeView();
      setViewData(demoData);
    } catch (err) {
      console.error("Failed to launch demo:", err);
    }
  };

  const handleExitDemo = () => {
    handleLogout();

    const url = new URL(window.location.href);
    url.searchParams.delete("demo");
    url.searchParams.delete("state");
    window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
  };

  const handleSelectPatient = async (p: RelativePatientItem) => {
    setActivePatientId(p.id);
    setViewToken(p.access_token);
    await loadData(p.access_token);
  };

  // Demo switchers for presentation (only available in Demo mode)
  const setDemoState = async (lvl: AlertLevel) => {
    try {
      const demoData = await getDemoRelativeView(viewToken || undefined, lvl);
      setViewData(demoData);
    } catch (err) {
      console.error("Failed to set demo state:", err);
    }
  };

  const hasSession = Boolean(authToken || isDemo);

  return (
    <>
      {/* Isolated Demo Warning Banner */}
      {isDemo && (
        <aside className="demo-mode-alert-banner" aria-label="Demo mode warning">
          <div className="demo-banner-content">
            <span className="demo-flask-icon">🧪</span>
            <div>
              <strong>{t("demo.banner_title", lang)}: </strong>
              <span>{t("demo.banner_text", lang)}</span>
            </div>
          </div>
          <button
            type="button"
            className="btn-exit-demo"
            onClick={handleExitDemo}
          >
            {t("demo.switch_to_prod", lang)} →
          </button>
        </aside>
      )}

      <header className="app-header">
        <div className="brand-wrapper">
          <span className="brand-badge">{isDemo ? "DEMO" : "PRO"}</span>
          <span className="brand-title">{t("app.title", lang)}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <LanguageSelector lang={lang} onChange={setLang} />
          {hasSession && !isTMA && (
            <button
              type="button"
              onClick={handleLogout}
              className="lang-btn"
              style={{ fontSize: "12px", color: "var(--color-muted)" }}
            >
              {t("logout", lang)}
            </button>
          )}
        </div>
      </header>

      {!hasSession ? (
        <div className="login-container">
          <div className="login-header">
            <h1 className="login-title">{t("login.title", lang)}</h1>
            <p className="login-desc">{t("login.desc", lang)}</p>
          </div>

          {loginError && <div className="error-banner">{loginError}</div>}

          <div className="login-role-tabs-relative">
            <button
              type="button"
              className={`role-tab-btn ${loginRole === "relative" ? "active" : ""}`}
              onClick={() => setLoginRole("relative")}
            >
              <span aria-hidden="true">👥</span> {t("login.role_relative", lang)}
            </button>
            {import.meta.env.DEV && (
              <button
                type="button"
                className={`role-tab-btn ${loginRole === "patient" ? "active" : ""}`}
                onClick={() => setLoginRole("patient")}
              >
                <span aria-hidden="true">👤</span> {t("login.role_patient", lang)}
              </button>
            )}
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label htmlFor="relative-phone-input" className="form-label">{t("login.phone_label", lang)}</label>
              <input
                id="relative-phone-input"
                type="tel"
                className="form-input"
                placeholder={t("login.phone_placeholder", lang)}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                autoComplete="tel"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="relative-pin-input" className="form-label">{t("login.pin_label", lang)}</label>
              <input
                id="relative-pin-input"
                type="password"
                maxLength={6}
                inputMode="numeric"
                className="form-input"
                placeholder={t("login.pin_placeholder", lang)}
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="login-btn" disabled={loggingIn}>
              {loggingIn ? "..." : t("login.submit", lang)}
            </button>

            {import.meta.env.DEV && (
              <>
                <div className="login-demo-divider">
                  <span className="divider-line" />
                <span className="divider-label">{t("common.or", lang)}</span>
                  <span className="divider-line" />
                </div>

                <button
                  type="button"
                  className="quick-demo-btn"
                  onClick={handleLaunchDemo}
                >
                  {t("demo.enter_demo", lang)}
                </button>

                <div className="login-demo-hint">
                  <span>{t("login.hint", lang)}</span>
                </div>
              </>
            )}
          </form>
        </div>
      ) : loading ? (
        <div className="main-content" style={{ justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
          <span style={{ color: "var(--color-muted)" }}>{t("app.loading", lang)}</span>
        </div>
      ) : loadError && !viewData ? (
        <div className="relative-error-card">
          <div className="error-icon-circle">⚠️</div>
          <h3>{loadError}</h3>
          <div className="error-actions-row">
            <button
              type="button"
              className="btn-retry-relative"
              onClick={() => viewToken && loadData(viewToken)}
            >
              🔄 {t("error.retry", lang)}
            </button>
            <button
              type="button"
              className="btn-back-login"
              onClick={handleLogout}
            >
              {t("error.back_to_login", lang)}
            </button>
          </div>
        </div>
      ) : viewData ? (
        <main className="main-content">
          {/* 1. Multi-Patient Switcher */}
          {patients.length > 0 && (
            <PatientSwitcher
              patients={patients}
              activePatientId={activePatientId}
              onSelect={handleSelectPatient}
              lang={lang}
            />
          )}

          {/* 2. Hero Status & AI 72-hour Prognosis Hub */}
          <HeroStatusPrognosis
            level={viewData.level}
            compositeScore={viewData.composite_score}
            lastReadingAt={viewData.last_reading_at}
            prognosis={viewData.prognosis}
            lang={lang}
          />

          {/* 2.2. B2C Subscription Plan, Trial & Compliance Status */}
          <PlanStatusCard lang={lang} />

          {/* 2.5. Apple Health Style Vitals Grid */}
          {viewData.level !== "no_data" && viewData.vitals && (
            <Vitals vitals={viewData.vitals} lang={lang} />
          )}

          {/* V2 Emergency SOS & Weight Log Actions */}
          <V2ProfileActions patientId={activePatientId} />

          {/* no_data Warning if applicable */}
          {viewData.level === "no_data" && (
            <div className="no-data-warning-card">
              <div className="no-data-icon-wrap">
                <span className="no-data-icon">📡</span>
              </div>
              <div className="no-data-text-block">
                <h3 className="no-data-title">{t("no_data.title", lang)}</h3>
                <p className="no-data-desc">{t("no_data.desc", lang)}</p>
                <p className="no-data-hint">💡 {t("no_data.battery_hint", lang)}</p>
                {viewData.doctor_contact && (
                  <a href={`tel:${viewData.doctor_contact.phone}`} className="no-data-call-btn">
                    <span>📞</span>
                    <span>{t("no_data.call_btn", lang)}</span>
                  </a>
                )}
              </div>
            </div>
          )}

          {/* 3. Root-Cause Problem Breakdown */}
          {viewData.level !== "no_data" && viewData.problems && (
            <ProblemBreakdown problems={viewData.problems} lang={lang} />
          )}

          {/* 4. Interactive Metrics with Baseline Corridors */}
          {viewData.level !== "no_data" && viewData.series && (
            <React.Suspense fallback={<div className="section-loading">{t("app.loading", lang)}</div>}>
              <InteractiveMetrics series={viewData.series} lang={lang} />
            </React.Suspense>
          )}

          {/* 5. Doctor Advice & Quick Contact Bar */}
          <ActionContactBar
            doctorContact={viewData.doctor_contact}
            activeTask={viewData.tasks && viewData.tasks.length > 0 ? viewData.tasks[0] : null}
            recommendation={viewData.prognosis?.recommendation}
            lang={lang}
          />

          {/* Demo stage switcher chips — ONLY visible in Demo Mode and when not inside Telegram Mini App */}
          {isDemo && !isTMA && (
            <div className="demo-switcher-wrapper">
              <span className="demo-switcher-title">{t("demo.stage_label", lang)}</span>
              <div className="state-switcher-demo">
                <button
                  type="button"
                  className={`demo-chip ${viewData.level === "green" ? "active" : ""}`}
                  onClick={() => setDemoState("green")}
                >
                  {t("state.good", lang)}
                </button>
                <button
                  type="button"
                  className={`demo-chip ${viewData.level === "amber" ? "active" : ""}`}
                  onClick={() => setDemoState("amber")}
                >
                  {t("state.attention", lang)}
                </button>
                <button
                  type="button"
                  className={`demo-chip ${viewData.level === "red" ? "active" : ""}`}
                  onClick={() => setDemoState("red")}
                >
                  {t("state.risk", lang)}
                </button>
                <button
                  type="button"
                  className={`demo-chip ${viewData.level === "no_data" ? "active" : ""}`}
                  onClick={() => setDemoState("no_data")}
                >
                  {t("state.no_data", lang)}
                </button>
              </div>
            </div>
          )}
        </main>
      ) : null}
    </>
  );
};

export default App;
