import React, { useState } from "react";
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
import type { Lang } from "../i18n";
import { t } from "../i18n";
import type { ParamSeries } from "../lib/types";
import { COLORS } from "../lib/types";

interface InteractiveMetricsProps {
  series: ParamSeries[];
  lang: Lang;
}

type TimeRange = "24h" | "3d" | "7d";

const PARAM_TABS: Record<string, { labelKey: string; unit: string; color: string }> = {
  hr_mean: { labelKey: "metrics.tab_hr", unit: "bpm", color: COLORS.risk },
  spo2: { labelKey: "metrics.tab_spo2", unit: "%", color: COLORS.good },
  rmssd: { labelKey: "metrics.tab_rmssd", unit: "ms", color: COLORS.attention },
  skin_temp: { labelKey: "metrics.tab_temp", unit: "°C", color: "#65558F" },
};

export const InteractiveMetrics: React.FC<InteractiveMetricsProps> = ({ series, lang }) => {
  const [activeParam, setActiveParam] = useState<string>("spo2");
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");

  const currentSeries = series.find((s) => s.param === activeParam) || series[0];
  const meta = PARAM_TABS[activeParam] || {
    labelKey: activeParam,
    unit: "",
    color: COLORS.text,
  };

  if (!currentSeries) return null;

  // Filter points according to timeRange
  const pointLimit = timeRange === "24h" ? 6 : timeRange === "3d" ? 18 : 42;
  const filteredPoints = currentSeries.points.slice(-pointLimit);

  const chartData = filteredPoints.map((p) => ({
    time: new Date(p.ts).toLocaleDateString([], {
      weekday: timeRange === "7d" ? "short" : undefined,
      hour: "2-digit",
      minute: "2-digit",
    }),
    value: p.value,
    rawTs: p.ts,
  }));

  return (
    <div className="metrics-interactive-section">
      <div className="metrics-header-row">
        <h3 className="section-title">{t("metrics.title", lang)}</h3>

        {/* Time Filter Buttons */}
        <div className="time-filter-group">
          {(["24h", "3d", "7d"] as TimeRange[]).map((range) => (
            <button
              key={range}
              type="button"
              className={`range-btn ${timeRange === range ? "active" : ""}`}
              onClick={() => setTimeRange(range)}
            >
              {t(`metrics.range_${range}`, lang)}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Tabs */}
      <div className="metric-tabs-row">
        {Object.entries(PARAM_TABS).map(([key, tab]) => {
          const isSelected = activeParam === key;
          const s = series.find((item) => item.param === key);
          const latestVal = s?.points[s.points.length - 1]?.value;

          return (
            <button
              key={key}
              type="button"
              className={`metric-tab-pill ${isSelected ? "active" : ""}`}
              onClick={() => setActiveParam(key)}
            >
              <span className="tab-pill-label">{t(tab.labelKey, lang)}</span>
              {latestVal !== undefined && (
                <span className="tab-pill-val">
                  {latestVal}
                  <span className="tab-pill-unit">{tab.unit}</span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Chart Canvas */}
      <div className="chart-canvas-container">
        <div className="chart-legend-row">
          <div className="legend-item">
            <span className="corridor-box" />
            <span>{t("metrics.baseline_corridor", lang)}</span>
            {currentSeries.baseline_low !== null && currentSeries.baseline_high !== null && (
              <strong style={{ marginLeft: "4px" }}>
                ({currentSeries.baseline_low} - {currentSeries.baseline_high} {meta.unit})
              </strong>
            )}
          </div>
          <div className="legend-item">
            <span className="line-indicator" style={{ backgroundColor: meta.color }} />
            <span>{t("metrics.reading", lang)}</span>
          </div>
        </div>

        <div style={{ width: "100%", height: 210 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                formatter={(val: unknown) => [`${val} ${meta.unit}`, t(meta.labelKey, lang)]}
              />
              {currentSeries.baseline_low !== null && currentSeries.baseline_high !== null && (
                <ReferenceArea
                  y1={currentSeries.baseline_low}
                  y2={currentSeries.baseline_high}
                  fill="#2E7D5B"
                  fillOpacity={0.12}
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke={meta.color}
                strokeWidth={3}
                dot={{ r: 2, fill: meta.color }}
                activeDot={{ r: 5 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
