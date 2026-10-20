import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  AlertTriangle,
  BatteryWarning,
  CheckCircle2,
  Footprints,
  HeartPulse,
  Info,
  Loader2,
  Moon,
  Phone,
  Scale,
  Send,
  Siren,
  Stethoscope,
  Thermometer,
  TrendingDown,
  TrendingUp,
  Minus,
  Wind,
  Droplets,
} from "lucide-react";
import { LevelBadge } from "@/components/app/level-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useNow } from "@/hooks/use-now";
import { pick, type Lang } from "@/i18n";
import { t } from "@/i18n/family";
import { recordPatientMeasurement, triggerEmergencySos } from "@/lib/family-api";
import { formatAgo, formatDateTime } from "@/lib/format";
import { paramMeta } from "@/lib/params";
import type { AlertLevel, ProblemItem, RelativeView } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ParamChart } from "@/features/clinic/ParamChart";

const LEVEL_WORD: Record<AlertLevel, string> = {
  green: "state.good",
  amber: "state.attention",
  red: "state.risk",
  no_data: "state.no_data",
};

const HERO_TONE: Record<AlertLevel, string> = {
  green: "border-good/30 bg-good-soft/60",
  amber: "border-attention/30 bg-attention-soft/60",
  red: "border-risk/40 bg-risk-soft/70",
  no_data: "border-nodata/30 bg-nodata-soft/70",
};

const HERO_INK: Record<AlertLevel, string> = {
  green: "text-good-ink",
  amber: "text-attention-ink",
  red: "text-risk-ink",
  no_data: "text-nodata-ink",
};

type VitalState = "normal" | "attention" | "risk" | "missing";

function vitalState(kind: string, v: number | null | undefined): VitalState {
  if (v === null || v === undefined) return "missing";
  switch (kind) {
    case "hr":
      return v > 110 || v < 45 ? "risk" : v > 90 || v < 60 ? "attention" : "normal";
    case "spo2":
      return v < 90 ? "risk" : v < 95 ? "attention" : "normal";
    case "temp":
      return v >= 38 ? "risk" : v < 36 || v > 37.2 ? "attention" : "normal";
    case "rr":
      return v > 24 || v < 10 ? "risk" : v > 20 || v < 12 ? "attention" : "normal";
    case "sleep":
      return v < 7 || v > 9 ? "attention" : "normal";
    default:
      return "normal";
  }
}

const VITAL_TONE: Record<VitalState, string> = {
  normal: "text-good",
  attention: "text-attention",
  risk: "text-risk",
  missing: "text-muted-foreground",
};

