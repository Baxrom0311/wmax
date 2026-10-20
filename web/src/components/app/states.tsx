import type React from "react";
import { AlertTriangle, FlaskConical, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed px-6 py-14 text-center", className)}>
      <span className="bg-muted text-muted-foreground flex size-12 items-center justify-center rounded-full">
        <Icon className="size-6" />
      </span>
      <div className="space-y-1">
        <p className="font-display font-semibold">{title}</p>
        {description && <p className="text-muted-foreground mx-auto max-w-md text-sm">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  title,
  description,
  onRetry,
  retryLabel,
  extra,
}: {
  title: string;
  description?: string;
  onRetry?: () => void;
  retryLabel: string;
  extra?: React.ReactNode;
}) {
  return (
    <div className="border-risk/30 bg-risk-soft/40 flex flex-col items-center gap-3 rounded-xl border px-6 py-12 text-center">
      <span className="bg-risk-soft text-risk flex size-12 items-center justify-center rounded-full">
        <AlertTriangle className="size-6" />
      </span>
      <div className="space-y-1">
        <p className="font-display font-semibold">{title}</p>
        {description && <p className="text-muted-foreground mx-auto max-w-md text-sm">{description}</p>}
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <RefreshCw />
            {retryLabel}
          </Button>
        )}
        {extra}
      </div>
    </div>
  );
}

export function LoadingState({ label, className }: { label: string; className?: string }) {
  return (
    <div className={cn("text-muted-foreground flex items-center justify-center gap-2 py-16 text-sm", className)}>
      <Loader2 className="size-4 animate-spin" />
      {label}
    </div>
  );
}

export function DemoBanner({ title, text, actionLabel, onExit }: { title: string; text: string; actionLabel: string; onExit: () => void }) {
  return (
    <div className="bg-attention text-white">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2 text-xs sm:text-sm">
        <FlaskConical className="size-4 shrink-0" />
        <p className="min-w-0 flex-1">
          <strong className="font-semibold">{title}.</strong> <span className="opacity-90">{text}</span>
        </p>
        <Button size="sm" variant="secondary" className="h-7 shrink-0 bg-white/20 text-white hover:bg-white/30" onClick={onExit}>
          {actionLabel}
        </Button>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="min-w-0 space-y-1">
        <h1 className="font-display text-2xl font-bold tracking-tight">{title}</h1>
        {description && <p className="text-muted-foreground text-sm">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
