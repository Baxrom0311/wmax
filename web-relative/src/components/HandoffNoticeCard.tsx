import React from "react";
import { Building2, Clock, CheckCircle2, Phone } from "lucide-react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface HandoffNoticeCardProps {
  patientName: string;
  facilityName?: string;
  nurseName?: string;
  nursePhone?: string;
  hoursLeft?: number;
  lang: Lang;
}

export const HandoffNoticeCard: React.FC<HandoffNoticeCardProps> = ({
  patientName,
  facilityName = "Urganch Kardiologiya Dispanseri",
  nurseName = "Dilnoza Otajonova",
  nursePhone = "+998 90 123 45 68",
  hoursLeft = 18,
  lang,
}) => {
  return (
    <div className="mx-4 mb-3 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50/60 border border-blue-200/80 p-4 shadow-sm flex flex-col gap-3 animate-fade-up">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
            <Building2 size={16} />
          </div>
          <div>
            <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">
              {t("handoff.badge", lang)}
            </span>
            <h4 className="text-[14px] font-extrabold text-slate-800 leading-tight">
              {t("handoff.title", lang, { name: patientName })}
            </h4>
          </div>
        </div>

        <span className="inline-flex items-center gap-1 text-[10.5px] font-extrabold bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full flex-shrink-0">
          <Clock size={11} />
          {t("handoff.hours_left", lang, { h: hoursLeft })}
        </span>
      </div>

      <p className="text-[12px] text-slate-600 leading-relaxed">
        {t("handoff.desc", lang, { facility: facilityName })}
      </p>

      <div className="bg-white rounded-xl p-3 border border-blue-100 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-9 h-9 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 border border-emerald-100">
            <CheckCircle2 size={18} />
          </div>
          <div className="min-w-0">
            <span className="text-[10px] font-bold text-slate-400 block">{t("handoff.assigned_nurse", lang)}</span>
            <p className="text-[13px] font-bold text-slate-800 truncate">{nurseName} (OvaBMU)</p>
          </div>
        </div>

        <a
          href={`tel:${nursePhone}`}
          className="flex items-center gap-1 text-[12px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-xl hover:bg-blue-100 active:scale-95 transition-all flex-shrink-0"
        >
          <Phone size={13} />
          <span>{t("handoff.call_nurse", lang)}</span>
        </a>
      </div>
    </div>
  );
};
