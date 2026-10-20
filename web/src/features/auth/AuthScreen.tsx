import React, { useState } from "react";
import { Link, useNavigate } from "react-router";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BellRing,
  FlaskConical,
  HeartHandshake,
  KeyRound,
  Loader2,
  Lock,
  Phone,
  ShieldCheck,
  Stethoscope,
  Watch,
} from "lucide-react";
import { Brand } from "@/components/app/brand";
import { LangSwitcher, ThemeToggle } from "@/components/app/prefs-controls";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { pick } from "@/i18n";
import { t as tc } from "@/i18n/clinic";
import { t as tf } from "@/i18n/family";
import { usePrefs } from "@/lib/prefs";
import { cn } from "@/lib/utils";

type ClinicRole = "doctor" | "nurse";
type FamilyRole = "relative" | "patient";

// Seeded demo accounts of the backend fixtures (contracts/seed.sql); shown only as a convenience.
const CLINIC_DEMO: Record<ClinicRole, { phone: string; password: string }> = {
  doctor: { phone: "+998901234567", password: "wmax123" },
  nurse: { phone: "+998901234568", password: "wmax123" },
};

interface ClinicProps {
  audience: "clinic";
  onLogin: (phone: string, password: string) => Promise<unknown>;
  onDemo: (role: ClinicRole) => void;
}

interface FamilyProps {
  audience: "family";
  onLogin: (phone: string, pin: string, role: FamilyRole) => Promise<unknown>;
  onDemo: () => void;
}

