import React, { useEffect, useState } from "react";
import { ActionContactBar } from "./components/ActionContactBar";
import { HeroStatusPrognosis } from "./components/HeroStatusPrognosis";
import { InteractiveMetrics } from "./components/InteractiveMetrics";
import { LanguageSelector } from "./components/LanguageSelector";
import { PatientSwitcher } from "./components/PatientSwitcher";
import { ProblemBreakdown } from "./components/ProblemBreakdown";
import { Vitals } from "./components/Vitals";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import {
  clearTokens,
  fetchRelativeView,
  getStoredPatients,
  getStoredToken,
  loginRelative,
} from "./lib/api";
import {
  MOCK_RELATIVE_PATIENTS,
  MOCK_RELATIVE_VIEW_NODATA,
  MOCK_RELATIVE_VIEW_PRO,
  MOCK_RELATIVE_VIEW_STABLE,
} from "./lib/mock";
import type { AlertLevel, RelativePatientItem, RelativeView } from "./lib/types";

export const App: React.FC = () => {
  const [lang, setLang] = useState<Lang>("uz");
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [patients, setPatients] = useState<RelativePatientItem[]>(getStoredPatients());
  const [activePatientId, setActivePatientId] = useState<string>(
    patients[0]?.id || "p-001-red"
  );
  const [viewData, setViewData] = useState<RelativeView | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Login form state
  const [phone, setPhone] = useState<string>("");
  const [pin, setPin] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tg = (window as any).Telegram?.WebApp;
  const isTMA = Boolean(tg?.initData);

  // Extract token from URL path if available (/r/:token)
  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      try {
        tg.enableClosingConfirmation?.();
        tg.setHeaderColor?.("#ffffff");
        tg.setBackgroundColor?.("#f8fafc");
      } catch { /* older TMA versions may not support */ }
      // Auto-launch inside Telegram Mini App
      if (!token && !getStoredToken()) {
        setViewData(MOCK_RELATIVE_VIEW_PRO);
        setToken("tg_webapp_session");
      }
    }

    const pathParts = window.location.pathname.split("/").filter(Boolean);
    const rIndex = pathParts.indexOf("r");
    if (rIndex !== -1 && pathParts[rIndex + 1]) {
      const urlToken = pathParts[rIndex + 1];
      setToken(urlToken);
    }
  }, []);

  const loadData = async (activeToken: string) => {
    setLoading(true);
    try {
      const data = await fetchRelativeView(activeToken);
      setViewData(data);
    } catch {
      setViewData(MOCK_RELATIVE_VIEW_PRO);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadData(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoggingIn(true);
    try {
      const res = await loginRelative(phone, pin);
      setToken(res.access_token);
      setPatients(res.patients || MOCK_RELATIVE_PATIENTS);
      if (res.patients && res.patients.length > 0) {
        setActivePatientId(res.patients[0].id);
      }
      await loadData(res.access_token);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t("login.error", lang);
      setLoginError(message);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    clearTokens();
    setToken(null);
    setPatients([]);
    setViewData(null);
  };

  const handleSelectPatient = async (p: RelativePatientItem) => {
    setActivePatientId(p.id);
    await loadData(p.access_token);
  };

  // Demo switchers for presentation
  const setDemoState = (lvl: AlertLevel) => {
    if (lvl === "green") setViewData(MOCK_RELATIVE_VIEW_STABLE);
    else if (lvl === "amber") setViewData(MOCK_RELATIVE_VIEW_PRO);
    else if (lvl === "red") {
      setViewData({
        ...MOCK_RELATIVE_VIEW_PRO,
        level: "red",
        level_word_key: "state.risk",
        composite_score: 4.6,
        prognosis: {
          ...MOCK_RELATIVE_VIEW_PRO.prognosis,
          risk_level: "high",
          risk_probability_pct: 88,
          summary: "SpO2 88% gacha tushgan, taxikardiya 114 bpm. Zudlik bilan shifokor ko'rigi talab etiladi!",
        },
      });
    } else if (lvl === "no_data") setViewData(MOCK_RELATIVE_VIEW_NODATA);
  };

  return (
    <>
      <header className="app-header">
        <div className="brand-wrapper">
          <span className="brand-badge">PRO</span>
          <span className="brand-title">{t("app.title", lang)}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <LanguageSelector lang={lang} onChange={setLang} />
          {token && !isTMA && (
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

      {!token ? (
        <div className="login-container">
          <div className="login-header">
            <h1 className="login-title">{t("login.title", lang)}</h1>
            <p className="login-desc">{t("login.desc", lang)}</p>
          </div>

          {loginError && <div className="error-banner">{loginError}</div>}

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
              />
            </div>

            <button type="submit" className="login-btn" disabled={loggingIn}>
              {loggingIn ? "..." : t("login.submit", lang)}
            </button>

            <button
              type="button"
              className="quick-demo-btn"
              onClick={() => {
                setPhone("+998901234567");
                setPin("112233");
              }}
            >
              🚀 {t("login.quick_demo", lang)}
            </button>

            <div className="login-demo-hint">
              <span>{t("login.hint", lang)}</span>
            </div>
          </form>
        </div>
      ) : loading ? (
        <div className="main-content" style={{ justifyContent: "center", alignItems: "center" }}>
          <span style={{ color: "var(--color-muted)" }}>{t("app.loading", lang)}</span>
        </div>
      ) : viewData ? (
        <main className="main-content">
          {/* 1. Multi-Patient Switcher */}
          <PatientSwitcher
            patients={patients.length > 0 ? patients : MOCK_RELATIVE_PATIENTS}
            activePatientId={activePatientId}
            onSelect={handleSelectPatient}
            lang={lang}
          />

          {/* 2. Hero Status & AI 72-hour Prognosis Hub */}
          <HeroStatusPrognosis
            level={viewData.level}
            compositeScore={viewData.composite_score}
            lastReadingAt={viewData.last_reading_at}
            prognosis={viewData.prognosis}
            lang={lang}
          />

          {/* 2.5. Apple Health Style Vitals Grid */}
          {viewData.level !== "no_data" && viewData.vitals && (
            <Vitals vitals={viewData.vitals} lang={lang} />
          )}

          {/* no_data Warning if applicable */}
          {viewData.level === "no_data" && (
            <div className="no-data-warning-card">
              <h3>⚠️ {t("no_data.title", lang)}</h3>
              <p>{t("no_data.desc", lang)}</p>
            </div>
          )}

          {/* 3. Root-Cause Problem Breakdown */}
          {viewData.level !== "no_data" && viewData.problems && (
            <ProblemBreakdown problems={viewData.problems} lang={lang} />
          )}

          {/* 4. Interactive Metrics with Baseline Corridors */}
          {viewData.level !== "no_data" && viewData.series && (
            <InteractiveMetrics series={viewData.series} lang={lang} />
          )}

          {/* 5. Doctor Advice & Quick Contact Bar */}
          <ActionContactBar
            doctorContact={viewData.doctor_contact}
            activeTask={viewData.tasks && viewData.tasks.length > 0 ? viewData.tasks[0] : null}
            recommendation={viewData.prognosis?.recommendation}
            lang={lang}
          />

          {/* Demo stage switcher chips — hidden inside Telegram Mini App */}
          {!isTMA && (
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
          )}
        </main>
      ) : null}
    </>
  );
};

export default App;
