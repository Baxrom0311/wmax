export type Lang = "uz" | "ru" | "en";

export const LANGS: Lang[] = ["uz", "ru", "en"];

export const LOCALE: Record<Lang, string> = {
  uz: "uz-Latn-UZ",
  ru: "ru-RU",
  en: "en-US",
};

/** Small inline dictionary helper for strings that only one screen uses. */
export function pick<T>(lang: Lang, dict: Record<Lang, T>): T {
  return dict[lang] ?? dict.uz;
}
