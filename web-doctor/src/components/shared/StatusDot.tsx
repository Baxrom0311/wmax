import React from "react";
import type { AlertLevel } from "../../lib/types";
import { cn } from "../../utils/cn";

interface StatusDotProps {
  level: AlertLevel;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  className?: string;
}

const LEVEL_COLORS: Record<AlertLevel, string> = {
  green: "bg-[var(--good)]",
  amber: "bg-[var(--attention)]",
  red: "bg-[var(--risk)]",
  no_data: "bg-[var(--nodata)]",
};

const SIZE_CLASSES = {
  sm: "w-2 h-2",
  md: "w-2.5 h-2.5",
  lg: "w-3 h-3",
};

export const StatusDot: React.FC<StatusDotProps> = ({
  level,
  size = "md",
  pulse = false,
  className,
}) => (
  <span
    className={cn(
      "inline-block rounded-full shrink-0",
      LEVEL_COLORS[level],
      SIZE_CLASSES[size],
      pulse && level === "red" && "pulse-dot-red",
      className
    )}
    aria-label={`Holat: ${level}`}
    role="img"
  />
);
