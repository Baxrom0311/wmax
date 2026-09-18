import type { I18nKey } from "./lib/types";

export type Lang = "uz" | "ru";

const translations: Record<Lang, Record<string, string>> = {
  uz: {
    "app.title": "NAZORAT",
    "app.doctor_panel": "NAZORAT · Shifokor Paneli",
    "login.title": "Shifokor va Hamshiralar Tizimi",
    "login.desc": "Bemorlar monitoringi va aktiv chaqiruvlarni boshqarish",
    "login.phone_label": "Telefon raqami",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.password_label": "Parol",
    "login.password_placeholder": "••••••••",
    "login.submit": "Tizimga kirish",
    "login.demo": "Demo hisob: +998901234567 / nazorat123",
    "login.error": "Telefon yoki parol xato",
    "logout": "Chiqish",

    // Backend emitted keys
    "state.good": "Yaxshi",
    "state.attention": "E'tibor",
    "state.risk": "Xavf",
    "state.no_data": "Ma'lumot yo'q",
    "rec.contact_today": "Bugun bog'laning",
    "rec.visit_within_3_days": "3 kun ichida ko'rik tavsiya etiladi",
    "rec.routine_followup": "Reja bo'yicha kuzatuv",
    "rec.continue_monitoring": "Monitoring davom etsin",
    "trend.improving": "Yaxshilanmoqda",
    "trend.stable": "Barqaror",
    "trend.worsening": "Yomonlashmoqda",

    // Dashboard UI
    "patients.attention_count": "Bugun e'tibor talab qiladi — {n} bemor",
    "patients.all_patients": "Barcha bemorlar",
    "patients.th_status": "Holat",
    "patients.th_fio": "F.I.O",
    "patients.th_age_sex": "Yosh",
    "patients.th_district": "Tuman",
    "patients.th_diagnosis": "Tashxis",
    "patients.th_trend": "Trend",
    "patients.th_deviations": "Chetlanishlar",
    "patients.th_task": "Topshiriq / Chaqiruv",
    "patients.th_action": "Amal",
    "patients.btn_view": "Ko'rish",
    "patients.btn_confirm": "Tasdiqlash",
    "patients.task_active_call": "Aktiv chaqiruv",
    "patients.task_red_alert": "Qizil signal",
    "patients.hours_left": "{h} soat qoldi",
    "patients.overdue": "Muddati o'tdi",
    "patients.done": "Bajarildi",

    // Detail UI
    "detail.back": "← Bemorlar ro'yxatiga qaytish",
    "detail.clinical_summary": "Klinik ma'lumotlar",
    "detail.phase": "Bosqich",
    "detail.phase_calib": "Texnik sozlash",
    "detail.phase_learning": "O'rganish rejimi (7 kun)",
    "detail.phase_full": "To'liq nazorat rejimi",
    "detail.approve_baseline": "Shaxsiy normani tasdiqlash",
    "detail.baseline_approved": "Norma tasdiqlangan",
    "detail.vitals_history": "7 kunlik ko'p parametrli monitoring",
    "detail.baseline_legend": "Me'yoriy koridor (Baseline)",
    "detail.alerts_history": "Signallar jurnali",
    "detail.anomaly_advisory": "Model anomaliya qayd etdi (advisory): {score}%",
    "detail.active_call_card": "Aktiv chaqiruv topshirig'i (11-muammo)",
    "detail.active_call_desc": "Bemor statsionardan chiqarilgan, 24 soatlik patronaj ko'rigi talab etiladi.",
    "detail.confirm_visit": "Patronajni tasdiqlash",
    "confirm_modal.title": "Patronaj ko'rigini tasdiqlash",
    "confirm_modal.note_label": "Tashrif xulosasi va tavsiyalar:",
    "confirm_modal.placeholder": "Bemor ahvoli qoniqarli, dori rejimi qayta ko'rildi...",
    "confirm_modal.submit": "Tasdiqlash",
    "confirm_modal.cancel": "Bekor qilish",
  },
  ru: {
    "app.title": "НАЗОРАТ",
    "app.doctor_panel": "НАЗОРАТ · Панель Врача",
    "login.title": "Система для Врачей и Медсестер",
    "login.desc": "Мониторинг пациентов и активные вызовы",
    "login.phone_label": "Номер телефона",
    "login.phone_placeholder": "+998 90 123 45 67",
    "login.password_label": "Пароль",
    "login.password_placeholder": "••••••••",
    "login.submit": "Войти в систему",
    "login.demo": "Демо: +998901234567 / nazorat123",
    "login.error": "Неверный телефон или пароль",
    "logout": "Выйти",

    // Backend emitted keys
    "state.good": "В норме",
    "state.attention": "Внимание",
    "state.risk": "Опасность",
    "state.no_data": "Нет данных",
    "rec.contact_today": "Свяжитесь сегодня",
    "rec.visit_within_3_days": "Осмотр в течение 3 дней",
    "rec.routine_followup": "Плановое наблюдение",
    "rec.continue_monitoring": "Продолжать мониторинг",
    "trend.improving": "Улучшается",
    "trend.stable": "Стабильно",
    "trend.worsening": "Ухудшается",

    // Dashboard UI
    "patients.attention_count": "Сегодня требуют внимания — {n} пациентов",
    "patients.all_patients": "Все пациенты",
    "patients.th_status": "Статус",
    "patients.th_fio": "Ф.И.О",
    "patients.th_age_sex": "Возраст",
    "patients.th_district": "Район",
    "patients.th_diagnosis": "Диагноз",
    "patients.th_trend": "Тренд",
    "patients.th_deviations": "Отклонения",
    "patients.th_task": "Задача / Вызов",
    "patients.th_action": "Действие",
    "patients.btn_view": "Просмотр",
    "patients.btn_confirm": "Подтвердить",
    "patients.task_active_call": "Активный вызов",
    "patients.task_red_alert": "Красный сигнал",
    "patients.hours_left": "осталось {h}ч",
    "patients.overdue": "Просрочено",
    "patients.done": "Выполнено",

    // Detail UI
    "detail.back": "← Назад к списку пациентов",
    "detail.clinical_summary": "Клинические данные",
    "detail.phase": "Фаза",
    "detail.phase_calib": "Калибровка",
    "detail.phase_learning": "Режим обучения (7 дней)",
    "detail.phase_full": "Полный контроль",
    "detail.approve_baseline": "Утвердить норму",
    "detail.baseline_approved": "Норма утверждена",
    "detail.vitals_history": "7-дневный многопараметрический мониторинг",
    "detail.baseline_legend": "Индивидуальный коридор (Baseline)",
    "detail.alerts_history": "Журнал оповещений",
    "detail.anomaly_advisory": "Модель зафиксировала аномалию: {score}%",
    "detail.active_call_card": "Активный вызов (Проблема 11)",
    "detail.active_call_desc": "Пациент выписан, требуется 24-часовой патронажный осмотр.",
    "detail.confirm_visit": "Подтвердить осмотр",
    "confirm_modal.title": "Подтверждение патронажного визита",
    "confirm_modal.note_label": "Заключение врача и рекомендации:",
    "confirm_modal.placeholder": "Состояние стабильное, скорректирован прием препаратов...",
    "confirm_modal.submit": "Подтвердить",
    "confirm_modal.cancel": "Отмена",
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
