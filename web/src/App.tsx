import React, { Suspense, useCallback } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router";
import { LoadingState } from "@/components/app/states";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthScreen } from "@/features/auth/AuthScreen";
import { ClinicDataProvider, ClinicSessionProvider, useClinicSession } from "@/features/clinic/session";
import { PrefsProvider, usePrefs } from "@/lib/prefs";

const LandingPage = React.lazy(() => import("@/pages/LandingPage").then((m) => ({ default: m.LandingPage })));
const PitchHome = React.lazy(() => import("@/pages/pitch/PitchHome").then((m) => ({ default: m.PitchHome })));
const DemoPage = React.lazy(() => import("@/pages/DemoPage").then((m) => ({ default: m.DemoPage })));
const PresentationPage = React.lazy(() => import("@/pages/PresentationPage").then((m) => ({ default: m.PresentationPage })));
const ClinicLayout = React.lazy(() => import("@/features/clinic/ClinicLayout").then((m) => ({ default: m.ClinicLayout })));
const PatientsPage = React.lazy(() => import("@/features/clinic/PatientsPage").then((m) => ({ default: m.PatientsPage })));
const PatientDetailPage = React.lazy(() => import("@/features/clinic/PatientDetailPage").then((m) => ({ default: m.PatientDetailPage })));
const TasksPage = React.lazy(() => import("@/features/clinic/TasksPage").then((m) => ({ default: m.TasksPage })));
const SosPage = React.lazy(() => import("@/features/clinic/SosPage").then((m) => ({ default: m.SosPage })));
const DevicesPage = React.lazy(() => import("@/features/clinic/DevicesPage").then((m) => ({ default: m.DevicesPage })));
const ProfilePage = React.lazy(() => import("@/features/clinic/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const FamilyPortal = React.lazy(() => import("@/features/family/FamilyPortal").then((m) => ({ default: m.FamilyPortal })));

/** Route helper for the public pages, which navigate with plain strings such as "/aifu#aloqa". */
function usePublicNavigate() {
  const navigate = useNavigate();
  return useCallback(
    (route: string) => {
      const [, hash] = route.split("#");
      navigate(route);
      if (hash) {
        window.setTimeout(() => document.getElementById(hash)?.scrollIntoView({ behavior: "smooth" }), 100);
      } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    },
    [navigate],
  );
}

// Landing, Pitch Day and presentation pages keep their own dark visual design.
function PublicShell({ page }: { page: "landing" | "pitch" | "demo" | "pptx" }) {
  const { lang, setLang } = usePrefs();
  const onNavigate = usePublicNavigate();
  return (
    <div className="flex min-h-screen flex-col bg-slate-900 font-sans text-slate-100">
      {page === "landing" && <LandingPage key={lang} lang={lang} onNavigate={onNavigate} onOpenLogin={() => onNavigate("/doctor")} />}
      {page === "pitch" && <PitchHome lang={lang} onLangChange={setLang} onNavigate={onNavigate} />}
      {page === "demo" && <DemoPage key={lang} lang={lang} onLangChange={setLang} onNavigate={onNavigate} />}
      {page === "pptx" && <PresentationPage lang={lang} onNavigate={onNavigate} />}
    </div>
  );
}

function ClinicApp() {
  const { user, login, launchDemo, logout } = useClinicSession();
  if (!user) {
    return <AuthScreen audience="clinic" onLogin={login} onDemo={(role) => launchDemo(role)} />;
  }
  return (
    <ClinicDataProvider onUnauthorized={logout}>
      <ClinicLayout />
    </ClinicDataProvider>
  );
}

function RouteFallback() {
  const { lang } = usePrefs();
  return <LoadingState label={lang === "ru" ? "Загрузка..." : lang === "en" ? "Loading..." : "Yuklanmoqda..."} className="min-h-svh" />;
}

export default function App() {
  return (
    <PrefsProvider>
      <TooltipProvider delayDuration={200}>
        <BrowserRouter>
          <ClinicSessionProvider>
            <Suspense fallback={<RouteFallback />}>
              <Routes>
                <Route path="/" element={<PublicShell page="landing" />} />
                <Route path="/aifu/*" element={<PublicShell page="pitch" />} />
                <Route path="/demo" element={<PublicShell page="demo" />} />
                <Route path="/pptx" element={<PublicShell page="pptx" />} />
                <Route path="/presentation" element={<PublicShell page="pptx" />} />

                <Route path="/doctor" element={<ClinicApp />}>
                  <Route index element={<PatientsPage />} />
                  <Route path="patients/:id" element={<PatientDetailPage />} />
                  <Route path="tasks" element={<TasksPage />} />
                  <Route path="sos" element={<SosPage />} />
                  <Route path="devices" element={<DevicesPage />} />
                  <Route path="profile" element={<ProfilePage />} />
                  <Route path="*" element={<Navigate to="/doctor" replace />} />
                </Route>

                <Route path="/r" element={<FamilyPortal />} />
                <Route path="/r/:token" element={<FamilyPortal />} />
                <Route path="/relative" element={<FamilyPortal />} />
                <Route path="/relative/:token" element={<FamilyPortal />} />

                <Route path="/login" element={<Navigate to="/doctor" replace />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </ClinicSessionProvider>
        </BrowserRouter>
        <Toaster position="bottom-right" />
      </TooltipProvider>
    </PrefsProvider>
  );
}
