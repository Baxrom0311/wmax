import React, { useState } from 'react';
import {
  Rocket,
  AlertCircle,
  CheckCircle2,
  Compass,
  Cpu,
  Bot,
  Terminal,
  Play,
  ArrowRight,
  ExternalLink,
  Sparkles,
  ShieldCheck,
  Activity,
  Send,
  Database
} from 'lucide-react';
import type { Lang } from '../i18n';
import { TEAM } from './pitch/content';

interface AifuPageProps {
  onNavigate: (route: string) => void;
  lang: Lang;
}

export const AifuPage: React.FC<AifuPageProps> = ({ onNavigate, lang }) => {
  // Mini AI chat state
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([
    {
      sender: 'ai',
      text: lang === 'ru'
        ? "Здравствуйте! Я ИИ-ассистент WMAX. Могу рассказать о нашей методологии предиктивной кардиологии, архитектуре и технологиях Pitch Day 3.0. Что вас интересует?"
        : lang === 'en'
        ? "Hello! I am the WMAX AI clinical assistant. I can explain our predictive cardiology methodology, system architecture, or tech stack for Pitch Day 3.0. What would you like to know?"
        : "Assalomu alaykum! Men WMAX AI klinik assistentiman. Pitch Day 3.0 uchun tayyorlangan kardio-monitoring arxitekturamiz, AI algoritmlarimiz va jamoamiz haqida so'rashingiz mumkin."
    }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const sampleQuestions = [
    lang === 'ru' ? "Как работает ИИ-ядро?" : lang === 'en' ? "How does the AI core work?" : "AI yadro qanday ishlaydi?",
    lang === 'ru' ? "Какие носимые устройства поддерживаются?" : lang === 'en' ? "Which wearable devices are supported?" : "Qaysi aqlli soatlar tizimga ulanadi?",
    lang === 'ru' ? "Как защищены персональные медицинские данные?" : lang === 'en' ? "How are personal medical health data secured?" : "Bemorlarning tibbiy ma'lumotlari qanday himoyalangan?",
    lang === 'ru' ? "Какая роль родственников и опекунов?" : lang === 'en' ? "What is the role of family caregivers?" : "Oila a'zolari va qarovchilar roli qanday?"
  ];

  const handleSendMessage = (q?: string) => {
    const textToSend = q || inputVal;
    if (!textToSend.trim()) return;

    const userMsg = textToSend.trim();
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    if (!q) setInputVal('');
    setIsTyping(true);

    setTimeout(() => {
      let reply = "";
      const lower = userMsg.toLowerCase();
      if (lower.includes('bashorat') || lower.includes('прогноз') || lower.includes('predict')) {
        reply = lang === 'ru'
          ? "WMAX сначала изучает личную норму пациента, затем сравнивает новые измерения по z-score с учётом циркадного ритма и сигнализирует медсестре при устойчивом отклонении. Это не диагноз; точность будет проверена в пилоте."
          : lang === 'en'
          ? "WMAX first learns each patient's personal baseline, then compares new readings with a circadian-aware z-score and alerts the nurse on sustained deviation. It is not a diagnosis; accuracy will be tested in the pilot."
          : "WMAX avval har bir bemorning shaxsiy normasini o'rganadi, keyin yangi o'lchovlarni sirkadian ritmni hisobga olgan z-score bilan solishtiradi va barqaror og'ishda hamshiraga signal beradi. Bu tashxis emas; aniqlik pilotda tekshiriladi.";
      } else if (lower.includes('soat') || lower.includes('устройств') || lower.includes('device') || lower.includes('watch')) {
        reply = lang === 'ru'
          ? "Мы поддерживаем Samsung Galaxy Watch (Wear OS). Версия для Apple Watch запланирована на этапе MVP."
          : lang === 'en'
          ? "We support Samsung Galaxy Watch (Wear OS) today. An Apple Watch version is planned for the MVP."
          : "Hozir Samsung Galaxy Watch (Wear OS). Apple Watch versiyasi MVP bosqichida rejalashtirilgan.";
      } else if (lower.includes('himoya') || lower.includes('защит') || lower.includes('secur')) {
        reply = lang === 'ru'
          ? "Пациент сам даёт согласие и может отозвать его в любой момент. Передача данных идёт по HTTPS, в PostgreSQL используются RLS (Row Level Security) и ограниченные роли."
          : lang === 'en'
          ? "Patients give consent and can revoke it at any time. Data travels over HTTPS, and PostgreSQL uses Row Level Security (RLS) and restricted roles."
          : "Bemor kuzatuvga o'zi rozilik beradi va istalgan vaqtda bekor qila oladi. Ma'lumot HTTPS orqali uzatiladi, PostgreSQL da RLS (qatorlar darajasida kirish nazorati) va cheklangan rollar ishlatiladi.";
      } else {
        reply = lang === 'ru'
          ? "Отличный вопрос! WMAX объединяет носимые датчики, рабочее место кардиолога с ИИ-триажем и мобильный портал для близких, чтобы ухудшение замечали раньше."
          : lang === 'en'
          ? "Great question! WMAX bridges consumer wearables, an AI cardiologist triage workstation, and a peace-of-mind caregiver app, so deterioration is noticed earlier."
          : "Ajoyib savol! WMAX aqlli soatlar, sun'iy intellektli shifokor ish stansiyasi va qarovchilar mobil ilovasini bitta xavfsizlik zanjiriga birlashtiradi.";
      }
      setMessages(prev => [...prev, { sender: 'ai', text: reply }]);
      setIsTyping(false);
    }, 600);
  };

  const t = {
    uz: {
      badge: "Pitch Day 3.0 · 1-Bosqich Konkurs Taqdimoti",
      heroTitle: "WMAX — Masofaviy Kardio-Monitoring va AI Tizimi",
      heroSub: "Kasalxonadan chiqqan bemorni 30 kun davomida aqlli soat orqali kuzatib, oilaviy shifokor va yaqinlarini bog'laydigan uzluksiz parvarish zanjiri.",
      btnDemo: "Jonli Video & Prototip Demoni Ko'rish",
      btnApi: "API Hujjatlari (OpenAPI)",
      btnClinic: "Shifokor Stansiyasini Sinash",
      
      sec1Title: "1. Muammo → Yechim",
      sec1Sub: "O'zbekistondagi tibbiy holat va WMAX yechimi",
      p1Title: "Kritik Muammo",
      p1Desc: "O'zbekistonda o'limlarning 57% i yurak-qon tomir kasalliklari sababli (O'zbekiston statistika agentligi, 2024). Bemorlar kasalxonadan chiqqach, ularning holati nazoratsiz qoladi, shifokorlar esa faqat infarkt yoki krizis yuz bergandagina xabar topadi.",
      s1Title: "Bizning Yechim",
      s1Desc: "WMAX — aqlli soat orqali 24/7 kuzatuv, har bir bemorning shaxsiy normasidan barqaror og'ishda shifokor va oilaga signal yuboruvchi platforma. Tizim tashxis qo'ymaydi, qarorni shifokor qabul qiladi.",

      sec2Title: "2. Jamoa",
      sec2Sub: "Jamoa 0xDEAD",
      
      sec3Title: "3. Nima uchun Bizning Jamoa Buni Hal Qila Oladi?",
      sec3Sub: "Ishlaydigan prototip, mahalliy sharoitni bilish va halol yondashuv",

      sec4Title: "4. Rivojlanish Yo'l Xaritasi (Roadmap)",
      sec4Sub: "Idea'dan to To'liq Bozorga Chiqishgacha (Idea → Prototype → MVP → Launched)",

      sec5Title: "5. Texnik Amalga Oshirish & AI Arxitekturasi",
      sec5Sub: "Texnologiyalar steki, AI vositalari va biofizik hisoblash tizimi",

      sec6Title: "6. Interaktiv AI-Chatbot & API Access",
      sec6Sub: "Pitch Day hay'ati uchun tezkor savol-javob va integratsiya imkoniyatlari",
    },
    ru: {
      badge: "Pitch Day 3.0 · Этап 1 Конкурсная Презентация",
      heroTitle: "WMAX — Удаленный Кардиомониторинг и ИИ-Система",
      heroSub: "Непрерывная цепочка ухода: 30 дней наблюдения после выписки через умные часы, связывающая пациента, семейного врача и близких.",
      btnDemo: "Смотреть Видео и Демо Прототипа",
      btnApi: "API Документация (OpenAPI)",
      btnClinic: "Открыть Рабочую Станцию",

      sec1Title: "1. Проблема → Решение",
      sec1Sub: "Реальная медицинская ситуация в Узбекистане и подход WMAX",
      p1Title: "Критическая Проблема",
      p1Desc: "57% смертей в Узбекистане вызваны сердечно-сосудистыми заболеваниями (Агентство статистики, 2024). После выписки пациент остается без мониторинга, а врач узнает о проблеме лишь при наступлении инфаркта.",
      s1Title: "Наше Решение",
      s1Desc: "WMAX — платформа 24/7 наблюдения через часы, которая сигнализирует врачу и семье при устойчивом отклонении от личной нормы пациента. Диагноз ставит врач.",

      sec2Title: "2. Команда",
      sec2Sub: "Команда 0xDEAD",

      sec3Title: "3. Почему Наша Команда Решит Эту Проблему?",
      sec3Sub: "Работающий прототип, знание местных условий и честный подход",

      sec4Title: "4. Дорожная Карта (Roadmap)",
      sec4Sub: "От Идеи до Полноценного Запуска (Idea → Prototype → MVP → Launched)",

      sec5Title: "5. Техническая Реализация и Архитектура ИИ",
      sec5Sub: "Стек технологий, ИИ-инструменты и биофизические вычисления",

      sec6Title: "6. Интерактивный ИИ-Чатбот и Доступ к API",
      sec6Sub: "Быстрые ответы на вопросы жюри и готовые интеграции",
    },
    en: {
      badge: "Pitch Day 3.0 · Stage 1 Competition Submission",
      heroTitle: "WMAX — Remote Cardio-Monitoring & AI Platform",
      heroSub: "An unbroken care chain: 30 days of smartwatch follow-up after discharge, connecting the patient, the family doctor and relatives.",
      btnDemo: "Watch Demo Video & Live Prototype",
      btnApi: "API Documentation (OpenAPI)",
      btnClinic: "Explore Clinician Workstation",

      sec1Title: "1. Problem → Solution",
      sec1Sub: "Current healthcare crisis vs WMAX innovative telehealth paradigm",
      p1Title: "Critical Problem",
      p1Desc: "57% of deaths in Uzbekistan are caused by cardiovascular disease (Statistics Agency, 2024). Once patients leave the hospital, they lack continuous monitoring, so deterioration is noticed late.",
      s1Title: "Our Solution",
      s1Desc: "WMAX combines 24/7 smartwatch monitoring with a personal-baseline AI that alerts doctors and caregivers on sustained deviation. It does not diagnose; the doctor decides.",

      sec2Title: "2. The Team",
      sec2Sub: "Team 0xDEAD",

      sec3Title: "3. Why Our Team Will Solve This",
      sec3Sub: "A working prototype, local knowledge and an honest approach",

      sec4Title: "4. Strategic Roadmap",
      sec4Sub: "From Conception to Scale (Idea → Prototype → MVP → Launched)",

      sec5Title: "5. Technical Implementation & AI Architecture",
      sec5Sub: "Core stack, AI tools, signal processing pipelines, and data security",

      sec6Title: "6. Interactive AI Chatbot & API Access",
      sec6Sub: "Live questions & answers for the jury, plus open API documentation",
    }
  }[lang];

  const teamMembers = TEAM.map((m) => ({
    name: m.name,
    role: m.role[lang],
    skills: m.skills.join(', '),
    links: m.links.map((l) => l.label).join(' / ') || '0xDEAD',
    bio: '',
  }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
      
      {/* ----------------- HERO SECTION ----------------- */}
      <section className="relative pt-12 pb-20 overflow-hidden border-b border-slate-800/80">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-slate-950 to-slate-950 pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto space-y-6">
            
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs sm:text-sm font-semibold tracking-wide">
              <Sparkles className="w-4 h-4 text-amber-400 animate-spin-slow" />
              <span>{t.badge}</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              {t.heroTitle}
            </h1>

            <p className="text-lg sm:text-xl text-slate-300 leading-relaxed font-normal max-w-3xl mx-auto">
              {t.heroSub}
            </p>

            {/* Quick CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
              <button
                onClick={() => onNavigate('/demo')}
                className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-sm sm:text-base shadow-lg shadow-emerald-500/25 flex items-center gap-2 transition hover:scale-[1.02]"
              >
                <Play className="w-4 h-4 fill-slate-950" />
                <span>{t.btnDemo}</span>
              </button>

              <button
                onClick={() => onNavigate('/doctor')}
                className="px-5 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-semibold text-sm sm:text-base transition flex items-center gap-2"
              >
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>{t.btnClinic}</span>
              </button>

              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-3.5 rounded-2xl bg-slate-900/60 hover:bg-slate-800/80 text-sky-400 border border-sky-900/50 font-semibold text-sm sm:text-base transition flex items-center gap-2"
              >
                <Terminal className="w-4 h-4" />
                <span>{t.btnApi}</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-60" />
              </a>
            </div>

            {/* Key stats badges */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-10 text-left">
              <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm">
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">30 kun</div>
                <div className="text-xs text-slate-400 mt-1">Chiqarilgandan keyingi kuzatuv</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm">
                <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 font-mono">24 / 7</div>
                <div className="text-xs text-slate-400 mt-1">Uzluksiz telemetriya o'lchovi</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm">
                <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 font-mono">24 soat</div>
                <div className="text-xs text-slate-400 mt-1">Shifokorga topshiriq muddati</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-sm">
                <div className="text-2xl sm:text-3xl font-extrabold text-purple-400 font-mono">Onlayn</div>
                <div className="text-xs text-slate-400 mt-1">Ishlayotgan real prototip</div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ----------------- 1. PROBLEM -> SOLUTION ----------------- */}
      <section className="py-16 sm:py-24 border-b border-slate-800/80 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 1</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec1Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec1Sub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* The Problem Card */}
            <div className="p-8 rounded-3xl bg-gradient-to-b from-rose-950/20 to-slate-900 border border-rose-900/40 relative overflow-hidden group">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-6 border border-rose-500/20">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">{t.p1Title}</h3>
              <p className="text-slate-300 leading-relaxed mb-6 text-sm sm:text-base">
                {t.p1Desc}
              </p>
              
              <ul className="space-y-3 text-xs sm:text-sm text-slate-400 border-t border-rose-900/30 pt-6">
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span>Bemorlar shifokorga faqat ahvoli og'irlashib, holati og'irlashgandagina murojaat qiladi.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span>Shifoxonadan keyingi reabilitatsiya davrida bemor o'z holiga tashlab qo'yiladi.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span>Oila a'zolari ota-onalari holatini bilolmay, doimiy xavotirda yashaydi.</span>
                </li>
              </ul>
            </div>

            {/* The Solution Card */}
            <div className="p-8 rounded-3xl bg-gradient-to-b from-emerald-950/20 to-slate-900 border border-emerald-900/40 relative overflow-hidden group">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-6 border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">{t.s1Title}</h3>
              <p className="text-slate-300 leading-relaxed mb-6 text-sm sm:text-base">
                {t.s1Desc}
              </p>
              
              <ul className="space-y-3 text-xs sm:text-sm text-slate-300 border-t border-emerald-900/30 pt-6">
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Aqlli Soat (Galaxy Watch / Apple Watch):</strong> Puls, SpO₂, faollik, yiqilish va SOS ni qayd etadi.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>AI Tahlil Markazi:</strong> Har bir bemorning shaxsiy normasini o'rganadi va barqaror og'ishda shifokorga signal beradi.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Oila Portali:</strong> Farzandlarga ko'ngil xotirjamligini beradi va 1-bosishda yordam ko'rsatishni ta'minlaydi.</span>
                </li>
              </ul>
            </div>

          </div>
        </div>
      </section>

      {/* ----------------- 2. THE TEAM ----------------- */}
      <section className="py-16 sm:py-24 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 2</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec2Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec2Sub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member, idx) => (
              <div
                key={idx}
                className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 transition flex flex-col justify-between"
              >
                <div>
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-sky-500 p-0.5 shadow-md mb-5">
                    <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center font-bold text-xl text-emerald-400">
                      {member.name.charAt(0)}
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-white">{member.name}</h3>
                  <div className="text-xs font-semibold text-emerald-400 mt-1 mb-3">{member.role}</div>
                  {member.bio && <p className="text-xs text-slate-400 leading-relaxed mb-4">{member.bio}</p>}
                </div>
                
                <div className="border-t border-slate-800/80 pt-4">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Ko'nikmalar:</div>
                  <div className="text-xs text-slate-300 font-mono bg-slate-950/60 p-2 rounded-xl border border-slate-800">
                    {member.skills}
                  </div>
                </div>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* ----------------- 3. WHY OUR TEAM CAN SOLVE THIS ----------------- */}
      <section className="py-16 sm:py-24 border-b border-slate-800/80 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 3</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec3Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec3Sub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800">
              <div className="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-6 border border-sky-500/20">
                <Compass className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">1. Halol tibbiy yondashuv</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Tizim tashxis qo'ymaydi: o'lchaydi va xabar beradi, qarorni shifokor qabul qiladi. Ma'lumot yo'qligi "sog'lom" deb talqin qilinmaydi. Signal aniqligi pilotda EKG sensori bilan tekshiriladi.
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-6 border border-emerald-500/20">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">2. Haqiqiy Ishlayotgan Prototip</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                WMAX — shunchaki slayd emas. Bizda serverda ishlayotgan jonli backend (FastAPI), ma'lumotlar bazasi (Postgres 16), shifokor ish stansiyasi va qarovchi portali to'liq ishga tushirilgan.
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800">
              <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-6 border border-purple-500/20">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">3. O'zbekiston Bozoriga Moslashtirilgan</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Tizim mahalliy internet sifati (offline-first kesh), Telegram orqali oila a'zolariga xabar va eng muhim holatlar uchun SMS zaxira kanalini hisobga olgan holda loyihalashtirilgan.
              </p>
            </div>
          </div>

        </div>
      </section>

      {/* ----------------- 4. ROADMAP (Idea -> Prototype -> MVP -> Launched) ----------------- */}
      <section className="py-16 sm:py-24 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 4</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec4Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec4Sub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            
            {/* Step 1: Idea */}
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 relative">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300">Bosqich 1</span>
                <span className="text-xs font-semibold text-emerald-400">Bajarildi ✓</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Idea (G'oya)</h3>
              <div className="text-xs text-slate-400 mb-4">Iyun – Iyul 2026</div>
              <ul className="text-xs text-slate-400 space-y-2">
                <li>• Kardiologik muammolarni chuqur o'rganish</li>
                <li>• Bemor, farzand va shifokor rollarini aniqlash</li>
                <li>• Tibbiy cheklovlar va arxitektura loyihasi</li>
              </ul>
            </div>

            {/* Step 2: Prototype (Hozirgi holat) */}
            <div className="p-6 rounded-3xl bg-slate-900 border-2 border-emerald-500 shadow-xl shadow-emerald-500/10 relative">
              <div className="absolute -top-3 left-6 px-3 py-0.5 rounded-full bg-emerald-500 text-slate-950 font-extrabold text-[10px] uppercase tracking-wider">
                Hozirgi Holat
              </div>
              <div className="flex items-center justify-between mb-4 mt-1">
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400">Bosqich 2</span>
                <span className="text-xs font-semibold text-emerald-400">Faol ✓</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Prototype (Prototip)</h3>
              <div className="text-xs text-slate-400 mb-4">Avgust – Oktyabr 2026</div>
              <ul className="text-xs text-slate-300 space-y-2">
                <li>• 24/7 telemetriya yig'uvchi FastAPI server</li>
                <li>• Shifokor triaj stansiyasi (Web-Doctor)</li>
                <li>• Qarovchi portali (Web-Relative)</li>
                <li>• Wear OS soat ilovasi va Telegram bot</li>
              </ul>
            </div>

            {/* Step 3: MVP */}
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 relative">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400">Bosqich 3</span>
                <span className="text-xs font-semibold text-sky-400">Rejada</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">MVP (Pilot Sinov)</h3>
              <div className="text-xs text-slate-400 mb-4">Noyabr – Yanvar 2026/27</div>
              <ul className="text-xs text-slate-400 space-y-2">
                <li>• 100 nafar bemorda rozilik asosida pilot</li>
                <li>• Oilaviy poliklinika bilan hamkorlik</li>
                <li>• Wear OS uchun rasmiy ilova relizi</li>
                <li>• Puls aniqligini Polar H10 EKG bilan solishtirish</li>
              </ul>
            </div>

            {/* Step 4: Launched */}
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 relative">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400">Bosqich 4</span>
                <span className="text-xs font-semibold text-purple-400">Kengayish</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Launched (Bozorga Chiqish)</h3>
              <div className="text-xs text-slate-400 mb-4">Fevral 2027 dan</div>
              <ul className="text-xs text-slate-400 space-y-2">
                <li>• B2C obuna (oyiga 190k so'm) va B2B klinikalar</li>
                <li>• Tuman tibbiyot birlashmalari bilan shartnoma</li>
                <li>• Yuridik shaxs va dasturiy ta'minotni ro'yxatdan o'tkazish</li>
              </ul>
            </div>

          </div>
        </div>
      </section>

      {/* ----------------- 5. TECHNICAL IMPLEMENTATION & AI ----------------- */}
      <section className="py-16 sm:py-24 border-b border-slate-800/80 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 5</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec5Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec5Sub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-white">Telemetriya & Hisoblash</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Har 5 daqiqalik oyna (timewin.py) bo'yicha puls, SpO2 va harakat ma'lumotlari qabul qilinadi. Sensordagi titrashlar va artefaktlar avvaldan filtrlanadi.
              </p>
              <div className="text-[11px] font-mono text-emerald-400 bg-slate-950 p-2 rounded-xl border border-slate-800">
                contracts/timewin.py · algo/baseline.py
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Bot className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-white">Shaxsiy norma (AI yadro)</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Dastlabki kunlarda shaxsiy norma o'rganiladi, keyin sirkadian ritmni hisobga olgan z-score bilan barqaror og'ish aniqlanadi. LLM shifokorga qisqa xulosa yozadi, tashxis emas.
              </p>
              <div className="text-[11px] font-mono text-purple-400 bg-slate-950 p-2 rounded-xl border border-slate-800">
                Python · z-score · Gemini / DeepSeek
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-white">Backend & Xavfsizlik</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                FastAPI asinxron arxitekturasi, PostgreSQL 16 bilan RLS (Row Level Security), Redis keshlash va zaxira nusxa.
              </p>
              <div className="text-[11px] font-mono text-sky-400 bg-slate-950 p-2 rounded-xl border border-slate-800">
                FastAPI · Postgres 16 · Redis · HTTPS
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* ----------------- 6. AI CHATBOT & API ACCESS ----------------- */}
      <section className="py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">Bo'lim 6 · Qo'shimcha Vazifalar</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-1">{t.sec6Title}</h2>
            <p className="text-slate-400 text-base sm:text-lg mt-2">{t.sec6Sub}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* Interactive AI Chatbot (7 cols) */}
            <div className="lg:col-span-7 rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col h-[560px]">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">WMAX AI Expert Chatbot</h3>
                    <div className="text-xs text-emerald-400 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>Pitch Day savollariga javob berishga tayyor</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sample Questions Pills */}
              <div className="py-3 flex flex-wrap gap-2 border-b border-slate-800/80">
                {sampleQuestions.map((sq, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(sq)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
                  >
                    💬 {sq}
                  </button>
                ))}
              </div>

              {/* Messages list */}
              <div className="flex-1 overflow-y-auto py-4 space-y-3 pr-2">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                        m.sender === 'user'
                          ? 'bg-emerald-600 text-white rounded-tr-none'
                          : 'bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-none'
                      }`}
                    >
                      {m.text}
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800/90 text-slate-400 rounded-2xl px-4 py-2 text-xs flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce delay-100" />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce delay-200" />
                    </div>
                  </div>
                )}
              </div>

              {/* Input field */}
              <div className="pt-3 border-t border-slate-800 flex gap-2">
                <input
                  type="text"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Loyihamiz haqida savol bering..."
                  className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
                <button
                  onClick={() => handleSendMessage()}
                  className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition flex items-center justify-center"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* API Access Box (5 cols) */}
            <div className="lg:col-span-5 space-y-6">
              
              <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    <Terminal className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-base">API Kirish (API Access)</h3>
                    <p className="text-xs text-slate-400">OpenAPI 3.1 & Swagger interfeysi</p>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                  WMAX to'liq REST API va WebSocket arxitekturasiga ega. Har qanday tibbiy CRM, MIS yoki aqlli qurilmalar bizning API orqali ulanishi mumkin.
                </p>

                <div className="bg-slate-950 p-3.5 rounded-2xl border border-slate-800 font-mono text-xs text-emerald-400 mb-4 overflow-x-auto">
                  GET https://wmax.boos.uz/api/v1/patients<br />
                  POST https://wmax.boos.uz/api/v1/readings<br />
                  WS wss://wmax.boos.uz/api/v1/realtime/ws
                </div>

                <div className="flex gap-2">
                  <a
                    href="/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs text-center transition flex items-center justify-center gap-1.5"
                  >
                    <span>Swagger Docs</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  <a
                    href="/redoc"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs text-center transition flex items-center justify-center gap-1.5"
                  >
                    <span>ReDoc</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>

              {/* Pitch Day Direct Link Callout */}
              <div className="p-6 rounded-3xl bg-gradient-to-tr from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30">
                <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                  <Rocket className="w-4 h-4" />
                  <span>Pitch Day 3.0 Hakamlariga</span>
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Demo video va prototipni ko'rmoqchimisiz?</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Maxsus tayyorlangan <code>/demo</code> sahifamizda 3 daqiqalik to'liq video-ko'rsatma va ishlayotgan jonli tizim havolalari joylashtirilgan.
                </p>
                <button
                  onClick={() => onNavigate('/demo')}
                  className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition flex items-center justify-center gap-2"
                >
                  <span>/demo Sahifasiga O'tish</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </div>

          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-slate-900 bg-slate-950 text-slate-500 text-xs text-center">
        <div className="max-w-7xl mx-auto px-4">
          WMAX Telehealth © 2026 · Pitch Day 3.0 1-bosqich ishtirokchisi · Toshkent, O'zbekiston
        </div>
      </footer>

    </div>
  );
};
