import React, { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { cn } from "../../utils/cn";

interface CountdownTimerProps {
  dueAt: string;
  className?: string;
}

function getTimeLeft(dueAt: string) {
  const diffMs = new Date(dueAt).getTime() - Date.now();
  if (diffMs <= 0) return { hours: 0, minutes: 0, expired: true };
  const hours = Math.floor(diffMs / (3600 * 1000));
  const minutes = Math.floor((diffMs % (3600 * 1000)) / (60 * 1000));
  return { hours, minutes, expired: false };
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({ dueAt, className }) => {
  const [timeLeft, setTimeLeft] = useState(() => getTimeLeft(dueAt));

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(getTimeLeft(dueAt));
    }, 30_000); // update every 30 seconds
    return () => clearInterval(interval);
  }, [dueAt]);

  const isCritical = !timeLeft.expired && timeLeft.hours < 4;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-sm font-mono font-semibold",
        timeLeft.expired ? "text-[var(--risk)]" : isCritical ? "text-[var(--attention)]" : "text-[var(--text)]",
        className
      )}
      aria-live="polite"
      aria-label={
        timeLeft.expired
          ? "Muddati o'tgan"
          : `${timeLeft.hours} soat ${timeLeft.minutes} daqiqa qoldi`
      }
    >
      <Clock className="w-4 h-4 shrink-0" />
      {timeLeft.expired
        ? "Muddati o'tgan!"
        : `${timeLeft.hours}s ${timeLeft.minutes.toString().padStart(2, "0")}d qoldi`}
    </span>
  );
};
