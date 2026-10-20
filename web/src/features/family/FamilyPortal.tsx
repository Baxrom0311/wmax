import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { LogOut, RefreshCw, WifiOff } from "lucide-react";
import { Brand } from "@/components/app/brand";
import { LevelDot } from "@/components/app/level-badge";
import { LangSwitcher, ThemeToggle } from "@/components/app/prefs-controls";
import { DemoBanner, ErrorState, LoadingState } from "@/components/app/states";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AuthScreen } from "@/features/auth/AuthScreen";
import { pick } from "@/i18n";
import { t } from "@/i18n/family";
import {
  clearTokens,
  fetchRelativeView,
  getDemoRelativeView,
  getStoredPatients,
  getStoredToken,
  isRelativeDemoSession,
  loginPatient,
  loginRelative,
  saveTokens,
  startDemoRelativeSession,
} from "@/lib/family-api";
import { usePrefs } from "@/lib/prefs";
import { loadTelegram } from "@/lib/telegram";
import type { AlertLevel, RelativePatientItem, RelativeView } from "@/lib/types";
import { FamilyDashboard } from "./FamilyDashboard";

const PENDING_TOKEN_KEY = "wmax_pending_token";

function readPending(): string | null {
  try {
    return sessionStorage.getItem(PENDING_TOKEN_KEY);
  } catch {
    return null;
  }
}

function writePending(token: string | null) {
  try {
    if (token) sessionStorage.setItem(PENDING_TOKEN_KEY, token);
    else sessionStorage.removeItem(PENDING_TOKEN_KEY);
  } catch {
    // storage blocked in some webviews
  }
}

