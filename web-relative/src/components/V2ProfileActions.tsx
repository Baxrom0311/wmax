import React, { useState } from "react";
import { recordPatientMeasurement, triggerEmergencySos } from "../lib/api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { cn } from "../lib/utils";
import { Scale, Siren, CheckCircle, X, AlertTriangle, AlertCircle } from "lucide-react";

interface V2ProfileActionsProps {
  patientId: string;
  lang?: Lang;
  onSuccess?: (msg: string) => void;
}

export const V2ProfileActions: React.FC<V2ProfileActionsProps> = ({
  patientId,
  lang = "uz",
  onSuccess,
}) => {
  const [weight, setWeight] = useState<string>("");
  const [savingWeight, setSavingWeight] = useState<boolean>(false);
  const [weightSaved, setWeightSaved] = useState<boolean>(false);
  const [weightError, setWeightError] = useState<string | null>(null);

  const [sosActive, setSosActive] = useState<boolean>(false);
  const [sosSent, setSosSent] = useState<boolean>(false);
  const [sosLoading, setSosLoading] = useState<boolean>(false);
  const [sosError, setSosError] = useState<string | null>(null);

  const handleSaveWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    setWeightError(null);
    const val = parseFloat(weight);
    if (isNaN(val) || val < 30 || val > 250) {
      setWeightError(t("actions.weight_invalid", lang));
      return;
    }
    setSavingWeight(true);
    try {
      await recordPatientMeasurement(patientId, val);
      setWeightSaved(true);
      setWeight("");
      onSuccess?.(t("actions.weight_saved", lang));
      setTimeout(() => setWeightSaved(false), 4000);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setWeightError(e?.message || t("actions.weight_invalid", lang));
    } finally {
      setSavingWeight(false);
    }
  };

  const handleTriggerSos = async () => {
    setSosLoading(true);
    setSosError(null);
    try {
      await triggerEmergencySos(patientId);
      setSosSent(true);
      setSosActive(false);
      onSuccess?.(t("actions.sos_card_sent", lang));
    } catch (err: unknown) {
      const e = err as { message?: string };
      setSosError(e?.message || t("actions.sos_card_error", lang));
    } finally {
      setSosLoading(false);
    }
  };

  return (
    <div className="px-4 pb-4 flex flex-col gap-3 animate-fade-up">
      {/* ── Weight Logging Card ── */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0">
            <Scale size={18} className="text-blue-600" />
          </div>
          <div>
            <h4
              className="text-[14px] font-bold text-slate-800 leading-tight"
              style={{ fontFamily: "'Outfit',sans-serif" }}
            >
              {t("actions.weight_title", lang)}
            </h4>
            <p className="text-[11.5px] text-slate-400">
              {t("actions.weight_desc", lang)}
            </p>
          </div>
        </div>

        {weightError && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-3.5 py-2 text-[12px] font-medium animate-fade-up">
            <AlertCircle size={14} className="text-red-500 flex-shrink-0" />
            <span>{weightError}</span>
          </div>
        )}

        {weightSaved ? (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-800 rounded-xl px-4 py-3 text-[13px] font-semibold">
            <CheckCircle size={16} className="text-green-600" />
            {t("actions.weight_saved", lang)}
          </div>
        ) : (
          <form onSubmit={handleSaveWeight} className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="number"
                step="0.1"
                min="30"
                max="250"
                placeholder="72.5"
                value={weight}
                onChange={(e) => {
                  setWeight(e.target.value);
                  if (weightError) setWeightError(null);
                }}
                className={cn(
                  "w-full pl-4 pr-12 py-2.5 rounded-xl border border-slate-200 text-[15px] font-bold text-slate-800",
                  "focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all",
                  "placeholder:text-slate-300 placeholder:font-normal"
                )}
                required
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[13px] font-bold text-slate-400">
                kg
              </span>
            </div>
            <button
              type="submit"
              disabled={savingWeight}
              className={cn(
                "px-4 py-2.5 rounded-xl font-bold text-[13px] transition-all active:scale-95",
                "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
              )}
            >
              {savingWeight ? t("actions.weight_saving", lang) : t("actions.weight_save_btn", lang)}
            </button>
          </form>
        )}
      </div>

      {/* ── SOS Card ── */}
      <div className="bg-red-50 rounded-2xl border border-red-200 p-4 flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-red-100 border border-red-200 flex items-center justify-center flex-shrink-0">
            <Siren size={18} className="text-red-600" />
          </div>
          <div>
            <h4
              className="text-[14px] font-bold text-red-800 leading-tight"
              style={{ fontFamily: "'Outfit',sans-serif" }}
            >
              {t("actions.sos_card_title", lang)}
            </h4>
            <p className="text-[11.5px] text-red-500">
              {t("actions.sos_card_desc", lang)}
            </p>
          </div>
        </div>

        {sosSent ? (
          <div className="flex items-center gap-2 bg-white border border-red-200 text-red-800 rounded-xl px-4 py-3 text-[13px] font-semibold">
            <CheckCircle size={16} className="text-red-600" />
            {t("actions.sos_card_sent", lang)}
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setSosActive(true)}
            className={cn(
              "flex items-center justify-center gap-2 w-full py-3 rounded-xl font-bold text-[13px] sm:text-[14px] transition-all active:scale-[0.98]",
              "bg-red-600 hover:bg-red-700 text-white shadow-md shadow-red-200"
            )}
          >
            <Siren size={18} />
            {t("actions.sos_card_btn", lang)}
          </button>
        )}
      </div>

      {/* ── SOS Confirm Modal ── */}
      {sosActive && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSosActive(false)}
        >
          <div
            className="bg-white rounded-3xl w-full max-w-sm p-6 shadow-2xl flex flex-col items-center gap-4 animate-fade-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-16 h-16 rounded-2xl bg-red-100 border border-red-200 flex items-center justify-center">
              <AlertTriangle size={32} className="text-red-600" />
            </div>
            <div className="text-center">
              <h3
                className="text-[16px] font-extrabold text-slate-800 mb-1"
                style={{ fontFamily: "'Outfit',sans-serif" }}
              >
                {t("actions.sos_confirm_title", lang)}
              </h3>
              <p className="text-[12.5px] text-slate-500 leading-relaxed">
                {t("actions.sos_confirm_desc", lang)}
              </p>
            </div>

            {sosError && (
              <div className="flex items-center gap-2 w-full bg-red-50 border border-red-200 text-red-700 rounded-xl p-3 text-[12px]">
                <AlertCircle size={14} className="text-red-500 flex-shrink-0" />
                <span>{sosError}</span>
              </div>
            )}

            <div className="flex gap-2 w-full">
              <button
                type="button"
                onClick={() => setSosActive(false)}
                disabled={sosLoading}
                className="flex-1 flex items-center justify-center gap-1.5 py-3 rounded-xl border border-slate-200 text-slate-600 font-semibold text-[13px] hover:bg-slate-50 transition-colors"
              >
                <X size={14} />
                {t("actions.sos_cancel", lang)}
              </button>
              <button
                type="button"
                onClick={handleTriggerSos}
                disabled={sosLoading}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 py-3 rounded-xl font-bold text-[13px] transition-all",
                  "bg-red-600 hover:bg-red-700 text-white active:scale-95 disabled:opacity-60"
                )}
              >
                <Siren size={14} />
                {sosLoading ? t("actions.sos_sending", lang) : t("actions.sos_confirm_btn", lang)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
