import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";
import { CheckCircle2, ChevronRight, ClipboardCheck, ClipboardList, Clock, Eye, Loader2, RefreshCw } from "lucide-react";
import { LevelDot } from "@/components/app/level-badge";
import { EmptyState, ErrorState, PageHeader } from "@/components/app/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useNow } from "@/hooks/use-now";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import { acknowledgeTask, completeTask, fetchTasks } from "@/lib/clinic-api";
import { formatAgo, formatCountdown, formatDateTime, msUntil } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import type { Task, TaskStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ConfirmTaskDialog } from "./ConfirmTaskDialog";
import { useClinicData, useClinicSession } from "./session";

type Filter = "open" | "pending" | "seen" | "overdue" | "done" | "all";

const PENDING: TaskStatus[] = ["created", "sent"];

function isOverdue(task: Task, now: number) {
  if (task.status === "overdue") return true;
  if (task.status === "done") return false;
  const left = msUntil(task.due_at, now);
  return left !== null && left <= 0;
}

function matches(task: Task, filter: Filter, now: number) {
  switch (filter) {
    case "open":
      return task.status !== "done";
    case "pending":
      return PENDING.includes(task.status) && !isOverdue(task, now);
    case "seen":
      return task.status === "seen" && !isOverdue(task, now);
    case "overdue":
      return isOverdue(task, now);
    case "done":
      return task.status === "done";
    default:
      return true;
  }
}

