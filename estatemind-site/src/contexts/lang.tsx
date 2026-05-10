"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { type Locale, DEFAULT_LOCALE, isRTL, dict } from "@/lib/i18n";

interface LangCtx { locale: Locale; setLocale: (l: Locale) => void; t: typeof dict[Locale]; }
const Ctx = createContext<LangCtx>({ locale: DEFAULT_LOCALE, setLocale: () => {}, t: dict[DEFAULT_LOCALE] });

export function LangProvider({ children }: { children: React.ReactNode }) {
  // Always start with DEFAULT_LOCALE so server and client render identical HTML.
  // After hydration, restore the user's saved preference from localStorage.
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  useEffect(() => {
    const saved = localStorage.getItem("estatemind_lang") as Locale | null;
    if (saved && saved in dict) setLocaleState(saved as Locale);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = isRTL(locale) ? "rtl" : "ltr";
  }, [locale]);

  function applyLocale(l: Locale) {
    setLocaleState(l);
    localStorage.setItem("estatemind_lang", l);
  }

  return (
    <Ctx.Provider value={{ locale, setLocale: applyLocale, t: dict[locale] }}>
      {children}
    </Ctx.Provider>
  );
}

export const useLang = () => useContext(Ctx);
