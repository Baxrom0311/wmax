import React, { useRef, useState } from 'react';
import { Copy, ExternalLink, KeyRound } from 'lucide-react';
import type { Lang } from '../i18n';
import { DEMO_VIDEO, LINKS } from './pitch/content';
import { DEMO } from './pitch/demoContent';
import { PitchChat } from './pitch/PitchChat';
import { PitchTopBar } from './pitch/PitchHome';
import './pitch/pitch.css';

interface DemoPageProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  onNavigate: (route: string) => void;
}

export const DemoPage: React.FC<DemoPageProps> = ({ lang, onLangChange, onNavigate }) => {
  const d = DEMO[lang];
  const [copied, setCopied] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const seek = (t: string) => {
    const v = videoRef.current;
    if (!v) return;
    const [m, s] = t.split(':').map(Number);
    v.currentTime = m * 60 + s;
    void v.play().catch(() => undefined);
  };

  const origin = window.location.origin;
  const curl = `curl ${origin}/api/v1/health`;
  const isExternal = (href: string) => href.startsWith('http');

  return (
    <div className="pitch-root">
      <div className="pitch-blob b1" />
      <div className="pitch-blob b2" />
      <div className="pitch-blob b3" />
      <PitchTopBar lang={lang} onLangChange={onLangChange} onNavigate={onNavigate} page="demo" />

      <main className="relative z-10 max-w-6xl mx-auto px-4 sm:px-8 pt-[7.5rem] lg:pt-24 pb-28 space-y-5">
        {/* 6.1 Video + 6.2 description */}
        <section className="glass glass-strong rounded-3xl p-3 sm:p-4">
          <div className="aspect-video w-full rounded-2xl overflow-hidden bg-black">
            {DEMO_VIDEO.embedUrl ? (
              <iframe src={DEMO_VIDEO.embedUrl} title={d.videoTitle} className="w-full h-full" allow="autoplay; encrypted-media; picture-in-picture" allowFullScreen />
            ) : (
              <video ref={videoRef} src={DEMO_VIDEO.fileUrl} poster={DEMO_VIDEO.poster} controls preload="metadata" className="w-full h-full" />
            )}
          </div>
          <div className="px-1 sm:px-2 pt-4 pb-1 flex flex-col lg:flex-row lg:items-center gap-3 justify-between">
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight">{d.videoTitle}</h1>
              <p className="text-sm text-white/65">{d.descLead}</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {d.chapters.map((c) => (
                <button key={c.t} onClick={() => seek(c.t)} className="glass-chip rounded-lg px-2.5 py-1 text-xs hover:bg-white/15">
                  <span className="font-mono text-emerald-300 mr-1">{c.t}</span>
                  {c.text}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* 6.3 Working prototype */}
        <section>
          <h2 className="text-sm uppercase tracking-wider text-white/55 font-bold mb-2 px-1">{d.protoTitle}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {d.protos.map((pr) => (
              <a
                key={pr.href}
                href={pr.href}
                target={isExternal(pr.href) ? '_blank' : undefined}
                rel={isExternal(pr.href) ? 'noreferrer' : undefined}
                className="glass rounded-2xl p-4 flex items-center justify-between gap-3 hover:bg-white/10 transition"
              >
                <div>
                  <div className="font-bold">{pr.title}</div>
                  <div className="text-xs text-white/60">{pr.desc}</div>
                </div>
                <ExternalLink className="w-4 h-4 text-emerald-300 shrink-0" />
              </a>
            ))}
          </div>
        </section>

        {/* Optional: API access (the Q&A chatbot is the floating button) */}
        <div>
          <section className="glass rounded-3xl p-4">
            <h2 className="font-extrabold flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-amber-300" />
              {d.apiTitle}
            </h2>
            <p className="text-xs text-white/60 mt-1">{d.apiSub}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {[
                { label: 'Swagger', href: LINKS.apiDocs },
                { label: 'ReDoc', href: LINKS.apiRedoc },
                { label: 'OpenAPI', href: LINKS.openapi },
              ].map((l) => (
                <a key={l.href} href={l.href} target="_blank" rel="noreferrer" className="glass-chip rounded-xl px-3 py-1.5 text-sm font-semibold inline-flex items-center gap-1.5 hover:bg-white/15">
                  {l.label}
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
            <div className="mt-3 rounded-xl bg-black/40 border border-white/10 p-3 font-mono text-xs text-emerald-200 flex items-start justify-between gap-2">
              <code className="break-all">{curl}</code>
              <button
                onClick={() => {
                  navigator.clipboard
                    .writeText(curl)
                    .then(() => {
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    })
                    .catch(() => undefined);
                }}
                aria-label={d.copy}
                className="shrink-0 text-white/70 hover:text-white"
              >
                {copied ? <span className="font-sans text-[11px]">{d.copied}</span> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-[11px] text-white/45 mt-3">{d.apiNote}</p>
          </section>
        </div>
      </main>
      <PitchChat lang={lang} />
    </div>
  );
};
