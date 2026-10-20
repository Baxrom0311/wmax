import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LOCALE, pick, type Lang } from "@/i18n";
import { t } from "@/i18n/clinic";
import { useChartTheme } from "@/lib/chart-theme";
import { paramMeta } from "@/lib/params";
import type { ParamSeries } from "@/lib/types";
import { cn } from "@/lib/utils";

type Range = "24h" | "3d" | "7d" | "all";

export function ParamChart({ series, lang }: { series: ParamSeries; lang: Lang }) {
  const [range, setRange] = useState<Range>("7d");
  const theme = useChartTheme();
  const meta = paramMeta(series.param);
  const points = useMemo(() => series.points ?? [], [series.points]);
  const latest = [...points].reverse().find((p) => p.value !== null) ?? null;
  const hasDeviations = (series.deviated_ranges ?? []).length > 0;

  const data = useMemo(() => {
    let subset = points;
    if (range !== "all" && points.length > 0) {
      const end = new Date(points[points.length - 1].ts).getTime();
      const hours = range === "24h" ? 24 : range === "3d" ? 72 : 168;
      const inRange = points.filter((p) => new Date(p.ts).getTime() >= end - hours * 3600 * 1000);
      subset = inRange.length >= 2 ? inRange : points.slice(-Math.min(points.length, 24));
    }
    return subset.map((p) => {
      const d = new Date(p.ts);
      const time = d.toLocaleTimeString(LOCALE[lang], { hour: "2-digit", minute: "2-digit" });
      const date = d.toLocaleDateString(LOCALE[lang], { day: "numeric", month: "numeric" });
      return { label: range === "24h" ? time : `${date} ${time}`, value: p.value };
    });
  }, [points, range, lang]);

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="gap-1 px-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-sm">{meta.title[lang]}</CardTitle>
            <p className="text-muted-foreground text-xs">
              {latest ? (
                <>
                  {pick(lang, { uz: "Oxirgi", ru: "Последнее", en: "Latest" })}:{" "}
                  <span className="text-foreground tabular font-semibold">
                    {latest.value} {meta.unit}
                  </span>
                </>
              ) : (
                pick(lang, { uz: "O'lchov yo'q", ru: "Нет измерений", en: "No readings" })
              )}
              {series.baseline_median !== null && (
                <>
                  {" · "}
                  {pick(lang, { uz: "Shaxsiy me'yor", ru: "Личная норма", en: "Baseline" })}{" "}
                  <span className="tabular">
                    {series.baseline_low}–{series.baseline_high}
                  </span>
                </>
              )}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {hasDeviations && <Badge variant="risk">{pick(lang, { uz: "Og'ish", ru: "Отклонение", en: "Deviation" })}</Badge>}
            <div className="bg-muted flex rounded-md p-0.5">
              {(["24h", "3d", "7d", "all"] as Range[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRange(r)}
                  className={cn(
                    "rounded px-2 py-0.5 text-[11px] font-medium cursor-pointer",
                    range === r ? "bg-background shadow-xs" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {r === "all" ? t("detail.all_points", lang) : t(`detail.range_${r}`, lang)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-2">
        {data.length === 0 ? (
          <div className="text-muted-foreground flex h-44 items-center justify-center text-sm">
            {pick(lang, { uz: "Bu davr uchun ma'lumot yo'q", ru: "Нет данных за период", en: "No data for this period" })}
          </div>
        ) : (
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 6, right: 12, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.grid} />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: theme.tick }} interval="preserveStartEnd" tickLine={false} axisLine={{ stroke: theme.axis }} minTickGap={24} />
                <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: theme.tick }} tickLine={false} axisLine={false} width={44} />
                <Tooltip
                  contentStyle={{
                    background: theme.tooltipBg,
                    border: `1px solid ${theme.tooltipBorder}`,
                    borderRadius: 8,
                    fontSize: 12,
                    color: theme.tooltipText,
                  }}
                  labelStyle={{ color: theme.tick }}
                  formatter={(val: unknown) => {
                    const v = Number(val);
                    let delta = "";
                    if (series.baseline_median !== null && series.baseline_median !== undefined) {
                      const diff = v - series.baseline_median;
                      delta = ` (Δ ${diff > 0 ? "+" : ""}${diff.toFixed(1)})`;
                    }
                    return [`${val} ${meta.unit}${delta}`, meta.title[lang]];
                  }}
                />
                {series.baseline_low !== null && series.baseline_high !== null && (
                  <ReferenceArea y1={series.baseline_low} y2={series.baseline_high} fill={theme.corridor} fillOpacity={0.12} />
                )}
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={hasDeviations ? theme.deviation : meta.color}
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
