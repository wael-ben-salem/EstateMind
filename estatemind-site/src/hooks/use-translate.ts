"use client";
import { useState, useEffect } from "react";
import { type Locale } from "@/lib/i18n";

// Module-level cache — survives re-renders, cleared on full page refresh
const cache = new Map<string, string>();

const LANG_CODE: Record<Locale, string> = { fr: "fr", en: "en", ar: "ar" };

export function useTranslateTitles(
  texts: (string | null | undefined)[],
  locale: Locale
): (string | null | undefined)[] {
  const [result, setResult] = useState<(string | null | undefined)[]>(texts);

  useEffect(() => {
    const target = LANG_CODE[locale];

    // Build per-text cache keys
    const getCached = (text: string) => cache.get(`${target}:${text}`);

    // Apply whatever is already cached immediately (no flicker)
    const applyCache = () =>
      texts.map((t) => (!t ? t : getCached(t) ?? t));

    setResult(applyCache());

    // Find texts that still need fetching
    const missing = texts
      .filter((t): t is string => !!t && !getCached(t));

    if (!missing.length) return;

    fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: missing, target }),
    })
      .then((r) => r.json())
      .then(({ translations }: { translations: string[] }) => {
        missing.forEach((orig, i) => {
          if (translations[i]) cache.set(`${target}:${orig}`, translations[i]);
        });
        setResult(applyCache());
      })
      .catch(() => {}); // silently keep originals on error
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale, texts.map((t) => t ?? "").join("\x00")]);

  return result;
}
