import React from "react";
import { cn } from "../../utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "good" | "attention" | "risk" | "nodata";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "bg-[var(--primary)] text-[var(--primary-foreground)]",
    secondary: "bg-[var(--secondary)] text-[var(--secondary-foreground)]",
    outline: "border border-[var(--line)] text-[var(--text)] bg-transparent",
    good: "bg-[var(--good-bg)] text-[var(--good)] border border-[var(--good-border)]",
    attention: "bg-[var(--attention-bg)] text-[var(--attention)] border border-[var(--attention-border)]",
    risk: "bg-[var(--risk-bg)] text-[var(--risk)] border border-[var(--risk-border)] font-semibold",
    nodata: "bg-[var(--nodata-bg)] text-[var(--nodata)] border border-[var(--nodata-border)]",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium leading-none tracking-tight shrink-0",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
