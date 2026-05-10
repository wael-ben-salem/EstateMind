"use client";
import { useState } from "react";
import Link from "next/link";
import { signOut } from "next-auth/react";
import { User, Home, Heart, Plus, MapPin, Bed, Maximize2, LogOut } from "lucide-react";
import { useLang } from "@/contexts/lang";
import { LangSwitcher } from "@/components/lang-switcher";
import { NavbarDashboard } from "@/components/navbar";

interface ListingSnippet {
  id: number; titre?: string | null; prix?: number | null; gouvernerat?: string | null;
  ville?: string | null; type?: string | null; contrat?: string | null;
  surface?: number | null; pieces?: number | null; images?: string | null;
}
interface Props {
  user: { id: number; email: string; name: string | null; role: string; createdAt: string };
  myListings: (ListingSnippet & { createdAt: string })[];
  favorites: ListingSnippet[];
}

const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number) => `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=400&h=260`;
const listingImg = (images: string | null | undefined, id: number) => {
  if (images) { const u = images.split(" | ")[0]; if (u?.startsWith("http")) return u; }
  return px(PX_IDS[id % PX_IDS.length]);
};
const NUM_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };
const fmtPrice = (p: number | null | undefined, priceOnRequest: string, locale: string) =>
  (!p || p <= 100) ? priceOnRequest : `${new Intl.NumberFormat(NUM_LOCALE[locale] ?? "fr-TN").format(p)} TND`;

type Tab = "profile" | "listings" | "favorites";

const DATE_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };

