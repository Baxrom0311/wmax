import React, { useState } from 'react';
import {
  Heart,
  ShieldCheck,
  AlertTriangle,
  Siren,
  PhoneCall,
  Activity,
  BatteryCharging,
  Clock,
  Sparkles,
  ChevronRight,
  LogOut,
  Phone,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  HeartHandshake
} from 'lucide-react';
import type { Lang } from '../i18n';

interface RelativePortalPageProps {
  onNavigate: (route: string) => void;
  lang: Lang;
  relativeUser?: { full_name: string; role: string; patients?: any[] } | null;
  onRelativeLoginSuccess?: (token: string, relative: any) => void;
  onLogoutRelative?: () => void;
}

export const RelativePortalPage: React.FC<RelativePortalPageProps> = ({
  onNavigate,
  lang,
  relativeUser,
  onRelativeLoginSuccess,
  onLogoutRelative,
}) => {
  // Login form state (if not logged in)
  const [phone, setPhone] = useState('+998901110011');
  const [pin, setPin] = useState('112233');
  const [loading, setLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Live vitals / patient telemetry state
  const telemetry = {
    patient_name: "Otabek Ro'zmetov",
    relationship: "Otam (68 yosh)",
    diagnosis: "Yurak yetishmovchiligi (NYHA III)",
    level: "green",
    hr: 74,
    spo2: 98,
    pressure: "120/80",
    temp: 36.6,
    battery: 88,
    worn: true,
    last_reading_at: "Hozir (2 daqiqa oldin)",
    doctor_name: "Doktor Islom Yusupov",
    doctor_phone: "+998901234567",
    nurse_name: "Hamshira Zilola",
    nurse_phone: "+998901234568",
    plan_name: "WMAX Shifokor Nazorati (Pro)",
    plan_until: "15.11.2026",
  };

  const t = {
    uz: {
      portalTitle: "Qarovchi va Oila Portali",
      portalSub: "Ota-onangiz va yaqinlaringiz salomatligini masofadan tinch kuzating",
      loginTitle: "Qarovchi sifatida tizimga kirish",
      loginSub: "Bemorga biriktirilgan telefon raqam va 6 xonali PIN kodni kiriting",
      phoneLabel: "Telefon raqamingiz",
      pinLabel: "6 xonali PIN kod",
      loginBtn: "Portalga kirish",
      demoHint: "Sinov uchun tezkor hisob:",
      demoAccount: "Dilnoza (+998901110011) · PIN: 112233",
      switchPatient: "Nazoratdagi yaqinlar:",
      goodTitle: "Hammasi joyida. Bemor holati barqaror.",
      goodDesc: "Oxirgi o'lchovlar me'yorda. Yurak ritmi va kislorod to'yinishi normada saqlanmoqda.",
      amberTitle: "Diqqat talab holat kuzatildi",
      amberDesc: "Ko'rsatkichlarda kichik og'ish bor. Mas'ul shifokor xabardor qilindi va kuzatmoqda.",
      redTitle: "Zudlik bilan e'tibor talab etiladi!",
      redDesc: "Bemor ko'rsatkichlari xavfli darajaga yetdi. Shifokor bilan zudlikda bog'laning yoki 103 ga qo'ng'iroq qiling.",
      vitalsTitle: "Joriy Telemetriya Ko'rsatkichlari",
      vitalsSub: "Smart Watch Galaxy 5 orqali har 5 daqiqada avtomatik yangilanadi",
      pulse: "Puls (Yurak urishi)",
      spo2: "Kislorod (SpO₂)",
      pressure: "Arterial Bosim",
      temp: "Tana harorati",
      battery: "Soat quvvati",
      wornStatus: "Taqilganlik holati",
      wornYes: "Qo'lda taqilgan",
      wornNo: "Yechilgan",
      quickActions: "Tezkor Shoshilinch Aloqa",
      callDoctor: "Kardiologga qo'ng'iroq",
      callNurse: "Hamshiraga xabar",
      callAmbulance: "Tez Yordam (103)",
      planCard: "Faol Obuna va Qurilma",
      planActive: "Faol (Kafolat mavjud)",
      until: "Muddati:",
      logout: "Chiqish",
      backHome: "Bosh sahifaga",
    },
    ru: {
      portalTitle: "Портал для Членов Семьи и Опекунов",
      portalSub: "Спокойный удаленный контроль за здоровьем пожилых родителей",
      loginTitle: "Вход для опекуна",
      loginSub: "Введите привязанный номер телефона и 6-значный PIN-код",
      phoneLabel: "Номер телефона",
      pinLabel: "6-значный PIN-код",
      loginBtn: "Войти в портал",
      demoHint: "Тестовый аккаунт:",
      demoAccount: "Дильноза (+998901110011) · PIN: 112233",
      switchPatient: "Подопечные:",
      goodTitle: "Все в порядке. Состояние стабильное.",
      goodDesc: "Последние измерения в норме. Ритм сердца и уровень кислорода устойчивы.",
      amberTitle: "Требуется внимание",
      amberDesc: "Зафиксировано небольшое отклонение. Лечащий врач уведомлен.",
      redTitle: "Срочное внимание!",
      redDesc: "Показатели вышли за пределы нормы. Свяжитесь с врачом или вызовите скорую (103).",
      vitalsTitle: "Текущие Показатели Телеметрии",
      vitalsSub: "Автоматически обновляется каждые 5 минут через Galaxy Watch 5",
      pulse: "Пульс",
      spo2: "Кислород (SpO₂)",
      pressure: "Давление",
      temp: "Температура",
      battery: "Заряд часов",
      wornStatus: "Датчик ношения",
      wornYes: "На руке",
      wornNo: "Сняты",
      quickActions: "Экстренная Связь",
      callDoctor: "Звонок кардиологу",
      callNurse: "Сообщение медсестре",
      callAmbulance: "Скорая помощь (103)",
      planCard: "Тариф и Устройство",
      planActive: "Активно (Гарантия)",
      until: "Действует до:",
      logout: "Выйти",
      backHome: "На главную",
    },
    en: {
      portalTitle: "Caregiver & Family Portal",
      portalSub: "Peace-of-mind remote monitoring for your elderly parents",
      loginTitle: "Caregiver Sign In",
      loginSub: "Enter your registered phone number and 6-digit PIN code",
      phoneLabel: "Phone number",
      pinLabel: "6-digit PIN code",
      loginBtn: "Sign In to Portal",
      demoHint: "Quick demo credentials:",
      demoAccount: "Dilnoza (+998901110011) · PIN: 112233",
      switchPatient: "Linked Patients:",
      goodTitle: "All Good. Patient status is stable.",
      goodDesc: "Recent measurements are within target baseline. Heart rate and SpO₂ are optimal.",
      amberTitle: "Attention Needed",
      amberDesc: "Slight deviation detected. Assigned clinician has been alerted.",
      redTitle: "Urgent Attention Required!",
      redDesc: "Critical vital anomaly. Contact the physician immediately or call 103.",
      vitalsTitle: "Current Vital Signs",
      vitalsSub: "Updated automatically every 5 minutes from Galaxy Watch 5",
      pulse: "Heart Rate",
      spo2: "Oxygen (SpO₂)",
      pressure: "Blood Pressure",
      temp: "Skin Temp",
      battery: "Watch Battery",
      wornStatus: "Wearing Sensor",
      wornYes: "On Wrist",
      wornNo: "Removed",
      quickActions: "Quick Emergency Contact",
      callDoctor: "Call Cardiologist",
      callNurse: "Message Nurse",
      callAmbulance: "Emergency 103",
      planCard: "Active Plan & Device",
      planActive: "Active (Covered)",
      until: "Valid until:",
      logout: "Sign Out",
      backHome: "Back to Home",
    }
  }[lang];

  // Handle Caregiver Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLoginError(null);

    try {
      const res = await fetch('/api/v1/auth/relative/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, pin }),
      });
      const data = await res.json();
      if (!res.ok || !data.access_token) {
        throw new Error(data.message || "PIN yoki telefon noto'g'ri");
      }
      localStorage.setItem('wmax_relative_token', data.access_token);
      localStorage.setItem('wmax_relative_name', data.full_name || 'Qarovchi');
      if (onRelativeLoginSuccess) {
        onRelativeLoginSuccess(data.access_token, {
          full_name: data.full_name,
          role: 'relative',
          patients: data.patients || [],
        });
      }
    } catch (err: any) {
      setLoginError(err.message || "Tizimga kirishda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  // If user is not logged in: show modern Shadcn login card
  if (!relativeUser) {
    return (
      <div className="min-h-[85vh] flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8">
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 mx-auto flex items-center justify-center mb-3 border border-sky-500/20">
              <HeartHandshake className="w-6 h-6" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {t.loginTitle}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              {t.loginSub}
            </p>
          </div>

          {loginError && (
            <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-600 dark:text-rose-300 text-xs sm:text-sm flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                {t.phoneLabel}
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+998901110011"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                {t.pinLabel}
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  maxLength={6}
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="112233"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm tracking-widest font-mono bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm shadow-md shadow-sky-600/20 flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span>{t.loginBtn}</span>
              )}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 text-center">
            <span className="text-xs text-slate-400 block mb-2">{t.demoHint}</span>
            <button
              type="button"
              onClick={() => {
                setPhone('+998901110011');
                setPin('112233');
              }}
              className="px-3 py-1.5 rounded-lg bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-300 border border-sky-200 dark:border-sky-800/40 text-xs font-semibold hover:bg-sky-100 transition"
            >
              👥 {t.demoAccount}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Logged in: Main Caregiver Dashboard
  const statusColor = telemetry.level === 'red'
    ? {
        border: 'border-rose-500/40',
        bg: 'bg-rose-50 dark:bg-rose-950/20',
        badge: 'bg-rose-500 text-white',
        icon: <Siren className="w-8 h-8 text-rose-600 dark:text-rose-400 animate-bounce" />,
        title: t.redTitle,
        desc: t.redDesc,
      }
    : telemetry.level === 'amber'
    ? {
        border: 'border-amber-500/40',
        bg: 'bg-amber-50 dark:bg-amber-950/20',
        badge: 'bg-amber-500 text-white',
        icon: <AlertTriangle className="w-8 h-8 text-amber-600 dark:text-amber-400" />,
        title: t.amberTitle,
        desc: t.amberDesc,
      }
    : {
        border: 'border-emerald-500/40',
        bg: 'bg-emerald-50 dark:bg-emerald-950/20',
        badge: 'bg-emerald-600 text-white',
        icon: <ShieldCheck className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />,
        title: t.goodTitle,
        desc: t.goodDesc,
      };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Top Header Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold text-lg">
              {relativeUser.full_name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {relativeUser.full_name}
                </h1>
                <span className="px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-400 text-xs font-semibold">
                  Qarovchi
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Bemor: <span className="font-semibold text-slate-800 dark:text-slate-200">{telemetry.patient_name}</span> ({telemetry.relationship})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end md:self-auto">
            <button
              onClick={() => onNavigate('/')}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              {t.backHome}
            </button>
            {onLogoutRelative && (
              <button
                onClick={onLogoutRelative}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>{t.logout}</span>
              </button>
            )}
          </div>
        </div>

        {/* ----------------- PEACE OF MIND HERO CARD ----------------- */}
        <div className={`p-6 sm:p-8 rounded-3xl border-2 ${statusColor.border} ${statusColor.bg} shadow-lg transition-all`}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-2xl bg-white dark:bg-slate-900 shadow-sm shrink-0">
                {statusColor.icon}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${statusColor.badge}`}>
                    {telemetry.level === 'green' ? 'Barqaror' : telemetry.level === 'amber' ? 'Diqqat' : 'SOS Xavf'}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {telemetry.last_reading_at}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white">
                  {statusColor.title}
                </h2>
                <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 mt-1 max-w-2xl">
                  {statusColor.desc}
                </p>
              </div>
            </div>

            {/* Wearable sensor status */}
            <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 text-xs space-y-2 shrink-0 w-full sm:w-auto">
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">{t.wornStatus}:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  {t.wornYes}
                </span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">{t.battery}:</span>
                <span className="font-bold font-mono text-slate-800 dark:text-slate-200 flex items-center gap-1">
                  <BatteryCharging className="w-3.5 h-3.5 text-emerald-500" />
                  {telemetry.battery}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ----------------- LIVE VITALS GRID ----------------- */}
        <div>
          <div className="mb-3">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-500" />
              <span>{t.vitalsTitle}</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">{t.vitalsSub}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Heart Rate */}
            <div className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{t.pulse}</span>
                <Heart className="w-4 h-4 text-rose-500 fill-rose-500" />
              </div>
              <div className="my-3">
                <span className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">{telemetry.hr}</span>
                <span className="text-xs text-slate-400 ml-1">bpm</span>
              </div>
              <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                Norma: 60 - 85 bpm
              </div>
            </div>

            {/* SpO2 */}
            <div className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{t.spo2}</span>
                <Activity className="w-4 h-4 text-sky-500" />
              </div>
              <div className="my-3">
                <span className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">{telemetry.spo2}</span>
                <span className="text-xs text-slate-400 ml-1">%</span>
              </div>
              <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                Norma: 95% - 99%
              </div>
            </div>

            {/* Pressure */}
            <div className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{t.pressure}</span>
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="my-3">
                <span className="text-2xl sm:text-3xl font-extrabold font-mono text-slate-900 dark:text-white">{telemetry.pressure}</span>
                <span className="text-xs text-slate-400 ml-1">mmHg</span>
              </div>
              <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                Norma: 120 / 80
              </div>
            </div>

            {/* Skin Temp */}
            <div className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{t.temp}</span>
                <Sparkles className="w-4 h-4 text-amber-500" />
              </div>
              <div className="my-3">
                <span className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">{telemetry.temp}</span>
                <span className="text-xs text-slate-400 ml-1">°C</span>
              </div>
              <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                Norma: 36.4 - 37.0 °C
              </div>
            </div>
          </div>
        </div>

        {/* ----------------- EMERGENCY ACTION BAR (UX OPTIMIZED) ----------------- */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href={`tel:${telemetry.doctor_phone}`}
            className="p-5 rounded-3xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center justify-between shadow-lg shadow-emerald-600/20 transition transform hover:-translate-y-0.5"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-white/10">
                <PhoneCall className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-emerald-100 font-medium">{t.callDoctor}</div>
                <div className="text-sm font-extrabold">{telemetry.doctor_name}</div>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-emerald-200" />
          </a>

          <a
            href={`tel:${telemetry.nurse_phone}`}
            className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-900 dark:text-white font-bold flex items-center justify-between shadow-sm transition transform hover:-translate-y-0.5"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-sky-500/10 text-sky-500">
                <PhoneCall className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">{t.callNurse}</div>
                <div className="text-sm font-extrabold">{telemetry.nurse_name}</div>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400" />
          </a>

          <a
            href="tel:103"
            className="p-5 rounded-3xl bg-rose-600 hover:bg-rose-500 text-white font-bold flex items-center justify-between shadow-lg shadow-rose-600/20 transition transform hover:-translate-y-0.5"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-white/10">
                <Siren className="w-5 h-5 text-white animate-pulse" />
              </div>
              <div>
                <div className="text-xs text-rose-100 font-medium">Favqulodda Chaqiruv</div>
                <div className="text-sm font-extrabold">{t.callAmbulance}</div>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-rose-200" />
          </a>
        </div>

        {/* ----------------- ACTIVE PLAN CARD ----------------- */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900 dark:text-white">
                {telemetry.plan_name}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {t.until} {telemetry.plan_until} · {t.planActive}
              </div>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold border border-emerald-500/20">
            Kafolatlangan
          </span>
        </div>

      </div>
    </div>
  );
};
