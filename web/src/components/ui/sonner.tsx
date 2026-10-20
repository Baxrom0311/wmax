import { Toaster as Sonner, type ToasterProps } from "sonner";
import { usePrefs } from "@/lib/prefs";

function Toaster(props: ToasterProps) {
  const { theme } = usePrefs();
  return (
    <Sonner
      theme={theme}
      className="toaster group"
      richColors
      closeButton
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
}

export { Toaster };
