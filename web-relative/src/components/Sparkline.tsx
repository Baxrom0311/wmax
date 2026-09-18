import React from "react";
import type { AlertLevel } from "../lib/types";
import { LEVEL_COLOR } from "../lib/types";

interface SparklineProps {
  data: number[];
  level: AlertLevel;
}

export const Sparkline: React.FC<SparklineProps> = ({ data, level }) => {
  const color = LEVEL_COLOR[level];
  const width = 320;
  const height = 84;
  const padX = 12;
  const padY = 14;

  const points = (data && data.length > 0 ? data : [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]).map(
    (val, i, arr) => {
      const x = padX + (i / (arr.length - 1)) * (width - padX * 2);
      // val is 0..1, inverted for SVG coordinate space
      const clamped = Math.max(0, Math.min(1, val));
      const y = height - padY - clamped * (height - padY * 2);
      return { x, y };
    }
  );

  // Generate smooth SVG curve using catmull-rom / bezier control points
  const pathD = points.reduce((acc, curr, i, arr) => {
    if (i === 0) return `M ${curr.x} ${curr.y}`;
    const prev = arr[i - 1];
    const cp1x = prev.x + (curr.x - prev.x) / 2;
    const cp1y = prev.y;
    const cp2x = prev.x + (curr.x - prev.x) / 2;
    const cp2y = curr.y;
    return `${acc} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
  }, "");

  const fillD = `${pathD} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`;

  return (
    <div className="sparkline-wrapper">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="sparkline-svg"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="sparkline-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.22" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path d={fillD} fill="url(#sparkline-grad)" />
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};
