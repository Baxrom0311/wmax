import { AlertCircle, AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { LEVEL_DOT, LEVEL_VARIANT } from "@/lib/levels";
import type { AlertLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

const ICONS = { red: AlertCircle, amber: AlertTriangle, green: CheckCircle2, no_data: HelpCircle };

export function LevelBadge({ level, label, className }: { level: AlertLevel; label: string; className?: string }) {
  const Icon = ICONS[level];
  return (
    <Badge variant={LEVEL_VARIANT[level]} className={cn("gap-1", className)}>
      <Icon />
      {label}
    </Badge>
  );
}

export function LevelDot({ level, pulse, className }: { level: AlertLevel; pulse?: boolean; className?: string }) {
  return (
    <span className={cn("relative inline-flex size-2.5 shrink-0", className)} aria-hidden="true">
      {pulse && <span className={cn("absolute inline-flex size-full animate-ping rounded-full opacity-60", LEVEL_DOT[level])} />}
      <span className={cn("relative inline-flex size-2.5 rounded-full", LEVEL_DOT[level])} />
    </span>
  );
}
