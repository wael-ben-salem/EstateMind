"use client";
import Link from "next/link";
import { MapPin, Bed, Maximize2, SlidersHorizontal, X } from "lucide-react";
import { NavbarLight } from "@/components/navbar";
import { useLang } from "@/contexts/lang";
import { SearchFilters } from "./filters";
import { useTranslateTitles } from "@/hooks/use-translate";

const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number) =>
  `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=600&h=400`;
const listingImg = (images: string | null | undefined, id: number) => {
  if (images) { const u = images.split(" | ")[0]; if (u?.startsWith("http")) return u; }
  return px(PX_IDS[id % PX_IDS.length]);
};
const NUM_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };
const fmtPrice = (p: number | null | undefined, label: string, numLocale: string) =>
  (!p || p <= 100) ? label : `${new Intl.NumberFormat(numLocale).format(p)} TND`;

const TYPE_MAP: Record<string, [string, string, string]> = {
  "Appartement":     ["Appartement", "شقة",       "Apartment"],
  "Villa":           ["Villa",       "فيلا",      "Villa"],
  "Maison":          ["Maison",      "منزل",       "House"],
  "Terrain":         ["Terrain",     "أرض",        "Land"],
  "Studio":          ["Studio",      "ستوديو",     "Studio"],
  "Bureau":          ["Bureau",      "مكتب",       "Office"],
  "Local commercial":["Local comm.", "محل تجاري", "Commercial"],
};

interface Listing {
  id: number; titre: string | null; prix: number | null; gouvernerat: string | null;
  ville: string | null; type: string | null; contrat: string | null;
  surface: number | null; pieces: number | null; images: string | null;
}

interface SearchContentProps {
  listings: Listing[];
  total: number;
  page: number;
  totalPages: number;
  q: string;
  types: string[];
  contrat: string;
  gov: string;
  minP: string;
  maxP: string;
  pieces: string;
  TYPES: string[];
  CONTRATS: string[];
  GOVS: string[];
}

function buildUrl(
  overrides: Record<string, string | undefined>,
  base: { q: string; types: string[]; contrat: string; gov: string; minP: string; maxP: string; pieces: string; page: number }
) {
  const p = new URLSearchParams();
  if (base.q)       p.set("q", base.q);
  base.types.forEach(t => p.append("type", t));
  if (base.contrat) p.set("contrat", base.contrat);
  if (base.gov)     p.set("gouvernerat", base.gov);
  if (base.minP)    p.set("min_prix", base.minP);
  if (base.maxP)    p.set("max_prix", base.maxP);
  if (base.pieces)  p.set("pieces", base.pieces);
  p.set("page", String(base.page));
  for (const [k, v] of Object.entries(overrides)) {
    if (v === undefined) p.delete(k); else p.set(k, v);
  }
  return `/search?${p.toString()}`;
}

