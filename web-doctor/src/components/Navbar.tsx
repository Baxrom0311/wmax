import React, { useEffect, useRef, useState } from "react";
import {
  Users,
  ArrowRightLeft,
  Siren,
  Watch,
  User,
  LogOut,
  ChevronDown,
  Menu,
  X,
  ExternalLink,
} from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AuthRole } from "../lib/types";

export type NavTab = "patients" | "handoffs" | "sos" | "devices" | "profile";

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
  openHandoffsCount = 0,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown on click outside
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
        .filter(Boolean)
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "??";

  const handleTabClick = (tab: NavTab) => {
    onTabChange(tab);
    setMobileMenuOpen(false);
  };

  const handoffsLabel =
    role === "nurse"
      ? (lang === "ru" ? "Патронаж" : lang === "en" ? "Patronage" : "Patronaj")
      : (lang === "ru" ? "Направления" : lang === "en" ? "Referrals" : "Yo'naltirish");

  return (
    <>
      <header className="doc-header">
        {/* 1. Left: Brand */}
        <div
          className="doc-header-brand"
          onClick={() => handleTabClick("patients")}
          style={{ cursor: "pointer" }}
        >
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

        {/* 2. Center: Desktop Nav tabs (hidden on mobile <=820px) */}
        <nav className="doc-nav-tabs">
          <button
            type="button"
            className={`doc-tab-btn ${activeTab === "patients" ? "active" : ""}`}
            onClick={() => handleTabClick("patients")}
          >
            <span className="tab-icon"><Users size={16} /></span>
            <span className="tab-title">
              {lang === "ru" ? "Пациенты" : lang === "en" ? "Patients" : "Bemorlar"}
            </span>
          </button>

          <button
            type="button"
            className={`doc-tab-btn ${activeTab === "handoffs" ? "active" : ""}`}
            onClick={() => handleTabClick("handoffs")}
          >
            <span className="tab-icon"><ArrowRightLeft size={16} /></span>
            <span className="tab-title">{handoffsLabel}</span>
            {openHandoffsCount > 0 && (
              <span className="tab-badge blue-badge">{openHandoffsCount}</span>
            )}
          </button>

          <button
            type="button"
            className={`doc-tab-btn ${activeTab === "sos" ? "active" : ""}`}
            onClick={() => handleTabClick("sos")}
          >
            <span className="tab-icon"><Siren size={16} /></span>
            <span className="tab-title">
              {lang === "ru" ? "Экстренные" : lang === "en" ? "Emergency" : "Shoshilinch"}
            </span>
            {activeSosCount > 0 && (
              <span className="tab-badge pulse-badge">{activeSosCount}</span>
            )}
          </button>

          <button
            type="button"
            className={`doc-tab-btn ${activeTab === "devices" ? "active" : ""}`}
            onClick={() => handleTabClick("devices")}
          >
            <span className="tab-icon"><Watch size={16} /></span>
            <span className="tab-title">
              {lang === "ru" ? "Устройства" : lang === "en" ? "Devices" : "Qurilmalar"}
            </span>
          </button>
        </nav>

        {/* 3. Right: lang + profile avatar + mobile toggle */}
        <div className="doc-header-controls">
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

          {/* Profile avatar & Dropdown Popover */}
          <div className="profile-menu-wrapper" ref={profileRef} style={{ position: "relative" }}>
            <button
              type="button"
              className={`profile-avatar-btn ${profileOpen ? "active" : ""}`}
              onClick={() => setProfileOpen(!profileOpen)}
              title="Profil va litsenziya"
              aria-label="Doctor Profile"
            >
              <div className="avatar-circle">{initials}</div>
              <ChevronDown
                size={14}
                strokeWidth={2.5}
                style={{
                  transform: profileOpen ? "rotate(180deg)" : "none",
                  transition: "transform 0.2s ease",
                }}
              />
            </button>

            {profileOpen && (
              <div className="profile-dropdown-popover">
                <div className="profile-popover-header">
                  <div className="avatar-large avatar-circle" style={{ fontSize: 16 }}>{initials}</div>
                  <div className="profile-text-wrap">
                    <div className="profile-name">{doctorName}</div>
                    <div className="profile-role">
                      {role === "nurse" ? "Patronaj hamshirasi" : role === "admin" ? "Tizim administratori" : "Shifokor-kardiolog"}
                    </div>
                    <div className="profile-org">
                      {role === "nurse" ? "Urganch shahar 1-son OP (OvaBMU)" : "Urganch Kardiologiya Dispanseri"}
                    </div>
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
                      <span className="lic-val">{role === "nurse" ? "Birlamchi bo'g'in / OvaBMU" : "Ixtisoslashgan Statsionar"}</span>
                    </div>
                    <div className="license-item">
                      <span className="lic-lbl">Faol bemorlar:</span>
                      <span className="lic-val">100 ta kvota (85 000 so'm/oy)</span>
                    </div>
                    <div className="license-item">
                      <span className="lic-lbl">Monitoringdagi bemorlar:</span>
                      <span className="lic-val">4 nafar faol</span>
                    </div>
                  </div>
                </div>

                {/* Status / Env info */}
                <div className="profile-system-info">
                  <span className="system-dot" />
                  <span>Tizim: <b>Jonli (Production)</b> · Himoyalangan</span>
                </div>

                <div className="profile-divider" />

                {/* Open Full Profile Page Button */}
                <button
                  type="button"
                  className="profile-page-link-btn"
                  onClick={() => {
                    setProfileOpen(false);
                    handleTabClick("profile");
                  }}
                >
                  <User size={15} />
                  <span>Profilni ochish va tahrirlash</span>
                  <ExternalLink size={13} style={{ marginLeft: "auto", opacity: 0.7 }} />
                </button>

                {/* Logout Button */}
                <button
                  type="button"
                  className="profile-logout-btn"
                  onClick={() => {
                    setProfileOpen(false);
                    onLogout();
                  }}
                >
                  <LogOut size={16} />
                  <span>{t("logout", lang)}</span>
                </button>
              </div>
            )}
          </div>

          {/* Mobile hamburger menu toggle */}
          <button
            type="button"
            className={`mobile-menu-toggle ${mobileMenuOpen ? "open" : ""}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "Menyuni yopish" : "Menyuni ochish"}
          >
            {mobileMenuOpen ? (
              <X size={22} strokeWidth={2.5} />
            ) : (
              <Menu size={22} strokeWidth={2.5} />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Drawer & Backdrop */}
      {mobileMenuOpen && (
        <>
          <div
            className="mobile-nav-backdrop"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="mobile-nav-dropdown">
            <div className="mobile-user-snippet">
              <div className="avatar-circle">{initials}</div>
              <div className="mobile-user-details">
                <div className="mobile-user-name">{doctorName}</div>
                <div className="mobile-user-role">
                  {role === "nurse" ? "Hamshira" : role === "admin" ? "Administrator" : "Shifokor"}
                </div>
              </div>
            </div>

            <div className="mobile-nav-links">
              <button
                type="button"
                className={`mobile-nav-link ${activeTab === "patients" ? "active" : ""}`}
                onClick={() => handleTabClick("patients")}
              >
                <span className="nav-icon"><Users size={18} /></span>
                <span className="nav-label">
                  {lang === "ru" ? "Пациенты" : lang === "en" ? "Patients" : "Bemorlar"}
                </span>
              </button>

              <button
                type="button"
                className={`mobile-nav-link ${activeTab === "handoffs" ? "active" : ""}`}
                onClick={() => handleTabClick("handoffs")}
              >
                <span className="nav-icon"><ArrowRightLeft size={18} /></span>
                <span className="nav-label">{handoffsLabel}</span>
                {openHandoffsCount > 0 && (
                  <span className="tab-badge blue-badge">{openHandoffsCount}</span>
                )}
              </button>

              <button
                type="button"
                className={`mobile-nav-link ${activeTab === "sos" ? "active" : ""}`}
                onClick={() => handleTabClick("sos")}
              >
                <span className="nav-icon"><Siren size={18} /></span>
                <span className="nav-label">
                  {lang === "ru" ? "Экстренные (SOS)" : lang === "en" ? "Emergency (SOS)" : "Shoshilinch (SOS)"}
                </span>
                {activeSosCount > 0 && (
                  <span className="tab-badge pulse-badge">{activeSosCount}</span>
                )}
              </button>

              <button
                type="button"
                className={`mobile-nav-link ${activeTab === "devices" ? "active" : ""}`}
                onClick={() => handleTabClick("devices")}
              >
                <span className="nav-icon"><Watch size={18} /></span>
                <span className="nav-label">
                  {lang === "ru" ? "Устройства" : lang === "en" ? "Devices" : "Qurilmalar"}
                </span>
              </button>

              <button
                type="button"
                className={`mobile-nav-link ${activeTab === "profile" ? "active" : ""}`}
                onClick={() => handleTabClick("profile")}
              >
                <span className="nav-icon"><User size={18} /></span>
                <span className="nav-label">
                  {lang === "ru" ? "Профиль и лицензия" : lang === "en" ? "Profile & License" : "Profil va litsenziya"}
                </span>
              </button>
            </div>

            <div className="mobile-nav-footer">
              <button
                type="button"
                className="mobile-logout-btn"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onLogout();
                }}
              >
                <LogOut size={16} />
                <span>{lang === "ru" ? "Выйти из системы" : lang === "en" ? "Sign Out" : "Tizimdan chiqish"}</span>
              </button>
            </div>
          </div>
        </>
      )}
    </>
  );
};
