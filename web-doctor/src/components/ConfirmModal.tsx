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
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onConfirm(note);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <h2 className="modal-title">{t("confirm_modal.title", lang)}</h2>

        <form onSubmit={handleSubmit}>
          <label htmlFor="confirm-note-textarea" style={{ display: "block", fontSize: "14px", marginBottom: "8px" }}>
            {t("confirm_modal.note_label", lang)}
          </label>
          <textarea
            id="confirm-note-textarea"
            className="modal-textarea"
            placeholder={t("confirm_modal.placeholder", lang)}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            required
          />

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={submitting}
            >
              {t("confirm_modal.cancel", lang)}
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "..." : t("confirm_modal.submit", lang)}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
