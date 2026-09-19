import React, { useEffect, useState } from "react";
import { Siren, ArrowRight } from "lucide-react";
import { fetchActiveSos } from "../lib/api";
import type { SosEventItem } from "../lib/types";

interface SosBannerProps {
  onOpenDispatcher: () => void;
  isDemo?: boolean;
}

export const SosBanner: React.FC<SosBannerProps> = ({ onOpenDispatcher, isDemo }) => {
  const [activeEvents, setActiveEvents] = useState<SosEventItem[]>([]);

  useEffect(() => {
    let isMounted = true;

    const checkSos = async () => {
      try {
        const events = await fetchActiveSos(isDemo);
        if (isMounted) {
          // Filter raised or uncompleted events
          const unresolved = events.filter(
            (e) => e.status === "raised" || e.status === "acknowledged" || e.status === "dispatched_103"
          );
          setActiveEvents(unresolved);
        }
      } catch {
        // Silent failure in background polling
      }
    };

    checkSos();
    const timer = setInterval(checkSos, 5000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, [isDemo]);

  if (activeEvents.length === 0) return null;

  const raisedCount = activeEvents.filter((e) => e.status === "raised").length;

  return (
    <div className="sos-global-top-banner" role="alert">
      <div className="sos-banner-left">
        <div className="sos-banner-pulse-dot" aria-hidden="true" />
        <div className="sos-banner-content">
          <div className="sos-banner-title">
            <Siren size={16} color="#fee2e2" />
            <span className="sos-title-text">
              SHOSHILINCH SOS: {activeEvents.length} ta faol favqulodda holat!
            </span>
            {raisedCount > 0 && (
              <span className="sos-raised-tag">{raisedCount} ta yangi</span>
            )}
          </div>
          <span className="sos-banner-sub">
            Bemor zudlik bilan tibbiy yordam va 103 dispetcherlik aralashuvini talab qiladi.
          </span>
        </div>
      </div>
      <button
        type="button"
        className="btn-open-sos-dispatcher"
        onClick={onOpenDispatcher}
      >
        <span>Dispetcherni ochish</span>
        <ArrowRight size={14} />
      </button>
    </div>
  );
};
