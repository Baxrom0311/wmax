import React, { useCallback, useEffect, useState } from "react";
import { ActionContactBar } from "./components/ActionContactBar";
import { HeroStatusPrognosis } from "./components/HeroStatusPrognosis";
import { LanguageSelector } from "./components/LanguageSelector";
import { PatientSwitcher } from "./components/PatientSwitcher";
import { ProblemBreakdown } from "./components/ProblemBreakdown";
import { PlanStatusCard } from "./components/PlanStatusCard";
import { Vitals } from "./components/Vitals";
import { V2ProfileActions } from "./components/V2ProfileActions";
import { cn } from "./lib/utils";
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
import {
  Activity,
  LogOut,
  Phone,
  Lock,
  RefreshCcw,
  FlaskConical,
  Wifi,
  WifiOff,
  Battery,
} from "lucide-react";

const InteractiveMetrics = React.lazy(() =>
  import("./components/InteractiveMetrics").then((module) => ({
    default: module.InteractiveMetrics,
  }))
);

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

  const [loginRole, setLoginRole] = useState<"relative" | "patient">("relative");
  const [phone, setPhone] = useState<string>("");
  const [pin, setPin] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState<boolean>(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tg] = useState(() => (window as any).Telegram?.WebApp);
  const isTMA = Boolean(tg?.initData);

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      try {
        tg.enableClosingConfirmation?.();
        tg.setHeaderColor?.("#0284c7");
        tg.setBackgroundColor?.("#f0f9ff");
      } catch {
        /* older TMA versions */
      }
    }

    let deepLinkToken: string | null = null;
    const startParam = tg?.initDataUnsafe?.start_param;
    if (startParam) deepLinkToken = startParam;

    if (!deepLinkToken) {
      const searchToken = new URLSearchParams(window.location.search).get("t");
      if (searchToken) deepLinkToken = searchToken;
    }
    if (!deepLinkToken) {
      const pathParts = window.location.pathname.split("/").filter(Boolean);
      const rIndex = pathParts.indexOf("r");
      if (rIndex !== -1 && pathParts[rIndex + 1]) deepLinkToken = pathParts[rIndex + 1];
    }

    const currentAuth = getStoredToken();
    if (deepLinkToken) {
      if (currentAuth || isRelativeDemoSession()) {
        // oxlint-disable-next-line react/set-state-in-effect
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

  const loadData = useCallback(
    async (activeToken: string) => {
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
    },
    [handleLogout, isDemo, lang]
  );

  useEffect(() => {
    if (authToken || isDemo) {
      if (viewToken) {
        // oxlint-disable-next-line react/set-state-in-effect
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
        setViewData({ ...patView, patient_name: res.full_name });
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
          if (matched) setActivePatientId(matched.id);
          else if (resPatients.length > 0) setActivePatientId(resPatients[0].id);
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
    window.history.replaceState({}, "", url.pathname + (url.search || ""));
  };

  const handleSelectPatient = async (p: RelativePatientItem) => {
    setActivePatientId(p.id);
    setViewToken(p.access_token);
    await loadData(p.access_token);
  };

  const setDemoState = async (lvl: AlertLevel) => {
    try {
      const demoData = await getDemoRelativeView(viewToken || undefined, lvl);
      setViewData(demoData);
    } catch (err) {
      console.error("Failed to set demo state:", err);
    }
  };

  const hasSession = Boolean(authToken || isDemo);

  const DEMO_CHIP_CLASSES: Record<AlertLevel, string> = {
    green: "bg-green-100 text-green-700 border-green-300 data-[active=true]:ring-2 data-[active=true]:ring-green-400",
    amber: "bg-amber-100 text-amber-700 border-amber-300 data-[active=true]:ring-2 data-[active=true]:ring-amber-400",
    red: "bg-red-100 text-red-700 border-red-300 data-[active=true]:ring-2 data-[active=true]:ring-red-400",
    no_data: "bg-slate-100 text-slate-600 border-slate-300 data-[active=true]:ring-2 data-[active=true]:ring-slate-400",
  };

  return (
    <>
      {/* ── Demo Warning Banner ── */}
      {isDemo && (
        <aside className="flex items-center gap-3 bg-amber-600 text-white px-4 py-2.5 text-[12.5px]">
          <FlaskConical size={14} className="flex-shrink-0" />
          <span className="flex-1">
            <strong>{t("demo.banner_title", lang)}: </strong>
            {t("demo.banner_text", lang)}
          </span>
          <button
            type="button"
            onClick={handleExitDemo}
            className="bg-white/20 hover:bg-white/30 rounded-lg px-2.5 py-1 text-[11px] font-bold whitespace-nowrap transition-colors"
          >
            {t("demo.switch_to_prod", lang)} →
          </button>
        </aside>
      )}

      {/* ── App Header ── */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-sm"
        style={{ paddingTop: `max(12px, env(safe-area-inset-top, 12px))` }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm">
            <Activity size={16} className="text-white" strokeWidth={2.5} />
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-[10px] font-extrabold px-2 py-0.5 rounded-full tracking-wider",
              isDemo ? "bg-amber-100 text-amber-700 border border-amber-200" : "bg-blue-600 text-white"
            )}>
              {isDemo ? "DEMO" : "PRO"}
            </span>
            <span className="text-[17px] font-extrabold text-slate-800 tracking-tight" style={{ fontFamily: "'Outfit',sans-serif" }}>
              {t("app.title", lang)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <LanguageSelector lang={lang} onChange={setLang} />
          {hasSession && !isTMA && (
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600 transition-colors px-1"
            >
              <LogOut size={13} />
              {t("logout", lang)}
            </button>
          )}
        </div>
      </header>

      {/* ── Login Screen ── */}
      {!hasSession ? (
        <div className="flex flex-col flex-1 px-5 py-8 animate-fade-up">
          {/* Top brand section */}
          <div className="flex flex-col items-center gap-4 mb-8">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-xl shadow-blue-200">
              <Activity size={36} className="text-white" strokeWidth={2} />
            </div>
            <div className="text-center">
              <h1 className="text-[24px] font-extrabold text-slate-900 mb-1" style={{ fontFamily: "'Outfit',sans-serif" }}>
                {t("login.title", lang)}
              </h1>
              <p className="text-[13px] text-slate-500 leading-snug max-w-xs mx-auto">
                {t("login.desc", lang)}
              </p>
            </div>
          </div>

          {/* Role tabs */}
          <div className="flex gap-2 mb-5 bg-slate-100 rounded-2xl p-1">
            <button
              type="button"
              className={cn(
                "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-[13px] font-semibold transition-all",
                loginRole === "relative"
                  ? "bg-white text-blue-700 shadow-sm font-bold"
                  : "text-slate-500 hover:text-slate-700"
              )}
              onClick={() => setLoginRole("relative")}
            >
              👥 {t("login.role_relative", lang)}
            </button>
            {import.meta.env.DEV && (
              <button
                type="button"
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-[13px] font-semibold transition-all",
                  loginRole === "patient"
                    ? "bg-white text-blue-700 shadow-sm font-bold"
                    : "text-slate-500 hover:text-slate-700"
                )}
                onClick={() => setLoginRole("patient")}
              >
                👤 {t("login.role_patient", lang)}
              </button>
            )}
          </div>

          {/* Error banner */}
          {loginError && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 mb-4 text-[13px]">
              <span>⚠️</span> {loginError}
            </div>
          )}

          {/* Login form */}
          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="relative-phone-input" className="text-[12px] font-bold text-slate-600">
                {t("login.phone_label", lang)}
              </label>
              <div className="relative">
                <Phone size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="relative-phone-input"
                  type="tel"
                  className={cn(
                    "w-full pl-10 pr-4 py-3 rounded-2xl border border-slate-200 text-[15px] font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all",
                    "placeholder:text-slate-300 bg-white"
                  )}
                  placeholder={t("login.phone_placeholder", lang)}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  autoComplete="tel"
                  required
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="relative-pin-input" className="text-[12px] font-bold text-slate-600">
                {t("login.pin_label", lang)}
              </label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="relative-pin-input"
                  type="password"
                  maxLength={6}
                  inputMode="numeric"
                  className={cn(
                    "w-full pl-10 pr-4 py-3 rounded-2xl border border-slate-200 text-[15px] font-medium tracking-[0.3em]",
                    "focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all",
                    "placeholder:tracking-normal placeholder:text-slate-300 bg-white"
                  )}
                  placeholder={t("login.pin_placeholder", lang)}
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loggingIn}
              className={cn(
                "w-full py-3.5 rounded-2xl font-extrabold text-[15px] transition-all active:scale-[0.98] mt-1",
                "bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-200",
                "disabled:opacity-60 disabled:cursor-not-allowed"
              )}
            >
              {loggingIn ? "..." : t("login.submit", lang)}
            </button>

            {import.meta.env.DEV && (
              <>
                <div className="flex items-center gap-3 my-1">
                  <span className="flex-1 h-px bg-slate-200" />
                  <span className="text-[11px] text-slate-400 font-semibold">{t("common.or", lang)}</span>
                  <span className="flex-1 h-px bg-slate-200" />
                </div>
                <button
                  type="button"
                  onClick={handleLaunchDemo}
                  className={cn(
                    "w-full py-3 rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50",
                    "text-amber-700 font-semibold text-[13.5px] transition-all hover:bg-amber-100 active:scale-[0.98]"
                  )}
                >
                  <FlaskConical size={14} className="inline mr-1.5 -mt-0.5" />
                  {t("demo.enter_demo", lang)}
                </button>
                <p className="text-center text-[11px] text-slate-400">
                  {t("login.hint", lang)}
                </p>
              </>
            )}
          </form>
        </div>
      ) : loading ? (
        /* ── Loading State ── */
        <div className="flex flex-col flex-1 items-center justify-center gap-3 py-20">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 border border-blue-200 flex items-center justify-center animate-pulse">
            <Wifi size={22} className="text-blue-500" />
          </div>
          <span className="text-[13px] text-slate-400 font-medium">{t("app.loading", lang)}</span>
        </div>
      ) : loadError && !viewData ? (
        /* ── Error State ── */
        <div className="flex flex-col flex-1 items-center justify-center gap-4 px-6 py-20 text-center">
          <div className="w-16 h-16 rounded-3xl bg-red-50 border border-red-200 flex items-center justify-center">
            <WifiOff size={28} className="text-red-400" />
          </div>
          <div>
            <h3 className="text-[15px] font-bold text-slate-700 mb-1">{loadError}</h3>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => viewToken && loadData(viewToken)}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-[13px] font-semibold hover:bg-blue-700 transition-colors"
            >
              <RefreshCcw size={13} />
              {t("error.retry", lang)}
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-[13px] font-semibold hover:bg-slate-50 transition-colors"
            >
              <LogOut size={13} />
              {t("error.back_to_login", lang)}
            </button>
          </div>
        </div>
      ) : viewData ? (
        /* ── Main Dashboard ── */
        <main className="flex flex-col flex-1 py-2">
          {/* 1. Patient Switcher */}
          {patients.length > 0 && (
            <PatientSwitcher
              patients={patients}
              activePatientId={activePatientId}
              onSelect={handleSelectPatient}
              lang={lang}
            />
          )}

          {/* 2. Hero Status + AI Prognosis */}
          <HeroStatusPrognosis
            level={viewData.level}
            compositeScore={viewData.composite_score}
            lastReadingAt={viewData.last_reading_at}
            prognosis={viewData.prognosis}
            lang={lang}
          />

          {/* 3. Plan Status */}
          <PlanStatusCard lang={lang} />

          {/* 4. Vitals Grid */}
          {viewData.level !== "no_data" && viewData.vitals && (
            <Vitals vitals={viewData.vitals} lang={lang} />
          )}

          {/* 5. V2 Profile Actions */}
          <V2ProfileActions patientId={activePatientId} />

          {/* 6. no_data Warning */}
          {viewData.level === "no_data" && (
            <div className="mx-4 mb-4 rounded-2xl bg-slate-50 border border-slate-200 p-5 flex flex-col gap-4 animate-fade-up">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center flex-shrink-0">
                  <WifiOff size={20} className="text-slate-400" />
                </div>
                <div>
                  <h3 className="text-[15px] font-bold text-slate-700 mb-1" style={{ fontFamily: "'Outfit',sans-serif" }}>
                    {t("no_data.title", lang)}
                  </h3>
                  <p className="text-[12.5px] text-slate-500 leading-relaxed">
                    {t("no_data.desc", lang)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-[12px] text-slate-500 bg-blue-50 border border-blue-100 rounded-xl px-3 py-2.5">
                <Battery size={14} className="text-blue-400 flex-shrink-0" />
                {t("no_data.battery_hint", lang)}
              </div>
              {viewData.doctor_contact && (
                <a
                  href={`tel:${viewData.doctor_contact.phone}`}
                  className="flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white font-bold text-[14px] hover:bg-blue-700 transition-colors"
                >
                  <Phone size={16} />
                  {t("no_data.call_btn", lang)}
                </a>
              )}
            </div>
          )}

          {/* 7. Problem Breakdown */}
          {viewData.level !== "no_data" && viewData.problems && (
            <ProblemBreakdown problems={viewData.problems} lang={lang} />
          )}

          {/* 8. Interactive Metrics Charts */}
          {viewData.level !== "no_data" && viewData.series && (
            <React.Suspense
              fallback={<div className="section-loading">{t("app.loading", lang)}</div>}
            >
              <InteractiveMetrics series={viewData.series} lang={lang} />
            </React.Suspense>
          )}

          {/* 9. Doctor Contact & Emergency */}
          <ActionContactBar
            doctorContact={viewData.doctor_contact}
            activeTask={viewData.tasks && viewData.tasks.length > 0 ? viewData.tasks[0] : null}
            recommendation={viewData.prognosis?.recommendation}
            lang={lang}
          />

          {/* 10. Demo State Switcher (only in demo, not TMA) */}
          {isDemo && !isTMA && (
            <div className="mx-4 mb-6 flex flex-col gap-3 bg-amber-50/80 border border-amber-200 border-dashed rounded-2xl p-4">
              <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">
                {t("demo.stage_label", lang)}
              </span>
              <div className="flex gap-2 flex-wrap">
                {(["green", "amber", "red", "no_data"] as AlertLevel[]).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    data-active={viewData.level === lvl}
                    onClick={() => setDemoState(lvl)}
                    className={cn(
                      "px-3 py-1.5 rounded-xl border text-[12px] font-bold transition-all",
                      DEMO_CHIP_CLASSES[lvl],
                      viewData.level === lvl ? "ring-2" : "hover:opacity-80"
                    )}
                  >
                    {t(
                      lvl === "green" ? "state.good" :
                      lvl === "amber" ? "state.attention" :
                      lvl === "red" ? "state.risk" : "state.no_data",
                      lang
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </main>
      ) : null}
    </>
  );
};

export default App;
