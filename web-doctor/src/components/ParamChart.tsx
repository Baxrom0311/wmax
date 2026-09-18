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

interface ParamChartProps {
  series: ParamSeries;
}

const PARAM_LABELS: Record<string, { title: string; unit: string; color: string }> = {
  hr_mean: { title: "Yurak qisqarish soni (Puls)", unit: "bpm", color: "#ef4444" },
  spo2: { title: "Qon kislorod saturatsiyasi (SpO₂)", unit: "%", color: "#10b981" },
  skin_temp: { title: "Teri harorati (Harorat)", unit: "°C", color: "#f59e0b" },
  rmssd: { title: "Yurak ritmi variabilligi (RMSSD)", unit: "ms", color: "#38bdf8" },
  sdnn: { title: "Sinus ritmi variabilligi (SDNN)", unit: "ms", color: "#818cf8" },
  rr_est: { title: "Nafas harakatlari soni (RR)", unit: "/min", color: "#06b6d4" },
  steps: { title: "Kunlik harakat faolligi", unit: "qadam", color: "#34d399" },
  sleep_frag: { title: "Tungi uyqu uzilishi (Fragillik)", unit: "%", color: "#a855f7" },
};

export const ParamChart: React.FC<ParamChartProps> = ({ series }) => {
  const meta = PARAM_LABELS[series.param] || {
    title: series.param,
    unit: "",
    color: "#38bdf8",
  };

  const latestPoint =
    series.points && series.points.length > 0
      ? series.points[series.points.length - 1]
      : null;

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
    <div className="telemetry-card-official">
      <div className="telemetry-card-header">
        <div className="telemetry-title-block">
          <span className="telemetry-name">{meta.title}</span>
          {latestPoint && (
            <span className="telemetry-current-val">
              Oxirgi: <strong>{latestPoint.value} {meta.unit}</strong>
            </span>
          )}
        </div>

        <div className="telemetry-meta-block">
          {series.baseline_median !== null && (
            <span className="telemetry-norm-range">
              Normativ baza: <strong>{series.baseline_median}</strong> ({series.baseline_low} – {series.baseline_high} {meta.unit})
            </span>
          )}
          {hasDeviations && (
            <span className="telemetry-alert-tag">
              Klinik og'ish
            </span>
          )}
        </div>
      </div>

      <div style={{ width: "100%", height: 160 }}>
        <ResponsiveContainer>
          <LineChart data={formattedData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: "#64748b" }}
              interval="preserveStartEnd"
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#ffffff",
                border: "1px solid #cbd5e1",
                fontSize: "12px",
                borderRadius: "6px",
                color: "#0f172a",
                boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
              }}
              labelStyle={{ color: "#64748b", marginBottom: "4px" }}
              itemStyle={{ color: "#0284c7", fontWeight: "600" }}
              formatter={(val: unknown) => [`${val} ${meta.unit}`, meta.title]}
            />
            {series.baseline_low !== null && series.baseline_high !== null && (
              <ReferenceArea
                y1={series.baseline_low}
                y2={series.baseline_high}
                fill="#10b981"
                fillOpacity={0.12}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={hasDeviations ? "#ef4444" : meta.color}
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
