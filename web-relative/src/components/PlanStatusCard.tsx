import React, { useState } from "react";
import type { Lang } from "../i18n";
import { cn } from "../lib/utils";
import { Diamond, CreditCard, CheckCircle, X } from "lucide-react";

interface PlanStatusCardProps {
  lang: Lang;
}

const PLAN_LABELS = {
  free: { uz: "Baza (Bepul)", ru: "Базовый (Бесплатно)" },
  premium: { uz: "Premium (Tahliliy)", ru: "Премиум (Аналитика)" },
  premium_doc: { uz: "Premium + Shifokor", ru: "Премиум + Врач" },
};

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

  const l = lang === "ru" ? "ru" : "uz";
  const planLabel = PLAN_LABELS[currentPlan][l];
  const isPremiumDoc = currentPlan === "premium_doc";

  return (
    <>
      <div className="mx-4 mb-2 rounded-2xl bg-white border border-slate-100 shadow-sm p-4 flex flex-col gap-3 animate-fade-up">
        {/* Plan row */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 flex-wrap">
              <Diamond size={16} className="text-blue-500" />
              <span className="text-[14px] font-extrabold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
                {planLabel}
              </span>
              {trialDaysLeft > 0 && (
                <span className="text-[10px] font-bold bg-blue-100 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full">
                  {l === "ru" ? `Триал: ${trialDaysLeft} дн.` : `Trial: ${trialDaysLeft} kun`}
                </span>
              )}
            </div>
            <p className="text-[11.5px] text-slate-500 leading-snug max-w-[220px]">
              {currentPlan === "premium"
                ? l === "ru"
                  ? "AI прогноз 72ч, дорогой журнал, PDF отчёт"
                  : "AI 72-soatlik prognoz, dori tahlili, PDF hisobot"
                : currentPlan === "premium_doc"
                ? l === "ru"
                  ? "24/7 кардиолог, звонок за 15 мин при красном сигнале"
                  : "24/7 kardiolog, qizil signalda 15 daqiqada qo'ng'iroq"
                : l === "ru" ? "Базовый мониторинг" : "Asosiy monitoring"}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowUpgradeModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[12px] font-semibold px-3 py-2 rounded-xl transition-all active:scale-95 flex-shrink-0"
          >
            <CreditCard size={13} />
            {l === "ru" ? "Управление" : "Boshqarish"}
          </button>
        </div>

        {/* Compliance strip */}
        <div className={cn(
          "flex items-start gap-2 rounded-xl px-3 py-2.5 border text-[11.5px] leading-snug",
          isPremiumDoc
            ? "bg-green-50 border-green-200 text-green-800"
            : "bg-amber-50 border-amber-200 text-amber-800"
        )}>
          <span className="text-base flex-shrink-0">{isPremiumDoc ? "👨‍⚕️" : "ℹ️"}</span>
          <span>
            {isPremiumDoc
              ? l === "ru"
                ? "Дежурный кардиолог подключён. Позвонит в течение 15 минут при красном сигнале."
                : "Navbatchi kardiolog ulangan. Qizil signalda 15 daqiqada qo'ng'iroq qilinadi."
              : l === "ru"
              ? "Личный врач не закреплён. При красном сигнале немедленно звоните 103."
              : "Shifokor biriktirilmagan. Qizil holatda darhol 103 ga qo'ng'iroq qiling."}
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
            className="bg-white rounded-3xl w-full max-w-[520px] p-6 shadow-2xl animate-fade-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-[16px] font-extrabold text-slate-800" style={{ fontFamily: "'Outfit',sans-serif" }}>
                {l === "ru" ? "Тарифы WMAX" : "WMAX Tariflari"}
              </h3>
              <button
                type="button"
                onClick={() => setShowUpgradeModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors"
              >
                <X size={15} className="text-slate-500" />
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
                      "text-left rounded-2xl p-4 border-2 transition-all",
                      isSelected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white hover:border-slate-300"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[14px] font-bold text-slate-800">
                        {PLAN_LABELS[plan][l]}
                      </span>
                      <span className="text-[14px] font-extrabold text-blue-600">
                        {plan === "premium" ? "59 000" : "249 000"} {l === "ru" ? "сум/мес" : "so'm/oy"}
                      </span>
                    </div>
                    <p className="text-[11.5px] text-slate-500 leading-snug">
                      {plan === "premium"
                        ? l === "ru"
                          ? "AI прогноз 72ч, анализ лекарств, безлимитная история, PDF для врача."
                          : "AI 72-soatlik prognoz, dori ta'siri tahlili, cheksiz tarix, PDF hisobot."
                        : l === "ru"
                        ? "24/7 кардиолог, вызов за 15 мин при критическом сигнале, 2 видеоконсультации в месяц."
                        : "24/7 navbatchi kardiolog, qizil signalda 15 daqiqada chaqiruv, oyda 2 video-konsultatsiya."}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Payment provider */}
            <div className="mb-5">
              <label className="text-[12px] font-bold text-slate-600 mb-2 block">
                {l === "ru" ? "Способ оплаты:" : "To'lov usuli:"}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(["payme", "click", "uzum"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPaymentProvider(p)}
                    className={cn(
                      "py-2.5 rounded-xl border-2 font-bold text-[13px] transition-all",
                      paymentProvider === p
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                    )}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Success message */}
            {upgradedSuccess && (
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-800 rounded-xl px-4 py-3 mb-4 text-[13px] font-semibold">
                <CheckCircle size={16} className="text-green-600" />
                {l === "ru" ? "Оплата прошла! Тариф активирован." : "To'lov muvaffaqiyatli! Tarif faollashtirildi."}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowUpgradeModal(false)}
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-semibold text-[13px] hover:bg-slate-50 transition-colors"
              >
                {l === "ru" ? "Отмена" : "Bekor qilish"}
              </button>
              <button
                type="button"
                onClick={handlePay}
                className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-[13px] transition-colors active:scale-95"
              >
                {paymentProvider.toUpperCase()} {l === "ru" ? "оплатить" : "orqali to'lash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
