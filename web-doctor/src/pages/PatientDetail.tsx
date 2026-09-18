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
      {/* 1. Breadcrumbs Navigation */}
      <div className="detail-breadcrumb">
        <button type="button" className="back-link" onClick={onBack}>
          <span className="back-arrow">←</span>
          <span>{t("detail.back", lang)}</span>
        </button>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{patient.full_name}</span>
      </div>

      {/* 2. Clinical Passport Header */}
      <div className="detail-title-bar">
        <div className="patient-passport-left">
          <div className="patient-lg-avatar">
            {patient.full_name
              .split(" ")
              .map((w) => w[0])
              .slice(0, 2)
              .join("")}
          </div>
          <div className="patient-main-info">
            <div className="patient-name-title-row">
              <h1>{patient.full_name}</h1>
              <span className={`status-pill ${patient.level}`}>
                <span className={`status-dot ${patient.level}`} />
                {t(`state.${patient.level}`, lang)}
              </span>
            </div>
            <div className="patient-sub-info">
              <span className="passport-meta-item">
                <strong>Yosh / Jins:</strong> {patient.age} yosh, {patient.sex === "m" ? "Erkak" : "Ayol"}
              </span>
              <span className="passport-meta-item">
                <strong>Tuman:</strong> {patient.district}
              </span>
              <span className="passport-meta-item">
                <strong>Tashxis:</strong> <span className="diagnosis-highlight">{patient.diagnosis}</span>
              </span>
              <span className="passport-meta-item">
                <strong>Bosqich:</strong>{" "}
                <span className={`phase-tag ${patient.phase}`}>
                  {t(`detail.phase_${patient.phase}`, lang)}
                </span>
              </span>
            </div>
          </div>
        </div>

        <div className="passport-actions-right">
          {!activeTask && (
            <button
              type="button"
              className="btn btn-discharge"
              onClick={() => setIsDischargeModalOpen(true)}
            >
              <span className="btn-icon">📋</span>
              <span>{t("detail.discharge_btn", lang)}</span>
            </button>
          )}
          {patient.phase === "learning" && (
            <button
              type="button"
              className="btn btn-approve-baseline"
              onClick={handleApproveBaseline}
              disabled={approving}
            >
              <span className="btn-icon">✓</span>
              <span>{approving ? "..." : t("detail.approve_baseline", lang)}</span>
            </button>
          )}
          {patient.baseline_approved && (
            <span className="baseline-approved-badge">
              <span className="check-icon">✓</span>
              <span>{t("detail.baseline_approved", lang)}</span>
            </span>
          )}
        </div>
      </div>

      {/* 3. 24-Hour Active Call Card (Problem 11) */}
      {activeTask && (
        <div
          className={`active-call-widget ${isOverdue ? "overdue" : isUrgent ? "urgent" : "normal"}`}
        >
          <div className="active-call-left">
            <div className="active-call-title-row">
              <span className="active-call-pulse-icon">⏳</span>
              <h3>
                {t("detail.active_call_card", lang)}
                {isOverdue && <span className="overdue-pill">MUDDATI O'TGAN</span>}
                {isUrgent && !isOverdue && <span className="urgent-pill">SHOSHILINCH (&lt; 4 soat)</span>}
              </h3>
            </div>
            <p className="active-call-desc">
              {t("detail.active_call_desc", lang)}
            </p>
            <div className="active-call-timer">
              <span className="timer-icon">🕒</span>
              <span className="timer-val">{formatCountdown(activeTask.due_at)}</span>
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary btn-confirm-visit"
            onClick={() => setIsConfirmModalOpen(true)}
          >
            <span>{t("detail.confirm_visit", lang)}</span>
            <span className="btn-arrow">✓</span>
          </button>
        </div>
      )}

      {/* 4. AI 72-Hour Prognosis & Problem Breakdown */}
      {patient.prognosis && (
        <div className="doc-ai-prognosis-card">
          <div className="prognosis-header-line">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="ai-engine-tag">AI CLINICAL ENGINE (XORAZM WMAX)</span>
              <span className="ai-model-tag">CIRCADIAN 72H</span>
            </div>
            <span
              className={`risk-pct-pill ${patient.prognosis.risk_level}`}
            >
              {t("detail.risk_prob", lang)}: <strong>{patient.prognosis.risk_probability_pct}%</strong>
            </span>
          </div>

          {/* Visual Risk Meter */}
          <div className="risk-meter-bar">
            <div
              className={`risk-meter-fill ${patient.prognosis.risk_level}`}
              style={{ width: `${patient.prognosis.risk_probability_pct}%` }}
            />
          </div>

          <h3 className="prognosis-title-text">
            {t("detail.prognosis_header", lang)}
          </h3>
          <p className="prognosis-summary-text">
            {patient.prognosis.summary}
          </p>
          <div className="prognosis-recommendation-box">
            <span className="rec-bulb-icon">💡</span>
            <div>
              <strong>Klinik tavsiya:</strong> {patient.prognosis.recommendation}
            </div>
          </div>

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
