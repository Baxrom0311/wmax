import React, { useEffect, useState } from "react";
import { Navbar } from "./components/Navbar";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import {
  clearTokens,
  fetchPatientDetail,
  fetchPatients,
  getStoredToken,
  loginDoctor,
} from "./lib/api";
import type { PatientDetail, PatientSummary, TokenPair } from "./lib/types";
import { PatientDetailPage } from "./pages/PatientDetail";
import { PatientsList } from "./pages/PatientsList";

export const App: React.FC = () => {
  const [lang, setLang] = useState<Lang>("uz");
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [user, setUser] = useState<TokenPair | null>(null);

  // Data states
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [detailPatient, setDetailPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Login form state
  const [selectedRole, setSelectedRole] = useState<"doctor" | "nurse">("doctor");
  const [phone, setPhone] = useState<string>("+998901234567");
  const [password, setPassword] = useState<string>("nazorat123");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const data = await fetchPatients();
      setPatients(data);
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id: string) => {
    setLoading(true);
    try {
      const data = await fetchPatientDetail(id);
      setDetailPatient(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadPatients();
    }
  }, [token]);

  useEffect(() => {
    if (selectedPatientId) {
      loadDetail(selectedPatientId);
    } else {
      setDetailPatient(null);
    }
  }, [selectedPatientId]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoggingIn(true);
    try {
      const pair = await loginDoctor(phone, password);
      setToken(pair.access_token);
      setUser(pair);
    } catch {
      setLoginError(t("login.error", lang));
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    clearTokens();
    setToken(null);
    setUser(null);
    setSelectedPatientId(null);
    setDetailPatient(null);
  };

  return (
    <>
      <Navbar
        lang={lang}
        onLangChange={setLang}
        doctorName={user?.full_name || (token ? "Dr. Alimov Bahrom" : undefined)}
        onLogout={handleLogout}
      />

      {!token ? (
        <div className="doctor-login-wrapper">
          <div className="doctor-login-box">
            {/* Hospital & Department Tag */}
            <div className="login-hospital-badge">
              <span className="hospital-dot" />
              <span>Xorazm viloyati Kardiologiya Dispanseri</span>
            </div>

            <div className="login-brand-header">
              <div className="medical-pulse-logo">
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="ecg-svg"
                >
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </div>
              <div>
                <h1 className="login-title">
                  {t("login.title", lang)}
                </h1>
                <p className="login-desc">
                  {t("login.desc", lang)}
                </p>
              </div>
            </div>

            {/* Quick Role Selection Cards */}
            <div className="login-role-selector">
              <div
                className={`login-role-card ${selectedRole === "doctor" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("doctor");
                  setPhone("+998901234567");
                  setPassword("nazorat123");
                }}
              >
                <span className="role-card-icon">👨‍⚕️</span>
                <div className="role-card-info">
                  <span className="role-card-title">{t("login.quick_doc", lang)}</span>
                  <span className="role-card-sub">Dr. B. Alimov</span>
                </div>
                {selectedRole === "doctor" && <span className="role-active-check">✓</span>}
              </div>

              <div
                className={`login-role-card ${selectedRole === "nurse" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("nurse");
                  setPhone("+998901234568");
                  setPassword("nazorat123");
                }}
              >
                <span className="role-card-icon">👩‍⚕️</span>
                <div className="role-card-info">
                  <span className="role-card-title">{t("login.quick_nurse", lang)}</span>
                  <span className="role-card-sub">Hamshira N. Rahimova</span>
                </div>
                {selectedRole === "nurse" && <span className="role-active-check">✓</span>}
              </div>
            </div>

            {loginError && (
              <div className="login-error-banner">
                <span>⚠️ {loginError}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="login-form">
              <div className="login-field-group">
                <label htmlFor="doctor-phone-input" className="login-field-label">
                  {t("login.phone_label", lang)}
                </label>
                <div className="input-with-icon">
                  <span className="input-decor-icon">📞</span>
                  <input
                    id="doctor-phone-input"
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="doctor-text-input"
                    placeholder="+998901234567"
                    required
                  />
                </div>
              </div>

              <div className="login-field-group">
                <label htmlFor="doctor-password-input" className="login-field-label">
                  {t("login.password_label", lang)}
                </label>
                <div className="input-with-icon">
                  <span className="input-decor-icon">🔒</span>
                  <input
                    id="doctor-password-input"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="doctor-text-input"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary login-submit-btn"
                disabled={loggingIn}
              >
                {loggingIn ? "Kirilmoqda..." : t("login.submit", lang)}
              </button>

              <div className="login-compliance-footer">
                <span>🔒 O'zbekiston Respublikasi SSV standartlariga muvofiq shifrlangan</span>
              </div>
            </form>
          </div>
        </div>
      ) : loading && !detailPatient && patients.length === 0 ? (
        <div style={{ textAlign: "center", padding: "40px", color: "var(--color-muted)" }}>
          Yuklanmoqda...
        </div>
      ) : selectedPatientId && detailPatient ? (
        <PatientDetailPage
          patient={detailPatient}
          onBack={() => setSelectedPatientId(null)}
          onRefresh={() => loadDetail(selectedPatientId)}
          lang={lang}
        />
      ) : (
        <PatientsList
          patients={patients}
          onSelectPatient={(id) => setSelectedPatientId(id)}
          lang={lang}
        />
      )}
    </>
  );
};

export default App;
