import React, { useEffect, useRef, useState } from 'react';
import { Bot, MessageCircle, Send, X } from 'lucide-react';
import type { Lang } from '../../i18n';
import { LINKS } from './content';
import { CHAT_UI, SAMPLE_QUESTIONS, answer, isSample } from './chatbot';

const CHAT_URL = '/api/v1/public/pitch-chat';

type Msg = { from: 'bot' | 'user'; text: string; fallback?: boolean };

/* Floating Q&A chat in the bottom-right corner of the Pitch Day pages. */
export const PitchChat: React.FC<{ lang: Lang }> = ({ lang }) => {
  const ui = CHAT_UI[lang];
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const field = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = box.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open, thinking]);

  useEffect(() => {
    if (open) field.current?.focus();
  }, [open]);

  // Sample questions get the prepared answer instantly. Anything else goes to
  // DeepSeek through our backend; if that is unavailable the prepared answers
  // and the Telegram link still cover it.
  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q || thinking) return;
    setInput('');
    const history = messages.filter((m) => !m.fallback).slice(-8).map((m) => ({ role: m.from === 'user' ? 'user' : 'assistant', content: m.text }));
    setMessages((prev) => [...prev, { from: 'user', text: q }]);

    const local = answer(lang, q);
    if (local && isSample(lang, q)) {
      setMessages((prev) => [...prev, { from: 'bot', text: local }]);
      return;
    }

    setThinking(true);
    let reply: Msg;
    try {
      const res = await fetch(CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q.slice(0, 500), lang, history }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const data = (await res.json()) as { answer?: string };
      if (!data.answer) throw new Error('empty');
      reply = { from: 'bot', text: data.answer };
    } catch {
      reply = local ? { from: 'bot', text: local } : { from: 'bot', text: ui.fallback, fallback: true };
    } finally {
      setThinking(false);
    }
    setMessages((prev) => [...prev, reply]);
  };

  return (
    <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[60] flex flex-col items-end gap-3">
      {open && (
        <div className="glass glass-strong pitch-chat-panel rounded-3xl w-[min(92vw,380px)] h-[min(72svh,540px)] flex flex-col overflow-hidden text-slate-100" role="dialog" aria-label={ui.title}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div className="flex items-center gap-2 font-extrabold">
              <span className="w-8 h-8 rounded-xl bg-emerald-400/90 text-slate-950 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </span>
              {ui.title}
            </div>
            <button onClick={() => setOpen(false)} aria-label={ui.close} className="w-8 h-8 rounded-lg flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div ref={box} className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
            {[{ from: 'bot' as const, text: ui.hello }, ...messages].map((m, i) => (
              <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm leading-snug ${m.from === 'user' ? 'bg-emerald-400 text-slate-950 rounded-br-md' : 'glass-chip rounded-bl-md'}`}>
                  {m.text}
                  {'fallback' in m && m.fallback && (
                    <a href={LINKS.telegramBot} target="_blank" rel="noreferrer" className="block mt-1.5 text-emerald-300 font-semibold underline underline-offset-2">
                      {ui.telegram} →
                    </a>
                  )}
                </div>
              </div>
            ))}
            {thinking && (
              <div className="flex justify-start" aria-label={ui.thinking}>
                <div className="glass-chip rounded-2xl rounded-bl-md px-3 py-2.5 flex gap-1">
                  {[0, 1, 2].map((d) => (
                    <span key={d} className="w-1.5 h-1.5 rounded-full bg-white/70 animate-bounce" style={{ animationDelay: `${d * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="px-4 pb-2 flex gap-1.5 overflow-x-auto no-scrollbar">
            {SAMPLE_QUESTIONS(lang).map((q) => (
              <button key={q} onClick={() => void ask(q)} disabled={thinking} className="glass-chip shrink-0 rounded-full px-2.5 py-1 text-xs hover:bg-white/15">
                {q}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void ask(input);
            }}
            className="flex gap-2 p-3 pt-1"
          >
            <input
              ref={field}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={ui.placeholder}
              className="glass-chip flex-1 min-w-0 rounded-xl px-3 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-emerald-300/70"
            />
            <button type="submit" aria-label={ui.send} disabled={thinking} className="disabled:opacity-50 px-3.5 rounded-xl bg-emerald-400 text-slate-950 hover:bg-emerald-300">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? ui.close : ui.open}
        className="pitch-chat-fab w-14 h-14 rounded-full bg-emerald-400 text-slate-950 flex items-center justify-center hover:bg-emerald-300 transition"
      >
        {open ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
      </button>
    </div>
  );
};
