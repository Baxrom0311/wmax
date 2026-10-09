import React, { useRef, useState } from 'react';
import { ArrowLeft, Maximize2, ExternalLink, Presentation, Sparkles } from 'lucide-react';

interface PresentationPageProps {
  onNavigate: (route: string) => void;
  lang?: 'uz' | 'ru' | 'en';
}

export const PresentationPage: React.FC<PresentationPageProps> = ({ onNavigate, lang = 'uz' }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [version, setVersion] = useState<'v2' | 'v1'>('v2');

  const t = {
    uz: {
      back: "Bosh sahifaga qaytish",
      title: "WMAX Telehealth Taqdimoti",
      badgeV2: "3D Interaktiv Pitch (v2)",
      badgeV1: "Slaydlar (v1)",
      fullscreen: "To'liq ekran",
      openTab: "Alohida oynada ochish",
      hint: version === 'v2' ? "Sichqoncha yoki skroll orqali 3D soatni aylantiring" : "Slaydlarni klaviaturadagi strelkalar (← / →) orqali almashtiring",
    },
    ru: {
      back: "На главную",
      title: "Презентация WMAX Telehealth",
      badgeV2: "3D Интерактивный Питч (v2)",
      badgeV1: "Слайды (v1)",
      fullscreen: "Полный экран",
      openTab: "В новой вкладке",
      hint: version === 'v2' ? "Вращайте 3D-часы колесиком мыши или свайпом" : "Переключайте слайды стрелками (← / →) на клавиатуре",
    },
    en: {
      back: "Back to Home",
      title: "WMAX Telehealth Presentation",
      badgeV2: "3D Interactive Pitch (v2)",
      badgeV1: "Slides (v1)",
      fullscreen: "Full Screen",
      openTab: "Open in New Tab",
      hint: version === 'v2' ? "Scroll or drag to rotate the 3D watch and explore scenes" : "Navigate slides using keyboard arrows (← / →)",
    }
  }[lang];

  const handleFullscreen = () => {
    if (iframeRef.current) {
      if (!document.fullscreenElement) {
        iframeRef.current.requestFullscreen().catch((err) => {
          console.error("Fullscreen error:", err);
        });
        setIsFullscreen(true);
      } else {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  const activeSrc = version === 'v2' ? '/pptx/v2.html' : '/pptx/v1.html';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Bar */}
      <header className="h-16 border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('/')}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">{t.back}</span>
          </button>
          <div className="h-4 w-px bg-slate-800 hidden sm:block" />
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Presentation className="w-4 h-4" />
            </div>
            <h1 className="text-sm sm:text-base font-semibold tracking-tight text-white flex items-center gap-2">
              {t.title}
            </h1>
          </div>

          {/* v2 / v1 Segmented Switcher */}
          <div className="inline-flex p-1 rounded-xl bg-slate-800/80 border border-slate-700/60 ml-2">
            <button
              onClick={() => setVersion('v2')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                version === 'v2'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3 h-3 text-amber-300" />
              <span>3D Pitch v2</span>
            </button>
            <button
              onClick={() => setVersion('v1')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                version === 'v1'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span>Slaydlar v1</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden xl:inline text-xs text-slate-400 font-mono pr-2">
            {t.hint}
          </span>
          <button
            onClick={handleFullscreen}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            title={t.fullscreen}
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{isFullscreen ? (lang === 'ru' ? 'Выйти из полноэкранного' : lang === 'en' ? 'Exit Fullscreen' : "Kichraytirish") : t.fullscreen}</span>
          </button>
          <a
            href={activeSrc}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm"
            title={t.openTab}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t.openTab}</span>
          </a>
        </div>
      </header>

      {/* Main Presentation Viewport */}
      <main className="flex-1 p-2 sm:p-4 md:p-6 flex flex-col items-center justify-center bg-radial from-slate-900 to-slate-950">
        <div className="w-full max-w-7xl h-[calc(100vh-6.5rem)] rounded-2xl overflow-hidden border border-slate-800 bg-slate-900/50 shadow-2xl relative">
          <iframe
            key={activeSrc}
            ref={iframeRef}
            src={activeSrc}
            title={version === 'v2' ? "WMAX 3D Pitch v2" : "WMAX Slaydlar v1"}
            className="w-full h-full border-0"
            allow="fullscreen; accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          />
        </div>
      </main>
    </div>
  );
};
