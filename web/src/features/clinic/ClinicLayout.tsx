import React, { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import {
  ArrowRight,
  ClipboardList,
  LogOut,
  Menu,
  Radio,
  Siren,
  User,
  Users,
  Watch,
  WifiOff,
} from "lucide-react";
import { Brand } from "@/components/app/brand";
import { LangSwitcher, ThemeToggle } from "@/components/app/prefs-controls";
import { DemoBanner } from "@/components/app/states";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { pick } from "@/i18n";
import { t } from "@/i18n/clinic";
import { initials } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import { cn } from "@/lib/utils";
import { useClinicData, useClinicSession } from "./session";

interface NavItem {
  to: string;
  end?: boolean;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
  tone?: "risk" | "attention";
}

function useNavItems(): NavItem[] {
  const { lang } = usePrefs();
  const { user } = useClinicSession();
  const { patients, activeSos } = useClinicData();
  const redCount = patients.filter((p) => p.level === "red").length;
  const openTasks = patients.filter((p) => p.open_task && p.open_task.status !== "done").length;
  return [
    { to: "/doctor", end: true, label: pick(lang, { uz: "Bemorlar", ru: "Пациенты", en: "Patients" }), icon: Users, count: redCount, tone: "risk" },
    {
      to: "/doctor/tasks",
      label: user?.role === "nurse"
        ? pick(lang, { uz: "Patronaj", ru: "Патронаж", en: "Patrol" })
        : pick(lang, { uz: "Vazifalar", ru: "Задачи", en: "Tasks" }),
      icon: ClipboardList,
      count: openTasks,
      tone: "attention",
    },
    { to: "/doctor/sos", label: pick(lang, { uz: "SOS dispetcher", ru: "SOS-диспетчер", en: "SOS dispatch" }), icon: Siren, count: activeSos.length, tone: "risk" },
    { to: "/doctor/devices", label: pick(lang, { uz: "Qurilmalar", ru: "Устройства", en: "Devices" }), icon: Watch },
    { to: "/doctor/profile", label: pick(lang, { uz: "Profil", ru: "Профиль", en: "Profile" }), icon: User },
  ];
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const items = useNavItems();
  return (
    <nav className="flex flex-col gap-0.5">
      {items.map(({ to, end, label, icon: Icon, count, tone }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
            )
          }
        >
          <Icon className="size-4 shrink-0" />
          <span className="flex-1 truncate">{label}</span>
          {!!count && (
            <span
              className={cn(
                "tabular min-w-5 rounded-full px-1.5 text-center text-[11px] leading-5 font-semibold",
                tone === "risk" ? "bg-risk text-white" : "bg-attention-soft text-attention-ink",
              )}
            >
              {count}
            </span>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

function RealtimeIndicator() {
  const { lang } = usePrefs();
  const { realtime } = useClinicData();
  const label =
    realtime === "live"
      ? pick(lang, { uz: "Real vaqt ulanishi faol", ru: "Онлайн-обновления активны", en: "Live updates on" })
      : realtime === "demo"
        ? pick(lang, { uz: "Demo ma'lumotlar", ru: "Демо-данные", en: "Demo data" })
        : pick(lang, { uz: "Har daqiqada yangilanadi", ru: "Обновление раз в минуту", en: "Refreshing every minute" });
  return (
    <div className="text-muted-foreground flex items-center gap-2 text-xs">
      <span className={cn("size-2 rounded-full", realtime === "live" ? "bg-good animate-pulse" : realtime === "demo" ? "bg-attention" : "bg-nodata")} />
      {label}
    </div>
  );
}

function SosAlertBar() {
  const { lang } = usePrefs();
  const { activeSos, sosStale } = useClinicData();
  const location = useLocation();
  if (location.pathname.startsWith("/doctor/sos")) return null;

  if (sosStale && activeSos.length === 0) {
    return (
      <div className="border-attention/30 bg-attention-soft text-attention-ink flex items-center gap-3 border-b px-4 py-2 text-sm">
        <WifiOff className="size-4 shrink-0" />
        {pick(lang, {
          uz: "SOS serveri bilan aloqa yo'q — yangi favqulodda chaqiruvlar ko'rinmasligi mumkin.",
          ru: "Нет связи с SOS-сервером — новые экстренные вызовы могут быть не видны.",
          en: "SOS server unreachable — new emergency calls may not be visible.",
        })}
      </div>
    );
  }
  if (activeSos.length === 0) return null;
  const raised = activeSos.filter((e) => e.status === "raised").length;
  return (
    <div role="alert" className="bg-risk flex flex-wrap items-center gap-3 px-4 py-2.5 text-sm text-white">
      <span className="relative flex size-2.5">
        <span className="absolute inline-flex size-full animate-ping rounded-full bg-white opacity-75" />
        <span className="relative inline-flex size-2.5 rounded-full bg-white" />
      </span>
      <Siren className="size-4" />
      <span className="flex-1 font-medium">
        {pick(lang, {
          uz: `Faol SOS: ${activeSos.length} ta favqulodda holat`,
          ru: `Активные SOS: ${activeSos.length}`,
          en: `Active SOS: ${activeSos.length} emergencies`,
        })}
        {raised > 0 && (
          <Badge className="ml-2 bg-white/20 text-white">{pick(lang, { uz: `${raised} ta yangi`, ru: `${raised} новых`, en: `${raised} new` })}</Badge>
        )}
      </span>
      <Button size="sm" variant="secondary" className="h-7 bg-white text-risk hover:bg-white/90" asChild>
        <Link to="/doctor/sos">
          {pick(lang, { uz: "Dispetcherni ochish", ru: "Открыть диспетчер", en: "Open dispatcher" })}
          <ArrowRight />
        </Link>
      </Button>
    </div>
  );
}

function UserMenu() {
  const { lang } = usePrefs();
  const { user, logout } = useClinicSession();
  const navigate = useNavigate();
  const name = user?.full_name || "—";
  const roleLabel = user?.role === "nurse" ? t("role.nurse", lang) : user?.role === "doctor" ? t("role.doctor", lang) : user?.role ?? "";
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-9 gap-2 px-1.5 sm:px-2">
          <Avatar className="size-7">
            <AvatarFallback>{initials(name)}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-36 truncate text-sm font-medium md:inline">{name}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col">
          <span className="truncate">{name}</span>
          <span className="text-muted-foreground text-xs font-normal">{roleLabel}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate("/doctor/profile")}>
          <User />
          {pick(lang, { uz: "Profil", ru: "Профиль", en: "Profile" })}
        </DropdownMenuItem>
        <DropdownMenuItem variant="destructive" onSelect={() => logout()}>
          <LogOut />
          {pick(lang, { uz: "Tizimdan chiqish", ru: "Выйти", en: "Sign out" })}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ClinicLayout() {
  const { lang } = usePrefs();
  const { isDemo, logout } = useClinicSession();
  const { activeSos } = useClinicData();
  const [menuOpen, setMenuOpen] = useState(false);
  const subtitle = pick(lang, { uz: "Klinik ish stansiyasi", ru: "Клиническая станция", en: "Clinical workstation" });

  return (
    <div className="bg-background flex min-h-dvh">
      {/* Desktop sidebar */}
      <aside className="bg-sidebar sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r lg:flex">
        <div className="flex h-16 items-center px-5">
          <Link to="/doctor">
            <Brand subtitle={subtitle} />
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-2">
          <NavList />
        </div>
        <div className="space-y-3 border-t p-4">
          <RealtimeIndicator />
        </div>
      </aside>

      {/* Mobile navigation */}
      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="bg-sidebar w-72 p-0">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <div className="flex h-16 items-center px-5">
            <Brand subtitle={subtitle} />
          </div>
          <div className="px-3">
            <NavList onNavigate={() => setMenuOpen(false)} />
          </div>
          <div className="mt-auto border-t p-4">
            <RealtimeIndicator />
          </div>
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        {isDemo && (
          <DemoBanner
            title={t("demo.banner_title", lang)}
            text={t("demo.banner_text", lang)}
            actionLabel={pick(lang, { uz: "Demodan chiqish", ru: "Выйти из демо", en: "Exit demo" })}
            onExit={logout}
          />
        )}
        <header className="bg-background/85 sticky top-0 z-30 flex h-14 items-center gap-2 border-b px-3 backdrop-blur sm:px-5">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMenuOpen(true)} aria-label={t("nav.menu_open", lang)}>
            <Menu />
          </Button>
          <Link to="/doctor" className="lg:hidden">
            <Brand />
          </Link>
          <div className="ml-auto flex items-center gap-1">
            {activeSos.length > 0 && (
              <Button size="sm" variant="destructive" className="mr-1 hidden sm:inline-flex" asChild>
                <Link to="/doctor/sos">
                  <Radio className="animate-pulse" />
                  SOS · {activeSos.length}
                </Link>
              </Button>
            )}
            <LangSwitcher />
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>
        <SosAlertBar />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
