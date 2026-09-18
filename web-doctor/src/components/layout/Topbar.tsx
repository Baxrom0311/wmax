import React, { useRef, useState } from "react";
import {
  Bell,
  Brain,
  ChevronDown,
  Globe,
  LogOut,
  Search,
  Settings,
  User,
} from "lucide-react";
import { useAuthStore } from "../../stores/authStore";
import { useUIStore } from "../../stores/uiStore";
import { cn } from "../../utils/cn";
import { Button } from "../ui/Button";
import { useClickOutside } from "../../hooks/useClickOutside";

interface TopbarProps {
  title?: string;
  onSearchChange?: (query: string) => void;
  searchValue?: string;
  searchPlaceholder?: string;
  onAICopilot?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  title,
  onSearchChange,
  searchValue = "",
  searchPlaceholder,
  onAICopilot,
}) => {
  const { isSidebarCollapsed, lang, setLang, unreadAlertCount } = useUIStore();
  const { user, logout } = useAuthStore();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  const userMenuRef = useRef<HTMLDivElement>(null);
  const langMenuRef = useRef<HTMLDivElement>(null);

  useClickOutside(userMenuRef, () => setUserMenuOpen(false));
  useClickOutside(langMenuRef, () => setLangMenuOpen(false));

  const sidebarW = isSidebarCollapsed ? "68px" : "260px";
  const ph = searchPlaceholder ?? (lang === "uz" ? "Bemor qidiruv..." : "Поиск пациента...");

  return (
    <header
      className="fixed top-0 right-0 z-30 flex items-center gap-3 h-[60px] border-b border-[var(--line)] bg-[var(--surface)] px-4"
      style={{ left: sidebarW, transition: "left 0.3s ease" }}
    >
      {/* Page title */}
      {title && (
        <h1 className="text-base font-bold text-[var(--text)] mr-2 shrink-0 hidden sm:block">
          {title}
        </h1>
      )}

      {/* Search */}
      {onSearchChange && (
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] pointer-events-none" />
          <input
            type="search"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={ph}
            aria-label={ph}
            className="w-full h-8 pl-8 pr-3 rounded border border-[var(--line)] bg-[var(--bg)] text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-1 transition-colors"
          />
        </div>
      )}

      <div className="flex items-center gap-1 ml-auto shrink-0">
        {/* AI Copilot */}
        {onAICopilot && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onAICopilot}
            className="gap-1.5 hidden sm:flex"
          >
            <Brain className="w-3.5 h-3.5 text-[var(--good)]" />
            <span className="text-xs">AI Assistent</span>
          </Button>
        )}

        {/* Language Selector */}
        <div ref={langMenuRef} className="relative">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setLangMenuOpen((p) => !p)}
            aria-expanded={langMenuOpen}
            aria-label="Tilni o'zgartirish"
          >
            <Globe className="w-4 h-4" />
          </Button>
          {langMenuOpen && (
            <div className="absolute top-full right-0 mt-1 w-28 rounded-md border border-[var(--line)] bg-[var(--surface)] shadow-lg py-1 z-50">
              {(["uz", "ru"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => { setLang(l); setLangMenuOpen(false); }}
                  className={cn(
                    "w-full text-left px-3 py-1.5 text-sm transition-colors",
                    lang === l
                      ? "text-[var(--text)] font-semibold bg-[var(--surface-hover)]"
                      : "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
                  )}
                >
                  {l === "uz" ? "🇺🇿 O'zbekcha" : "🇷🇺 Русский"}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notifications */}
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            aria-label={`${unreadAlertCount} yangi signal`}
          >
            <Bell className="w-4 h-4" />
          </Button>
          {unreadAlertCount > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[var(--risk)] text-white text-[9px] font-bold flex items-center justify-center pointer-events-none">
              {unreadAlertCount > 9 ? "9+" : unreadAlertCount}
            </span>
          )}
        </div>

        {/* User Menu */}
        <div ref={userMenuRef} className="relative">
          <button
            onClick={() => setUserMenuOpen((p) => !p)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-[var(--surface-hover)] transition-colors text-sm"
            aria-expanded={userMenuOpen}
            aria-haspopup="true"
          >
            <div className="w-7 h-7 rounded-full bg-[var(--good)] flex items-center justify-center text-white text-xs font-bold shrink-0">
              {(user?.full_name ?? "D")[0].toUpperCase()}
            </div>
            <span className="font-medium text-[var(--text)] hidden md:block max-w-[120px] truncate">
              {user?.full_name ?? "Dr. Alimov"}
            </span>
            <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />
          </button>

          {userMenuOpen && (
            <div className="absolute top-full right-0 mt-1 w-48 rounded-md border border-[var(--line)] bg-[var(--surface)] shadow-lg py-1 z-50">
              <div className="px-3 py-2 border-b border-[var(--line-light)]">
                <div className="text-xs font-semibold text-[var(--text)] truncate">
                  {user?.full_name ?? "Dr. Alimov"}
                </div>
                <div className="text-[10px] text-[var(--text-muted)]">{user?.role ?? "doctor"}</div>
              </div>
              <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] transition-colors">
                <User className="w-4 h-4" />
                {lang === "uz" ? "Profil" : "Профиль"}
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] transition-colors">
                <Settings className="w-4 h-4" />
                {lang === "uz" ? "Sozlamalar" : "Настройки"}
              </button>
              <div className="border-t border-[var(--line-light)] mt-1 pt-1">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--risk)] hover:bg-[var(--risk-bg)] transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  {lang === "uz" ? "Chiqish" : "Выйти"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