export function DashboardClient({ user, myListings, favorites }: Props) {
  const { t, locale } = useLang();
  const [tab, setTab] = useState<Tab>("profile");

  const tabClass = (tb: Tab) =>
    `px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors ${tab === tb ? "" : "hover:bg-navy/5"}`;
  const tabStyle = (tb: Tab) =>
    tab === tb
      ? { background: "var(--color-navy)", color: "white" }
      : { color: "var(--color-navy)", opacity: 0.6 };

  const dateLocale = DATE_LOCALE[locale] ?? "fr-TN";

  return (
    <div className="min-h-screen" style={{ background: "var(--color-cream)" }}>
      <NavbarDashboard />

      {/* Page hero */}
      <div className="px-4 sm:px-6 py-7"
           style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}>
        <div className="max-w-5xl mx-auto flex items-center gap-4 flex-wrap">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold shrink-0"
               style={{ background: "var(--color-gold)", color: "var(--color-navy)", fontFamily: "var(--font-display)" }}>
            {(user.name ?? user.email).charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-white" style={{ fontFamily: "var(--font-display)" }}>
              {user.name ?? t.dashboard.my_account}
            </h1>
            <p className="text-xs mt-0.5 truncate" style={{ color: "rgba(255,255,255,0.45)" }}>{user.email}</p>
          </div>
          <Link href="/me/post"
                className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-opacity hover:opacity-85"
                style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
            <Plus size={16} /> {t.dashboard.post_listing}
          </Link>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: t.dashboard.my_listings, value: myListings.length, icon: <Home size={18} /> },
            { label: t.dashboard.favorites,   value: favorites.length,  icon: <Heart size={18} /> },
            { label: t.dashboard.member_since, value: new Date(user.createdAt).getFullYear(), icon: <User size={18} /> },
          ].map(({ label, value, icon }) => (
            <div key={label} className="rounded-2xl bg-white border border-navy/8 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-1" style={{ color: "var(--color-gold)" }}>{icon}</div>
              <p className="text-2xl font-bold" style={{ fontFamily: "var(--font-display)", color: "var(--color-navy)" }}>{value}</p>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-navy)", opacity: 0.45 }}>{label}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 p-1 rounded-2xl bg-white border border-navy/8 w-fit shadow-sm">
          {([
            ["profile",   t.dashboard.profile,     <User key="u" size={14}/>],
            ["listings",  t.dashboard.my_listings,  <Home key="h" size={14}/>],
            ["favorites", t.dashboard.favorites,    <Heart key="hrt" size={14}/>],
          ] as [Tab, string, React.ReactNode][]).map(([tb, label, icon]) => (
            <button key={tb} onClick={() => setTab(tb)} className={tabClass(tb)} style={tabStyle(tb)}>
              <span className="flex items-center gap-1.5">{icon}{label}</span>
            </button>
          ))}
        </div>

        {/* Profile tab */}
        {tab === "profile" && (
          <div className="rounded-2xl bg-white border border-navy/8 p-8 shadow-sm max-w-lg">
            <h2 className="font-semibold text-lg mb-6" style={{ color: "var(--color-navy)" }}>{t.dashboard.personal_info}</h2>
            <dl className="space-y-5">
              {[
                [t.dashboard.name,         user.name ?? "—"],
                [t.dashboard.email,        user.email],
                [t.dashboard.role,         user.role],
                [t.dashboard.member_since, new Date(user.createdAt).toLocaleDateString(dateLocale, { year: "numeric", month: "long", day: "numeric" })],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{k}</dt>
                  <dd className="font-medium text-sm" style={{ color: "var(--color-navy)" }}>{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* My listings tab */}
        {tab === "listings" && (
          <div>
            {myListings.length === 0 ? (
              <div className="text-center py-20 rounded-2xl bg-white border border-navy/8">
                <Home size={36} style={{ color: "var(--color-gold)", margin: "0 auto 12px" }} />
                <p className="font-semibold mb-1" style={{ color: "var(--color-navy)" }}>{t.dashboard.no_listings}</p>
                <p className="text-sm mb-5" style={{ color: "var(--color-navy)", opacity: 0.45 }}>{t.dashboard.no_listings_sub}</p>
                <Link href="/me/post" className="px-6 py-3 rounded-xl font-bold text-sm inline-block"
                      style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                  {t.dashboard.post_first}
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {myListings.map(l => (
                  <div key={l.id} className="group rounded-2xl overflow-hidden bg-white border border-navy/8 shadow-sm">
                    <div className="relative h-40 overflow-hidden">
                      <img src={listingImg(l.images, l.id)} alt={l.titre ?? ""} className="w-full h-full object-cover" />
                    </div>
                    <div className="p-4">
                      <p className="font-semibold text-sm line-clamp-1 mb-1" style={{ color: "var(--color-navy)" }}>{l.titre ?? t.dashboard.untitled}</p>
                      <p className="text-xs mb-2 flex items-center gap-1" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                        <MapPin size={10} />{[l.ville, l.gouvernerat].filter(Boolean).join(", ")}
                      </p>
                      <div className="flex items-center justify-between">
                        <p className="font-bold text-sm" style={{ color: "var(--color-gold)" }}>{fmtPrice(l.prix, t.common.price_on_request, locale)}</p>
                        <Link href={`/listings/${l.id}`} className="text-xs font-medium hover:underline" style={{ color: "var(--color-primary)" }}>
                          {t.dashboard.view}
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Favorites tab */}
        {tab === "favorites" && (
          <div>
            {favorites.length === 0 ? (
              <div className="text-center py-20 rounded-2xl bg-white border border-navy/8">
                <Heart size={36} style={{ color: "var(--color-gold)", margin: "0 auto 12px" }} />
                <p className="font-semibold mb-1" style={{ color: "var(--color-navy)" }}>{t.dashboard.no_favorites}</p>
                <p className="text-sm" style={{ color: "var(--color-navy)", opacity: 0.45 }}>{t.dashboard.no_favorites_sub}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {favorites.map(l => (
                  <Link key={l.id} href={`/listings/${l.id}`}
                        className="group rounded-2xl overflow-hidden bg-white border border-navy/8 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
                    <div className="relative h-40 overflow-hidden">
                      <img src={listingImg(l.images, l.id)} alt={l.titre ?? ""} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    </div>
                    <div className="p-4">
                      <p className="font-semibold text-sm line-clamp-1 mb-1" style={{ color: "var(--color-navy)" }}>{l.titre ?? t.listing.unnamed}</p>
                      <p className="text-xs mb-2 flex items-center gap-1" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                        <MapPin size={10} />{[l.ville, l.gouvernerat].filter(Boolean).join(", ")}
                      </p>
                      <div className="flex items-center justify-between">
                        <p className="font-bold text-sm" style={{ color: "var(--color-gold)" }}>{fmtPrice(l.prix, t.common.price_on_request, locale)}</p>
                        <div className="flex gap-3 text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                          {l.pieces && <span className="flex items-center gap-0.5"><Bed size={10} />{l.pieces}</span>}
                          {l.surface && <span className="flex items-center gap-0.5"><Maximize2 size={10} />{l.surface}m²</span>}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
