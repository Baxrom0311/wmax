import React from "react";
import { cn } from "../../utils/cn";

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className }) => (
  <div
    className={cn("rounded skeleton-shimmer", className)}
    aria-hidden="true"
  />
);

export const SkeletonRow: React.FC<{ cols?: number }> = ({ cols = 6 }) => (
  <tr className="border-b border-[var(--line)]">
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="px-4 py-3">
        <Skeleton className="h-4 w-full" />
      </td>
    ))}
  </tr>
);

export const SkeletonCard: React.FC = () => (
  <div className="rounded-lg border border-[var(--line)] bg-[var(--surface)] p-4 space-y-3">
    <Skeleton className="h-5 w-2/3" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
    <div className="flex gap-2 pt-1">
      <Skeleton className="h-6 w-16" />
      <Skeleton className="h-6 w-20" />
    </div>
  </div>
);
