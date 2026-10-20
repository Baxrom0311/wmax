import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { toast } from "sonner";
import {
  Ambulance,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  HeartPulse,
  Loader2,
  MapPin,
  Phone,
  Pill,
  RefreshCw,
  ShieldCheck,
  Siren,
  WifiOff,
} from "lucide-react";
import { EmptyState, PageHeader } from "@/components/app/states";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useNow } from "@/hooks/use-now";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import { acknowledgeSos, dispatchSos103, resolveSos } from "@/lib/clinic-api";
import { formatAgo, formatDateTime } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import type { SosEventItem, SosStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useClinicData, useClinicSession } from "./session";

const STATUS_VARIANT: Partial<Record<SosStatus, "risk" | "attention" | "good">> = {
  raised: "risk",
  acknowledged: "attention",
  dispatched: "good",
};

type Snapshot = Record<string, unknown>;

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function str(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function list(value: unknown): Snapshot[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "object" && item !== null ? (item as Snapshot) : { name: String(item) }));
}

function addressLine(addr: Snapshot, lang: ReturnType<typeof usePrefs>["lang"]) {
  const parts = [str(addr.region), str(addr.district), str(addr.mahalla), str(addr.street)].filter(Boolean);
  const house = str(addr.house) ?? (num(addr.house) !== null ? String(addr.house) : null);
  const flat = str(addr.flat) ?? (num(addr.flat) !== null ? String(addr.flat) : null);
  if (house) parts.push(`№${house}`);
  if (flat) parts.push(pick(lang, { uz: `xonadon ${flat}`, ru: `кв. ${flat}`, en: `flat ${flat}` }));
  return parts.join(", ");
}

