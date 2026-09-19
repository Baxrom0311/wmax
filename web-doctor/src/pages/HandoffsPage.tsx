import React from "react";
import type { Lang } from "../i18n";

interface HandoffsPageProps {
  lang: Lang;
}

const COPY = {
  uz: {
    title: "Topshirilgan bemorlar",
    lead: "Statsionardan chiqarilgan bemor hududiy hamshira va oilaviy shifokorga shu yerda topshiriladi.",
    emptyTitle: "Hozircha topshirilgan bemor yo'q",
    emptyBody:
      "Bemor chiqarilganda u avtomatik ravishda yashash hududiga biriktirilgan hamshiraga yuboriladi va shu ro'yxatda paydo bo'ladi.",
    steps: [
      "Chiqarish — statsionar shifokori bemorni chiqaradi",
      "Yo'naltirish — tizim mahalla bo'yicha mas'ul hamshirani topadi",
      "Xabar — hamshiraga Telegram orqali bemor kartasi boradi",
      "Qabul — hamshira tasdiqlaydi, 24 soatlik taymer boshlanadi",
    ],
  },
  ru: {
    title: "Переданные пациенты",
    lead: "Выписанный из стационара пациент передаётся участковой медсестре и семейному врачу здесь.",
    emptyTitle: "Переданных пациентов пока нет",
    emptyBody:
      "При выписке пациент автоматически направляется медсестре по месту жительства и появляется в этом списке.",
    steps: [
      "Выписка — врач стационара выписывает пациента",
      "Маршрутизация — система находит ответственную медсестру по махалле",
      "Уведомление — карта пациента уходит медсестре в Telegram",
      "Приём — медсестра подтверждает, запускается 24-часовой таймер",
    ],
  },
  en: {
    title: "Handed-over patients",
    lead: "A patient discharged from hospital is handed over to the district nurse and family doctor here.",
    emptyTitle: "No handovers yet",
    emptyBody:
      "On discharge a patient is routed automatically to the nurse responsible for their address and appears in this list.",
    steps: [
      "Discharge — the hospital doctor discharges the patient",
      "Routing — the system finds the nurse responsible for the mahalla",
      "Notification — the patient card reaches the nurse on Telegram",
      "Acceptance — the nurse confirms and the 24-hour timer starts",
    ],
  },
} as const;

export const HandoffsPage: React.FC<HandoffsPageProps> = ({ lang }) => {
  const c = COPY[lang] ?? COPY.uz;

  return (
    <div className="doc-container">
      <div className="page-head">
        <h1 className="page-title">{c.title}</h1>
        <p className="page-lead">{c.lead}</p>
      </div>

      <div className="handoff-empty">
        <h2 className="handoff-empty-title">{c.emptyTitle}</h2>
        <p className="handoff-empty-body">{c.emptyBody}</p>

        {/* The handover genuinely is a sequence, so the steps are numbered. */}
        <ol className="handoff-flow">
          {c.steps.map((step, i) => (
            <li key={step} className="handoff-flow-step">
              <span className="handoff-flow-num">{i + 1}</span>
              <span className="handoff-flow-text">{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
};
