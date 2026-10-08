import React, { useState } from "react";
import {
  Check,
  Clock,
  Activity,
  MapPin,
  CheckCircle2,
  Building2,
  UserCheck,
  Stethoscope,
  Pill,
  FileText,
  FileEdit,
} from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

export interface HandoffItem {
  id: string;
  patient_id: string;
  patient_name: string;
  age: number;
  sex: "m" | "f";
  diagnosis: string;
  from_facility: string;
  from_department: string;
  discharged_by: string;
  discharged_at: string;
  to_facility: string;
  to_district: string;
  to_mahalla: string;
  assigned_nurse: string;
  assigned_doctor: string;
  status: "pending_ack" | "in_patronage" | "completed";
  due_hours_left: number;
  triage_level: "red" | "amber" | "green";
  vitals: {
    hr: number;
    spo2: number;
    bp?: string;
  };
  discharge_notes: string;
  medications: string[];
}

const INITIAL_HANDOFFS: HandoffItem[] = [
  {
    id: "h-001",
    patient_id: "p-001-red",
    patient_name: "Otabek Rahimov",
    age: 68,
    sex: "m",
    diagnosis: "Yurak ishemik kasalligi (YIK). Zo'riqish stenokardiyasi FK III. Postinfarkt kardioskleroz. SYuYe IIB bosqich.",
    from_facility: "Urganch Kardiologiya Dispanseri",
    from_department: "O'tkir infarkt va reabilitatsiya bo'limi",
    discharged_by: "Dr. Islom Yusupov",
    discharged_at: "Bugun, 08:30",
    to_facility: "Urganch shahar 1-son OP (OvaBMU)",
    to_district: "Urganch",
    to_mahalla: "Navbahor MFY, Al-Xorazmiy ko'chasi 45-uy",
    assigned_nurse: "Hamshira Dilnoza Otajonova",
    assigned_doctor: "Dr. S. Ahmedov (Oilaviy shifokor)",
    status: "pending_ack",
    due_hours_left: 19,
    triage_level: "red",
    vitals: { hr: 112, spo2: 87, bp: "140/90" },
    discharge_notes: "Statsionardan chiqarildi. SpO2 va puls bo'yicha tebranishlar kuzatilgan. 24 soat ichida soat taqilishini va tonomatrda qon bosimini tekshirish shart.",
    medications: ["Bisoprolol 5mg (ertalab)", "Klopidogrel 75mg", "Atorvastatin 40mg"],
  },
  {
    id: "h-002",
    patient_id: "p-002-amber",
    patient_name: "Gulnora Matyoqubova",
    age: 72,
    sex: "f",
    diagnosis: "Gipertoniya kasalligi III bosqich, 3-daraja, xavf IV (o'ta yuqori). 2-tur qandli diabet, subkompensatsiya.",
    from_facility: "Urganch Kardiologiya Dispanseri",
    from_department: "Arterial gipertoniya bo'limi",
    discharged_by: "Dr. M. Qosimov",
    discharged_at: "Kecha, 16:00",
    to_facility: "Xiva tuman Markaziy Poliklinikasi",
    to_district: "Xiva",
    to_mahalla: "Ichan Qal'a MFY, P. Mahmud ko'chasi 12-uy",
    assigned_nurse: "Hamshira Dilnoza Otajonova",
    assigned_doctor: "Dr. N. Saidova (Oilaviy shifokor)",
    status: "in_patronage",
    due_hours_left: 4,
    triage_level: "amber",
    vitals: { hr: 94, spo2: 95, bp: "155/95" },
    discharge_notes: "Qon bosimi krizdan so'ng nazorat ostida. Dori ichish va tuz cheklovi bo'yicha patronaj ko'rsatmasi berilgan.",
    medications: ["Ramipril 2.5mg (kechqurun)", "Amlodipin 5mg", "Metformin 850mg"],
  },
];

interface HandoffsPageProps {
  lang: Lang;
  onSelectPatient?: (patientId: string) => void;
  role?: string;
}

