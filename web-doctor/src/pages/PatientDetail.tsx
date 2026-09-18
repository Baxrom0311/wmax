import React, { useEffect, useState } from "react";
import { ConfirmModal } from "../components/ConfirmModal";
import { ParamChart } from "../components/ParamChart";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { approveBaseline, confirmTask, dischargePatient } from "../lib/api";
import type { PatientDetail as PatientDetailType } from "../lib/types";

interface PatientDetailPageProps {
  patient: PatientDetailType;
  onBack: () => void;
  onRefresh: () => Promise<void>;
  lang: Lang;
}

export const PatientDetailPage: React.FC<PatientDetailPageProps> = ({
  patient,
  onBack,
  onRefresh,
  lang,
}) => {
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isDischargeModalOpen, setIsDischargeModalOpen] = useState(false);
  const [approving, setApproving] = useState(false);
  const [discharging, setDischarging] = useState(false);
  const [, setTick] = useState(0);

  // Live timer tick every 10 seconds
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(timer);
  }, []);

  const activeTask = patient.tasks.find(
    (t) => t.status !== "done" && t.type === "active_call"
  );

  const formatCountdown = (dueAtIso: string) => {
    const diffMs = new Date(dueAtIso).getTime() - Date.now();
    if (diffMs <= 0) return t("patients.overdue", lang);
    const hours = Math.floor(diffMs / (3600 * 1000));
    const mins = Math.floor((diffMs % (3600 * 1000)) / (60 * 1000));
    return `${hours} soat ${mins} daqiqa qoldi`;
  };

  const isUrgent =
    activeTask &&
    new Date(activeTask.due_at).getTime() - Date.now() < 4 * 3600 * 1000;

  const isOverdue =
    activeTask && new Date(activeTask.due_at).getTime() - Date.now() <= 0;

  const handleApproveBaseline = async () => {
    setApproving(true);
    try {
      await approveBaseline(patient.id);
      await onRefresh();
    } finally {
      setApproving(false);
    }
  };

  const handleDischargePatient = async () => {
    setDischarging(true);
    try {
      await dischargePatient(patient.id);
      setIsDischargeModalOpen(false);
      await onRefresh();
    } finally {
      setDischarging(false);
    }
  };

  const handleConfirmTask = async (note: string) => {
    if (!activeTask) return;
    await confirmTask(activeTask.id, note);
    await onRefresh();
  };

  return (
    <div className="doc-container">
      {/* 1. Back link */}
      <button type="button" className="back-link" onClick={onBack}>
        {t("detail.back", lang)}
      </button>

      {/* 2. Clinical Passport Header */}
      <div className="detail-title-bar">
        <div className="patient-main-info">
          <h1>
            <span className={`status-dot ${patient.level}`} style={{ width: "14px", height: "14px" }} />
            {patient.full_name}
            <span style={{ fontSize: "14px", fontWeight: 400, color: "var(--color-muted)" }}>
              ({patient.age} yosh, {patient.sex === "m" ? "Erkak" : "Ayol"}, {patient.district})
            </span>
          </h1>
          <div className="patient-sub-info">
            <span><strong>Tashxis:</strong> {patient.diagnosis}</span>
            <span>
              <strong>Bosqich:</strong> {t(`detail.phase_${patient.phase}`, lang)}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {!activeTask && (
            <button
              type="button"
              className="btn btn-outline"
              style={{ borderColor: "var(--color-attention)", color: "var(--color-attention)" }}
              onClick={() => setIsDischargeModalOpen(true)}
            >
              {t("detail.discharge_btn", lang)}
            </button>
          )}
          {patient.phase === "learning" && (
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleApproveBaseline}
              disabled={approving}
            >
              {approving ? "..." : t("detail.approve_baseline", lang)}
            </button>
          )}
          {patient.baseline_approved && (
            <span className="task-tag" style={{ color: "var(--color-good)" }}>
              ✓ {t("detail.baseline_approved", lang)}
            </span>
          )}
        </div>
      </div>

      {/* 3. 24-Hour Active Call Card (Problem 11) */}
      {activeTask && (
        <div
          className="active-call-widget"
          style={{
            borderColor: isOverdue ? "var(--color-risk)" : isUrgent ? "var(--color-attention)" : "var(--color-good)",
            backgroundColor: isOverdue ? "#FDF2F2" : "#FFFDF9",
          }}
        >
          <div className="active-call-left">
            <h3 style={{ color: isOverdue ? "var(--color-risk)" : "var(--color-attention)" }}>
              {t("detail.active_call_card", lang)}
              {isOverdue && <span style={{ marginLeft: "8px", fontSize: "12px", color: "var(--color-risk)" }}>(MUDDATI O'TGAN)</span>}
            </h3>
            <p style={{ fontSize: "13px", color: "var(--color-muted)" }}>
              {t("detail.active_call_desc", lang)}
            </p>
            <div className="active-call-timer" style={{ marginTop: "6px" }}>
              ⏳ {formatCountdown(activeTask.due_at)}
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsConfirmModalOpen(true)}
          >
            {t("detail.confirm_visit", lang)}
          </button>
        </div>
      )}

      {/* 4. AI 72-Hour Prognosis & Problem Breakdown */}
      {patient.prognosis && (
        <div className="doc-ai-prognosis-card">
          <div className="prognosis-header-line">
            <span className="ai-engine-tag">AI CLINICAL ENGINE</span>
            <span
              className="risk-pct-pill"
              style={{
                color: patient.prognosis.risk_level === "high" ? "var(--color-risk)" : "var(--color-attention)",
              }}
            >
              {t("detail.risk_prob", lang)}: {patient.prognosis.risk_probability_pct}%
            </span>
          </div>
          <h3 style={{ fontSize: "16px", fontWeight: 700, margin: "8px 0 4px" }}>
            {t("detail.prognosis_header", lang)}
          </h3>
          <p style={{ fontSize: "14px", color: "var(--color-text)", lineHeight: 1.5 }}>
            {patient.prognosis.summary}
          </p>
          <p style={{ fontSize: "13px", color: "var(--color-muted)", marginTop: "6px" }}>
            💡 <strong>Tavsiya:</strong> {patient.prognosis.recommendation}
          </p>

          {/* Root-cause problems */}
          {patient.problems && patient.problems.length > 0 && (
            <div className="doc-problems-list">
              {patient.problems.map((pr, i) => (
                <div key={i} className="doc-problem-chip">
                  <strong>{pr.label}:</strong> {pr.deviation} ({pr.current_value} vs {pr.baseline_range}) —{" "}
                  <span style={{ color: "var(--color-muted)" }}>{pr.explanation}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 5. Multi-Row 7-Day Physiological Charts with Baseline Corridors */}
      <div className="charts-grid">
        <h3 style={{ fontSize: "17px", fontWeight: 700, marginTop: "12px" }}>
          {t("detail.vitals_history", lang)}
        </h3>

        {patient.series.map((s) => (
          <ParamChart key={s.param} series={s} />
        ))}
      </div>

      {/* 6. Alerts History & Isolation Forest AI Advisory */}
      {patient.alerts && patient.alerts.length > 0 && (
        <div className="alerts-card">
          <h3 className="alerts-title">{t("detail.alerts_history", lang)}</h3>
          {patient.alerts.map((a) => (
            <div key={a.id} className="alert-item">
              <div>
                <span className={`status-dot ${a.level}`} />
                <strong>{new Date(a.ts).toLocaleString()}</strong> — {a.reason}
                {a.anomaly_score !== null && (
                  <span
                    style={{
                      marginLeft: "10px",
                      fontSize: "11px",
                      color: "var(--color-muted)",
                      backgroundColor: "#F0EFEB",
                      padding: "2px 6px",
                      borderRadius: "3px",
                    }}
                  >
                    IsolationForest: {Math.round(a.anomaly_score * 100)}% (advisory)
                  </span>
                )}
              </div>
              <span style={{ fontWeight: 600 }}>Score: {a.composite_score}</span>
            </div>
          ))}
        </div>
      )}

      {/* Confirm active call modal */}
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleConfirmTask}
        lang={lang}
      />

      {/* Discharge confirm modal */}
      {isDischargeModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsDischargeModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{t("detail.discharge_confirm_title", lang)}</h2>
            <p style={{ fontSize: "14px", color: "var(--color-text)", lineHeight: 1.5, marginBottom: "20px" }}>
              {t("detail.discharge_confirm_desc", lang)}
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setIsDischargeModalOpen(false)}
                disabled={discharging}
              >
                {t("confirm_modal.cancel", lang)}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleDischargePatient}
                disabled={discharging}
              >
                {discharging ? "..." : t("detail.discharge_confirm_submit", lang)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
