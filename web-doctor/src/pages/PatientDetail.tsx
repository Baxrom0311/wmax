import React, { useEffect, useState } from "react";
import { ConfirmModal } from "../components/ConfirmModal";
import { NurseHandoverPanel } from "../components/NurseHandoverPanel";
import { ParamChart } from "../components/ParamChart";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { approveBaseline, confirmTask, dischargePatient, fetchNurseHandover, fetchPatientFullProfile } from "../lib/api";
import type { NurseHandoverSBAR, PatientDetail as PatientDetailType, PatientFullProfile } from "../lib/types";

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
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);
  const [approving, setApproving] = useState(false);
  const [discharging, setDischarging] = useState(false);
  const [, setTick] = useState(0);
  const [fullProfile, setFullProfile] = useState<PatientFullProfile | null>(null);
  const [activeTab, setActiveTab] = useState<"telemetry" | "profile" | "medications" | "admissions" | "nurse">("telemetry");
  const [nurseHandover, setNurseHandover] = useState<NurseHandoverSBAR | null>(null);
  const [nurseLoading, setNurseLoading] = useState(false);

  useEffect(() => {
    fetchPatientFullProfile(patient.id).then(setFullProfile).catch(() => {});
  }, [patient.id]);


  // Live timer tick every 10 seconds
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(timer);
  }, []);

  const activeTask = patient.tasks.find(
    (t) => t.status !== "done" && t.type === "active_call"
  );

  const formatCountdown = (dueAtIso: string) => {
    // oxlint-disable-next-line react/purity -- countdown intentionally reads wall-clock time
    const diffMs = new Date(dueAtIso).getTime() - Date.now();
    if (diffMs <= 0) return "Muddati o'tgan";
    const hours = Math.floor(diffMs / (3600 * 1000));
    const mins = Math.floor((diffMs % (3600 * 1000)) / (60 * 1000));
    return `${hours} soat ${mins} daqiqa qoldi`;
  };

  const isUrgent =
    activeTask &&
    // oxlint-disable-next-line react/purity -- urgency changes with wall-clock time
    new Date(activeTask.due_at).getTime() - Date.now() < 4 * 3600 * 1000;

  const isOverdue =
    // oxlint-disable-next-line react/purity -- overdue status changes with wall-clock time
    activeTask && new Date(activeTask.due_at).getTime() - Date.now() <= 0;

  const handleApproveBaseline = async () => {
    setApproving(true);
    try {
      await approveBaseline(patient.id);
      setIsApproveModalOpen(false);
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

      <div className="clinical-passport-card">
        <div className="passport-institution-line">
          <span className="passport-card-no">№ {patientCode}</span>
        </div>

        <div className="passport-body">
          <div className="passport-main">
            <div className="passport-name-row">
              <h1 className="patient-name-heading">{patient.full_name}</h1>
              <span className={`status-badge-official large ${patient.level}`}>
                <span className={`status-badge-dot ${patient.level}`} />
                {t(`state.${patient.level}`, lang)}
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
                onClick={() => setIsApproveModalOpen(true)}
                disabled={approving}
              >
                <span>{approving ? t("common.saving", lang) : t("detail.approve_baseline", lang)}</span>
              </button>
            )}

            {patient.baseline_approved && (
              <span className="badge-baseline-confirmed">
                <span>{t("detail.baseline_approved", lang)}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="patient-tabs-nav no-print">
        <button
          type="button"
          className={`patient-nav-tab ${activeTab === "telemetry" ? "active" : ""}`}
          onClick={() => setActiveTab("telemetry")}
        >
          {t("detail.tab_telemetry", lang)}
        </button>
        <button
          type="button"
          className={`patient-nav-tab ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          {t("detail.tab_profile", lang)}
        </button>
        <button
          type="button"
          className={`patient-nav-tab ${activeTab === "medications" ? "active" : ""}`}
          onClick={() => setActiveTab("medications")}
        >
          {t("detail.tab_medications", lang)}
        </button>
        <button
          type="button"
          className={`patient-nav-tab ${activeTab === "admissions" ? "active" : ""}`}
          onClick={() => setActiveTab("admissions")}
        >
          {t("detail.tab_risks", lang)}
        </button>
        <button
          type="button"
          className={`patient-nav-tab nurse-tab ${activeTab === "nurse" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("nurse");
            if (!nurseHandover && !nurseLoading) {
              setNurseLoading(true);
              fetchNurseHandover(patient.id)
                .then((data) => setNurseHandover(data))
                .catch(() => setNurseHandover(null))
                .finally(() => setNurseLoading(false));
            }
          }}
        >
          {t("detail.tab_nurse", lang)}
        </button>
      </div>

      {activeTab === "telemetry" && (
        <>
          {/* 3. 24-Hour Clinical Protocol Alert (Problem 11) */}
          {activeTask && (
            <div className={`clinical-protocol-alert ${isOverdue ? "overdue" : isUrgent ? "urgent" : "active"}`}>
          <div className="protocol-alert-left">
            <div className="protocol-header-tag">
              <span className="protocol-badge">{t("detail.emergency_patrol_call", lang)}</span>
              {isOverdue && <span className="tag-overdue">{t("detail.overdue", lang)}</span>}
              {isUrgent && !isOverdue && <span className="tag-urgent">{t("detail.urgent_sub_4h", lang)}</span>}
            </div>
            <div className="protocol-timer">
              <span className="timer-countdown">{formatCountdown(activeTask.due_at)}</span>
            </div>
          </div>

          <div className="protocol-alert-right no-print">
            <button
              type="button"
              className="btn-confirm-protocol"
              onClick={() => setIsConfirmModalOpen(true)}
            >
              {t("detail.submit_report_btn", lang)}
            </button>
          </div>
        </div>
      )}

      {patient.prognosis && (
        <div className="cdss-prognosis-panel">
          <div className="cdss-header">
            <div className="cdss-title-group">
              <span className="cdss-badge">{t("detail.cdss_badge", lang)}</span>
            </div>
            <div className="cdss-risk-indicator">
              <span className={`risk-probability-val ${patient.prognosis.risk_level}`}>
                {patient.prognosis.risk_probability_pct}%
              </span>
            </div>
          </div>

          <div className="cdss-meter-track">
            <div
              className={`cdss-meter-fill ${patient.prognosis.risk_level}`}
              style={{ width: `${patient.prognosis.risk_probability_pct}%` }}
            />
          </div>

          <div className="cdss-content-grid">
            <div className="cdss-summary-box">
              <p className="cdss-summary-text">{patient.prognosis.summary}</p>
            </div>

            <div className="cdss-rec-box">
              <p className="cdss-rec-text">{patient.prognosis.recommendation}</p>
            </div>
          </div>

          {patient.problems && patient.problems.length > 0 && (
            <div className="cdss-problems-section">
              <div className="problems-table-official">
                {patient.problems.map((pr, i) => (
                  <div key={i} className="problem-row-official">
                    <span className="pr-param">{pr.label}</span>
                    <span className="pr-deviation">{pr.deviation}</span>
                    <span className="pr-values">
                      {t("detail.measured_vs_baseline", lang, { curr: pr.current_value, base: pr.baseline_range })}
                    </span>
                    <span className="pr-desc">{pr.explanation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="telemetry-section">
        <div className="telemetry-charts-grid">
          {patient.series.map((s) => (
            <ParamChart key={s.param} series={s} lang={lang} />
          ))}
        </div>
      </div>

      {patient.alerts && patient.alerts.length > 0 && (
        <div className="alerts-audit-panel">
          <div className="alerts-table">
            {patient.alerts.map((a) => (
              <div key={a.id} className="alert-row-official">
                <div className="alert-time-cell">
                  <span className={`status-badge-dot ${a.level}`} />
                  <code>{new Date(a.ts).toLocaleString(lang === "ru" ? "ru-RU" : lang === "en" ? "en-US" : "uz-UZ")}</code>
                </div>
                <div className="alert-reason-cell">
                  <span>{a.reason}</span>
                </div>
                <div className="alert-score-cell">
                  <strong>{a.composite_score}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
        </>
      )}

      {activeTab === "profile" && (
        <div className="tab-panel-card">
          <div className="addresses-grid">
            {(fullProfile?.addresses || []).map((addr) => (
              <div key={addr.id} className={`address-detail-card ${addr.is_primary ? "primary-card" : ""}`}>
                <div className="addr-card-header">
                  <span className="addr-kind-badge">{addr.kind.toUpperCase()}</span>
                  {addr.is_primary && <span className="badge-primary-addr">Asosiy</span>}
                </div>

                <p className="addr-full-text">
                  <strong>{addr.district}</strong>{addr.street ? `, ${addr.street}` : ""}
                  {addr.house ? ` №${addr.house}` : ""}
                  {addr.flat ? `, ${addr.flat}-xonadon` : ""}
                </p>

                {addr.mahalla && (
                  <p className="addr-field-sub">
                    <strong>Mahalla:</strong> {addr.mahalla}
                  </p>
                )}

                {addr.landmark && (
                  <p className="addr-field-sub landmark-highlight">
                    <strong>Mo'ljal:</strong> {addr.landmark}
                  </p>
                )}

                {addr.entrance_note && (
                  <p className="addr-field-sub">
                    <strong>Kirish:</strong> {addr.entrance_note}
                  </p>
                )}

                {addr.lat && addr.lon && (
                  <div className="addr-gps-row">
                    <a
                      href={`https://maps.google.com/?q=${addr.lat},${addr.lon}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="addr-map-link"
                    >
                      Xaritada ↗
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "medications" && (
        <div className="tab-panel-card">
          <div className="meds-table-container">
            <table className="clinical-table-official">
              <thead>
                <tr>
                  <th>Dori</th>
                  <th>Doza</th>
                  <th>Vaqt</th>
                  <th>Parametr</th>
                  <th>Holat</th>
                </tr>
              </thead>
              <tbody>
                {(fullProfile?.medications || []).map((m) => (
                    <tr key={m.id}>
                      <td className="font-bold">{m.name}</td>
                      <td>{m.dose || "—"}</td>
                      <td>{m.frequency || "—"}</td>
                      <td>
                        {Object.entries(m.affects_params || {}).map(([param, eff]) => (
                          <span key={param} className="badge-param-tag">
                            {param.toUpperCase()} {eff === "lowers" ? "↓" : "↑"}
                          </span>
                        ))}
                      </td>
                      <td>
                        <span className={`status-pill ${m.stopped_at ? "stopped" : "active"}`}>
                          {m.stopped_at ? "To'xtatilgan" : "Faol"}
                        </span>
                      </td>
                    </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "admissions" && (
        <div className="tab-panel-card">
          <div className="profile-tri-grid">
            <div className="sub-profile-card">
              <h4>Allergiyalar</h4>
              {fullProfile?.allergies && fullProfile.allergies.length > 0 ? (
                <div className="allergies-list-box">
                  {fullProfile.allergies.map((al) => (
                    <div key={al.id} className={`allergy-item-chip severity-${al.severity}`}>
                      <div className="chip-header">
                        <strong>{al.substance}</strong>
                        <span className="severity-tag">{al.severity.toUpperCase()}</span>
                      </div>
                      {al.reaction && <p className="chip-reaction">{al.reaction}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-text">Yo'q</p>
              )}
            </div>

            <div className="sub-profile-card">
              <h4>Xavf omillari</h4>
              <div className="risk-factors-list">
                <div className="rf-row">
                  <span className="rf-label">Yolg'iz:</span>
                  <span className="rf-val">{fullProfile?.risk_factors?.lives_alone ? "Ha" : "Yo'q"}</span>
                </div>
                <div className="rf-row">
                  <span className="rf-label">Harakatchanlik:</span>
                  <span className="rf-val">{fullProfile?.risk_factors?.mobility || "Mustaqil"}</span>
                </div>
                <div className="rf-row">
                  <span className="rf-label">Diabet:</span>
                  <span className="rf-val">{fullProfile?.risk_factors?.diabetes ? "Bor" : "Yo'q"}</span>
                </div>
                <div className="rf-row">
                  <span className="rf-label">Buyrak (CKD):</span>
                  <span className="rf-val">{fullProfile?.risk_factors?.ckd ? "Bor" : "Yo'q"}</span>
                </div>
                <div className="rf-row">
                  <span className="rf-label">Chekish:</span>
                  <span className="rf-val">{fullProfile?.risk_factors?.smoking || "Yo'q"}</span>
                </div>
              </div>
            </div>

            <div className="sub-profile-card">
              <h4>Vazn</h4>
              {fullProfile?.measurements && fullProfile.measurements.length > 0 ? (
                <div className="measurements-history">
                  {fullProfile.measurements.map((m) => (
                    <div key={m.id} className="meas-row">
                      <span>{new Date(m.measured_at).toLocaleDateString()}</span>
                      <strong className="meas-weight">{m.weight_kg ? `${m.weight_kg} kg` : "—"}</strong>
                      <span className="meas-source">{m.source}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-text">Ma'lumot yo'q</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Nurse Handover SBAR Tab */}
      {activeTab === "nurse" && (
        <div className="tab-panel-card">
          {nurseLoading ? (
            <div className="nurse-loading-state">
              <div className="nurse-loading-spinner">⌛</div>
              <p>AI SBAR xisoboti tayyorlanmoqda…</p>
            </div>
          ) : nurseHandover ? (
            <NurseHandoverPanel
              handover={nurseHandover}
              patientName={patient.full_name}
              onRefresh={async () => {
                setNurseLoading(true);
                const fresh = await fetchNurseHandover(patient.id);
                setNurseHandover(fresh);
                setNurseLoading(false);
              }}
              lang={lang}
            />
          ) : (
            <div className="nurse-empty-state">
              <span className="nurse-empty-icon">🏥</span>
              <h3>Hamshira SBAR Xisoboti mavjud emas</h3>
              <p>AI xizmati vaqtincha mavjud emas yoki bemor uchun yetarli ma'lumot yo'q.</p>
              <button
                type="button"
                className="btn-clinical"
                onClick={() => {
                  setNurseLoading(true);
                  fetchNurseHandover(patient.id)
                    .then((data) => setNurseHandover(data))
                    .catch(() => setNurseHandover(null))
                    .finally(() => setNurseLoading(false));
                }}
              >
                Qayta urinish
              </button>
            </div>
          )}
        </div>
      )}


      <ConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleConfirmTask}
        lang={lang}
      />

      {/* Baseline approve modal */}
      {isApproveModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsApproveModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{t("detail.approve_modal_title", lang)}</h2>
            <p className="modal-desc">
              {t("detail.approve_modal_desc", lang)}
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-clinical"
                onClick={() => setIsApproveModalOpen(false)}
                disabled={approving}
              >
                {t("detail.approve_modal_cancel", lang)}
              </button>
              <button
                type="button"
                className="btn-clinical btn-approve-official"
                onClick={handleApproveBaseline}
                disabled={approving}
              >
                {approving ? "..." : t("detail.approve_modal_submit", lang)}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Discharge confirm modal */}
      {isDischargeModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsDischargeModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">{t("detail.discharge_modal_title", lang)}</h2>
            <p className="modal-desc">
              {t("detail.discharge_modal_desc", lang, { name: patient.full_name })}
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-clinical"
                onClick={() => setIsDischargeModalOpen(false)}
                disabled={discharging}
              >
                {t("detail.discharge_modal_cancel", lang)}
              </button>
              <button
                type="button"
                className="btn-clinical btn-discharge-submit"
                onClick={handleDischargePatient}
                disabled={discharging}
              >
                {discharging ? t("detail.discharging", lang) : t("detail.discharge_modal_submit", lang)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
