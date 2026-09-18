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
            <h1 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>
              {t("login.title", lang)}
            </h1>
            <p style={{ fontSize: "13px", color: "var(--color-muted)", marginBottom: "20px" }}>
              {t("login.desc", lang)}
            </p>

            {loginError && (
              <div
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#FDF2F2",
                  color: "var(--color-risk)",
                  borderRadius: "4px",
                  fontSize: "13px",
                  marginBottom: "14px",
                }}
              >
                {loginError}
              </div>
            )}

            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: "14px" }}>
                <label
                  htmlFor="doctor-phone-input"
                  style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "4px" }}
                >
                  {t("login.phone_label", lang)}
                </label>
                <input
                  id="doctor-phone-input"
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  style={{
                    width: "100%",
                    height: "40px",
                    border: "1px solid var(--color-line)",
                    borderRadius: "4px",
                    padding: "0 10px",
                    fontSize: "14px",
                  }}
                  required
                />
              </div>

              <div style={{ marginBottom: "18px" }}>
                <label
                  htmlFor="doctor-password-input"
                  style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "4px" }}
                >
                  {t("login.password_label", lang)}
                </label>
                <input
                  id="doctor-password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: "100%",
                    height: "40px",
                    border: "1px solid var(--color-line)",
                    borderRadius: "4px",
                    padding: "0 10px",
                    fontSize: "14px",
                  }}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: "100%", height: "42px" }}
                disabled={loggingIn}
              >
                {loggingIn ? "..." : t("login.submit", lang)}
              </button>

              <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "6px" }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ width: "100%", height: "36px", fontSize: "12px" }}
                  onClick={() => {
                    setPhone("+998901234567");
                    setPassword("nazorat123");
                  }}
                >
                  👨‍⚕️ {t("login.quick_doc", lang)}
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ width: "100%", height: "36px", fontSize: "12px" }}
                  onClick={() => {
                    setPhone("+998901234568");
                    setPassword("nazorat123");
                  }}
                >
                  👩‍⚕️ {t("login.quick_nurse", lang)}
                </button>
              </div>

              <p style={{ fontSize: "12px", color: "var(--color-muted)", marginTop: "10px", textAlign: "center" }}>
                {t("login.demo", lang)}
              </p>
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
