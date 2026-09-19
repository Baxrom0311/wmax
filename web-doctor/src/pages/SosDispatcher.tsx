import React, { useCallback, useEffect, useState } from "react";
import { acknowledgeSos, dispatchSos103, fetchActiveSos, resolveSos } from "../lib/api";
import type { SosEventItem } from "../lib/types";

interface SosDispatcherProps {
  onClose: () => void;
  isDemo?: boolean;
}

export const SosDispatcher: React.FC<SosDispatcherProps> = ({ onClose, isDemo }) => {
  const [events, setEvents] = useState<SosEventItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<string, string>>({});
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadSos = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchActiveSos(isDemo);
      setEvents(data);
      if (data.length > 0 && !selectedEventId) {
        setSelectedEventId(data[0].id);
      }
    } catch (e: any) {
      setActionError(e?.message || "SOS ma'lumotlarini yuklashda xatolik");
    } finally {
      setLoading(false);
    }
  }, [isDemo, selectedEventId]);

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
    const note = resolutionNotes[sosId] || "Tez tibbiy yordam brigadasi yetib keldi, holat barqarorlashtirildi.";
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
          <span className="dispatcher-badge-live">LIVE 103 DISPATCH</span>
          <h2>🚨 Favqulodda SOS Signallari Boshqaruvi</h2>
          <p>Kardiologik bemorlar uchun shoshilinch tez tibbiy yordam va lokatsiya dispetcheri</p>
        </div>
        <div className="dispatcher-actions">
          <button type="button" className="btn-refresh-sos" onClick={loadSos}>
            🔄 Yangilash
          </button>
          <button type="button" className="btn-close-dispatcher" onClick={onClose}>
            ✕ Ro'yxatga qaytish
          </button>
        </div>
      </div>

      {actionError && (
        <div className="dispatcher-error-bar">
          ⚠️ {actionError}
          <button type="button" onClick={() => setActionError(null)}>✕</button>
        </div>
      )}

      {loading && events.length === 0 ? (
        <div className="dispatcher-loading">Yuklanmoqda...</div>
      ) : events.length === 0 ? (
        <div className="dispatcher-empty-card">
          <span className="empty-check-icon">✓</span>
          <h3>Hozirda faol SOS signallari yo'q</h3>
          <p>Barcha bemorlar barqaror yoki avvalgi signallar muvaffaqiyatli bartaraf etilgan.</p>
        </div>
      ) : (
        <div className="dispatcher-main-grid">
          {/* List of active events */}
          <div className="dispatcher-events-list">
            <h3>Navbatdagi chaqiruvlar ({events.length})</h3>
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
                        ? "YANGI"
                        : evt.status === "acknowledged"
                        ? "QABUL QILINGAN"
                        : evt.status === "dispatched_103"
                        ? "103 YUBORILGAN"
                        : evt.status}
                    </span>
                  </div>
                  <div className="event-item-address">
                    📍 {addr.street || addr.district || "Manzil"}, {addr.landmark || ""}
                  </div>
                  <div className="event-item-meta">
                    <span>Manba: {evt.source}</span>
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
                  <h3>{activeEvent.patient_name || "Bemor"}</h3>
                  <div className="detail-tags-row">
                    <span className="detail-tag-blood">
                      🩸 Qon guruhi: {activeEvent.clinical_snapshot?.blood_group || "Noma'lum"}{" "}
                      {activeEvent.clinical_snapshot?.rh ? `(${activeEvent.clinical_snapshot.rh})` : ""}
                    </span>
                    <span className="detail-tag-status">
                      Holat: {activeEvent.status.toUpperCase()}
                    </span>
                    <span className="detail-tag-source">
                      Turi: {activeEvent.source}
                    </span>
                  </div>
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
                      ✓ Qabul qilish
                    </button>
                  )}

                  <button
                    type="button"
                    className="btn-dispatch-103"
                    disabled={actionInProgress === activeEvent.id}
                    onClick={() => handleDispatch103(activeEvent.id)}
                  >
                    🚑 103 Brigadasini yo'naltirish
                  </button>
                </div>
              </div>

              {/* Address & GPS Card */}
              <div className="detail-section-card">
                <h4>📍 Yashash manzili va Orientir (103 brigadasi uchun)</h4>
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
                      🎯 <strong>Mo'ljal:</strong> {activeEvent.address_snapshot.landmark}
                    </p>
                  )}
                  {activeEvent.address_snapshot?.entrance_note && (
                    <p className="address-line-sub">
                      🚪 <strong>Podyezd / Kirish eslatmasi:</strong> {activeEvent.address_snapshot.entrance_note}
                    </p>
                  )}
                </div>

                {activeEvent.device_lat && activeEvent.device_lon && (
                  <div className="gps-location-bar">
                    <span>
                      🌐 GPS koordinatalar: {activeEvent.device_lat.toFixed(6)}, {activeEvent.device_lon.toFixed(6)}
                    </span>
                    <a
                      href={`https://maps.google.com/?q=${activeEvent.device_lat},${activeEvent.device_lon}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-map-link"
                    >
                      Google Xaritada ochish ↗
                    </a>
                  </div>
                )}
              </div>

              {/* Clinical Snapshot Card */}
              <div className="detail-section-card">
                <h4>💊 Shoshilinch Klinik Ko'rsatkichlar</h4>
                <div className="clinical-snap-grid">
                  <div className="snap-col">
                    <h5>Allergiyalar:</h5>
                    {activeEvent.clinical_snapshot?.allergies && activeEvent.clinical_snapshot.allergies.length > 0 ? (
                      <ul className="allergies-list-badges">
                        {activeEvent.clinical_snapshot.allergies.map((a: any, idx: number) => (
                          <li key={idx} className="allergy-badge-danger">
                            ⚠️ {a.substance || a} ({a.reaction || "og'ir"})
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted">Ma'lum emas / Allergiyasi yo'q</p>
                    )}
                  </div>

                  <div className="snap-col">
                    <h5>Qabul qilayotgan dorilari:</h5>
                    {activeEvent.clinical_snapshot?.active_medications && activeEvent.clinical_snapshot.active_medications.length > 0 ? (
                      <ul className="meds-list-badges">
                        {activeEvent.clinical_snapshot.active_medications.map((m: any, idx: number) => (
                          <li key={idx}>
                            • {m.name} {m.dose ? `(${m.dose})` : ""} {m.frequency || ""}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted">Tayinlovlar yo'q</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Resolution Form Card */}
              <div className="detail-section-card resolution-card">
                <h4>✓ Hodisani Yakunlash / Yopish</h4>
                <div className="resolution-input-row">
                  <input
                    type="text"
                    placeholder="Qisqa klinik xulosa (masalan: 103 brigadasi yordam ko'rsatdi, kasalxonaga yotqizildi)"
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
                    Hal qilindi va Yopish
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
