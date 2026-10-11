import React, { useEffect, useRef, useState } from 'react';
import {
  Award,
  Bot,
  CalendarRange,
  Check,
  ChevronDown,
  ChevronLeft,
  Code2,
  Globe,
  Lightbulb,
  Map as MapIcon,
  MonitorSmartphone,
  Play,
  Stethoscope,
  TriangleAlert,
  Users,
  Watch,
} from 'lucide-react';
import type { Lang } from '../../i18n';
import { AI_TOOLS, LINKS, PITCH, SECTION_IDS, TEAM, TECH, WATCH_FACES } from './content';
import { PitchChat } from './PitchChat';
import './pitch.css';

interface PitchPageProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  onNavigate: (route: string) => void;
}

const LANGS: Lang[] = ['uz', 'ru', 'en'];
const CONTACT_ID = 'aloqa';
const SECTION_ICONS = [TriangleAlert, Lightbulb, Users, Award, MapIcon, CalendarRange];

/** Fixed glass navbar shared by the home page and /demo. */
export const PitchTopBar: React.FC<PitchPageProps & { page: 'home' | 'demo'; current?: number; onSection?: (id: string) => void }> = ({
  lang,
  onLangChange,
  onNavigate,
  page,
  current,
  onSection,
}) => {
  const p = PITCH[lang];
  const links = [...SECTION_IDS.map((id, i) => ({ id, label: p.sections[i].label })), { id: CONTACT_ID, label: p.contact }];
  const go = (id: string) => (onSection ? onSection(id) : onNavigate(`/#${id}`));

  return (
    <header className="fixed top-0 inset-x-0 z-50 px-3 sm:px-6 pt-3">
      <div className="glass rounded-2xl max-w-6xl mx-auto px-3 sm:px-4">
        <div className="h-14 flex items-center justify-between gap-3">
          <button onClick={() => (onSection ? onSection(SECTION_IDS[0]) : onNavigate('/'))} className="text-xl font-extrabold tracking-tight shrink-0">
            WMAX
          </button>
          <nav className="hidden lg:flex items-center gap-0.5 min-w-0">
            {links.map((l, i) => (
              <button
                key={l.id}
                onClick={() => go(l.id)}
                className={`px-2.5 py-1.5 rounded-lg text-sm font-semibold transition whitespace-nowrap ${current === i ? 'bg-white/15 text-white' : 'text-white/65 hover:text-white'}`}
              >
                {l.label}
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-2 shrink-0">
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
              onClick={() => onNavigate(page === 'demo' ? '/' : '/demo')}
              className="px-3.5 py-2 rounded-xl bg-emerald-400 text-slate-950 text-sm font-bold flex items-center gap-1.5 hover:bg-emerald-300 transition"
            >
              {page === 'demo' ? <ChevronLeft className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
              <span>{page === 'demo' ? 'WMAX' : p.demo}</span>
            </button>
          </div>
        </div>
        <nav className="lg:hidden flex gap-1 overflow-x-auto pb-2 -mx-1 px-1 no-scrollbar">
          {links.map((l, i) => (
            <button
              key={l.id}
              onClick={() => go(l.id)}
              className={`shrink-0 px-2.5 py-1 rounded-lg text-xs font-semibold transition ${current === i ? 'bg-white/15 text-white' : 'text-white/65'}`}
            >
              {l.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};

const Chip: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="glass-chip rounded-md px-1.5 py-0.5 text-[10px] sm:text-xs font-semibold text-white/85">{children}</span>
);

const Stat: React.FC<{ value: string; label: string; tone?: string }> = ({ value, label, tone = 'text-emerald-300' }) => (
  <>
    <div className={`text-xl sm:text-3xl font-extrabold font-mono leading-none ${tone}`}>{value}</div>
    <div className="text-[11px] sm:text-sm text-white/65 mt-1 leading-tight">{label}</div>
  </>
);

const Head: React.FC<{ icon?: React.ElementType; title: string; kicker?: string }> = ({ icon: I, title, kicker }) => (
  <div className="flex items-center gap-1.5">
    {I && <I className="w-4 h-4 text-emerald-300 shrink-0" />}
    {kicker && <span className="text-[10px] sm:text-xs font-mono text-emerald-300">{kicker}</span>}
    <span className="text-sm sm:text-lg font-bold leading-tight">{title}</span>
  </div>
);

const Note: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="text-[11px] sm:text-sm text-white/65 mt-1 leading-snug">{children}</div>
);

/**
 * The pieces of one section, each shown as its own glass card around the watch.
 * Order: left column top to bottom, then right column top to bottom.
 */
function sectionPieces(index: number, lang: Lang): { key: string; node: React.ReactNode; hot?: boolean }[] {
  const p = PITCH[lang];
  const stepIcons = [Watch, Stethoscope, Users];
  switch (index) {
    case 0:
      return [
        { key: 'days', node: <Stat value="30" label={p.problemDays} tone="text-rose-300" /> },
        ...p.problemStats.map((s) => ({ key: s.value, node: <Stat value={s.value} label={s.label} tone="text-rose-300" /> })),
      ];
    case 1:
      return [
        ...p.solutionSteps.map((s, i) => ({ key: s.title, node: (<><Head icon={stepIcons[i]} title={s.title} /><Note>{s.note}</Note></>) })),
        { key: 'ai', node: (<><Head icon={Bot} title="AI" /><Note>{p.solutionAi}</Note></>) },
      ];
    case 2:
      return [
        ...TEAM.map((m) => ({
          key: m.name,
          node: (
            <>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 shrink-0 rounded-lg bg-gradient-to-br from-emerald-400 to-sky-400 text-slate-950 text-xs font-extrabold flex items-center justify-center">
                  {m.name.split(' ').map((w) => w[0]).join('')}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-bold leading-tight">{m.name}</div>
                  <div className="text-[11px] text-emerald-300 leading-tight">{m.role[lang]}</div>
                </div>
              </div>
              <Note>{m.skills.join(' · ')}</Note>
            </>
          ),
        })),
        {
          key: 'tech',
          node: (
            <>
              <Head title={p.techLabel} />
              <div className="flex flex-wrap gap-1 mt-1.5">
                {TECH.map((t) => (
                  <Chip key={t}>{t}</Chip>
                ))}
              </div>
            </>
          ),
        },
        {
          key: 'links',
          node: (
            <div className="flex flex-col gap-1">
              <a href={LINKS.github} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold hover:text-emerald-300">
                <Code2 className="w-3.5 h-3.5" /> GitHub
              </a>
              <a href={LINKS.telegramBot} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold hover:text-emerald-300">
                <Bot className="w-3.5 h-3.5" /> Telegram bot
              </a>
              <a href={LINKS.doctorDemo} className="inline-flex items-center gap-1.5 text-xs font-semibold hover:text-emerald-300">
                <MonitorSmartphone className="w-3.5 h-3.5" /> {p.prototype}
              </a>
            </div>
          ),
        },
      ];
    case 3:
      return p.why.map((w) => ({ key: w.value, node: <Stat value={w.value} label={w.label} /> }));
    case 4:
      return p.roadmap.map((r, i) => ({
        key: r.title,
        hot: r.state === 'now',
        node: (
          <>
            <div className="flex items-center justify-between gap-1">
              <Head kicker={`0${i + 1}`} title={r.title} />
              {r.state === 'done' && <Check className="w-4 h-4 text-emerald-300 shrink-0" />}
              {r.state === 'now' && <span className="text-[9px] font-bold uppercase bg-emerald-300 text-slate-950 rounded-full px-1.5 shrink-0">{p.nowLabel}</span>}
            </div>
            <Note>{r.note}</Note>
          </>
        ),
      }));
    default:
      return [
        ...p.plan.map((s, i) => ({ key: s.title, node: (<><Head kicker={`0${i + 1}`} title={s.title} /><Note>{s.note}</Note></>) })),
        {
          key: 'ai-tools',
          node: (
            <>
              <Head icon={Bot} title={p.aiLabel} />
              <div className="flex flex-wrap gap-1 mt-1.5">
                {AI_TOOLS.map((t) => (
                  <Chip key={t}>{t}</Chip>
                ))}
              </div>
            </>
          ),
        },
      ];
  }
}

/* Slot angles (degrees, screen coordinates: negative is up) for n cards around the watch. */
const SLOTS: Record<number, number[]> = {
  2: [180, 0],
  3: [-150, 150, 0],
  4: [-150, 150, -30, 30],
  5: [-145, 180, 145, -30, 30],
  6: [-142, 180, 142, -38, 0, 38],
};

/**
 * Scroll-driven presentation: the page is one tall track with a sticky stage.
 * Each section's pieces sit around the watch; scrolling swings them round the
 * watch and out while the next section's pieces swing in from the other side.
 */
export const PitchHome: React.FC<PitchPageProps> = ({ lang, onLangChange, onNavigate }) => {
  const p = PITCH[lang];
  const count = SECTION_IDS.length;
  const [active, setActive] = useState(0);
  const [atContact, setAtContact] = useState(false);
  const [started, setStarted] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const watchRef = useRef<HTMLDivElement>(null);
  const headRef = useRef<HTMLDivElement>(null);

  const scrollToId = (id: string, smooth = true) => {
    const el = document.getElementById(id);
    if (!el) return;
    window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY, behavior: smooth ? 'smooth' : 'auto' });
    window.history.replaceState(null, '', `/#${id}`);
  };

  // Let the page settle on a section instead of stopping between two.
  useEffect(() => {
    const root = document.documentElement;
    root.style.scrollSnapType = 'y proximity';
    return () => {
      root.style.scrollSnapType = '';
    };
  }, []);

  // Arriving from /demo with "/#section": jump straight there.
  useEffect(() => {
    const id = window.location.hash.slice(1);
    if (!id) return;
    const t = window.setTimeout(() => scrollToId(id, false), 50);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    const stage = stageRef.current;
    if (!track || !stage) return;
    let raf = 0;
    let shown = -1;
    let lastActive = -1;
    let lastContact: boolean | null = null;
    let lastStarted: boolean | null = null;

    const tick = () => {
      const vh = window.innerHeight;
      const top = track.getBoundingClientRect().top;
      const target = Math.min(count - 1, Math.max(0, -top / vh));
      shown = shown < 0 ? target : shown + (target - shown) * 0.2;
      if (Math.abs(target - shown) < 0.001) shown = target;

      const idx = Math.round(shown);
      if (idx !== lastActive) {
        lastActive = idx;
        setActive(idx);
      }
      const contact = top + track.offsetHeight < vh * 0.6;
      if (contact !== lastContact) {
        lastContact = contact;
        setAtContact(contact);
      }
      const isStarted = target > 0.15;
      if (isStarted !== lastStarted) {
        lastStarted = isStarted;
        setStarted(isStarted);
      }

      // -0.5..0.5 inside the current section; 0 when it is centred.
      const delta = shown - idx;
      // Fully visible around the centre of a section, gone at the hand-over point.
      const fade = Math.min(1, Math.max(0, (0.5 - Math.abs(delta)) / 0.3));
      const w = stage.clientWidth;
      const h = stage.clientHeight;
      const mobile = w < 640;
      const watchW = watchRef.current?.offsetWidth ?? 120;
      const cardW = mobile ? Math.max(118, Math.min(180, (w - watchW) / 2 - 4)) : Math.min(250, w * 0.24);
      const rx = Math.min(w / 2 - cardW / 2 - 2, watchW / 2 + cardW / 2 + 150);
      const ry = h * (mobile ? 0.36 : 0.4);

      stage.querySelectorAll<HTMLElement>('[data-slot]').forEach((el) => {
        const slot = (Number(el.dataset.slot) * Math.PI) / 180;
        // Swing along the orbit: pieces leave clockwise and arrive from the other side.
        const a = slot - delta * 1.6;
        let x = Math.cos(a) * rx;
        if (mobile) x = Math.sign(Math.cos(slot)) * rx * (0.7 + 0.3 * Math.abs(Math.cos(a)));
        const y = Math.sin(a) * ry;
        el.style.width = `${cardW}px`;
        el.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px) scale(${0.85 + 0.15 * fade})`;
        el.style.opacity = String(fade);
        el.style.pointerEvents = fade > 0.5 ? 'auto' : 'none';
      });
      if (headRef.current) {
        headRef.current.style.opacity = String(fade);
        headRef.current.style.transform = `translateY(${delta * -24}px)`;
      }
      if (watchRef.current) {
        watchRef.current.style.transform = `perspective(900px) rotateY(${Math.sin(shown * Math.PI) * 16}deg) rotateZ(${Math.sin(shown * 1.3) * 3}deg)`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [count]);

  const faces = Array.from(new Set(WATCH_FACES));
  const Icon = SECTION_ICONS[active];
  const pieces = sectionPieces(active, lang);
  const slots = SLOTS[pieces.length] ?? SLOTS[4];

  return (
    <div className="pitch-root">
      <div className="pitch-blob b1" />
      <div className="pitch-blob b2" />
      <div className="pitch-blob b3" />

      <PitchTopBar lang={lang} onLangChange={onLangChange} onNavigate={onNavigate} page="home" current={atContact ? count : active} onSection={scrollToId} />

      <div ref={trackRef} className="relative" style={{ height: `${count * 100}svh` }}>
        {SECTION_IDS.map((id, i) => (
          <div key={id} id={id} aria-hidden className="absolute left-0 w-px h-px snap-start" style={{ top: `${i * 100}svh` }} />
        ))}

        <div className="sticky top-0 h-[100svh] flex flex-col max-w-6xl mx-auto px-2 sm:px-8 pt-[7.25rem] lg:pt-[5.75rem] pb-3 sm:pb-6">
          {/* Section name and its one sentence */}
          <div ref={headRef} className="text-center px-2" aria-live="polite">
            <div className="inline-flex items-center gap-1.5 glass-chip rounded-full px-3 py-1 text-emerald-300 text-[11px] font-bold uppercase tracking-wider">
              <Icon className="w-3.5 h-3.5" />
              <span className="font-mono">0{active + 1}</span>
              {p.sections[active].label}
            </div>
            <h1 className="text-lg sm:text-3xl font-extrabold tracking-tight leading-snug mt-2 max-w-3xl mx-auto">{p.sections[active].line}</h1>
          </div>

          {/* Watch in the middle, the section's pieces around it */}
          <div ref={stageRef} className="relative flex-1 min-h-[280px] mt-2">
            <div className="pitch-ring absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ width: 'min(86%, 900px)', height: '78%' }} />
            <div className="pitch-watch absolute left-1/2 top-1/2 h-[50%] sm:h-[92%] max-h-[500px] aspect-[512/1105] z-10 pointer-events-none select-none" style={{ translate: '-50% -50%' }}>
              <div ref={watchRef} className="relative w-full h-full">
                {faces.map((src) => (
                  <img
                    key={src}
                    src={src}
                    alt=""
                    className="absolute inset-0 w-full h-full object-contain transition-opacity duration-700"
                    style={{ opacity: WATCH_FACES[active] === src ? 1 : 0 }}
                  />
                ))}
              </div>
            </div>
            {pieces.map((piece, i) => (
              <div
                key={`${active}-${piece.key}`}
                data-slot={slots[i]}
                className={`pitch-piece glass absolute left-1/2 top-1/2 z-20 rounded-2xl p-2.5 sm:p-3.5 ${piece.hot ? 'active' : ''}`}
                style={{ opacity: 0 }}
              >
                {piece.node}
              </div>
            ))}
            {!started && (
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 z-30 flex flex-col items-center text-[11px] text-white/55 animate-bounce pointer-events-none">
                {p.scrollHint}
                <ChevronDown className="w-4 h-4" />
              </div>
            )}
          </div>

          {/* Progress */}
          <div className="flex justify-center gap-1.5 pt-2">
            {SECTION_IDS.map((id, i) => (
              <button
                key={id}
                aria-label={p.sections[i].label}
                onClick={() => scrollToId(id)}
                className={`h-1.5 rounded-full transition-all ${i === active ? 'w-7 bg-emerald-300' : 'w-1.5 bg-white/30 hover:bg-white/60'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Contact */}
      <footer id={CONTACT_ID} className="snap-end relative z-10 max-w-6xl mx-auto px-3 sm:px-8 pt-10 pb-28">
        <div className="glass glass-strong rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">{p.contact}</h2>
            <p className="text-white/65 text-sm mt-1">{p.contactLine}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href={LINKS.telegramBot} target="_blank" rel="noreferrer" className="px-4 py-2.5 rounded-xl bg-emerald-400 text-slate-950 font-bold inline-flex items-center gap-2 hover:bg-emerald-300">
              <Bot className="w-4 h-4" /> @WMAX_uz_bot
            </a>
            <a href={LINKS.github} target="_blank" rel="noreferrer" className="glass-chip px-4 py-2.5 rounded-xl font-bold inline-flex items-center gap-2 hover:bg-white/15">
              <Code2 className="w-4 h-4" /> GitHub
            </a>
            <a href={LINKS.site} className="glass-chip px-4 py-2.5 rounded-xl font-bold inline-flex items-center gap-2 hover:bg-white/15">
              <Globe className="w-4 h-4" /> wmax.boos.uz
            </a>
            <button onClick={() => onNavigate('/demo')} className="glass-chip px-4 py-2.5 rounded-xl font-bold inline-flex items-center gap-2 hover:bg-white/15">
              <Play className="w-4 h-4 fill-current" /> {p.demo}
            </button>
          </div>
        </div>
        <p className="text-center text-[11px] text-white/40 mt-6">WMAX · Pitch Day 3.0 · {TEAM.map((m) => m.name).join(', ')}</p>
      </footer>

      <PitchChat lang={lang} />
    </div>
  );
};
