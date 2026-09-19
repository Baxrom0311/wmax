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
  BarChart3,
  Watch,
} from "lucide-react";
import type { AuthRole } from "../lib/types";

interface ProfilePageProps {
  doctorName: string;
  role: AuthRole;
  onLogout: () => void;
  onBack: () => void;
}

interface ProfileForm {
  fullName: string;
  specialty: string;
  organization: string;
}

const STORAGE_KEY = "wmax_profile_overrides";

function loadOverrides(): Partial<ProfileForm> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveOverrides(data: Partial<ProfileForm>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export const ProfilePage: React.FC<ProfilePageProps> = ({
  doctorName,
  role,
  onLogout,
  onBack,
}) => {
  const overrides = loadOverrides();

  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<ProfileForm>({
    fullName: overrides.fullName ?? doctorName,
    specialty: overrides.specialty ?? (role === "nurse" ? "Patronaj hamshirasi" : "Shifokor-kardiolog"),
    organization: overrides.organization ?? "Urganch Kardiologiya Dispanseri",
  });
  const [draft, setDraft] = useState<ProfileForm>({ ...form });

  const initials = form.fullName
    .split(" ")
    .filter((w) => !w.startsWith("Dr."))
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "??";

  const handleEdit = () => {
    setDraft({ ...form });
    setEditing(true);
    setSaved(false);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handleSave = () => {
    setForm({ ...draft });
    saveOverrides(draft);
    setEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const licenseItems = [
    { label: "Klinika rejimi", value: "OvaBMU / Statsionar" },
    { label: "Faol bemorlar", value: "100 ta kvota" },
    { label: "Litsenziya to'lovi", value: "85 000 so'm / oy" },
    { label: "Arendadagi qurilmalar", value: "4 ta biriktirilgan" },
  ];

  return (
    <div className="prof-page">
      {/* ── Back bar ── */}
      <div className="prof-topbar">
        <button type="button" className="prof-back-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          <span>Ro'yxatga qaytish</span>
        </button>
        {saved && (
          <span className="prof-save-toast">
            <Check size={14} style={{ marginRight: 4, verticalAlign: "middle" }} />
            <span>Saqlandi</span>
          </span>
        )}
      </div>

      <div className="prof-content">
        {/* ── Left column: identity ── */}
        <div className="prof-col-left">

          {/* Avatar card */}
          <div className="prof-card prof-identity-card">
            <div className="prof-avatar-xl">{initials}</div>
            {editing ? (
              <div className="prof-edit-fields">
                <label className="prof-field-label">To'liq ismi</label>
                <input
                  className="prof-field-input"
                  value={draft.fullName}
                  onChange={(e) => setDraft({ ...draft, fullName: e.target.value })}
                  placeholder="Dr. Ismi Familiyasi"
                />
                <label className="prof-field-label">Mutaxassislik</label>
                <input
                  className="prof-field-input"
                  value={draft.specialty}
                  onChange={(e) => setDraft({ ...draft, specialty: e.target.value })}
                  placeholder="Shifokor-kardiolog"
                />
                <label className="prof-field-label">Muassasa</label>
                <input
                  className="prof-field-input"
                  value={draft.organization}
                  onChange={(e) => setDraft({ ...draft, organization: e.target.value })}
                  placeholder="Klinika nomi"
                />
                <div className="prof-edit-actions">
                  <button type="button" className="prof-btn-save" onClick={handleSave}>
                    <Check size={14} style={{ marginRight: 4 }} />
                    <span>Saqlash</span>
                  </button>
                  <button type="button" className="prof-btn-cancel" onClick={handleCancel}>
                    Bekor
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="prof-display-name">{form.fullName}</div>
                <div className="prof-display-specialty">{form.specialty}</div>
                <div className="prof-display-org">
                  <Building2 size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                  <span>{form.organization}</span>
                </div>
                <button type="button" className="prof-btn-edit" onClick={handleEdit}>
                  <Edit2 size={13} style={{ marginRight: 4 }} />
                  <span>Tahrirlash</span>
                </button>
              </>
            )}
          </div>

          {/* Role badge */}
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
                    <span>Shifokor</span>
                  </>
                )}
              </span>
            </div>
            <div className="prof-role-row">
              <span className="prof-role-label">Muhit</span>
              <span className="prof-env-pill">
                <span className="prof-env-dot" />
                Jonli (Production)
              </span>
            </div>
            <div className="prof-role-row">
              <span className="prof-role-label">Xavfsizlik</span>
              <span className="prof-sec-pill">
                <ShieldCheck size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                <span>Himoyalangan</span>
              </span>
            </div>
          </div>

          {/* Logout */}
          <button type="button" className="prof-logout-btn" onClick={onLogout}>
            <LogOut size={15} style={{ marginRight: 6 }} />
            <span>Tizimdan chiqish</span>
          </button>
        </div>

        {/* ── Right column: license + quota ── */}
        <div className="prof-col-right">

          {/* B2B License card */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon prof-icon-license">
                <Building2 size={20} color="#0284c7" />
              </div>
              <div>
                <div className="prof-card-title">B2B Litsenziya</div>
                <div className="prof-card-sub">Klinik sheriklik shartnomasi</div>
              </div>
              <span className="prof-active-badge">FAOL</span>
            </div>

            <div className="prof-license-grid">
              {licenseItems.map((item) => (
                <div key={item.label} className="prof-license-item">
                  <span className="prof-lic-label">{item.label}</span>
                  <span className="prof-lic-value">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quota progress */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon prof-icon-quota">
                <BarChart3 size={20} color="#16a34a" />
              </div>
              <div>
                <div className="prof-card-title">Kvota holati</div>
                <div className="prof-card-sub">Joriy oy uchun bemorlar yuklamasi</div>
              </div>
            </div>
            <div className="prof-quota-wrap">
              <div className="prof-quota-bar-row">
                <span className="prof-quota-label">4 / 100 bemor</span>
                <span className="prof-quota-pct">4%</span>
              </div>
              <div className="prof-quota-track">
                <div className="prof-quota-fill" style={{ width: "4%" }} />
              </div>
              <div className="prof-quota-hint">96 ta bo'sh kvota mavjud</div>
            </div>
          </div>

          {/* Devices assigned */}
          <div className="prof-card">
            <div className="prof-card-header">
              <div className="prof-card-icon prof-icon-devices">
                <Watch size={20} color="#9333ea" />
              </div>
              <div>
                <div className="prof-card-title">Biriktirilgan qurilmalar</div>
                <div className="prof-card-sub">Arenda orqali berilgan</div>
              </div>
            </div>
            <div className="prof-device-slots">
              {[
                { tier: "Tier 1", name: "Galaxy Watch 5 (44mm)", sn: "SM-R910-8841", patient: "Qodirov B.", status: "on" },
                { tier: "Tier 3", name: "Medical PPG Band", sn: "BLE-BAND-041", patient: "Yoqubova D.", status: "on" },
                { tier: "Tier 1", name: "Galaxy Watch 5 (40mm)", sn: "SM-R910-8842", patient: "—", status: "free" },
                { tier: "Tier 2", name: "Xiaomi Watch 2", sn: "XW-M2-1029", patient: "—", status: "free" },
              ].map((d) => (
                <div key={d.sn} className={`prof-device-row prof-device-${d.status}`}>
                  <div className="prof-device-left">
                    <span className="prof-device-tier">{d.tier}</span>
                    <div>
                      <div className="prof-device-name">{d.name}</div>
                      <div className="prof-device-sn">{d.sn}</div>
                    </div>
                  </div>
                  <div className="prof-device-right">
                    {d.status === "on" ? (
                      <span className="prof-device-badge-on">{d.patient}</span>
                    ) : (
                      <span className="prof-device-badge-free">Bo'sh</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
