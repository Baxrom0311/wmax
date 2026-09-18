import type { I18nKey } from "./lib/types";

export type Lang = "uz" | "ru";

const translations: Record<Lang, Record<string, string>> = {
  uz: {
    // Backend emitted keys
    "state.good": "YAXSHI",
    "state.attention": "E'TIBOR TALAB",
    "state.risk": "YUQORI XAVF",
    "state.no_data": "MA'LUMOT YO'Q",
    "rec.contact_today": "Bugun shifokor bilan bog'laning",
    "rec.visit_within_3_days": "3 kun ichida ko'rik tavsiya etiladi",
    "rec.routine_followup": "Reja bo'yicha kuzatuv",
    "rec.continue_monitoring": "Monitoring davom etsin",
    "trend.improving": "Uch kundan beri yaxshilanmoqda",
    "trend.stable": "Holat barqaror saqlanmoqda",
    "trend.worsening": "Salbiy tendensiya kuzatilmoqda",

    // Header & Login
    "app.title": "NAZORAT",
    "app.subtitle": "Qarovchi Portali (Pro)",
    "login.title": "Qarovchi Portali",
    "login.desc": "Bemorlaringiz salomatligini masofadan nazorat qiling",
    "login.phone_label": "Telefon raqamingiz",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.pin_label": "6 xonali PIN kod",
    "login.pin_placeholder": "112233",
    "login.submit": "KIRISH",
    "login.error": "Telefon yoki PIN noto'g'ri",
    "login.hint": "Demo kirish: PIN 112233",
    "logout": "Chiqish",

    // Multi-Patient Switcher
    "patients.title": "Kuzatuvdagi yaqinlaringiz",
    "patients.select": "Bemor",

    // Hero & AI Prognosis
    "hero.composite_deviation": "Kompozit og'ish",
    "hero.prognosis_title": "AI 72-soatlik Erta Ogohlantirish Prognozi",
    "hero.risk_prob": "Dekommutatsiya xavfi",
    "hero.early_warning": "{h} soat oldin ogohlantirish",
    "hero.risk_low": "Past",
    "hero.risk_moderate": "O'rta",
    "hero.risk_high": "Yuqori",

    // Root-Cause Problems
    "problems.title": "Aniqlangan Asosiy Muammolar Tahlili",
    "problems.none": "Hozirda shaxsiy me'yordan sezilarli og'ishlar yo'q",
    "problems.current": "Joriy qiymat",
    "problems.baseline": "Shaxsiy me'yor",
    "problems.deviation": "Og'ish",

    // Interactive Metrics & Corridors
    "metrics.title": "Shaxsiy Me'yor Koridorlari Dinamikasi",
    "metrics.range_24h": "24 soat",
    "metrics.range_3d": "3 kun",
    "metrics.range_7d": "7 kun",
    "metrics.tab_hr": "Puls",
    "metrics.tab_spo2": "SpO₂",
    "metrics.tab_rmssd": "HRV Stress",
    "metrics.tab_temp": "Harorat",
    "metrics.tab_rr": "Nafas",
    "metrics.tab_sleep": "Uyqu",
    "metrics.baseline_corridor": "Shaxsiy me'yor koridori",
    "metrics.reading": "O'lchov",
    "metrics.deviation_zone": "Og'ish zonasi",

    // Doctor Contact & Actions
    "actions.title": "Shifokor Tavsiyalari va Aloqa",
    "actions.doctor_name": "Biriktirilgan shifokor",
    "actions.call_doctor": "Qo'ng'iroq qilish",
    "actions.telegram": "Telegram",
    "actions.emergency": "Tez yordam (103)",
    "actions.active_call_status": "Aktiv chaqiruv holati",
    "actions.active_call_scheduled": "Patronaj ko'rigi rejalashtirilgan",

    // No Data Protection
    "no_data.title": "Soatdan ma'lumot kelmayapti",
    "no_data.desc": "Aqlli soat 45 daqiqadan beri ma'lumot uzatmayapti. Soat yechilgan yoki batareya quvvati tugagan bo'lishi mumkin. Iltimos, bemor bilan bog'lanib, soatni taqishini iltimos qiling.",

    // Time Formatting
    "updated.just_now": "Hozirgina yangilandi",
    "updated.mins_ago": "{m} daqiqa oldin",
    "updated.hours_ago": "{h} soat oldin",
  },
  ru: {
    // Backend emitted keys
    "state.good": "В НОРМЕ",
    "state.attention": "ТРЕБУЕТ ВНИМАНИЯ",
    "state.risk": "ВЫСОКИЙ РИСК",
    "state.no_data": "НЕТ ДАННЫХ",
    "rec.contact_today": "Свяжитесь с врачом сегодня",
    "rec.visit_within_3_days": "Рекомендован осмотр в течение 3 дней",
    "rec.routine_followup": "Плановое наблюдение",
    "rec.continue_monitoring": "Продолжать мониторинг",
    "trend.improving": "Улучшается три дня подряд",
    "trend.stable": "Состояние стабильное",
    "trend.worsening": "Отрицательная динамика",

    // Header & Login
    "app.title": "НАЗОРАТ",
    "app.subtitle": "Портал Близких (Pro)",
    "login.title": "Портал Близких",
    "login.desc": "Дистанционный мониторинг здоровья близких",
    "login.phone_label": "Номер телефона",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.pin_label": "6-значный PIN",
    "login.pin_placeholder": "112233",
    "login.submit": "ВОЙТИ",
    "login.error": "Неверный телефон или PIN",
    "login.hint": "Демо: PIN 112233",
    "logout": "Выйти",

    // Multi-Patient Switcher
    "patients.title": "Наблюдаемые близкие",
    "patients.select": "Пациент",

    // Hero & AI Prognosis
    "hero.composite_deviation": "Композитное отклонение",
    "hero.prognosis_title": "AI Прогноз раннего предупреждения на 72ч",
    "hero.risk_prob": "Риск декомпенсации",
    "hero.early_warning": "Предупреждение за {h} часов",
    "hero.risk_low": "Низкий",
    "hero.risk_moderate": "Умеренный",
    "hero.risk_high": "Высокий",

    // Root-Cause Problems
    "problems.title": "Анализ выявленных ключевых проблем",
    "problems.none": "Значительных отклонений от нормы не зафиксировано",
    "problems.current": "Текущее значение",
    "problems.baseline": "Личная норма",
    "problems.deviation": "Отклонение",

    // Interactive Metrics & Corridors
    "metrics.title": "Динамика с индивидуальным коридором нормы",
    "metrics.range_24h": "24 часа",
    "metrics.range_3d": "3 дня",
    "metrics.range_7d": "7 дней",
    "metrics.tab_hr": "Пульс",
    "metrics.tab_spo2": "SpO₂",
    "metrics.tab_rmssd": "HRV Стресс",
    "metrics.tab_temp": "Температура",
    "metrics.tab_rr": "Дыхание",
    "metrics.tab_sleep": "Сон",
    "metrics.baseline_corridor": "Индивидуальный коридор нормы",
    "metrics.reading": "Измерение",
    "metrics.deviation_zone": "Зона отклонения",

    // Doctor Contact & Actions
    "actions.title": "Рекомендации врача и связь",
    "actions.doctor_name": "Прикрепленный врач",
    "actions.call_doctor": "Позвонить врачу",
    "actions.telegram": "Telegram",
    "actions.emergency": "Скорая помощь (103)",
    "actions.active_call_status": "Статус активного вызова",
    "actions.active_call_scheduled": "Запланирован патронажный осмотр",

    // No Data Protection
    "no_data.title": "Часы не передают данные",
    "no_data.desc": "Часы не передают данные более 45 минут. Возможно, они сняты или разряжены. Пожалуйста, свяжитесь с близким и попросите надеть часы.",

    // Time Formatting
    "updated.just_now": "Обновлено только что",
    "updated.mins_ago": "{m} минут назад",
    "updated.hours_ago": "{h} часов назад",
  },
};

export function t(
  key: I18nKey | string,
  lang: Lang = "uz",
  vars?: Record<string, string | number>
): string {
  let text = translations[lang]?.[key] || translations["uz"]?.[key] || key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    }
  }
  return text;
}
