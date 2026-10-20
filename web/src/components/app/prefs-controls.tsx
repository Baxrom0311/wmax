import { Check, Languages, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LANGS, pick, type Lang } from "@/i18n";
import { usePrefs } from "@/lib/prefs";

const LANG_NAMES: Record<Lang, string> = { uz: "O'zbekcha", ru: "Русский", en: "English" };

export function ThemeToggle() {
  const { theme, toggleTheme, lang } = usePrefs();
  const label = pick(lang, { uz: "Mavzuni almashtirish", ru: "Сменить тему", en: "Toggle theme" });
  return (
    <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={label} title={label}>
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}

export function LangSwitcher() {
  const { lang, setLang } = usePrefs();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-1.5 font-semibold" aria-label="Language">
          <Languages />
          {lang.toUpperCase()}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {LANGS.map((item) => (
          <DropdownMenuItem key={item} onSelect={() => setLang(item)}>
            <span className="w-6 text-xs font-bold text-muted-foreground">{item.toUpperCase()}</span>
            {LANG_NAMES[item]}
            {item === lang && <Check className="ml-auto" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
