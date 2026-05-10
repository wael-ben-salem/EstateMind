"use client";
import Link from "next/link";
import { MapPin, Bed, Maximize2, Calendar, Phone, ArrowLeft, Star, CheckCircle2 } from "lucide-react";
import { NavbarLight } from "@/components/navbar";
import { useLang } from "@/contexts/lang";
import { useTranslateTitles } from "@/hooks/use-translate";
import { AiAnalysis } from "./ai-analysis";
import { ImageGallery } from "./image-gallery";

const TYPE_MAP: Record<string, [string, string, string]> = {
  "Appartement":      ["Appartement", "شقة",       "Apartment"],
  "Villa":            ["Villa",       "فيلا",      "Villa"],
  "Maison":           ["Maison",      "منزل",       "House"],
  "Terrain":          ["Terrain",     "أرض",        "Land"],
  "Studio":           ["Studio",      "ستوديو",     "Studio"],
  "Bureau":           ["Bureau",      "مكتب",       "Office"],
  "Local commercial": ["Local comm.", "محل تجاري", "Commercial"],
};

interface ListingData {
  id: number;
  titre: string | null;
  prix: number | null;
  prixM2: number | null;
  gouvernerat: string | null;
  ville: string | null;
  delegation: string | null;
  adresse: string | null;
  type: string | null;
  contrat: string | null;
  surface: number | null;
  pieces: number | null;
  images: string | null;
  description: string | null;
  descClean: string | null;
  tel: string | null;
  source: string | null;
  url: string | null;
  pubYear: number | null;
  hautStanding: boolean | null;
  hasAscenseur: boolean | null;
  hasBalcon: boolean | null;
  hasClimatisation: boolean | null;
  hasGarage: boolean | null;
  hasGardien: boolean | null;
  hasJardin: boolean | null;
  hasParking: boolean | null;
  hasPiscine: boolean | null;
  hasTerrasse: boolean | null;
  hasChaffage: boolean | null;
}

const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number) =>
  `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=1200&h=700`;

function listingImgs(images: string | null | undefined, id: number): string[] {
  const fallback = px(PX_IDS[id % PX_IDS.length]);
  if (!images) return [fallback];
  const urls = images.split(" | ").filter(u => u?.startsWith("http"));
  return urls.length ? urls.slice(0, 8) : [fallback];
}

const AMENITY_KEYS = [
  { key: "hasAscenseur",     label_fr: "Ascenseur",     label_ar: "مصعد",      label_en: "Elevator" },
  { key: "hasBalcon",        label_fr: "Balcon",        label_ar: "شرفة",      label_en: "Balcony" },
  { key: "hasClimatisation", label_fr: "Climatisation", label_ar: "تكييف",     label_en: "A/C" },
  { key: "hasGarage",        label_fr: "Garage",        label_ar: "مرآب",      label_en: "Garage" },
  { key: "hasGardien",       label_fr: "Gardien",       label_ar: "حارس",      label_en: "Guard" },
  { key: "hasJardin",        label_fr: "Jardin",        label_ar: "حديقة",     label_en: "Garden" },
  { key: "hasParking",       label_fr: "Parking",       label_ar: "موقف",      label_en: "Parking" },
  { key: "hasPiscine",       label_fr: "Piscine",       label_ar: "مسبح",      label_en: "Pool" },
  { key: "hasTerrasse",      label_fr: "Terrasse",      label_ar: "تراس",      label_en: "Terrace" },
  { key: "hasChaffage",      label_fr: "Chauffage",     label_ar: "تدفئة",     label_en: "Heating" },
] as const;

