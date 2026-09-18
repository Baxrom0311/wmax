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

  const getStatusIcon = (lvl: AlertLevel) => {
    if (lvl === "green") return "🛡️";
    if (lvl === "amber") return "⚠️";
    if (lvl === "red") return "🚨";
    return "📡";
  };

  return (
    <div className="hero-prognosis-wrapper">
      {/* 1. Katta Doira / Status Hub */}
      <div className="status-hub-card">
        <div className="orb-outer-halo">
          <div
            className={`main-orb orb-${level}`}
            style={{
              backgroundColor: color,
            }}
          >
            <div className="orb-inner-content">
              <span className="orb-icon">{getStatusIcon(level)}</span>
              <span className="orb-status-text">{word}</span>
            </div>
          </div>
        </div>

        <div className="status-hub-meta">
          <div className="composite-badge">
            <span className="composite-dot" style={{ backgroundColor: color }} />
            <span>
              {t("hero.composite_deviation", lang)}:{" "}
              <strong>{compositeScore > 0 ? `+${compositeScore.toFixed(1)}` : compositeScore.toFixed(1)}σ</strong>
            </span>
          </div>
          <span className="time-ago-text">
            <span className="time-icon">🕒</span> {formatLastUpdated(lastReadingAt)}
          </span>
        </div>
      </div>

      {/* 2. AI 72-soatlik Erta Ogohlantirish Prognozi */}
      {level !== "no_data" && prognosis && (
        <div className="ai-prognosis-card">
          <div className="prognosis-header">
            <div className="prognosis-badge-group">
              <span className="prognosis-ai-tag">✨ AI CLINICAL ENGINE</span>
              <span className="prognosis-sub-tag">CIRCADIAN 72H</span>
            </div>
            <span
              className="prognosis-risk-badge"
              style={{
                backgroundColor: `${getRiskColor(prognosis.risk_level)}15`,
                color: getRiskColor(prognosis.risk_level),
                borderColor: `${getRiskColor(prognosis.risk_level)}35`,
              }}
            >
              {t(`hero.risk_${prognosis.risk_level}`, lang)}: {prognosis.risk_probability_pct}%
            </span>
          </div>

          <h3 className="prognosis-title">{t("hero.prognosis_title", lang)}</h3>

          {/* Visual Risk Meter */}
          <div className="prognosis-meter-track">
            <div
              className={`prognosis-meter-fill risk-${prognosis.risk_level}`}
              style={{
                width: `${prognosis.risk_probability_pct}%`,
                backgroundColor: getRiskColor(prognosis.risk_level),
              }}
            />
          </div>

          <p className="prognosis-summary">{prognosis.summary}</p>

          <div className="prognosis-footer">
            <div className="early-warning-tag">
              ⏱ {t("hero.early_warning", lang, { h: prognosis.early_warning_hours || 48 })}
            </div>
            <div className="prognosis-rec-box">
              <span className="prognosis-rec-icon">💡</span>
              <p className="prognosis-rec">
                <strong>Tavsiya:</strong> {prognosis.recommendation}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
