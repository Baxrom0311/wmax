import React from "react";
import { cn } from "../../utils/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          type={type}
          className={cn(
            "flex h-9 w-full rounded border border-[var(--line)] bg-[var(--surface)] px-3 py-1 text-sm text-[var(--text)] transition-colors placeholder:text-[var(--text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-[var(--risk)] focus-visible:ring-[var(--risk)]",
            className
          )}
          ref={ref}
          aria-invalid={error ? "true" : "false"}
          {...props}
        />
        {error && (
          <span className="text-xs text-[var(--risk)] mt-1 block font-medium">
            {error}
          </span>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
