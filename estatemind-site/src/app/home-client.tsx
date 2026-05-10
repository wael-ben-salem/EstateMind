"use client";
import Link from "next/link";
import { Camera, TrendingUp, AlertTriangle, Scale, Map, Sparkles, ChevronDown, ArrowRight, Star, MapPin, Home, Bed, Maximize2 } from "lucide-react";
import { NavbarDark } from "@/components/navbar";
import { useLang } from "@/contexts/lang";
import { useTranslateTitles } from "@/hooks/use-translate";

/* ── helpers ────────────────────────────────────── */
const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number, w = 800, h = 500) =>
  `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=${w}&h=${h}`;
const listingImg = (images: string | null | undefined, id: number) => {
  if (images) { const u = images.split(" | ")[0]; if (u?.startsWith("http")) return u; }
  return px(PX_IDS[id % PX_IDS.length]);
};
const NUM_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };
const fmtPrice = (p: number | null | undefined, priceOnRequest: string, numLocale: string) =>
  (!p || p <= 100) ? priceOnRequest : `${new Intl.NumberFormat(numLocale).format(p)} TND`;

const GALLERY   = [29679540, 27637106, 14809503, 12305351, 35663123, 28811770, 27631749, 27599624, 37284584];
const CITY_PHOTOS: Record<string, number> = {
  Tunis: 29465759, Sousse: 32465895, Sfax: 14558088, Nabeul: 27637106,
  "Sidi Bou Saïd": 27967576, Ariana: 29679540, "La Marsa": 35663123,
};

const FEATURE_ICONS = [Camera, TrendingUp, AlertTriangle, Scale, Map, Sparkles];

interface Listing {
  id: number; titre: string | null; prix: number | null; gouvernerat: string | null;
  ville: string | null; type: string | null; contrat: string | null;
  surface: number | null; pieces: number | null; images: string | null;
}
interface CityGroup { gouvernerat: string | null; _count: { id: number } }

interface HomeClientProps {
  featured: Listing[];
  cities: CityGroup[];
  total: number;
}

const TYPE_MAP: Record<string, [string, string, string]> = {
  "Appartement":     ["Appartement", "شقة",          "Apartment"],
  "Villa":           ["Villa",       "فيلا",         "Villa"],
  "Maison":          ["Maison",      "منزل",          "House"],
  "Terrain":         ["Terrain",     "أرض",           "Land"],
  "Studio":          ["Studio",      "ستوديو",        "Studio"],
  "Bureau":          ["Bureau",      "مكتب",          "Office"],
  "Local commercial":["Local comm.", "محل تجاري",    "Commercial"],
};