export function TasksPage() {
  const { lang } = usePrefs();
  const { isDemo, user } = useClinicSession();
  const { patients, revision, reloadPatients } = useClinicData();
  const now = useNow(15000);
  const isNurse = user?.role === "nurse";

  const [tasks, setTasks] = useState<Task[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("open");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [completing, setCompleting] = useState<Task | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchTasks(undefined, isDemo);
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoaded(true);
    }
  }, [isDemo]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- task list hydrates from the API and on realtime ticks
    void load();
  }, [load, revision]);

  const patientById = useMemo(() => new Map(patients.map((p) => [p.id, p])), [patients]);

  const counts = useMemo(() => {
    const c: Record<Filter, number> = { open: 0, pending: 0, seen: 0, overdue: 0, done: 0, all: tasks.length };
    for (const task of tasks) {
      for (const f of ["open", "pending", "seen", "overdue", "done"] as Filter[]) if (matches(task, f, now)) c[f] += 1;
    }
    return c;
  }, [tasks, now]);

  const visible = useMemo(
    () =>
      tasks
        .filter((task) => matches(task, filter, now))
        .sort((a, b) => {
          if (a.status === "done" && b.status !== "done") return 1;
          if (b.status === "done" && a.status !== "done") return -1;
          const da = a.due_at ? Date.parse(a.due_at) : Number.MAX_SAFE_INTEGER;
          const db = b.due_at ? Date.parse(b.due_at) : Number.MAX_SAFE_INTEGER;
          return da - db;
        }),
    [tasks, filter, now],
  );

  const handleAck = async (task: Task) => {
    setBusyId(task.id);
    try {
      await acknowledgeTask(task.id, isDemo);
      toast.success(pick(lang, { uz: "Vazifa qabul qilindi", ru: "Задача принята", en: "Task acknowledged" }));
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleComplete = async (note: string) => {
    if (!completing) return;
    const task = completing;
    setBusyId(task.id);
    try {
      await completeTask(task.id, note, isDemo);
      toast.success(t("confirm_modal.toast_confirmed", lang));
      setCompleting(null);
      await Promise.all([load(), reloadPatients(true)]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  };

  const typeLabel = (task: Task) => {
    switch (task.type) {
      case "active_call":
        return t("patients.task_active_call", lang);
      case "red_alert":
        return t("patients.task_red_alert", lang);
      case "clinical":
        return pick(lang, { uz: "Klinik vazifa", ru: "Клиническая задача", en: "Clinical task" });
      default:
        return pick(lang, { uz: "Texnik vazifa", ru: "Техническая задача", en: "Technical task" });
    }
  };

  const statusBadge = (task: Task) => {
    if (task.status === "done") return <Badge variant="good">{t("patients.done", lang)}</Badge>;
    if (isOverdue(task, now)) return <Badge variant="risk">{t("patients.overdue", lang)}</Badge>;
    if (task.status === "seen") return <Badge variant="attention">{pick(lang, { uz: "Qabul qilingan", ru: "Принята", en: "Acknowledged" })}</Badge>;
    return <Badge variant="nodata">{pick(lang, { uz: "Qabul kutilmoqda", ru: "Ожидает принятия", en: "Awaiting acknowledgement" })}</Badge>;
  };

  const FILTERS: { key: Filter; label: string }[] = [
    { key: "open", label: pick(lang, { uz: "Ochiq", ru: "Открытые", en: "Open" }) },
    { key: "pending", label: t("handoffs.kpi_pending", lang) },
    { key: "seen", label: t("handoffs.kpi_active", lang) },
    { key: "overdue", label: t("patients.overdue", lang) },
    { key: "done", label: t("handoffs.kpi_completed", lang) },
    { key: "all", label: pick(lang, { uz: "Barchasi", ru: "Все", en: "All" }) },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={isNurse ? t("handoffs.title_nurse", lang) : pick(lang, { uz: "Vazifalar", ru: "Задачи", en: "Tasks" })}
        description={pick(lang, {
          uz: "Aktiv chaqiruvlar va qizil signal bo'yicha mas'ul vazifalar. Muddat o'tsa, vazifa kechikkan deb belgilanadi.",
          ru: "Активные вызовы и задачи по красным сигналам. По истечении срока задача помечается как просроченная.",
          en: "Active calls and red-alert follow-ups. A task is marked overdue once its deadline passes.",
        })}
        actions={
          <Button variant="outline" size="sm" onClick={() => void load()}>
            <RefreshCw />
            {t("sos.refresh", lang)}
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {(
          [
            ["pending", "text-foreground", ClipboardList],
            ["seen", "text-attention", Eye],
            ["overdue", "text-risk", Clock],
            ["done", "text-good", CheckCircle2],
          ] as const
        ).map(([key, tone, Icon]) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilter(key)}
            className={cn(
              "bg-card hover:border-primary/40 rounded-xl border p-4 text-left transition-colors",
              filter === key && "border-primary ring-primary/20 ring-2",
            )}
          >
            <div className="text-muted-foreground flex items-center justify-between text-xs font-medium">
              {FILTERS.find((f) => f.key === key)?.label}
              <Icon className={cn("size-4", tone)} />
            </div>
            <div className={cn("font-display tabular mt-1 text-2xl font-bold", tone)}>{loaded ? counts[key] : "–"}</div>
          </button>
        ))}
      </div>

      <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
        <TabsList className="h-auto flex-wrap">
          {FILTERS.map((f) => (
            <TabsTrigger key={f.key} value={f.key}>
              {f.label}
              <span className="text-muted-foreground tabular ml-1 text-xs">{counts[f.key]}</span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {error && !tasks.length ? (
        <ErrorState title={t("error.server_connection", lang)} description={error} onRetry={() => void load()} retryLabel={t("error.retry", lang)} />
      ) : !loaded ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title={t("handoffs.empty_title", lang)} description={t("handoffs.empty_desc", lang)} />
      ) : (
        <div className="space-y-3">
          {error && (
            <p className="text-risk text-xs">
              {pick(lang, { uz: "Ro'yxat yangilanmadi, oxirgi ma'lumot ko'rsatilmoqda.", ru: "Список не обновился, показаны последние данные.", en: "Refresh failed; showing the last loaded list." })}
            </p>
          )}
          {visible.map((task) => {
            const patient = patientById.get(task.patient_id);
            const left = msUntil(task.due_at, now);
            const overdue = isOverdue(task, now);
            return (
              <Card key={task.id} className={cn("py-0", overdue && "border-risk/40")}>
                <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      {patient && <LevelDot level={patient.level} pulse={patient.level === "red"} />}
                      <Link to={`/doctor/patients/${task.patient_id}`} className="font-display truncate font-semibold hover:underline">
                        {patient?.full_name ?? pick(lang, { uz: "Bemor", ru: "Пациент", en: "Patient" })}
                      </Link>
                      {statusBadge(task)}
                      <Badge variant="outline">{typeLabel(task)}</Badge>
                    </div>
                    <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-xs">
                      {patient && <span>{patient.diagnosis}</span>}
                      {patient && <span>{patient.district}</span>}
                      <span>
                        {pick(lang, { uz: "Yaratilgan", ru: "Создана", en: "Created" })}: {formatAgo(task.created_at, lang, now)}
                      </span>
                      {task.status === "done" && task.confirmed_at && (
                        <span>
                          {pick(lang, { uz: "Yakunlangan", ru: "Завершена", en: "Completed" })}: {formatDateTime(task.confirmed_at, lang)}
                        </span>
                      )}
                    </div>
                    {task.note && <p className="text-sm">{task.note}</p>}
                  </div>

                  <div className="flex shrink-0 flex-wrap items-center gap-2">
                    {task.status !== "done" && left !== null && (
                      <span className={cn("tabular flex items-center gap-1 text-sm font-medium", overdue ? "text-risk" : left < 4 * 3600_000 ? "text-attention" : "text-muted-foreground")}>
                        <Clock className="size-4" />
                        {overdue ? t("patients.overdue", lang) : formatCountdown(left, lang)}
                      </span>
                    )}
                    {PENDING.includes(task.status) && (
                      <Button size="sm" variant="outline" disabled={busyId === task.id} onClick={() => void handleAck(task)}>
                        {busyId === task.id ? <Loader2 className="animate-spin" /> : <Eye />}
                        {t("handoffs.btn_ack", lang)}
                      </Button>
                    )}
                    {task.status !== "done" && (
                      <Button size="sm" disabled={busyId === task.id} onClick={() => setCompleting(task)}>
                        <ClipboardCheck />
                        {t("handoffs.btn_complete", lang)}
                      </Button>
                    )}
                    <Button size="icon-sm" variant="ghost" asChild aria-label={t("handoffs.btn_chart", lang)}>
                      <Link to={`/doctor/patients/${task.patient_id}`}>
                        <ChevronRight />
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <ConfirmTaskDialog
        open={!!completing}
        onOpenChange={(open) => !open && setCompleting(null)}
        onConfirm={handleComplete}
        lang={lang}
        withVitals={completing?.type === "active_call"}
        title={completing ? `${typeLabel(completing)} · ${patientById.get(completing.patient_id)?.full_name ?? ""}` : undefined}
      />
    </div>
  );
}
