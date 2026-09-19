import React, { useState } from "react";
import type { Lang } from "../i18n";

export interface DeviceItem {
  id: string;
  serial_number: string;
  model_name: string;
  model_sub: string;
  tier: "tier1_wearos" | "tier2_wearos_budget" | "tier3_ble_band";
  status: "in_stock" | "assigned" | "active" | "maintenance" | "retired" | "lost";
  ownership: string;
  battery_health_pct: number;
  last_sync_at: string | null;
  patient_name?: string;
  patient_city?: string;
}

interface Props { onClose: () => void; lang: Lang; }

/* ─── SVG Icon Library ─────────────────────────────────────────────────────── */
const Icon = {
  Watch: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="7" y="7" width="10" height="10" rx="3"/>
      <path d="M9 7V5a3 3 0 0 1 6 0v2"/><path d="M9 17v2a3 3 0 0 0 6 0v-2"/>
      <path d="M12 10v2l1 1"/>
    </svg>
  ),
  Band: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="8" y="9" width="8" height="6" rx="2"/>
      <path d="M10 9V6a2 2 0 0 1 4 0v3"/><path d="M10 15v3a2 2 0 0 0 4 0v-3"/>
      <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none"/>
    </svg>
  ),
  Budget: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="7" y="7" width="10" height="10" rx="3"/>
      <path d="M9 7V4.5a2.5 2.5 0 0 1 5 0V7"/><path d="M9 17v2.5a2.5 2.5 0 0 0 5 0V17"/>
      <path d="M10 12h4"/>
    </svg>
  ),
  Battery: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="8" width="16" height="8" rx="2"/>
      <path d="M22 11v2"/><rect x="4" y="10" width="6" height="4" rx="1" fill="currentColor" stroke="none"/>
    </svg>
  ),
  Person: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="3.5"/><path d="M4.5 20c0-3.866 3.358-7 7.5-7s7.5 3.134 7.5 7"/>
    </svg>
  ),
  Location: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2C8.686 2 6 4.686 6 8c0 5 6 13 6 13s6-8 6-13c0-3.314-2.686-6-6-6z"/>
      <circle cx="12" cy="8" r="2.2"/>
    </svg>
  ),
  ArrowLeft: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5"/><path d="M12 5l-7 7 7 7"/>
    </svg>
  ),
  Plus: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5v14M5 12h14"/>
    </svg>
  ),
  Download: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v14"/><path d="M5 13l7 7 7-7"/><path d="M3 21h18"/>
    </svg>
  ),
  Tool: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>
  ),
  Check: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17l-5-5"/>
    </svg>
  ),
  X: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6L6 18M6 6l12 12"/>
    </svg>
  ),
  Sync: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    </svg>
  ),
  Package: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/>
    </svg>
  ),
  Star: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  Wifi: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/>
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1" fill="currentColor" stroke="none"/>
    </svg>
  ),
  Alert: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <path d="M12 9v4"/><path d="M12 17h.01"/>
    </svg>
  ),
  BoxOpen: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 8V21H3V8"/><path d="M23 3H1l2 5h18z"/><path d="M12 3v5"/>
    </svg>
  ),
};

/* ─── Data ─────────────────────────────────────────────────────────────────── */
const DEVICES: DeviceItem[] = [
  { id:"d1", serial_number:"SM-R910-8841", model_name:"Galaxy Watch 5", model_sub:"44mm · Wear OS 3.5", tier:"tier1_wearos", status:"assigned", ownership:"owned", battery_health_pct:94, last_sync_at:"2026-09-19T06:45:00Z", patient_name:"Qodirov Baxtiyor", patient_city:"Urganch" },
  { id:"d2", serial_number:"SM-R910-8842", model_name:"Galaxy Watch 5", model_sub:"40mm · Wear OS 3.5", tier:"tier1_wearos", status:"in_stock", ownership:"owned", battery_health_pct:98, last_sync_at:null },
  { id:"d3", serial_number:"XW-M2-1029", model_name:"Xiaomi Watch 2", model_sub:"Budget Wear OS 3", tier:"tier2_wearos_budget", status:"in_stock", ownership:"owned", battery_health_pct:100, last_sync_at:null },
  { id:"d4", serial_number:"BLE-BAND-041", model_name:"Medical PPG Band", model_sub:"14-kun batareya · BLE 5.2", tier:"tier3_ble_band", status:"assigned", ownership:"leased", battery_health_pct:91, last_sync_at:"2026-09-19T07:10:00Z", patient_name:"Yoqubova Dilnoza", patient_city:"Xiva" },
  { id:"d5", serial_number:"SM-R900-5120", model_name:"Galaxy Watch 4", model_sub:"Classic · Wear OS 3", tier:"tier1_wearos", status:"maintenance", ownership:"owned", battery_health_pct:79, last_sync_at:"2026-09-18T12:00:00Z" },
];