export function HomeClient({ featured, cities, total }: HomeClientProps) {
  const { t, locale } = useLang();
  const translatedTitles = useTranslateTitles(featured.map(l => l.titre), locale);
  const typeLabel = (raw: string | null) => {
    if (!raw) return null;
    const e = TYPE_MAP[raw];
    if (!e) return raw;
    return locale === "ar" ? e[1] : locale === "en" ? e[2] : e[0];
  };

  const MARQUEE = [
    total.toLocaleString() + "+ " + t.nav.search.toUpperCase(), "TUNIS", "SFAX", "SOUSSE",
    "HAMMAMET", "SIDI BOU SAÏD", "DJERBA", "6 " + t.home.ai_label.toUpperCase(),
    t.features[1].title.toUpperCase(), t.features[3].title.toUpperCase(), t.features[2].title.toUpperCase(),
  ];

  return (
    <main className="overflow-x-hidden">
      <NavbarDark />

      {/* ── HERO ─────────────────────────────────── */}
      <section className="relative h-screen w-full overflow-hidden">
        <div className="absolute inset-0 z-0">
          <iframe
            src="https://www.youtube-nocookie.com/embed/5jxzeMW_T00?autoplay=1&mute=1&loop=1&playlist=5jxzeMW_T00&controls=0&showinfo=0&rel=0&iv_load_policy=3&modestbranding=1"
            allow="autoplay; encrypted-media"
            className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ width: "100vw", height: "56.25vw", minHeight: "100vh", minWidth: "177.77vh" }}
          />
        </div>
        <div className="absolute inset-0 z-10 bg-gradient-to-b from-navy/55 via-navy/25 to-navy/72" />

        <div className="relative z-20 flex h-full flex-col items-center justify-center text-center px-6 gap-6">
          <div className="animate-fadeIn inline-flex items-center gap-2 rounded-full border border-gold/40
                          bg-gold/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-gold">
            <Star size={10} fill="currentColor" /> {t.hero.badge}
          </div>

          <h1 className="animate-fadeUp font-[family-name:var(--font-display)] text-5xl md:text-7xl
                         font-bold text-white leading-[1.05] max-w-4xl"
              style={{ animationDelay: "0.1s", textShadow: "0 2px 24px rgba(0,0,0,0.45)" }}>
            {t.hero.title}<br />
            <span className="text-gold">{t.hero.accent}</span>
          </h1>

          <p className="animate-fadeUp text-white/70 text-lg max-w-xl leading-relaxed"
             style={{ animationDelay: "0.25s" }}>
            {total.toLocaleString(NUM_LOCALE[locale] ?? "fr-TN")} {t.hero.subtitle}
          </p>

          <div className="animate-fadeUp w-full flex justify-center" style={{ animationDelay: "0.4s" }}>
            <div className="w-full max-w-2xl">
              <form action="/search" method="GET">
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md border border-white/30 rounded-2xl px-5 py-4 shadow-2xl">
                  <input name="q" placeholder={t.hero.placeholder}
                         className="flex-1 bg-transparent text-white placeholder:text-white/50 text-sm outline-none" />
                  <button type="submit"
                          className="shrink-0 bg-gold text-navy font-bold text-sm px-5 py-2.5 rounded-xl hover:opacity-90 transition-opacity">
                    {t.hero.search}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div className="animate-fadeUp flex flex-wrap justify-center gap-2" style={{ animationDelay: "0.5s" }}>
            {(t.hero.filters as string[]).map((label, i) => {
              const types = ["Appartement", "Villa", "Maison", "Terrain"];
              return (
                <Link key={label} href={`/search?type=${types[i]}`}
                      className="text-xs font-semibold text-white/70 border border-white/20
                                 px-4 py-2 rounded-full hover:border-gold/60 hover:text-gold transition-all backdrop-blur-sm">
                  {label}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 animate-bounce flex flex-col
                        items-center gap-1 text-white/40 text-xs tracking-widest">
          <span>{t.hero.scroll}</span><ChevronDown size={16} />
        </div>
      </section>

      {/* ── MARQUEE ──────────────────────────────── */}
      <div className="overflow-hidden py-4" style={{ background: "linear-gradient(90deg, var(--color-primary) 0%, var(--color-gold) 100%)" }}>
        <div className="flex animate-marquee whitespace-nowrap">
          {[...MARQUEE, ...MARQUEE].map((item, i) => (
            <span key={i} className="inline-flex items-center gap-4 mx-8 text-xs font-bold uppercase tracking-widest text-white">
              {item}<span className="text-white/40">✦</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── FEATURED LISTINGS ────────────────────── */}
      <section className="py-24 px-6" style={{ background: "white" }}>
        <div className="mx-auto max-w-6xl">
          <div className="flex items-end justify-between mb-12">
            <div>
              <p className="text-terra text-xs font-bold uppercase tracking-[0.3em] mb-3">{t.home.recent_label}</p>
              <h2 className="font-[family-name:var(--font-display)] text-4xl md:text-5xl font-bold text-navy">
                {t.home.recent_title}
              </h2>
            </div>
            <Link href="/search"
                  className="hidden sm:inline-flex items-center gap-2 text-primary font-semibold text-sm hover:text-primary-l transition-colors">
              {t.home.see_all} <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((l, idx) => (
              <Link key={l.id} href={`/listings/${l.id}`}
                    className="group bg-white rounded-2xl overflow-hidden shadow-card hover:shadow-card-hover
                               hover:-translate-y-1 transition-all duration-300 border border-navy/5">
                <div className="relative overflow-hidden bg-navy/5" style={{ aspectRatio: "4/3" }}>
                  <img src={listingImg(l.images, l.id)} alt={l.titre ?? "Annonce"}
                       onError={(e) => { e.currentTarget.src = px(PX_IDS[l.id % PX_IDS.length]); e.currentTarget.onerror = null; }}
                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                  <div className="absolute top-3 left-3 flex gap-2">
                    {l.contrat && (
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full
                        ${l.contrat === "Vente" ? "bg-gold text-navy" : "bg-primary text-white"}`}>
                        {l.contrat === "Vente" ? t.common.for_sale : t.common.for_rent}
                      </span>
                    )}
                    {l.type && (
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-white/90 text-navy">
                        {typeLabel(l.type)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="p-5">
                  <p className="font-[family-name:var(--font-display)] text-xl font-bold text-gold mb-1">
                    {fmtPrice(l.prix, t.common.price_on_request, NUM_LOCALE[locale] ?? "fr-TN")}
                  </p>
                  <p className="text-navy font-semibold text-sm line-clamp-1 mb-2">
                    {translatedTitles[idx] ?? `${typeLabel(l.type) ?? ""} — ${l.ville ?? l.gouvernerat ?? "Tunisie"}`}
                  </p>
                  <div className="flex items-center gap-1 text-navy/50 text-xs mb-3">
                    <MapPin size={11} />
                    <span>{[l.ville, l.gouvernerat].filter(Boolean).join(", ") || "Tunisie"}</span>
                  </div>
                  <div className="flex items-center gap-4 text-navy/60 text-xs border-t border-navy/8 pt-3">
                    {l.pieces  && <span className="flex items-center gap-1"><Bed size={12}/> {l.pieces} {t.home.rooms}</span>}
                    {l.surface && <span className="flex items-center gap-1"><Maximize2 size={12}/> {l.surface} m²</span>}
                    <span className="ml-auto flex items-center gap-1 text-primary font-semibold">
                      <Home size={12}/> {t.home.view}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="text-center mt-10">
            <Link href="/search"
                  className="inline-flex items-center gap-2 border-2 border-navy text-navy font-bold
                             px-8 py-3.5 rounded-xl hover:bg-navy hover:text-white transition-all">
              {t.home.see_all_btn} <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── CITY TILES ───────────────────────────── */}
      <section className="py-24 px-6 bg-navy">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <p className="text-gold text-xs font-bold uppercase tracking-[0.3em] mb-3">{t.home.cities_label}</p>
            <h2 className="font-[family-name:var(--font-display)] text-4xl md:text-5xl font-bold text-white">
              {t.home.cities_title}
            </h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {cities.map(({ gouvernerat: gov, _count }) => {
              const pid = CITY_PHOTOS[gov ?? ""] ?? PX_IDS[(gov?.length ?? 0) % PX_IDS.length];
              return (
                <Link key={gov} href={`/search?gouvernerat=${encodeURIComponent(gov ?? "")}`}
                      className="group relative overflow-hidden rounded-2xl" style={{ height: "280px" }}>
                  <img src={px(pid)} alt={gov ?? ""} className="absolute inset-0 w-full h-full object-cover
                       group-hover:scale-110 transition-transform duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-navy/90 via-navy/30 to-transparent" />
                  <div className="absolute bottom-0 inset-x-0 p-5">
                    <h3 className="font-[family-name:var(--font-display)] text-xl font-bold text-white">{gov}</h3>
                    <p className="text-white/60 text-xs mt-1">{_count.id.toLocaleString(NUM_LOCALE[locale] ?? "fr-TN")} {t.home.listings_count}</p>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── AI FEATURES ──────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "oklch(0.97 0.008 30)" }}>
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <p className="text-terra text-xs font-bold uppercase tracking-[0.3em] mb-3">{t.home.ai_label}</p>
            <h2 className="font-[family-name:var(--font-display)] text-4xl md:text-5xl font-bold text-navy mb-4">
              {t.home.ai_title}
            </h2>
            <p className="text-navy/55 max-w-lg mx-auto">{t.home.ai_subtitle}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {(t.features as { title: string; desc: string }[]).map(({ title, desc }, i) => {
              const Icon = FEATURE_ICONS[i];
              return (
                <div key={title}
                     className="group p-6 rounded-2xl bg-white border border-navy/8
                                hover:border-primary/40 hover:shadow-lg transition-all duration-300">
                  <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center mb-4
                                  group-hover:bg-primary/20 transition-colors">
                    <Icon size={20} className="text-primary" />
                  </div>
                  <h3 className="font-semibold text-navy mb-2">{title}</h3>
                  <p className="text-navy/55 text-sm leading-relaxed">{desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── VIDEO ────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "white" }}>
        <div className="mx-auto max-w-5xl">
          <div className="text-center mb-10">
            <p className="text-terra text-xs font-bold uppercase tracking-[0.3em] mb-3">{t.home.video_label}</p>
            <h2 className="font-[family-name:var(--font-display)] text-4xl font-bold text-navy">{t.home.video_title}</h2>
          </div>
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border-4 border-white" style={{ paddingTop: "56.25%" }}>
            <iframe className="absolute inset-0 w-full h-full"
              src="https://www.youtube-nocookie.com/embed/kRpGRfhhGZs?rel=0&modestbranding=1"
              title="Tunisia 4K" allowFullScreen
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture" />
          </div>
        </div>
      </section>

      {/* ── GALLERY ──────────────────────────────── */}
      <section className="py-24 px-6 bg-navy">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <p className="text-gold text-xs font-bold uppercase tracking-[0.3em] mb-3">{t.home.gallery_label}</p>
            <h2 className="font-[family-name:var(--font-display)] text-4xl font-bold text-white">{t.home.gallery_title}</h2>
          </div>
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-4 space-y-4">
            {GALLERY.map((id, i) => (
              <div key={id} className="group relative overflow-hidden rounded-2xl break-inside-avoid">
                <img src={px(id, 800, i % 3 === 0 ? 560 : 380)} alt={`Tunisie ${i + 1}`}
                     className="w-full object-cover group-hover:scale-105 transition-transform duration-700"
                     style={{ height: i % 3 === 0 ? "340px" : "230px" }} />
                <div className="absolute inset-0 bg-navy/0 group-hover:bg-navy/20 transition-colors duration-300" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────── */}
      <section className="relative overflow-hidden py-36 px-6">
        <img src={px(35812446, 1920, 1080)} alt="Tunisia" className="animate-kenburns absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-br from-navy/75 via-navy/55 to-primary/70" />
        <div className="relative z-10 text-center max-w-2xl mx-auto">
          <p className="text-gold text-xs font-bold uppercase tracking-[0.3em] mb-5">{t.home.cta_label}</p>
          <h2 className="font-[family-name:var(--font-display)] text-5xl md:text-6xl font-bold text-white mb-5 leading-tight">
            {t.home.cta_title}
          </h2>
          <p className="text-white/60 text-lg mb-9 leading-relaxed">{t.home.cta_sub}</p>
          <Link href="/search"
                className="inline-flex items-center gap-3 bg-gold text-navy font-bold px-10 py-5
                           rounded-full text-lg hover:opacity-90 transition-all hover:scale-105 shadow-2xl shadow-gold/30">
            {t.home.cta_btn} <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────── */}
      <footer className="bg-navy border-t border-white/10 px-6 py-16">
        <div className="mx-auto max-w-6xl grid md:grid-cols-4 gap-10 mb-10">
          <div className="md:col-span-2">
            <span className="font-[family-name:var(--font-display)] text-3xl font-bold">
              <span className="text-gold">Estate</span><span className="text-white">Mind</span>
            </span>
            <p className="text-white/40 text-sm leading-relaxed mt-3 max-w-xs">{t.home.footer_desc}</p>
            <p className="text-white/25 text-xs mt-4">{t.home.footer_built}</p>
          </div>
          <div>
            <p className="text-gold/60 text-xs font-bold uppercase tracking-widest mb-4">{t.home.footer_platform}</p>
            <ul className="space-y-2 text-sm text-white/45">
              {[t.nav.search, t.nav.map, t.nav.apartments, t.nav.villas, t.nav.land].map((l, i) => {
                const hrefs = ["/search", "/map", "/search?type=Appartement", "/search?type=Villa", "/search?type=Terrain"];
                return (
                  <li key={l}><Link href={hrefs[i]} className="hover:text-white/80 transition-colors">{l}</Link></li>
                );
              })}
            </ul>
          </div>
          <div>
            <p className="text-gold/60 text-xs font-bold uppercase tracking-widest mb-4">{t.home.footer_cities}</p>
            <ul className="space-y-2 text-sm text-white/45">
              {["Tunis", "Sfax", "Sousse", "Hammamet", "Sidi Bou Saïd", "Djerba"].map(c => (
                <li key={c}><Link href={`/search?gouvernerat=${c}`} className="hover:text-white/80 transition-colors">{c}</Link></li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mx-auto max-w-6xl border-t border-white/10 pt-6 flex justify-between">
          <p className="text-white/20 text-xs">© 2026 EstateMind. {t.home.footer_rights}</p>
          <p className="text-white/20 text-xs">{t.home.footer_powered}</p>
        </div>
      </footer>
    </main>
  );
}
