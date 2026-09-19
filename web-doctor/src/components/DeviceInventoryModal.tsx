import React, { useState } from "react";
import type { Lang } from "../i18n";

export interface DeviceItem {
  id: string;
  serial_number: string;
  model_name: string;
  tier: "tier1_wearos" | "tier2_wearos_budget" | "tier3_ble_band";
  status: "in_stock" | "assigned" | "active" | "returning" | "maintenance" | "lost" | "retired";
  ownership: string;
  battery_health_pct: number;
  last_sync_at: string | null;
  patient_name?: string;
}

interface DeviceInventoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: Lang;
}

// Initial realistic clinic inventory demo data
const INITIAL_DEVICES: DeviceItem[] = [
  {
    id: "d1",
    serial_number: "SM-R910-8841",
    model_name: "Samsung Galaxy Watch 5 (44mm)",
    tier: "tier1_wearos",
    status: "assigned",
    ownership: "owned",
    battery_health_pct: 94,
    last_sync_at: "2026-09-19T06:45:00Z",
    patient_name: "Qodirov Baxtiyor (Urganch)",
  },
  {
    id: "d2",
    serial_number: "SM-R910-8842",
    model_name: "Samsung Galaxy Watch 5 (40mm)",
    tier: "tier1_wearos",
    status: "in_stock",
    ownership: "owned",
    battery_health_pct: 98,
    last_sync_at: null,
  },
  {
    id: "d3",
    serial_number: "XW-M2-1029",
    model_name: "Xiaomi Watch 2 (Budget Wear OS)",
    tier: "tier2_wearos_budget",
    status: "in_stock",
    ownership: "owned",
    battery_health_pct: 100,
    last_sync_at: null,
  },
  {
    id: "d4",
    serial_number: "BLE-BAND-041",
    model_name: "Medical PPG Band (14 kun batareya)",
    tier: "tier3_ble_band",
    status: "assigned",
    ownership: "leased",
    battery_health_pct: 91,
    last_sync_at: "2026-09-19T07:10:00Z",
    patient_name: "Yoqubova Dilnoza (Xiva)",
  },
  {
    id: "d5",
    serial_number: "SM-R900-5120",
    model_name: "Galaxy Watch 4 (Klassik)",
    tier: "tier1_wearos",
    status: "maintenance",
    ownership: "owned",
    battery_health_pct: 79,
    last_sync_at: "2026-09-18T12:00:00Z",
  },
];

