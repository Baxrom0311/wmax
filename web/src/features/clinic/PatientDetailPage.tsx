import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  ExternalLink,
  Info,
  Lightbulb,
  Loader2,
  LogOut,
  MapPin,
  Pill,
  Printer,
  Stethoscope,
  User,
} from "lucide-react";
import { LevelBadge, LevelDot } from "@/components/app/level-badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/app/states";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useNow } from "@/hooks/use-now";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import {
  approveBaseline,
  confirmTask,
  dischargePatient,
  fetchNurseHandover,
  fetchPatientDetail,
  fetchPatientFullProfile,
} from "@/lib/clinic-api";
import { formatAgo, formatCountdown, formatDate, formatDateTime, msUntil } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import type { NurseHandoverSBAR, PatientDetail, PatientFullProfile } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ConfirmTaskDialog } from "./ConfirmTaskDialog";
import { NurseHandoverPanel } from "./NurseHandoverPanel";
import { ParamChart } from "./ParamChart";
import { useClinicData, useClinicSession } from "./session";

function errText(err: unknown) {
  return err instanceof Error ? err.message : String(err);
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-muted-foreground text-xs">{label.replace(/:$/, "")}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  );
}

export function PatientDetailPage() {
  const { id = "" } = useParams();
  const { lang } = usePrefs();
  const { isDemo, logout } = useClinicSession();
  const { revision, reloadPatients } = useClinicData();
  const now = useNow(15000);

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<PatientFullProfile | null>(null);
  const [profileError, setProfileError] = useState(false);
  const [handover, setHandover] = useState<NurseHandoverSBAR | null | undefined>(undefined);
  const [handoverLoading, setHandoverLoading] = useState(false);
  const [dialog, setDialog] = useState<"confirm" | "approve" | "discharge" | null>(null);
  const [busy, setBusy] = useState(false);

  const handleAuth = useCallback(
    (err: unknown) => {
      if (errText(err) === "UNAUTHORIZED") {
        logout();
        return true;
      }
      return false;
    },
    [logout],
  );

  const load = useCallback(async () => {
    try {
      const data = await fetchPatientDetail(id, isDemo);
      setPatient(data);
      setError(null);
    } catch (err) {
      if (!handleAuth(err)) setError(errText(err));
    }
  }, [id, isDemo, handleAuth]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- detail refetches on route change and realtime ticks
    void load();
  }, [load, revision]);

  useEffect(() => {
    let alive = true;
    fetchPatientFullProfile(id, isDemo)
      .then((p) => alive && (setProfile(p), setProfileError(false)))
      .catch((err) => alive && !handleAuth(err) && setProfileError(true));
    return () => {
      alive = false;
    };
  }, [id, isDemo, handleAuth]);

  const loadHandover = useCallback(async () => {
    setHandoverLoading(true);
    try {
      setHandover(await fetchNurseHandover(id, isDemo));
    } catch (err) {
      if (!handleAuth(err)) setHandover(null);
    } finally {
      setHandoverLoading(false);
    }
  }, [id, isDemo, handleAuth]);

  const run = async (action: () => Promise<void>, success: string) => {
    setBusy(true);
    try {
      await action();
      toast.success(success);
      setDialog(null);
      await Promise.all([load(), reloadPatients(true)]);
    } catch (err) {
      if (!handleAuth(err)) toast.error(errText(err));
    } finally {
      setBusy(false);
    }
  };

  if (error && !patient) {
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorState title={t("error.server_connection", lang)} description={error} onRetry={() => void load()} retryLabel={t("error.retry", lang)} />
      </div>
    );
  }
  if (!patient) return <LoadingState label={t("app.loading", lang)} />;

  const activeTask = patient.tasks.find((task) => task.status !== "done" && task.type === "active_call");
  const remaining = activeTask ? msUntil(activeTask.due_at, now) : null;
  const overdue = remaining !== null && remaining <= 0;
  const urgent = remaining !== null && remaining > 0 && remaining < 4 * 3600 * 1000;
  const code = `K-2026/${patient.id.replace(/-/g, "").slice(0, 4).toUpperCase()}`;

  return (
    <div className="space-y-6">
      <BackLink />

      {/* Clinical passport */}
      <Card className="gap-4">
        <CardHeader className="gap-3">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0 space-y-2">
              <div className="text-muted-foreground flex items-center gap-2 text-xs">
                <span className="font-mono">№ {code}</span>
                <span>·</span>
                <span>
                  {pick(lang, { uz: "Oxirgi o'lchov", ru: "Последнее измерение", en: "Last reading" })}: {formatAgo(patient.last_reading_at, lang, now)}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-display text-2xl font-bold tracking-tight">{patient.full_name}</h1>
                <LevelBadge level={patient.level} label={t(`state.${patient.level}`, lang)} className="text-sm" />
              </div>
            </div>
            <div className="no-print flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={() => window.print()}>
                <Printer />
                {t("detail.print", lang)}
              </Button>
              {patient.phase === "learning" && !patient.baseline_approved && (
                <Button size="sm" onClick={() => setDialog("approve")}>
                  <CheckCircle2 />
                  {t("detail.approve_baseline", lang)}
                </Button>
              )}
              {!activeTask && (
                <Button variant="outline" size="sm" onClick={() => setDialog("discharge")}>
                  <LogOut />
                  {t("detail.discharge_action", lang)}
                </Button>
              )}
              {patient.baseline_approved && (
                <Badge variant="good" className="h-8 px-2.5">
                  <CheckCircle2 />
                  {t("detail.baseline_approved", lang)}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Field label={t("detail.passport_age_sex", lang)}>
              {t("patients.age_years", lang, { age: patient.age })}, {patient.sex === "m" ? t("patients.sex_male", lang) : t("patients.sex_female", lang)}
            </Field>
            <Field label={t("detail.passport_address", lang)}>{patient.district}</Field>
            <Field label={t("detail.passport_phase", lang)}>
              <Badge variant="secondary">{t(`detail.phase_${patient.phase}`, lang)}</Badge>
            </Field>
            <Field label={pick(lang, { uz: "Kompozit og'ish", ru: "Композитное отклонение", en: "Composite deviation" })}>
              <span className="tabular">{patient.composite_score.toFixed(1)}σ</span>
            </Field>
            <div className="sm:col-span-2 lg:col-span-4">
              <Field label={t("detail.passport_diag", lang)}>
                <span className="font-normal leading-relaxed">{patient.diagnosis}</span>
              </Field>
            </div>
          </dl>
        </CardContent>
      </Card>

      {activeTask && (
        <Alert variant={overdue ? "destructive" : urgent ? "attention" : "info"} className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <Clock />
          <div className="flex-1">
            <AlertTitle className="flex flex-wrap items-center gap-2">
              {t("detail.emergency_patrol_call", lang)}
              {overdue && <Badge variant="risk">{t("detail.overdue", lang)}</Badge>}
              {urgent && <Badge variant="attention">{t("detail.urgent_sub_4h", lang)}</Badge>}
            </AlertTitle>
            <AlertDescription>
              <span className="tabular text-base font-semibold">{remaining !== null ? formatCountdown(remaining, lang) : "—"}</span>
              <span>{t("detail.active_call_desc", lang)}</span>
            </AlertDescription>
          </div>
          <Button className="no-print shrink-0" onClick={() => setDialog("confirm")}>
            <ClipboardCheck />
            {t("detail.submit_report_btn", lang)}
          </Button>
        </Alert>
      )}

      <Tabs defaultValue="telemetry" onValueChange={(v) => v === "nurse" && handover === undefined && !handoverLoading && void loadHandover()}>
        <TabsList className="no-print w-full justify-start sm:w-fit">
          <TabsTrigger value="telemetry">
            <Activity />
            {t("detail.tab_telemetry", lang)}
          </TabsTrigger>
          <TabsTrigger value="profile">
            <User />
            {t("detail.tab_profile", lang)}
          </TabsTrigger>
          <TabsTrigger value="medications">
            <Pill />
            {t("detail.tab_medications", lang)}
          </TabsTrigger>
          <TabsTrigger value="risks">
            <AlertTriangle />
            {t("detail.tab_risks", lang)}
          </TabsTrigger>
          <TabsTrigger value="nurse">
            <Stethoscope />
            {t("detail.tab_nurse", lang)}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="telemetry" className="space-y-6">
          {patient.prognosis && (
            <Card className="gap-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="text-primary size-4" />
                  {t("detail.cdss_badge", lang)}
                </CardTitle>
                <CardDescription>{t(`trend.${patient.trend.direction}`, lang)} · {t(patient.trend.recommendation_key, lang)}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="bg-muted/50 rounded-lg p-4 text-sm leading-relaxed">{patient.prognosis.summary}</div>
                  <div className="bg-accent/60 text-accent-foreground rounded-lg p-4 text-sm leading-relaxed">
                    <span className="font-semibold">{t("detail.recommended_actions", lang)} </span>
                    {patient.prognosis.recommendation}
                  </div>
                </div>
                {patient.prognosis.uncertainty_note && (
                  <p className="text-muted-foreground flex items-start gap-2 text-xs">
                    <Info className="mt-0.5 size-3.5 shrink-0" />
                    {patient.prognosis.uncertainty_note}
                  </p>
                )}
                {patient.problems && patient.problems.length > 0 && (
                  <div className="divide-y rounded-lg border">
                    {patient.problems.map((pr, i) => (
                      <div key={i} className="grid gap-1 p-3 text-sm sm:grid-cols-[10rem_7rem_1fr] sm:items-center sm:gap-4">
                        <span className="font-medium">{pr.label}</span>
                        <Badge variant={pr.severity === "severe" ? "risk" : pr.severity === "moderate" ? "attention" : "secondary"}>{pr.deviation}</Badge>
                        <span className="text-muted-foreground">
                          <span className="tabular text-foreground">{t("detail.measured_vs_baseline", lang, { curr: pr.current_value, base: pr.baseline_range })}</span>
                          {" — "}
                          {pr.explanation}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <section className="space-y-3">
            <div>
              <h2 className="font-display text-lg font-semibold">{pick(lang, { uz: "Telemetriya grafiklari", ru: "Графики телеметрии", en: "Telemetry charts" })}</h2>
              <p className="text-muted-foreground text-xs">{t("detail.vitals_shaded_note", lang)}</p>
            </div>
            {patient.series.length === 0 ? (
              <EmptyState icon={Activity} title={pick(lang, { uz: "Hali o'lchovlar yo'q", ru: "Измерений пока нет", en: "No readings yet" })} />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {patient.series.map((s) => (
                  <ParamChart key={s.param} series={s} lang={lang} />
                ))}
              </div>
            )}
          </section>

          {patient.alerts.length > 0 && (
            <Card className="gap-0 py-0">
              <CardHeader className="border-b py-4">
                <CardTitle className="text-base">{t("detail.alerts_heading", lang)}</CardTitle>
              </CardHeader>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-5">{pick(lang, { uz: "Vaqt", ru: "Время", en: "Time" })}</TableHead>
                    <TableHead>{pick(lang, { uz: "Sabab", ru: "Причина", en: "Reason" })}</TableHead>
                    <TableHead className="pr-5 text-right">Z</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patient.alerts.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="pl-5 whitespace-nowrap">
                        <span className="flex items-center gap-2">
                          <LevelDot level={a.level} />
                          <span className="tabular text-xs">{formatDateTime(a.ts, lang)}</span>
                        </span>
                      </TableCell>
                      <TableCell className="text-sm">
                        {a.reason}
                        {a.anomaly_score !== null && (
                          <span className="text-muted-foreground ml-2 text-xs">
                            ({t("detail.isolation_forest_idx", lang, { score: Math.round(a.anomaly_score * 100) })})
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="tabular pr-5 text-right font-semibold">{a.composite_score}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="profile">
          <ProfileSection profile={profile} failed={profileError} />
        </TabsContent>

        <TabsContent value="medications">
          {!profile ? (
            <ProfileSection profile={null} failed={profileError} />
          ) : profile.medications.length === 0 ? (
            <EmptyState icon={Pill} title={pick(lang, { uz: "Dorilar kiritilmagan", ru: "Препараты не внесены", en: "No medications recorded" })} />
          ) : (
            <Card className="gap-0 py-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-5">{t("detail.med_th_name", lang)}</TableHead>
                    <TableHead>{t("detail.med_th_dose", lang)}</TableHead>
                    <TableHead>{t("detail.med_th_freq", lang)}</TableHead>
                    <TableHead>{t("detail.med_th_param", lang)}</TableHead>
                    <TableHead className="pr-5">{t("detail.med_th_status", lang)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profile.medications.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="pl-5 font-medium">{m.name}</TableCell>
                      <TableCell>{m.dose || "—"}</TableCell>
                      <TableCell>{m.frequency || "—"}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(m.affects_params || {}).map(([param, eff]) => (
                            <Badge key={param} variant="outline">
                              {param.toUpperCase()} {eff === "lowers" ? "↓" : "↑"}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="pr-5">
                        <Badge variant={m.stopped_at ? "secondary" : "good"}>{m.stopped_at ? t("detail.med_stopped", lang) : t("detail.med_active", lang)}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="risks">
          {!profile ? (
            <ProfileSection profile={null} failed={profileError} />
          ) : (
            <div className="grid gap-4 lg:grid-cols-3">
              <Card className="gap-3">
                <CardHeader>
                  <CardTitle className="text-base">{t("detail.allergies_heading", lang)}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {profile.allergies.length === 0 ? (
                    <p className="text-muted-foreground text-sm">{t("detail.none", lang)}</p>
                  ) : (
                    profile.allergies.map((al) => (
                      <div key={al.id} className={cn("rounded-lg border p-3", al.severity === "severe" || al.severity === "life_threatening" ? "border-risk/40 bg-risk-soft/50" : "bg-attention-soft/40 border-attention/30")}>
                        <div className="flex items-center justify-between gap-2">
                          <strong className="text-sm">{al.substance}</strong>
                          <Badge variant={al.severity === "mild" ? "secondary" : al.severity === "moderate" ? "attention" : "risk"}>{al.severity.replace("_", " ")}</Badge>
                        </div>
                        {al.reaction && <p className="text-muted-foreground mt-1 text-xs">{al.reaction}</p>}
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
              <Card className="gap-3">
                <CardHeader>
                  <CardTitle className="text-base">{t("detail.risk_factors", lang)}</CardTitle>
                </CardHeader>
                <CardContent>
                  {!profile.risk_factors ? (
                    <p className="text-muted-foreground text-sm">{t("detail.no_data", lang)}</p>
                  ) : (
                    <dl className="divide-y text-sm">
                      {[
                        [t("detail.lives_alone", lang), profile.risk_factors.lives_alone ? t("detail.yes", lang) : t("detail.no", lang)],
                        [t("detail.mobility", lang), profile.risk_factors.mobility],
                        [t("detail.diabetes", lang), profile.risk_factors.diabetes ? t("detail.yes", lang) : t("detail.no", lang)],
                        [t("detail.ckd", lang), profile.risk_factors.ckd ? t("detail.yes", lang) : t("detail.no", lang)],
                        [t("detail.smoking", lang), profile.risk_factors.smoking],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-3 py-2">
                          <dt className="text-muted-foreground">{k.replace(/:$/, "")}</dt>
                          <dd className="font-medium">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                </CardContent>
              </Card>
              <Card className="gap-3">
                <CardHeader>
                  <CardTitle className="text-base">{t("detail.weight_heading", lang)}</CardTitle>
                </CardHeader>
                <CardContent>
                  {profile.measurements.length === 0 ? (
                    <p className="text-muted-foreground text-sm">{t("detail.no_data", lang)}</p>
                  ) : (
                    <ul className="divide-y text-sm">
                      {profile.measurements.map((m) => (
                        <li key={m.id} className="flex items-center justify-between gap-3 py-2">
                          <span className="text-muted-foreground">{formatDate(m.measured_at, lang)}</span>
                          <span className="tabular font-semibold">{m.weight_kg ? `${m.weight_kg} kg` : "—"}</span>
                          {m.systolic_bp && m.diastolic_bp ? (
                            <span className="tabular text-muted-foreground text-xs">
                              {m.systolic_bp}/{m.diastolic_bp}
                            </span>
                          ) : null}
                          <Badge variant="outline" className="font-normal">
                            {m.source}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="nurse">
          {handoverLoading && handover === undefined ? (
            <LoadingState label={t("detail.sbar_loading", lang)} />
          ) : handover ? (
            <NurseHandoverPanel key={handover.generated_at ?? "h"} handover={handover} refreshing={handoverLoading} onRefresh={() => void loadHandover()} lang={lang} />
          ) : (
            <EmptyState
              icon={Building2}
              title={t("detail.sbar_empty_title", lang)}
              description={t("detail.sbar_empty_desc", lang)}
              action={
                <Button variant="outline" onClick={() => void loadHandover()} disabled={handoverLoading}>
                  {handoverLoading && <Loader2 className="animate-spin" />}
                  {t("error.retry", lang)}
                </Button>
              }
            />
          )}
        </TabsContent>
      </Tabs>

      <ConfirmTaskDialog
        open={dialog === "confirm"}
        onOpenChange={(open) => setDialog(open ? "confirm" : null)}
        lang={lang}
        onConfirm={async (note) => {
          if (!activeTask) return;
          await run(() => confirmTask(activeTask.id, note, isDemo), t("confirm_modal.toast_confirmed", lang));
        }}
      />

      <Dialog open={dialog === "approve"} onOpenChange={(open) => !busy && setDialog(open ? "approve" : null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("detail.approve_modal_title", lang)}</DialogTitle>
            <DialogDescription>{t("detail.approve_modal_desc", lang)}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialog(null)} disabled={busy}>
              {t("detail.approve_modal_cancel", lang)}
            </Button>
            <Button onClick={() => void run(() => approveBaseline(patient.id, isDemo), t("toast.baseline_success", lang))} disabled={busy}>
              {busy && <Loader2 className="animate-spin" />}
              {t("detail.approve_modal_submit", lang)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === "discharge"} onOpenChange={(open) => !busy && setDialog(open ? "discharge" : null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("detail.discharge_confirm_title", lang)}</DialogTitle>
            <DialogDescription>{t("detail.discharge_confirm_desc", lang)}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialog(null)} disabled={busy}>
              {t("detail.discharge_modal_cancel", lang)}
            </Button>
            <Button onClick={() => void run(() => dischargePatient(patient.id, isDemo), t("toast.discharge_success", lang))} disabled={busy}>
              {busy && <Loader2 className="animate-spin" />}
              {t("detail.discharge_confirm_submit", lang)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function BackLink() {
  const { lang } = usePrefs();
  return (
    <Button variant="ghost" size="sm" className="no-print -ml-2" asChild>
      <Link to="/doctor">
        <ArrowLeft />
        {t("detail.back", lang).replace(/^←\s*/, "")}
      </Link>
    </Button>
  );
}

function ProfileSection({ profile, failed }: { profile: PatientFullProfile | null; failed: boolean }) {
  const { lang } = usePrefs();
  if (!profile) {
    return failed ? (
      <EmptyState icon={AlertTriangle} title={pick(lang, { uz: "Profilni yuklab bo'lmadi", ru: "Не удалось загрузить профиль", en: "Could not load the profile" })} />
    ) : (
      <LoadingState label={t("app.loading", lang)} />
    );
  }
  if (profile.addresses.length === 0) {
    return <EmptyState icon={MapPin} title={pick(lang, { uz: "Manzil kiritilmagan", ru: "Адрес не указан", en: "No address on file" })} />;
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {profile.addresses.map((addr) => (
        <Card key={addr.id} className={cn("gap-3", addr.is_primary && "border-primary/40")}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="uppercase">
                {addr.kind}
              </Badge>
              {addr.is_primary && <Badge>{t("detail.primary_badge", lang)}</Badge>}
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="font-medium">
              {[addr.region, addr.district, addr.street].filter(Boolean).join(", ")}
              {addr.house ? ` №${addr.house}` : ""}
              {addr.flat ? `, ${addr.flat}-xonadon` : ""}
            </p>
            {addr.mahalla && (
              <p>
                <span className="text-muted-foreground">Mahalla: </span>
                {addr.mahalla}
              </p>
            )}
            {addr.landmark && (
              <p className="bg-attention-soft/60 rounded-md px-2 py-1">
                <span className="text-muted-foreground">{t("sos.landmark", lang)} </span>
                {addr.landmark}
              </p>
            )}
            {addr.entrance_note && (
              <p>
                <span className="text-muted-foreground">{t("sos.entrance", lang)} </span>
                {addr.entrance_note}
              </p>
            )}
            {addr.lat != null && addr.lon != null && (
              <Button variant="outline" size="sm" asChild>
                <a href={`https://maps.google.com/?q=${addr.lat},${addr.lon}`} target="_blank" rel="noopener noreferrer">
                  {t("detail.map_view", lang)}
                  <ExternalLink />
                </a>
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
