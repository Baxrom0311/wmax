import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Bot, Clock, Copy, ExternalLink, KeyRound, PlayCircle, Send, Video } from 'lucide-react';
import type { Lang } from '../i18n';
import { DEMO_VIDEO, LINKS } from './pitch/content';
import { DEMO, answerFor } from './pitch/demoContent';

interface DemoPageProps {
  lang: Lang;
  onNavigate: (route: string) => void;
}

type ChatMsg = { from: 'bot' | 'user'; text: string };

const card = 'rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm';

export const DemoPage: React.FC<DemoPageProps> = ({ lang, onNavigate }) => {
  const d = DEMO[lang];
  const [messages, setMessages] = useState<ChatMsg[]>([{ from: 'bot', text: d.chatHello }]);
  const [input, setInput] = useState('');
  const [copied, setCopied] = useState<string | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [messages]);

  const ask = (question: string, preset?: string) => {
    const q = question.trim();
    if (!q) return;
    const answer = preset ?? answerFor(lang, q) ?? d.chatFallback;
    setMessages((prev) => [...prev, { from: 'user', text: q }, { from: 'bot', text: answer }]);
    setInput('');
  };

  const origin = typeof window !== 'undefined' ? window.location.origin : LINKS.site;
  const snippets = [
    { id: 'health', code: `curl ${origin}/api/v1/health` },
    { id: 'openapi', code: `curl ${origin}${LINKS.openapi} -o wmax-openapi.json` },
  ];

  const copy = async (id: string, code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* clipboard unavailable: user can still select the text */
    }
  };

  const isExternal = (href: string) => href.startsWith('http');

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-12">
        <div>
          <button
            onClick={() => onNavigate('/')}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            {d.back}
          </button>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-950 dark:text-white">{d.title}</h1>
          <p className="text-slate-600 dark:text-slate-400 text-base sm:text-lg mt-3">{d.sub}</p>
        </div>

        {/* 6.1 Demo video */}
        <section id="video" aria-labelledby="video-title">
          <h2 id="video-title" className="text-2xl font-extrabold mb-4 flex items-center gap-2">
            <Video className="w-6 h-6 text-emerald-500" />
            {d.videoTitle}
          </h2>
          <div className="aspect-video w-full rounded-3xl overflow-hidden bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg">
            {DEMO_VIDEO.embedUrl ? (
              <iframe
                src={DEMO_VIDEO.embedUrl}
                title={d.videoTitle}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : DEMO_VIDEO.fileUrl ? (
              <video src={DEMO_VIDEO.fileUrl} poster={DEMO_VIDEO.poster} controls preload="metadata" className="w-full h-full bg-black" />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center gap-4 text-slate-300 bg-gradient-to-br from-slate-900 to-emerald-950">
                <img src={DEMO_VIDEO.poster} alt="" className="w-24 sm:w-56 opacity-80" />
                <div className="flex items-center gap-2 text-sm sm:text-base font-semibold px-4 text-center">
                  <PlayCircle className="w-5 h-5" />
                  {d.videoPending}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* 6.2 Video description */}
        <section id="tavsif" className={`${card} p-6 sm:p-8`} aria-labelledby="desc-title">
          <h2 id="desc-title" className="text-2xl font-extrabold mb-3">{d.descTitle}</h2>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6">{d.descLead}</p>
          <ol className="space-y-3">
            {d.chapters.map((c) => (
              <li key={c.t} className="flex gap-3 text-sm sm:text-base">
                <span className="inline-flex items-center gap-1 shrink-0 w-16 font-mono font-bold text-emerald-700 dark:text-emerald-400">
                  <Clock className="w-3.5 h-3.5" />
                  {c.t}
                </span>
                <span className="text-slate-700 dark:text-slate-300">{c.text}</span>
              </li>
            ))}
          </ol>
        </section>

        {/* 6.3 Working prototype */}
        <section id="prototip" aria-labelledby="proto-title">
          <h2 id="proto-title" className="text-2xl font-extrabold mb-1">{d.protoTitle}</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-5">{d.protoSub}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {d.protos.map((pr) => (
              <a
                key={pr.href}
                href={pr.href}
                target={isExternal(pr.href) ? '_blank' : undefined}
                rel={isExternal(pr.href) ? 'noreferrer' : undefined}
                className={`${card} p-5 group hover:border-emerald-500/60 transition block`}
              >
                <div className="flex items-center justify-between gap-2 font-bold text-slate-900 dark:text-white">
                  {pr.title}
                  <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-emerald-500" />
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{pr.desc}</p>
                <p className="text-xs font-mono text-emerald-700 dark:text-emerald-400 mt-3 break-all">
                  {isExternal(pr.href) ? pr.href.replace('https://', '') : `${origin.replace(/^https?:\/\//, '')}${pr.href}`}
                </p>
              </a>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Optional: Q&A chatbot */}
          <section id="chatbot" className={`${card} p-6 flex flex-col`} aria-labelledby="chat-title">
            <h2 id="chat-title" className="text-xl font-extrabold flex items-center gap-2">
              <Bot className="w-5 h-5 text-sky-500" />
              {d.chatTitle}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 mb-4">{d.chatSub}</p>
            <div className="flex-1 min-h-64 max-h-80 overflow-y-auto space-y-3 p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] px-3.5 py-2 rounded-2xl text-sm leading-relaxed ${
                      m.from === 'user'
                        ? 'bg-emerald-600 text-white rounded-br-md'
                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-200 dark:border-slate-700 rounded-bl-md'
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              ))}
              <div ref={chatEnd} />
            </div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-4 mb-2">{d.chatTry}</div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {d.qa.map((item) => (
                <button
                  key={item.q}
                  onClick={() => ask(item.q, item.a)}
                  className="px-2.5 py-1 rounded-full border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:border-emerald-500 hover:text-emerald-700 dark:hover:text-emerald-400"
                >
                  {item.q}
                </button>
              ))}
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                ask(input);
              }}
              className="flex gap-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={d.chatPlaceholder}
                className="flex-1 min-w-0 px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
              />
              <button type="submit" className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm inline-flex items-center gap-1.5">
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">{d.chatSend}</span>
              </button>
            </form>
          </section>

          {/* Optional: API access */}
          <section id="api" className={`${card} p-6`} aria-labelledby="api-title">
            <h2 id="api-title" className="text-xl font-extrabold flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-amber-500" />
              {d.apiTitle}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 mb-4">{d.apiSub}</p>
            <div className="flex flex-wrap gap-2 mb-5">
              {[
                { label: 'Swagger UI', href: LINKS.apiDocs },
                { label: 'ReDoc', href: LINKS.apiRedoc },
                { label: 'openapi.json', href: LINKS.openapi },
              ].map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3.5 py-2 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold inline-flex items-center gap-1.5"
                >
                  {l.label}
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
            <div className="space-y-3">
              {snippets.map((s) => (
                <div key={s.id} className="relative rounded-xl bg-slate-950 text-emerald-300 font-mono text-xs p-4 pt-10">
                  <code className="block whitespace-pre-wrap break-all">{s.code}</code>
                  <button
                    onClick={() => copy(s.id, s.code)}
                    className="absolute top-2.5 right-2.5 px-2 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white text-[11px] font-sans font-semibold inline-flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" />
                    {copied === s.id ? d.copied : d.copy}
                  </button>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-4">{d.apiNote}</p>
          </section>
        </div>
      </div>
    </div>
  );
};
