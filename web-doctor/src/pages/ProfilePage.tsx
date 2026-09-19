import React, { useState } from "react";
import {
  ArrowLeft,
  Check,
  Building2,
  Edit2,
  Stethoscope,
  User,
  ShieldCheck,
  LogOut,
  Phone,
  Clock,
  FileText,
  Users,
  Activity,
  HeartPulse,
} from "lucide-react";
import type { AuthRole } from "../lib/types";

interface ProfilePageProps {
  doctorName: string;
  role: AuthRole;
  onLogout: () => void;
  onBack: () => void;
}

interface DoctorProfileForm {
  fullName: string;
  specialty: string;
  organization: string;
  department: string;
  phone: string;
  workHours: string;
  licenseNumber: string;
}

const STORAGE_KEY = "wmax_doctor_profile_data";

function loadDoctorProfile(initialName: string, role: AuthRole): DoctorProfileForm {
  const defaults: DoctorProfileForm = {
    fullName: initialName || "Dr. Bahrom Alimov",
    specialty: role === "nurse" ? "Katta patronaj hamshirasi" : "Shifokor-kardiolog, Oliy toifa",
    organization: "Urganch Kardiologiya Dispanseri",
    department: role === "nurse" ? "Patronaj va ambulator monitoring bo'limi" : "O'tkir kardiologiya va reanimatsiya bo'limi",
    phone: "+998 90 123-45-67",
    workHours: "Dush – Shanba, 08:30 – 17:00",
    licenseNumber: "MED-UZ-2024-KARDIO-0419",
  };

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults;
    const parsed = JSON.parse(raw);
    return { ...defaults, ...parsed };
  } catch {
    return defaults;
  }
}

function saveDoctorProfile(data: DoctorProfileForm) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // ignore
  }
}

