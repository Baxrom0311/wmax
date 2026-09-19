import React, { useState } from "react";
import type { Lang } from "../i18n";
import { t } from "../i18n";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (note: string) => Promise<void>;
  lang: Lang;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  lang,
}) => {
  const [note, setNote] = useState("");
  const [bp, setBp] = useState("125/80");
  const [hr, setHr] = useState("74");
  const [spo2, setSpo2] = useState("97");
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const quickTags = [
    t("confirm_modal.tag_vitals_normal", lang),
    t("confirm_modal.tag_home_visited", lang),
    t("confirm_modal.tag_med_adjusted", lang),
    t("confirm_modal.tag_hospital_no", lang),
    t("confirm_modal.tag_monitoring_cont", lang),
  ];

  const handleTagClick = (tag: string) => {
    setNote((prev) => (prev ? `${prev}. ${tag}` : tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const fullNote = `AQB: ${bp} mm sim. ust., HR: ${hr} bpm, SpO2: ${spo2}%. ${note}`.trim();
      await onConfirm(fullNote);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-dialog modal-dialog-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header-official">
          <div className="modal-emblem-wrap">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth="2.2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <div>
            <h2 className="modal-title">{t("confirm_modal.title", lang)}</h2>
            <p className="modal-subtitle">Protokol №11 · 24 soatlik shoshilinch aktiv patronaj yopilishi</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="modal-body-form">
          {/* Clinical Vitals during visit */}
          <div className="modal-vitals-row">
            <div className="modal-vital-input-group">
              <label htmlFor="modal-bp-input">{t("confirm_modal.bp_label", lang)}</label>
              <input
                id="modal-bp-input"
                type="text"
                className="form-input-official"
                placeholder="120/80"
                value={bp}
                onChange={(e) => setBp(e.target.value)}
              />
            </div>
            <div className="modal-vital-input-group">
              <label htmlFor="modal-hr-input">{t("confirm_modal.hr_label", lang)}</label>
              <input
                id="modal-hr-input"
                type="number"
                className="form-input-official"
                placeholder="72"
                value={hr}
                onChange={(e) => setHr(e.target.value)}
              />
            </div>
            <div className="modal-vital-input-group">
              <label htmlFor="modal-spo2-input">{t("confirm_modal.spo2_label", lang)}</label>
              <input
                id="modal-spo2-input"
                type="number"
                className="form-input-official"
                placeholder="98"
                value={spo2}
                onChange={(e) => setSpo2(e.target.value)}
              />
            </div>
          </div>

          {/* Quick clinical templates */}
          <div className="modal-quick-tags-section">
            <span className="quick-tags-title">{t("confirm_modal.quick_tags_label", lang)}</span>
            <div className="quick-tags-chips">
              {quickTags.map((tag, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="quick-tag-chip"
                  onClick={() => handleTagClick(tag)}
                >
                  + {tag}
                </button>
              ))}
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="confirm-note-textarea" className="form-label-official">
              {t("confirm_modal.note_label", lang)}
            </label>
            <textarea
              id="confirm-note-textarea"
              className="modal-textarea form-input-official"
              rows={4}
              placeholder={t("confirm_modal.placeholder", lang)}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              required
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-clinical"
              onClick={onClose}
              disabled={submitting}
            >
              {t("confirm_modal.cancel", lang)}
            </button>
            <button
              type="submit"
              className="btn-clinical btn-approve-official"
              disabled={submitting}
            >
              {submitting ? "..." : t("confirm_modal.submit", lang)}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
