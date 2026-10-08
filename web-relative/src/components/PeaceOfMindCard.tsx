import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AlertLevel } from "../lib/types";
import { cn } from "../lib/utils";
import {
  HeartHandshake,
  Sparkles,
  AlertTriangle,
  Siren,
  WifiOff,
  Smile,
  ShieldCheck,
  Compass,
} from "lucide-react";

export type PeaceStatus = "peaceful" | "attention" | "alert" | "no_data";

interface PeaceOfMindCardProps {
  level: AlertLevel;
  compositeScore?: number;
  lang: Lang;
  className?: string;
}

export const PeaceOfMindCard: React.FC<PeaceOfMindCardProps> = ({
  level,
  compositeScore = 0,
  lang,
  className,
}) => {
  // Map alert level to PeaceStatus
  const status: PeaceStatus =
    level === "green"
      ? "peaceful"
      : level === "amber"
      ? "attention"
      : level === "red"
      ? "alert"
      : "no_data";

  // Calculate peaceful index percentage (0-100%)
  const peaceScore =
    status === "peaceful"
      ? Math.max(92, Math.min(99, Math.round(98 - Math.abs(compositeScore) * 2)))
      : status === "attention"
      ? Math.max(65, Math.min(84, Math.round(76 - Math.abs(compositeScore) * 4)))
      : status === "alert"
      ? Math.max(25, Math.min(48, Math.round(38 - Math.abs(compositeScore) * 3)))
      : null;

  // Visual theming tokens for each peace status
  const STATUS_CONFIG: Record<
    PeaceStatus,
    {
      cardBg: string;
      borderColor: string;
      badgeBg: string;
      badgeText: string;
      badgeBorder: string;
      haloColor: string;
      icon: React.ReactNode;
      barColor: string;
    }
  > = {
    peaceful: {
      cardBg:
        "bg-gradient-to-br from-emerald-50/70 via-teal-50/40 to-sky-50/60 dark:from-emerald-950/30 dark:via-slate-900 dark:to-teal-950/20",
      borderColor: "border-emerald-200/80 dark:border-emerald-900/50",
      badgeBg: "bg-emerald-100/90 dark:bg-emerald-900/60",
      badgeText: "text-emerald-800 dark:text-emerald-200",
      badgeBorder: "border-emerald-300 dark:border-emerald-700",
      haloColor: "bg-emerald-500",
      icon: <Smile size={18} className="text-emerald-600 dark:text-emerald-400" />,
      barColor: "bg-emerald-500",
    },
    attention: {
      cardBg:
        "bg-gradient-to-br from-amber-50/80 via-orange-50/40 to-yellow-50/50 dark:from-amber-950/30 dark:via-slate-900 dark:to-orange-950/20",
      borderColor: "border-amber-200/90 dark:border-amber-900/50",
      badgeBg: "bg-amber-100/90 dark:bg-amber-900/60",
      badgeText: "text-amber-800 dark:text-amber-200",
      badgeBorder: "border-amber-300 dark:border-amber-700",
      haloColor: "bg-amber-500",
      icon: <AlertTriangle size={18} className="text-amber-600 dark:text-amber-400" />,
      barColor: "bg-amber-500",
    },
    alert: {
      cardBg:
        "bg-gradient-to-br from-rose-50/80 via-red-50/40 to-orange-50/50 dark:from-rose-950/30 dark:via-slate-900 dark:to-red-950/20",
      borderColor: "border-rose-200/90 dark:border-rose-900/50",
      badgeBg: "bg-rose-100/90 dark:bg-rose-900/60",
      badgeText: "text-rose-800 dark:text-rose-200",
      badgeBorder: "border-rose-300 dark:border-rose-700",
      haloColor: "bg-rose-500",
      icon: <Siren size={18} className="text-rose-600 dark:text-rose-400" />,
      barColor: "bg-rose-500",
    },
    no_data: {
      cardBg:
        "bg-gradient-to-br from-slate-50/80 via-slate-100/40 to-slate-50/60 dark:from-slate-900/80 dark:via-slate-900 dark:to-slate-800/50",
      borderColor: "border-slate-200 dark:border-slate-800",
      badgeBg: "bg-slate-100 dark:bg-slate-800",
      badgeText: "text-slate-700 dark:text-slate-300",
      badgeBorder: "border-slate-300 dark:border-slate-700",
      haloColor: "bg-slate-400",
      icon: <WifiOff size={18} className="text-slate-500 dark:text-slate-400" />,
      barColor: "bg-slate-400",
    },
  };

  const currentCfg = STATUS_CONFIG[status];

  return (
    <section
      className={cn(
        "rounded-3xl border shadow-xs p-4 sm:p-5 flex flex-col gap-3.5 transition-all duration-300",
        currentCfg.cardBg,
        currentCfg.borderColor,
        className
      )}
      aria-label={t("peace.title", lang)}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-white/80 dark:bg-slate-800/90 border border-white dark:border-slate-700 flex items-center justify-center shadow-xs flex-shrink-0">
            <HeartHandshake size={17} className="text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span
                className="text-[14px] font-extrabold text-slate-800 dark:text-slate-100 tracking-tight"
                style={{ fontFamily: "'Outfit', sans-serif" }}
              >
                {t("peace.title", lang)}
              </span>
              <Sparkles size={13} className="text-amber-500" />
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
              {t("peace.subtitle", lang)}
            </p>
          </div>
        </div>

        {/* Serene Status Pill */}
        <div
          className={cn(
            "flex items-center gap-1.5 text-xs font-extrabold px-3 py-1 rounded-full border shadow-xs flex-shrink-0",
            currentCfg.badgeBg,
            currentCfg.badgeText,
            currentCfg.badgeBorder
          )}
        >
          {currentCfg.icon}
          <span>{t(`peace.status_${status}`, lang)}</span>
        </div>
      </div>

      {/* 3-Step Peace Gauge Meter */}
      <div className="flex flex-col gap-1.5 pt-1">
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Compass size={12} className="text-slate-400" />
            {t("peace.score_label", lang)}
          </span>
          {peaceScore !== null && (
            <span className="font-extrabold text-slate-800 dark:text-slate-200">
              {peaceScore}% {t("peace.stability", lang)}
            </span>
          )}
        </div>

        {/* Triple serenity track */}
        <div className="grid grid-cols-3 gap-1.5 h-2 w-full">
          {/* Segment 1: Peaceful */}
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              status === "peaceful"
                ? "bg-emerald-500 ring-2 ring-emerald-300 dark:ring-emerald-700"
                : "bg-slate-200/80 dark:bg-slate-800"
            )}
          />
          {/* Segment 2: Attention */}
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              status === "attention"
                ? "bg-amber-500 ring-2 ring-amber-300 dark:ring-amber-700"
                : "bg-slate-200/80 dark:bg-slate-800"
            )}
          />
          {/* Segment 3: Alert */}
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              status === "alert"
                ? "bg-rose-500 ring-2 ring-rose-300 dark:ring-rose-700"
                : "bg-slate-200/80 dark:bg-slate-800"
            )}
          />
        </div>
      </div>

      {/* Reassuring Emotional Description */}
      <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xs rounded-2xl p-3 border border-white/90 dark:border-slate-800/90 flex flex-col gap-2">
        <div className="flex items-start gap-2">
          <ShieldCheck size={16} className="text-blue-500 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="text-[12.5px] text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
            <strong className="text-slate-900 dark:text-slate-100 mr-1">
              {t("peace.reassurance_label", lang)}
            </strong>
            {t(`peace.desc_${status}`, lang)}
          </p>
        </div>

        {/* Thoughtful advice for relatives */}
        <div className="border-t border-slate-100 dark:border-slate-800/80 pt-2 flex items-center gap-1.5 text-[11.5px] text-slate-600 dark:text-slate-400">
          <span className="font-bold text-slate-800 dark:text-slate-200">
            {t("peace.advice_label", lang)}
          </span>
          <span className="italic">{t(`peace.advice_${status}`, lang)}</span>
        </div>
      </div>
    </section>
  );
};
