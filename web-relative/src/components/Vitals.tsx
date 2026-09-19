import React from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { cn } from "../lib/utils";
import {
  Heart,
  Wind,
  Thermometer,
  Droplets,
  Moon,
  Footprints,
  Activity,
  ChevronUp,
  ChevronDown,
} from "lucide-react";

interface VitalsProps {
  vitals?: {
    hr: number | null;
    spo2: number | null;
    sleep_hours: number | null;
    skin_temp?: number | null;
    rr?: number | null;
    steps?: number | null;
  };
  lang: Lang;
}

type VitalStatus = "good" | "attention" | "risk" | "nodata";

const STATUS_STYLES: Record<VitalStatus, {
  card: string;
  badge: string;
  value: string;
}> = {
  good: {
    card: "border-slate-100 bg-white hover:border-blue-200 hover:shadow-md",
    badge: "bg-green-50 text-green-700 border border-green-200",
    value: "text-slate-900",
  },
  attention: {
    card: "border-amber-200 bg-amber-50/30 hover:shadow-md",
    badge: "bg-amber-50 text-amber-700 border border-amber-200",
    value: "text-amber-900",
  },
  risk: {
    card: "border-red-200 bg-red-50/20 hover:shadow-md",
    badge: "bg-red-50 text-red-700 border border-red-200",
    value: "text-red-900",
  },
  nodata: {
    card: "border-slate-100 bg-slate-50 hover:border-slate-200",
    badge: "bg-slate-100 text-slate-500 border border-slate-200",
    value: "text-slate-400",
  },
};

