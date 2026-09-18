import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AlertLevel, PrognosisInfo } from "../lib/types";
import { LEVEL_COLOR, LEVEL_WORD_KEY } from "../lib/types";

interface HeroStatusPrognosisProps {
  level: AlertLevel;
  compositeScore: number;
  lastReadingAt: string | null;
  prognosis: PrognosisInfo;
  lang: Lang;
}

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

  const formatLastUpdated = (isoDate: string | null) => {
    if (!isoDate) return t("updated.just_now", lang);
    const diffMins = Math.max(1, Math.round((Date.now() - new Date(isoDate).getTime()) / 60000));
    if (diffMins < 60) {
      return t("updated.mins_ago", lang, { m: diffMins });
    }
    const diffHours = Math.round(diffMins / 60);
    return t("updated.hours_ago", lang, { h: diffHours });
  };

  const getRiskColor = (risk: string) => {
    if (risk === "high") return "var(--color-risk)";
    if (risk === "moderate") return "var(--color-attention)";
    return "var(--color-good)";
  };

  return (
    <div className="hero-prognosis-wrapper">
      {/* 1. Katta Doira / Status Hub */}
      <div className="status-hub-card">
        <div
          className="main-orb"
          style={{
            backgroundColor: color,
            boxShadow: `0 14px 45px ${color}40`,
          }}
        >
          <span className="orb-status-text">{word}</span>
        </div>

        <div className="status-hub-meta">
          <span className="composite-badge">
            {t("hero.composite_deviation", lang)}: <strong>{compositeScore.toFixed(1)}σ</strong>
          </span>
          <span className="time-ago-text">{formatLastUpdated(lastReadingAt)}</span>
        </div>
      </div>

      {/* 2. AI 72-soatlik Erta Ogohlantirish Prognozi */}
      {level !== "no_data" && prognosis && (
        <div className="ai-prognosis-card">
          <div className="prognosis-header">
            <span className="prognosis-ai-tag">AI CLINICAL ENGINE</span>
            <span
              className="prognosis-risk-badge"
              style={{
                backgroundColor: `${getRiskColor(prognosis.risk_level)}20`,
                color: getRiskColor(prognosis.risk_level),
                borderColor: getRiskColor(prognosis.risk_level),
              }}
            >
              {t(`hero.risk_${prognosis.risk_level}`, lang)}: {prognosis.risk_probability_pct}%
            </span>
          </div>

          <h3 className="prognosis-title">{t("hero.prognosis_title", lang)}</h3>

          <p className="prognosis-summary">{prognosis.summary}</p>

          <div className="prognosis-footer">
            <div className="early-warning-tag">
              ⏱ {t("hero.early_warning", lang, { h: prognosis.early_warning_hours || 48 })}
            </div>
            <p className="prognosis-rec">
              💡 <strong>Tavsiya:</strong> {prognosis.recommendation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
