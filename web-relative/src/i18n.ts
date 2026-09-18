import type { I18nKey } from "./lib/types";

export type Lang = "uz" | "ru";

const translations: Record<Lang, Record<string, string>> = {
  uz: {
    // Backend emitted keys
    "state.good": "YAXSHI",
    "state.attention": "E'TIBOR",
    "state.risk": "XAVF",
    "state.no_data": "MA'LUMOT YO'Q",
    "rec.contact_today": "Bugun bog'laning",
    "rec.visit_within_3_days": "3 kun ichida ko'rik tavsiya etiladi",
    "rec.routine_followup": "Reja bo'yicha kuzatuv",
    "rec.continue_monitoring": "Monitoring davom etsin",
    "trend.improving": "Uch kundan beri yaxshilanmoqda",
    "trend.stable": "Holat barqaror saqlanmoqda",
    "trend.worsening": "Holat e'tibor talab qilmoqda",

    // UI phrases
    "app.title": "NAZORAT",
    "app.subtitle": "Yaqin kishi kuzatuv portali",
    "login.title": "Tizimga kirish",
    "login.desc": "Bemor holatini ko'rish uchun telefon va PIN kiriting",
    "login.phone_label": "Telefon raqami",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.pin_label": "6 xonali PIN",
    "login.pin_placeholder": "112233",
    "login.submit": "KIRISH",
    "login.error": "Telefon yoki PIN noto'g'ri",
    "login.hint": "Demo: PIN 112233",
    "no_data.desc": "Soat 45 daqiqadan beri ma'lumot yubormayapti.",
    "vitals.hr": "Puls",
    "vitals.spo2": "SpO₂",
    "vitals.sleep": "Uyqu",
    "vitals.bpm": "bpm",
    "vitals.pct": "%",
    "vitals.hours": "s",
    "updated.just_now": "Hozirgina yangilandi",
    "updated.mins_ago": "{m} daqiqa oldin",
    "updated.hours_ago": "{h} soat oldin",
    "logout": "Chiqish",
  },
  ru: {
    // Backend emitted keys
    "state.good": "В НОРМЕ",
    "state.attention": "ВНИМАНИЕ",
    "state.risk": "ОПАСНОСТЬ",
    "state.no_data": "НЕТ ДАННЫХ",
    "rec.contact_today": "Свяжитесь сегодня",
    "rec.visit_within_3_days": "Осмотр в течение 3 дней",
    "rec.routine_followup": "Плановое наблюдение",
    "rec.continue_monitoring": "Продолжать мониторинг",
    "trend.improving": "Улучшается три дня подряд",
    "trend.stable": "Состояние стабильное",
    "trend.worsening": "Состояние требует внимания",

    // UI phrases
    "app.title": "NAZORAT",
    "app.subtitle": "Портал близких",
    "login.title": "Вход в систему",
    "login.desc": "Введите номер телефона и PIN для просмотра состояния",
    "login.phone_label": "Номер телефона",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.pin_label": "6-значный PIN",
    "login.pin_placeholder": "112233",
    "login.submit": "ВОЙТИ",
    "login.error": "Неверный телефон или PIN",
    "login.hint": "Демо: PIN 112233",
    "no_data.desc": "Часы не передают данные более 45 минут.",
    "vitals.hr": "Пульс",
    "vitals.spo2": "SpO₂",
    "vitals.sleep": "Сон",
    "vitals.bpm": "уд/мин",
    "vitals.pct": "%",
    "vitals.hours": "ч",
    "updated.just_now": "Обновлено только что",
    "updated.mins_ago": "{m} минут назад",
    "updated.hours_ago": "{h} часов назад",
    "logout": "Выйти",
  },
};

export function t(key: I18nKey | string, lang: Lang = "uz", vars?: Record<string, string | number>): string {
  let text = translations[lang]?.[key] || translations["uz"]?.[key] || key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    }
  }
  return text;
}
