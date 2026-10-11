import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Bot,
  CheckCircle2,
  Circle,
  Code2,
  ExternalLink,
  Lightbulb,
  Map as MapIcon,
  Rocket,
  ShieldCheck,
  Users,
  Watch,
  Workflow,
  MonitorSmartphone,
  PlayCircle,
} from 'lucide-react';
import type { Lang } from '../../i18n';
import { LINKS, PITCH, TEAM, TECH } from './content';

interface PitchSectionsProps {
  lang: Lang;
  onNavigate: (route: string) => void;
}

const SectionHeader: React.FC<{ tag: string; title: string; sub?: string; icon: React.ReactNode }> = ({ tag, title, sub, icon }) => (
  <div className="max-w-3xl mb-10 sm:mb-14">
    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-3">
      {icon}
      <span>{tag}</span>
    </div>
    <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white">{title}</h2>
    {sub && <p className="text-slate-600 dark:text-slate-400 text-base sm:text-lg mt-3">{sub}</p>}
  </div>
);

const card = 'rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm';

export const PitchSections: React.FC<PitchSectionsProps> = ({ lang, onNavigate }) => {
  const p = PITCH[lang];
  const solutionIcons = [<Watch key="w" className="w-6 h-6" />, <Workflow key="f" className="w-6 h-6" />, <MonitorSmartphone key="m" className="w-6 h-6" />];

  return (
    <>
      {/* 1. Problem → Solution */}
      <section id="muammo" className="py-16 sm:py-24 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader tag={p.problemTag} title={p.problemTitle} sub={p.problemLead} icon={<AlertTriangle className="w-3.5 h-3.5" />} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 items-stretch">
            <ul className={`${card} p-6 sm:p-8 space-y-4`}>
              {p.problemPoints.map((pt) => (
                <li key={pt} className="flex gap-3 text-sm sm:text-base text-slate-700 dark:text-slate-300 leading-relaxed">
                  <AlertTriangle className="w-5 h-5 shrink-0 text-rose-500 mt-0.5" />
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
            <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-br from-emerald-600 to-teal-700 text-white shadow-lg shadow-emerald-600/20">
              <div className="flex items-center gap-2 text-emerald-100 text-xs font-bold uppercase tracking-wider mb-2">
                <ArrowRight className="w-4 h-4" />
                <span>{lang === 'uz' ? 'Yechim' : lang === 'ru' ? 'Решение' : 'Solution'}</span>
              </div>
              <h3 className="text-2xl font-extrabold mb-2">{p.solutionTitle}</h3>
              <p className="text-emerald-50/90 text-sm sm:text-base mb-6">{p.solutionLead}</p>
              <div className="space-y-4">
                {p.solutionPoints.map((s, i) => (
                  <div key={s.title} className="flex gap-4 p-4 rounded-2xl bg-white/10 border border-white/15">
                    <div className="w-11 h-11 shrink-0 rounded-xl bg-white/15 flex items-center justify-center">{solutionIcons[i]}</div>
                    <div>
                      <div className="font-bold">{s.title}</div>
                      <div className="text-sm text-emerald-50/90 leading-relaxed">{s.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Team */}
      <section id="jamoa" className="py-16 sm:py-24 bg-white dark:bg-slate-900/60 border-y border-slate-200/80 dark:border-slate-800 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader tag={p.teamTag} title={p.teamTitle} sub={p.teamSub} icon={<Users className="w-3.5 h-3.5" />} />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TEAM.map((m) => (
              <div key={m.name} className={`${card} p-6 flex flex-col`}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-sky-500 text-white font-extrabold flex items-center justify-center">
                    {m.name.split(' ').map((w) => w[0]).join('').slice(0, 2)}
                  </div>
                  <div className="font-bold text-lg text-slate-900 dark:text-white">{m.name}</div>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-4">{m.role[lang]}</p>
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {m.skills.map((s) => (
                    <span key={s} className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300">{s}</span>
                  ))}
                </div>
                <div className="mt-auto flex flex-wrap gap-3">
                  {m.links.map((l) => (
                    <a key={l.url} href={l.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 dark:text-emerald-400 hover:underline">
                      {l.label}
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-12 mb-5">{p.techTitle}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {TECH.map((g) => (
              <div key={g.group} className={`${card} p-5`}>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">{g.group}</div>
                <div className="flex flex-wrap gap-1.5">
                  {g.items.map((it) => (
                    <span key={it} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 text-xs font-semibold">{it}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <a href={LINKS.github} target="_blank" rel="noreferrer" className="px-5 py-3 rounded-2xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold text-sm inline-flex items-center gap-2">
              <Code2 className="w-4 h-4" />
              {p.ctaGithub}
            </a>
            <a href={LINKS.telegramBot} target="_blank" rel="noreferrer" className="px-5 py-3 rounded-2xl border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-100 font-bold text-sm inline-flex items-center gap-2">
              <Bot className="w-4 h-4 text-sky-500" />
              Telegram bot
            </a>
          </div>
        </div>
      </section>

      {/* 3. Why us */}
      <section id="nima-uchun" className="py-16 sm:py-24 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader tag={p.whyTag} title={p.whyTitle} icon={<BadgeCheck className="w-3.5 h-3.5" />} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {p.whyPoints.map((w) => (
              <div key={w.title} className={`${card} p-6 flex gap-4`}>
                <ShieldCheck className="w-7 h-7 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <div className="font-bold text-slate-900 dark:text-white mb-1">{w.title}</div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{w.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Roadmap */}
      <section id="yol-xaritasi" className="py-16 sm:py-24 bg-white dark:bg-slate-900/60 border-y border-slate-200/80 dark:border-slate-800 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader tag={p.roadmapTag} title={p.roadmapTitle} sub={p.roadmapSub} icon={<MapIcon className="w-3.5 h-3.5" />} />
          <ol className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {p.stages.map((s) => {
              const tone =
                s.status === 'done'
                  ? 'border-emerald-300 dark:border-emerald-800'
                  : s.status === 'current'
                    ? 'border-sky-400 dark:border-sky-600 ring-2 ring-sky-400/30'
                    : 'border-slate-200 dark:border-slate-800';
              const badge =
                s.status === 'done'
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400'
                  : s.status === 'current'
                    ? 'bg-sky-500 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400';
              return (
                <li key={s.key} className={`rounded-3xl bg-white dark:bg-slate-900 border p-6 ${tone}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400">{s.key}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${badge}`}>{p.statusLabels[s.status]}</span>
                  </div>
                  <div className="text-xl font-extrabold text-slate-900 dark:text-white mb-3">{s.title}</div>
                  <ul className="space-y-2">
                    {s.items.map((it) => (
                      <li key={it} className="flex gap-2 text-sm text-slate-600 dark:text-slate-400">
                        {s.status === 'next' ? (
                          <Circle className="w-4 h-4 shrink-0 mt-0.5 text-slate-400" />
                        ) : (
                          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" />
                        )}
                        <span>{it}</span>
                      </li>
                    ))}
                  </ul>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      {/* 5. Implementation plan */}
      <section id="reja" className="py-16 sm:py-24 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionHeader tag={p.planTag} title={p.planTitle} sub={p.planSub} icon={<Rocket className="w-3.5 h-3.5" />} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
            {p.phases.map((ph, i) => (
              <div key={ph.title} className={`${card} p-6`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-bold flex items-center justify-center">{i + 1}</span>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{ph.when}</span>
                </div>
                <div className="font-bold text-lg text-slate-900 dark:text-white mb-2">{ph.title}</div>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{ph.desc}</p>
              </div>
            ))}
          </div>

          <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Lightbulb className="w-6 h-6 text-amber-500" />
            {p.aiTitle}
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[
              { label: p.aiProductLabel, items: p.aiProduct },
              { label: p.aiDevLabel, items: p.aiDev },
            ].map((col) => (
              <div key={col.label} className={`${card} p-6`}>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-4">{col.label}</div>
                <div className="space-y-4">
                  {col.items.map((a) => (
                    <div key={a.title} className="flex gap-3">
                      <Bot className="w-5 h-5 shrink-0 text-sky-500 mt-0.5" />
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white text-sm">{a.title}</div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">{a.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <p className="mt-8 text-xs sm:text-sm text-slate-500 dark:text-slate-400 border-l-4 border-amber-400 pl-4">{p.honesty}</p>

          <div className="mt-10 flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('/demo')}
              className="px-6 py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm sm:text-base shadow-lg shadow-emerald-600/25 inline-flex items-center gap-2.5 transition"
            >
              <PlayCircle className="w-5 h-5" />
              {p.ctaDemo}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>
    </>
  );
};
