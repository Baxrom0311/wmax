import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowRight, Bot, Check, ChevronLeft, ChevronRight, Code2, Globe, MonitorSmartphone, Play, Stethoscope, Users, Watch } from 'lucide-react';
import type { Lang } from '../../i18n';
import { AI_TOOLS, LINKS, PITCH, TEAM, TECH, WATCH_IMAGE } from './content';
import './pitch.css';

interface PitchHomeProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  onNavigate: (route: string) => void;
}

const SLIDE_MS = 8000;
const LANGS: Lang[] = ['uz', 'ru', 'en'];

export const PitchTopBar: React.FC<PitchHomeProps & { active?: 'home' | 'demo' }> = ({ lang, onLangChange, onNavigate, active }) => {
  const p = PITCH[lang];
  return (
    <header className="relative z-40 px-4 sm:px-8 pt-4">
      <div className="glass rounded-2xl max-w-6xl mx-auto px-4 sm:px-5 h-14 flex items-center justify-between gap-3">
        <button onClick={() => onNavigate('/')} className="flex items-baseline gap-3 min-w-0">
          <span className="text-xl font-extrabold tracking-tight">WMAX</span>
          <span className="hidden md:inline text-xs text-white/60 truncate">{p.tagline}</span>
        </button>
        <div className="flex items-center gap-2">
          <div className="glass-chip rounded-xl p-0.5 flex">
            {LANGS.map((l) => (
              <button
                key={l}
                onClick={() => onLangChange(l)}
                className={`px-2 py-1 rounded-lg text-[11px] font-bold uppercase transition ${lang === l ? 'bg-white/90 text-slate-900' : 'text-white/70 hover:text-white'}`}
              >
                {l}
              </button>
            ))}
          </div>
          <button
            onClick={() => onNavigate(active === 'demo' ? '/' : '/demo')}
            className="px-3.5 py-2 rounded-xl bg-emerald-400 text-slate-950 text-sm font-bold flex items-center gap-1.5 hover:bg-emerald-300 transition"
          >
            {active === 'demo' ? <ChevronLeft className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{active === 'demo' ? 'WMAX' : p.demo}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

const Chip: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="glass-chip rounded-lg px-2.5 py-1 text-xs font-semibold text-white/85">{children}</span>
);

function Slide({ index, lang, onNavigate }: { index: number; lang: Lang; onNavigate: (r: string) => void }) {
  const p = PITCH[lang];
  const stepIcons = [Watch, Stethoscope, Users];

  if (index === 0) {
    return (
      <div className="grid sm:grid-cols-2 gap-5 items-center">
        <div>
          <p className="text-lg sm:text-xl font-bold leading-snug">{p.problemLead}</p>
          <div className="mt-3 flex gap-5">
            {p.problemStats.map((s) => (
              <div key={s.value}>
                <div className="text-2xl font-extrabold text-rose-300 font-mono">{s.value}</div>
                <div className="text-xs text-white/60">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {p.solutionSteps.map((s, i) => {
            const Icon = stepIcons[i];
            return (
              <React.Fragment key={s.title}>
                {i > 0 && <ArrowRight className="w-4 h-4 text-emerald-300 shrink-0" />}
                <div className="glass-chip rounded-2xl p-3 flex-1 min-w-0 text-center">
                  <Icon className="w-5 h-5 mx-auto text-emerald-300" />
                  <div className="text-sm font-bold mt-1">{s.title}</div>
                  <div className="text-[11px] text-white/60 leading-tight">{s.note}</div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    );
  }

  if (index === 1) {
    return (
      <div className="space-y-4">
        <div className="grid sm:grid-cols-2 gap-3">
          {TEAM.map((m) => (
            <div key={m.name} className="glass-chip rounded-2xl p-3.5 flex gap-3 items-start">
              <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-br from-emerald-400 to-sky-400 text-slate-950 font-extrabold flex items-center justify-center">
                {m.name.split(' ').map((w) => w[0]).join('')}
              </div>
              <div className="min-w-0">
                <div className="font-bold">{m.name}</div>
                <div className="text-xs text-emerald-300">{m.role[lang]}</div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {m.skills.map((s) => (
                    <span key={s} className="text-[11px] text-white/70">#{s}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] uppercase tracking-wider text-white/50 mr-1">{p.techLabel}</span>
          {TECH.map((t) => (
            <Chip key={t}>{t}</Chip>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={LINKS.github} target="_blank" rel="noreferrer" className="glass-chip rounded-xl px-3 py-1.5 text-sm font-semibold inline-flex items-center gap-1.5 hover:bg-white/15">
            <Code2 className="w-4 h-4" /> GitHub
          </a>
          <a href={LINKS.site} target="_blank" rel="noreferrer" className="glass-chip rounded-xl px-3 py-1.5 text-sm font-semibold inline-flex items-center gap-1.5 hover:bg-white/15">
            <Globe className="w-4 h-4" /> wmax.boos.uz
          </a>
          <a href={LINKS.telegramBot} target="_blank" rel="noreferrer" className="glass-chip rounded-xl px-3 py-1.5 text-sm font-semibold inline-flex items-center gap-1.5 hover:bg-white/15">
            <Bot className="w-4 h-4" /> Telegram
          </a>
        </div>
      </div>
    );
  }

  if (index === 2) {
    return (
      <div className="grid grid-cols-3 gap-3">
        {p.why.map((w) => (
          <div key={w.value} className="glass-chip rounded-2xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-300">{w.value}</div>
            <div className="text-xs text-white/65 mt-1">{w.label}</div>
          </div>
        ))}
      </div>
    );
  }

  if (index === 3) {
    return (
      <ol className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {p.roadmap.map((r) => (
          <li
            key={r.title}
            className={`rounded-2xl p-3.5 border ${
              r.state === 'now' ? 'bg-emerald-400/20 border-emerald-300/70 shadow-[0_0_24px_rgba(16,185,129,0.35)]' : 'glass-chip'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-extrabold">{r.title}</span>
              {r.state === 'done' && <Check className="w-4 h-4 text-emerald-300" />}
              {r.state === 'now' && <span className="text-[10px] font-bold uppercase bg-emerald-300 text-slate-950 rounded-full px-1.5">{p.nowLabel}</span>}
            </div>
            <div className="text-xs text-white/65 mt-1">{r.note}</div>
          </li>
        ))}
      </ol>
    );
  }

  if (index === 4) {
    return (
      <div className="space-y-4">
        <ol className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {p.plan.map((s, i) => (
            <li key={s.title} className="glass-chip rounded-2xl p-3">
              <div className="text-[11px] font-mono text-emerald-300">0{i + 1} · {s.title}</div>
              <div className="text-sm font-semibold mt-0.5">{s.note}</div>
            </li>
          ))}
        </ol>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] uppercase tracking-wider text-white/50 mr-1">{p.aiLabel}</span>
          {AI_TOOLS.map((t) => (
            <Chip key={t}>{t}</Chip>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <p className="text-lg font-bold">{p.demoLead}</p>
      <div className="flex gap-2">
        <button onClick={() => onNavigate('/demo')} className="px-4 py-2.5 rounded-xl bg-emerald-400 text-slate-950 font-bold inline-flex items-center gap-2 hover:bg-emerald-300">
          <Play className="w-4 h-4 fill-current" /> {p.demo}
        </button>
        <a href={LINKS.doctorDemo} className="glass-chip px-4 py-2.5 rounded-xl font-bold inline-flex items-center gap-2 hover:bg-white/15">
          <MonitorSmartphone className="w-4 h-4" /> {p.prototype}
        </a>
      </div>
    </div>
  );
}

export const PitchHome: React.FC<PitchHomeProps> = ({ lang, onLangChange, onNavigate }) => {
  const p = PITCH[lang];
  const count = p.nav.length;
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const stageRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const go = useCallback((i: number) => setActive(((i % count) + count) % count), [count]);

  // Auto-advance like a presentation; the progress bar restarts with each slide.
  useEffect(() => {
    if (paused) return;
    const id = window.setTimeout(() => go(active + 1), SLIDE_MS);
    return () => window.clearTimeout(id);
  }, [active, paused, go]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') go(active + 1);
      if (e.key === 'ArrowLeft') go(active - 1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [active, go]);

  // Section labels orbit the watch on a tilted ring. The ring turns to bring
  // the active section to the front; nodes behind the watch are smaller and dimmer.
  const activeRef = useRef(active);
  useEffect(() => {
    activeRef.current = active;
  }, [active]);
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const step = (Math.PI * 2) / count;
    let raf = 0;
    let angle = Math.PI / 2;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = Math.min(64, now - last);
      last = now;
      // Front of the ring is +PI/2; take the shortest way round to the target.
      const target = Math.PI / 2 - activeRef.current * step;
      let diff = (target - angle) % (Math.PI * 2);
      if (diff > Math.PI) diff -= Math.PI * 2;
      if (diff < -Math.PI) diff += Math.PI * 2;
      angle += reduce ? diff : diff * Math.min(1, dt * 0.004);
      const w = stage.clientWidth;
      const h = stage.clientHeight;
      const rx = Math.min(w * 0.42, 460);
      const ry = Math.min(h * 0.2, 120);
      nodeRefs.current.forEach((el, i) => {
        if (!el) return;
        const a = angle + i * step;
        const depth = (Math.sin(a) + 1) / 2;
        const x = Math.cos(a) * rx;
        const y = Math.sin(a) * ry;
        const scale = 0.78 + depth * 0.3;
        el.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px) scale(${scale})`;
        el.style.zIndex = depth > 0.5 ? '30' : '10';
        el.style.opacity = String(0.5 + depth * 0.5);
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [count]);

  return (
    <div className="pitch-root">
      <div className="pitch-blob b1" />
      <div className="pitch-blob b2" />
      <div className="pitch-blob b3" />

      <PitchTopBar lang={lang} onLangChange={onLangChange} onNavigate={onNavigate} />

      <main className="relative z-10 max-w-6xl mx-auto px-4 sm:px-8 pb-8 flex flex-col min-h-[calc(100svh-4.5rem)]">
        {/* Stage: watch in the middle, sections orbiting around it (desktop) */}
        <div ref={stageRef} className="relative flex-1 min-h-[300px] sm:min-h-[420px] hidden sm:block">
          <div className="pitch-ring absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ width: 'min(84%, 920px)', height: 'min(40%, 240px)' }} />
          <img
            src={WATCH_IMAGE}
            alt="WMAX"
            className="pitch-watch absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[88%] max-h-[520px] w-auto z-20 pointer-events-none select-none"
          />
          {p.nav.map((label, i) => (
            <button
              key={label}
              ref={(el) => {
                nodeRefs.current[i] = el;
              }}
              onClick={() => go(i)}
              onMouseEnter={() => setPaused(true)}
              onMouseLeave={() => setPaused(false)}
              className={`pitch-node glass absolute left-1/2 top-1/2 rounded-2xl px-4 py-2.5 flex items-center gap-2 whitespace-nowrap ${active === i ? 'active' : ''}`}
            >
              <span className="text-[11px] font-mono text-emerald-300">0{i + 1}</span>
              <span className="text-sm font-bold">{label}</span>
            </button>
          ))}
        </div>

        {/* Mobile: watch + section tabs */}
        <div className="sm:hidden flex flex-col items-center pt-2">
          <img src={WATCH_IMAGE} alt="WMAX" className="pitch-watch h-56 w-auto" />
          <div className="w-full mt-3 flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
            {p.nav.map((label, i) => (
              <button
                key={label}
                onClick={(e) => {
                  go(i);
                  e.currentTarget.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                }}
                className={`pitch-node glass shrink-0 rounded-xl px-3 py-2 text-xs font-bold ${active === i ? 'active' : ''}`}
              >
                <span className="font-mono text-emerald-300 mr-1">0{i + 1}</span>
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Active section */}
        <section
          className="glass glass-strong rounded-3xl mt-4 overflow-hidden sm:min-h-[230px]"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          aria-live="polite"
        >
          <div className="h-0.5 bg-white/10">
            <div key={`${active}-${paused}`} className="pitch-progress h-full bg-emerald-300" style={{ animationDuration: `${SLIDE_MS}ms`, animationPlayState: paused ? 'paused' : 'running' }} />
          </div>
          <div className="p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight">
                <span className="font-mono text-emerald-300 mr-2 text-base">0{active + 1}</span>
                {p.nav[active]}
              </h2>
              <div className="flex gap-1.5">
                <button aria-label="prev" onClick={() => go(active - 1)} className="glass-chip w-9 h-9 rounded-xl flex items-center justify-center hover:bg-white/15">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button aria-label="next" onClick={() => go(active + 1)} className="glass-chip w-9 h-9 rounded-xl flex items-center justify-center hover:bg-white/15">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div key={`${active}-${lang}`} className="pitch-slide-enter">
              <Slide index={active} lang={lang} onNavigate={onNavigate} />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};
