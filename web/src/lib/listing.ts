import type { Listing } from "@/generated/prisma";

export function listingImages(l: Pick<Listing, "images">): string[] {
  if (!l.images) return [];
  return l.images
    .split("|")
    .map((s) => s.trim())
    .filter((s) => s.startsWith("http"));
}

export function formatPrice(value: number | null | undefined, locale: string): string | null {
  if (value === null || value === undefined || !isFinite(value)) return null;
  const lang = locale === "ar" ? "ar-TN" : locale === "en" ? "en-TN" : "fr-TN";
  return new Intl.NumberFormat(lang, {
    style: "currency",
    currency: "TND",
    maximumFractionDigits: 0,
  }).format(value);
}

export function listingTitle(l: Pick<Listing, "titre" | "type" | "ville" | "gouvernerat">): string {
  if (l.titre) return l.titre;
  const parts = [l.type, l.ville ?? l.gouvernerat].filter(Boolean);
  return parts.join(" — ") || "Bien immobilier";
}
