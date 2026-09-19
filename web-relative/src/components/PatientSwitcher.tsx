import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { RelativePatientItem } from "../lib/types";
import { LEVEL_COLOR, LEVEL_WORD_KEY } from "../lib/types";
import { cn } from "../lib/utils";
import { Users } from "lucide-react";

interface PatientSwitcherProps {
  patients: RelativePatientItem[];
  activePatientId: string;
  onSelect: (patient: RelativePatientItem) => void;
  lang: Lang;
}

const STATUS_BADGE: Record<string, string> = {
  green: "bg-green-100 text-green-700 border-green-200",
  amber: "bg-amber-100 text-amber-700 border-amber-200",
  red: "bg-red-100 text-red-700 border-red-200",
  no_data: "bg-slate-100 text-slate-500 border-slate-200",
};

export const PatientSwitcher: React.FC<PatientSwitcherProps> = ({
  patients,
  activePatientId,
  onSelect,
  lang,
}) => {
  if (patients.length <= 1) return null;

  return (
    <div className="px-4 pt-4 pb-1 animate-fade-up">
      <div className="flex items-center gap-1.5 mb-3">
        <Users size={13} className="text-slate-400" />
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
          {t("patients.title", lang)}
        </span>
      </div>

      <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-1">
        {patients.map((p) => {
          const isActive = p.id === activePatientId;
          const statusColor = LEVEL_COLOR[p.level];
          const wordKey = LEVEL_WORD_KEY[p.level];
          const initials = p.full_name
            .split(" ")
            .map((w) => w[0])
            .slice(0, 2)
            .join("");

          const handleClick = () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const tg = (window as any).Telegram?.WebApp?.HapticFeedback;
            if (tg) tg.selectionChanged();
            onSelect(p);
          };

          return (
            <button
              key={p.id}
              type="button"
              onClick={handleClick}
              className={cn(
                "flex items-center gap-3 rounded-2xl border px-4 py-3 transition-all duration-200 cursor-pointer text-left flex-shrink-0 outline-none",
                isActive
                  ? "bg-white shadow-md border-blue-300 ring-1 ring-blue-200"
                  : "bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm"
              )}
            >
              {/* Avatar */}
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-[13px] font-extrabold flex-shrink-0 border"
                style={{
                  backgroundColor: `${statusColor}18`,
                  color: statusColor,
                  borderColor: `${statusColor}40`,
                }}
              >
                {initials}
              </div>

              {/* Info */}
              <div className="flex flex-col gap-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[11px] font-bold text-blue-600">
                    {p.relationship || t("patients.select", lang)}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] font-bold px-1.5 py-0.5 rounded border",
                      STATUS_BADGE[p.level]
                    )}
                  >
                    {t(wordKey, lang)}
                  </span>
                </div>
                <span className="text-[13px] font-bold text-slate-800 truncate max-w-[120px]">
                  {p.full_name}
                </span>
              </div>

              {/* Status dot */}
              <span
                className={cn(
                  "w-2.5 h-2.5 rounded-full flex-shrink-0 ml-1",
                  p.level === "red" ? "dot-pulse-red" : ""
                )}
                style={{ backgroundColor: statusColor }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
};
