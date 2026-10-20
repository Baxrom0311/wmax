import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import {
  ArrowDownUp,
  ChevronRight,
  ClipboardList,
  Clock,
  FlaskConical,
  RefreshCw,
  RotateCcw,
  Search,
  TrendingDown,
  TrendingUp,
  Minus,
  Users,
  X,
} from "lucide-react";
import { LevelBadge, LevelDot } from "@/components/app/level-badge";
import { LEVEL_PRIORITY } from "@/lib/levels";
import { EmptyState, ErrorState, PageHeader } from "@/components/app/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useNow } from "@/hooks/use-now";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import { formatAgo, formatCountdown, msUntil } from "@/lib/format";
import { paramMeta } from "@/lib/params";
import { usePrefs } from "@/lib/prefs";
import type { AlertLevel, PatientSummary } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useClinicData, useClinicSession } from "./session";

type SortField = "priority" | "name" | "age" | "score" | "due";

const KPI: { key: string; level?: AlertLevel; task?: boolean; label: string; tone: string }[] = [
  { key: "all", label: "triage.all_count", tone: "text-foreground" },
  { key: "red", level: "red", label: "triage.red_title", tone: "text-risk" },
  { key: "task", task: true, label: "triage.active_call_title", tone: "text-attention" },
  { key: "amber", level: "amber", label: "triage.amber_title", tone: "text-attention" },
  { key: "green", level: "green", label: "triage.green_title", tone: "text-good" },
  { key: "no_data", level: "no_data", label: "triage.nodata_title", tone: "text-nodata" },
];

function hasOpenTask(p: PatientSummary) {
  return !!p.open_task && p.open_task.status !== "done";
}

function TrendIcon({ direction }: { direction: string }) {
  if (direction === "worsening") return <TrendingUp className="text-risk size-4" />;
  if (direction === "improving") return <TrendingDown className="text-good size-4" />;
  return <Minus className="text-muted-foreground size-4" />;
}

