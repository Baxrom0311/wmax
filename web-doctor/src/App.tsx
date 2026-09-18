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
            {/* Ministry & Hospital Header */}
            <div className="login-institution-header">
              <div className="institution-flag-bar" />
              <div className="institution-names">
                <span className="inst-sub">O'ZBEKISTON RESPUBLIKASI SOG'LIQNI SAQLASH VAZIRLIGI</span>
                <span className="inst-main">Xorazm Viloyati Kardiologiya Dispanseri</span>
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
                <p>Masofaviy telemetrik monitoring va erta ogohlantirish tizimi</p>
              </div>
            </div>

            {/* Segmented Official Role Selector */}
            <div className="official-role-segmented">
              <button
                type="button"
                className={`role-tab ${selectedRole === "doctor" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("doctor");
                  setPhone("+998901234567");
                  setPassword("nazorat123");
                }}
              >
                <span className="role-tab-name">Shifokor-kardiolog</span>
                <span className="role-tab-sub">Dr. B. Alimov</span>
              </button>
              <button
                type="button"
                className={`role-tab ${selectedRole === "nurse" ? "active" : ""}`}
                onClick={() => {
                  setSelectedRole("nurse");
                  setPhone("+998901234568");
                  setPassword("nazorat123");
                }}
              >
                <span className="role-tab-name">Patronaj hamshirasi</span>
                <span className="role-tab-sub">N. Rahimova</span>
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
                {loggingIn ? "Avtorizatsiya..." : t("login.submit", lang)}
              </button>

              <div className="login-notice-box">
                <p>
                  Ushbu tizim O'zbekiston Respublikasi SSV klinik protokollari asosida
                  shifokorlik sirini saqlash va bemor ma'lumotlarini himoyalash
                  talablariga to'liq javob beradi.
                </p>
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
