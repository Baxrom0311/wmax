import React, { useState } from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { PatientSummary } from "../lib/types";

interface PatientsListProps {
  patients: PatientSummary[];
  onSelectPatient: (id: string) => void;
  lang: Lang;
}

export const PatientsList: React.FC<PatientsListProps> = ({
  patients,
  onSelectPatient,
  lang,
}) => {
  const [districtFilter, setDistrictFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [taskFilterOnly, setTaskFilterOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");

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
    setDistrictFilter("all");
    setStatusFilter("all");
    setTaskFilterOnly(false);
    setSearchQuery("");
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
              setStatusFilter("all");
              setTaskFilterOnly(false);
            }}
          >
            <span className="kpi-value">{patients.length}</span>
            <span className="kpi-tag">{t("triage.all_count", lang)}</span>
          </button>

          <button
            type="button"
            className={`triage-kpi-tab kpi-red ${statusFilter === "red" ? "active" : ""}`}
            onClick={() => {
              setStatusFilter(statusFilter === "red" ? "all" : "red");
              setTaskFilterOnly(false);
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
              setTaskFilterOnly((prev) => !prev);
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
              setStatusFilter(statusFilter === "amber" ? "all" : "amber");
              setTaskFilterOnly(false);
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
              setStatusFilter(statusFilter === "green" ? "all" : "green");
              setTaskFilterOnly(false);
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
              setStatusFilter(statusFilter === "no_data" ? "all" : "no_data");
              setTaskFilterOnly(false);
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
          <svg className="search-svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="filter-search-input-official"
            placeholder={t("patients.search_placeholder", lang)}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn-official"
              onClick={() => setSearchQuery("")}
            >
              ✕
            </button>
          )}
        </div>

        <div className="filter-select-group">
          <label htmlFor="filter-district-select" className="filter-label-official">
            {t("patients.filter_district_short", lang)}
          </label>
          <select
            id="filter-district-select"
            className="filter-select-official"
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
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
            onChange={(e) => setStatusFilter(e.target.value)}
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
            {t("patients.reset_filters", lang)} ({filteredPatients.length})
          </button>
        )}
      </div>

      {/* 3. Official High Density Worklist Table */}
      <ol className="worklist">
        {filteredPatients.length === 0 ? (
          <li className="worklist-empty">
            <h2 className="worklist-empty-title">{t("patients.no_matches", lang)}</h2>
            <button type="button" className="btn-official-reset" onClick={resetAllFilters}>
              {t("patients.clear_filters", lang)}
            </button>
          </li>
        ) : (
          filteredPatients.map((p) => {
            const slope = p.trend?.slope ?? 0;
            const trendArrow =
              p.trend.direction === "worsening" ? "↗" : p.trend.direction === "improving" ? "↘" : "→";

            const dueLabel = p.open_task
              ? new Intl.DateTimeFormat(lang === "ru" ? "ru-RU" : lang === "en" ? "en-GB" : "uz-UZ", {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                }).format(new Date(p.open_task.due_at))
              : null;

            const deviations = Object.entries(p.triggered_params ?? {})
              .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
              .slice(0, 4);

            return (
              <li key={p.id} className={`wl-row wl-${p.level}`}>
                <button
                  type="button"
                  className="wl-open"
                  onClick={() => onSelectPatient(p.id)}
                  aria-label={`${p.full_name} — ${t("patients.th_action", lang)}`}
                >
                  <span className="wl-spine" aria-hidden="true" />

                  <span className="wl-body">
                    <span className="wl-line-top">
                      <span className="wl-name">{p.full_name}</span>
                      <span className={`wl-level wl-level-${p.level}`}>
                        <span aria-hidden="true">
                          {p.level === "red" ? "!" : p.level === "amber" ? "△" : p.level === "green" ? "✓" : "×"}
                        </span>
                        {t(`state.${p.level}`, lang)}
                      </span>
                      <span className="wl-meta">
                        {p.age} {lang === "ru" ? "лет" : lang === "en" ? "yrs" : "yosh"} · {p.district}
                      </span>
                    </span>

                    <span className="wl-dx">{p.diagnosis}</span>

                    {deviations.length > 0 && (
                      <span className="wl-devs">
                        {deviations.map(([k, v]) => (
                          <span key={k} className={`wl-dev ${v < 0 ? "down" : "up"}`}>
                            <span className="wl-dev-k">{k}</span>
                            <span className="wl-dev-v">
                              {v > 0 ? "+" : ""}
                              {v.toFixed(1)}σ
                            </span>
                          </span>
                        ))}
                      </span>
                    )}
                  </span>

                  <span className="wl-side">
                    <span className="wl-score" title={t("patients.th_trend", lang)}>
                      <span className="wl-score-v">{p.composite_score.toFixed(1)}</span>
                      <span className="wl-score-t">
                        {trendArrow} {slope > 0 ? "+" : ""}
                        {slope.toFixed(2)}
                      </span>
                    </span>

                    {dueLabel && (
                      <span className={`wl-due ${p.open_task?.status === "overdue" ? "overdue" : ""}`}>
                        {p.open_task?.status === "overdue" ? t("patients.overdue", lang) : dueLabel}
                      </span>
                    )}
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