type TierKey = "tier1_wearos" | "tier2_wearos_budget" | "tier3_ble_band";
type StatusKey = "in_stock" | "assigned" | "active" | "maintenance" | "retired" | "lost";

const TIER: Record<TierKey, { label: string; sub: string; color: string; from: string; to: string; shadow: string; IconEl: React.FC }> = {
  tier1_wearos:       { label:"Tier 1", sub:"Galaxy Watch",   color:"#60a5fa", from:"#1d4ed8", to:"#3b82f6",   shadow:"rgba(59,130,246,0.5)",  IconEl: Icon.Watch  },
  tier2_wearos_budget:{ label:"Tier 2", sub:"Wear OS Budget", color:"#a78bfa", from:"#6d28d9", to:"#8b5cf6",   shadow:"rgba(139,92,246,0.5)",  IconEl: Icon.Budget },
  tier3_ble_band:     { label:"Tier 3", sub:"BLE Braslet",    color:"#34d399", from:"#065f46", to:"#10b981",   shadow:"rgba(16,185,129,0.5)",  IconEl: Icon.Band   },
};

const STATUS: Record<StatusKey, { label: string; dot: string; glow: string; ring: string }> = {
  in_stock:    { label:"Bo'sh",       dot:"#22c55e", glow:"rgba(34,197,94,0.4)",   ring:"rgba(34,197,94,0.15)"  },
  assigned:    { label:"Arendada",    dot:"#38bdf8", glow:"rgba(56,189,248,0.4)",  ring:"rgba(56,189,248,0.15)" },
  active:      { label:"Faol",        dot:"#38bdf8", glow:"rgba(56,189,248,0.4)",  ring:"rgba(56,189,248,0.15)" },
  maintenance: { label:"Ko'rikda",    dot:"#fbbf24", glow:"rgba(251,191,36,0.4)",  ring:"rgba(251,191,36,0.15)" },
  retired:     { label:"Yaroqsiz",    dot:"#f87171", glow:"rgba(248,113,113,0.4)", ring:"rgba(248,113,113,0.15)"},
  lost:        { label:"Yo'qolgan",   dot:"#94a3b8", glow:"rgba(148,163,184,0.3)", ring:"rgba(148,163,184,0.1)" },
};

/* ─── Battery Gauge ─────────────────────────────────────────────────────────── */
function BatteryGauge({ pct }: { pct: number }) {
  const color = pct >= 80 ? "#22c55e" : pct >= 50 ? "#fbbf24" : "#f87171";
  const glow  = pct >= 80 ? "rgba(34,197,94,0.6)" : pct >= 50 ? "rgba(251,191,36,0.6)" : "rgba(248,113,113,0.6)";
  return (
    <div className="gb-wrap">
      <div className="gb-track">
        <div className="gb-fill" style={{ width:`${pct}%`, background:`linear-gradient(90deg, ${color}cc, ${color})`, boxShadow:`0 0 8px ${glow}` }} />
      </div>
      <span className="gb-pct" style={{ color }}>{pct}%</span>
    </div>
  );
}

