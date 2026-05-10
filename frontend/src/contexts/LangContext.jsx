import { createContext, useContext, useEffect, useState } from "react";
import { DEFAULT_LOCALE, isRTL, adminDict } from "../lib/i18n";

const LangCtx = createContext({
  locale: DEFAULT_LOCALE,
  setLocale: () => {},
  t: adminDict[DEFAULT_LOCALE],
});

export function LangProvider({ children }) {
  const [locale, setLocaleState] = useState(DEFAULT_LOCALE);

  useEffect(() => {
    const saved = localStorage.getItem("em_lang");
    if (saved && adminDict[saved]) setLocaleState(saved);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = isRTL(locale) ? "rtl" : "ltr";
  }, [locale]);

  function setLocale(l) {
    setLocaleState(l);
    localStorage.setItem("em_lang", l);
  }

  return (
    <LangCtx.Provider value={{ locale, setLocale, t: adminDict[locale] }}>
      {children}
    </LangCtx.Provider>
  );
}

export const useLang = () => useContext(LangCtx);
