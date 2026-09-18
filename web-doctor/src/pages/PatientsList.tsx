import React from "react";
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
  const attentionPatients = patients.filter(
    (p) => p.level === "red" || p.level === "amber"
  );

  const formatHoursLeft = (dueAtIso: string) => {
    const diffHours = Math.round(
      (new Date(dueAtIso).getTime() - Date.now()) / (3600 * 1000)
    );
    if (diffHours <= 0) return t("patients.overdue", lang);
    return t("patients.hours_left", lang, { h: diffHours });
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

      {/* 2. High Density Worklist Table */}
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
            {patients.map((p) => {
              const trendArrow =
                p.trend.direction === "worsening"
                  ? "↘"
                  : p.trend.direction === "improving"
                  ? "↗"
                  : "→";

              const isUrgent =
                p.level === "red" ||
                (p.open_task &&
                  new Date(p.open_task.due_at).getTime() - Date.now() < 6 * 3600 * 1000);

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
                  <td>{p.age}y</td>
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
