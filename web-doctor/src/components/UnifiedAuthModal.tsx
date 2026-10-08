import React, { useState } from 'react';
import { X, Lock, Phone, Stethoscope, HeartHandshake, KeyRound, AlertCircle, ArrowRight } from 'lucide-react';
import type { Lang } from '../i18n';

interface UnifiedAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: Lang;
  onDoctorLogin: (token: string, user: { full_name: string; role: string }) => void;
  onRelativeLogin: (token: string, relative: { full_name: string; role: string; patients: any[] }) => void;
}

export const UnifiedAuthModal: React.FC<UnifiedAuthModalProps> = ({
  isOpen,
  onClose,
  lang,
  onDoctorLogin,
  onRelativeLogin,
}) => {
  const [activeTab, setActiveTab] = useState<'doctor' | 'relative'>('doctor');
  const [phone, setPhone] = useState('+998901234567');
  const [password, setPassword] = useState('wmax123');
  const [pin, setPin] = useState('112233');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const t = {
    uz: {
      title: "WMAX Tizimiga Kirish",
      subtitle: "Klinik mutaxassislar va bemor yaqinlari uchun yagona portal",
      doctorTab: "Shifokor / Klinika",
      relativeTab: "Oila a'zosi / Qarovchi",
      phoneLabel: "Telefon raqamingiz",
      passwordLabel: "Klinik parol",
      pinLabel: "6 xonali maxfiy PIN-kod",
      loginBtn: "Tizimga kirish",
      quickDemo: "Tezkor demo hisoblar:",
      demoDoc: "Doktor Yusupov (+998901234567)",
      demoCare: "Dilnoza (+998901110011)",
      invalid: "Telefon raqami yoki parol noto'g'ri",
      invalidPin: "PIN-kod yoki telefon raqami noto'g'ri",
      networkError: "Server bilan bog'lanishda xatolik yuz berdi",
    },
    ru: {
      title: "Вход в систему WMAX",
      subtitle: "Единый портал для врачей и родственников пациентов",
      doctorTab: "Врач / Клиника",
      relativeTab: "Член семьи / Опекун",
      phoneLabel: "Номер телефона",
      passwordLabel: "Клинический пароль",
      pinLabel: "6-значный секретный PIN-код",
      loginBtn: "Войти в систему",
      quickDemo: "Быстрые демо-аккаунты:",
      demoDoc: "Д-р Юсупов (+998901234567)",
      demoCare: "Дильноза (+998901110011)",
      invalid: "Неверный номер телефона или пароль",
      invalidPin: "Неверный номер телефона или PIN-код",
      networkError: "Ошибка подключения к серверу",
    },
    en: {
      title: "Log in to WMAX",
      subtitle: "Unified portal for clinicians and family caregivers",
      doctorTab: "Doctor / Clinic",
      relativeTab: "Family / Caregiver",
      phoneLabel: "Phone number",
      passwordLabel: "Clinical password",
      pinLabel: "6-digit secret PIN code",
      loginBtn: "Sign in",
      quickDemo: "Quick demo accounts:",
      demoDoc: "Dr. Yusupov (+998901234567)",
      demoCare: "Dilnoza (+998901110011)",
      invalid: "Invalid phone number or password",
      invalidPin: "Invalid phone number or PIN code",
      networkError: "Network connection error",
    },
  }[lang];

  const handleTabSwitch = (tab: 'doctor' | 'relative') => {
    setActiveTab(tab);
    setError(null);
    if (tab === 'doctor') {
      setPhone('+998901234567');
      setPassword('wmax123');
    } else {
      setPhone('+998901110011');
      setPin('112233');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'doctor') {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, password }),
        });
        const data = await res.json();
        if (!res.ok || !data.access_token) {
          throw new Error(data.message || t.invalid);
        }
        localStorage.setItem('wmax_token', data.access_token);
        localStorage.setItem('wmax_role', data.role || 'doctor');
        localStorage.setItem('wmax_user_name', data.full_name || 'Shifokor');
        onDoctorLogin(data.access_token, { full_name: data.full_name, role: data.role });
        onClose();
      } else {
        const res = await fetch('/api/v1/auth/relative/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, pin }),
        });
        const data = await res.json();
        if (!res.ok || !data.access_token) {
          throw new Error(data.message || t.invalidPin);
        }
        localStorage.setItem('wmax_relative_token', data.access_token);
        localStorage.setItem('wmax_relative_name', data.full_name || 'Qarovchi');
        onRelativeLogin(data.access_token, {
          full_name: data.full_name,
          role: 'relative',
          patients: data.patients || [],
        });
        onClose();
      }
    } catch (err: any) {
      setError(err.message || t.networkError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mb-3 border border-emerald-500/20">
            {activeTab === 'doctor' ? <Stethoscope className="w-6 h-6" /> : <HeartHandshake className="w-6 h-6" />}
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {t.title}
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.subtitle}
          </p>
        </div>

        {/* Role Segmented Switcher */}
        <div className="grid grid-cols-2 p-1 rounded-2xl bg-slate-100 dark:bg-slate-800/80 mb-6 border border-slate-200 dark:border-slate-700/60">
          <button
            type="button"
            onClick={() => handleTabSwitch('doctor')}
            className={`py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-2 ${
              activeTab === 'doctor'
                ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm border border-slate-200/80 dark:border-slate-700'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            {t.doctorTab}
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch('relative')}
            className={`py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-2 ${
              activeTab === 'relative'
                ? 'bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-sm border border-slate-200/80 dark:border-slate-700'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <HeartHandshake className="w-4 h-4" />
            {t.relativeTab}
          </button>
        </div>

        {/* Form Error Alert */}
        {error && (
          <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-600 dark:text-rose-300 text-xs sm:text-sm flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              {t.phoneLabel}
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+998901234567"
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>
          </div>

          {activeTab === 'doctor' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                {t.passwordLabel}
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
                />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                {t.pinLabel}
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  maxLength={6}
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="112233"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm tracking-widest font-mono bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-xl text-sm font-semibold text-white shadow-md flex items-center justify-center gap-2 transition disabled:opacity-50 ${
              activeTab === 'doctor'
                ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20'
                : 'bg-sky-600 hover:bg-sky-500 shadow-sky-500/20'
            }`}
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>{t.loginBtn}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Demo Shortcuts */}
        <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            {t.quickDemo}
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              onClick={() => {
                handleTabSwitch('doctor');
                setPhone('+998901234567');
                setPassword('wmax123');
              }}
              className="px-2.5 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition"
            >
              👨‍⚕️ {t.demoDoc}
            </button>
            <button
              type="button"
              onClick={() => {
                handleTabSwitch('relative');
                setPhone('+998901110011');
                setPin('112233');
              }}
              className="px-2.5 py-1.5 rounded-lg bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200/80 dark:border-sky-800/40 hover:bg-sky-100 dark:hover:bg-sky-900/60 transition"
            >
              👥 {t.demoCare}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