export function FamilyDashboard({
  view,
  lang,
  isDemo,
  relationship,
  onDemoState,
}: {
  view: RelativeView;
  lang: Lang;
  isDemo: boolean;
  relationship?: string;
  onDemoState?: (level: AlertLevel) => void;
}) {
  const now = useNow(30000);
  const noData = view.level === "no_data";

  return (
    <div className="space-y-5">
      {view.level === "red" && <RedBanner view={view} lang={lang} />}
      <HeroCard view={view} lang={lang} now={now} relationship={relationship} />

      {noData ? (
        <NoDataCard view={view} lang={lang} now={now} />
      ) : (
        <>
          <VitalsGrid view={view} lang={lang} />
          <ProblemsCard problems={view.problems ?? []} lang={lang} />
          <MetricsCard view={view} lang={lang} />
        </>
      )}

      <div className="grid gap-5 md:grid-cols-2">
        <WeightCard patientId={view.patient_id} lang={lang} />
        <SosCard patientId={view.patient_id} lang={lang} />
      </div>

      <ContactCard view={view} lang={lang} />

      {isDemo && onDemoState && (
        <Card className="border-attention/40 border-dashed py-4">
          <CardContent className="space-y-3">
            <p className="text-attention-ink text-xs font-semibold tracking-wide uppercase">{t("demo.stage_label", lang)}</p>
            <div className="flex flex-wrap gap-2">
              {(["green", "amber", "red", "no_data"] as AlertLevel[]).map((level) => (
                <Button key={level} size="sm" variant={view.level === level ? "default" : "outline"} onClick={() => onDemoState(level)}>
                  {t(LEVEL_WORD[level], lang)}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RedBanner({ view, lang }: { view: RelativeView; lang: Lang }) {
  const [open, setOpen] = useState(false);
  const { hr, spo2 } = view.vitals ?? { hr: null, spo2: null };
  const readings = [spo2 !== null && spo2 !== undefined ? `SpO₂ ${spo2}%` : null, hr !== null && hr !== undefined ? `${pick(lang, { uz: "Puls", ru: "Пульс", en: "Pulse" })} ${hr} bpm` : null]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <div className="bg-risk flex flex-col gap-3 rounded-xl p-4 text-white sm:flex-row sm:items-center">
        <Siren className="size-6 shrink-0 animate-pulse" />
        <div className="min-w-0 flex-1">
          <p className="font-display font-bold">{t("sos.critical", lang)}</p>
          <p className="text-sm opacity-90">
            {readings ||
              pick(lang, { uz: "Ko'rsatkichlar keskin og'gan.", ru: "Показатели резко отклонились.", en: "Readings deviate sharply." })}
          </p>
        </div>
        <Button variant="secondary" className="text-risk shrink-0 bg-white hover:bg-white/90" onClick={() => setOpen(true)}>
          {t("sos.action_btn", lang)}
        </Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-risk flex items-center gap-2">
              <AlertTriangle className="size-5" />
              {t("sos.modal_title", lang)}
            </DialogTitle>
            {readings && <DialogDescription>{readings}</DialogDescription>}
          </DialogHeader>
          <div className="space-y-3">
            <Button variant="destructive" size="lg" className="w-full" asChild>
              <a href="tel:103">
                <Phone />
                {pick(lang, { uz: "103 ga qo'ng'iroq qilish", ru: "Позвонить в 103", en: "Call 103" })}
              </a>
            </Button>
            {view.doctor_contact?.phone && (
              <Button variant="outline" className="w-full" asChild>
                <a href={`tel:${view.doctor_contact.phone}`}>
                  <Stethoscope />
                  {t("sos.call_doctor", lang)}
                </a>
              </Button>
            )}
            <div className="bg-muted/60 rounded-lg p-3 text-sm">
              <p className="mb-2 font-semibold">{t("sos.first_aid_title", lang)}</p>
              <ul className="text-muted-foreground list-disc space-y-1 pl-5">
                <li>{t("sos.tip_1", lang)}</li>
                <li>{t("sos.tip_2", lang)}</li>
                <li>{t("sos.tip_3", lang)}</li>
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function HeroCard({ view, lang, now, relationship }: { view: RelativeView; lang: Lang; now: number; relationship?: string }) {
  const direction = view.trend?.direction;
  const TrendIcon = direction === "worsening" ? TrendingUp : direction === "improving" ? TrendingDown : Minus;
  const noData = view.level === "no_data";

  return (
    <Card className={cn("gap-4 border", HERO_TONE[view.level])}>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <p className="text-muted-foreground text-xs">
              {relationship ? `${relationship} · ` : ""}
              {view.last_reading_at
                ? `${pick(lang, { uz: "Oxirgi o'lchov", ru: "Последнее измерение", en: "Last reading" })}: ${formatAgo(view.last_reading_at, lang, now)}`
                : pick(lang, { uz: "O'lchovlar hali kelmagan", ru: "Измерений ещё нет", en: "No readings yet" })}
            </p>
            <h2 className="font-display truncate text-2xl font-bold">{view.patient_name}</h2>
            <p className={cn("font-display text-lg font-semibold", HERO_INK[view.level])}>{t(LEVEL_WORD[view.level], lang)}</p>
          </div>
          <LevelBadge level={view.level} label={t(LEVEL_WORD[view.level], lang)} />
        </div>

        {!noData && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-background/70 rounded-lg p-3">
              <p className="text-muted-foreground text-xs">{t("hero.composite_deviation", lang)}</p>
              <p className="font-display tabular text-xl font-bold">{view.composite_score.toFixed(1)}</p>
            </div>
            {direction && (
              <div className="bg-background/70 rounded-lg p-3">
                <p className="text-muted-foreground text-xs">{pick(lang, { uz: "Tendensiya", ru: "Тенденция", en: "Trend" })}</p>
                <p className="flex items-center gap-1.5 text-sm font-semibold">
                  <TrendIcon className={cn("size-4", direction === "worsening" ? "text-risk" : direction === "improving" ? "text-good" : "text-muted-foreground")} />
                  {t(`trend.${direction}`, lang)}
                </p>
              </div>
            )}
          </div>
        )}

        {!noData && view.prognosis && (view.prognosis.summary || view.prognosis.recommendation) && (
          <div className="bg-background/70 space-y-2 rounded-lg p-3 text-sm">
            <p className="text-muted-foreground text-xs font-medium">{t("hero.prognosis_title", lang)}</p>
            {view.prognosis.summary && <p>{view.prognosis.summary}</p>}
            {view.prognosis.recommendation && (
              <p>
                <span className="font-semibold">{t("hero.rec_label", lang)}</span> {view.prognosis.recommendation}
              </p>
            )}
            <p className="text-muted-foreground flex items-start gap-1.5 text-xs">
              <Info className="mt-0.5 size-3.5 shrink-0" />
              {view.prognosis.uncertainty_note ||
                pick(lang, {
                  uz: "Bu xulosa soat o'lchovlari asosida avtomatik tuziladi va tashxis emas. Qarorlarni shifokor bilan birga qiling.",
                  ru: "Сводка составляется автоматически по измерениям часов и не является диагнозом. Решения принимайте вместе с врачом.",
                  en: "This summary is generated from watch readings and is not a diagnosis. Make decisions together with the doctor.",
                })}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function NoDataCard({ view, lang, now }: { view: RelativeView; lang: Lang; now: number }) {
  return (
    <Alert variant="info">
      <BatteryWarning />
      <AlertTitle>{t("no_data.title", lang)}</AlertTitle>
      <AlertDescription className="space-y-2">
        <p>
          {pick(lang, {
            uz: "Soatdan yangi o'lchovlar kelmayapti. Bu bemorning holati yaxshi degani emas: soat yechilgan, quvvati tugagan yoki aloqa uzilgan bo'lishi mumkin.",
            ru: "С часов не поступают новые измерения. Это не значит, что с пациентом всё хорошо: часы могли снять, разрядить или потерять связь.",
            en: "No new readings are arriving from the watch. That does not mean the patient is fine: the watch may be off, discharged or disconnected.",
          })}
        </p>
        {view.last_reading_at && <p className="text-xs">{t("no_data.last_seen", lang, { t: formatAgo(view.last_reading_at, lang, now) })}</p>}
        <p className="text-xs">{t("no_data.battery_hint", lang)}</p>
      </AlertDescription>
    </Alert>
  );
}

function VitalsGrid({ view, lang }: { view: RelativeView; lang: Lang }) {
  const v = view.vitals ?? { hr: null, spo2: null, sleep_hours: null };
  const tiles = [
    { kind: "hr", icon: HeartPulse, label: t("vitals.hr", lang), value: v.hr, unit: "bpm", norm: t("vitals.norm_hr", lang) },
    { kind: "spo2", icon: Droplets, label: t("vitals.spo2", lang), value: v.spo2, unit: "%", norm: t("vitals.norm_spo2", lang) },
    { kind: "temp", icon: Thermometer, label: t("vitals.temp", lang), value: v.skin_temp, unit: "°C", norm: t("vitals.norm_temp", lang) },
    { kind: "rr", icon: Wind, label: t("vitals.rr", lang), value: v.rr, unit: t("vitals.breaths", lang), norm: t("vitals.norm_rr", lang) },
    { kind: "sleep", icon: Moon, label: t("vitals.sleep", lang), value: v.sleep_hours, unit: t("vitals.hours", lang), norm: t("vitals.norm_sleep", lang) },
    { kind: "steps", icon: Footprints, label: t("vitals.steps", lang), value: v.steps, unit: t("vitals.steps_unit", lang), norm: "" },
  ].filter((tile) => tile.value !== undefined);

  const stateLabel: Record<VitalState, string> = {
    normal: t("vitals.normal", lang),
    attention: t("vitals.attention", lang),
    risk: t("vitals.risk", lang),
    missing: pick(lang, { uz: "Ma'lumot yo'q", ru: "Нет данных", en: "No data" }),
  };

  return (
    <section className="space-y-3">
      <h3 className="font-display font-semibold">{t("vitals.title", lang)}</h3>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        {tiles.map((tile) => {
          const state = vitalState(tile.kind, tile.value);
          const Icon = tile.icon;
          return (
            <Card key={tile.kind} className="gap-2 py-4">
              <CardContent className="space-y-1.5 px-4">
                <div className="text-muted-foreground flex items-center gap-1.5 text-xs">
                  <Icon className="size-3.5" />
                  <span className="truncate">{tile.label}</span>
                </div>
                <p className="font-display tabular text-2xl font-bold">
                  {tile.value !== null && tile.value !== undefined ? (tile.kind === "steps" ? tile.value.toLocaleString() : tile.value) : "—"}
                  {tile.value !== null && tile.value !== undefined && <span className="text-muted-foreground ml-1 text-sm font-medium">{tile.unit}</span>}
                </p>
                {tile.kind !== "steps" && (
                  <p className={cn("text-xs font-medium", VITAL_TONE[state])}>
                    {stateLabel[state]}
                    {tile.norm && <span className="text-muted-foreground font-normal"> · {tile.norm}</span>}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      <p className="text-muted-foreground text-xs">
        {pick(lang, {
          uz: "Me'yorlar kattalar uchun umumiy ko'rsatkich. Shifokor bemorning shaxsiy me'yoridan kelib chiqib baholaydi.",
          ru: "Нормы указаны общие для взрослых. Врач оценивает по индивидуальной норме пациента.",
          en: "Ranges are general adult references. The doctor judges against the patient's personal baseline.",
        })}
      </p>
    </section>
  );
}

function ProblemsCard({ problems, lang }: { problems: ProblemItem[]; lang: Lang }) {
  const sev: Record<ProblemItem["severity"], "risk" | "attention" | "secondary"> = { severe: "risk", moderate: "attention", mild: "secondary" };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("problems.title", lang)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {problems.length === 0 ? (
          <p className="text-muted-foreground flex items-center gap-2 text-sm">
            <CheckCircle2 className="text-good size-4" />
            {t("problems.none", lang)}
          </p>
        ) : (
          problems.map((p) => (
            <div key={p.param} className="rounded-lg border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold">{p.label || paramMeta(p.param).title[lang]}</p>
                <Badge variant={sev[p.severity]}>{t(`problems.severity_${p.severity}`, lang)}</Badge>
              </div>
              <div className="text-muted-foreground mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                <span>
                  {t("problems.current", lang)}: <span className="text-foreground tabular font-medium">{p.current_value}</span>
                </span>
                <span>
                  {t("problems.baseline", lang)}: <span className="text-foreground tabular font-medium">{p.baseline_range}</span>
                </span>
                {p.deviation && (
                  <span>
                    {t("problems.deviation", lang)}: <span className="text-foreground tabular font-medium">{p.deviation}</span>
                  </span>
                )}
              </div>
              {p.explanation && <p className="mt-2 text-sm">{p.explanation}</p>}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function MetricsCard({ view, lang }: { view: RelativeView; lang: Lang }) {
  const series = useMemo(() => (view.series ?? []).filter((s) => s.points?.some((p) => p.value !== null)), [view.series]);
  const [active, setActive] = useState<string | null>(null);
  if (series.length === 0) return null;
  const current = series.find((s) => s.param === active) ?? series.find((s) => s.param === "spo2") ?? series[0];

  return (
    <section className="space-y-3">
      <h3 className="font-display font-semibold">{t("metrics.title", lang)}</h3>
      <Tabs value={current.param} onValueChange={setActive}>
        <TabsList className="h-auto flex-wrap">
          {series.map((s) => (
            <TabsTrigger key={s.param} value={s.param}>
              {paramMeta(s.param).short}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <ParamChart key={current.param} series={current} lang={lang} />
    </section>
  );
}

function WeightCard({ patientId, lang }: { patientId: string; lang: Lang }) {
  const [weight, setWeight] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const value = Number.parseFloat(weight.replace(",", "."));
    if (!Number.isFinite(value) || value < 30 || value > 250) {
      setError(t("actions.weight_invalid", lang));
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await recordPatientMeasurement(patientId, value);
      setWeight("");
      toast.success(t("actions.weight_saved", lang));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Scale className="text-primary size-4" />
          {t("actions.weight_title", lang)}
        </CardTitle>
        <CardDescription>{t("actions.weight_desc", lang)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <form onSubmit={save} className="flex gap-2">
          <div className="relative flex-1">
            <Input
              type="number"
              inputMode="decimal"
              step="0.1"
              min={30}
              max={250}
              placeholder="72.5"
              value={weight}
              onChange={(e) => {
                setWeight(e.target.value);
                setError(null);
              }}
              className="pr-10"
              aria-label={t("actions.weight_title", lang)}
              required
            />
            <span className="text-muted-foreground absolute top-1/2 right-3 -translate-y-1/2 text-sm">kg</span>
          </div>
          <Button type="submit" disabled={saving}>
            {saving && <Loader2 className="animate-spin" />}
            {t("actions.weight_save_btn", lang)}
          </Button>
        </form>
        {error && <p className="text-risk text-sm">{error}</p>}
      </CardContent>
    </Card>
  );
}

function SosCard({ patientId, lang }: { patientId: string; lang: Lang }) {
  const [confirming, setConfirming] = useState(false);
  const [sending, setSending] = useState(false);
  const [sentAt, setSentAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const send = async () => {
    setSending(true);
    setError(null);
    try {
      await triggerEmergencySos(patientId);
      setSentAt(new Date().toISOString());
      setConfirming(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("actions.sos_card_error", lang));
    } finally {
      setSending(false);
    }
  };

  return (
    <Card className="border-risk/40 bg-risk-soft/40">
      <CardHeader>
        <CardTitle className="text-risk-ink flex items-center gap-2 text-base">
          <Siren className="text-risk size-4" />
          {t("actions.sos_card_title", lang)}
        </CardTitle>
        <CardDescription>{t("actions.sos_card_desc", lang)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {sentAt ? (
          <p className="text-risk-ink flex items-start gap-2 text-sm font-medium">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            {pick(lang, {
              uz: `SOS klinika navbatiga yuborildi (${formatDateTime(sentAt, lang)}). Ahvol og'ir bo'lsa, kutmasdan 103 ga qo'ng'iroq qiling.`,
              ru: `SOS отправлен в очередь клиники (${formatDateTime(sentAt, lang)}). Если состояние тяжёлое, не ждите и звоните 103.`,
              en: `SOS sent to the clinic queue (${formatDateTime(sentAt, lang)}). If the condition is serious, call 103 without waiting.`,
            })}
          </p>
        ) : (
          <Button variant="destructive" className="w-full" onClick={() => setConfirming(true)}>
            <Siren />
            {pick(lang, { uz: "Klinikaga SOS yuborish", ru: "Отправить SOS в клинику", en: "Send SOS to the clinic" })}
          </Button>
        )}
        <Button variant="outline" className="border-risk/40 text-risk w-full" asChild>
          <a href="tel:103">
            <Phone />
            {t("actions.emergency", lang)}
          </a>
        </Button>
      </CardContent>

      <Dialog open={confirming} onOpenChange={(open) => !sending && setConfirming(open)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="text-risk size-5" />
              {t("actions.sos_confirm_title", lang)}
            </DialogTitle>
            <DialogDescription>
              {pick(lang, {
                uz: "Signal bemor manzili bilan klinikaning navbatchi xodimiga yuboriladi. U 103 brigadasini chaqirishga qaror qiladi. Bu tez yordam avtomatik chaqirildi degani emas.",
                ru: "Сигнал с адресом пациента уйдёт дежурному сотруднику клиники, который решит, вызывать ли бригаду 103. Это не автоматический вызов скорой.",
                en: "The alert goes to the clinic's on-duty staff with the patient's address; they decide whether to call a 103 crew. It does not call an ambulance automatically.",
              })}
            </DialogDescription>
          </DialogHeader>
          {error && <p className="text-risk text-sm">{error}</p>}
          <DialogFooter>
            <Button variant="outline" disabled={sending} onClick={() => setConfirming(false)}>
              {t("actions.sos_cancel", lang)}
            </Button>
            <Button variant="destructive" disabled={sending} onClick={() => void send()}>
              {sending ? <Loader2 className="animate-spin" /> : <Siren />}
              {sending ? t("actions.sos_sending", lang) : t("actions.sos_confirm_btn", lang)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

function ContactCard({ view, lang }: { view: RelativeView; lang: Lang }) {
  const doctor = view.doctor_contact;
  const openTask = (view.tasks ?? []).find((task) => task.status !== "done");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Stethoscope className="text-primary size-4" />
          {t("actions.title", lang)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {doctor ? (
          <div>
            <p className="text-muted-foreground text-xs">{t("actions.doctor_name", lang)}</p>
            <p className="font-display font-semibold">{doctor.name}</p>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">
            {pick(lang, { uz: "Mas'ul shifokor hali biriktirilmagan.", ru: "Ответственный врач ещё не назначен.", en: "No responsible doctor assigned yet." })}
          </p>
        )}
        {view.trend?.recommendation_key && <p className="text-sm">{t(view.trend.recommendation_key, lang)}</p>}
        {openTask && (
          <Alert variant="attention">
            <AlertTitle>{t("actions.active_call_status", lang)}</AlertTitle>
            <AlertDescription>{t("actions.active_call_scheduled", lang)}</AlertDescription>
          </Alert>
        )}
        <div className="grid gap-2 sm:grid-cols-2">
          {doctor?.phone && (
            <Button asChild>
              <a href={`tel:${doctor.phone}`}>
                <Phone />
                {t("actions.call_doctor", lang)}
              </a>
            </Button>
          )}
          <Button variant="outline" asChild>
            <a href="https://t.me/WMAX_uz_bot" target="_blank" rel="noreferrer">
              <Send />
              {t("actions.telegram", lang)}
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
