import { useEffect, useState } from "react";

/** Wall-clock that re-renders the caller every `intervalMs` (countdowns, "x min ago"). */
export function useNow(intervalMs = 30000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);
  return now;
}