export function SosPage() {
  const { lang } = usePrefs();
  const { isDemo } = useClinicSession();
  const { activeSos, sosStale, reloadSos } = useClinicData();
  const now = useNow(10000);
  const [params, setParams] = useSearchParams();
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const events = useMemo(
    () => [...activeSos].sort((a, b) => Date.parse(b.raised_at) - Date.parse(a.raised_at)),
    [activeSos],
  );
  const selectedId = params.get("id");
  const active = events.find((e) => e.id === selectedId) ?? events[0] ?? null;

  useEffect(() => {
    // A faster refresh while the dispatcher has this screen open.
    const id = window.setInterval(() => void reloadSos(), 6000);
    return () => window.clearInterval(id);
  }, [reloadSos]);

  const select = (id: string) => {
    const next = new URLSearchParams(params);
    next.set("id", id);
    setParams(next, { replace: true });
  };

  const run = async (event: SosEventItem, action: "ack" | "dispatch" | "resolve") => {
    setBusy(`${event.id}:${action}`);
    try {
      if (action === "ack") {
        await acknowledgeSos(event.id, isDemo);
        toast.success(pick(lang, { uz: "Chaqiruv qabul qilindi", ru: "Вызов принят", en: "Call acknowledged" }));
      } else if (action === "dispatch") {
        await dispatchSos103(event.id, { dispatch_method: "manual_call_103" }, isDemo);
        toast.success(pick(lang, { uz: "103 ga qo'ng'iroq qayd etildi", ru: "Звонок в 103 зафиксирован", en: "103 call recorded" }));
      } else {
        await resolveSos(event.id, notes[event.id]?.trim() || t("sos.default_resolution", lang), isDemo);
        toast.success(pick(lang, { uz: "Hodisa yopildi", ru: "Инцидент закрыт", en: "Incident closed" }));
      }
      await reloadSos();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  };

  const refresh = async () => {
    setRefreshing(true);
    await reloadSos();
    setRefreshing(false);
  };

  const statusLabel = (status: SosStatus) =>
    status === "raised" ? t("sos.status_raised", lang) : status === "acknowledged" ? t("sos.status_ack", lang) : t("sos.status_dispatched", lang);

  const sourceLabel = (source: SosEventItem["source"]) => {
    if (source === "watch_button") return t("sos.source_watch", lang);
    if (source === "auto_critical") return t("sos.source_auto", lang);
    if (source === "relative_portal") return pick(lang, { uz: "Oila portali", ru: "Портал семьи", en: "Family portal" });
    return pick(lang, { uz: "Telefon ilovasi", ru: "Мобильное приложение", en: "Phone app" });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("sos.title", lang)}
        description={t("sos.subtitle", lang)}
        actions={
          <Button variant="outline" size="sm" onClick={() => void refresh()} disabled={refreshing}>
            <RefreshCw className={cn(refreshing && "animate-spin")} />
            {t("sos.refresh", lang)}
          </Button>
        }
      />

      {sosStale && (
        <Alert variant="destructive">
          <WifiOff />
          <AlertTitle>{t("error.server_connection", lang)}</AlertTitle>
          <AlertDescription>
            {pick(lang, {
              uz: "SOS navbati yangilanmadi. Ekrandagi ro'yxat eskirgan bo'lishi mumkin; shoshilinch holatda 103 ga bevosita qo'ng'iroq qiling.",
              ru: "Очередь SOS не обновилась. Список может быть устаревшим; в экстренном случае звоните 103 напрямую.",
              en: "The SOS queue failed to refresh. The list may be stale; in an emergency call 103 directly.",
            })}
          </AlertDescription>
        </Alert>
      )}

      {events.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title={sosStale ? pick(lang, { uz: "Navbat holati noma'lum", ru: "Состояние очереди неизвестно", en: "Queue state unknown" }) : t("sos.no_active", lang)}
          description={sosStale ? undefined : t("sos.all_stable", lang)}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
          <div className="space-y-2">
            <p className="text-muted-foreground text-sm font-medium">{t("sos.queue", lang, { n: events.length })}</p>
            {events.map((event) => {
              const addr = (event.address_snapshot ?? {}) as Snapshot;
              const selected = active?.id === event.id;
              return (
                <button
                  key={event.id}
                  type="button"
                  onClick={() => select(event.id)}
                  className={cn(
                    "bg-card w-full rounded-xl border p-3 text-left transition-colors",
                    selected ? "border-risk ring-risk/20 ring-2" : "hover:border-risk/40",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-display truncate font-semibold">{event.patient_name ?? t("sos.unknown", lang)}</span>
                    <Badge variant={STATUS_VARIANT[event.status] ?? "nodata"}>{statusLabel(event.status)}</Badge>
                  </div>
                  <div className="text-muted-foreground mt-1 flex items-center justify-between gap-2 text-xs">
                    <span className="truncate">{str(addr.district) ?? sourceLabel(event.source)}</span>
                    <span className="tabular shrink-0">{formatAgo(event.raised_at, lang, now)}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {active && (
            <SosDetail
              key={active.id}
              event={active}
              lang={lang}
              busy={busy}
              note={notes[active.id] ?? ""}
              onNote={(v) => setNotes((prev) => ({ ...prev, [active.id]: v }))}
              onAction={(action) => void run(active, action)}
              statusLabel={statusLabel}
              sourceLabel={sourceLabel}
            />
          )}
        </div>
      )}
    </div>
  );
}

function SosDetail({
  event,
  lang,
  busy,
  note,
  onNote,
  onAction,
  statusLabel,
  sourceLabel,
}: {
  event: SosEventItem;
  lang: ReturnType<typeof usePrefs>["lang"];
  busy: string | null;
  note: string;
  onNote: (value: string) => void;
  onAction: (action: "ack" | "dispatch" | "resolve") => void;
  statusLabel: (status: SosStatus) => string;
  sourceLabel: (source: SosEventItem["source"]) => string;
}) {
  const addr = (event.address_snapshot ?? {}) as Snapshot;
  const clinical = (event.clinical_snapshot ?? {}) as Snapshot;
  const vitals = (event.vitals_snapshot ?? null) as Snapshot | null;
  const allergies = list(clinical.allergies);
  const meds = list(clinical.active_medications);
  const isBusy = (action: string) => busy === `${event.id}:${action}`;
  const anyBusy = busy?.startsWith(`${event.id}:`) ?? false;

  const spo2 = vitals ? num(vitals.spo2) : null;
  const hr = vitals ? num(vitals.hr) : null;
  const temp = vitals ? num(vitals.skin_temp) : null;
  const rr = vitals ? num(vitals.rr) : null;

  const vitalTiles: { label: string; value: string; danger: boolean; note: string }[] = [];
  if (spo2 !== null) vitalTiles.push({ label: "SpO₂", value: `${spo2}%`, danger: spo2 < 90, note: spo2 < 90 ? t("sos.danger_hypoxia", lang) : t("sos.normal", lang) });
  if (hr !== null) vitalTiles.push({ label: pick(lang, { uz: "Puls", ru: "Пульс", en: "Heart rate" }), value: `${hr} bpm`, danger: hr > 100, note: hr > 100 ? t("sos.danger_tachycardia", lang) : t("sos.normal", lang) });
  if (temp !== null) vitalTiles.push({ label: t("sos.skin_temp", lang), value: `${temp}°C`, danger: false, note: "" });
  if (rr !== null) vitalTiles.push({ label: t("sos.rr", lang), value: `${rr}/min`, danger: rr > 22, note: rr > 22 ? t("sos.accelerated", lang) : t("sos.normal", lang) });

  const bloodGroup = str(clinical.blood_group);
  const rh = str(clinical.rh);
  const diagnosis = str(clinical.primary_diagnosis);
  const phone = str(clinical.phone) ?? str(addr.phone);
  const line = addressLine(addr, lang);

  return (
    <div className="space-y-4">
      <Card className="border-risk/40">
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="bg-risk text-white flex size-9 items-center justify-center rounded-full">
                  <Siren className="size-5" />
                </span>
                <h2 className="font-display text-xl font-bold">{event.patient_name ?? t("sos.unknown", lang)}</h2>
              </div>
              <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
                <span>{formatDateTime(event.raised_at, lang)}</span>
                <span>{sourceLabel(event.source)}</span>
                <span>
                  {t("sos.blood_group", lang)} {bloodGroup ?? t("sos.unknown", lang)}
                  {rh ? ` (${rh})` : ""}
                </span>
              </div>
              {diagnosis && (
                <p className="text-sm">
                  <span className="text-muted-foreground">{t("sos.diagnosis_label", lang)}</span> {diagnosis}
                </p>
              )}
            </div>
            <Badge variant={STATUS_VARIANT[event.status] ?? "nodata"} className="text-sm">
              {statusLabel(event.status)}
            </Badge>
          </div>

          <div className="flex flex-wrap gap-2">
            {event.status === "raised" && (
              <Button variant="outline" disabled={anyBusy} onClick={() => onAction("ack")}>
                {isBusy("ack") ? <Loader2 className="animate-spin" /> : <CheckCircle2 />}
                {t("sos.btn_ack", lang)}
              </Button>
            )}
            {event.status !== "dispatched" && (
              <Button variant="destructive" disabled={anyBusy} onClick={() => onAction("dispatch")}>
                {isBusy("dispatch") ? <Loader2 className="animate-spin" /> : <Ambulance />}
                {t("sos.btn_dispatch103", lang)}
              </Button>
            )}
            <Button variant="outline" asChild>
              <a href="tel:103">
                <Phone />
                103
              </a>
            </Button>
            <Button variant="ghost" asChild>
              <Link to={`/doctor/patients/${event.patient_id}`}>{t("handoffs.btn_chart", lang)}</Link>
            </Button>
          </div>
          {event.status === "dispatched" && (
            <p className="text-muted-foreground text-xs">
              {pick(lang, {
                uz: "WMAX 103 ni avtomatik chaqirmaydi; bu faqat xodim qo'ng'iroq qilganini qayd etadi. Brigada chiqqanini 103 bilan tasdiqlang.",
                ru: "WMAX не вызывает 103 автоматически; здесь лишь фиксируется звонок сотрудника. Выезд бригады подтверждайте в 103.",
                en: "WMAX never calls 103 automatically; this only records that staff called. Confirm the crew is on its way with 103.",
              })}
              {event.dispatched_at ? ` · ${formatDateTime(event.dispatched_at, lang)}` : ""}
              {event.dispatch_ref ? ` · ${event.dispatch_ref}` : ""}
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <HeartPulse className="text-risk size-4" />
              {t("sos.telemetry_title", lang)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {vitalTiles.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                {pick(lang, { uz: "Chaqiruv paytidagi o'lchovlar yo'q.", ru: "Нет измерений на момент вызова.", en: "No readings captured with this call." })}
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {vitalTiles.map((v) => (
                  <div key={v.label} className={cn("rounded-lg border p-3", v.danger && "border-risk/40 bg-risk-soft/50")}>
                    <p className="text-muted-foreground text-xs">{v.label}</p>
                    <p className={cn("font-display tabular text-xl font-bold", v.danger && "text-risk")}>{v.value}</p>
                    {v.note && (
                      <p className={cn("text-xs", v.danger ? "text-risk" : "text-muted-foreground")}>
                        {v.danger && <AlertTriangle className="mr-1 inline size-3" />}
                        {v.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MapPin className="text-primary size-4" />
              {t("sos.address_title", lang)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="font-medium">{line || pick(lang, { uz: "Manzil kiritilmagan", ru: "Адрес не указан", en: "No address on file" })}</p>
            {str(addr.landmark) && (
              <p>
                <span className="text-muted-foreground">{t("sos.landmark", lang)}</span> {str(addr.landmark)}
              </p>
            )}
            {str(addr.entrance_note) && (
              <p>
                <span className="text-muted-foreground">{t("sos.entrance", lang)}</span> {str(addr.entrance_note)}
              </p>
            )}
            {phone && (
              <a className="text-primary inline-flex items-center gap-1 hover:underline" href={`tel:${phone}`}>
                <Phone className="size-3.5" />
                {phone}
              </a>
            )}
            {event.device_lat != null && event.device_lon != null && (
              <div className="bg-muted/50 flex flex-wrap items-center justify-between gap-2 rounded-lg p-2">
                <span className="tabular text-xs">
                  GPS: {event.device_lat.toFixed(6)}, {event.device_lon.toFixed(6)}
                </span>
                <Button size="sm" variant="outline" asChild>
                  <a href={`https://maps.google.com/?q=${event.device_lat},${event.device_lon}`} target="_blank" rel="noreferrer">
                    {t("sos.open_map", lang)}
                    <ExternalLink />
                  </a>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Pill className="text-primary size-4" />
            {t("sos.clinical_title", lang)}
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs font-medium">{t("sos.allergies_label", lang)}</p>
            {allergies.length ? (
              <div className="flex flex-wrap gap-1.5">
                {allergies.map((a, i) => (
                  <Badge key={i} variant="risk">
                    <AlertTriangle />
                    {str(a.substance) ?? str(a.name) ?? "?"}
                    {str(a.reaction) ? ` (${str(a.reaction)})` : ""}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm">{t("detail.none", lang)}</p>
            )}
          </div>
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs font-medium">{t("sos.meds_label", lang)}</p>
            {meds.length ? (
              <ul className="space-y-1 text-sm">
                {meds.map((m, i) => (
                  <li key={i}>
                    <span className="font-medium">{str(m.name) ?? "?"}</span>
                    <span className="text-muted-foreground">
                      {str(m.dose) ? ` · ${str(m.dose)}` : ""}
                      {str(m.frequency) ? ` · ${str(m.frequency)}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm">{t("sos.no_meds", lang)}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CheckCircle2 className="text-good size-4" />
            {t("sos.resolution_title", lang)}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea value={note} onChange={(e) => onNote(e.target.value)} placeholder={t("sos.resolution_placeholder", lang)} rows={3} />
          <Button disabled={anyBusy} onClick={() => onAction("resolve")}>
            {isBusy("resolve") ? <Loader2 className="animate-spin" /> : <CheckCircle2 />}
            {t("sos.btn_resolve", lang)}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
