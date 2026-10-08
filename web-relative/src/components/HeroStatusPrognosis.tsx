import React, { useEffect, useState } from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AlertLevel, PrognosisInfo } from "../lib/types";
import { LEVEL_COLOR, LEVEL_WORD_KEY } from "../lib/types";
import { cn } from "../lib/utils";
import { PeaceOfMindCard } from "./PeaceOfMindCard";
import {
  ShieldCheck,
  AlertTriangle,
  Siren,
  Signal,
  Clock,
  BrainCircuit,
  Lightbulb,
  TrendingUp,
} from "lucide-react";

interface HeroStatusPrognosisProps {
  level: AlertLevel;
  compositeScore: number;
  lastReadingAt: string | null;
  prognosis: PrognosisInfo;
  lang: Lang;
}

const ORB_ICON: Record<AlertLevel, React.ReactNode> = {
  green: <ShieldCheck size={36} strokeWidth={2.5} />,
  amber: <AlertTriangle size={36} strokeWidth={2.5} />,
  red: <Siren size={36} strokeWidth={2.5} />,
  no_data: <Signal size={36} strokeWidth={2.5} />,
};

const RISK_BADGES: Record<string, string> = {
  low: "bg-green-50 dark:bg-green-950/50 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800",
  moderate: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
  high: "bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800",
};

export const HeroStatusPrognosis: React.FC<HeroStatusPrognosisProps> = ({
  level,
  compositeScore,
  lastReadingAt,
  prognosis,
  lang,
}) => {
  const color = LEVEL_COLOR[level];
  const wordKey = LEVEL_WORD_KEY[level];
  const word = t(wordKey, lang);

  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick((v) => v + 1), 10000);
    return () => clearInterval(timer);
  }, []);

  const formatLastUpdated = (isoDate: string | null) => {
    if (!isoDate) return t("updated.just_now", lang);
    // oxlint-disable-next-line react/purity -- wall-clock intentional
    const diffMins = Math.max(1, Math.round((Date.now() - new Date(isoDate).getTime()) / 60000));
    if (diffMins < 60) return t("updated.mins_ago", lang, { m: diffMins });
    return t("updated.hours_ago", lang, { h: Math.round(diffMins / 60) });
  };

  return (
    <div className="flex flex-col gap-4 px-4 pt-3 pb-4 animate-fade-up">
      {/* ── Status Orb Card ── */}
      <div className="rounded-3xl bg-white border border-slate-100 shadow-sm overflow-hidden">
        {/* Top tinted stripe matching status */}
        <div
          className="h-1.5 w-full"
          style={{ background: `linear-gradient(90deg, ${color}88, ${color}44)` }}
        />
        <div className="flex flex-col items-center py-8 px-6 gap-4">
          {/* Orb */}
          <div
            className={cn(
              "w-36 h-36 rounded-full flex flex-col items-center justify-center gap-1.5 shadow-lg transition-all duration-300",
              `main-orb orb-${level}`
            )}
          >
            {ORB_ICON[level]}
            <span className="text-[17px] font-extrabold tracking-wide text-shadow-sm"
              style={{ fontFamily: "'Outfit', sans-serif" }}>
              {word}
            </span>
          </div>

          {/* Meta row */}
          <div className="flex flex-col items-center gap-2 w-full">
            {/* Composite score badge */}
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5">
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-slate-600 dark:text-slate-300">
                {t("hero.composite_deviation", lang)}:{" "}
                <strong className="text-blue-600 dark:text-blue-400 font-bold">
                  {compositeScore > 0 ? `+${compositeScore.toFixed(1)}` : compositeScore.toFixed(1)}σ
                </strong>
              </span>
            </div>

            {/* Last updated */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500">
              <Clock size={12} />
              {formatLastUpdated(lastReadingAt)}
            </div>
          </div>
        </div>
      </div>

      {/* ── Tinchlik Ko'rsatkichi (Peace of Mind Index) Card ── */}
      <PeaceOfMindCard
        level={level}
        compositeScore={compositeScore}
        lang={lang}
      />

      {/* ── Signal summary; no unvalidated probability or forecast ── */}
      {level !== "no_data" && prognosis && (
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm p-5 flex flex-col gap-4">
          {/* Header row */}
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-100 dark:border-blue-900/50 flex items-center justify-center">
                <BrainCircuit size={15} className="text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10.5px] font-extrabold bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 px-2 py-0.5 rounded tracking-wider uppercase">
                    {t("hero.prognosis_title", lang)}
                  </span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-semibold">
                    {t("hero.circadian_tag", lang)}
                  </span>
                </div>
              </div>
            </div>
            {/* Risk level badge */}
            <span
              className={cn(
                "text-xs font-bold px-3 py-1 rounded-full border",
                RISK_BADGES[prognosis.risk_level] || RISK_BADGES.low
              )}
            >
              {t(`hero.risk_${prognosis.risk_level}`, lang)}
            </span>
          </div>

          <h3 className="text-[14px] font-bold text-slate-800 dark:text-slate-100" style={{ fontFamily: "'Outfit',sans-serif" }}>
            {t("hero.prognosis_title", lang)}
          </h3>

          <p className="text-[13.5px] text-slate-700 dark:text-slate-300 leading-relaxed">{prognosis.summary}</p>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-3 flex flex-col gap-3">
            <div className="flex items-start gap-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/40 rounded-xl p-3">
              <Lightbulb size={16} className="text-blue-500 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <p className="text-[12.5px] text-slate-700 dark:text-slate-300 leading-snug">
                <strong className="text-slate-800 dark:text-slate-100">{t("hero.rec_label", lang)} </strong>
                {prognosis.recommendation}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trend indicator strip (no_data safe) */}
      {level !== "no_data" && (
        <div className="flex items-center gap-2 px-1">
          <TrendingUp size={14} className="text-blue-400" />
          <span className="text-xs text-slate-400 font-medium">
            {t("trend.stable", lang)}
          </span>
        </div>
      )}
    </div>
  );
};
