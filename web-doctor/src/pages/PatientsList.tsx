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
    .sort((a, b) => (LEVEL_PRIORITY[a.level] ?? 99) - (LEVEL_PRIORITY[b.level] ?? 99));

  const formatHoursLeft = (dueAtIso: string) => {
    const diffMs = new Date(dueAtIso).getTime() - Date.now();
    if (diffMs <= 0) return t("patients.overdue", lang);
    const hours = Math.floor(diffMs / (3600 * 1000));
    const mins = Math.floor((diffMs % (3600 * 1000)) / (60 * 1000));
    return t("patients.hours_left", lang, { h: hours, m: mins });
  };

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

  const localeMap: Record<Lang, string> = { uz: "uz-UZ", ru: "ru-RU", en: "en-US" };

  return (
    <div className="doc-container">
      {/* 1. Institutional Clinical Triage Bar */}
      <div className="clinical-triage-panel">
        <div className="triage-panel-header">
          <div className="panel-title-left">
            <span className="panel-title">{t("triage.panel_title", lang)}</span>
            <span className="panel-date">
              {t("triage.date_label", lang)}: {new Date().toLocaleDateString(localeMap[lang] || "uz-UZ", { year: "numeric", month: "long", day: "numeric" })}
            </span>
          </div>
          <span className="triage-summary-count">
            {t("triage.total_coverage", lang, { n: patients.length })}
          </span>
        </div>

        <div className="triage-tabs-row">
          <button
            type="button"
            className={`triage-kpi-tab ${statusFilter === "all" && !taskFilterOnly ? "active" : ""}`}
            onClick={() => {
              setStatusFilter("all");
              setTaskFilterOnly(false);
            }}
          >
            <span className="kpi-tag">{t("triage.all_count", lang)}</span>
            <span className="kpi-value">{patients.length}</span>
            <span className="kpi-meta">{t("triage.meta_all", lang)}</span>
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
            <span className="kpi-meta">{t("triage.meta_red", lang)}</span>
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
            <span className="kpi-meta">{t("triage.meta_active_call", lang)}</span>
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
            <span className="kpi-meta">{t("triage.meta_amber", lang)}</span>
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
            <span className="kpi-meta">{t("triage.meta_green", lang)}</span>
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
            <span className="kpi-meta">{t("triage.meta_nodata", lang)}</span>
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
      <div className="table-wrapper-official">
        <table className="patients-table-official">
          <thead>
            <tr>
              <th style={{ width: "120px" }}>{t("patients.th_status", lang)}</th>
              <th style={{ width: "240px" }}>{t("patients.th_fio", lang)}</th>
              <th style={{ width: "110px" }}>{t("patients.th_age_sex", lang)}</th>
              <th style={{ width: "110px" }}>{t("patients.th_district", lang)}</th>
              <th>{t("patients.th_diagnosis", lang)}</th>
              <th style={{ width: "130px" }}>{t("patients.th_trend", lang)}</th>
              <th>{t("patients.th_deviations", lang)}</th>
              <th style={{ width: "160px" }}>{t("patients.th_task", lang)}</th>
              <th style={{ width: "110px", textAlign: "right" }}>{t("patients.th_action", lang)}</th>
            </tr>
          </thead>
          <tbody>
            {filteredPatients.map((p) => {
              const trendDelta =
                p.trend.direction === "worsening"
                  ? "+2.4σ"
                  : p.trend.direction === "improving"
                  ? "-1.6σ"
                  : "0.0σ";

              const trendArrow =
                p.trend.direction === "worsening"
                  ? "↗"
                  : p.trend.direction === "improving"
                  ? "↘"
                  : "→";

              const isUrgent =
                p.level === "red" ||
                (p.open_task &&
                  new Date(p.open_task.due_at).getTime() - Date.now() < 4 * 3600 * 1000);

              const patientCode = `P-${p.id.replace(/-/g, "").slice(0, 4).toUpperCase()}`;

              return (
                <tr key={p.id} className={`patient-row-official level-${p.level}`}>
                  <td>
                    <span className={`status-badge-official ${p.level}`}>
                      <span className={`status-badge-dot ${p.level}`} />
                      {t(`state.${p.level}`, lang)}
                    </span>
                  </td>
                  <td>
                    <div className="patient-identity-cell">
                      <span
                        className="patient-full-name"
                        onClick={() => onSelectPatient(p.id)}
                      >
                        {p.full_name}
                      </span>
                      <div className="patient-id-sub">
                        <code>{patientCode}</code> · {t(`detail.phase_${p.phase}`, lang)}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="age-sex-cell">
                      {t("patients.age_years", lang, { age: p.age })} · {p.sex === "m" ? t("patients.sex_male", lang) : t("patients.sex_female", lang)}
                    </span>
                  </td>
                  <td>
                    <span className="district-cell">{p.district}</span>
                  </td>
                  <td>
                    <div className="diagnosis-text-cell" title={p.diagnosis}>
                      {p.diagnosis}
                    </div>
                  </td>
                  <td>
                    <span className={`trend-tag-official trend-${p.trend.direction}`}>
                      <span>{trendArrow}</span>
                      <span>{trendDelta}</span>
                    </span>
                  </td>
                  <td>
                    {Object.entries(p.triggered_params).length > 0 ? (
                      <div className="deviations-chips-wrap">
                        {Object.entries(p.triggered_params).map(([param, val]) => {
                          const paramDisplay =
                            param === "spo2"
                              ? `SpO₂ ${val}% ↓`
                              : param === "hr_mean"
                              ? `HR ${val} bpm ↑`
                              : param === "rmssd"
                              ? `RMSSD ${val}ms ↓`
                              : param === "skin_temp"
                              ? `T ${val}°C ↑`
                              : param === "rr"
                              ? `${lang === "ru" ? "ЧДД" : lang === "en" ? "RR" : "Nafas"} ${val}/${lang === "ru" ? "мин" : lang === "en" ? "min" : "daq"} ↑`
                              : `${param}: ${val}`;

                          return (
                            <span
                              key={param}
                              className={`dev-chip-official ${p.level === "red" ? "risk" : "attention"}`}
                            >
                              <strong>{paramDisplay}</strong>
                            </span>
                          );
                        })}
                      </div>
                    ) : (
                      <span className="no-dev-dash">—</span>
                    )}
                  </td>
                  <td>
                    {p.open_task ? (
                      <span className={`task-badge-official ${isUrgent ? "urgent" : ""}`}>
                        <span className="task-type-sub">
                          {lang === "ru" ? "24ч Патронаж:" : lang === "en" ? "24h Patrol:" : "24s Patronaj:"}
                        </span>
                        <strong>{formatHoursLeft(p.open_task.due_at)}</strong>
                      </span>
                    ) : (
                      <span className="no-dev-dash">—</span>
                    )}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button
                      type="button"
                      className="btn-view-official"
                      onClick={() => onSelectPatient(p.id)}
                    >
                      <span>{t("patients.btn_chart", lang)}</span>
                      <span className="arrow-sym">→</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