export const HandoffsPage: React.FC<HandoffsPageProps> = ({
  lang,
  onSelectPatient,
  role = "doctor",
}) => {
  const [items, setItems] = useState<HandoffItem[]>(INITIAL_HANDOFFS);
  const [filter, setFilter] = useState<"all" | "pending_ack" | "in_patronage">("all");
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const handleAcknowledge = (id: string, name: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "in_patronage" as const } : item
      )
    );
    showToast(
      lang === "ru"
        ? `Пациент ${name} принят. 24-часовой патронаж начат.`
        : `Bemor ${name} qabul qilindi. 24 soatlik patronaj akti ochildi.`
    );
  };

  const handleCompletePatronage = (id: string, name: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "completed" as const } : item
      )
    );
    showToast(
      lang === "ru"
        ? `Патронаж для ${name} успешно зарегистрирован!`
        : `Bemor ${name} uchun 1-patronaj muvaffaqiyatli yakunlandi!`
    );
  };

  const filteredItems = items.filter((item) => {
    if (filter === "all") return true;
    return item.status === filter;
  });

  const pendingCount = items.filter((i) => i.status === "pending_ack").length;
  const inPatronageCount = items.filter((i) => i.status === "in_patronage").length;
  const completedCount = items.filter((i) => i.status === "completed").length;

  const isNurse = role === "nurse";

  const title = isNurse ? t("handoffs.title_nurse", lang) : t("handoffs.title_doctor", lang);
  const lead = isNurse ? t("handoffs.lead_nurse", lang) : t("handoffs.lead_doctor", lang);

  return (
    <div className="doc-container">
      {/* Toast */}
      {toast && (
        <div className="doc-toast-notification">
          <span className="toast-icon"><Check size={16} /></span>
          <span>{toast}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="page-head" style={{ marginBottom: 20 }}>
        <h1 className="page-title">{title}</h1>
        <p className="page-lead">{lead}</p>
      </div>

      {/* KPI Stats Bar */}
      <div className="handoff-kpi-bar">
        <div className="handoff-kpi-item">
          <span className="kpi-num">{items.length}</span>
          <span className="kpi-label">{t("handoffs.kpi_total", lang)}</span>
        </div>
        <div className="handoff-kpi-item warning">
          <span className="kpi-num">{pendingCount}</span>
          <span className="kpi-label">{t("handoffs.kpi_pending", lang)}</span>
        </div>
        <div className="handoff-kpi-item active">
          <span className="kpi-num">{inPatronageCount}</span>
          <span className="kpi-label">{t("handoffs.kpi_active", lang)}</span>
        </div>
        <div className="handoff-kpi-item success">
          <span className="kpi-num">{completedCount}</span>
          <span className="kpi-label">{t("handoffs.kpi_completed", lang)}</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="handoff-filters-row">
        <button
          type="button"
          className={`handoff-filter-btn ${filter === "all" ? "active" : ""}`}
          onClick={() => setFilter("all")}
        >
          {t("handoffs.tab_all", lang)} ({items.length})
        </button>
        <button
          type="button"
          className={`handoff-filter-btn ${filter === "pending_ack" ? "active" : ""}`}
          onClick={() => setFilter("pending_ack")}
        >
          <Clock size={14} />
          <span>{t("handoffs.tab_pending", lang)} ({pendingCount})</span>
        </button>
        <button
          type="button"
          className={`handoff-filter-btn ${filter === "in_patronage" ? "active" : ""}`}
          onClick={() => setFilter("in_patronage")}
        >
          <Activity size={14} />
          <span>{t("handoffs.tab_active", lang)} ({inPatronageCount})</span>
        </button>
      </div>

      {/* Patients List / Cards */}
      {filteredItems.length === 0 ? (
        <div className="handoff-empty" style={{ marginTop: 16 }}>
          <h2 className="handoff-empty-title">
            {t("handoffs.empty_title", lang)}
          </h2>
          <p className="handoff-empty-body">
            {t("handoffs.empty_desc", lang)}
          </p>
        </div>
      ) : (
        <div className="handoff-cards-grid">
          {filteredItems.map((item) => {
            const isRed = item.triage_level === "red";
            const isPending = item.status === "pending_ack";
            const isInProgress = item.status === "in_patronage";
            const isDone = item.status === "completed";

            return (
              <div key={item.id} className={`handoff-card ${isRed ? "border-red" : "border-amber"}`}>
                {/* Top Strip */}
                <div className="handoff-card-header">
                  <div className="handoff-patient-info">
                    <div className="patient-name-line">
                      <span className="patient-name-title">{item.patient_name}</span>
                      <span className="patient-age-tag">
                        {t("patients.age_years", lang, { age: item.age })} · {item.sex === "m" ? t("patients.sex_male", lang) : t("patients.sex_female", lang)}
                      </span>
                      <span className={`handoff-badge level-${item.triage_level}`}>
                        {item.triage_level.toUpperCase()}
                      </span>
                    </div>
                    <div className="patient-location-line">
                      <MapPin size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                      <span><b>{item.to_district}</b>, {item.to_mahalla}</span>
                    </div>
                  </div>

                  {/* 24-hour Patronage Timer */}
                  <div className="handoff-timer-badge">
                    {isDone ? (
                      <span className="timer-pill done">
                        <CheckCircle2 size={13} />
                        <span>{t("handoffs.timer_done", lang)}</span>
                      </span>
                    ) : (
                      <span className={`timer-pill ${item.due_hours_left <= 6 ? "urgent" : "active"}`}>
                        <Clock size={13} />
                        <span>{t("handoffs.timer_left", lang, { h: item.due_hours_left })}</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Clinical Diagnosis & Vitals */}
                <div className="handoff-card-body">
                  <div className="diagnosis-box">
                    <span className="section-label">{t("detail.passport_diag", lang)}</span>
                    <p className="diagnosis-text">{item.diagnosis}</p>
                  </div>

                  {/* Vitals Summary Strip */}
                  <div className="vitals-strip">
                    <div className="vital-item">
                      <span className="vital-lbl">SpO2:</span>
                      <span className={`vital-val ${item.vitals.spo2 < 90 ? "text-red" : "text-green"}`}>
                        {item.vitals.spo2}%
                      </span>
                    </div>
                    <div className="vital-item">
                      <span className="vital-lbl">{lang === "ru" ? "Пульс:" : lang === "en" ? "Pulse:" : "Puls:"}</span>
                      <span className={`vital-val ${item.vitals.hr > 100 ? "text-red" : ""}`}>
                        {item.vitals.hr} bpm
                      </span>
                    </div>
                    {item.vitals.bp && (
                      <div className="vital-item">
                        <span className="vital-lbl">{lang === "ru" ? "АД:" : lang === "en" ? "BP:" : "Qon bosimi:"}</span>
                        <span className="vital-val">{item.vitals.bp} mmHg</span>
                      </div>
                    )}
                    <div className="vital-item facility-meta">
                      <span className="vital-lbl">{t("handoffs.discharged_by", lang)}</span>
                      <span className="vital-val">{item.discharged_by} ({item.from_department})</span>
                    </div>
                  </div>

                  {/* Responsible Team */}
                  <div className="responsible-row">
                    <div className="resp-col">
                      <span className="resp-lbl"><Building2 size={13} /> {t("handoffs.assigned_facility", lang)}</span>
                      <span className="resp-val">{item.to_facility}</span>
                    </div>
                    <div className="resp-col">
                      <span className="resp-lbl"><UserCheck size={13} /> {t("handoffs.assigned_nurse", lang)}</span>
                      <span className="resp-val">{item.assigned_nurse}</span>
                    </div>
                    <div className="resp-col">
                      <span className="resp-lbl"><Stethoscope size={13} /> {t("handoffs.assigned_doctor", lang)}</span>
                      <span className="resp-val">{item.assigned_doctor}</span>
                    </div>
                  </div>

                  {/* Discharge notes */}
                  <div className="notes-box">
                    <span className="section-label">{t("handoffs.epicrisis", lang)}</span>
                    <p className="notes-text">{item.discharge_notes}</p>
                  </div>

                  {/* Prescribed Meds */}
                  <div className="meds-tags">
                    <span className="section-label" style={{ marginRight: 6 }}>{t("handoffs.recommended_meds", lang)}</span>
                    {item.medications.map((m) => (
                      <span key={m} className="med-tag">
                        <Pill size={12} />
                        <span>{m}</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Action Buttons Footer */}
                <div className="handoff-card-footer">
                  <div className="status-indicator">
                    {isPending && (
                      <span className="status-dot-pending">
                        <Clock size={13} />
                        <span>{t("handoffs.status_pending_desc", lang)}</span>
                      </span>
                    )}
                    {isInProgress && (
                      <span className="status-dot-progress">
                        <Activity size={13} />
                        <span>{t("handoffs.status_progress_desc", lang)}</span>
                      </span>
                    )}
                    {isDone && (
                      <span className="status-dot-done">
                        <CheckCircle2 size={13} />
                        <span>{t("handoffs.status_done_desc", lang)}</span>
                      </span>
                    )}
                  </div>

                  <div className="handoff-actions-group">
                    {onSelectPatient && (
                      <button
                        type="button"
                        className="btn-handoff-profile"
                        onClick={() => onSelectPatient(item.patient_id)}
                      >
                        <FileText size={14} />
                        <span>{t("handoffs.btn_chart", lang)}</span>
                      </button>
                    )}

                    {isPending && (
                      <button
                        type="button"
                        className="btn-handoff-ack"
                        onClick={() => handleAcknowledge(item.id, item.patient_name)}
                      >
                        <Check size={14} />
                        <span>{t("handoffs.btn_ack", lang)}</span>
                      </button>
                    )}

                    {isInProgress && (
                      <button
                        type="button"
                        className="btn-handoff-complete"
                        onClick={() => handleCompletePatronage(item.id, item.patient_name)}
                      >
                        <FileEdit size={14} />
                        <span>{t("handoffs.btn_complete", lang)}</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Workflow Explainer at bottom */}
      <div className="handoff-bottom-workflow">
        <h3 className="workflow-title">
          {t("handoffs.workflow_title", lang)}
        </h3>
        <div className="workflow-steps-row">
          <div className="wf-step-item">
            <span className="wf-num">1</span>
            <span className="wf-title">{t("handoffs.step1_title", lang)}</span>
            <span className="wf-desc">{t("handoffs.step1_desc", lang)}</span>
          </div>
          <div className="wf-step-item">
            <span className="wf-num">2</span>
            <span className="wf-title">{t("handoffs.step2_title", lang)}</span>
            <span className="wf-desc">{t("handoffs.step2_desc", lang)}</span>
          </div>
          <div className="wf-step-item">
            <span className="wf-num">3</span>
            <span className="wf-title">{t("handoffs.step3_title", lang)}</span>
            <span className="wf-desc">{t("handoffs.step3_desc", lang)}</span>
          </div>
          <div className="wf-step-item">
            <span className="wf-num">4</span>
            <span className="wf-title">{t("handoffs.step4_title", lang)}</span>
            <span className="wf-desc">{t("handoffs.step4_desc", lang)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
