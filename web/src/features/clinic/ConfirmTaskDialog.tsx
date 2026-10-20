import React, { useState } from "react";
import { CheckCircle2, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { pick, type Lang } from "@/i18n";
import { t } from "@/i18n/clinic";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (note: string) => Promise<void>;
  lang: Lang;
  /** Ask for visit vitals (patrol report) or only a free-text note. */
  withVitals?: boolean;
  title?: string;
}

export function ConfirmTaskDialog({ open, onOpenChange, onConfirm, lang, withVitals = true, title }: Props) {
  const [note, setNote] = useState("");
  const [bp, setBp] = useState("");
  const [hr, setHr] = useState("");
  const [spo2, setSpo2] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const tags = [
    t("confirm_modal.tag_vitals_normal", lang),
    t("confirm_modal.tag_home_visited", lang),
    t("confirm_modal.tag_med_adjusted", lang),
    t("confirm_modal.tag_hospital_no", lang),
    t("confirm_modal.tag_monitoring_cont", lang),
  ];

  const reset = () => {
    setNote("");
    setBp("");
    setHr("");
    setSpo2("");
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Only measured values go into the record; empty fields are not invented.
      const vitals = [
        bp.trim() && `AQB: ${bp.trim()} mm sim. ust.`,
        hr.trim() && `HR: ${hr.trim()} bpm`,
        spo2.trim() && `SpO2: ${spo2.trim()}%`,
      ].filter(Boolean);
      const full = [vitals.join(", "), note.trim()].filter(Boolean).join(". ");
      await onConfirm(full);
      reset();
      onOpenChange(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !submitting && onOpenChange(v)}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle2 className="text-primary size-5" />
            {title ?? t("confirm_modal.title", lang)}
          </DialogTitle>
          <DialogDescription>
            {pick(lang, {
              uz: "Ko'rik natijasini kiriting. Faqat haqiqatda o'lchangan qiymatlarni yozing.",
              ru: "Внесите итог осмотра. Указывайте только реально измеренные значения.",
              en: "Record the visit outcome. Enter only values you actually measured.",
            })}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          {withVitals && (
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="ct-bp">{t("confirm_modal.bp_label", lang).replace(/:$/, "")}</Label>
                <Input id="ct-bp" placeholder="120/80" value={bp} onChange={(e) => setBp(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ct-hr">{t("confirm_modal.hr_label", lang).replace(/:$/, "")}</Label>
                <Input id="ct-hr" type="number" inputMode="numeric" placeholder="72" value={hr} onChange={(e) => setHr(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ct-spo2">{t("confirm_modal.spo2_label", lang).replace(/:$/, "")}</Label>
                <Input id="ct-spo2" type="number" inputMode="numeric" placeholder="97" value={spo2} onChange={(e) => setSpo2(e.target.value)} />
              </div>
            </div>
          )}
          <div className="space-y-2">
            <span className="text-muted-foreground text-xs font-medium">{t("confirm_modal.quick_tags_label", lang)}</span>
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <Button key={tag} type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={() => setNote((prev) => (prev ? `${prev}. ${tag}` : tag))}>
                  <Plus />
                  {tag}
                </Button>
              ))}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ct-note">{t("confirm_modal.note_label", lang).replace(/:$/, "")}</Label>
            <Textarea id="ct-note" rows={4} required placeholder={t("confirm_modal.placeholder", lang)} value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
              {t("confirm_modal.cancel", lang)}
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting && <Loader2 className="animate-spin" />}
              {t("confirm_modal.submit", lang)}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
