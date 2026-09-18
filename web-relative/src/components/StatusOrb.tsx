import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { AlertLevel } from "../lib/types";
import { LEVEL_COLOR, LEVEL_WORD_KEY } from "../lib/types";

interface StatusOrbProps {
  level: AlertLevel;
  lang: Lang;
}

export const StatusOrb: React.FC<StatusOrbProps> = ({ level, lang }) => {
  const color = LEVEL_COLOR[level];
  const wordKey = LEVEL_WORD_KEY[level];
  const word = t(wordKey, lang);

  return (
    <div className="orb-container">
      <div
        className="status-orb"
        style={{
          backgroundColor: color,
          boxShadow: `0 12px 40px ${color}33`,
        }}
      >
        <span className="orb-word">{word}</span>
      </div>
    </div>
  );
};