/* ─── Main Component ─────────────────────────────────────────────────────────── */
export const DeviceInventoryModal: React.FC<Props> = ({ onClose }) => {
  const [devices, setDevices] = useState<DeviceItem[]>(DEVICES);
  const [tierF, setTierF] = useState("all");
  const [statF, setStatF] = useState("all");
  const [selected, setSelected] = useState<DeviceItem | null>(null);
  const [action, setAction]     = useState<"assign"|"return"|null>(null);
  const [patName, setPatName]   = useState("");
  const [patCity, setPatCity]   = useState("");
  const [deposit, setDeposit]   = useState("500 000");
  const [rental, setRental]     = useState("180 000");
  const [toast, setToast]       = useState<{msg:string;type:"ok"|"warn"}|null>(null);

  const pop = (msg: string, type:"ok"|"warn" = "ok") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3200);
  };

  const inStock    = devices.filter(d => d.status === "in_stock").length;
  const assigned   = devices.filter(d => d.status === "assigned" || d.status === "active").length;
  const maintenance= devices.filter(d => d.status === "maintenance").length;

  const list = devices.filter(d => {
    if (tierF !== "all" && d.tier !== tierF) return false;
    if (statF !== "all" && d.status !== statF) return false;
    return true;
  });

  const doAssign = () => {
    if (!selected || !patName.trim()) return;
    setDevices(p => p.map(d => d.id === selected.id
      ? { ...d, status:"assigned", patient_name:patName.trim(), patient_city:patCity.trim()||undefined }
      : d));
    pop(`${selected.model_name} bemorga biriktirildi`);
    setAction(null); setSelected(null); setPatName(""); setPatCity("");
  };

  const doReturn = () => {
    if (!selected) return;
    const ns = selected.battery_health_pct < 80 ? "retired" : "in_stock";
    setDevices(p => p.map(d => d.id === selected.id
      ? { ...d, status:ns, patient_name:undefined, patient_city:undefined }
      : d));
    pop(ns === "retired" ? `${selected.model_name} yaroqsiz belgilandi` : `${selected.model_name} omborga qaytdi`, ns === "retired" ? "warn" : "ok");
    setAction(null); setSelected(null);
  };

  const doMaint = (dev: DeviceItem) => {
    setDevices(p => p.map(d => d.id === dev.id ? { ...d, status:"maintenance" } : d));
    pop(`${dev.model_name} texnik ko'rikka yuborildi`, "warn");
  };

  const doReady = (dev: DeviceItem) => {
    setDevices(p => p.map(d => d.id === dev.id ? { ...d, status:"in_stock" } : d));
    pop(`${dev.model_name} ko'rik yakunlandi — omborga qaytdi`);
  };

  const cancel = () => { setAction(null); setSelected(null); setPatName(""); setPatCity(""); };

  return (
    <div className="gl-shell">
      {/* Animated mesh BG */}
      <div className="gl-bg-mesh" aria-hidden="true">
        <div className="gl-orb gl-orb-1" />
        <div className="gl-orb gl-orb-2" />
        <div className="gl-orb gl-orb-3" />
      </div>

      {/* Toast */}
      {toast && (
        <div className={`gl-toast gl-toast-${toast.type}`}>
          <span className="gl-toast-icon">{toast.type === "ok" ? <Icon.Check /> : <Icon.Alert />}</span>
          {toast.msg}
        </div>
      )}

      {/* ── Header ─────────────────────────────────── */}
      <header className="gl-header">
        <div className="gl-header-brand">
          <div className="gl-header-logo">
            <Icon.Package />
          </div>
          <div>
            <h1 className="gl-header-title">Qurilmalar Inventari</h1>
            <p className="gl-header-sub">WMAX · Tier 1–3 · Batareya monitoring · Arenda boshqaruvi</p>
          </div>
        </div>
        <button className="gl-back-btn" onClick={onClose} type="button">
          <Icon.ArrowLeft />
          Ro'yxatga qaytish
        </button>
      </header>

      <div className="gl-content">

        {/* ── KPI Row ─────────────────────────────────── */}
        <div className="gl-kpi-row">
          <div className="gl-kpi-card gl-kpi-total">
            <div className="gl-kpi-icon-wrap" style={{background:"linear-gradient(135deg,#1e3a5f,#0284c7)"}}>
              <Icon.Package />
            </div>
            <div>
              <div className="gl-kpi-num">{devices.length}</div>
              <div className="gl-kpi-lbl">Jami qurilma</div>
            </div>
          </div>

          <div className="gl-kpi-card gl-kpi-stock">
            <div className="gl-kpi-icon-wrap" style={{background:"linear-gradient(135deg,#064e3b,#059669)"}}>
              <Icon.BoxOpen />
            </div>
            <div>
              <div className="gl-kpi-num gl-num-green">{inStock}</div>
              <div className="gl-kpi-lbl">Omborxonada</div>
            </div>
            <div className="gl-kpi-pulse" style={{background:"#22c55e"}} />
          </div>

          <div className="gl-kpi-card gl-kpi-assigned">
            <div className="gl-kpi-icon-wrap" style={{background:"linear-gradient(135deg,#1e3a5f,#0ea5e9)"}}>
              <Icon.Wifi />
            </div>
            <div>
              <div className="gl-kpi-num gl-num-blue">{assigned}</div>
              <div className="gl-kpi-lbl">Arendada</div>
            </div>
            <div className="gl-kpi-pulse" style={{background:"#38bdf8"}} />
          </div>

          <div className="gl-kpi-card gl-kpi-maint">
            <div className="gl-kpi-icon-wrap" style={{background:"linear-gradient(135deg,#451a03,#d97706)"}}>
              <Icon.Tool />
            </div>
            <div>
              <div className="gl-kpi-num gl-num-amber">{maintenance}</div>
              <div className="gl-kpi-lbl">Texnik ko'rikda</div>
            </div>
          </div>

          <div className="gl-kpi-card gl-kpi-license">
            <div className="gl-kpi-icon-wrap" style={{background:"linear-gradient(135deg,#2e1065,#7c3aed)"}}>
              <Icon.Star />
            </div>
            <div>
              <div className="gl-kpi-num gl-num-purple">85 000</div>
              <div className="gl-kpi-lbl">so'm / oy · Litsenziya</div>
            </div>
          </div>
        </div>

        {/* ── Filters ─────────────────────────────────── */}
        <div className="gl-filter-bar">
          {/* Tier filter */}
          <div className="gl-filter-group">
            {[
              { v:"all", label:"Barcha Tier" },
              { v:"tier1_wearos", label:"Tier 1 · Watch" },
              { v:"tier2_wearos_budget", label:"Tier 2 · Budget" },
              { v:"tier3_ble_band", label:"Tier 3 · BLE" },
            ].map(o => (
              <button key={o.v} type="button"
                className={`gl-filter-btn ${tierF === o.v ? "active" : ""}`}
                onClick={() => setTierF(o.v)}>
                {o.label}
              </button>
            ))}
          </div>

          <div className="gl-filter-sep" />

          {/* Status filter */}
          <div className="gl-filter-group">
            {[
              { v:"all", label:"Barchasi", dot:"" },
              { v:"in_stock", label:"Bo'sh", dot:"#22c55e" },
              { v:"assigned", label:"Arendada", dot:"#38bdf8" },
              { v:"maintenance", label:"Ko'rikda", dot:"#fbbf24" },
            ].map(o => (
              <button key={o.v} type="button"
                className={`gl-filter-btn ${statF === o.v ? "active" : ""}`}
                onClick={() => setStatF(o.v)}>
                {o.dot && <span className="gl-dot" style={{background:o.dot, boxShadow:`0 0 6px ${o.dot}`}} />}
                {o.label}
              </button>
            ))}
          </div>

          <span className="gl-count-badge">{list.length} / {devices.length}</span>
        </div>

        {/* ── Cards Grid ─────────────────────────────── */}
        <div className="gl-grid">
          {list.map(dev => {
            const tier   = TIER[dev.tier];
            const status = STATUS[dev.status as StatusKey] ?? STATUS.in_stock;
            const TierIcon = tier.IconEl;
            const isAssigned = dev.status === "assigned" || dev.status === "active";
            const isStock    = dev.status === "in_stock";
            const isMaint    = dev.status === "maintenance";

            return (
              <div key={dev.id} className={`gl-card ${isAssigned ? "gl-card--on" : ""} ${isMaint ? "gl-card--warn" : ""}`}>
                {/* Glow accent */}
                <div className="gl-card-glow" style={{background:`radial-gradient(circle at 50% 0%, ${tier.shadow} 0%, transparent 70%)`}} />

                {/* Top row */}
                <div className="gl-card-top">
                  {/* Tier icon pill */}
                  <div className="gl-tier-pill" style={{background:`linear-gradient(135deg,${tier.from},${tier.to})`, boxShadow:`0 4px 14px ${tier.shadow}`}}>
                    <span className="gl-tier-ico"><TierIcon /></span>
                    <span className="gl-tier-lbl">{tier.label}</span>
                  </div>

                  {/* Status badge */}
                  <div className="gl-status-badge" style={{background:status.ring, borderColor:status.dot, color:status.dot}}>
                    <span className="gl-status-dot" style={{background:status.dot, boxShadow:`0 0 6px ${status.glow}`}} />
                    {status.label}
                  </div>
                </div>

                {/* Model info */}
                <div className="gl-card-model">
                  <div className="gl-model-name">{dev.model_name}</div>
                  <div className="gl-model-sub">{dev.model_sub}</div>
                  <div className="gl-serial">
                    <span className="gl-serial-label">S/N</span>
                    <span className="gl-serial-val">{dev.serial_number}</span>
                  </div>
                </div>

                {/* Battery */}
                <div className="gl-card-section">
                  <div className="gl-section-label"><Icon.Battery /> Batareya</div>
                  <BatteryGauge pct={dev.battery_health_pct} />
                </div>

                {/* Sync */}
                <div className="gl-card-section gl-sync-row">
                  <span className="gl-section-label"><Icon.Sync /> Sinxron</span>
                  <span className="gl-sync-val">
                    {dev.last_sync_at
                      ? new Date(dev.last_sync_at).toLocaleString("uz-Latn-UZ", { day:"2-digit", month:"2-digit", hour:"2-digit", minute:"2-digit" })
                      : <span className="gl-sync-none">—</span>}
                  </span>
                </div>

                {/* Patient */}
                {isAssigned && dev.patient_name && (
                  <div className="gl-patient-box">
                    <div className="gl-patient-avatar">
                      <Icon.Person />
                    </div>
                    <div className="gl-patient-info">
                      <div className="gl-patient-name">{dev.patient_name}</div>
                      {dev.patient_city && (
                        <div className="gl-patient-city">
                          <Icon.Location />
                          {dev.patient_city}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="gl-card-actions">
                  {isStock && (
                    <>
                      <button type="button" className="gl-btn gl-btn-primary"
                        onClick={() => { setSelected(dev); setAction("assign"); }}>
                        <Icon.Plus /> Arendaga berish
                      </button>
                      <button type="button" className="gl-btn gl-btn-ghost"
                        onClick={() => doMaint(dev)}>
                        <Icon.Tool /> Ko'rikka yuborish
                      </button>
                    </>
                  )}
                  {isAssigned && (
                    <button type="button" className="gl-btn gl-btn-return"
                      onClick={() => { setSelected(dev); setAction("return"); }}>
                      <Icon.Download /> Qaytarib olish
                    </button>
                  )}
                  {isMaint && (
                    <button type="button" className="gl-btn gl-btn-success"
                      onClick={() => doReady(dev)}>
                      <Icon.Check /> Ko'rik yakunlandi
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {list.length === 0 && (
            <div className="gl-empty">
              <div className="gl-empty-icon"><Icon.BoxOpen /></div>
              <p>Qurilmalar topilmadi</p>
              <button type="button" className="gl-btn gl-btn-ghost gl-btn-sm"
                onClick={() => { setTierF("all"); setStatF("all"); }}>
                Filtrlarni tozalash
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Assign Modal ──────────────────────────────── */}
      {action === "assign" && selected && (
        <div className="gl-overlay" onClick={cancel}>
          <div className="gl-modal" onClick={e => e.stopPropagation()}>
            <div className="gl-modal-header">
              <div className="gl-modal-icon" style={{background:"linear-gradient(135deg,#1e3a5f,#0284c7)"}}>
                <Icon.Plus />
              </div>
              <div>
                <h3 className="gl-modal-title">Arendaga berish</h3>
                <p className="gl-modal-sub">{selected.model_name} · {selected.serial_number}</p>
              </div>
              <button className="gl-modal-close" type="button" onClick={cancel}><Icon.X /></button>
            </div>

            <div className="gl-modal-body">
              <div className="gl-field">
                <label className="gl-field-label">Bemor F.I.O <span className="gl-req">*</span></label>
                <input className="gl-field-input" type="text" autoFocus
                  placeholder="Yusupov Otabek" value={patName}
                  onChange={e => setPatName(e.target.value)} />
              </div>
              <div className="gl-field">
                <label className="gl-field-label">Shahar / Tuman</label>
                <input className="gl-field-input" type="text"
                  placeholder="Urganch" value={patCity}
                  onChange={e => setPatCity(e.target.value)} />
              </div>
              <div className="gl-field-row">
                <div className="gl-field">
                  <label className="gl-field-label">Depozit (so'm)</label>
                  <input className="gl-field-input" type="text"
                    value={deposit} onChange={e => setDeposit(e.target.value)} />
                </div>
                <div className="gl-field">
                  <label className="gl-field-label">Oylik arenda (so'm)</label>
                  <input className="gl-field-input" type="text"
                    value={rental} onChange={e => setRental(e.target.value)} />
                </div>
              </div>
            </div>

            <div className="gl-modal-footer">
              <button type="button" className="gl-btn gl-btn-ghost gl-btn-sm" onClick={cancel}>
                Bekor qilish
              </button>
              <button type="button" className="gl-btn gl-btn-primary"
                onClick={doAssign} disabled={!patName.trim()}>
                <Icon.Check /> Tasdiqlash · Baseline boshlash
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Return Modal ──────────────────────────────── */}
      {action === "return" && selected && (
        <div className="gl-overlay" onClick={cancel}>
          <div className="gl-modal" onClick={e => e.stopPropagation()}>
            <div className="gl-modal-header">
              <div className="gl-modal-icon" style={{background:"linear-gradient(135deg,#1a3a2e,#059669)"}}>
                <Icon.Download />
              </div>
              <div>
                <h3 className="gl-modal-title">Qurilmani qaytarish</h3>
                <p className="gl-modal-sub">{selected.model_name} · {selected.serial_number}</p>
              </div>
              <button className="gl-modal-close" type="button" onClick={cancel}><Icon.X /></button>
            </div>

            <div className="gl-modal-body">
              <div className="gl-return-info">
                <div className="gl-return-row">
                  <span className="gl-return-k">Bemor</span>
                  <span className="gl-return-v">{selected.patient_name}{selected.patient_city ? ` · ${selected.patient_city}` : ""}</span>
                </div>
                <div className="gl-return-row">
                  <span className="gl-return-k">Batareya</span>
                  <span className="gl-return-v"><BatteryGauge pct={selected.battery_health_pct} /></span>
                </div>
              </div>
              {selected.battery_health_pct < 80 && (
                <div className="gl-warn-box">
                  <Icon.Alert />
                  Batareya 80% dan past — qurilma <b>yaroqsiz</b> deb belgilanadi
                </div>
              )}
            </div>

            <div className="gl-modal-footer">
              <button type="button" className="gl-btn gl-btn-ghost gl-btn-sm" onClick={cancel}>
                Bekor qilish
              </button>
              <button type="button" className="gl-btn gl-btn-success" onClick={doReturn}>
                <Icon.Check /> Depozit qaytarildi · Omborga qo'yish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
