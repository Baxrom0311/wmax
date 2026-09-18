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
    if (diffMs <= 0) return "Muddati o'tgan";
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

  const handlePrint = () => {
    window.print();
  };

  const patientCode = `K-2026/${patient.id.replace(/-/g, "").slice(0, 4).toUpperCase()}`;

  return (
    <div className="doc-container patient-detail-official">
      {/* 1. Official Breadcrumb Navigation */}
      <div className="official-breadcrumb no-print">
        <button type="button" className="btn-back-link" onClick={onBack}>
          <span className="back-arrow-icon">←</span>
          <span>Bemorlar ro'yxatiga qaytish</span>
        </button>
        <span className="breadcrumb-slash">/</span>
        <span className="breadcrumb-current-patient">
          {patient.full_name} ({patientCode})
        </span>
      </div>

      {/* 2. Official Clinical Case File Header (Bemorning kasallik varaqasi) */}
      <div className="clinical-passport-card">
        <div className="passport-institution-line">
          <span>O'ZBEKISTON RESPUBLIKASI SSV · XORAZM VILOYATI KARDIOLOGIYA DISPANSERI</span>
          <span className="passport-card-no">TIBBIY KARTA № {patientCode}</span>
        </div>

        <div className="passport-body">
          <div className="passport-main">
            <div className="passport-name-row">
              <h1 className="patient-name-heading">{patient.full_name}</h1>
              <span className={`status-badge-official large ${patient.level}`}>
                <span className={`status-badge-dot ${patient.level}`} />
                {t(`state.${patient.level}`, lang).toUpperCase()}
              </span>
            </div>

            <div className="passport-grid-meta">
              <div className="meta-field">
                <span className="meta-label">Yosh / Jins:</span>
                <span className="meta-value">{patient.age} yosh, {patient.sex === "m" ? "Erkak" : "Ayol"}</span>
              </div>
              <div className="meta-field">
                <span className="meta-label">Tuman / Manzil:</span>
                <span className="meta-value">{patient.district}</span>
              </div>
              <div className="meta-field">
                <span className="meta-label">Klinik tashxis:</span>
                <span className="meta-value text-bold">{patient.diagnosis}</span>
              </div>
              <div className="meta-field">
                <span className="meta-label">Monitoring bosqichi:</span>
                <span className="meta-value">
                  <span className={`phase-tag-official ${patient.phase}`}>
                    {t(`detail.phase_${patient.phase}`, lang)}
                  </span>
                </span>
              </div>
            </div>
          </div>

          <div className="passport-actions no-print">
            <button
              type="button"
              className="btn-clinical btn-print"
              onClick={handlePrint}
              title="Klinik epikrizni chop etish"
            >
              <span>Chop etish</span>
            </button>

            {!activeTask && (
              <button
                type="button"
                className="btn-clinical btn-discharge-official"
                onClick={() => setIsDischargeModalOpen(true)}
              >
                <span>Statsionardan chiqarish</span>
              </button>
            )}

            {patient.phase === "learning" && (
              <button
                type="button"
                className="btn-clinical btn-approve-official"
                onClick={handleApproveBaseline}
                disabled={approving}
              >
                <span>{approving ? "Saqlanmoqda..." : "Bazaviy normani tasdiqlash"}</span>
              </button>
            )}

            {patient.baseline_approved && (
              <span className="badge-baseline-confirmed">
                <span>Normativ baza tasdiqlangan</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 3. 24-Hour Clinical Protocol Alert (Problem 11) */}
      {activeTask && (
        <div className={`clinical-protocol-alert ${isOverdue ? "overdue" : isUrgent ? "urgent" : "active"}`}>
          <div className="protocol-alert-left">
            <div className="protocol-header-tag">
              <span className="protocol-badge">PROTOKOL #CP-24H</span>
              <span className="protocol-type">SHOSHILINCH PATRONAJ CHAQUROVI</span>
              {isOverdue && <span className="tag-overdue">MUDDATI O'TGAN</span>}
              {isUrgent && !isOverdue && <span className="tag-urgent">DIQQAT (&lt; 4 soat)</span>}
            </div>
            <p className="protocol-desc">
              Kardiologiya dispanseri shifokori tomonidan 24 soat ichida bemor bilan bevosita
              yoki masofaviy klinik ko'rik o'tkazilishi va xulosa kiritilishi shart.
            </p>
            <div className="protocol-timer">
              <span className="timer-label">Qolgan muddat:</span>
              <span className="timer-countdown">{formatCountdown(activeTask.due_at)}</span>
            </div>
          </div>

          <div className="protocol-alert-right no-print">
            <button
              type="button"
              className="btn-confirm-protocol"
              onClick={() => setIsConfirmModalOpen(true)}
            >
              Ko'rik hisobotini kiritish (Tasdiqlash)
            </button>
          </div>
        </div>
      )}

      {/* 4. CDSS (Clinical Decision Support System) 72-Hour Prognosis */}
      {patient.prognosis && (
        <div className="cdss-prognosis-panel">
          <div className="cdss-header">
            <div className="cdss-title-group">
              <span className="cdss-badge">CDSS KLINIK QAROR TIZIMI</span>
              <span className="cdss-model">CIRCADIAN-72H MULTI-PARAMETRIC ENGINE</span>
            </div>
            <div className="cdss-risk-indicator">
              <span className="risk-label">Dekommutatsiya xavfi ehtimoli:</span>
              <span className={`risk-probability-val ${patient.prognosis.risk_level}`}>
                {patient.prognosis.risk_probability_pct}%
              </span>
            </div>
          </div>

          {/* Exact Statistical Meter Track */}
          <div className="cdss-meter-track">
            <div
              className={`cdss-meter-fill ${patient.prognosis.risk_level}`}
              style={{ width: `${patient.prognosis.risk_probability_pct}%` }}
            />
          </div>

          <div className="cdss-content-grid">
            <div className="cdss-summary-box">
              <span className="box-title">KLINIK TAHLIL VA XULOSA:</span>
              <p className="cdss-summary-text">{patient.prognosis.summary}</p>
            </div>

            <div className="cdss-rec-box">
              <span className="box-title">TAVSIYA ETILADIGAN CHORALAR:</span>
              <p className="cdss-rec-text">{patient.prognosis.recommendation}</p>
            </div>
          </div>

          {/* Root-cause problems */}
          {patient.problems && patient.problems.length > 0 && (
            <div className="cdss-problems-section">
              <span className="problems-header-title">Aniqlangan patologik chetlanishlar:</span>
              <div className="problems-table-official">
                {patient.problems.map((pr, i) => (
                  <div key={i} className="problem-row-official">
                    <span className="pr-param">{pr.label}</span>
                    <span className="pr-deviation">{pr.deviation}</span>
                    <span className="pr-values">O'lchangan: <strong>{pr.current_value}</strong> / Baza: {pr.baseline_range}</span>
                    <span className="pr-desc">{pr.explanation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. Telemetric Physiological Charts with Shaded Baseline Corridors */}
      <div className="telemetry-section">
        <div className="telemetry-header">
          <h3 className="section-heading">UZLUKSIZ FIZIOLOGIK TELEMETRIYA GRAFIKLARI (OXIRGI 7 KUN)</h3>
          <span className="telemetry-sub-note">
            Soyalangan soha: bemorning shaxsiy normativ koridori (Median ± 2σ)
          </span>
        </div>

        <div className="telemetry-charts-grid">
          {patient.series.map((s) => (
            <ParamChart key={s.param} series={s} />
          ))}
        </div>
      </div>

      {/* 6. Alerts & Anomaly Audit Trail */}
      {patient.alerts && patient.alerts.length > 0 && (
        <div className="alerts-audit-panel">
          <h3 className="section-heading">KUZATUV PROTOKOLI VA SIGNALLAR TARIXI</h3>
          <div className="alerts-table">
            {patient.alerts.map((a) => (
              <div key={a.id} className="alert-row-official">
                <div className="alert-time-cell">
                  <span className={`status-badge-dot ${a.level}`} />
                  <code>{new Date(a.ts).toLocaleString("uz-UZ")}</code>
                </div>
                <div className="alert-reason-cell">
                  <span>{a.reason}</span>
                  {a.anomaly_score !== null && (
                    <span className="advisory-score-tag">
                      IsolationForest indeksi: {Math.round(a.anomaly_score * 100)}% (advisory)
                    </span>
                  )}
                </div>
                <div className="alert-score-cell">
                  Kompozit Z: <strong>{a.composite_score}</strong>
                </div>
              </div>
            ))}
          </div>
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
            <h2 className="modal-title">Bemor monitoringini yakunlash (Chiqarish)</h2>
            <p className="modal-desc">
              Bemor <strong>{patient.full_name}</strong> bo'yicha masofaviy telemetrik
              monitoring yakunlanadi va bemor reabilitatsiya rejasiga o'tkaziladi.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-clinical"
                onClick={() => setIsDischargeModalOpen(false)}
                disabled={discharging}
              >
                Bekor qilish
              </button>
              <button
                type="button"
                className="btn-clinical btn-discharge-submit"
                onClick={handleDischargePatient}
                disabled={discharging}
              >
                {discharging ? "Bajarilmoqda..." : "Tasdiqlash va chiqarish"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
