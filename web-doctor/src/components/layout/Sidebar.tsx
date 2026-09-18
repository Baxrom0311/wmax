import React from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  ChevronLeft,
  ChevronRight,
  FileText,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Moon,
  Settings,
  Sun,
  Users,
} from "lucide-react";
import { useAuthStore } from "../../stores/authStore";
import { useUIStore } from "../../stores/uiStore";
import { cn } from "../../utils/cn";
import { Button } from "../ui/Button";

interface NavItem {
  id: string;
  label: string;
  label_ru: string;
  icon: React.ReactNode;
  badge?: number;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: "patients",
    label: "Bemorlar ro'yxati",
    label_ru: "Список пациентов",
    icon: <Users className="w-4 h-4" />,
  },
  {
    id: "alerts",
    label: "Signallar",
    label_ru: "Сигналы",
    icon: <AlertTriangle className="w-4 h-4" />,
  },
  {
    id: "activity",
    label: "Faoliyat",
    label_ru: "Активность",
    icon: <Activity className="w-4 h-4" />,
  },
  {
    id: "ai",
    label: "AI Assistent",
    label_ru: "ИИ Ассистент",
    icon: <Brain className="w-4 h-4" />,
  },
];

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  unreadAlerts?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  unreadAlerts = 0,
}) => {
  const { isSidebarCollapsed, toggleSidebar, theme, setTheme, lang } = useUIStore();
  const { user, logout } = useAuthStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 bottom-0 z-40 flex flex-col border-r border-[var(--line)] bg-[var(--surface)] transition-all duration-300 ease-in-out",
        isSidebarCollapsed ? "w-[68px]" : "w-[260px]"
      )}
      aria-label="Asosiy navigatsiya"
    >
      {/* Logo */}
      <div
        className={cn(
          "flex items-center border-b border-[var(--line)] h-[60px] px-4 shrink-0",
          isSidebarCollapsed ? "justify-center" : "justify-between"
        )}
      >
        {!isSidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-[var(--good)] flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight text-[var(--text)]">NAZORAT</div>
              <div className="text-[10px] text-[var(--text-muted)] leading-tight">
                {lang === "uz" ? "Shifokor Paneli" : "Панель Врача"}
              </div>
            </div>
          </div>
        )}
        {isSidebarCollapsed && (
          <div className="w-7 h-7 rounded bg-[var(--good)] flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
        )}

        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          aria-label={isSidebarCollapsed ? "Kengaytirish" : "Yig'ish"}
          className={cn(
            "text-[var(--text-muted)] hover:text-[var(--text)] shrink-0",
            isSidebarCollapsed && "ml-0"
          )}
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5" role="navigation">
        {/* Dashboard shortcut */}
        <button
          onClick={() => onNavigate("patients")}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors text-left",
            activePage === "dashboard"
              ? "bg-[var(--surface-active)] text-[var(--text)]"
              : "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          )}
          aria-current={activePage === "dashboard" ? "page" : undefined}
        >
          <LayoutDashboard className="w-4 h-4 shrink-0" />
          {!isSidebarCollapsed && <span>{lang === "uz" ? "Boshqaruv paneli" : "Панель управления"}</span>}
        </button>

        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors text-left relative",
              activePage === item.id
                ? "bg-[var(--surface-active)] text-[var(--text)]"
                : "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
            )}
            aria-current={activePage === item.id ? "page" : undefined}
            title={isSidebarCollapsed ? (lang === "uz" ? item.label : item.label_ru) : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!isSidebarCollapsed && (
              <span className="flex-1">{lang === "uz" ? item.label : item.label_ru}</span>
            )}
            {/* Badge for alerts */}
            {item.id === "alerts" && unreadAlerts > 0 && (
              <span
                className={cn(
                  "bg-[var(--risk)] text-white text-[10px] font-bold rounded-full flex items-center justify-center shrink-0",
                  isSidebarCollapsed
                    ? "absolute top-1 right-1 w-4 h-4 text-[9px]"
                    : "w-5 h-5"
                )}
                aria-label={`${unreadAlerts} yangi signal`}
              >
                {unreadAlerts > 9 ? "9+" : unreadAlerts}
              </span>
            )}
          </button>
        ))}

        {/* Divider */}
        <div className="my-2 border-t border-[var(--line-light)]" />

        <button
          onClick={() => onNavigate("reports")}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors text-left",
            "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          )}
          title={isSidebarCollapsed ? (lang === "uz" ? "Hisobotlar" : "Отчёты") : undefined}
        >
          <FileText className="w-4 h-4 shrink-0" />
          {!isSidebarCollapsed && <span>{lang === "uz" ? "Hisobotlar" : "Отчёты"}</span>}
        </button>
        <button
          onClick={() => onNavigate("help")}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors text-left",
            "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]"
          )}
          title={isSidebarCollapsed ? (lang === "uz" ? "Yordam" : "Помощь") : undefined}
        >
          <HelpCircle className="w-4 h-4 shrink-0" />
          {!isSidebarCollapsed && <span>{lang === "uz" ? "Yordam" : "Помощь"}</span>}
        </button>
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--line)] p-3 space-y-1 shrink-0">
        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] transition-colors"
          aria-label={theme === "dark" ? "Kunduzgi rejim" : "Tungi rejim"}
          title={isSidebarCollapsed ? (theme === "dark" ? "Yorug' rejim" : "Qorong'i rejim") : undefined}
        >
          {theme === "dark" ? (
            <Sun className="w-4 h-4 shrink-0" />
          ) : (
            <Moon className="w-4 h-4 shrink-0" />
          )}
          {!isSidebarCollapsed && (
            <span>{theme === "dark" ? (lang === "uz" ? "Kunduzgi rejim" : "Светлый режим") : (lang === "uz" ? "Tungi rejim" : "Тёмный режим")}</span>
          )}
        </button>

        {/* Settings */}
        <button
          onClick={() => onNavigate("settings")}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] transition-colors"
          title={isSidebarCollapsed ? (lang === "uz" ? "Sozlamalar" : "Настройки") : undefined}
        >
          <Settings className="w-4 h-4 shrink-0" />
          {!isSidebarCollapsed && <span>{lang === "uz" ? "Sozlamalar" : "Настройки"}</span>}
        </button>

        {/* User info + logout */}
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-md",
            isSidebarCollapsed ? "justify-center" : "justify-between"
          )}
        >
          {!isSidebarCollapsed && (
            <div className="min-w-0">
              <div className="text-xs font-semibold text-[var(--text)] truncate">
                {user?.full_name ?? "Dr. Alimov"}
              </div>
              <div className="text-[10px] text-[var(--text-muted)] truncate">
                {user?.role ?? "doctor"}
              </div>
            </div>
          )}
          <button
            onClick={logout}
            className="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--risk)] hover:bg-[var(--risk-bg)] transition-colors"
            aria-label="Tizimdan chiqish"
            title={lang === "uz" ? "Chiqish" : "Выйти"}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