export const DeviceInventoryModal: React.FC<DeviceInventoryModalProps> = ({
  isOpen,
  onClose,
  lang,
}) => {
  const [devices, setDevices] = useState<DeviceItem[]>(INITIAL_DEVICES);
  const [activeTierFilter, setActiveTierFilter] = useState<string>("all");
  const [activeStatusFilter, setActiveStatusFilter] = useState<string>("all");
  const [selectedDevice, setSelectedDevice] = useState<DeviceItem | null>(null);
  const [actionType, setActionType] = useState<"assign" | "return" | null>(null);

  // Form states
  const [assignPatientName, setAssignPatientName] = useState("");
  const [depositAmount, setDepositAmount] = useState("500 000");
  const [rentalAmount, setRentalAmount] = useState("180 000");

  if (!isOpen) return null;

  const inStockCount = devices.filter((d) => d.status === "in_stock").length;
  const assignedCount = devices.filter((d) => d.status === "assigned" || d.status === "active").length;
  const maintenanceCount = devices.filter((d) => d.status === "maintenance").length;

  const filteredDevices = devices.filter((d) => {
    if (activeTierFilter !== "all" && d.tier !== activeTierFilter) return false;
    if (activeStatusFilter !== "all" && d.status !== activeStatusFilter) return false;
    return true;
  });

  const getTierLabel = (tier: string) => {
    if (tier === "tier1_wearos") return "Tier 1: Galaxy Watch (Etalon)";
    if (tier === "tier2_wearos_budget") return "Tier 2: Arzon Wear OS";
    return "Tier 3: BLE Tibbiy Braslet (14 kun)";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "in_stock":
        return <span className="inv-badge inv-stock">✅ Omborxonada (Bo'sh)</span>;
      case "assigned":
      case "active":
        return <span className="inv-badge inv-assigned">⌚ Arendada (Faol)</span>;
      case "maintenance":
        return <span className="inv-badge inv-maint">🔧 Texnik ko'rikda</span>;
      case "retired":
        return <span className="inv-badge inv-retired">⛔ Yaroqsiz</span>;
      default:
        return <span className="inv-badge">{status}</span>;
    }
  };

  const handleConfirmAssign = () => {
    if (!selectedDevice || !assignPatientName) return;
    setDevices((prev) =>
      prev.map((d) =>
        d.id === selectedDevice.id
          ? { ...d, status: "assigned", patient_name: assignPatientName }
          : d
      )
    );
    setActionType(null);
    setSelectedDevice(null);
    setAssignPatientName("");
  };

  const handleConfirmReturn = () => {
    if (!selectedDevice) return;
    setDevices((prev) =>
      prev.map((d) =>
        d.id === selectedDevice.id
          ? {
              ...d,
              status: d.battery_health_pct < 80 ? "retired" : "in_stock",
              patient_name: undefined,
            }
          : d
      )
    );
    setActionType(null);
    setSelectedDevice(null);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card modal-inventory"
        style={{ maxWidth: "860px", width: "95%" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.4rem" }}>📦</span>
            <div>
              <h2 className="modal-title" style={{ margin: 0 }}>
                {lang === "ru" ? "Инвентарь устройств и аренда" : "Qurilmalar Inventari va Arenda Boshqaruvi"}
              </h2>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "var(--color-muted)" }}>
                {lang === "ru"
                  ? "3-уровневая аппаратная модель WMAX (Tier 1-3), контроль деградации батареи и залогов"
                  : "WMAX 3-pog'onali apparat modeli (Tier 1–3), batareya testi va depozit hisobi"}
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* 1. Summary Stat Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "12px",
            margin: "16px 0",
          }}
        >
          <div className="inv-stat-card">
            <span className="inv-stat-num" style={{ color: "#10b981" }}>{inStockCount}</span>
            <span className="inv-stat-lbl">Bo'sh (Omborda)</span>
          </div>
          <div className="inv-stat-card">
            <span className="inv-stat-num" style={{ color: "#3b82f6" }}>{assignedCount}</span>
            <span className="inv-stat-lbl">Bemorga biriktirilgan</span>
          </div>
          <div className="inv-stat-card">
            <span className="inv-stat-num" style={{ color: "#f59e0b" }}>{maintenanceCount}</span>
            <span className="inv-stat-lbl">Ko'rik / Zaryadlash</span>
          </div>
          <div className="inv-stat-card">
            <span className="inv-stat-num" style={{ color: "#8b5cf6" }}>85 000 so'm</span>
            <span className="inv-stat-lbl">Klinika oylik litsenziyasi</span>
          </div>
        </div>

        {/* 2. Filter Bar */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px" }}>
          <select
            className="filter-select"
            value={activeTierFilter}
            onChange={(e) => setActiveTierFilter(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--border-color)" }}
          >
            <option value="all">Barcha apparat qatlamlari (Tier 1–3)</option>
            <option value="tier1_wearos">Tier 1: Galaxy Watch (Etalon)</option>
            <option value="tier2_wearos_budget">Tier 2: Arzon Wear OS</option>
            <option value="tier3_ble_band">Tier 3: BLE Tibbiy Braslet</option>
          </select>

          <select
            className="filter-select"
            value={activeStatusFilter}
            onChange={(e) => setActiveStatusFilter(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--border-color)" }}
          >
            <option value="all">Barcha holatlar</option>
            <option value="in_stock">Faqat bo'sh qurilmalar</option>
            <option value="assigned">Arendadagi qurilmalar</option>
            <option value="maintenance">Texnik ko'rikdagilar</option>
          </select>
        </div>

        {/* 3. Devices Table */}
        <div style={{ maxHeight: "320px", overflowY: "auto", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
            <thead style={{ background: "var(--bg-card)", borderBottom: "1px solid var(--border-color)" }}>
              <tr>
                <th style={{ padding: "10px" }}>Qurilma / Model</th>
                <th style={{ padding: "10px" }}>Qatlam (Tier)</th>
                <th style={{ padding: "10px" }}>Batareya</th>
                <th style={{ padding: "10px" }}>Holat</th>
                <th style={{ padding: "10px" }}>Bemor</th>
                <th style={{ padding: "10px", textAlign: "right" }}>Amal</th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map((dev) => (
                <tr key={dev.id} style={{ borderBottom: "1px solid var(--border-color)" }}>
                  <td style={{ padding: "10px" }}>
                    <div style={{ fontWeight: 600 }}>{dev.model_name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--color-muted)", fontFamily: "monospace" }}>
                      S/N: {dev.serial_number}
                    </div>
                  </td>
                  <td style={{ padding: "10px" }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-muted)" }}>{getTierLabel(dev.tier)}</span>
                  </td>
                  <td style={{ padding: "10px" }}>
                    <span
                      style={{
                        color:
                          dev.battery_health_pct >= 90
                            ? "#10b981"
                            : dev.battery_health_pct >= 80
                            ? "#f59e0b"
                            : "#ef4444",
                        fontWeight: 600,
                      }}
                    >
                      {dev.battery_health_pct}%
                    </span>
                  </td>
                  <td style={{ padding: "10px" }}>{getStatusBadge(dev.status)}</td>
                  <td style={{ padding: "10px" }}>
                    {dev.patient_name ? (
                      <span style={{ fontWeight: 500 }}>{dev.patient_name}</span>
                    ) : (
                      <span style={{ color: "var(--color-muted)" }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: "10px", textAlign: "right" }}>
                    {dev.status === "in_stock" && (
                      <button
                        className="btn-sm btn-primary"
                        onClick={() => {
                          setSelectedDevice(dev);
                          setActionType("assign");
                        }}
                        style={{ padding: "4px 10px", borderRadius: "6px", fontSize: "0.8rem" }}
                      >
                        Arendaga berish
                      </button>
                    )}
                    {(dev.status === "assigned" || dev.status === "active") && (
                      <button
                        className="btn-sm btn-outline"
                        onClick={() => {
                          setSelectedDevice(dev);
                          setActionType("return");
                        }}
                        style={{ padding: "4px 10px", borderRadius: "6px", fontSize: "0.8rem" }}
                      >
                        Qaytarib olish
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 4. Action Forms (Assign or Return) */}
        {actionType === "assign" && selectedDevice && (
          <div
            style={{
              marginTop: "16px",
              padding: "14px",
              background: "rgba(59, 130, 246, 0.08)",
              borderRadius: "8px",
              border: "1px solid rgba(59, 130, 246, 0.2)",
            }}
          >
            <h4 style={{ margin: "0 0 10px 0" }}>
              ⌚ {selectedDevice.model_name} ni bemorga biriktirish
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "10px" }}>
              <div>
                <label style={{ fontSize: "0.8rem", display: "block" }}>Bemor F.I.O:</label>
                <input
                  type="text"
                  placeholder="Masalan: Yusupov Otabek"
                  value={assignPatientName}
                  onChange={(e) => setAssignPatientName(e.target.value)}
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", display: "block" }}>Depozit (so'm):</label>
                <input
                  type="text"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", display: "block" }}>Oylik arenda (so'm):</label>
                <input
                  type="text"
                  value={rentalAmount}
                  onChange={(e) => setRentalAmount(e.target.value)}
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
                />
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              <button className="btn-sm btn-outline" onClick={() => setActionType(null)}>
                Bekor qilish
              </button>
              <button className="btn-sm btn-primary" onClick={handleConfirmAssign} disabled={!assignPatientName}>
                Tasdiqlash va Shaxsiy Baseline Boshlash
              </button>
            </div>
          </div>
        )}

        {actionType === "return" && selectedDevice && (
          <div
            style={{
              marginTop: "16px",
              padding: "14px",
              background: "rgba(16, 185, 129, 0.08)",
              borderRadius: "8px",
              border: "1px solid rgba(16, 185, 129, 0.2)",
            }}
          >
            <h4 style={{ margin: "0 0 10px 0" }}>
              📥 {selectedDevice.model_name} ni qabul qilish va depozitni qaytarish
            </h4>
            <p style={{ fontSize: "0.85rem", color: "var(--color-muted)", margin: "0 0 10px 0" }}>
              Bemor: <b>{selectedDevice.patient_name}</b> · Joriy batareya salomatligi: <b>{selectedDevice.battery_health_pct}%</b>
            </p>
            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              <button className="btn-sm btn-outline" onClick={() => setActionType(null)}>
                Bekor qilish
              </button>
              <button className="btn-sm btn-primary" onClick={handleConfirmReturn}>
                Tozalash va Omborga Qaytarish (Depozit Qaytarildi)
              </button>
            </div>
          </div>
        )}

        <div className="modal-footer" style={{ marginTop: "16px", display: "flex", justifyContent: "flex-end" }}>
          <button className="btn btn-outline" onClick={onClose}>
            {lang === "ru" ? "Закрыть" : "Yopish"}
          </button>
        </div>
      </div>
    </div>
  );
};
