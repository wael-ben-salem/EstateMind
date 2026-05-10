"use client";
import { useLang } from "@/contexts/lang";
import { LOCALES, type Locale } from "@/lib/i18n";

const LABELS: Record<Locale, string> = { fr: "FR", ar: "AR", en: "EN" };

export function LangSwitcher() {
  const { locale, setLocale } = useLang();
  return (
    <div className="flex items-center gap-0.5">
      {LOCALES.map(l => (
        <button key={l} onClick={() => setLocale(l)}
                className="px-2 py-1 rounded-lg text-xs font-bold uppercase transition-all"
                style={l === locale
                  ? { background: "var(--color-gold)", color: "var(--color-navy)" }
                  : { color: "white", opacity: 0.5 }}>
          {LABELS[l]}
        </button>
      ))}
    </div>
  );
}
