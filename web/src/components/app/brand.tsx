import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm",
        className,
      )}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="2 12 6 12 9 4 14 20 17 12 22 12" />
      </svg>
    </span>
  );
}

export function Brand({ subtitle, className }: { subtitle?: string; className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <BrandMark />
      <span className="flex flex-col leading-tight">
        <span className="font-display text-base font-extrabold tracking-tight">WMAX</span>
        {subtitle && <span className="text-muted-foreground text-xs">{subtitle}</span>}
      </span>
    </span>
  );
}
