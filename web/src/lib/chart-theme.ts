import { usePrefs } from "@/lib/prefs";

/** Recharts takes SVG presentation attributes, so chart chrome gets concrete colours per theme. */
export function useChartTheme() {
  const { theme } = usePrefs();
  const dark = theme === "dark";
  return {
    grid: dark ? "#1e293b" : "#e2e8f0",
    axis: dark ? "#334155" : "#cbd5e1",
    tick: dark ? "#94a3b8" : "#64748b",
    tooltipBg: dark ? "#0f172a" : "#ffffff",
    tooltipBorder: dark ? "#334155" : "#e2e8f0",
    tooltipText: dark ? "#e2e8f0" : "#0f172a",
    corridor: dark ? "#22c55e" : "#16a34a",
    deviation: "#e11d48",
  };
}
