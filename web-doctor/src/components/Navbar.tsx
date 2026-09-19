import React, { useEffect, useRef, useState } from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AuthRole } from "../lib/types";

export type NavTab = "patients" | "handoffs" | "sos" | "devices";

interface NavbarProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  doctorName?: string;
  role?: AuthRole;
  onLogout: () => void;
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  activeSosCount?: number;
  openHandoffsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  lang,
  onLangChange,
  doctorName = "Dr. Islom Yusupov",
  role = "doctor",
  onLogout,
  activeTab,
  onTabChange,
  activeSosCount = 0,
  openHandoffsCount = 2,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    };
    if (profileOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileOpen]);

  const initials = doctorName
    ? doctorName
        .split(" ")
        .filter((w) => !w.startsWith("Dr."))
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "IY";

  return (
    <header className="doc-header">
      {/* 1. Left: Modern Minimalist Brand */}
      <div className="doc-header-brand" onClick={() => onTabChange("patients")} style={{ cursor: "pointer" }}>
        <div className="med-emblem">
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        </div>
        <div className="brand-text-block">
          <div className="brand-primary-line">
            <span className="brand-name">WMAX</span>
            <span className="brand-badge-official">Klinika</span>
          </div>
        </div>
      </div>

      {/* 2. Center: 4 Essential Navigation Tabs */}
      <nav className="doc-nav-tabs">
        <button
          type="button"
          className={`doc-tab-btn ${activeTab === "patients" ? "active" : ""}`}
          onClick={() => onTabChange("patients")}
        >
          <span className="tab-icon">📋</span>
          <span className="tab-title">{lang === "ru" ? "Пациенты" : "Bemorlar"}</span>
        </button>

        <button
          type="button"
          className={`doc-tab-btn ${activeTab === "handoffs" ? "active" : ""}`}
          onClick={() => onTabChange("handoffs")}
        >
          <span className="tab-icon">🏥</span>
          <span className="tab-title">{lang === "ru" ? "Переводы (М11)" : "Topshirish (M11)"}</span>
          {openHandoffsCount > 0 && (
            <span className="tab-badge blue-badge">{openHandoffsCount}</span>
          )}
        </button>

        <button
          type="button"
          className={`doc-tab-btn ${activeTab === "sos" ? "active" : ""}`}
          onClick={() => onTabChange("sos")}
        >
          <span className="tab-icon">🚨</span>
          <span className="tab-title">{lang === "ru" ? "Экстренные (SOS)" : "Shoshilinch (SOS)"}</span>
          {activeSosCount > 0 && (
            <span className="tab-badge pulse-badge">{activeSosCount}</span>
          )}
        </button>

        <button
          type="button"
          className={`doc-tab-btn ${activeTab === "devices" ? "active" : ""}`}
          onClick={() => onTabChange("devices")}
        >
          <span className="tab-icon">📦</span>
          <span className="tab-title">{lang === "ru" ? "Устройства (Аренда)" : "Qurilmalar (Arenda)"}</span>
        </button>
      </nav>

      {/* 3. Right Controls: Language Switcher + Sleek Profile Popover */}
      <div className="doc-header-controls">
        {/* Clean Language Toggle */}
        <div className="official-lang-toggle">
          <button
            type="button"
            className={`lang-opt ${lang === "uz" ? "active" : ""}`}
            onClick={() => onLangChange("uz")}
          >
            UZ
          </button>
          <span className="lang-sep">|</span>
          <button
            type="button"
            className={`lang-opt ${lang === "ru" ? "active" : ""}`}
            onClick={() => onLangChange("ru")}
          >
            RU
          </button>
          <span className="lang-sep">|</span>
          <button
            type="button"
            className={`lang-opt ${lang === "en" ? "active" : ""}`}
            onClick={() => onLangChange("en")}
          >
            EN
          </button>
        </div>

        {/* Professional Profile Button & Dropdown */}
        <div className="profile-menu-wrapper" ref={profileRef}>
          <button
            type="button"
            className={`profile-avatar-btn ${profileOpen ? "active" : ""}`}
            onClick={() => setProfileOpen(!profileOpen)}
            title="Shifokor profili va litsenziya"
            aria-label="Doctor Profile"
          >
            <div className="avatar-circle">{initials}</div>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {profileOpen && (
            <div className="profile-dropdown-popover">
              <div className="profile-popover-header">
                <div className="avatar-large">{initials}</div>
                <div className="profile-text-wrap">
                  <div className="profile-name">{doctorName}</div>
                  <div className="profile-role">
                    {role === "nurse" ? "Patronaj hamshirasi" : "Shifokor-kardiolog"}
                  </div>
                  <div className="profile-org">Urganch Kardiologiya Dispanseri</div>
                </div>
              </div>

              {/* B2B License Section inside Profile */}
              <div className="profile-license-card">
                <div className="license-header-line">
                  <span className="license-title">🏥 B2B Litsenziya</span>
                  <span className="license-active-pill">FAOL</span>
                </div>
                <div className="license-details">
                  <div className="license-item">
                    <span className="lic-lbl">Klinika rejimi:</span>
                    <span className="lic-val">OvaBMU / Statsionar</span>
                  </div>
                  <div className="license-item">
                    <span className="lic-lbl">Faol bemorlar:</span>
                    <span className="lic-val">100 ta kvota (85 000 so'm/oy)</span>
                  </div>
                  <div className="license-item">
                    <span className="lic-lbl">Arendadagi soatlar:</span>
                    <span className="lic-val">4 ta biriktirilgan</span>
                  </div>
                </div>
              </div>

              {/* Status / Env info */}
              <div className="profile-system-info">
                <span className="system-dot" />
                <span>Tizim: <b>Jonli (Production)</b> · Himoyalangan</span>
              </div>

              <div className="profile-divider" />

              {/* Logout Button */}
              <button
                type="button"
                className="profile-logout-btn"
                onClick={() => {
                  setProfileOpen(false);
                  onLogout();
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                <span>{t("logout", lang)}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
