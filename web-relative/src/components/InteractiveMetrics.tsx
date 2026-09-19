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
import { cn } from "../lib/utils";
import { Activity } from "lucide-react";

interface InteractiveMetricsProps {
  series: ParamSeries[];
  lang: Lang;
}

type TimeRange = "24h" | "3d" | "7d";

const PARAM_TABS: Record<string, { labelKey: string; unit: string; color: string; altParam?: string }> = {
  hr_mean: { labelKey: "metrics.tab_hr", unit: "bpm", color: COLORS.risk },
  spo2: { labelKey: "metrics.tab_spo2", unit: "%", color: COLORS.good },
  rmssd: { labelKey: "metrics.tab_rmssd", unit: "ms", color: COLORS.attention },
  skin_temp: { labelKey: "metrics.tab_temp", unit: "°C", color: "#65558F" },
  rr_est: { labelKey: "metrics.tab_rr", unit: "/daq", color: "#0284c7", altParam: "rr" },
  sleep_frag: { labelKey: "metrics.tab_sleep", unit: "soat", color: "#7c3aed", altParam: "sleep_hours" },
  steps: { labelKey: "metrics.tab_steps", unit: "qadam", color: "#16a34a" },
};

// O'zbekcha qisqa kun nomlari
const UZ_DAYS_SHORT: Record<number, string> = {
  0: "Yak", 1: "Du", 2: "Se", 3: "Cho", 4: "Pa", 5: "Ju", 6: "Sha",
};

const RU_DAYS_SHORT: Record<number, string> = {
  0: "Вс", 1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб",
};

const EN_DAYS_SHORT: Record<number, string> = {
  0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat",
};

export const InteractiveMetrics: React.FC<InteractiveMetricsProps> = ({ series, lang }) => {
  const [activeParam, setActiveParam] = useState<string>("spo2");
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");

  const currentSeries =
    series.find(
      (s) =>
        s.param === activeParam ||
        (PARAM_TABS[activeParam]?.altParam && s.param === PARAM_TABS[activeParam].altParam)
    ) || series[0];

  const meta = PARAM_TABS[activeParam] || {
    labelKey: activeParam,
    unit: "",
    color: COLORS.text,
  };

  if (!currentSeries) return null;

  // Filter points according to timeRange
  const pointLimit = timeRange === "24h" ? 6 : timeRange === "3d" ? 18 : 42;
  const filteredPoints = currentSeries.points.slice(-pointLimit);

  const daysMap = lang === "uz" ? UZ_DAYS_SHORT : lang === "ru" ? RU_DAYS_SHORT : EN_DAYS_SHORT;

  const chartData = filteredPoints.map((p) => {
    const d = new Date(p.ts);
    const dayLabel = daysMap[d.getDay()] || "";
    const timeLabel = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    return {
      time: timeRange === "7d" ? `${dayLabel} ${timeLabel}` : timeLabel,
      value: p.value,
      rawTs: p.ts,
    };
  });

  // Haptic for Telegram
  const haptic = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const tg = (window as any).Telegram?.WebApp?.HapticFeedback;
    if (tg) tg.selectionChanged();
  };

  // Only render tabs that have available series data
  const availableTabs = Object.entries(PARAM_TABS).filter(([key, tab]) =>
    series.some((s) => s.param === key || (tab.altParam && s.param === tab.altParam))
  );

  return (
    <div className="px-4 pb-4 flex flex-col gap-3 animate-fade-up">
      {/* Header Row */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-blue-600" />
          <h3
            className="text-[14px] font-bold text-slate-800"
            style={{ fontFamily: "'Outfit',sans-serif" }}
          >
            {t("metrics.title", lang)}
          </h3>
        </div>

        {/* Time Filter — iOS Segment Control style */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/60">
          {(["24h", "3d", "7d"] as TimeRange[]).map((range) => (
            <button
              key={range}
              type="button"
              className={cn(
                "px-2.5 py-1 text-[11px] font-bold rounded-lg transition-all cursor-pointer",
                timeRange === range
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
              onClick={() => {
                setTimeRange(range);
                haptic();
              }}
            >
              {t(`metrics.range_${range}`, lang)}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Tabs — horizontal scrollable pills */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide py-1">
        {availableTabs.map(([key, tab]) => {
          const isSelected = activeParam === key;
          const s = series.find(
            (item) => item.param === key || (tab.altParam && item.param === tab.altParam)
          );
          const latestVal = s?.points[s.points.length - 1]?.value;

          return (
            <button
              key={key}
              type="button"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[12px] font-bold whitespace-nowrap transition-all cursor-pointer flex-shrink-0",
                isSelected
                  ? "bg-blue-50 border-blue-300 text-blue-700 shadow-xs"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
              onClick={() => {
                setActiveParam(key);
                haptic();
              }}
            >
              <span>{t(tab.labelKey, lang)}</span>
              {latestVal !== undefined && latestVal !== null && (
                <span className="text-[11px] font-extrabold opacity-85">
                  {typeof latestVal === "number" ? latestVal.toFixed(1) : latestVal}
                  <span className="text-[10px] font-normal"> {tab.unit}</span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Chart Canvas Card */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-3.5 flex flex-col gap-3">
        <div className="flex items-center justify-between text-[11px] text-slate-500 flex-wrap gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-600/20 border border-emerald-500/40 inline-block" />
            <span>{t("metrics.baseline_corridor", lang)}</span>
            {currentSeries.baseline_low !== null && currentSeries.baseline_high !== null && (
              <strong className="text-slate-700 ml-1">
                ({currentSeries.baseline_low} - {currentSeries.baseline_high} {meta.unit})
              </strong>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 rounded-full inline-block" style={{ backgroundColor: meta.color }} />
            <span>{t("metrics.reading", lang)}</span>
          </div>
        </div>

        <div style={{ width: "100%", height: 210 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.line} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: COLORS.nodata }}
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
                  borderRadius: "8px",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
                  padding: "8px 12px",
                }}
                formatter={(val: unknown) => {
                  const v = Number(val);
                  const bm = currentSeries.baseline_median;
                  let diffStr = "";
                  if (bm !== null && bm !== undefined) {
                    const diff = v - bm;
                    const arrow = diff > 0 ? "↑" : diff < 0 ? "↓" : "=";
                    diffStr = ` (${arrow}${Math.abs(diff).toFixed(1)})`;
                  }
                  return [`${v} ${meta.unit}${diffStr}`, t(meta.labelKey, lang)];
                }}
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
                activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
                isAnimationActive={true}
                animationDuration={600}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
