import React from "react";
import {
  Search,
  X,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  ClipboardList,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { PatientSummary } from "../lib/types";

interface PatientsListProps {
  patients: PatientSummary[];
  onSelectPatient: (id: string) => void;
  lang: Lang;
  // Hoisted to App.tsx — prevents reset on re-render/remount
  districtFilter: string;
  onDistrictFilterChange: (v: string) => void;
  statusFilter: string;
  onStatusFilterChange: (v: string) => void;
  taskFilterOnly: boolean;
  onTaskFilterChange: (v: boolean) => void;
  searchQuery: string;
  onSearchQueryChange: (v: string) => void;
}

export const PatientsList: React.FC<PatientsListProps> = ({
  patients,
  onSelectPatient,
  lang,
  districtFilter,
  onDistrictFilterChange,
  statusFilter,
  onStatusFilterChange,
  taskFilterOnly,
  onTaskFilterChange,
  searchQuery,
  onSearchQueryChange,
}) => {
  // useState lar olib tashlandi — hamma filter state App.tsx da

  const districts = Array.from(new Set(patients.map((p) => p.district)));

  const LEVEL_PRIORITY: Record<string, number> = {
    red: 0,
    no_data: 1,
    amber: 2,
    green: 3,
  };

  type SortField = "priority" | "name" | "age" | "score" | "due";
  const sortBy: SortField = "priority";
  const sortAsc = true;


  const filteredPatients = patients
    .filter((p) => {
      if (districtFilter !== "all" && p.district !== districtFilter) return false;
      if (statusFilter !== "all" && p.level !== statusFilter) return false;
      if (taskFilterOnly && (!p.open_task || p.open_task.status === "done")) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = p.full_name.toLowerCase().includes(q);
        const matchDiag = p.diagnosis.toLowerCase().includes(q);
        if (!matchName && !matchDiag) return false;
      }
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      if (sortBy === "priority") {
        cmp = (LEVEL_PRIORITY[a.level] ?? 99) - (LEVEL_PRIORITY[b.level] ?? 99);
      } else if (sortBy === "name") {
        cmp = a.full_name.localeCompare(b.full_name);
      } else if (sortBy === "age") {
        cmp = a.age - b.age;
      } else if (sortBy === "score") {
        cmp = a.composite_score - b.composite_score;
      } else if (sortBy === "due") {
        const dueA = a.open_task ? new Date(a.open_task.due_at).getTime() : Infinity;
        const dueB = b.open_task ? new Date(b.open_task.due_at).getTime() : Infinity;
        cmp = dueA - dueB;
      }
      return sortAsc ? cmp : -cmp;
    });


  const redCount = patients.filter((p) => p.level === "red").length;
  const activeCallCount = patients.filter(
    (p) => p.open_task && p.open_task.status !== "done"
  ).length;
  const amberCount = patients.filter((p) => p.level === "amber").length;
  const greenCount = patients.filter((p) => p.level === "green").length;
  const noDataCount = patients.filter((p) => p.level === "no_data").length;

  const isFiltering =
    districtFilter !== "all" ||
    statusFilter !== "all" ||
    taskFilterOnly ||
    searchQuery.trim().length > 0;

  const resetAllFilters = () => {
    onDistrictFilterChange("all");
    onStatusFilterChange("all");
    onTaskFilterChange(false);
    onSearchQueryChange("");
  };


  return (
    <div className="doc-container">
      {/* 1. Institutional Clinical Triage Bar */}
      <div className="clinical-triage-panel">
        <div className="triage-tabs-row">
          <button
            type="button"
            className={`triage-kpi-tab ${statusFilter === "all" && !taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              onStatusFilterChange("all");
              onTaskFilterChange(false);
            }}
          >
            <span className="kpi-value">{patients.length}</span>
            <span className="kpi-tag">{t("triage.all_count", lang)}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-red ${statusFilter === "red" ? "active" : ""}`}
            onClick={() => {
              onStatusFilterChange(statusFilter === "red" ? "all" : "red");
              onTaskFilterChange(false);
            }}
          >
            <div className="kpi-top-tag">
              <span className="kpi-dot red" />
              <span className="kpi-tag text-risk">{t("triage.red_title", lang)}</span>
            </div>
            <span className="kpi-value text-risk">{redCount}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-task ${taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              onTaskFilterChange(!taskFilterOnly);
            }}
          >
            <div className="kpi-top-tag">
              <span className="kpi-dot amber" />
              <span className="kpi-tag text-attention">{t("triage.active_call_title", lang)}</span>
            </div>
            <span className="kpi-value text-attention">{activeCallCount}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-amber ${statusFilter === "amber" && !taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              onStatusFilterChange(statusFilter === "amber" ? "all" : "amber");
              onTaskFilterChange(false);
            }}
          >
            <div className="kpi-top-tag">
              <span className="kpi-dot amber" />
              <span className="kpi-tag text-attention">{t("triage.amber_title", lang)}</span>
            </div>
            <span className="kpi-value text-attention">{amberCount}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-green ${statusFilter === "green" && !taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              onStatusFilterChange(statusFilter === "green" ? "all" : "green");
              onTaskFilterChange(false);
            }}
          >
            <div className="kpi-top-tag">
              <span className="kpi-dot green" />
              <span className="kpi-tag text-good">{t("triage.green_title", lang)}</span>
            </div>
            <span className="kpi-value text-good">{greenCount}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-nodata ${statusFilter === "no_data" && !taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              onStatusFilterChange(statusFilter === "no_data" ? "all" : "no_data");
              onTaskFilterChange(false);
            }}
          >
            <div className="kpi-top-tag">
              <span className="kpi-dot nodata" />
              <span className="kpi-tag text-muted">{t("triage.nodata_title", lang)}</span>
            </div>
            <span className="kpi-value text-muted">{noDataCount}</span>
          </button>
        </div>
      </div>

      {/* 2. Official Filters Bar */}
      <div className="filters-control-bar-official">
        <div className="filter-search-box">
          <Search className="search-svg" size={15} />
          <input
            type="text"
            className="filter-search-input-official"
            placeholder={t("patients.search_placeholder", lang)}
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn-official"
              onClick={() => onSearchQueryChange("")}
              aria-label="Qidiruvni tozalash"
            >
              <X size={13} />
            </button>
          )}
        </div>

        <div className="filter-selects-row">
          <div className="filter-select-group">
            <label htmlFor="filter-district-select" className="filter-label-official">
              {t("patients.filter_district_short", lang)}
            </label>
            <select
              id="filter-district-select"
              className="filter-select-official"
              value={districtFilter}
              onChange={(e) => onDistrictFilterChange(e.target.value)}
            >
              <option value="all">{t("patients.all_districts", lang)}</option>
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-select-group">
            <label htmlFor="filter-status-select" className="filter-label-official">
              {t("patients.filter_status_short", lang)}
            </label>
            <select
              id="filter-status-select"
              className="filter-select-official"
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value)}
            >
              <option value="all">{t("patients.all_statuses", lang)}</option>
              <option value="red">{t("state.red", lang)}</option>
              <option value="no_data">{t("state.no_data", lang)}</option>
              <option value="amber">{t("state.amber", lang)}</option>
              <option value="green">{t("state.green", lang)}</option>
            </select>
          </div>

          {isFiltering && (
            <button
              type="button"
              className="btn-official-reset"
              onClick={resetAllFilters}
            >
              <RotateCcw size={12} style={{ marginRight: 4 }} />
              {t("patients.reset_filters", lang)} ({filteredPatients.length})
            </button>
          )}
        </div>
      </div>

      {/* 3. Official High Density Worklist Table */}
      <ol className="worklist">
        {filteredPatients.length === 0 ? (
          <li className="worklist-empty">
            <h2 className="worklist-empty-title">{t("patients.no_matches", lang)}</h2>
            <button type="button" className="btn-official-reset" onClick={resetAllFilters}>
              <RotateCcw size={12} style={{ marginRight: 4 }} />
              {t("patients.clear_filters", lang)}
            </button>
          </li>
        ) : (
          filteredPatients.map((p) => {
            const hasTask = p.open_task && p.open_task.status !== "done";
            const isOverdue = p.open_task?.status === "overdue";

            return (
              <li key={p.id} className={`wl-row wl-${p.level}`}>
                <button
                  type="button"
                  className="wl-open"
                  onClick={() => onSelectPatient(p.id)}
                  aria-label={`${p.full_name} — batafsil ko'rish`}
                >
                  {/* Left accent spine */}
                  <span className="wl-spine" aria-hidden="true" />

                  {/* Left zone: name + meta */}
                  <span className="wl-left">
                    <span className="wl-name">{p.full_name}</span>
                    <span className="wl-meta">
                      {p.age} {lang === "ru" ? "лет" : lang === "en" ? "yrs" : "yosh"}
                      <span className="wl-meta-sep">·</span>
                      {p.district}
                    </span>
                  </span>

                  {/* Right zone: status badge + task pill */}
                  <span className="wl-right">
                    <span className={`wl-level wl-level-${p.level}`}>
                      <span className="wl-level-icon" aria-hidden="true">
                        {p.level === "red" ? (
                          <AlertCircle size={12} strokeWidth={2.5} />
                        ) : p.level === "amber" ? (
                          <AlertTriangle size={12} strokeWidth={2.5} />
                        ) : p.level === "green" ? (
                          <CheckCircle2 size={12} strokeWidth={2.5} />
                        ) : (
                          <HelpCircle size={12} strokeWidth={2.5} />
                        )}
                      </span>
                      {t(`state.${p.level}`, lang)}
                    </span>
                    {hasTask && (
                      <span className={`wl-task-dot ${isOverdue ? "overdue" : ""}`}>
                        {isOverdue ? (
                          <>
                            <Clock size={11} strokeWidth={2.2} />
                            <span>Muddati o'tdi</span>
                          </>
                        ) : (
                          <>
                            <ClipboardList size={11} strokeWidth={2.2} />
                            <span>Patronaj</span>
                          </>
                        )}
                      </span>
                    )}
                  </span>

                  {/* Arrow */}
                  <span className="wl-arrow" aria-hidden="true">
                    <ChevronRight size={18} strokeWidth={2} />
                  </span>
                </button>
              </li>
            );
          })
        )}
      </ol>
    </div>
  );
};
