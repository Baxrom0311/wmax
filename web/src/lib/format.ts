import { LOCALE, pick, type Lang } from "@/i18n";

export function formatDateTime(iso: string | null | undefined, lang: Lang): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(LOCALE[lang], {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(iso: string | null | undefined, lang: Lang): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString(LOCALE[lang], { hour: "2-digit", minute: "2-digit" });
}

export function formatDate(iso: string | null | undefined, lang: Lang): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(LOCALE[lang], { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** "5 daqiqa oldin" style age of a timestamp; `now` is passed in so callers control re-rendering. */
export function formatAgo(iso: string | null | undefined, lang: Lang, now: number): string {
  if (!iso) return pick(lang, { uz: "o'lchov yo'q", ru: "нет измерений", en: "no readings" });
  const mins = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000));
  if (mins < 1) return pick(lang, { uz: "hozirgina", ru: "только что", en: "just now" });
  if (mins < 60) return pick(lang, { uz: `${mins} daq. oldin`, ru: `${mins} мин назад`, en: `${mins} min ago` });
  const hours = Math.round(mins / 60);
  if (hours < 48) return pick(lang, { uz: `${hours} soat oldin`, ru: `${hours} ч назад`, en: `${hours} h ago` });
  const days = Math.round(hours / 24);
  return pick(lang, { uz: `${days} kun oldin`, ru: `${days} дн назад`, en: `${days} d ago` });
}

/** Remaining time until `iso`; negative values mean overdue. */
export function msUntil(iso: string | null | undefined, now: number): number | null {
  if (!iso) return null;
  return new Date(iso).getTime() - now;
}

export function formatCountdown(ms: number, lang: Lang): string {
  if (ms <= 0) return pick(lang, { uz: "Muddati o'tgan", ru: "Просрочено", en: "Overdue" });
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return pick(lang, { uz: `${h} soat ${m} daq. qoldi`, ru: `осталось ${h} ч ${m} мин`, en: `${h}h ${m}m left` });
}

export function initials(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter((w) => w && !/^(dr\.?|hamshira|д-р)$/i.test(w))
      .map((w) => w[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "W"
  );
}

export function formatUzs(value: number): string {
  return value.toLocaleString("ru-RU").replace(/,/g, " ");
}
