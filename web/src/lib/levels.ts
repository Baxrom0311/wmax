import type { AlertLevel } from "./types";

export const LEVEL_VARIANT: Record<AlertLevel, "risk" | "attention" | "good" | "nodata"> = {
  red: "risk",
  amber: "attention",
  green: "good",
  no_data: "nodata",
};

export const LEVEL_DOT: Record<AlertLevel, string> = {
  red: "bg-risk",
  amber: "bg-attention",
  green: "bg-good",
  no_data: "bg-nodata",
};

export const LEVEL_PRIORITY: Record<AlertLevel, number> = { red: 0, no_data: 1, amber: 2, green: 3 };