export function PatientsPage() {
  const { lang } = usePrefs();
  const { launchDemo } = useClinicSession();
  const { patients, patientsLoaded, patientsError, reloadPatients } = useClinicData();
  const navigate = useNavigate();
  const now = useNow();
  const [params, setParams] = useSearchParams();

  const district = params.get("district") ?? "all";
  const status = params.get("status") ?? "all";
  const tasksOnly = params.get("tasks") === "1";
  const query = params.get("q") ?? "";
  const sortBy = (params.get("sort") as SortField) ?? "priority";
  const sortAsc = params.get("dir") !== "desc";

  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null || v === "" || v === "all") next.delete(k);
      else next.set(k, v);
    }
    setParams(next, { replace: true });
  };

  const districts = useMemo(() => Array.from(new Set(patients.map((p) => p.district))).sort(), [patients]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return patients
      .filter((p) => {
        if (district !== "all" && p.district !== district) return false;
        if (status !== "all" && p.level !== status) return false;
        if (tasksOnly && !hasOpenTask(p)) return false;
        if (q && !p.full_name.toLowerCase().includes(q) && !p.diagnosis.toLowerCase().includes(q)) return false;
        return true;
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortBy === "priority") cmp = (LEVEL_PRIORITY[a.level] ?? 9) - (LEVEL_PRIORITY[b.level] ?? 9) || b.composite_score - a.composite_score;
        else if (sortBy === "name") cmp = a.full_name.localeCompare(b.full_name);
        else if (sortBy === "age") cmp = a.age - b.age;
        else if (sortBy === "score") cmp = a.composite_score - b.composite_score;
        else if (sortBy === "due") {
          const da = a.open_task?.due_at ? new Date(a.open_task.due_at).getTime() : Infinity;
          const db = b.open_task?.due_at ? new Date(b.open_task.due_at).getTime() : Infinity;
          cmp = da - db;
        }
        return sortAsc ? cmp : -cmp;
      });
  }, [patients, district, status, tasksOnly, query, sortBy, sortAsc]);

  const counts: Record<string, number> = {
    all: patients.length,
    red: patients.filter((p) => p.level === "red").length,
    task: patients.filter(hasOpenTask).length,
    amber: patients.filter((p) => p.level === "amber").length,
    green: patients.filter((p) => p.level === "green").length,
    no_data: patients.filter((p) => p.level === "no_data").length,
  };

  const isFiltering = district !== "all" || status !== "all" || tasksOnly || query.trim().length > 0;
  const resetFilters = () => update({ district: null, status: null, tasks: null, q: null });
  const open = (id: string) => navigate(`/doctor/patients/${encodeURIComponent(id)}`);

  const kpiActive = (k: (typeof KPI)[number]) =>
    k.key === "all" ? status === "all" && !tasksOnly : k.task ? tasksOnly : status === k.level && !tasksOnly;

  const onKpi = (k: (typeof KPI)[number]) => {
    if (k.key === "all") update({ status: null, tasks: null });
    else if (k.task) update({ tasks: tasksOnly ? null : "1", status: null });
    else update({ status: status === k.level && !tasksOnly ? null : k.level!, tasks: null });
  };

  const taskCell = (p: PatientSummary) => {
    if (!hasOpenTask(p)) return <span className="text-muted-foreground">—</span>;
    const ms = msUntil(p.open_task!.due_at, now);
    const overdue = p.open_task!.status === "overdue" || (ms !== null && ms <= 0);
    return (
      <Badge variant={overdue ? "risk" : "attention"} className="gap-1">
        {overdue ? <Clock /> : <ClipboardList />}
        {overdue ? t("patients.overdue", lang) : ms !== null ? formatCountdown(ms, lang) : t("patients.task_active_call", lang)}
      </Badge>
    );
  };

  const deviations = (p: PatientSummary) => {
    const entries = Object.entries(p.triggered_params || {});
    if (entries.length === 0) return <span className="text-muted-foreground">—</span>;
    return (
      <div className="flex flex-wrap gap-1">
        {entries.slice(0, 3).map(([param, value]) => {
          const meta = paramMeta(param);
          return (
            <Badge key={param} variant="outline" className="tabular font-normal">
              {meta.short} <span className="font-semibold">{value}</span>
              {meta.unit && <span className="text-muted-foreground">{meta.unit}</span>}
            </Badge>
          );
        })}
      </div>
    );
  };

  if (patientsError && patients.length === 0) {
    return (
      <ErrorState
        title={t("error.server_connection", lang)}
        description={patientsError}
        onRetry={() => void reloadPatients()}
        retryLabel={t("error.retry", lang)}
        extra={
          <Button variant="outline" onClick={() => launchDemo("doctor")}>
            <FlaskConical />
            {t("demo.enter_demo", lang)}
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={pick(lang, { uz: "Bemorlar ish ro'yxati", ru: "Рабочий список пациентов", en: "Patient worklist" })}
        description={pick(lang, {
          uz: "Xavf darajasi bo'yicha saralangan. Ma'lumot kelmayotgan bemorlar alohida ko'rsatiladi.",
          ru: "Отсортировано по уровню риска. Пациенты без данных выделены отдельно.",
          en: "Sorted by risk. Patients without data are flagged separately.",
        })}
        actions={
          <Button variant="outline" size="sm" onClick={() => void reloadPatients()}>
            <RefreshCw />
            {pick(lang, { uz: "Yangilash", ru: "Обновить", en: "Refresh" })}
          </Button>
        }
      />

      {/* Triage counters double as quick filters */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {KPI.map((k) => (
          <button
            key={k.key}
            type="button"
            onClick={() => onKpi(k)}
            aria-pressed={kpiActive(k)}
            className={cn(
              "bg-card flex flex-col items-start gap-1 rounded-xl border p-4 text-left shadow-xs transition hover:border-primary/40 cursor-pointer",
              kpiActive(k) && "border-primary ring-primary/20 ring-2",
            )}
          >
            <span className="text-muted-foreground flex items-center gap-1.5 text-xs font-medium">
              {k.level && <LevelDot level={k.level} />}
              {k.task && <ClipboardList className="text-attention size-3.5" />}
              {t(k.label, lang)}
            </span>
            <span className={cn("tabular font-display text-2xl font-bold", k.tone)}>
              {patientsLoaded ? counts[k.key] : <Skeleton className="h-7 w-10" />}
            </span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <Card className="gap-0 p-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
            <Input
              value={query}
              onChange={(e) => update({ q: e.target.value })}
              placeholder={t("patients.search_placeholder", lang)}
              className="pl-9"
            />
            {query && (
              <button
                type="button"
                onClick={() => update({ q: null })}
                className="text-muted-foreground hover:text-foreground absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 cursor-pointer"
                aria-label={t("nav.search_clear", lang)}
              >
                <X className="size-3.5" />
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Select value={district} onValueChange={(v) => update({ district: v })}>
              <SelectTrigger className="min-w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("patients.all_districts", lang)}</SelectItem>
                {districts.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={(v) => update({ status: v })}>
              <SelectTrigger className="min-w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("patients.all_statuses", lang)}</SelectItem>
                {(["red", "no_data", "amber", "green"] as const).map((lvl) => (
                  <SelectItem key={lvl} value={lvl}>
                    {t(`state.${lvl}`, lang)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={(v) => update({ sort: v === "priority" ? null : v })}>
              <SelectTrigger className="min-w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(["priority", "name", "age", "score", "due"] as const).map((f) => (
                  <SelectItem key={f} value={f}>
                    {t(`sort.${f}`, lang)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              onClick={() => update({ dir: sortAsc ? "desc" : null })}
              title={sortAsc ? t("patients.order_asc", lang) : t("patients.order_desc", lang)}
              aria-label={sortAsc ? t("patients.order_asc", lang) : t("patients.order_desc", lang)}
            >
              <ArrowDownUp className={cn(!sortAsc && "rotate-180")} />
            </Button>
            {isFiltering && (
              <Button variant="ghost" onClick={resetFilters}>
                <RotateCcw />
                {t("patients.reset_filters", lang)} ({filtered.length})
              </Button>
            )}
          </div>
        </div>
      </Card>

      {!patientsLoaded ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Users}
          title={patients.length === 0 ? t("error.no_patients", lang) : t("patients.no_matches", lang)}
          action={
            isFiltering ? (
              <Button variant="outline" onClick={resetFilters}>
                <RotateCcw />
                {t("patients.clear_filters", lang)}
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          {/* Desktop table */}
          <Card className="hidden gap-0 overflow-hidden py-0 md:flex">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40 hover:bg-muted/40">
                  <TableHead className="pl-5">{pick(lang, { uz: "Bemor", ru: "Пациент", en: "Patient" })}</TableHead>
                  <TableHead>{t("patients.th_status", lang)}</TableHead>
                  <TableHead>{pick(lang, { uz: "Og'ishlar", ru: "Отклонения", en: "Deviations" })}</TableHead>
                  <TableHead>{pick(lang, { uz: "Trend", ru: "Тренд", en: "Trend" })}</TableHead>
                  <TableHead>{pick(lang, { uz: "Oxirgi o'lchov", ru: "Последнее измерение", en: "Last reading" })}</TableHead>
                  <TableHead>{pick(lang, { uz: "Vazifa", ru: "Задача", en: "Task" })}</TableHead>
                  <TableHead className="w-8" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((p) => (
                  <TableRow
                    key={p.id}
                    className="cursor-pointer"
                    onClick={() => open(p.id)}
                    onKeyDown={(e) => e.key === "Enter" && open(p.id)}
                    tabIndex={0}
                    aria-label={t("patients.card_view", lang, { name: p.full_name })}
                  >
                    <TableCell className="pl-5">
                      <div className="flex items-center gap-3">
                        <LevelDot level={p.level} pulse={p.level === "red"} />
                        <div className="min-w-0">
                          <p className="truncate font-medium">{p.full_name}</p>
                          <p className="text-muted-foreground truncate text-xs">
                            {t("patients.age_years", lang, { age: p.age })} · {p.sex === "m" ? t("patients.sex_male", lang) : t("patients.sex_female", lang)} · {p.district}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <LevelBadge level={p.level} label={t(`state.${p.level}`, lang)} />
                    </TableCell>
                    <TableCell>{deviations(p)}</TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5 text-xs" title={t(`trend.${p.trend.direction}`, lang)}>
                        <TrendIcon direction={p.trend.direction} />
                        <span className="text-muted-foreground hidden xl:inline">{t(`trend.${p.trend.direction}`, lang)}</span>
                      </span>
                    </TableCell>
                    <TableCell className={cn("text-xs", p.level === "no_data" ? "text-nodata-ink font-medium" : "text-muted-foreground")}>
                      {formatAgo(p.last_reading_at, lang, now)}
                    </TableCell>
                    <TableCell>{taskCell(p)}</TableCell>
                    <TableCell>
                      <ChevronRight className="text-muted-foreground size-4" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>

          {/* Mobile cards */}
          <ul className="space-y-2 md:hidden">
            {filtered.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => open(p.id)}
                  className={cn(
                    "bg-card flex w-full items-start gap-3 rounded-xl border p-4 text-left shadow-xs cursor-pointer",
                    p.level === "red" && "border-risk/40",
                  )}
                >
                  <LevelDot level={p.level} pulse={p.level === "red"} className="mt-1.5" />
                  <div className="min-w-0 flex-1 space-y-2">
                    <div>
                      <p className="font-medium">{p.full_name}</p>
                      <p className="text-muted-foreground text-xs">
                        {t("patients.age_years", lang, { age: p.age })} · {p.district} · {formatAgo(p.last_reading_at, lang, now)}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      <LevelBadge level={p.level} label={t(`state.${p.level}`, lang)} />
                      {hasOpenTask(p) && taskCell(p)}
                    </div>
                  </div>
                  <ChevronRight className="text-muted-foreground mt-1 size-4" />
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