export function AuthScreen(props: ClinicProps | FamilyProps) {
  const { lang } = usePrefs();
  const navigate = useNavigate();
  const isClinic = props.audience === "clinic";

  const [clinicRole, setClinicRole] = useState<ClinicRole>("doctor");
  const [familyRole, setFamilyRole] = useState<FamilyRole>("relative");
  const [phone, setPhone] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (props.audience === "clinic") await props.onLogin(phone.trim(), secret);
      else await props.onLogin(phone.trim(), secret.trim(), familyRole);
    } catch (err) {
      const fallback = isClinic ? tc("login.error", lang) : tf("login.error", lang);
      setError(err instanceof Error && err.message ? err.message : fallback);
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = () => {
    const creds = CLINIC_DEMO[clinicRole];
    setPhone(creds.phone);
    setSecret(creds.password);
  };

  const copy = isClinic
    ? {
        title: tc("login.title", lang),
        desc: tc("login.desc", lang),
        panelTitle: pick(lang, {
          uz: "Bemorlarni masofadan kuzatish uchun klinik ish stansiyasi",
          ru: "Клиническая рабочая станция для удалённого наблюдения",
          en: "Clinical workstation for remote patient monitoring",
        }),
      }
    : {
        title: tf("login.title", lang),
        desc: tf("login.desc", lang),
        panelTitle: pick(lang, {
          uz: "Yaqinlaringiz holatini o'lchovlar asosida kuzating",
          ru: "Следите за состоянием близких по реальным измерениям",
          en: "Follow your loved ones through real measurements",
        }),
      };

  const features = [
    {
      icon: Watch,
      text: pick(lang, {
        uz: "Aqlli soat o'lchovlari: puls, SpO₂, harorat, uyqu",
        ru: "Измерения смарт-часов: пульс, SpO₂, температура, сон",
        en: "Smartwatch readings: pulse, SpO₂, temperature, sleep",
      }),
    },
    {
      icon: BellRing,
      text: pick(lang, {
        uz: "Shaxsiy me'yordan og'ish va SOS signallari",
        ru: "Отклонения от личной нормы и SOS-сигналы",
        en: "Deviations from a personal baseline and SOS alerts",
      }),
    },
    {
      icon: ShieldCheck,
      text: pick(lang, {
        uz: "Ma'lumot yo'qligi hech qachon \"sog'lom\" deb ko'rsatilmaydi",
        ru: "Отсутствие данных никогда не показывается как «здоров»",
        en: "Missing data is never shown as \"healthy\"",
      }),
    },
  ];

  return (
    <div className="bg-background grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-gradient-to-br from-teal-700 via-teal-800 to-slate-900 p-10 text-white lg:flex lg:flex-col">
        <div className="pointer-events-none absolute -top-24 -right-24 size-96 rounded-full bg-teal-400/20 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 size-80 rounded-full bg-sky-500/10 blur-3xl" />
        <Link to="/" className="relative flex w-fit items-center gap-2.5">
          <span className="inline-flex size-9 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="2 12 6 12 9 4 14 20 17 12 22 12" />
            </svg>
          </span>
          <span className="font-display text-lg font-extrabold tracking-tight">WMAX</span>
        </Link>
        <div className="relative mt-auto max-w-md space-y-6">
          <h2 className="font-display text-3xl leading-tight font-bold">{copy.panelTitle}</h2>
          <ul className="space-y-3">
            {features.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3 text-sm text-teal-50/90">
                <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <Icon className="size-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative mt-10 text-xs text-teal-100/60">
          {pick(lang, {
            uz: "Klinik qarorlarni shifokor qabul qiladi. WMAX o'lchov va noaniqlikni ko'rsatadi.",
            ru: "Клинические решения принимает врач. WMAX показывает измерения и их неопределённость.",
            en: "Clinicians make clinical decisions. WMAX reports measurements and their uncertainty.",
          })}
        </p>
      </aside>

      {/* Form panel */}
      <main className="flex flex-col">
        <header className="flex items-center justify-between px-4 py-3 sm:px-8">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/">
              <ArrowLeft />
              {pick(lang, { uz: "Bosh sahifa", ru: "Главная", en: "Home" })}
            </Link>
          </Button>
          <div className="flex items-center gap-1">
            <LangSwitcher />
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 items-center justify-center px-4 pb-12 sm:px-8">
          <div className="w-full max-w-md space-y-6">
            <Brand className="lg:hidden" subtitle={pick(lang, { uz: "Masofaviy monitoring", ru: "Удалённый мониторинг", en: "Remote monitoring" })} />

            <Tabs value={props.audience} onValueChange={(v) => navigate(v === "clinic" ? "/doctor" : "/r")}>
              <TabsList className="w-full">
                <TabsTrigger value="clinic">
                  <Stethoscope />
                  {pick(lang, { uz: "Klinika xodimi", ru: "Сотрудник клиники", en: "Clinic staff" })}
                </TabsTrigger>
                <TabsTrigger value="family">
                  <HeartHandshake />
                  {pick(lang, { uz: "Oila a'zosi", ru: "Член семьи", en: "Family" })}
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-xl">{copy.title}</CardTitle>
                <CardDescription>{copy.desc}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {isClinic ? (
                  <div className="bg-muted grid grid-cols-2 gap-1 rounded-lg p-1">
                    {(["doctor", "nurse"] as const).map((role) => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => setClinicRole(role)}
                        className={cn(
                          "rounded-md py-1.5 text-sm font-medium transition cursor-pointer",
                          clinicRole === role ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        {tc(role === "doctor" ? "login.role_doctor" : "login.role_nurse", lang)}
                      </button>
                    ))}
                  </div>
                ) : (
                  import.meta.env.DEV && (
                    <div className="bg-muted grid grid-cols-2 gap-1 rounded-lg p-1">
                      {(["relative", "patient"] as const).map((role) => (
                        <button
                          key={role}
                          type="button"
                          onClick={() => setFamilyRole(role)}
                          className={cn(
                            "rounded-md py-1.5 text-sm font-medium transition cursor-pointer",
                            familyRole === role ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
                          )}
                        >
                          {tf(role === "relative" ? "login.role_relative" : "login.role_patient", lang)}
                        </button>
                      ))}
                    </div>
                  )
                )}

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <form onSubmit={submit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="auth-phone">{isClinic ? tc("login.phone_label", lang) : tf("login.phone_label", lang)}</Label>
                    <div className="relative">
                      <Phone className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                      <Input
                        id="auth-phone"
                        type="tel"
                        inputMode="tel"
                        autoComplete="tel"
                        className="h-11 pl-9"
                        placeholder="+998 90 123 45 67"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="auth-secret">{isClinic ? tc("login.password_label", lang) : tf("login.pin_label", lang)}</Label>
                    <div className="relative">
                      {isClinic ? (
                        <Lock className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                      ) : (
                        <KeyRound className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
                      )}
                      <Input
                        id="auth-secret"
                        type="password"
                        autoComplete={isClinic ? "current-password" : "one-time-code"}
                        inputMode={isClinic ? undefined : "numeric"}
                        maxLength={isClinic ? undefined : 6}
                        className={cn("h-11 pl-9", !isClinic && "tracking-[0.3em]")}
                        placeholder={isClinic ? "••••••••" : "••••••"}
                        value={secret}
                        onChange={(e) => setSecret(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                  <Button type="submit" size="lg" className="h-11 w-full" disabled={busy}>
                    {busy ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                    {busy ? tc("login.loading", lang) : isClinic ? tc("login.submit", lang) : tf("login.submit", lang)}
                  </Button>
                </form>

                {isClinic && (
                  <button
                    type="button"
                    onClick={fillDemo}
                    className="text-muted-foreground hover:text-foreground w-full text-center text-xs underline-offset-4 hover:underline cursor-pointer"
                  >
                    {pick(lang, {
                      uz: "Test hisobi ma'lumotlarini to'ldirish",
                      ru: "Заполнить данные тестового аккаунта",
                      en: "Fill in the test account",
                    })}
                  </button>
                )}

                <div className="flex items-center gap-3">
                  <span className="bg-border h-px flex-1" />
                  <span className="text-muted-foreground text-xs">{tc("common.or", lang)}</span>
                  <span className="bg-border h-px flex-1" />
                </div>

                <Button
                  type="button"
                  variant="outline"
                  className="border-attention/40 bg-attention-soft/50 text-attention-ink hover:bg-attention-soft h-11 w-full border-dashed"
                  onClick={() => (props.audience === "clinic" ? props.onDemo(clinicRole) : props.onDemo())}
                >
                  <FlaskConical />
                  {isClinic ? tc("demo.enter_demo", lang) : tf("demo.enter_demo", lang)}
                </Button>
                <p className="text-muted-foreground text-center text-xs">
                  {pick(lang, {
                    uz: "Demo rejim sun'iy bemorlar bilan ishlaydi va serverga hech narsa yubormaydi.",
                    ru: "Демо-режим работает с вымышленными пациентами и ничего не отправляет на сервер.",
                    en: "Demo mode uses synthetic patients and never writes to the server.",
                  })}
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
