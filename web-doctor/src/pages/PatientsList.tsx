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

  const isFiltering = districtFilter !== "all" || statusFilter !== "all" || taskFilterOnly || searchQuery.trim().length > 0;

  const resetAllFilters = () => {
    setDistrictFilter("all");
    setStatusFilter("all");
    setTaskFilterOnly(false);
    setSearchQuery("");
  };

  return (
    <div className="doc-container">
      {/* 1. Interactive Clinical Triage Stat Bar */}
      <div className="triage-cards-grid">
        <div
          className={`triage-stat-card card-all ${statusFilter === "all" && !taskFilterOnly ? "active" : ""}`}
          onClick={() => {
            setStatusFilter("all");
            setTaskFilterOnly(false);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-stat-icon">🏥</span>
            <span className="triage-stat-num">{patients.length}</span>
          </div>
          <div className="triage-stat-label">{t("triage.all_count", lang)}</div>
        </div>

        <div
          className={`triage-stat-card card-red ${statusFilter === "red" ? "active" : ""}`}
          onClick={() => {
            setStatusFilter(statusFilter === "red" ? "all" : "red");
            setTaskFilterOnly(false);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-pulse-ring red" />
            <span className="triage-stat-num text-risk">{redCount}</span>
          </div>
          <div className="triage-stat-label">{t("triage.red_title", lang)}</div>
        </div>

        <div
          className={`triage-stat-card card-task ${taskFilterOnly ? "active" : ""} ${activeCallCount > 0 ? "has-tasks" : ""}`}
          onClick={() => {
            setTaskFilterOnly((prev) => !prev);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-stat-icon">⏳</span>
            <span className="triage-stat-num text-attention">{activeCallCount}</span>
          </div>
          <div className="triage-stat-label">{t("triage.active_call_title", lang)}</div>
        </div>

        <div
          className={`triage-stat-card card-amber ${statusFilter === "amber" && !taskFilterOnly ? "active" : ""}`}
          onClick={() => {
            setStatusFilter(statusFilter === "amber" ? "all" : "amber");
            setTaskFilterOnly(false);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-stat-icon">🟡</span>
            <span className="triage-stat-num text-attention">{amberCount}</span>
          </div>
          <div className="triage-stat-label">{t("triage.amber_title", lang)}</div>
        </div>

        <div
          className={`triage-stat-card card-green ${statusFilter === "green" && !taskFilterOnly ? "active" : ""}`}
          onClick={() => {
            setStatusFilter(statusFilter === "green" ? "all" : "green");
            setTaskFilterOnly(false);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-stat-icon">🟢</span>
            <span className="triage-stat-num text-good">{greenCount}</span>
          </div>
          <div className="triage-stat-label">{t("triage.green_title", lang)}</div>
        </div>

        <div
          className={`triage-stat-card card-nodata ${statusFilter === "no_data" && !taskFilterOnly ? "active" : ""}`}
          onClick={() => {
            setStatusFilter(statusFilter === "no_data" ? "all" : "no_data");
            setTaskFilterOnly(false);
          }}
        >
          <div className="triage-stat-top">
            <span className="triage-stat-icon">⚪</span>
            <span className="triage-stat-num text-muted">{noDataCount}</span>
          </div>
          <div className="triage-stat-label">{t("triage.nodata_title", lang)}</div>
        </div>
      </div>

      {/* 2. Search & Filter Bar */}
      <div className="filters-control-bar">
        {/* Search input with icon */}
        <div className="filter-group filter-search-group">
          <span className="search-icon-decor">🔍</span>
          <input
            type="text"
            className="filter-search-input"
            placeholder={t("patients.search_placeholder", lang)}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearchQuery("")}
            >
              ✕
            </button>
          )}
        </div>

        <div className="filter-group">
          <label htmlFor="filter-district-select" className="filter-label">
            {t("patients.filter_district", lang)}
          </label>
          <select
            id="filter-district-select"
            className="filter-select"
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

        <div className="filter-group">
          <label htmlFor="filter-status-select" className="filter-label">
            {t("patients.filter_status", lang)}
          </label>
          <select
            id="filter-status-select"
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">{t("patients.all_statuses", lang)}</option>
            <option value="red">{t("state.risk", lang)}</option>
            <option value="no_data">{t("state.no_data", lang)}</option>
            <option value="amber">{t("state.attention", lang)}</option>
            <option value="green">{t("state.good", lang)}</option>
          </select>
        </div>

        {isFiltering && (
          <button
            type="button"
            className="btn btn-outline reset-filters-btn"
            onClick={resetAllFilters}
          >
            {t("patients.reset_filters", lang)} ({filteredPatients.length})
          </button>
        )}
      </div>

      {/* 3. High Density Worklist Table */}
      <div className="table-wrapper">
        <table className="patients-table">
          <thead>
            <tr>
              <th>{t("patients.th_status", lang)}</th>
              <th>{t("patients.th_fio", lang)}</th>
              <th>{t("patients.th_age_sex", lang)}</th>
              <th>{t("patients.th_district", lang)}</th>
              <th>{t("patients.th_diagnosis", lang)}</th>
              <th>{t("patients.th_trend", lang)}</th>
              <th>{t("patients.th_deviations", lang)}</th>
              <th>{t("patients.th_task", lang)}</th>
              <th style={{ textAlign: "right" }}>{t("patients.th_action", lang)}</th>
            </tr>
          </thead>
          <tbody>
            {filteredPatients.map((p) => {
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

              const patientInitials = p.full_name
                .split(" ")
                .map((w) => w[0])
                .slice(0, 2)
                .join("");

              return (
                <tr key={p.id} className={`patient-row level-${p.level}`}>
                  <td>
                    <div className="status-pill-cell">
                      <span className={`status-dot ${p.level}`} />
                      <span className={`status-text-pill ${p.level}`}>
                        {t(`state.${p.level}`, lang)}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="patient-name-wrap">
                      <div className="patient-mini-avatar">{patientInitials}</div>
                      <div>
                        <span
                          className="fio-cell"
                          style={{ cursor: "pointer" }}
                          onClick={() => onSelectPatient(p.id)}
                        >
                          {p.full_name}
                        </span>
                        <div className="patient-phase-sub">
                          {t(`detail.phase_${p.phase}`, lang)}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="age-sex-badge">
                      {p.age}y · {p.sex === "m" ? "Erkak" : "Ayol"}
                    </span>
                  </td>
                  <td>
                    <span className="district-tag">{p.district}</span>
                  </td>
                  <td className="diagnosis-cell" title={p.diagnosis}>
                    {p.diagnosis}
                  </td>
                  <td>
                    <span
                      className={`trend-indicator-badge trend-${p.trend.direction}`}
                    >
                      <span className="trend-arrow">{trendArrow}</span>
                      <span>{t(`trend.${p.trend.direction}`, lang)}</span>
                    </span>
                  </td>
                  <td>
                    {Object.entries(p.triggered_params).length > 0 ? (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                        {Object.entries(p.triggered_params).map(([param, val]) => (
                          <span
                            key={param}
                            className={`deviations-tag ${p.level === "amber" ? "amber" : ""}`}
                          >
                            <strong>{param}:</strong> {val}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: "var(--color-muted)", fontSize: "12px" }}>
                        —
                      </span>
                    )}
                  </td>
                  <td>
                    {p.open_task ? (
                      <span className={`task-tag ${isUrgent ? "urgent" : ""}`}>
                        <span className="task-icon">⏳</span>
                        <span>
                          {t(`patients.task_${p.open_task.type}`, lang)} ·{" "}
                          <strong>{formatHoursLeft(p.open_task.due_at)}</strong>
                        </span>
                      </span>
                    ) : (
                      <span style={{ color: "var(--color-muted)", fontSize: "12px" }}>
                        —
                      </span>
                    )}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button
                      type="button"
                      className="btn btn-view-patient"
                      onClick={() => onSelectPatient(p.id)}
                    >
                      <span>{t("patients.btn_view", lang)}</span>
                      <span className="btn-arrow">→</span>
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
