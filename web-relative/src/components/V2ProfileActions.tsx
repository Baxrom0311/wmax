import React, { useState } from "react";
import { recordPatientMeasurement, triggerEmergencySos } from "../lib/api";

interface V2ProfileActionsProps {
  patientId: string;
  onSuccess?: (msg: string) => void;
}

export const V2ProfileActions: React.FC<V2ProfileActionsProps> = ({
  patientId,
  onSuccess,
}) => {
  const [weight, setWeight] = useState<string>("");
  const [savingWeight, setSavingWeight] = useState<boolean>(false);
  const [weightSaved, setWeightSaved] = useState<boolean>(false);

  const [sosActive, setSosActive] = useState<boolean>(false);
  const [sosSent, setSosSent] = useState<boolean>(false);
  const [sosLoading, setSosLoading] = useState<boolean>(false);

  const handleSaveWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(weight);
    if (isNaN(val) || val < 30 || val > 250) {
      alert("Iltimos, to'g'ri vazn kiriting (30 - 250 kg)");
      return;
    }

    setSavingWeight(true);
    try {
      await recordPatientMeasurement(patientId, val);
      setWeightSaved(true);
      setWeight("");
      onSuccess?.("Vazn muvaffaqiyatli saqlandi!");
      setTimeout(() => setWeightSaved(false), 4000);
    } catch (err: any) {
      alert(err?.message || "Vaznni saqlashda xatolik");
    } finally {
      setSavingWeight(false);
    }
  };

  const handleTriggerSos = async () => {
    setSosLoading(true);
    try {
      await triggerEmergencySos(patientId);
      setSosSent(true);
      setSosActive(false);
      onSuccess?.("🚨 SOS signali dispetcher va shifokorga yetkazildi!");
    } catch (err: any) {
      alert(err?.message || "SOS yuborishda xatolik");
    } finally {
      setSosLoading(false);
    }
  };

  return (
    <div className="v2-profile-actions-container">
      {/* 1. Weight Logging (G7 Fluid Indicator) */}
      <div className="v2-action-card weight-logging-card">
        <div className="card-top-icon-row">
          <span className="card-icon">⚖️</span>
          <div>
            <h4 className="card-title">Bugungi vazn (Suyuqlik monitoringi)</h4>
            <p className="card-sub">Ertalab och qoringa o'lchangan vaznni kiriting</p>
          </div>
        </div>

        <form onSubmit={handleSaveWeight} className="weight-entry-form">
          <div className="weight-input-group">
            <input
              type="number"
              step="0.1"
              min="30"
              max="250"
              placeholder="72.5"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="weight-input-field"
              required
            />
            <span className="unit-label">kg</span>
          </div>
          <button
            type="submit"
            className="btn-save-weight"
            disabled={savingWeight}
          >
            {savingWeight ? "Saqlanmoqda..." : weightSaved ? "✓ Saqlandi" : "Saqlash"}
          </button>
        </form>
      </div>

      {/* 2. Urgent Emergency SOS Button */}
      <div className="v2-action-card sos-emergency-card">
        <div className="card-top-icon-row">
          <span className="card-icon">🚨</span>
          <div>
            <h4 className="card-title">Shoshilinch Yordam (SOS)</h4>
            <p className="card-sub">O'zingizni juda yomon his qilsangiz, zudlik bilan bosing</p>
          </div>
        </div>

        {sosSent ? (
          <div className="sos-sent-badge">
            ✓ SOS signali qabul qilindi! Tez yordam va kardiologga yo'naltirildi.
          </div>
        ) : (
          <button
            type="button"
            className="btn-trigger-sos-urgent"
            onClick={() => setSosActive(true)}
          >
            🚨 103 VA SHIFOKORGA SOS CHAQIRUV
          </button>
        )}
      </div>

      {/* Confirmation modal for SOS */}
      {sosActive && (
        <div className="sos-confirm-backdrop" onClick={() => setSosActive(false)}>
          <div className="sos-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-alert-icon">🚨</div>
            <h3>Shoshilinch SOS signalini tasdiqlaysizmi?</h3>
            <p>
              Ushbu signal zudlik bilan 103 tez tibbiy yordam dispetcheriga va navbatchi
              shifokorga bemorning joylashuv manzili bilan birga yuboriladi.
            </p>
            <div className="sos-modal-buttons">
              <button
                type="button"
                className="btn-sos-cancel"
                onClick={() => setSosActive(false)}
                disabled={sosLoading}
              >
                Bekor qilish
              </button>
              <button
                type="button"
                className="btn-sos-confirm-yes"
                onClick={handleTriggerSos}
                disabled={sosLoading}
              >
                {sosLoading ? "Yuborilmoqda..." : "Ha, Zudlik bilan chaqirilsin"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
