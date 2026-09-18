import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { ProblemItem } from "../lib/types";

interface ProblemBreakdownProps {
  problems: ProblemItem[];
  lang: Lang;
}

export const ProblemBreakdown: React.FC<ProblemBreakdownProps> = ({ problems, lang }) => {
  return (
    <div className="problems-section">
      <h3 className="section-title">{t("problems.title", lang)}</h3>

      {problems.length === 0 ? (
        <div className="no-problems-card">
          <span>✓ {t("problems.none", lang)}</span>
        </div>
      ) : (
        <div className="problems-grid">
          {problems.map((prob, idx) => {
            const isSevere = prob.severity === "severe";
            const isModerate = prob.severity === "moderate";
            const badgeColor = isSevere
              ? "var(--color-risk)"
              : isModerate
              ? "var(--color-attention)"
              : "var(--color-good)";

            return (
              <div key={idx} className="problem-card">
                <div className="problem-top-row">
                  <span className="problem-label">{prob.label}</span>
                  <span
                    className="problem-deviation-badge"
                    style={{
                      color: badgeColor,
                      backgroundColor: `${badgeColor}15`,
                      borderColor: `${badgeColor}40`,
                    }}
                  >
                    {prob.deviation}
                  </span>
                </div>

                <div className="problem-values-row">
                  <div className="val-col">
                    <span className="val-col-title">{t("problems.current", lang)}:</span>
                    <span className="val-col-number">{prob.current_value}</span>
                  </div>
                  <div className="val-divider" />
                  <div className="val-col">
                    <span className="val-col-title">{t("problems.baseline", lang)}:</span>
                    <span className="val-col-number" style={{ color: "var(--color-muted)" }}>
                      {prob.baseline_range}
                    </span>
                  </div>
                </div>

                <p className="problem-explanation">{prob.explanation}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
