import React from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ParamSeries } from "../lib/types";
import { COLORS } from "../lib/types";

interface ParamChartProps {
  series: ParamSeries;
}

const PARAM_LABELS: Record<string, { title: string; unit: string; color: string; icon: string }> = {
  hr_mean: { title: "Puls (Tinch holatda)", unit: "bpm", color: "#B3261E", icon: "❤️" },
  spo2: { title: "Kislorod to'yinishi (SpO₂)", unit: "%", color: "#2E7D5B", icon: "🫁" },
  skin_temp: { title: "Teri harorati", unit: "°C", color: "#C77A0A", icon: "🌡️" },
  rmssd: { title: "Yurak variabelligi (RMSSD)", unit: "ms", color: "#4A4740", icon: "💓" },
  sdnn: { title: "Yurak ritmi variabilligi (SDNN)", unit: "ms", color: "#6A5ACD", icon: "📈" },
  rr_est: { title: "Nafas tezligi (RR)", unit: "/min", color: "#2B6CB0", icon: "🌬️" },
  steps: { title: "Kunlik qadamlar / Faollik", unit: "qadam", color: "#319795", icon: "👟" },
  sleep_frag: { title: "Uyqu uzilishi / Fragilite", unit: "%", color: "#4C51BF", icon: "🌙" },
};

export const ParamChart: React.FC<ParamChartProps> = ({ series }) => {
  const meta = PARAM_LABELS[series.param] || {
    title: series.param,
    unit: "",
    color: COLORS.text,
    icon: "📊",
  };

  const latestPoint = series.points && series.points.length > 0 ? series.points[series.points.length - 1] : null;

  const formattedData = series.points.map((p) => ({
    time: new Date(p.ts).toLocaleDateString([], {
      weekday: "short",
      hour: "2-digit",
    }),
    value: p.value,
    rawTs: p.ts,
  }));

  const hasDeviations = series.deviated_ranges && series.deviated_ranges.length > 0;

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div className="chart-title-left">
          <span className="chart-icon">{meta.icon}</span>
          <span className="chart-title">{meta.title}</span>
          {latestPoint && (
            <span className="chart-latest-val" style={{ color: meta.color }}>
              {latestPoint.value} {meta.unit}
            </span>
          )}
        </div>
        <div className="chart-meta-right">
          {series.baseline_median !== null && (
            <span className="chart-meta-badge">
              Baza: <strong>{series.baseline_median}</strong> ({series.baseline_low} – {series.baseline_high} {meta.unit})
            </span>
          )}
          {hasDeviations && (
            <span className="deviations-tag urgent">
              ⚠️ Og'ish
            </span>
          )}
        </div>
      </div>

      <div style={{ width: "100%", height: 165 }}>
        <ResponsiveContainer>
          <LineChart data={formattedData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.line} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: COLORS.nodata }}
              interval="preserveStartEnd"
              tickLine={false}
              axisLine={{ stroke: COLORS.line }}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fontSize: 11, fill: COLORS.nodata }}
              tickLine={false}
              axisLine={{ stroke: COLORS.line }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: `1px solid ${COLORS.line}`,
                fontSize: "12px",
                borderRadius: "6px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
              formatter={(val: unknown) => [`${val} ${meta.unit}`, meta.title]}
            />
            {series.baseline_low !== null && series.baseline_high !== null && (
              <ReferenceArea
                y1={series.baseline_low}
                y2={series.baseline_high}
                fill="#2E7D5B"
                fillOpacity={0.08}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={hasDeviations ? COLORS.risk : meta.color}
              strokeWidth={2.2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
