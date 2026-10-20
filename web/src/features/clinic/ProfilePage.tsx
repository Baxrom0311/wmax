import { useMemo, useState } from "react";
import { toast } from "sonner";
import { LogOut, Pencil, Radio, Save, X } from "lucide-react";
import { LEVEL_DOT } from "@/lib/levels";
import { PageHeader } from "@/components/app/states";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import { initials } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import type { AlertLevel } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useClinicData, useClinicSession } from "./session";

interface ProfileForm {
  fullName: string;
  specialty: string;
  organization: string;
  department: string;
  phone: string;
  workHours: string;
}

// Local, per-browser contact card. The server account is the source of truth for name and role.
const STORAGE_KEY = "wmax_doctor_profile_data";

function loadProfile(fullName: string): ProfileForm {
  const defaults: ProfileForm = { fullName, specialty: "", organization: "", department: "", phone: "", workHours: "" };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? { ...defaults, ...JSON.parse(raw), fullName: JSON.parse(raw).fullName || fullName } : defaults;
  } catch {
    return defaults;
  }
}

export function ProfilePage() {
  const { lang } = usePrefs();
  const { user, isDemo, logout } = useClinicSession();
  const { patients, realtime } = useClinicData();
  const [form, setForm] = useState<ProfileForm>(() => loadProfile(user?.full_name ?? ""));
  const [draft, setDraft] = useState<ProfileForm | null>(null);

  const levels = useMemo(() => {
    const c: Record<AlertLevel, number> = { red: 0, amber: 0, green: 0, no_data: 0 };
    for (const p of patients) c[p.level] += 1;
    return c;
  }, [patients]);

  const fields: { key: keyof ProfileForm; label: string }[] = [
    { key: "fullName", label: pick(lang, { uz: "F.I.Sh", ru: "ФИО", en: "Full name" }) },
    { key: "specialty", label: pick(lang, { uz: "Mutaxassislik", ru: "Специальность", en: "Specialty" }) },
    { key: "organization", label: pick(lang, { uz: "Tibbiy muassasa", ru: "Медучреждение", en: "Facility" }) },
    { key: "department", label: pick(lang, { uz: "Bo'lim", ru: "Отделение", en: "Department" }) },
    { key: "phone", label: pick(lang, { uz: "Telefon", ru: "Телефон", en: "Phone" }) },
    { key: "workHours", label: pick(lang, { uz: "Ish tartibi", ru: "График работы", en: "Working hours" }) },
  ];

  const save = () => {
    if (!draft) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
    } catch {
      // storage may be unavailable (private mode); keep the in-memory copy
    }
    setForm(draft);
    setDraft(null);
    toast.success(pick(lang, { uz: "Saqlandi", ru: "Сохранено", en: "Saved" }));
  };

  const roleLabel = user?.role === "nurse" ? t("role.nurse", lang) : user?.role === "doctor" ? t("role.doctor", lang) : (user?.role ?? "—");
  const realtimeLabel =
    realtime === "live"
      ? pick(lang, { uz: "Jonli ulanish", ru: "Живое соединение", en: "Live connection" })
      : realtime === "demo"
        ? t("demo.badge", lang)
        : pick(lang, { uz: "Har daqiqada yangilanadi", ru: "Обновление раз в минуту", en: "Refreshing every minute" });

  return (
    <div className="space-y-6">
      <PageHeader title={pick(lang, { uz: "Profil", ru: "Профиль", en: "Profile" })} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card>
          <CardHeader className="flex flex-row items-center gap-4">
            <Avatar className="size-14">
              <AvatarFallback className="bg-primary text-primary-foreground text-lg font-semibold">{initials(form.fullName || "W")}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <CardTitle className="truncate text-xl">{form.fullName || "—"}</CardTitle>
              <CardDescription className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{roleLabel}</Badge>
                {isDemo && <Badge variant="attention">{t("demo.badge", lang)}</Badge>}
              </CardDescription>
            </div>
            {!draft ? (
              <Button variant="outline" size="sm" onClick={() => setDraft(form)}>
                <Pencil />
                {pick(lang, { uz: "Tahrirlash", ru: "Изменить", en: "Edit" })}
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button variant="ghost" size="icon-sm" onClick={() => setDraft(null)} aria-label={t("confirm_modal.cancel", lang)}>
                  <X />
                </Button>
                <Button size="sm" onClick={save}>
                  <Save />
                  {pick(lang, { uz: "Saqlash", ru: "Сохранить", en: "Save" })}
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              {fields.map((f) => (
                <div key={f.key} className="space-y-1.5">
                  <Label htmlFor={`prof-${f.key}`} className="text-muted-foreground text-xs">
                    {f.label}
                  </Label>
                  {draft ? (
                    <Input id={`prof-${f.key}`} value={draft[f.key]} onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })} />
                  ) : (
                    <p id={`prof-${f.key}`} className={cn("text-sm font-medium", !form[f.key] && "text-muted-foreground")}>
                      {form[f.key] || pick(lang, { uz: "Kiritilmagan", ru: "Не указано", en: "Not set" })}
                    </p>
                  )}
                </div>
              ))}
            </div>
            <p className="text-muted-foreground mt-6 text-xs">
              {pick(lang, {
                uz: "Bu ma'lumotlar faqat shu brauzerda saqlanadi. Ism va rol serverdagi hisobingizdan olinadi.",
                ru: "Эти данные хранятся только в этом браузере. Имя и роль берутся из учётной записи на сервере.",
                en: "These details are stored in this browser only. Name and role come from your server account.",
              })}
            </p>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{pick(lang, { uz: "Kuzatuvdagi bemorlar", ru: "Пациенты под наблюдением", en: "Monitored patients" })}</CardTitle>
              <CardDescription className="font-display tabular text-foreground text-3xl font-bold">{patients.length}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {(
                [
                  ["red", t("triage.red_title", lang)],
                  ["amber", t("triage.amber_title", lang)],
                  ["green", t("triage.green_title", lang)],
                  ["no_data", t("triage.nodata_title", lang)],
                ] as const
              ).map(([level, label]) => (
                <div key={level} className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className={cn("size-2 rounded-full", LEVEL_DOT[level])} />
                    {label}
                  </span>
                  <span className="tabular font-medium">{levels[level]}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 text-sm">
                <Radio className={cn("size-4", realtime === "live" ? "text-good" : "text-muted-foreground")} />
                {realtimeLabel}
              </div>
              <Button variant="outline" className="w-full" onClick={logout}>
                <LogOut />
                {t("logout", lang)}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
