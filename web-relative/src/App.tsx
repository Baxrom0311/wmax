import React, { useEffect, useState } from "react";
import { LanguageSelector } from "./components/LanguageSelector";
import { Sparkline } from "./components/Sparkline";
import { StatusOrb } from "./components/StatusOrb";
import { Vitals } from "./components/Vitals";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import { clearTokens, fetchRelativeView, getStoredToken, loginRelative } from "./lib/api";
import {
  MOCK_RELATIVE_VIEW_ATTENTION,
  MOCK_RELATIVE_VIEW_GOOD,
  MOCK_RELATIVE_VIEW_NODATA,
  MOCK_RELATIVE_VIEW_RISK,
} from "./lib/mock";
import type { AlertLevel, RelativeView } from "./lib/types";

export const App: React.FC = () => {
  const [lang, setLang] = useState<Lang>("uz");
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [viewData, setViewData] = useState<RelativeView | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Login form state
  const [phone, setPhone] = useState<string>("");
  const [pin, setPin] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  // Extract token from URL path if available (/r/:token)
  useEffect(() => {
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
      setViewData(MOCK_RELATIVE_VIEW_GOOD);
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
    setViewData(null);
  };

  // Demo switchers for presentation
  const setDemoState = (lvl: AlertLevel) => {
    if (lvl === "green") setViewData(MOCK_RELATIVE_VIEW_GOOD);
    else if (lvl === "amber") setViewData(MOCK_RELATIVE_VIEW_ATTENTION);
    else if (lvl === "red") setViewData(MOCK_RELATIVE_VIEW_RISK);
    else if (lvl === "no_data") setViewData(MOCK_RELATIVE_VIEW_NODATA);
  };

  const formatLastUpdated = (isoDate: string | null) => {
    if (!isoDate) return t("updated.just_now", lang);
    const diffMins = Math.max(1, Math.round((Date.now() - new Date(isoDate).getTime()) / 60000));
    if (diffMins < 60) {
      return t("updated.mins_ago", lang, { m: diffMins });
    }
    const diffHours = Math.round(diffMins / 60);
    return t("updated.hours_ago", lang, { h: diffHours });
  };

  return (
    <>
      <header className="app-header">
        <span className="brand-title">{t("app.title", lang)}</span>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <LanguageSelector lang={lang} onChange={setLang} />
          {token && (
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

            <div className="login-demo-hint">
              <span>{t("login.hint", lang)}</span>
            </div>
          </form>
        </div>
      ) : loading ? (
        <div className="main-content" style={{ justifyContent: "center" }}>
          <span style={{ color: "var(--color-muted)" }}>Yuklanmoqda...</span>
        </div>
      ) : viewData ? (
        <main className="main-content">
          {/* 1. Katta Doira (The Big Status Orb) */}
          <StatusOrb level={viewData.level} lang={lang} />

          {/* 2. Bemor ismi + Oxirgi yangilanish vaqti */}
          <div className="patient-meta">
            <h2 className="patient-name">{viewData.patient_name}</h2>
            <div className="update-time">
              {formatLastUpdated(viewData.last_reading_at)}
            </div>
          </div>

          {/* 3. Trend jumlasi */}
          <div className="trend-section">
            {viewData.level === "no_data" ? (
              <p className="no-data-hint">{t("no_data.desc", lang)}</p>
            ) : (
              <p className="trend-sentence">
                {viewData.trend.direction === "improving" && "↗ "}
                {viewData.trend.direction === "worsening" && "↘ "}
                {viewData.trend.direction === "stable" && "→ "}
                {t(`trend.${viewData.trend.direction}`, lang)}
              </p>
            )}
          </div>

          {/* 4. 7 kunlik sparkline (o'qsiz, to'rsiz, sof shakl) */}
          <div className="sparkline-container">
            <Sparkline data={viewData.sparkline} level={viewData.level} />
          </div>

          {/* 5. Pastki ko'rsatkichlar (Puls, SpO2, Uyqu) */}
          <Vitals
            hr={viewData.vitals.hr}
            spo2={viewData.vitals.spo2}
            sleepHours={viewData.vitals.sleep_hours}
            lang={lang}
          />

          {/* Demo hakamlar uchun holat o'zgartirgich tugmalar */}
          <div className="state-switcher-demo">
            <button
              type="button"
              className={`demo-chip ${viewData.level === "green" ? "active" : ""}`}
              onClick={() => setDemoState("green")}
            >
              Yashil
            </button>
            <button
              type="button"
              className={`demo-chip ${viewData.level === "amber" ? "active" : ""}`}
              onClick={() => setDemoState("amber")}
            >
              Sariq
            </button>
            <button
              type="button"
              className={`demo-chip ${viewData.level === "red" ? "active" : ""}`}
              onClick={() => setDemoState("red")}
            >
              Qizil
            </button>
            <button
              type="button"
              className={`demo-chip ${viewData.level === "no_data" ? "active" : ""}`}
              onClick={() => setDemoState("no_data")}
            >
              No Data
            </button>
          </div>
        </main>
      ) : null}
    </>
  );
};

export default App;
