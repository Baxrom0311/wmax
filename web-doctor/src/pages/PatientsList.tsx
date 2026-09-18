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
  const [searchQuery, setSearchQuery] = useState<string>("");

  const attentionPatients = patients.filter(
    (p) => p.level === "red" || p.level === "amber"
  );

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

  return (
    <div className="doc-container">
      {/* 1. Attention Banner */}
      {attentionPatients.length > 0 && (
        <div className="attention-banner">
          <span className="attention-banner-title">
            ⚠️ {t("patients.attention_count", lang, { n: attentionPatients.length })}
          </span>
        </div>
      )}

      {/* 2. Filters & Search Row */}
      <div className="filters-control-bar">
        {/* Search input */}
        <div className="filter-group filter-search-group">
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
          <label htmlFor="filter-district-select" className="filter-label">{t("patients.filter_district", lang)}</label>
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
          <label htmlFor="filter-status-select" className="filter-label">{t("patients.filter_status", lang)}</label>
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
              <th>{t("patients.th_action", lang)}</th>
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

              return (
                <tr key={p.id}>
                  <td>
                    <span className={`status-dot ${p.level}`} />
                    <span style={{ fontSize: "12px", textTransform: "capitalize" }}>
                      {t(`state.${p.level}`, lang)}
                    </span>
                  </td>
                  <td>
                    <span
                      className="fio-cell"
                      style={{ cursor: "pointer" }}
                      onClick={() => onSelectPatient(p.id)}
                    >
                      {p.full_name}
                    </span>
                  </td>
                  <td>
                    {p.age}y / {p.sex === "m" ? "Erkak" : "Ayol"}
                  </td>
                  <td>{p.district}</td>
                  <td className="diagnosis-cell" title={p.diagnosis}>
                    {p.diagnosis}
                  </td>
                  <td>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: "15px",
                        color:
                          p.trend.direction === "worsening"
                            ? "var(--color-risk)"
                            : p.trend.direction === "improving"
                            ? "var(--color-good)"
                            : "var(--color-muted)",
                      }}
                    >
                      {trendArrow}
                    </span>{" "}
                    <span style={{ fontSize: "12px" }}>
                      {t(`trend.${p.trend.direction}`, lang)}
                    </span>
                  </td>
                  <td>
                    {Object.entries(p.triggered_params).length > 0 ? (
                      Object.entries(p.triggered_params).map(([param, val]) => (
                        <span
                          key={param}
                          className={`deviations-tag ${p.level === "amber" ? "amber" : ""}`}
                        >
                          {param}: {val}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: "var(--color-muted)", fontSize: "12px" }}>
                        —
                      </span>
                    )}
                  </td>
                  <td>
                    {p.open_task ? (
                      <span className={`task-tag ${isUrgent ? "urgent" : ""}`}>
                        {t(`patients.task_${p.open_task.type}`, lang)} ·{" "}
                        {formatHoursLeft(p.open_task.due_at)}
                      </span>
                    ) : (
                      <span style={{ color: "var(--color-muted)", fontSize: "12px" }}>
                        —
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={() => onSelectPatient(p.id)}
                    >
                      {t("patients.btn_view", lang)}
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
