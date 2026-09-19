import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { Task } from "../lib/types";
import { cn } from "../lib/utils";
import {
  Stethoscope,
  Phone,
  Send,
  Clock3,
  Siren,
} from "lucide-react";

interface ActionContactBarProps {
  doctorContact?: { name: string; phone: string } | null;
  activeTask?: Task | null;
  recommendation?: string;
  lang: Lang;
}

export const ActionContactBar: React.FC<ActionContactBarProps> = ({
  doctorContact,
  activeTask,
  recommendation,
  lang,
}) => {
  return (
    <section className="px-4 pb-4 flex flex-col gap-3 animate-fade-up">
      {/* Section title */}
      <div className="flex items-center gap-2">
        <Stethoscope size={16} className="text-blue-600" />
        <h3 className="text-[14px] font-bold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
          {t("actions.title", lang)}
        </h3>
      </div>

      {/* Doctor Card */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 flex flex-col gap-4">
        {/* Doctor info row */}
        <div className="flex items-center gap-3">
          <div className="relative w-12 h-12 rounded-full bg-blue-50 border-2 border-blue-100 flex items-center justify-center text-2xl flex-shrink-0">
            👨‍⚕️
            <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-green-500 border-2 border-white" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-[10.5px] font-bold text-blue-600 uppercase tracking-wide">
              {t("actions.doctor_name", lang)}
            </span>
            <h4 className="text-[15px] font-extrabold text-slate-800 leading-tight" style={{ fontFamily: "'Outfit',sans-serif" }}>
              {doctorContact?.name || "Dr. Bahrom Alimov"}
            </h4>
            <span className="text-[11px] text-slate-400">
              {t("actions.doc_specialty", lang)}
            </span>
            {recommendation && (
              <p className="text-[12px] text-slate-600 mt-1 leading-snug">
                💬 {recommendation}
              </p>
            )}
          </div>
        </div>

        {/* Call buttons row */}
        <div className="grid grid-cols-2 gap-2">
          <a
            href={`tel:${doctorContact?.phone || "+998901234567"}`}
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl font-semibold text-[13px] transition-all",
              "bg-blue-600 text-white shadow-sm hover:bg-blue-700 active:scale-95"
            )}
          >
            <Phone size={15} />
            {t("actions.call_doctor", lang)}
          </a>
          <a
            href="https://t.me/WMAX_uz_bot"
            target="_blank"
            rel="noreferrer"
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl font-semibold text-[13px] transition-all",
              "bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 active:scale-95"
            )}
          >
            <Send size={15} />
            {t("actions.telegram", lang)}
          </a>
        </div>
      </div>

      {/* Active patronaj notice */}
      {activeTask && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 border-l-4 border-l-amber-500 rounded-xl p-4">
          <Clock3 size={20} className="text-amber-600 flex-shrink-0" />
          <div>
            <strong className="text-[13px] text-amber-800">
              {t("actions.active_call_status", lang)}:
            </strong>
            <p className="text-[12px] text-amber-700">
              {t("actions.active_call_scheduled", lang)}
            </p>
          </div>
        </div>
      )}

      {/* Emergency 103 */}
      <a
        href="tel:103"
        className={cn(
          "flex items-center justify-between px-5 py-4 rounded-2xl transition-all",
          "bg-gradient-to-r from-red-600 to-red-500 text-white shadow-lg shadow-red-200",
          "hover:from-red-700 hover:to-red-600 active:scale-[0.98]"
        )}
      >
        <div className="flex items-center gap-3">
          <Siren size={22} className="flex-shrink-0" />
          <span className="text-[14px] font-bold">{t("actions.emergency", lang)}</span>
        </div>
        <span className="bg-white text-red-600 text-[14px] font-black px-3 py-1 rounded-xl">
          103
        </span>
      </a>
    </section>
  );
};
