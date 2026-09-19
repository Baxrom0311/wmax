import React, { useState } from "react";
import type { Lang } from "../i18n";

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
    }, 1500);
  };

  return (
    <div
      style={{
        background: "var(--bg-card, #ffffff)",
        borderRadius: "14px",
        padding: "16px",
        margin: "12px 0",
        border: "1px solid var(--border-color, #e2e8f0)",
        boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", flexWrap: "wrap" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "1.1rem" }}>💎</span>
            <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>
              {currentPlan === "free"
                ? "Tarif: Free (Baza)"
                : currentPlan === "premium"
                ? "Tarif: Premium (Tahliliy)"
                : "Tarif: Premium + Shifokor"}
            </span>
            {trialDaysLeft > 0 && (
              <span
                style={{
                  background: "rgba(59, 130, 246, 0.12)",
                  color: "#2563eb",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  padding: "2px 8px",
                  borderRadius: "10px",
                }}
              >
                {lang === "ru" ? `14 дней триал: осталось ${trialDaysLeft} дн.` : `14 kunlik trial: ${trialDaysLeft} kun qoldi`}
              </span>
            )}
          </div>
          <p style={{ margin: "2px 0 0 0", fontSize: "0.8rem", color: "var(--color-muted, #64748b)" }}>
            {currentPlan === "premium"
              ? lang === "ru"
                ? "Включено: AI прогноз на 72ч, отклик на лекарства, безлимитная история, PDF отчет"
                : "Faol: AI 72-soatlik prognoz, dori ta'siri, cheksiz tarix, shifokor uchun PDF hisobot"
              : lang === "ru"
              ? "Включено: Круглосуточный дежурный кардиолог и экстренный вызов"
              : "Faol: 24/7 Navbatchi kardiolog nazorati va qizil signalda qo'ng'iroq"}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowUpgradeModal(true)}
          style={{
            background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            padding: "8px 14px",
            fontSize: "0.8rem",
            fontWeight: 600,
            cursor: "pointer",
            boxShadow: "0 2px 6px rgba(37, 99, 235, 0.25)",
          }}
        >
          {lang === "ru" ? "Управление тарифом" : "Tarifni boshqarish"}
        </button>
      </div>

      {/* R2 Compliance Banner: Shifokor biriktirilmaganligi yoki telemeditsina holati */}
      <div
        style={{
          marginTop: "12px",
          padding: "8px 12px",
          background: currentPlan === "premium_doc" ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
          borderRadius: "8px",
          border: currentPlan === "premium_doc" ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid rgba(245, 158, 11, 0.2)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          fontSize: "0.78rem",
        }}
      >
        <span>{currentPlan === "premium_doc" ? "👨‍⚕️" : "ℹ️"}</span>
        <span style={{ color: currentPlan === "premium_doc" ? "#065f46" : "#92400e" }}>
          {currentPlan === "premium_doc"
            ? lang === "ru"
              ? "Дежурный врач подключен: при критическом отклонении поступит звонок в течение 15 минут."
              : "Navbatchi shifokor ulangan: qizil signalda 15 daqiqa ichida qo'ng'iroq qilinadi."
            : lang === "ru"
              ? "Внимание (B2C): Личный врач не закреплен. Система мониторит показатели для осведомленности семьи. При красном сигнале срочно вызовите 103."
              : "Eslatma (B2C): Shifokor biriktirilmagan. Tizim oilangiz xabardorligi uchun monitoring qiladi. Kritik qizil holatda darhol 103 ga qo'ng'iroq qiling."}
        </span>
      </div>

      {/* Upgrade / Subscription Modal */}
      {showUpgradeModal && (
        <div className="modal-backdrop" onClick={() => setShowUpgradeModal(false)}>
          <div
            className="modal-card"
            style={{ maxWidth: "520px", width: "92%" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3 style={{ margin: 0 }}>
                {lang === "ru" ? "Тарифы подписки WMAX" : "WMAX Obuna Tariflari"}
              </h3>
              <button className="modal-close-btn" onClick={() => setShowUpgradeModal(false)}>
                ✕
              </button>
            </div>

            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <div
                onClick={() => setSelectedUpgrade("premium")}
                style={{
                  border: selectedUpgrade === "premium" ? "2px solid #2563eb" : "1px solid #cbd5e1",
                  borderRadius: "10px",
                  padding: "12px",
                  cursor: "pointer",
                  background: selectedUpgrade === "premium" ? "rgba(37, 99, 235, 0.04)" : "#fff",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700 }}>Premium (Tahliliy)</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>59 000 so'm / oy</span>
                </div>
                <p style={{ fontSize: "0.8rem", color: "#64748b", margin: "4px 0 0 0" }}>
                  AI 72-soatlik dekompensatsiya prognozi, dori ta'siri tahlili va shifokor uchun PDF-hisobot.
                </p>
              </div>

              <div
                onClick={() => setSelectedUpgrade("premium_doc")}
                style={{
                  border: selectedUpgrade === "premium_doc" ? "2px solid #2563eb" : "1px solid #cbd5e1",
                  borderRadius: "10px",
                  padding: "12px",
                  cursor: "pointer",
                  background: selectedUpgrade === "premium_doc" ? "rgba(37, 99, 235, 0.04)" : "#fff",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700 }}>Premium + Shifokor (Telemeditsina)</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>249 000 so'm / oy</span>
                </div>
                <p style={{ fontSize: "0.8rem", color: "#64748b", margin: "4px 0 0 0" }}>
                  24/7 navbatchi kardiolog nazorati, qizil signalda 15 daqiqada shifokor qo'ng'irog'i, oyiga 2 marta video-konsultatsiya.
                </p>
              </div>
            </div>

            {/* Payment Provider selector */}
            <div style={{ marginTop: "16px" }}>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                {lang === "ru" ? "Способ оплаты:" : "To'lov usuli:"}
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setPaymentProvider("payme")}
                  style={{
                    padding: "8px",
                    borderRadius: "8px",
                    border: paymentProvider === "payme" ? "2px solid #00cccc" : "1px solid #cbd5e1",
                    background: paymentProvider === "payme" ? "rgba(0, 204, 204, 0.08)" : "#fff",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Payme
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentProvider("click")}
                  style={{
                    padding: "8px",
                    borderRadius: "8px",
                    border: paymentProvider === "click" ? "2px solid #0056b3" : "1px solid #cbd5e1",
                    background: paymentProvider === "click" ? "rgba(0, 86, 179, 0.08)" : "#fff",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Click
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentProvider("uzum")}
                  style={{
                    padding: "8px",
                    borderRadius: "8px",
                    border: paymentProvider === "uzum" ? "2px solid #7000ff" : "1px solid #cbd5e1",
                    background: paymentProvider === "uzum" ? "rgba(112, 0, 255, 0.08)" : "#fff",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Uzum Bank
                </button>
              </div>
            </div>

            {upgradedSuccess && (
              <div style={{ marginTop: "12px", padding: "8px", background: "#ecfdf5", color: "#065f46", borderRadius: "6px", textAlign: "center", fontSize: "0.85rem", fontWeight: 600 }}>
                ✅ To'lov muvaffaqiyatli amalga oshirildi! Tarif faollashtirildi.
              </div>
            )}

            <div style={{ marginTop: "18px", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button className="btn btn-outline" onClick={() => setShowUpgradeModal(false)}>
                Bekor qilish
              </button>
              <button
                className="btn btn-primary"
                onClick={handlePay}
                style={{ background: "linear-gradient(135deg, #2563eb, #1d4ed8)", color: "#fff" }}
              >
                {paymentProvider.toUpperCase()} orqali to'lash
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
