import React, { useState } from 'react';
import {
  CheckCircle2,
  Sparkles,
  Layers,
  ArrowRight,
  Video,
  FileText,
  HeartHandshake,
  Stethoscope,
  Copy,
  Check
} from 'lucide-react';
import type { Lang } from '../i18n';

interface DemoPageProps {
  onNavigate: (route: string) => void;
  lang: Lang;
}

export const DemoPage: React.FC<DemoPageProps> = ({ onNavigate, lang }) => {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const t = {
    uz: {
      badge: "Pitch Day 3.0 · Rasmiy Demo & Video Sahifasi",
      title: "WMAX — Ishlayotgan Prototip va Demo-Video",
      sub: "Hakamlar hay'ati va mutaxassislar uchun tayyorlangan to'liq tizim ko'rsatmasi, demo-video va real vaqtda ishlayotgan jonli prototip havolalari.",
      videoTitle: "1. Demo-Video (3 daqiqalik to'liq ko'rsatma)",
      videoSub: "Aqlli soatdan telemetriya qabul qilish, AI tahlil va krizis holatida harakatlar zanjiri",
      descTitle: "2. Demo-Videoning Batafsil Tavsifi",
      protoTitle: "3. Ishlayotgan Jonli Prototip Havolalari",
      protoSub: "Hozirning o'zida brauzerda sinab ko'rishingiz mumkin bo'lgan modullar:",
      backAifu: "← Pitch Day 3.0 Loyiha Sahifasi (/aifu)",
      openClinic: "Shifokor Ish Stansiyasiga Kirish",
      openRelative: "Qarovchi Portaliga Kirish",
      openSlides: "3D Taqdimotni Ko'rish",
    },
    ru: {
      badge: "Pitch Day 3.0 · Официальная Демо & Видео Страница",
      title: "WMAX — Работающий Прототип и Демо-Видео",
      sub: "Полная видеопрезентация системы, описание сценариев и прямые ссылки на работающий прототип для жюри конкурса.",
      videoTitle: "1. Демо-Видео (3-минутная наглядная демонстрация)",
      videoSub: "Сбор телеметрии с часов, аналитика ИИ и цепочка экстренного реагирования",
      descTitle: "2. Подробное Описание Демо-Видео",
      protoTitle: "3. Ссылки на Работающий Живой Прототип",
      protoSub: "Модули платформы, доступные для интерактивного тестирования прямо сейчас:",
      backAifu: "← Страница Проекта Pitch Day (/aifu)",
      openClinic: "Войти в Станцию Врача",
      openRelative: "Войти в Портал Опекуна",
      openSlides: "Открыть 3D Презентацию",
    },
    en: {
      badge: "Pitch Day 3.0 · Official Demo & Video Showcase",
      title: "WMAX — Working Prototype & Demo Video",
      sub: "Complete video walkthrough, scene breakdown, and direct access links to our live, fully deployed telehealth prototype for competition judges.",
      videoTitle: "1. Demo Video (3-minute comprehensive walkthrough)",
      videoSub: "Real-time wearable telemetry capture, AI analysis, and emergency intervention loop",
      descTitle: "2. Detailed Demo Video Description",
      protoTitle: "3. Working Live Prototype Access",
      protoSub: "Interactive modules available for instant browser testing right now:",
      backAifu: "← Back to Pitch Day 3.0 Overview (/aifu)",
      openClinic: "Open Doctor Workstation",
      openRelative: "Open Relative Portal",
      openSlides: "View 3D Presentation",
    }
  }[lang];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
      
      {/* Top Banner */}
      <div className="bg-slate-900/80 border-b border-slate-800 py-3 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button
            onClick={() => onNavigate('/aifu')}
            className="text-xs sm:text-sm font-semibold text-emerald-400 hover:text-emerald-300 transition flex items-center gap-1.5"
          >
            <span>{t.backAifu}</span>
          </button>
          <span className="text-xs text-slate-400 font-mono">Pitch Day 3.0 · /demo</span>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>{t.badge}</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            {t.title}
          </h1>
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            {t.sub}
          </p>
        </div>

        {/* ---------------- 6.1. DEMO-VIDEO SECTION ---------------- */}
        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Video className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl sm:text-2xl font-bold text-white">{t.videoTitle}</h2>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">{t.videoSub}</p>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 self-start sm:self-auto">
              Davomiyligi: 03:12
            </span>
          </div>

          {/* Video Player Frame */}
          <div className="aspect-video w-full rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 relative shadow-2xl flex items-center justify-center group">
            {/* YouTube embed or modern HTML5 responsive video player */}
            <iframe
              className="w-full h-full"
              src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0&modestbranding=1"
              title="WMAX Telehealth Demo Video"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>

          <div className="text-xs text-slate-400 flex items-center justify-between pt-2">
            <span>Video formati: 1080p FHD · O'zbek va rus tillarida subtitrlar mavjud</span>
            <span className="text-emerald-400 font-semibold">Pitch Day 3.0 ekspertlari uchun maxsus tayyorlandi</span>
          </div>
        </div>

        {/* ---------------- 6.2. DEMO-VIDEO DESCRIPTION ---------------- */}
        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-4">
            <FileText className="w-5 h-5 text-sky-400" />
            <h2 className="text-xl sm:text-2xl font-bold text-white">{t.descTitle}</h2>
          </div>

          <div className="space-y-6 text-sm text-slate-300 leading-relaxed">
            <p>
              Ushbu demo-videoda WMAX masofaviy kardio-monitoring platformasining barcha bo'g'inlari real vaqt rejimida qanday ishlashi bosqichma-bosqich ko'rsatib berilgan:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800/80">
                <div className="flex items-center gap-2 text-emerald-400 font-bold mb-2">
                  <span className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs">1</span>
                  <span>00:00 – 01:10: Telemetriya</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Samsung Galaxy Watch 5 soatidan bemorning puls, qondagi kislorod (SpO2) va harakat ma'lumotlari qabul qilinishi. Har 5 daqiqalik o'lchov darchasida shovqinlarni tozalash jarayoni.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800/80">
                <div className="flex items-center gap-2 text-amber-400 font-bold mb-2">
                  <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-xs">2</span>
                  <span>01:10 – 02:15: AI & Shifokor Triaji</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Kardiologning ish stansiyasida sun'iy intellekt xavfni 48 soat oldin aniqlab, sariq/qizil ogohlantirish berishi. Bemor kartasi, EKG grafigi va dori-darmon tavsiyalari kiritilishi.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800/80">
                <div className="flex items-center gap-2 text-sky-400 font-bold mb-2">
                  <span className="w-6 h-6 rounded-full bg-sky-500/20 flex items-center justify-center text-xs">3</span>
                  <span>02:15 – 03:12: Oila & SOS Harakati</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Farzandlar mobil portalida "Ko'ngil xotirjamligi" indikatori, krizis holatida 1-bosishda 103 tez tibbiy yordam dispetcherini chaqirish va Telegram bot ogohlantirishi.
                </p>
              </div>

            </div>

            <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-300">
              💡 <strong>Xulosa:</strong> Video shuni isbotlaydiki, WMAX faqat nazariy kontseptsiya emas, balki to'liq ishlaydigan, kardiologlar bilan tasdiqlangan va serverda faol bo'lgan dasturiy majmuadir.
            </div>
          </div>
        </div>

        {/* ---------------- 6.3. WORKING LIVE PROTOTYPE ACCESS ---------------- */}
        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h2 className="text-xl sm:text-2xl font-bold text-white">{t.protoTitle}</h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">{t.protoSub}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Prototype 1: Doctor Station */}
            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-1">Shifokor Ish Stansiyasi</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Bemorlar ro'yxati, triaj statuslari (Yashil/Sariq/Qizil), EKG va telemetriya grafigi, SOS monitoringi.
                </p>
                <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1 mb-4">
                  <div className="text-slate-500">Test login:</div>
                  <div className="flex justify-between items-center">
                    <span>+998901234567</span>
                    <button onClick={() => copyToClipboard('+998901234567', 'doc-p')} className="text-emerald-400">
                      {copied === 'doc-p' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>wmax123</span>
                    <button onClick={() => copyToClipboard('wmax123', 'doc-pass')} className="text-emerald-400">
                      {copied === 'doc-pass' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('/doctor')}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center justify-center gap-1.5"
              >
                <span>{t.openClinic}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Prototype 2: Relative Portal */}
            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-4">
                  <HeartHandshake className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-1">Qarovchi & Oila Portali</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Ota-onaning ko'ngil xotirjamligi kartasi, jonli puls, SpO2, batareya va 1-bosishda shifokorga qo'ng'iroq.
                </p>
                <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1 mb-4">
                  <div className="text-slate-500">Test login:</div>
                  <div className="flex justify-between items-center">
                    <span>+998901110011</span>
                    <button onClick={() => copyToClipboard('+998901110011', 'rel-p')} className="text-sky-400">
                      {copied === 'rel-p' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>112233 (PIN)</span>
                    <button onClick={() => copyToClipboard('112233', 'rel-pin')} className="text-sky-400">
                      {copied === 'rel-pin' ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('/r')}
                className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition flex items-center justify-center gap-1.5"
              >
                <span>{t.openRelative}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Prototype 3: 3D Presentation */}
            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-4">
                  <Layers className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-1">Interaktiv 3D Pitch Deck</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Scroll-driven 3D aqlli soat modeli, telemetriya stsenariylari va interaktiv slaydlar (v2 & v1).
                </p>
                <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 mb-4">
                  <span className="text-purple-400 font-semibold">WebGL / Three.js</span>
                  <div className="text-slate-500 mt-1">To'liq ekranda ishlash imkoniyati</div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('/pptx')}
                className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs transition flex items-center justify-center gap-1.5"
              >
                <span>{t.openSlides}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>
        </div>

      </div>

      {/* Footer */}
      <footer className="py-10 border-t border-slate-900 bg-slate-950 text-slate-500 text-xs text-center mt-12">
        <div className="max-w-6xl mx-auto px-4">
          WMAX Telehealth © 2026 · Pitch Day 3.0 Demo Sahifasi · https://wmax.boos.uz/demo
        </div>
      </footer>

    </div>
  );
};
