import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { ProblemItem } from "../lib/types";
import { cn } from "../lib/utils";
import { CheckCircle, AlertCircle, TrendingUp } from "lucide-react";

interface ProblemBreakdownProps {
  problems: ProblemItem[];
  lang: Lang;
}

const SEVERITY_STYLES = {
  severe: {
    card: "border-red-200 bg-red-50/30",
    badge: "bg-red-100 text-red-700 border-red-200",
    dot: "bg-red-500",
    devBadge: "bg-red-50 text-red-700 border-red-200",
  },
  moderate: {
    card: "border-amber-200 bg-amber-50/20",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
    dot: "bg-amber-500",
    devBadge: "bg-amber-50 text-amber-700 border-amber-200",
  },
  mild: {
    card: "border-blue-100 bg-blue-50/20",
    badge: "bg-blue-100 text-blue-700 border-blue-100",
    dot: "bg-blue-400",
    devBadge: "bg-blue-50 text-blue-600 border-blue-100",
  },
};

export const ProblemBreakdown: React.FC<ProblemBreakdownProps> = ({ problems, lang }) => {
  return (
    <section className="px-4 pb-4 flex flex-col gap-3 animate-fade-up">
      {/* Section title */}
      <div className="flex items-center gap-2">
        <TrendingUp size={16} className="text-blue-600" />
        <h3 className="text-[14px] font-bold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
          {t("problems.title", lang)}
        </h3>
      </div>

      {problems.length === 0 ? (
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-2xl p-4">
          <CheckCircle size={20} className="text-green-600 flex-shrink-0" />
          <span className="text-[13.5px] font-semibold text-green-800">
            {t("problems.none", lang)}
          </span>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {problems.map((prob, idx) => {
            const s = SEVERITY_STYLES[prob.severity] ?? SEVERITY_STYLES.mild;
            return (
              <div
                key={idx}
                className={cn(
                  "rounded-2xl border p-4 flex flex-col gap-3 transition-all duration-200",
                  s.card
                )}
              >
                {/* Top row */}
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className={cn("w-2.5 h-2.5 rounded-full flex-shrink-0", s.dot)} />
                    <span className="text-[14px] font-extrabold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
                      {prob.label}
                    </span>
                  </div>
                  <span className={cn("text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border", s.devBadge)}>
                    {prob.deviation}
                  </span>
                </div>

                {/* Values comparison */}
                <div className="flex items-center gap-2 bg-white/70 rounded-xl border border-white px-3 py-2.5">
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                      {t("problems.current", lang)}
                    </span>
                    <span className="text-[20px] font-extrabold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
                      {prob.current_value}
                    </span>
                  </div>
                  <div className="h-8 w-px bg-slate-200 flex-shrink-0" />
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                      {t("problems.baseline", lang)}
                    </span>
                    <span className="text-[14px] font-bold text-slate-500">
                      {prob.baseline_range}
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-[12.5px] text-slate-600 leading-relaxed">
                  {prob.explanation}
                </p>

                {/* Severity indicator */}
                <div className="flex items-center gap-1.5">
                  <AlertCircle size={12} className={
                    prob.severity === "severe" ? "text-red-500" :
                    prob.severity === "moderate" ? "text-amber-500" : "text-blue-400"
                  } />
                  <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-full border", s.badge)}>
                    {prob.severity === "severe" ? (lang === "ru" ? "Тяжёлое" : "Og'ir") :
                     prob.severity === "moderate" ? (lang === "ru" ? "Умеренное" : "O'rta") :
                     (lang === "ru" ? "Лёгкое" : "Yengil")}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
