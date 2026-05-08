import "server-only";

const dictionaries = {
  fr: () => import("./dictionaries/fr.json").then((m) => m.default),
  ar: () => import("./dictionaries/ar.json").then((m) => m.default),
  en: () => import("./dictionaries/en.json").then((m) => m.default),
};

export type Locale = keyof typeof dictionaries;
export const LOCALES: Locale[] = ["fr", "ar", "en"];
export const DEFAULT_LOCALE: Locale = "fr";

export const isLocale = (s: string): s is Locale => s in dictionaries;

export const getDict = (locale: Locale) => dictionaries[locale]();

export type Dict = Awaited<ReturnType<typeof getDict>>;

export const dirFor = (locale: Locale): "ltr" | "rtl" =>
  locale === "ar" ? "rtl" : "ltr";
