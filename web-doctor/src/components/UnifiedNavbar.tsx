import React, { useState, useRef, useEffect } from 'react';
import {
  Activity,
  Stethoscope,
  HeartHandshake,
  Presentation,
  Sun,
  Moon,
  Globe,
  LogIn,
  LogOut,
  Menu,
  X,
  ChevronDown,
} from 'lucide-react';
import type { Lang } from '../i18n';

interface UnifiedNavbarProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  doctorUser?: { full_name: string; role: string } | null;
  relativeUser?: { full_name: string; role: string } | null;
  onOpenLogin: () => void;
  onLogoutDoctor: () => void;
  onLogoutRelative: () => void;
  doctorActiveTab?: string;
  onDoctorTabChange?: (tab: string) => void;
  sosCount?: number;
}

export const UnifiedNavbar: React.FC<UnifiedNavbarProps> = ({
  currentRoute,
  onNavigate,
  lang,
  onLangChange,
  theme,
  onToggleTheme,
  doctorUser,
  relativeUser,
  onOpenLogin,
  onLogoutDoctor,
  onLogoutRelative,
  doctorActiveTab: _doctorActiveTab = 'patients',
  onDoctorTabChange: _onDoctorTabChange,
  sosCount = 0,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const langRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const t = {
    uz: {
      home: "Bosh sahifa",
      clinic: "Klinika",
      relative: "Oila & Qarovchi",
      presentation: "Taqdimot",
      login: "Kirish",
      logout: "Chiqish",
      doctorRole: "Klinik Shifokor",
      caregiverRole: "Bemor Qarovchisi",
      patients: "Bemorlar",
      handoffs: "Navbatchilik",
      sos: "SOS Chaqiruvlar",
      profile: "Profil",
    },
    ru: {
      home: "Главная",
      clinic: "Клиника",
      relative: "Семья & Опекун",
      presentation: "Презентация",
      login: "Войти",
      logout: "Выйти",
      doctorRole: "Врач-кардиолог",
      caregiverRole: "Опекун пациента",
      patients: "Пациенты",
      handoffs: "Дежурство",
      sos: "SOS Вызовы",
      profile: "Профиль",
    },
    en: {
      home: "Home",
      clinic: "Clinic",
      relative: "Family & Caregiver",
      presentation: "Slides",
      login: "Sign In",
      logout: "Sign Out",
      doctorRole: "Cardiologist",
      caregiverRole: "Family Caregiver",
      patients: "Patients",
      handoffs: "Handoffs",
      sos: "SOS Alerts",
      profile: "Profile",
    },
  }[lang];

  const isDoctorRoute = currentRoute.startsWith('/doctor');
  const isRelativeRoute = currentRoute.startsWith('/r') || currentRoute.startsWith('/relative');

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <button
            onClick={() => onNavigate('/')}
            className="flex items-center gap-2.5 group focus:outline-none"
          >
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 to-sky-500 p-0.5 shadow-md shadow-emerald-500/20 group-hover:scale-105 transition">
              <div className="w-full h-full bg-white dark:bg-slate-900 rounded-[14px] flex items-center justify-center">
                <Activity className="w-5 h-5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
              </div>
            </div>
            <div className="text-left">
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg sm:text-xl tracking-tight text-slate-900 dark:text-white">
                  WMAX
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  RPM
                </span>
              </div>
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block -mt-1">
                Telehealth & Telemonitoring
              </span>
            </div>
          </button>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-200 dark:border-slate-800">
            <button
              onClick={() => onNavigate('/')}
              className={`px-3 py-2 rounded-xl text-sm font-semibold transition ${
                currentRoute === '/'
                  ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/50'
              }`}
            >
              {t.home}
            </button>
            <button
              onClick={() => onNavigate('/doctor')}
              className={`px-3 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-1.5 ${
                isDoctorRoute
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800/40'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/50'
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              {t.clinic}
              {sosCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold animate-pulse">
                  {sosCount}
                </span>
              )}
            </button>
            <button
              onClick={() => onNavigate('/r')}
              className={`px-3 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-1.5 ${
                isRelativeRoute
                  ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 border border-sky-200/80 dark:border-sky-800/40'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/50'
              }`}
            >
              <HeartHandshake className="w-4 h-4" />
              {t.relative}
            </button>
            <button
              onClick={() => onNavigate('/pptx')}
              className={`px-3 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-1.5 ${
                currentRoute === '/pptx'
                  ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border border-purple-200/80 dark:border-purple-800/40'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/50'
              }`}
            >
              <Presentation className="w-4 h-4" />
              {t.presentation}
            </button>
          </nav>
        </div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={onToggleTheme}
            className="p-2 sm:p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title={theme === 'dark' ? "Yorug' mavzu" : "Qorong'i mavzu"}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          {/* Language Selector Popover */}
          <div className="relative" ref={langRef}>
            <button
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="inline-flex items-center gap-1.5 px-2.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="uppercase">{lang}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {langMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-32 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-150">
                {(['uz', 'ru', 'en'] as Lang[]).map((l) => (
                  <button
                    key={l}
                    onClick={() => {
                      onLangChange(l);
                      setLangMenuOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-xs font-semibold flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition ${
                      lang === l ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <span>{l === 'uz' ? "O'zbekcha" : l === 'ru' ? 'Русский' : 'English'}</span>
                    {lang === l && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Auth State Button */}
          {doctorUser ? (
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition"
              >
                <div className="w-7 h-7 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xs">
                  {doctorUser.full_name.charAt(0)}
                </div>
                <div className="text-left hidden sm:block">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block leading-tight">
                    {doctorUser.full_name}
                  </span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block font-medium">
                    {t.doctorRole}
                  </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
              </button>

              {profileOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="p-2 border-b border-slate-100 dark:border-slate-800 mb-1">
                    <p className="text-xs font-bold text-slate-900 dark:text-white">{doctorUser.full_name}</p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{t.doctorRole}</p>
                  </div>
                  <button
                    onClick={() => {
                      onNavigate('/doctor');
                      setProfileOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition flex items-center gap-2"
                  >
                    <Stethoscope className="w-3.5 h-3.5 text-emerald-500" />
                    <span>{t.clinic}</span>
                  </button>
                  <button
                    onClick={() => {
                      onLogoutDoctor();
                      setProfileOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition flex items-center gap-2 mt-1"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{t.logout}</span>
                  </button>
                </div>
              )}
            </div>
          ) : relativeUser ? (
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-2xl bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800/60 hover:bg-sky-100 dark:hover:bg-sky-900/40 transition"
              >
                <div className="w-7 h-7 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold text-xs">
                  {relativeUser.full_name.charAt(0)}
                </div>
                <div className="text-left hidden sm:block">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block leading-tight">
                    {relativeUser.full_name}
                  </span>
                  <span className="text-[10px] text-sky-600 dark:text-sky-400 block font-medium">
                    {t.caregiverRole}
                  </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
              </button>

              {profileOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="p-2 border-b border-slate-100 dark:border-slate-800 mb-1">
                    <p className="text-xs font-bold text-slate-900 dark:text-white">{relativeUser.full_name}</p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{t.caregiverRole}</p>
                  </div>
                  <button
                    onClick={() => {
                      onNavigate('/r');
                      setProfileOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition flex items-center gap-2"
                  >
                    <HeartHandshake className="w-3.5 h-3.5 text-sky-500" />
                    <span>{t.relative}</span>
                  </button>
                  <button
                    onClick={() => {
                      onLogoutRelative();
                      setProfileOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition flex items-center gap-2 mt-1"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{t.logout}</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 text-xs sm:text-sm font-semibold transition shadow-sm"
            >
              <LogIn className="w-4 h-4" />
              <span>{t.login}</span>
            </button>
          )}

          {/* Mobile Menu Hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-2 animate-in slide-in-from-top-2 duration-150">
          <button
            onClick={() => {
              onNavigate('/');
              setMobileMenuOpen(false);
            }}
            className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-semibold transition ${
              currentRoute === '/'
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            {t.home}
          </button>
          <button
            onClick={() => {
              onNavigate('/doctor');
              setMobileMenuOpen(false);
            }}
            className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-semibold transition flex items-center justify-between ${
              isDoctorRoute
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <span className="flex items-center gap-2">
              <Stethoscope className="w-4 h-4" />
              {t.clinic}
            </span>
            {sosCount > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-rose-500 text-white text-xs font-bold">
                {sosCount} SOS
              </span>
            )}
          </button>
          <button
            onClick={() => {
              onNavigate('/r');
              setMobileMenuOpen(false);
            }}
            className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
              isRelativeRoute
                ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <HeartHandshake className="w-4 h-4" />
            {t.relative}
          </button>
          <button
            onClick={() => {
              onNavigate('/pptx');
              setMobileMenuOpen(false);
            }}
            className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
              currentRoute === '/pptx'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <Presentation className="w-4 h-4" />
            {t.presentation}
          </button>
        </div>
      )}
    </header>
  );
};
