import React, { useCallback, useEffect, useState } from "react";
import {
  Siren,
  RefreshCw,
  ArrowLeft,
  X,
  AlertTriangle,
  CheckCircle2,
  MapPin,
  Droplets,
  AlertCircle,
  Clock,
  Send,
  Watch,
  Cpu,
  Check,
  Zap,
  Target,
  DoorOpen,
  Globe,
  ExternalLink,
  Pill,
} from "lucide-react";
import { acknowledgeSos, dispatchSos103, fetchActiveSos, resolveSos } from "../lib/api";
import type { SosEventItem } from "../lib/types";
import { t, type Lang } from "../i18n";

interface SosDispatcherProps {
  onClose: () => void;
  isDemo?: boolean;
  lang?: Lang;
}

export const SosDispatcher: React.FC<SosDispatcherProps> = ({ onClose, isDemo, lang = "uz" }) => {
  const [events, setEvents] = useState<SosEventItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<string, string>>({});
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Stable across selection changes so the poll interval is not torn down on
  // every click, and only the first load shows the spinner.
  const loadSos = useCallback(async () => {
    try {
      const data = await fetchActiveSos(isDemo);
      setEvents(data);
      setSelectedEventId((current) => current ?? (data.length > 0 ? data[0].id : null));
    } catch (e: any) {
      setActionError(e?.message || "SOS ma'lumotlarini yuklashda xatolik");
    } finally {
      setLoading(false);
    }
  }, [isDemo]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- dispatcher hydrates from the SOS endpoint on mount
    loadSos();
    const interval = setInterval(loadSos, 6000);
    return () => clearInterval(interval);
  }, [loadSos]);

  const activeEvent = events.find((e) => e.id === selectedEventId) || events[0];

  const handleAcknowledge = async (sosId: string) => {
    try {
      setActionInProgress(sosId);
      await acknowledgeSos(sosId, isDemo);
      await loadSos();
    } catch (e: any) {
      setActionError(e?.message || "Qabul qilishda xatolik");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDispatch103 = async (sosId: string) => {
    try {
      setActionInProgress(sosId);
      await dispatchSos103(sosId, { dispatch_method: "manual_call_103" }, isDemo);
      await loadSos();
    } catch (e: any) {
      setActionError(e?.message || "103 ga jo'natishda xatolik");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleResolve = async (sosId: string) => {
    const note = resolutionNotes[sosId] || t("sos.default_resolution", lang);
    try {
      setActionInProgress(sosId);
      await resolveSos(sosId, note, isDemo);
      await loadSos();
    } catch (e: any) {
      setActionError(e?.message || "SOS yakunlashda xatolik");
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="sos-dispatcher-screen">
      <div className="sos-dispatcher-header">
        <div className="dispatcher-title-area">
          <div className="sos-header-icon"><Siren size={26} color="#ef4444" /></div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 3 }}>
              <h2 style={{ margin: 0 }}>{t("sos.title", lang)}</h2>
              <span className="dispatcher-badge-live">LIVE 103</span>
            </div>
            <p>{t("sos.subtitle", lang)}</p>
          </div>
        </div>
        <div className="dispatcher-actions">
          <button type="button" className="btn-refresh-sos" onClick={loadSos}>
            <RefreshCw size={14} style={{ marginRight: 6 }} />
            <span>{t("sos.refresh", lang)}</span>
          </button>
          <button type="button" className="btn-close-dispatcher" onClick={onClose}>
            <ArrowLeft size={14} style={{ marginRight: 6 }} />
            <span>{t("sos.back", lang)}</span>
          </button>
        </div>
      </div>

      {actionError && (
        <div className="dispatcher-error-bar">
          <AlertTriangle size={16} />
          <span>{actionError}</span>
          <button type="button" onClick={() => setActionError(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {loading && events.length === 0 ? (
        <div className="dispatcher-loading">{t("app.loading", lang)}</div>
      ) : events.length === 0 ? (
        <div className="dispatcher-empty-card">
          <span className="empty-check-icon"><CheckCircle2 size={40} color="#16a34a" /></span>
          <h3>{t("sos.no_active", lang)}</h3>
          <p>{t("sos.all_stable", lang)}</p>
        </div>
      ) : (
        <div className="dispatcher-main-grid">
          {/* List of active events */}
          <div className="dispatcher-events-list">
            <h3>{t("sos.queue", lang, { n: events.length })}</h3>
            {events.map((evt) => {
              const isSelected = evt.id === activeEvent?.id;
              const addr = evt.address_snapshot || {};
              return (
                <div
                  key={evt.id}
                  className={`sos-event-item-card ${isSelected ? "selected" : ""} status-${evt.status}`}
                  onClick={() => setSelectedEventId(evt.id)}
                >
                  <div className="event-item-top">
                    <span className="event-item-name">{evt.patient_name || "Bemor"}</span>
                    <span className={`event-status-pill ${evt.status}`}>
                      {evt.status === "raised"
                        ? t("sos.status_raised", lang)
                        : evt.status === "acknowledged"
                        ? t("sos.status_ack", lang)
                        : evt.status === "dispatched_103"
                        ? t("sos.status_dispatched", lang)
                        : evt.status}
                    </span>
                  </div>
                  <div className="event-item-address">
                    <MapPin size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                    <span>{addr.street || addr.district || "Manzil"}, {addr.landmark || ""}</span>
                  </div>
                  <div className="event-item-meta">
                    <span>Manba: {evt.source === "watch_button" ? t("sos.source_watch", lang) : t("sos.source_auto", lang)}</span>
                    <span>{new Date(evt.raised_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detailed view of selected event */}
          {activeEvent && (
            <div className="dispatcher-event-detail">
              <div className="detail-top-card">
                <div className="detail-patient-identity">
                  <div className="detail-name-row">
                    <h3>{activeEvent.patient_name || "Bemor"}</h3>
                    <span className="detail-tag-blood">
                      <Droplets size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                      <span>{t("sos.blood_group", lang)} {activeEvent.clinical_snapshot?.blood_group || t("sos.unknown", lang)}{" "}
                      {activeEvent.clinical_snapshot?.rh ? `(${activeEvent.clinical_snapshot.rh})` : ""}</span>
                    </span>
                    <span className={`detail-tag-status status-${activeEvent.status}`}>
                      {activeEvent.status === "raised" ? (
                        <>
                          <AlertCircle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                          <span>{t("sos.status_raised", lang)}</span>
                        </>
                      ) : activeEvent.status === "acknowledged" ? (
                        <>
                          <Clock size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                          <span>{t("sos.status_ack", lang)}</span>
                        </>
                      ) : (
                        <>
                          <Send size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                          <span>{t("sos.status_dispatched", lang)}</span>
                        </>
                      )}
                    </span>
                    <span className="detail-tag-source">
                      {activeEvent.source === "watch_button" ? (
                        <>
                          <Watch size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                          <span>{t("sos.source_watch", lang)}</span>
                        </>
                      ) : (
                        <>
                          <Cpu size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                          <span>{t("sos.source_auto", lang)}</span>
                        </>
                      )}
                    </span>
                  </div>
                  {activeEvent.clinical_snapshot?.primary_diagnosis && (
                    <p className="detail-patient-diagnosis">
                      <strong>{t("sos.diagnosis_label", lang)}</strong> {activeEvent.clinical_snapshot.primary_diagnosis}
                    </p>
                  )}
                </div>

                {/* Dispatch action buttons */}
                <div className="detail-action-buttons">
                  {activeEvent.status === "raised" && (
                    <button
                      type="button"
                      className="btn-ack-sos"
                      disabled={actionInProgress === activeEvent.id}
                      onClick={() => handleAcknowledge(activeEvent.id)}
                    >
                      <Check size={14} style={{ marginRight: 6 }} />
                      <span>{t("sos.btn_ack", lang)}</span>
                    </button>
                  )}

                  <button
                    type="button"
                    className="btn-dispatch-103"
                    disabled={actionInProgress === activeEvent.id}
                    onClick={() => handleDispatch103(activeEvent.id)}
                  >
                    <Send size={14} style={{ marginRight: 6 }} />
                    <span>{t("sos.btn_dispatch103", lang)}</span>
                  </button>
                </div>
              </div>

              {/* Emergency Vitals Card */}
              {activeEvent.vitals_snapshot && (
                <div className="detail-section-card vitals-sos-card">
                  <h4>
                    <Zap size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                    <span>{t("sos.telemetry_title", lang)}</span>
                  </h4>
                  <div className="sos-vitals-grid">
                    <div className="sos-vital-box">
                      <span className="sos-vital-label">SpO2 (Kislorod)</span>
                      <span className={`sos-vital-value ${activeEvent.vitals_snapshot.spo2 < 90 ? "danger" : "normal"}`}>
                        {activeEvent.vitals_snapshot.spo2}%
                      </span>
                      <span className="sos-vital-note">
                        {activeEvent.vitals_snapshot.spo2 < 90 ? (
                          <>
                            <AlertTriangle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                            <span>{t("sos.danger_hypoxia", lang)}</span>
                          </>
                        ) : (
                          t("sos.normal", lang)
                        )}
                      </span>
                    </div>
                    <div className="sos-vital-box">
                      <span className="sos-vital-label">Puls (bpm)</span>
                      <span className={`sos-vital-value ${activeEvent.vitals_snapshot.hr > 100 ? "danger" : "normal"}`}>
                        {activeEvent.vitals_snapshot.hr} bpm
                      </span>
                      <span className="sos-vital-note">
                        {activeEvent.vitals_snapshot.hr > 100 ? (
                          <>
                            <AlertTriangle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                            <span>{t("sos.danger_tachycardia", lang)}</span>
                          </>
                        ) : (
                          t("sos.normal", lang)
                        )}
                      </span>
                    </div>
                    {activeEvent.vitals_snapshot.skin_temp && (
                      <div className="sos-vital-box">
                        <span className="sos-vital-label">{t("sos.skin_temp", lang)}</span>
                        <span className="sos-vital-value normal">
                          {activeEvent.vitals_snapshot.skin_temp}°C
                        </span>
                        <span className="sos-vital-note">{t("sos.stable", lang)}</span>
                      </div>
                    )}
                    {activeEvent.vitals_snapshot.rr && (
                      <div className="sos-vital-box">
                        <span className="sos-vital-label">{t("sos.rr", lang)}</span>
                        <span className={`sos-vital-value ${activeEvent.vitals_snapshot.rr > 22 ? "danger" : "normal"}`}>
                          {activeEvent.vitals_snapshot.rr}/daq
                        </span>
                        <span className="sos-vital-note">
                          {activeEvent.vitals_snapshot.rr > 22 ? (
                            <>
                              <AlertTriangle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                              <span>{t("sos.accelerated", lang)}</span>
                            </>
                          ) : (
                            t("sos.normal", lang)
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Address & GPS Card */}
              <div className="detail-section-card">
                <h4>
                  <MapPin size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  <span>{t("sos.address_title", lang)}</span>
                </h4>
                <div className="address-display-box">
                  <p className="address-line-primary">
                    <strong>
                      {activeEvent.address_snapshot?.region || "Xorazm"}, {activeEvent.address_snapshot?.district || ""}, {activeEvent.address_snapshot?.street || ""}{" "}
                      {activeEvent.address_snapshot?.house ? `№${activeEvent.address_snapshot.house}` : ""}
                      {activeEvent.address_snapshot?.flat ? `, xonadon ${activeEvent.address_snapshot.flat}` : ""}
                    </strong>
                  </p>
                  {activeEvent.address_snapshot?.landmark && (
                    <p className="address-line-sub">
                      <Target size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                      <strong>{t("sos.landmark", lang)}</strong> {activeEvent.address_snapshot.landmark}
                    </p>
                  )}
                  {activeEvent.address_snapshot?.entrance_note && (
                    <p className="address-line-sub">
                      <DoorOpen size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                      <strong>{t("sos.entrance", lang)}</strong> {activeEvent.address_snapshot.entrance_note}
                    </p>
                  )}
                </div>

                {activeEvent.device_lat && activeEvent.device_lon && (
                  <div className="gps-location-bar">
                    <span>
                      <Globe size={13} style={{ marginRight: 4, verticalAlign: "middle" }} />
                      GPS: {activeEvent.device_lat.toFixed(6)}, {activeEvent.device_lon.toFixed(6)}
                    </span>
                    <a
                      href={`https://maps.google.com/?q=${activeEvent.device_lat},${activeEvent.device_lon}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-map-link"
                    >
                      {t("sos.open_map", lang)} <ExternalLink size={12} style={{ marginLeft: 4, verticalAlign: "middle" }} />
                    </a>
                  </div>
                )}
              </div>

              {/* Clinical Snapshot Card */}
              <div className="detail-section-card">
                <h4>
                  <Pill size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  <span>{t("sos.clinical_title", lang)}</span>
                </h4>
                <div className="clinical-snap-grid">
                  <div className="snap-col">
                    <h5>{t("sos.allergies_label", lang)}</h5>
                    {activeEvent.clinical_snapshot?.allergies && activeEvent.clinical_snapshot.allergies.length > 0 ? (
                      <ul className="allergies-list-badges">
                        {activeEvent.clinical_snapshot.allergies.map((a: any, idx: number) => (
                          <li key={idx} className="allergy-badge-danger">
                            <AlertTriangle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />
                            <span>{a.substance || a} ({a.reaction || "og'ir"})</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted">{t("detail.none", lang)}</p>
                    )}
                  </div>

                  <div className="snap-col">
                    <h5>{t("sos.meds_label", lang)}</h5>
                    {activeEvent.clinical_snapshot?.active_medications && activeEvent.clinical_snapshot.active_medications.length > 0 ? (
                      <ul className="meds-list-badges">
                        {activeEvent.clinical_snapshot.active_medications.map((m: any, idx: number) => (
                          <li key={idx}>
                            • {m.name} {m.dose ? `(${m.dose})` : ""} {m.frequency || ""}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted">{t("sos.no_meds", lang)}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Resolution Form Card */}
              <div className="detail-section-card resolution-card">
                <h4>
                  <CheckCircle2 size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  <span>{t("sos.resolution_title", lang)}</span>
                </h4>
                <div className="resolution-input-row">
                  <input
                    type="text"
                    placeholder={t("sos.resolution_placeholder", lang)}
                    value={resolutionNotes[activeEvent.id] || ""}
                    onChange={(e) =>
                      setResolutionNotes({
                        ...resolutionNotes,
                        [activeEvent.id]: e.target.value,
                      })
                    }
                    className="input-resolution-note"
                  />
                  <button
                    type="button"
                    className="btn-resolve-sos"
                    disabled={actionInProgress === activeEvent.id}
                    onClick={() => handleResolve(activeEvent.id)}
                  >
                    {t("sos.btn_resolve", lang)}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
