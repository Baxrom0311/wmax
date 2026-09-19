import React, { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut, ShieldCheck, Heart, User, Clock, Stethoscope } from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { RelativePatientItem } from "../lib/types";

interface RelativeProfilePopoverProps {
  userName?: string;
  userPhone?: string;
  patients: RelativePatientItem[];
  activePatientId: string;
  onSelectPatient: (id: string) => void;
  onLogout: () => void;
  lang: Lang;
}

export const RelativeProfilePopover: React.FC<RelativeProfilePopoverProps> = ({
  userName = "Dilnoza Ro'zmetova",
  userPhone = "+998 90 111 00 11",
  patients,
  activePatientId,
  onSelectPatient,
  onLogout,
  lang,
}) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Outside click listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  const initials = userName
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "DR";

  return (
    <div className="relative" ref={ref}>
      {/* Avatar Button */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 p-1 pr-2 rounded-full border border-slate-200 bg-white hover:bg-slate-50 transition-all shadow-sm active:scale-95"
        aria-label="Foydalanuvchi profili"
      >
        <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-black text-[11px] flex items-center justify-center shadow-xs">
          {initials}
        </div>
        <ChevronDown
          size={13}
          className={`text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {/* Dropdown Popover */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-24px)] bg-white rounded-2xl border border-slate-200 shadow-2xl p-4 z-50 animate-fade-up">
          {/* User identity */}
          <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 text-blue-700 font-extrabold text-base flex items-center justify-center flex-shrink-0">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="font-extrabold text-slate-800 text-[14.5px] truncate">
                {userName}
              </h4>
              <p className="text-[12px] text-blue-600 font-semibold flex items-center gap-1">
                <User size={12} />
                <span>{t("popover.role", lang)}</span>
              </p>
              <p className="text-[11px] text-slate-400 font-medium truncate">
                {userPhone}
              </p>
            </div>
          </div>

          {/* Connected Patients Section */}
          {patients.length > 0 && (
            <div className="py-3 border-b border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                {t("popover.connected_patients", lang, { n: patients.length })}
              </span>
              <div className="flex flex-col gap-1.5">
                {patients.map((p) => {
                const isActive = p.id === activePatientId;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      onSelectPatient(p.id);
                      setOpen(false);
                    }}
                    className={`flex items-center justify-between p-2 rounded-xl text-left text-[12.5px] transition-colors ${
                      isActive
                        ? "bg-blue-50 text-blue-800 font-bold border border-blue-200"
                        : "hover:bg-slate-50 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Heart size={13} className={isActive ? "text-blue-600" : "text-slate-400"} />
                      <span className="truncate">{p.full_name}</span>
                    </div>
                    <span className="text-[10.5px] px-2 py-0.5 rounded-md font-semibold bg-white border border-slate-100 text-slate-500">
                      {p.relationship || "Bemor"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
          )}

          {/* Assigned Healthcare & Patronage Team */}
          <div className="py-3 border-b border-slate-100 flex flex-col gap-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              {t("popover.medical_team", lang)}
            </span>
            <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5 flex flex-col gap-1 text-[11.5px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 flex items-center gap-1">
                  <Stethoscope size={12} className="text-blue-600" />
                  {t("popover.family_doctor", lang)}
                </span>
                <span className="font-bold text-slate-700">Dr. Bahrom Alimov</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 flex items-center gap-1">
                  <Clock size={12} className="text-emerald-600" />
                  {t("popover.patronage_nurse", lang)}
                </span>
                <span className="font-bold text-slate-700">Dilnoza Otajonova (OvaBMU)</span>
              </div>
            </div>
          </div>

          {/* B2B License & Family Plan Status */}
          <div className="py-3 border-b border-slate-100">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11.5px] font-extrabold text-slate-700 flex items-center gap-1">
                <ShieldCheck size={14} className="text-emerald-600" />
                <span>{t("popover.license_title", lang)}</span>
              </span>
              <span className="text-[9.5px] font-extrabold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
                {t("popover.license_active", lang)}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-snug">
              {t("popover.license_desc", lang)}
            </p>
          </div>

          {/* Logout button */}
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            className="w-full mt-3 py-2.5 px-3 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 font-bold text-[12.5px] flex items-center justify-center gap-2 transition-colors active:scale-95"
          >
            <LogOut size={14} />
            <span>{t("logout", lang)}</span>
          </button>
        </div>
      )}
    </div>
  );
};
