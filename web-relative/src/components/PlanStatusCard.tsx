import React, { useState } from "react";
import type { Lang } from "../i18n";
import { cn } from "../lib/utils";
import { Diamond, CreditCard, CheckCircle, X } from "lucide-react";

interface PlanStatusCardProps {
  lang: Lang;
}

import { t } from "../i18n";

interface PlanStatusCardProps {
  lang: Lang;
}

export const PlanStatusCard: React.FC<PlanStatusCardProps> = ({ lang }) => {
  const [currentPlan, setCurrentPlan] = useState<"free" | "premium" | "premium_doc">("premium");
  const [trialDaysLeft, setTrialDaysLeft] = useState<number>(9);
  const [showUpgradeModal, setShowUpgradeModal] = useState<boolean>(false);
  const [selectedUpgrade, setSelectedUpgrade] = useState<"premium" | "premium_doc">("premium");
  const [paymentProvider, setPaymentProvider] = useState<"payme" | "click" | "uzum">("payme");
  const [upgradedSuccess, setUpgradedSuccess] = useState<boolean>(false);

  const handlePay = () => {
    setCurrentPlan(selectedUpgrade);
    setTrialDaysLeft(0);
    setUpgradedSuccess(true);
    setTimeout(() => {
      setUpgradedSuccess(false);
      setShowUpgradeModal(false);
    }, 1600);
  };

  const planLabel = t(`plan.${currentPlan}`, lang);
  const isPremiumDoc = currentPlan === "premium_doc";

  return (
    <>
      <div className="mx-4 mb-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm p-4 flex flex-col gap-3 animate-fade-up">
        {/* Plan row */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 flex-wrap">
              <Diamond size={16} className="text-blue-500" />
              <span className="text-[14px] font-extrabold text-slate-800 dark:text-slate-100" style={{ fontFamily: "'Outfit',sans-serif" }}>
                {planLabel}
              </span>
              {trialDaysLeft > 0 && (
                <span className="text-[10px] font-bold bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 px-2 py-0.5 rounded-full">
                  {t("plan.trial", lang, { d: trialDaysLeft })}
                </span>
              )}
            </div>
            <p className="text-[11.5px] text-slate-500 dark:text-slate-400 leading-snug max-w-[220px]">
              {t(`plan.desc_${currentPlan}`, lang)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowUpgradeModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[12px] font-semibold px-3 py-2 rounded-xl transition-all active:scale-95 flex-shrink-0 cursor-pointer"
          >
            <CreditCard size={13} />
            {t("plan.manage", lang)}
          </button>
        </div>

        {/* Compliance strip */}
        <div className={cn(
          "flex items-start gap-2 rounded-xl px-3 py-2.5 border text-[11.5px] leading-snug",
          isPremiumDoc
            ? "bg-green-50 dark:bg-green-950/40 border-green-200 dark:border-green-900/60 text-green-800 dark:text-green-300"
            : "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300"
        )}>
          <span className="text-base flex-shrink-0">{isPremiumDoc ? "👨‍⚕️" : "ℹ️"}</span>
          <span>
            {isPremiumDoc
              ? t("plan.compliance_doc", lang)
              : t("plan.compliance_nodoc", lang)}
          </span>
        </div>
      </div>

      {/* ── Upgrade Modal ── */}
      {showUpgradeModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4"
          onClick={() => setShowUpgradeModal(false)}
        >
          <div
            className="bg-white dark:bg-slate-900 rounded-3xl w-full max-w-[520px] p-6 shadow-2xl border border-slate-100 dark:border-slate-800 animate-fade-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-[16px] font-extrabold text-slate-800 dark:text-slate-100" style={{ fontFamily: "'Outfit',sans-serif" }}>
                {t("plan.modal_title", lang)}
              </h3>
              <button
                type="button"
                onClick={() => setShowUpgradeModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center transition-colors cursor-pointer"
              >
                <X size={15} className="text-slate-500 dark:text-slate-400" />
              </button>
            </div>

            {/* Plan options */}
            <div className="flex flex-col gap-3 mb-4">
              {(["premium", "premium_doc"] as const).map((plan) => {
                const isSelected = selectedUpgrade === plan;
                return (
                  <button
                    key={plan}
                    type="button"
                    onClick={() => setSelectedUpgrade(plan)}
                    className={cn(
                      "text-left rounded-2xl p-4 border-2 transition-all cursor-pointer",
                      isSelected
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[14px] font-bold text-slate-800 dark:text-slate-100">
                        {t(`plan.${plan}`, lang)}
                      </span>
                      <span className="text-[14px] font-extrabold text-blue-600 dark:text-blue-400">
                        {plan === "premium" ? "59 000" : "249 000"} {t("plan.price_per_month", lang)}
                      </span>
                    </div>
                    <p className="text-[11.5px] text-slate-500 dark:text-slate-400 leading-snug">
                      {t(`plan.desc_${plan}_detail`, lang)}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Payment provider */}
            <div className="mb-5">
              <label className="text-[12px] font-bold text-slate-600 dark:text-slate-300 mb-2 block">
                {t("plan.payment_method", lang)}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(["payme", "click", "uzum"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPaymentProvider(p)}
                    className={cn(
                      "py-2.5 rounded-xl border-2 font-bold text-[13px] transition-all cursor-pointer",
                      paymentProvider === p
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"
                    )}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Success message */}
            {upgradedSuccess && (
              <div className="flex items-center gap-2 bg-green-50 dark:bg-green-950/50 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 rounded-xl px-4 py-3 mb-4 text-[13px] font-semibold">
                <CheckCircle size={16} className="text-green-600 dark:text-green-400" />
                {t("plan.payment_success", lang)}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowUpgradeModal(false)}
                className="flex-1 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-semibold text-[13px] hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                {t("plan.cancel", lang)}
              </button>
              <button
                type="button"
                onClick={handlePay}
                className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-[13px] transition-colors active:scale-95 cursor-pointer"
              >
                {t("plan.pay_with", lang, { p: paymentProvider.toUpperCase() })}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