export function ListingContent({ l }: { l: ListingData }) {
  const { t, locale } = useLang();
  const [translatedTitle] = useTranslateTitles([l.titre], locale);
  const typeLabel = (raw: string | null) => {
    if (!raw) return null;
    const e = TYPE_MAP[raw];
    if (!e) return raw;
    return locale === "ar" ? e[1] : locale === "en" ? e[2] : e[0];
  };
  const imgs = listingImgs(l.images, l.id);
  const amenities = AMENITY_KEYS.filter(a => (l as unknown as Record<string, unknown>)[a.key] === true);
  const amenityLabel = (a: typeof AMENITY_KEYS[number]) =>
    locale === "ar" ? a.label_ar : locale === "en" ? a.label_en : a.label_fr;

  const fmtPrice = (p: number | null | undefined) =>
    p ? `${new Intl.NumberFormat("fr-TN").format(p)} TND` : t.listing.price_on_request;

  return (
    <div className="min-h-screen" style={{ background: "var(--color-cream)" }}>
      <NavbarLight />

      {/* Page hero strip */}
      <div style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}
           className="px-4 sm:px-6 py-5">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-2 text-xs mb-2" style={{ color: "rgba(255,255,255,0.5)" }}>
            <Link href="/search" className="hover:text-white transition-colors">{t.listing.back.replace("←", "").trim() || "Recherche"}</Link>
            <span>/</span>
            {l.gouvernerat && <span>{l.gouvernerat}</span>}
            {l.gouvernerat && l.type && <span>/</span>}
            {l.type && <span>{typeLabel(l.type)}</span>}
          </div>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap gap-2 mb-2">
                {l.contrat && (
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg"
                        style={{ background: l.contrat === "Vente" ? "var(--color-gold)" : "var(--color-primary)", color: l.contrat === "Vente" ? "var(--color-navy)" : "white" }}>
                    {l.contrat === "Vente" ? t.common.for_sale : t.common.for_rent}
                  </span>
                )}
                {l.hautStanding && (
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg flex items-center gap-1"
                        style={{ background: "rgba(255,255,255,0.15)", color: "var(--color-gold)" }}>
                    <Star size={10} /> {t.listing.high_standing}
                  </span>
                )}
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white line-clamp-2"
                  style={{ fontFamily: "var(--font-display)" }}>
                {translatedTitle ?? t.listing.unnamed}
              </h1>
              <p className="flex items-center gap-1.5 text-sm mt-1.5" style={{ color: "rgba(255,255,255,0.55)" }}>
                <MapPin size={13} />
                {[l.adresse, l.ville, l.gouvernerat].filter(Boolean).join(", ") || "Tunisie"}
              </p>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-2xl font-bold" style={{ color: "var(--color-gold)", fontFamily: "var(--font-display)" }}>
                {fmtPrice(l.prix)}
              </p>
              {l.prixM2 && (
                <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.45)" }}>
                  {new Intl.NumberFormat("fr-TN").format(l.prixM2)} {t.listing.per_sqm}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <ImageGallery images={imgs} title={l.titre ?? t.listing.unnamed} />

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Back link */}
            <Link href="/search" className="inline-flex items-center gap-1.5 text-sm font-medium hover:underline"
                  style={{ color: "var(--color-navy)", opacity: 0.5 }}>
              <ArrowLeft size={14} /> {t.listing.back}
            </Link>

            {/* Key stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: t.listing.price, value: fmtPrice(l.prix), icon: null, gold: true },
                l.surface ? { label: t.listing.surface, value: `${l.surface} m²`, icon: <Maximize2 size={14}/>, gold: false } : null,
                l.pieces  ? { label: t.listing.rooms,   value: `${l.pieces} ${t.common.rooms}`, icon: <Bed size={14}/>, gold: false } : null,
                l.pubYear ? { label: t.listing.publication, value: String(l.pubYear), icon: <Calendar size={14}/>, gold: false } : null,
              ].filter(Boolean).map((s, i) => s && (
                <div key={i} className="rounded-xl p-4 bg-white border border-navy/8 shadow-sm">
                  <p className="text-xs mb-1 flex items-center gap-1" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                    {s.icon} {s.label}
                  </p>
                  <p className="font-bold text-sm" style={{ color: s.gold ? "var(--color-gold)" : "var(--color-navy)" }}>
                    {s.value}
                  </p>
                </div>
              ))}
            </div>

            {/* Description */}
            {(l.description || l.descClean) && (
              <div className="rounded-2xl bg-white border border-navy/8 p-6 shadow-sm">
                <h2 className="font-semibold text-base mb-3" style={{ color: "var(--color-navy)" }}>{t.listing.description}</h2>
                <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: "var(--color-navy)", opacity: 0.75 }}>
                  {l.descClean ?? l.description}
                </p>
              </div>
            )}

            {/* Amenities */}
            {amenities.length > 0 && (
              <div className="rounded-2xl bg-white border border-navy/8 p-6 shadow-sm">
                <h2 className="font-semibold text-base mb-4" style={{ color: "var(--color-navy)" }}>{t.listing.amenities}</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {amenities.map(a => (
                    <div key={a.key} className="flex items-center gap-2">
                      <CheckCircle2 size={15} style={{ color: "var(--color-gold)" }} />
                      <span className="text-sm" style={{ color: "var(--color-navy)" }}>{amenityLabel(a)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Location */}
            {(l.gouvernerat || l.ville || l.delegation) && (
              <div className="rounded-2xl bg-white border border-navy/8 p-6 shadow-sm">
                <h2 className="font-semibold text-base mb-4" style={{ color: "var(--color-navy)" }}>{t.listing.location}</h2>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  {[
                    [t.listing.governorate, l.gouvernerat],
                    [t.listing.city, l.ville],
                    [t.listing.delegation, l.delegation],
                    [t.listing.address, l.adresse],
                  ].filter(([, v]) => v).map(([k, v]) => (
                    <div key={k as string}>
                      <dt className="text-xs mb-0.5" style={{ color: "var(--color-navy)", opacity: 0.45 }}>{k}</dt>
                      <dd className="font-medium" style={{ color: "var(--color-navy)" }}>{v}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <div className="rounded-2xl bg-white border border-navy/8 p-6 shadow-sm sticky top-24">
              <p className="text-2xl font-bold mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--color-gold)" }}>
                {fmtPrice(l.prix)}
              </p>
              {l.prixM2 && (
                <p className="text-sm mb-4" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                  {new Intl.NumberFormat("fr-TN").format(l.prixM2)} {t.listing.per_sqm}
                </p>
              )}
              {l.tel && (
                <a href={`tel:${l.tel}`}
                   className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold text-sm transition-opacity hover:opacity-85 mb-3"
                   style={{ background: "var(--color-navy)", color: "white" }}>
                  <Phone size={15} /> {t.listing.contact}
                </a>
              )}
              <button className="w-full py-3 rounded-xl font-medium text-sm border transition-colors hover:border-gold"
                      style={{ borderColor: "oklch(0.10 0.035 45 / 0.2)", color: "var(--color-navy)" }}>
                {t.listing.save}
              </button>
              {l.source && l.url && (
                <p className="text-xs text-center mt-4" style={{ color: "var(--color-navy)", opacity: 0.35 }}>
                  {t.listing.source} : <a href={l.url} target="_blank" rel="noopener noreferrer" className="hover:underline">{l.source}</a>
                </p>
              )}
            </div>
            <AiAnalysis listingId={l.id} prix={l.prix} surface={l.surface} pieces={l.pieces} gouvernerat={l.gouvernerat} type={l.type} contrat={l.contrat} />
          </div>
        </div>
      </div>
    </div>
  );
}