export const ProfilePage: React.FC<ProfilePageProps> = ({
  doctorName,
  role,
  onLogout,
  onBack,
}) => {
  const [form, setForm] = useState<DoctorProfileForm>(() =>
    loadDoctorProfile(doctorName, role)
  );
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<DoctorProfileForm>(form);
  const [saved, setSaved] = useState(false);

  const initials = form.fullName
    .split(" ")
    .filter((w) => !w.startsWith("Dr."))
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "BA";

  const handleEdit = () => {
    setDraft({ ...form });
    setEditing(true);
    setSaved(false);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setForm({ ...draft });
    saveDoctorProfile(draft);
    setEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  // Active monitored patients assigned to this clinical workstation
  const monitoredPatients = [
    {
      id: "p1",
      name: "Otabek Rahimov",
      age: 68,
      district: "Urganch",
      level: "red",
      statusText: "I Daraja (Shoshilinch dekompensatsiya)",
      task: "24h Aktiv patronaj",
    },
    {
      id: "p2",
      name: "Gulnora Matyoqubova",
      age: 72,
      district: "Xiva",
      level: "amber",
      statusText: "II Daraja (Klinik monitoring)",
      task: "Rejali kuzatuv",
    },
    {
      id: "p3",
      name: "Rustam Karimov",
      age: 59,
      district: "Xonqa",
      level: "green",
      statusText: "III Daraja (Barqaror remissiya)",
      task: "Rejali qabul",
    },
    {
      id: "p4",
      name: "Jumaniyoz Otajonov",
      age: 65,
      district: "Shovot",
      level: "no_data",
      statusText: "Telemetriya uzilgan",
      task: "Aloqani tiklash",
    },
  ];

  return (
    <div className="prof-page">
      {/* ── Top Bar ── */}
      <div className="prof-topbar">
        <button type="button" className="prof-back-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          <span>Bemorlar ro'yxatiga qaytish</span>
        </button>
        {saved && (
          <span className="prof-save-toast">
            <Check size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
            <span>O'zgarishlar muvaffaqiyatli saqlandi!</span>
          </span>
        )}
      </div>

      <div className="prof-content">
        {/* ── Left Column: Doctor Identity & Work Details ── */}
        <div className="prof-col-left">
          {/* Identity Card */}
          <div className="prof-card prof-identity-card">
            <div className="prof-avatar-xl">{initials}</div>

            {editing ? (
              <form onSubmit={handleSave} className="prof-edit-fields">
                <label className="prof-field-label">Shifokor F.I.Sh</label>
                <input
                  className="prof-field-input"
                  value={draft.fullName}
                  onChange={(e) => setDraft({ ...draft, fullName: e.target.value })}
                  placeholder="Dr. Bahrom Alimov"
                  required
                />

                <label className="prof-field-label">Mutaxassislik va toifa</label>
                <input
                  className="prof-field-input"
                  value={draft.specialty}
                  onChange={(e) => setDraft({ ...draft, specialty: e.target.value })}
                  placeholder="Shifokor-kardiolog, Oliy toifa"
                  required
                />

                <label className="prof-field-label">Tibbiy muassasa</label>
                <input
                  className="prof-field-input"
                  value={draft.organization}
                  onChange={(e) => setDraft({ ...draft, organization: e.target.value })}
                  placeholder="Urganch Kardiologiya Dispanseri"
                  required
                />

                <label className="prof-field-label">Bo'lim</label>
                <input
                  className="prof-field-input"
                  value={draft.department}
                  onChange={(e) => setDraft({ ...draft, department: e.target.value })}
                  placeholder="O'tkir kardiologiya bo'limi"
                />

                <label className="prof-field-label">Bog'lanish telefoni</label>
                <input
                  className="prof-field-input"
                  value={draft.phone}
                  onChange={(e) => setDraft({ ...draft, phone: e.target.value })}
                  placeholder="+998 90 123-45-67"
                />

                <label className="prof-field-label">Ish tartibi</label>
                <input
                  className="prof-field-input"
                  value={draft.workHours}
                  onChange={(e) => setDraft({ ...draft, workHours: e.target.value })}
                  placeholder="Dush – Shanba, 08:30 – 17:00"
                />

                <div className="prof-edit-actions">
                  <button type="submit" className="prof-btn-save">
                    <Check size={14} style={{ marginRight: 4 }} />
                    <span>Saqlash</span>
                  </button>
                  <button type="button" className="prof-btn-cancel" onClick={handleCancel}>
                    Bekor qilish
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="prof-display-name">{form.fullName}</div>
                <div className="prof-display-specialty">{form.specialty}</div>

                <div className="prof-meta-list">
                  <div className="prof-meta-item">
                    <Building2 size={14} className="prof-meta-icon" />
                    <span>{form.organization}</span>
                  </div>
                  <div className="prof-meta-item">
                    <HeartPulse size={14} className="prof-meta-icon" />
                    <span>{form.department}</span>
                  </div>
                  <div className="prof-meta-item">
                    <Phone size={14} className="prof-meta-icon" />
                    <span>{form.phone}</span>
                  </div>
                  <div className="prof-meta-item">
                    <Clock size={14} className="prof-meta-icon" />
                    <span>{form.workHours}</span>
                  </div>
                  <div className="prof-meta-item">
                    <FileText size={14} className="prof-meta-icon" />
                    <span>Litsenziya: <b>{form.licenseNumber}</b></span>
                  </div>
                </div>

                <button type="button" className="prof-btn-edit" onClick={handleEdit}>
                  <Edit2 size={13} style={{ marginRight: 6 }} />
                  <span>Ma'lumotlarni tahrirlash</span>
                </button>
              </>
            )}
          </div>

          {/* System & Security Card */}
          <div className="prof-card prof-role-card">
            <div className="prof-role-row">
              <span className="prof-role-label">Tizim roli</span>
              <span className="prof-role-pill">
                {role === "nurse" ? (
                  <>
                    <Stethoscope size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                    <span>Hamshira</span>
                  </>
                ) : (
                  <>
                    <User size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                    <span>Shifokor-kardiolog</span>
                  </>
                )}
              </span>
            </div>
            <div className="prof-role-row">
              <span className="prof-role-label">Tizim holati</span>
              <span className="prof-env-pill">
                <span className="prof-env-dot" />
                Jonli (Production)
              </span>
            </div>
            <div className="prof-role-row">
              <span className="prof-role-label">Klinik xavfsizlik</span>
              <span className="prof-sec-pill">
                <ShieldCheck size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                <span>Himoyalangan (TLS 1.3)</span>
              </span>
            </div>
          </div>

          {/* Logout button */}
          <button type="button" className="prof-logout-btn" onClick={onLogout}>
            <LogOut size={15} style={{ marginRight: 6 }} />
            <span>Tizimdan chiqish</span>
          </button>
        </div>

        {/* ── Right Column: Clinic B2B License & Monitored Patients ── */}
        <div className="prof-col-right">
          {/* Clinic & B2B Agreement Card */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon prof-icon-license">
                <Building2 size={20} color="#0284c7" />
              </div>
              <div>
                <div className="prof-card-title">Klinika va B2B Shartnoma</div>
                <div className="prof-card-sub">WMAX telemetrik monitoring tizimi litsenziyasi</div>
              </div>
              <span className="prof-active-badge">FAOL</span>
            </div>

            <div className="prof-license-grid">
              <div className="prof-license-item">
                <span className="prof-lic-label">Tibbiy muassasa:</span>
                <span className="prof-lic-value">{form.organization}</span>
              </div>
              <div className="prof-license-item">
                <span className="prof-lic-label">Klinika monitoring rejimi:</span>
                <span className="prof-lic-value">OvaBMU / Statsionar kardiomonitoring</span>
              </div>
              <div className="prof-license-item">
                <span className="prof-lic-label">Umumiy bemorlar kvotasi:</span>
                <span className="prof-lic-value">100 ta bemor (oylik)</span>
              </div>
              <div className="prof-license-item">
                <span className="prof-lic-label">Litsenziya to'lovi:</span>
                <span className="prof-lic-value">85 000 so'm / oy (bemor boshiga)</span>
              </div>
            </div>
          </div>

          {/* Doctor's Active Monitored Patients */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon prof-icon-quota">
                <Users size={20} color="#16a34a" />
              </div>
              <div>
                <div className="prof-card-title">Klinik kuzatuvdagi bemorlar</div>
                <div className="prof-card-sub">
                  Shifokor nazoratidagi bemorlar holati va triaji ({monitoredPatients.length} nafar)
                </div>
              </div>
            </div>

            {/* Patients summary bar */}
            <div className="prof-patients-summary-bar">
              <div className="prof-summary-stat">
                <span className="prof-stat-num text-risk">1</span>
                <span className="prof-stat-lbl">I Daraja (Kritik)</span>
              </div>
              <div className="prof-summary-stat">
                <span className="prof-stat-num text-attention">1</span>
                <span className="prof-stat-lbl">II Daraja (Kuzatuv)</span>
              </div>
              <div className="prof-summary-stat">
                <span className="prof-stat-num text-good">1</span>
                <span className="prof-stat-lbl">III Daraja (Barqaror)</span>
              </div>
              <div className="prof-summary-stat">
                <span className="prof-stat-num text-muted">1</span>
                <span className="prof-stat-lbl">Telemetriya uzilgan</span>
              </div>
            </div>

            {/* Patients list */}
            <div className="prof-patients-list">
              {monitoredPatients.map((p) => (
                <div key={p.id} className={`prof-patient-row prof-patient-${p.level}`}>
                  <div className="prof-patient-main">
                    <div className="prof-patient-name-line">
                      <span className="prof-patient-name">{p.name}</span>
                      <span className="prof-patient-meta">
                        {p.age} yosh · {p.district}
                      </span>
                    </div>
                    <div className="prof-patient-sub">
                      <span className={`prof-status-dot ${p.level}`} />
                      <span>{p.statusText}</span>
                    </div>
                  </div>
                  <div className="prof-patient-task">
                    <span className="prof-task-pill">{p.task}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Clinical Shift & Alert Notifications */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon" style={{ background: "#fef3c7" }}>
                <Activity size={20} color="#d97706" />
              </div>
              <div>
                <div className="prof-card-title">Shifokor ogohlantirish kanallari</div>
                <div className="prof-card-sub">Kritik signallarni qabul qilish sozlamalari</div>
              </div>
            </div>

            <div className="prof-channels-grid">
              <div className="prof-channel-item">
                <div className="prof-channel-info">
                  <span className="prof-channel-title">Favqulodda SOS 103 Dispetcher</span>
                  <span className="prof-channel-desc">Bemor favqulodda tugmani bosganda ekranda to'g'ridan-to'g'ri chaqiruv</span>
                </div>
                <span className="prof-channel-active">Faol</span>
              </div>

              <div className="prof-channel-item">
                <div className="prof-channel-info">
                  <span className="prof-channel-title">Telegram Notifier Bot</span>
                  <span className="prof-channel-desc">Kritik dekompensatsiya va telemetriya uzilish xabarlari</span>
                </div>
                <span className="prof-channel-active">Ulangan</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