export const Vitals: React.FC<VitalsProps> = ({ vitals, lang }) => {
  if (!vitals) return null;

  const hr = vitals.hr;
  const spo2 = vitals.spo2;
  const temp = vitals.skin_temp ?? null;
  const rr = vitals.rr ?? null;
  const sleep = vitals.sleep_hours;
  const steps = vitals.steps ?? null;

  const getHrStatus = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v > 100 || v < 50) return "risk";
    if (v > 85 || v < 58) return "attention";
    return "good";
  };
  const getSpo2Status = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v < 90) return "risk";
    if (v < 95) return "attention";
    return "good";
  };
  const getTempStatus = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v > 37.8 || v < 35.5) return "risk";
    if (v > 37.2) return "attention";
    return "good";
  };
  const getRrStatus = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v > 24 || v < 10) return "risk";
    if (v > 20 || v < 12) return "attention";
    return "good";
  };
  const getSleepStatus = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v < 4) return "risk";
    if (v < 6) return "attention";
    return "good";
  };
  const getStepsStatus = (v: number | null): VitalStatus => {
    if (v === null) return "nodata";
    if (v < 500) return "risk";
    if (v < 2500) return "attention";
    return "good";
  };

  const statusLabel = (st: VitalStatus) => {
    if (st === "good") return t("vitals.normal", lang);
    if (st === "attention") return t("vitals.attention", lang);
    if (st === "risk") return t("vitals.risk", lang);
    return "—";
  };

  const haptic = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const tg = (window as any).Telegram?.WebApp?.HapticFeedback;
    if (tg) tg.selectionChanged();
  };

  const formatVal = (v: number | null, decimals = 0) =>
    v !== null && v !== undefined ? (decimals > 0 ? v.toFixed(decimals) : String(v)) : "—";

  type CardDef = {
    key: string;
    icon: React.ReactNode;
    label: string;
    status: VitalStatus;
    value: string;
    unit: string;
    norm: string;
    trend?: "up" | "down";
  };

  const hrStatus = getHrStatus(hr);
  const spo2Status = getSpo2Status(spo2);
  const tempStatus = getTempStatus(temp);
  const rrStatus = getRrStatus(rr);
  const sleepStatus = getSleepStatus(sleep);
  const stepsStatus = getStepsStatus(steps);

  const cards: CardDef[] = [
    {
      key: "hr",
      icon: <Heart size={18} className="text-rose-500" />,
      label: t("vitals.hr", lang),
      status: hrStatus,
      value: formatVal(hr),
      unit: t("vitals.bpm", lang),
      norm: `${t("vitals.norm_prefix", lang)} ${t("vitals.norm_hr", lang)}`,
      trend: hrStatus !== "good" && hr !== null ? (hr > 85 ? "up" : "down") : undefined,
    },
    {
      key: "spo2",
      icon: <Droplets size={18} className="text-blue-500" />,
      label: t("vitals.spo2", lang),
      status: spo2Status,
      value: formatVal(spo2),
      unit: "%",
      norm: `${t("vitals.norm_prefix", lang)} ${t("vitals.norm_spo2", lang)}`,
      trend: spo2Status !== "good" && spo2 !== null ? "down" : undefined,
    },
    {
      key: "temp",
      icon: <Thermometer size={18} className="text-orange-500" />,
      label: t("vitals.temp", lang),
      status: tempStatus,
      value: formatVal(temp, 1),
      unit: "°C",
      norm: `${t("vitals.norm_prefix", lang)} ${t("vitals.norm_temp", lang)}`,
      trend: tempStatus !== "good" && temp !== null ? (temp > 37.2 ? "up" : "down") : undefined,
    },
    {
      key: "rr",
      icon: <Wind size={18} className="text-sky-500" />,
      label: t("vitals.rr", lang),
      status: rrStatus,
      value: formatVal(rr),
      unit: t("vitals.breaths", lang),
      norm: `${t("vitals.norm_prefix", lang)} ${t("vitals.norm_rr", lang)}`,
      trend: rrStatus !== "good" && rr !== null ? (rr > 20 ? "up" : "down") : undefined,
    },
    {
      key: "sleep",
      icon: <Moon size={18} className="text-indigo-500" />,
      label: t("vitals.sleep", lang),
      status: sleepStatus,
      value: formatVal(sleep, 1),
      unit: t("vitals.hours", lang),
      norm: `${t("vitals.norm_prefix", lang)} ${t("vitals.norm_sleep", lang)}`,
      trend: sleepStatus !== "good" && sleep !== null ? "down" : undefined,
    },
    {
      key: "steps",
      icon: <Footprints size={18} className="text-teal-500" />,
      label: t("vitals.steps", lang),
      status: stepsStatus,
      value: steps !== null ? steps.toLocaleString() : "—",
      unit: t("vitals.steps_unit", lang),
      norm: t("vitals.steps_target", lang),
      trend: stepsStatus !== "good" && steps !== null ? "down" : undefined,
    },
  ];

  return (
    <section className="px-4 pb-4 flex flex-col gap-3 animate-fade-up">
      {/* Section header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-blue-600" />
          <h3 className="text-[14px] font-bold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
            {t("vitals.title", lang)}
          </h3>
        </div>
        <div className="flex items-center gap-1.5 bg-green-50 border border-green-200 text-green-700 text-[10.5px] font-extrabold px-2.5 py-1 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 dot-live" />
          LIVE
        </div>
      </div>

      {/* Grid 2-col */}
      <div className="grid grid-cols-2 gap-3">
        {cards.map((c) => {
          const s = STATUS_STYLES[c.status];
          return (
            <div
              key={c.key}
              className={cn(
                "rounded-2xl border p-4 flex flex-col gap-1.5 cursor-pointer transition-all duration-200 select-none",
                s.card
              )}
              onClick={haptic}
            >
              {/* Top row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {c.icon}
                  <span className="text-[12px] font-semibold text-slate-600 leading-tight">
                    {c.label}
                  </span>
                </div>
                <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full", s.badge)}>
                  {statusLabel(c.status)}
                </span>
              </div>

              {/* Value row */}
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className={cn("text-[30px] font-extrabold leading-none", s.value)}
                  style={{ fontFamily: "'Outfit',sans-serif" }}>
                  {c.value}
                </span>
                <span className="text-[12px] font-semibold text-slate-400">{c.unit}</span>
                {c.trend === "up" && <ChevronUp size={16} className="text-amber-500 ml-auto" />}
                {c.trend === "down" && <ChevronDown size={16} className="text-blue-400 ml-auto" />}
              </div>

              {/* Norm note */}
              <div className="text-[10.5px] text-slate-400 border-t border-slate-100 pt-1.5 mt-0.5">
                {c.norm}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
