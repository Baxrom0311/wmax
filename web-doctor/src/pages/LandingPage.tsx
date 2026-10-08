import React, { useState } from 'react';
import {
  Activity,
  Heart,
  Stethoscope,
  HeartHandshake,
  ArrowRight,
  Sparkles,
  Zap,
  CheckCircle2,
  PlayCircle,
  ChevronDown
} from 'lucide-react';
import type { Lang } from '../i18n';

interface LandingPageProps {
  onNavigate: (route: string) => void;
  lang: Lang;
  onOpenLogin: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onNavigate,
  lang,
  onOpenLogin: _onOpenLogin,
}) => {
  // Simulator State: 'green' | 'amber' | 'red'
  const [simState, setSimState] = useState<'green' | 'amber' | 'red'>('green');
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const t = {
    uz: {
      badge: "O'zbekistonda birinchi masofaviy kardio-monitoring",
      heroTitle: "Siz uzoqdasiz.",
      heroHighlight: "Ular yolg'iz emas.",
      heroSub: "Aqlli soat ota-onangizning puls, SpO₂ va EKG ko'rsatkichlarini 24/7 o'lchaydi. Shifokor kuzatadi, siz esa xotirjam bo'lasiz.",
      btnDoctor: "Shifokor ish stansiyasi",
      btnRelative: "Qarovchi portali",
      btnSlides: "Loyihani ko'rish",
      stat1: "24/7",
      stat1Label: "Doimiy telemetriya",
      stat2: "5 daqiqa",
      stat2Label: "O'lchov darchasi",
      stat3: "100%",
      stat3Label: "Shifokor nazorati",
      
      simTitle: "Aqlli Soat va Tizim Simulyatori",
      simSub: "Soatdagi o'zgarish qanday qilib darhol shifokor va farzandga yetib borishini sinab ko'ring",
      simGreen: "Normal (Yashil)",
      simAmber: "Diqqat (Sariq)",
      simRed: "Xavf (Qizil)",
      
      howTitle: "Tizim Qanday Ishlaydi?",
      howSub: "3 bosqichli uzluksiz himoya zanjiri",
      step1Title: "1. Soat o'lchaydi",
      step1Desc: "Galaxy Watch 5 har 5 daqiqada yurak urishi, qondagi kislorod va harakatni tahlil qiladi.",
      step2Title: "2. Shifokor kuzatadi",
      step2Desc: "Kardiolog stansiyasida AI xavfni 48 soat oldin aniqlaydi va zarur bo'lsa dori dozasini to'g'irlaydi.",
      step3Title: "3. Oila xotirjam",
      step3Desc: "Farzandlar o'z telefonlarida ota-onasining tinch va barqaror ekanligini ko'rib turadi.",

      plansTitle: "Shakllantirilgan Tariflar",
      plansSub: "Oila a'zolari va tibbiyot markazlari uchun qulay yechimlar",
      plan1Title: "Oila / Oddiy",
      plan1Price: "190,000 so'm",
      plan1Per: "/ oyiga",
      plan1Feat: [
        "24/7 Masofaviy telemetriya",
        "Farzandlar uchun mobil portal",
        "Xavfli o'zgarishlarda SMS va Telegram",
        "Haftalik salomatlik xulosasi",
      ],
      plan2Title: "Shifokor Nazorati (Pro)",
      plan2Price: "380,000 so'm",
      plan2Per: "/ oyiga",
      plan2Feat: [
        "Galaxy Watch 5 soati taqdim etiladi",
        "Shaxsiy kardiolog doimiy nazorati",
        "Tez tibbiy yordam (103) avtomatik chaqiruv",
        "AI erta dekompensatsiya prognozi",
      ],
      plan3Title: "Klinikalar uchun",
      plan3Price: "Kelishuv asosida",
      plan3Per: "/ bemor boshiga",
      plan3Feat: [
        "Ko'p shifokorli klinik ish stansiyasi",
        "Barcha bemorlar triaj jurnali",
        "Kasalxonadan keyingi 30 kunlik reabilitatsiya",
        "HIS va CRM integratsiyasi",
      ],
      choosePlan: "Tanlash",
      popular: "Eng ommabop",

      faqTitle: "Ko'p So'raladigan Savollar",
      faqs: [
        {
          q: "Aqlli soat qanday o'lchaydi va qanchalik aniq?",
          a: "Samsung Galaxy Watch 5 va Wear OS sensorlari tibbiy darajadagi fotopletizmografiya (PPG) va bio-impedans datchiklari orqali puls, SpO2 va EKG signallarini uzluksiz qayd etadi."
        },
        {
          q: "Internet uzilib qolsa ma'lumotlar yo'qoladimi?",
          a: "Yo'q, soat xotirasida barcha o'lchovlar saqlanib turadi va internet qayta ulanganda avtomatik ravishda xavfsiz shifrlangan holda klinik bazaga yuklanadi."
        },
        {
          q: "Shifokor qachon aloqaga chiqadi?",
          a: "Agar bemor ko'rsatkichlari individual me'yordan (baseline) chetga chiqsa yoki sariq/qizil triaj yuzaga kelsa, navbatchi kardiolog darhol bemor yoki qarovchi bilan bog'lanadi."
        }
      ]
    },
    ru: {
      badge: "Первая в Узбекистане система телемониторинга сердца",
      heroTitle: "Вы далеко.",
      heroHighlight: "Они не одни.",
      heroSub: "Умные часы 24/7 измеряют пульс, SpO₂ и ЭКГ ваших родителей. Врач наблюдает, а вы спокойны.",
      btnDoctor: "Кабинет врача",
      btnRelative: "Портал опекуна",
      btnSlides: "Презентация проекта",
      stat1: "24/7",
      stat1Label: "Постоянная телеметрия",
      stat2: "5 минут",
      stat2Label: "Окно измерений",
      stat3: "100%",
      stat3Label: "Врачебный надзор",

      simTitle: "Симулятор Умных Часов и Системы",
      simSub: "Узнайте, как изменения на часах мгновенно доходят до врача и семьи",
      simGreen: "Норма (Зеленый)",
      simAmber: "Внимание (Желтый)",
      simRed: "Опасность (Красный)",

      howTitle: "Как Это Работает?",
      howSub: "3-ступенчатая непрерывная цепь безопасности",
      step1Title: "1. Часы измеряют",
      step1Desc: "Galaxy Watch 5 каждые 5 минут оценивает пульс, кислород в крови и двигательную активность.",
      step2Title: "2. Врач наблюдает",
      step2Desc: "В рабочей станции кардиолога ИИ выявляет риски за 48 часов до кризиса.",
      step3Title: "3. Семья спокойна",
      step3Desc: "Дети в мобильном приложении видят статус 'Все в порядке' и спокойны за родителей.",

      plansTitle: "Тарифные Планы",
      plansSub: "Удобные решения для семей и медицинских учреждений",
      plan1Title: "Семья (Базовый)",
      plan1Price: "190 000 сум",
      plan1Per: "/ месяц",
      plan1Feat: [
        "Круглосуточный телемониторинг",
        "Мобильный портал для детей",
        "SMS и Telegram при отклонениях",
        "Еженедельный отчет о здоровье",
      ],
      plan2Title: "Врачебный надзор (Pro)",
      plan2Price: "380 000 сум",
      plan2Per: "/ месяц",
      plan2Feat: [
        "Предоставляются часы Galaxy Watch 5",
        "Персональный врач-кардиолог",
        "Автовызов скорой помощи (103)",
        "ИИ прогноз декомпенсации за 48 часов",
      ],
      plan3Title: "Для Клиник",
      plan3Price: "По договору",
      plan3Per: "/ за пациента",
      plan3Feat: [
        "Многопользовательская станция врача",
        "Триаж-журнал всех пациентов",
        "30-дневная реабилитация после выписки",
        "Интеграция с МИС и CRM",
      ],
      choosePlan: "Выбрать",
      popular: "Популярный",

      faqTitle: "Часто Задаваемые Вопросы",
      faqs: [
        {
          q: "Насколько точны измерения умных часов?",
          a: "Датчики Samsung Galaxy Watch 5 сертифицированы для медицинского скрининга и фиксируют пульс и уровень кислорода с высокой клинической точностью."
        },
        {
          q: "Что произойдет, если отключится интернет?",
          a: "Часы сохраняют данные во внутренней памяти и передают их на сервер сразу после восстановления связи."
        },
        {
          q: "Когда врач выходит на связь?",
          a: "При возникновении желтого или красного статуса дежурный кардиолог немедленно связывается с пациентом или его родственником."
        }
      ]
    },
    en: {
      badge: "Uzbekistan's First Remote Cardiac Telemonitoring Platform",
      heroTitle: "You are away.",
      heroHighlight: "They are not alone.",
      heroSub: "Smartwatches measure your elderly parents' pulse, SpO₂, and ECG 24/7. Cardiologists monitor anomalies, giving you peace of mind.",
      btnDoctor: "Doctor Workstation",
      btnRelative: "Caregiver Portal",
      btnSlides: "View Slides",
      stat1: "24/7",
      stat1Label: "Continuous Telemetry",
      stat2: "5 min",
      stat2Label: "Measurement Window",
      stat3: "100%",
      stat3Label: "Physician Supervised",

      simTitle: "Smartwatch & Clinical Simulator",
      simSub: "Test how vital signs flow in real-time to clinicians and family",
      simGreen: "Normal (Green)",
      simAmber: "Attention (Amber)",
      simRed: "Critical (Red)",

      howTitle: "How It Works",
      howSub: "A seamless 3-step safety chain",
      step1Title: "1. Watch Measures",
      step1Desc: "Galaxy Watch 5 reads heart rate, oxygen saturation, and activity every 5 minutes.",
      step2Title: "2. Clinician Observes",
      step2Desc: "Our AI engine predicts decompensation up to 48 hours in advance for early intervention.",
      step3Title: "3. Family Reassured",
      step3Desc: "Children see real-time 'All Good' status and can check on their parents anytime.",

      plansTitle: "Membership Plans",
      plansSub: "Tailored for families and healthcare institutions",
      plan1Title: "Family (Standard)",
      plan1Price: "190,000 UZS",
      plan1Per: "/ month",
      plan1Feat: [
        "24/7 Continuous telemetry",
        "Family mobile portal",
        "SMS and Telegram critical alerts",
        "Weekly health summary",
      ],
      plan2Title: "Doctor Supervised (Pro)",
      plan2Price: "380,000 UZS",
      plan2Per: "/ month",
      plan2Feat: [
        "Galaxy Watch 5 device included",
        "Dedicated cardiologist supervision",
        "Ambulance (103) dispatch coordination",
        "AI early decompensation prediction",
      ],
      plan3Title: "For Clinics",
      plan3Price: "Custom quote",
      plan3Per: "/ per patient",
      plan3Feat: [
        "Multi-physician clinical workstation",
        "Hospital triage dashboard",
        "30-day post-discharge rehabilitation",
        "HIS & EHR API integration",
      ],
      choosePlan: "Get Started",
      popular: "Most Popular",

      faqTitle: "Frequently Asked Questions",
      faqs: [
        {
          q: "How accurate is the smartwatch?",
          a: "Galaxy Watch 5 utilizes clinical-grade PPG and bio-impedance sensors calibrated against standard Holter monitoring."
        },
        {
          q: "What happens if there is no internet?",
          a: "The watch buffers measurements locally and syncs automatically once connectivity is restored."
        },
        {
          q: "When does the doctor intervene?",
          a: "If amber or red triage conditions are triggered, our duty cardiologist initiates contact within minutes."
        }
      ]
    }
  }[lang];

  // Simulator display data
  const simData = {
    green: {
      image: '/images/3d/watch-green.webp',
      badge: lang === 'uz' ? 'Barqaror (Norma)' : lang === 'ru' ? 'Стабильно (Норма)' : 'Stable (Normal)',
      badgeColor: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
      hr: '72 bpm',
      spo2: '98%',
      pressure: '120 / 80',
      temp: '36.6 °C',
      doctorAction: lang === 'uz' ? "Doimiy avtomatik monitoring davom etmoqda. Shifokor aralashuvi talab etilmaydi." : lang === 'ru' ? "Мониторинг в норме. Вмешательство врача не требуется." : "Routine telemetry active. No clinical intervention needed.",
      familyNotice: lang === 'uz' ? "Otangiz o'zini yaxshi his qilmoqda. Xavf yo'q." : lang === 'ru' ? "Родители чувствуют себя хорошо. Рисков нет." : "Your parent is feeling well. All vitals normal."
    },
    amber: {
      image: '/images/3d/watch-amber.webp',
      badge: lang === 'uz' ? 'Diqqat (Kichik og\'ish)' : lang === 'ru' ? 'Внимание (Отклонение)' : 'Attention (Deviation)',
      badgeColor: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
      hr: '104 bpm',
      spo2: '93%',
      pressure: '145 / 92',
      temp: '37.2 °C',
      doctorAction: lang === 'uz' ? "Kardiologga bildirishnoma yuborildi. Dori ichish jadvali tekshirilmoqda." : lang === 'ru' ? "Уведомление врачу отправлено. Проверяется график приема лекарств." : "Cardiologist notified. Medication adherence being verified.",
      familyNotice: lang === 'uz' ? "Puls biroz ko'tarilgan. Shifokor xabardor qilindi." : lang === 'ru' ? "Пульс немного повышен. Врач уже в курсе." : "Slight pulse elevation. Doctor already notified."
    },
    red: {
      image: '/images/3d/watch-red.webp',
      badge: lang === 'uz' ? 'Xavf (Klinik SOS)' : lang === 'ru' ? 'Опасность (Клинический SOS)' : 'Critical (Clinical SOS)',
      badgeColor: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
      hr: '138 bpm',
      spo2: '86%',
      pressure: '180 / 110',
      temp: '38.1 °C',
      doctorAction: lang === 'uz' ? "Reanimatolog navbatchiligiga qizil signal uzatildi. Tez yordam (103) chaqiruvga tayyor." : lang === 'ru' ? "Красная тревога дежурному реаниматологу. Скорая 103 готова к выезду." : "Red alert sent to ICU staff. 103 ambulance standby triggered.",
      familyNotice: lang === 'uz' ? "Bemorga zudlik bilan shifokor jalb etildi. Telefon orqali bog'lanilmoqda." : lang === 'ru' ? "Врач срочно подключается. Идет вызов пациенту." : "Immediate doctor intervention. Contacting patient now."
    }
  }[simState];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white transition-colors">
      
      {/* -------------------- 1. HERO SECTION -------------------- */}
      <section className="relative pt-12 sm:pt-20 pb-16 sm:pb-28 overflow-hidden">
        {/* Subtle Background Glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-emerald-500/10 via-sky-500/5 to-transparent blur-3xl -z-10 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left Hero Content */}
            <div className="lg:col-span-7 text-left space-y-6">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 text-xs sm:text-sm font-semibold tracking-wide">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>{t.badge}</span>
              </div>

              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.08] text-slate-950 dark:text-white">
                {t.heroTitle}{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 via-teal-500 to-sky-600 dark:from-emerald-400 dark:via-teal-300 dark:to-sky-400">
                  {t.heroHighlight}
                </span>
              </h1>

              <p className="text-base sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed font-normal">
                {t.heroSub}
              </p>

              {/* Action Buttons (High UX Convenience) */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={() => onNavigate('/doctor')}
                  className="px-6 py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm sm:text-base shadow-lg shadow-emerald-600/25 flex items-center gap-2.5 transition transform hover:-translate-y-0.5"
                >
                  <Stethoscope className="w-5 h-5" />
                  <span>{t.btnDoctor}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onNavigate('/r')}
                  className="px-6 py-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-slate-800 dark:text-slate-100 font-bold text-sm sm:text-base hover:bg-slate-100 dark:hover:bg-slate-800 shadow-sm flex items-center gap-2.5 transition transform hover:-translate-y-0.5"
                >
                  <HeartHandshake className="w-5 h-5 text-sky-500" />
                  <span>{t.btnRelative}</span>
                </button>

                <button
                  onClick={() => onNavigate('/pptx')}
                  className="px-4 py-3.5 rounded-2xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-semibold text-sm flex items-center gap-2 transition"
                >
                  <PlayCircle className="w-4 h-4 text-purple-500" />
                  <span>{t.btnSlides}</span>
                </button>
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-200 dark:border-slate-800 max-w-lg">
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{t.stat1}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">{t.stat1Label}</div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{t.stat2}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">{t.stat2Label}</div>
                </div>
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{t.stat3}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">{t.stat3Label}</div>
                </div>
              </div>
            </div>

            {/* Right Hero Image (3D Watch Render) */}
            <div className="lg:col-span-5 flex justify-center relative">
              <div className="relative w-72 sm:w-96 aspect-square rounded-full bg-gradient-to-tr from-emerald-500/20 via-sky-500/20 to-purple-500/20 p-2 shadow-2xl flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border border-emerald-500/30 animate-spin-slow pointer-events-none" />
                <img
                  src="/images/3d/watch-hero.png"
                  alt="WMAX Smartwatch"
                  className="w-full h-auto object-contain filter drop-shadow-2xl transform hover:scale-105 transition duration-500"
                />

                {/* Floating telemetry badge */}
                <div className="absolute -bottom-4 -left-4 sm:left-2 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-500 flex items-center justify-center">
                    <Heart className="w-5 h-5 fill-rose-500 animate-pulse" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span>Puls: 74 bpm</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">SpO₂: 98% · Barqaror</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* -------------------- 2. INTERACTIVE SIMULATOR -------------------- */}
      <section className="py-16 sm:py-24 bg-white dark:bg-slate-900/60 border-y border-slate-200/80 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-400 text-xs font-bold uppercase tracking-wider mb-3">
              <Zap className="w-3.5 h-3.5" />
              <span>Interaktiv Nazorat</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white">
              {t.simTitle}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-base sm:text-lg mt-3">
              {t.simSub}
            </p>

            {/* State Switcher Buttons */}
            <div className="inline-flex p-1.5 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 mt-8 gap-1.5 shadow-inner">
              <button
                onClick={() => setSimState('green')}
                className={`px-4 sm:px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition flex items-center gap-2 ${
                  simState === 'green'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-300" />
                {t.simGreen}
              </button>
              <button
                onClick={() => setSimState('amber')}
                className={`px-4 sm:px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition flex items-center gap-2 ${
                  simState === 'amber'
                    ? 'bg-amber-500 text-white shadow-md shadow-amber-500/30'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-amber-200" />
                {t.simAmber}
              </button>
              <button
                onClick={() => setSimState('red')}
                className={`px-4 sm:px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition flex items-center gap-2 ${
                  simState === 'red'
                    ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-rose-300 animate-ping" />
                {t.simRed}
              </button>
            </div>
          </div>

          {/* Simulator Visual Showcase */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center bg-slate-50 dark:bg-slate-950 p-6 sm:p-10 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl">
            
            {/* 3D Watch Image */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="w-64 sm:w-80 h-auto relative">
                <img
                  src={simData.image}
                  alt="WMAX 3D Telemetry Watch"
                  className="w-full h-auto object-contain filter drop-shadow-2xl transition duration-500 transform hover:scale-105"
                />
              </div>
            </div>

            {/* Live Metrics & Actions */}
            <div className="lg:col-span-7 space-y-6 text-left">
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${simData.badgeColor}`}>
                  {simData.badge}
                </span>
                <span className="text-xs font-mono text-slate-400">Jonli o'lchov: 14:32:05</span>
              </div>

              {/* Vitals Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Puls (HR)</div>
                  <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">{simData.hr}</div>
                </div>
                <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Kislorod (SpO₂)</div>
                  <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">{simData.spo2}</div>
                </div>
                <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Qon bosimi</div>
                  <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">{simData.pressure}</div>
                </div>
                <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Harorat</div>
                  <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-0.5">{simData.temp}</div>
                </div>
              </div>

              {/* Action cards */}
              <div className="space-y-3">
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
                  <Stethoscope className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                      Shifokor javobi
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-300 mt-0.5">
                      {simData.doctorAction}
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
                  <HeartHandshake className="w-5 h-5 text-sky-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                      Oila bildirishnomasi
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-300 mt-0.5">
                      {simData.familyNotice}
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>

        </div>
      </section>

      {/* -------------------- 3. HOW IT WORKS -------------------- */}
      <section className="py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-950 dark:text-white">
              {t.howTitle}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-base sm:text-lg mt-3">
              {t.howSub}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm relative group hover:border-emerald-500/50 transition">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-lg mb-6 border border-emerald-500/20">
                1
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                {t.step1Title}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t.step1Desc}
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm relative group hover:border-emerald-500/50 transition">
              <div className="w-12 h-12 rounded-2xl bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-lg mb-6 border border-teal-500/20">
                2
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                {t.step2Title}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t.step2Desc}
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm relative group hover:border-emerald-500/50 transition">
              <div className="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold text-lg mb-6 border border-sky-500/20">
                3
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                {t.step3Title}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                {t.step3Desc}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------- 4. PRICING PLANS -------------------- */}
      <section className="py-16 sm:py-24 bg-white dark:bg-slate-900/60 border-y border-slate-200/80 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-950 dark:text-white">
              {t.plansTitle}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-base sm:text-lg mt-3">
              {t.plansSub}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            
            {/* Plan 1 */}
            <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex flex-col justify-between">
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">{t.plan1Title}</h3>
                <div className="mt-4 mb-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{t.plan1Price}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 ml-1.5">{t.plan1Per}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {t.plan1Feat.map((f, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-xs sm:text-sm text-slate-600 dark:text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => onNavigate('/r')}
                className="w-full py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-white font-bold text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                {t.choosePlan}
              </button>
            </div>

            {/* Plan 2 (Popular) */}
            <div className="p-8 rounded-3xl bg-slate-900 text-white border-2 border-emerald-500 shadow-xl relative flex flex-col justify-between transform md:-translate-y-2">
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3.5 py-1 rounded-full bg-emerald-500 text-white text-xs font-bold uppercase tracking-wider shadow-md">
                {t.popular}
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">{t.plan2Title}</h3>
                <div className="mt-4 mb-6">
                  <span className="text-3xl font-extrabold text-white font-mono">{t.plan2Price}</span>
                  <span className="text-xs text-emerald-300 ml-1.5">{t.plan2Per}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {t.plan2Feat.map((f, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-xs sm:text-sm text-slate-200">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => onNavigate('/doctor')}
                className="w-full py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/25 transition"
              >
                {t.choosePlan}
              </button>
            </div>

            {/* Plan 3 */}
            <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex flex-col justify-between">
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">{t.plan3Title}</h3>
                <div className="mt-4 mb-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{t.plan3Price}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 ml-1.5">{t.plan3Per}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {t.plan3Feat.map((f, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-xs sm:text-sm text-slate-600 dark:text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => onNavigate('/doctor')}
                className="w-full py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-white font-bold text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                {t.choosePlan}
              </button>
            </div>

          </div>
        </div>
      </section>

      {/* -------------------- 5. FAQ SECTION -------------------- */}
      <section className="py-16 sm:py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-950 dark:text-white">
              {t.faqTitle}
            </h2>
          </div>

          <div className="space-y-3">
            {t.faqs.map((faq, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden transition"
                >
                  <button
                    onClick={() => setActiveFaq(isOpen ? null : idx)}
                    className="w-full p-5 text-left flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-slate-900 dark:text-white focus:outline-none"
                  >
                    <span>{faq.q}</span>
                    <ChevronDown
                      className={`w-5 h-5 text-slate-400 transition transform ${
                        isOpen ? 'rotate-180 text-emerald-500' : ''
                      }`}
                    />
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-5 text-sm text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800/80 pt-3 animate-in fade-in duration-200">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* -------------------- 6. FOOTER -------------------- */}
      <footer className="py-12 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-500" />
            <span className="font-bold text-slate-900 dark:text-white">WMAX Telehealth © 2026</span>
            <span>· Masofaviy Bemor Monitoringi</span>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => onNavigate('/doctor')} className="hover:text-slate-900 dark:hover:text-white transition">Klinika</button>
            <button onClick={() => onNavigate('/r')} className="hover:text-slate-900 dark:hover:text-white transition">Qarovchi</button>
            <button onClick={() => onNavigate('/pptx')} className="hover:text-slate-900 dark:hover:text-white transition">Taqdimot</button>
          </div>
        </div>
      </footer>

    </div>
  );
};
