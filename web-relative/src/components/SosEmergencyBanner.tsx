import React, { useState } from "react";
import { Siren, Phone, AlertTriangle, X, ShieldAlert } from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface SosEmergencyBannerProps {
  patientName: string;
  relationship?: string;
  spo2?: number;
  hr?: number;
  doctorPhone?: string;
  nursePhone?: string;
  lang: Lang;
}

export const SosEmergencyBanner: React.FC<SosEmergencyBannerProps> = ({
  patientName,
  relationship = "Yaqiningiz",
  spo2 = 85,
  hr = 128,
  doctorPhone = "+998901234567",
  nursePhone = "+998901234568",
  lang,
}) => {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      {/* Top Sticky Urgent Banner */}
      <div className="mx-4 mt-2 mb-3 rounded-2xl bg-gradient-to-r from-red-600 via-red-700 to-rose-700 text-white p-3.5 shadow-xl shadow-red-200 border border-red-500 flex items-center justify-between gap-3 animate-fade-up">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-white/15 backdrop-blur-md flex items-center justify-center flex-shrink-0 animate-pulse">
            <Siren size={22} className="text-white" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-extrabold text-[13.5px] tracking-tight">
                🚨 {t("sos.attention", lang)} {patientName} ({relationship})
              </span>
              <span className="bg-white/20 text-white font-bold text-[10px] px-2 py-0.5 rounded-full">
                {t("sos.critical", lang)}
              </span>
            </div>
            <p className="text-[11.5px] text-red-100 font-medium leading-tight truncate">
              {t("sos.hypoxia_tachy", lang, { spo2, hr })}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="bg-white text-red-700 font-extrabold text-[12.5px] px-3.5 py-2 rounded-xl shadow-sm hover:bg-red-50 active:scale-95 transition-all flex-shrink-0 whitespace-nowrap"
        >
          {t("sos.action_btn", lang)}
        </button>
      </div>

      {/* Emergency Action Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-up">
          <div className="bg-white rounded-3xl max-w-sm w-full p-5 shadow-2xl border border-red-100 flex flex-col gap-4">
            {/* Modal header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center">
                  <ShieldAlert size={22} />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-[16px] leading-snug">
                    {t("sos.modal_title", lang)}
                  </h3>
                  <p className="text-[12px] text-slate-500">{patientName}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            {/* Vital parameters box */}
            <div className="bg-red-50 border border-red-200/80 rounded-2xl p-3 flex justify-around text-center">
              <div>
                <span className="text-[10px] font-bold text-red-700 uppercase">SpO2</span>
                <p className="text-[20px] font-black text-red-600 leading-tight">{spo2}%</p>
                <span className="text-[10px] text-red-600 font-bold">{t("vitals.risk", lang)}</span>
              </div>
              <div className="w-px bg-red-200" />
              <div>
                <span className="text-[10px] font-bold text-red-700 uppercase">{t("metrics.tab_hr", lang)}</span>
                <p className="text-[20px] font-black text-red-600 leading-tight">{hr} bpm</p>
                <span className="text-[10px] text-red-600 font-bold">{t("vitals.attention", lang)}</span>
              </div>
            </div>

            {/* Call 103 Button */}
            <a
              href="tel:103"
              className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-red-600 to-red-700 text-white font-black text-[15px] flex items-center justify-center gap-2 shadow-lg shadow-red-200 hover:from-red-700 hover:to-red-800 active:scale-[0.98] transition-all"
            >
              <Phone size={18} />
              <span>{t("sos.call_103", lang)}</span>
            </a>

            {/* Doctor & Nurse Direct Calls */}
            <div className="grid grid-cols-2 gap-2">
              <a
                href={`tel:${doctorPhone}`}
                className="p-2.5 rounded-xl border border-blue-200 bg-blue-50 text-blue-700 font-bold text-[12px] flex items-center justify-center gap-1.5 hover:bg-blue-100 transition-colors"
              >
                <Phone size={13} />
                <span>{t("sos.call_doctor", lang)}</span>
              </a>
              <a
                href={`tel:${nursePhone}`}
                className="p-2.5 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-[12px] flex items-center justify-center gap-1.5 hover:bg-emerald-100 transition-colors"
              >
                <Phone size={13} />
                <span>{t("sos.call_nurse", lang)}</span>
              </a>
            </div>

            {/* First Aid Instructions */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3 text-[12px] text-slate-600 leading-relaxed flex flex-col gap-1.5">
              <span className="font-bold text-slate-800 flex items-center gap-1">
                <AlertTriangle size={13} className="text-amber-600" />
                {t("sos.first_aid_title", lang)}
              </span>
              <p>• {t("sos.tip_1", lang)}</p>
              <p>• {t("sos.tip_2", lang)}</p>
              <p>• {t("sos.tip_3", lang)}</p>
            </div>

            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="w-full py-2.5 text-center text-slate-400 font-semibold text-[13px] hover:text-slate-600"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </>
  );
};
