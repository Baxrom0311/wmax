import React, { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ParamSeries } from "../../lib/types";
import { COLORS } from "../../lib/types";
import { cn } from "../../utils/cn";

interface ParamChartProps {
  series: ParamSeries;
  lang?: "uz" | "ru";
}

const PARAM_META: Record<
  string,
  { title: string; title_ru: string; unit: string; color: string }
> = {
  hr_mean:    { title: "Puls (HR Mean)",            title_ru: "Пульс (HR Mean)",           unit: "bpm", color: COLORS.risk },
  spo2:       { title: "Kislorod to'yinishi (SpO₂)", title_ru: "Насыщение кислородом (SpO₂)", unit: "%",  color: COLORS.good },
  skin_temp:  { title: "Teri harorati",              title_ru: "Температура кожи",           unit: "°C", color: COLORS.attention },
  rmssd:      { title: "HRV (RMSSD)",               title_ru: "ВРС (RMSSD)",                unit: "ms", color: "#6B6861" },
  sdnn:       { title: "HRV (SDNN)",                title_ru: "ВРС (SDNN)",                 unit: "ms", color: "#9E9B93" },
  rr_est:     { title: "Nafas tezligi (RR)",         title_ru: "Частота дыхания (RR)",       unit: "/min", color: "#2563EB" },
  steps:      { title: "Qadamlar",                  title_ru: "Шаги",                       unit: "",   color: "#7C3AED" },
  sleep_frag: { title: "Uyqu uzilishi",             title_ru: "Фрагментация сна",           unit: "x/h", color: "#DB2777" },
};

// Format timestamp to readable string
function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString([], {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const CustomTooltip = ({
  active,
  payload,
  label,
  unit,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  unit: string;
}) => {
  if (!active || !payload || !payload[0]) return null;
  return (
    <div className="bg-[var(--surface)] border border-[var(--line)] rounded shadow-lg px-3 py-2 text-xs">
      <div className="text-[var(--text-muted)] mb-1">{label}</div>
      <div className="font-semibold text-[var(--text)]">
        {payload[0].value} {unit}
      </div>
    </div>
  );
};

export const ParamChart: React.FC<ParamChartProps> = ({ series, lang = "uz" }) => {
  const meta = PARAM_META[series.param] ?? {
    title: series.param,
    title_ru: series.param,
    unit: "",
    color: COLORS.text,
  };

  const displayTitle = lang === "ru" ? meta.title_ru : meta.title;
  const hasDeviations = series.deviated_ranges && series.deviated_ranges.length > 0;

  // Downsample for long series (keep last 288 points = 24h at 5-min intervals)
  const maxPoints = 288;
  const rawData = series.points.slice(-maxPoints);
  const step = rawData.length > 100 ? Math.ceil(rawData.length / 100) : 1;
  const data = rawData
    .filter((_, i) => i % step === 0)
    .map((p) => ({
      time: fmtTime(p.ts),
      value: p.value !== null ? Number(p.value.toFixed(1)) : null,
    }));

  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true);
      },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border border-[var(--line)] bg-[var(--surface)] p-4 transition-opacity duration-300",
        isVisible ? "opacity-100" : "opacity-0"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: meta.color }}
          />
          <span className="font-medium text-sm text-[var(--text)]">{displayTitle}</span>
        </div>
        <div className="flex items-center gap-2">
          {series.baseline_median !== null && (
            <span className="text-xs text-[var(--text-muted)]">
              Baza: {series.baseline_median} {meta.unit}
            </span>
          )}
          {hasDeviations && (
            <span className="text-xs font-semibold text-[var(--risk)] bg-[var(--risk-bg)] border border-[var(--risk-border)] px-2 py-0.5 rounded">
              ⚠ Og'ish
            </span>
          )}
        </div>
      </div>

      {data.length === 0 ? (
        <div className="h-36 flex items-center justify-center text-xs text-[var(--text-muted)]">
          Ma'lumot mavjud emas
        </div>
      ) : (
        <div style={{ height: 150, width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="var(--line)"
                opacity={0.5}
              />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                interval="preserveStartEnd"
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                tickLine={false}
                axisLine={false}
                width={36}
              />
              <Tooltip
                content={<CustomTooltip unit={meta.unit} />}
                cursor={{ stroke: "var(--line)", strokeWidth: 1 }}
              />

              {/* Baseline corridor (soyalangan zona) */}
              {series.baseline_low !== null && series.baseline_high !== null && (
                <ReferenceArea
                  y1={series.baseline_low}
                  y2={series.baseline_high}
                  fill={COLORS.line}
                  fillOpacity={0.35}
                  stroke="none"
                />
              )}

              {/* Baseline median reference line */}
              {series.baseline_median !== null && (
                <ReferenceLine
                  y={series.baseline_median}
                  stroke="var(--text-muted)"
                  strokeDasharray="4 2"
                  strokeWidth={1}
                  opacity={0.5}
                />
              )}

              <Line
                type="monotone"
                dataKey="value"
                stroke={hasDeviations ? COLORS.risk : meta.color}
                strokeWidth={hasDeviations ? 2.5 : 2}
                dot={false}
                isAnimationActive={isVisible}
                animationDuration={600}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Baseline range label */}
      {series.baseline_low !== null && series.baseline_high !== null && (
        <div className="mt-2 text-xs text-[var(--text-muted)] flex items-center gap-1.5">
          <span
            className="inline-block w-8 h-2 rounded"
            style={{ backgroundColor: COLORS.line, opacity: 0.5 }}
          />
          Shaxsiy me'yoriy koridor: {series.baseline_low} – {series.baseline_high} {meta.unit}
        </div>
      )}
    </div>
  );
};