export function SearchContent({
  listings, total, page, totalPages, q, types, contrat, gov, minP, maxP, pieces,
  TYPES, CONTRATS, GOVS,
}: SearchContentProps) {
  const { t, locale } = useLang();
  const translatedTitles = useTranslateTitles(listings.map(l => l.titre), locale);
  const typeLabel = (raw: string | null) => {
    if (!raw) return null;
    const e = TYPE_MAP[raw];
    if (!e) return raw;
    return locale === "ar" ? e[1] : locale === "en" ? e[2] : e[0];
  };

  const activeFilters = [
    ...types.map(ty => ({ label: ty, key: "type" })),
    contrat ? { label: contrat, key: "contrat" } : null,
    gov ? { label: gov, key: "gouvernerat" } : null,
    pieces ? { label: `${pieces}+ ${t.common.rooms}`, key: "pieces" } : null,
    minP ? { label: `≥ ${minP} TND`, key: "min_prix" } : null,
    maxP ? { label: `≤ ${maxP} TND`, key: "max_prix" } : null,
  ].filter(Boolean) as { label: string; key: string }[];

  return (
    <div className="min-h-screen" style={{ background: "var(--color-cream)" }}>
      <NavbarLight withSearch />

      {/* Page hero banner */}
      <div style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}
           className="px-4 sm:px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl sm:text-2xl font-bold text-white"
              style={{ fontFamily: "var(--font-display)" }}>
            {q ? `${t.search.results_for} « ${q} »` : t.search.all}
          </h1>
          <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.55)" }}>
            {total.toLocaleString(NUM_LOCALE[locale] ?? "fr-TN")} {total === 1 ? t.search.found_one : t.search.found_many}
          </p>
          {activeFilters.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {activeFilters.map(f => (
                <span key={f.key + f.label}
                      className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg"
                      style={{ background: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.85)", border: "1px solid rgba(255,255,255,0.18)" }}>
                  <SlidersHorizontal size={10} />
                  {f.label}
                </span>
              ))}
              <Link href="/search"
                    className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg transition-colors hover:bg-white/20"
                    style={{ color: "var(--color-gold)" }}>
                <X size={10} /> {t.search.clear}
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex gap-8">
        {/* Sidebar */}
        <aside className="w-64 shrink-0 hidden lg:block">
          <div className="sticky top-24 space-y-6">
            <div className="rounded-2xl border border-navy/10 bg-white p-5 shadow-sm">
              <SearchFilters
                types={types} contrat={contrat} gov={gov}
                minP={minP} maxP={maxP} pieces={pieces}
                TYPES={TYPES} CONTRATS={CONTRATS} GOVS={GOVS}
              />
            </div>
          </div>
        </aside>

        {/* Results */}
        <main className="flex-1 min-w-0">

          {listings.length === 0 ? (
            <div className="text-center py-24" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              <p className="text-4xl mb-3">🏠</p>
              <p className="font-medium">{t.search.empty}</p>
              <Link href="/search" className="mt-4 inline-block text-sm underline" style={{ color: "var(--color-gold)" }}>
                {t.search.clear}
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
              {listings.map((l, idx) => (
                <Link key={l.id} href={`/listings/${l.id}`}
                      className="group rounded-2xl overflow-hidden bg-white border border-navy/8 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">
                  <div className="relative h-48 overflow-hidden bg-navy/5">
                    <img src={listingImg(l.images, l.id)} alt={l.titre ?? t.listing.unnamed}
                         onError={(e) => { e.currentTarget.src = px(PX_IDS[l.id % PX_IDS.length]); e.currentTarget.onerror = null; }}
                         className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    <div className="absolute top-3 left-3 flex gap-2">
                      {l.contrat && (
                        <span className="text-xs font-bold px-2.5 py-1 rounded-lg"
                              style={{ background: l.contrat === "Vente" ? "var(--color-gold)" : "var(--color-primary)", color: l.contrat === "Vente" ? "var(--color-navy)" : "white" }}>
                          {l.contrat === "Vente" ? t.common.for_sale : t.common.for_rent}
                        </span>
                      )}
                      {l.type && (
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white/90 text-navy">
                          {typeLabel(l.type)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="p-4">
                    <p className="font-semibold text-sm line-clamp-2 mb-1" style={{ color: "var(--color-navy)" }}>
                      {translatedTitles[idx] ?? t.listing.unnamed}
                    </p>
                    <p className="text-xs mb-3 flex items-center gap-1" style={{ color: "var(--color-navy)", opacity: 0.5 }}>
                      <MapPin size={12} />{[l.ville, l.gouvernerat].filter(Boolean).join(", ") || "Tunisie"}
                    </p>
                    <div className="flex items-center justify-between">
                      <p className="font-bold text-base" style={{ color: "var(--color-gold)" }}>
                        {fmtPrice(l.prix, t.common.price_on_request, NUM_LOCALE[locale] ?? "fr-TN")}
                      </p>
                      <div className="flex gap-3 text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                        {l.pieces  && <span className="flex items-center gap-1"><Bed size={12} />{l.pieces}</span>}
                        {l.surface && <span className="flex items-center gap-1"><Maximize2 size={12} />{l.surface} m²</span>}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-10">
              {page > 1 && (
                <Link href={buildUrl({ page: String(page - 1) }, { q, types, contrat, gov, minP, maxP, pieces, page })}
                      className="px-4 py-2 rounded-xl border border-navy/20 text-sm font-medium hover:border-gold transition-colors"
                      style={{ color: "var(--color-navy)" }}>
                  {t.search.prev}
                </Link>
              )}
              {(() => {
                const windowSize = Math.min(5, totalPages);
                const start = Math.max(1, Math.min(page - Math.floor(windowSize / 2), totalPages - windowSize + 1));
                return Array.from({ length: windowSize }, (_, i) => start + i).map(n => (
                  <Link key={n} href={buildUrl({ page: String(n) }, { q, types, contrat, gov, minP, maxP, pieces, page })}
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold border transition-colors"
                        style={n === page
                          ? { background: "var(--color-gold)", color: "var(--color-navy)", borderColor: "var(--color-gold)" }
                          : { color: "var(--color-navy)", borderColor: "oklch(0.18 0.065 260 / 0.15)" }}>
                    {n}
                  </Link>
                ));
              })()}
              {page < totalPages && (
                <Link href={buildUrl({ page: String(page + 1) }, { q, types, contrat, gov, minP, maxP, pieces, page })}
                      className="px-4 py-2 rounded-xl border border-navy/20 text-sm font-medium hover:border-gold transition-colors"
                      style={{ color: "var(--color-navy)" }}>
                  {t.search.next}
                </Link>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