/** Family (caregiver) portal: /r, /r/:token, /relative — also served as the Telegram Mini App. */
export function FamilyPortal() {
  const { lang } = usePrefs();
  const navigate = useNavigate();
  const { token: routeToken } = useParams();

  const [signedIn, setSignedIn] = useState(() => !!getStoredToken());
  const [isDemo, setIsDemo] = useState(() => isRelativeDemoSession());
  const [patients, setPatients] = useState<RelativePatientItem[]>(getStoredPatients);
  const [viewToken, setViewToken] = useState<string | null>(null);
  const [view, setView] = useState<RelativeView | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inTelegram, setInTelegram] = useState(false);
  const deepLinkRef = useRef<string | null>(null);

  const logout = useCallback(() => {
    clearTokens();
    writePending(null);
    setSignedIn(false);
    setIsDemo(false);
    setPatients([]);
    setViewToken(null);
    setView(null);
    setError(null);
  }, []);

  const startDemo = useCallback(async () => {
    const demo = await startDemoRelativeSession();
    setIsDemo(true);
    setSignedIn(true);
    setPatients(demo.patients);
    setViewToken(demo.patients[0]?.access_token ?? null);
  }, []);

  // Deep link: Telegram start_param, ?t=<token> or /r/<token>. Without a session it waits for login.
  useEffect(() => {
    let cancelled = false;
    const searchToken = new URLSearchParams(window.location.search).get("t");
    const wantsDemo = new URLSearchParams(window.location.search).get("demo") === "true";

    void loadTelegram().then((tg) => {
      if (cancelled) return;
      if (tg) {
        tg.ready();
        tg.expand();
        setInTelegram(!!tg.initData);
      }
      const link = tg?.initDataUnsafe?.start_param || searchToken || routeToken || null;
      deepLinkRef.current = link;
      const hasSession = !!getStoredToken();
      if (link) {
        if (hasSession) setViewToken(link);
        else writePending(link);
      } else if (hasSession) {
        setViewToken((current) => current ?? getStoredPatients()[0]?.access_token ?? null);
      }
      if (wantsDemo && !hasSession) void startDemo();
    });
    return () => {
      cancelled = true;
    };
  }, [routeToken, startDemo]);

  const load = useCallback(
    async (token: string) => {
      setLoading(true);
      setError(null);
      try {
        setView(await fetchRelativeView(token, isDemo));
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        if (msg === "UNAUTHORIZED") {
          logout();
          return;
        }
        setError(msg);
        setView(null);
      } finally {
        setLoading(false);
      }
    },
    [isDemo, logout],
  );

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- the selected patient's view is fetched from the API
    if (signedIn && viewToken) void load(viewToken);
  }, [signedIn, viewToken, load]);

  const handleLogin = async (phone: string, secret: string, role: "relative" | "patient") => {
    if (role === "patient") {
      const res = await loginPatient(phone, secret);
      const self: RelativePatientItem = {
        id: "patient_self",
        full_name: res.full_name,
        relationship: "",
        access_token: res.access_token,
        level: "no_data",
        diagnosis: "",
        age: 0,
        last_reading_at: null,
      };
      saveTokens(res, [self]);
      setPatients([self]);
      setIsDemo(false);
      setSignedIn(true);
      setViewToken(res.access_token);
      return;
    }
    const res = await loginRelative(phone, secret);
    const pending = readPending();
    writePending(null);
    setPatients(res.patients ?? []);
    setIsDemo(false);
    setSignedIn(true);
    setViewToken(pending ?? res.patients?.[0]?.access_token ?? null);
  };

  const exitDemo = () => {
    logout();
    navigate("/r", { replace: true });
  };

  const setDemoState = async (level: AlertLevel) => {
    setView(await getDemoRelativeView(viewToken ?? undefined, level));
  };

  if (!signedIn) {
    return <AuthScreen audience="family" onLogin={handleLogin} onDemo={() => void startDemo()} />;
  }

  const activePatient = patients.find((p) => p.access_token === viewToken);

  return (
    <div className="bg-background min-h-svh">
      {isDemo && <DemoBanner title={t("demo.banner_title", lang)} text={t("demo.banner_text", lang)} actionLabel={t("demo.switch_to_prod", lang)} onExit={exitDemo} />}
      <header className="bg-background/90 sticky top-0 z-30 border-b backdrop-blur" style={{ paddingTop: "env(safe-area-inset-top)" }}>
        <div className="mx-auto flex h-14 max-w-3xl items-center gap-2 px-4">
          <Brand subtitle={t("login.title", lang)} className="mr-auto" />
          <LangSwitcher />
          <ThemeToggle />
          {!inTelegram && (
            <Button variant="ghost" size="icon" onClick={logout} aria-label={t("error.back_to_login", lang)} title={t("error.back_to_login", lang)}>
              <LogOut />
            </Button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-5 px-4 py-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
        {patients.length > 1 && (
          <div className="flex items-center gap-3">
            <span className="text-muted-foreground shrink-0 text-sm">{t("patients.select", lang)}</span>
            <Select value={viewToken ?? undefined} onValueChange={setViewToken}>
              <SelectTrigger className="w-full sm:w-80">
                <SelectValue placeholder={t("patients.title", lang)} />
              </SelectTrigger>
              <SelectContent>
                {patients.map((p) => (
                  <SelectItem key={p.id} value={p.access_token}>
                    <LevelDot level={p.level} />
                    {p.full_name}
                    {p.relationship ? <span className="text-muted-foreground">· {p.relationship}</span> : null}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {loading && !view ? (
          <LoadingState label={t("app.loading", lang)} />
        ) : error && !view ? (
          <ErrorState
            title={t("error.fetch_failed", lang)}
            description={error}
            retryLabel={t("error.retry", lang)}
            onRetry={viewToken ? () => void load(viewToken) : undefined}
            extra={
              <Button variant="ghost" onClick={logout}>
                <LogOut />
                {t("error.back_to_login", lang)}
              </Button>
            }
          />
        ) : view ? (
          <>
            {loading && (
              <p className="text-muted-foreground flex items-center gap-2 text-xs">
                <RefreshCw className="size-3 animate-spin" />
                {t("app.loading", lang)}
              </p>
            )}
            <FamilyDashboard view={view} lang={lang} isDemo={isDemo} relationship={activePatient?.relationship} onDemoState={isDemo ? (l) => void setDemoState(l) : undefined} />
          </>
        ) : (
          <ErrorState
            title={t("patients.title", lang)}
            description={pick(lang, {
              uz: "Hisobingizga hali bemor biriktirilmagan. Klinikadan havola yoki PIN so'rang.",
              ru: "К вашей учётной записи пока не привязан пациент. Запросите ссылку или PIN в клинике.",
              en: "No patient is linked to your account yet. Ask the clinic for a link or PIN.",
            })}
            retryLabel={t("error.retry", lang)}
            extra={
              <Button variant="ghost" onClick={logout}>
                <WifiOff />
                {t("error.back_to_login", lang)}
              </Button>
            }
          />
        )}
      </main>
    </div>
  );
}
