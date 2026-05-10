"use client";
import { useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { signOut } from "next-auth/react";
import { ArrowRight, ChevronDown, Sparkles, Map, Home, Building2, Briefcase, Layers, ShoppingBag, CalendarDays, Menu, X, User, Scale, Search } from "lucide-react";
import { useLang } from "@/contexts/lang";
import { LangSwitcher } from "@/components/lang-switcher";
import { SearchBar } from "@/components/search-bar";

/* ── Dark (homepage) variant ──────────────────────────────── */
type MenuKey = "buy" | "rent" | null;

export function NavbarDark() {
  const { data: session } = useSession();
  const { t } = useLang();
  const [menu, setMenu] = useState<MenuKey>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const BUY_ITEMS = [
    { label: t.nav.apartments, href: "/search?type=Appartement&contrat=Vente", Icon: Building2 },
    { label: t.nav.villas,     href: "/search?type=Villa&contrat=Vente",       Icon: Home },
    { label: t.nav.house,      href: "/search?type=Maison&contrat=Vente",      Icon: Home },
    { label: t.nav.land,       href: "/search?type=Terrain&contrat=Vente",     Icon: Layers },
    { label: t.nav.studio,     href: "/search?type=Studio&contrat=Vente",      Icon: Building2 },
    { label: t.nav.office,     href: "/search?type=Bureau&contrat=Vente",      Icon: Briefcase },
  ];

  const RENT_ITEMS = [
    { label: t.nav.apartments, href: "/search?type=Appartement&contrat=Location",      Icon: Building2 },
    { label: t.nav.house,      href: "/search?type=Maison&contrat=Location",           Icon: Home },
    { label: t.nav.studio,     href: "/search?type=Studio&contrat=Location",           Icon: Building2 },
    { label: t.nav.commercial, href: "/search?type=Local+commercial&contrat=Location", Icon: ShoppingBag },
    { label: t.nav.seasonal,   href: "/search?contrat=Location+saisonni%C3%A8re",      Icon: CalendarDays },
  ];

  return (
    <>
      <nav className="fixed top-0 inset-x-0 z-50 bg-navy/85 backdrop-blur-md border-b border-white/10"
           onMouseLeave={() => setMenu(null)}>
        <div className="max-w-7xl mx-auto px-6 lg:px-10 h-[68px] flex items-center justify-between gap-4">

          {/* Logo */}
          <Link href="/" className="shrink-0">
            <img src="/logo-transparent.png" alt="EstateMind"
                 style={{ height: "54px", width: "auto", objectFit: "contain" }} />
          </Link>

          {/* Desktop nav */}
          <div className="hidden lg:flex items-center gap-1 text-sm font-medium">

            {/* Buy dropdown */}
            <div className="relative" onMouseEnter={() => setMenu("buy")}>
              <button className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl transition-all text-sm font-medium
                ${menu === "buy" ? "text-white bg-white/10" : "text-white/75 hover:text-white hover:bg-white/8"}`}>
                {t.nav.buy}
                <ChevronDown size={13} style={{ transform: menu === "buy" ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
              </button>

              {menu === "buy" && (
                <div className="absolute top-full left-0 mt-2 w-56 rounded-2xl overflow-hidden shadow-2xl z-50"
                     style={{ background: "oklch(0.13 0.045 260 / 0.97)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.1)" }}>
                  <div className="px-4 py-2.5 border-b border-white/8">
                    <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--color-gold)" }}>
                      {t.nav.buy}
                    </p>
                  </div>
                  {BUY_ITEMS.map(({ label, href, Icon }) => (
                    <Link key={href} href={href} onClick={() => setMenu(null)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-white/75 hover:text-white hover:bg-white/8 transition-colors group">
                      <Icon size={13} style={{ color: "var(--color-gold)", opacity: 0.8 }} />
                      {label}
                    </Link>
                  ))}
                  <div className="border-t border-white/8 mx-3 mt-1 pt-1 pb-1">
                    <Link href="/search?contrat=Vente" onClick={() => setMenu(null)}
                          className="flex items-center justify-between px-1 py-2 text-xs font-semibold hover:text-white transition-colors rounded-lg"
                          style={{ color: "var(--color-gold)" }}>
                      {t.nav.all_sale} <ArrowRight size={11} />
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Rent dropdown */}
            <div className="relative" onMouseEnter={() => setMenu("rent")}>
              <button className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl transition-all text-sm font-medium
                ${menu === "rent" ? "text-white bg-white/10" : "text-white/75 hover:text-white hover:bg-white/8"}`}>
                {t.nav.rent}
                <ChevronDown size={13} style={{ transform: menu === "rent" ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
              </button>

              {menu === "rent" && (
                <div className="absolute top-full left-0 mt-2 w-56 rounded-2xl overflow-hidden shadow-2xl z-50"
                     style={{ background: "oklch(0.13 0.045 260 / 0.97)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.1)" }}>
                  <div className="px-4 py-2.5 border-b border-white/8">
                    <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--color-primary)" }}>
                      {t.nav.rent}
                    </p>
                  </div>
                  {RENT_ITEMS.map(({ label, href, Icon }) => (
                    <Link key={href} href={href} onClick={() => setMenu(null)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-white/75 hover:text-white hover:bg-white/8 transition-colors">
                      <Icon size={13} style={{ color: "var(--color-primary)", opacity: 0.8 }} />
                      {label}
                    </Link>
                  ))}
                  <div className="border-t border-white/8 mx-3 mt-1 pt-1 pb-1">
                    <Link href="/search?contrat=Location" onClick={() => setMenu(null)}
                          className="flex items-center justify-between px-1 py-2 text-xs font-semibold hover:text-white transition-colors"
                          style={{ color: "var(--color-primary)" }}>
                      {t.nav.all_rent} <ArrowRight size={11} />
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Separator */}
            <span className="w-px h-4 bg-white/15 mx-1" />

            {/* Direct links */}
            <Link href="/search" onMouseEnter={() => setMenu(null)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-white/75 hover:text-white hover:bg-white/8 transition-all text-sm font-medium">
              {t.nav.search}
            </Link>
            <Link href="/map" onMouseEnter={() => setMenu(null)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-white/75 hover:text-white hover:bg-white/8 transition-all text-sm font-medium">
              <Map size={13} /> {t.nav.map}
            </Link>
            <Link href="/recommend" onMouseEnter={() => setMenu(null)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl transition-all text-sm font-semibold"
                  style={{ color: "var(--color-gold)" }}>
              <Sparkles size={13} /> {t.nav.recommend}
            </Link>
            <Link href="/legal" onMouseEnter={() => setMenu(null)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl transition-all text-sm font-medium text-white/75 hover:text-white hover:bg-white/8">
              <Scale size={13} /> {t.nav.legal}
            </Link>
            {(session?.user as { role?: string })?.role === "admin" && (
              <a href="http://localhost:5173" onMouseEnter={() => setMenu(null)}
                 className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl transition-all text-sm font-semibold"
                 style={{ color: "var(--color-gold)", border: "1px solid var(--color-gold)", borderRadius: 8 }}>
                Admin
              </a>
            )}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="hidden lg:block"><LangSwitcher /></div>

            {session?.user ? (
              <Link href="/me"
                    className="hidden lg:inline-flex items-center gap-1.5 text-sm text-white/75 hover:text-white transition-colors px-3 py-2 rounded-xl hover:bg-white/8">
                <User size={14} /> {session.user.name?.split(" ")[0] ?? t.nav.account}
              </Link>
            ) : (
              <Link href="/signin"
                    className="hidden lg:inline-flex text-sm text-white/70 hover:text-white transition-colors px-3 py-2 rounded-xl hover:bg-white/8">
                {t.nav.signin}
              </Link>
            )}

            <Link href="/me/post"
                  className="hidden sm:inline-flex items-center gap-1.5 text-sm font-bold px-4 py-2.5 rounded-xl hover:opacity-90 transition-opacity"
                  style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
              {t.nav.post} <ArrowRight size={13} />
            </Link>

            {/* Mobile hamburger */}
            <button onClick={() => setMobileOpen(o => !o)}
                    className="lg:hidden flex items-center justify-center w-10 h-10 rounded-xl text-white/80 hover:bg-white/10 transition-colors">
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="lg:hidden border-t border-white/10 px-6 pb-6 pt-4 space-y-1"
               style={{ background: "oklch(0.13 0.045 260 / 0.98)" }}>
            <p className="text-[10px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--color-gold)" }}>{t.nav.buy}</p>
            {BUY_ITEMS.map(({ label, href }) => (
              <Link key={href} href={href} onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-2 py-2.5 text-sm text-white/75 hover:text-white border-b border-white/5 transition-colors">
                <span className="w-1 h-1 rounded-full bg-gold/60 flex-shrink-0" />{label}
              </Link>
            ))}
            <p className="text-[10px] font-bold uppercase tracking-widest mb-3 pt-4" style={{ color: "var(--color-primary)" }}>{t.nav.rent}</p>
            {RENT_ITEMS.map(({ label, href }) => (
              <Link key={href} href={href} onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-2 py-2.5 text-sm text-white/75 hover:text-white border-b border-white/5 transition-colors">
                <span className="w-1 h-1 rounded-full flex-shrink-0" style={{ background: "var(--color-primary)", opacity: 0.6 }} />{label}
              </Link>
            ))}
            <div className="pt-4 space-y-1">
              <Link href="/search"    onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-2.5 text-sm text-white/75 hover:text-white">{t.nav.search}</Link>
              <Link href="/map"       onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-2.5 text-sm text-white/75 hover:text-white"><Map size={13} />{t.nav.map}</Link>
              <Link href="/recommend" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-2.5 text-sm font-semibold" style={{ color: "var(--color-gold)" }}><Sparkles size={13} />{t.nav.recommend}</Link>
              <Link href="/legal" onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-2 py-2.5 text-sm text-white/75 hover:text-white">
                <Scale size={13} />{t.nav.legal}
              </Link>
              {(session?.user as { role?: string })?.role === "admin" && (
                <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer"
                   onClick={() => setMobileOpen(false)}
                   className="flex items-center gap-2 py-2.5 text-sm font-semibold"
                   style={{ color: "var(--color-gold)" }}>
                  Admin
                </a>
              )}
            </div>
            <div className="pt-4 flex items-center gap-3 border-t border-white/10">
              <LangSwitcher />
              {session?.user
                ? <Link href="/me" onClick={() => setMobileOpen(false)} className="text-sm text-white/75 hover:text-white">{t.nav.account}</Link>
                : <Link href="/signin" onClick={() => setMobileOpen(false)} className="text-sm text-white/75 hover:text-white">{t.nav.signin}</Link>
              }
              <Link href="/me/post" onClick={() => setMobileOpen(false)}
                    className="ml-auto inline-flex items-center gap-1 text-sm font-bold px-4 py-2 rounded-xl"
                    style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                {t.nav.post} <ArrowRight size={12} />
              </Link>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}

/* ── Light (inner pages) variant ─────────────────────────── */
interface NavbarLightProps {
  withSearch?: boolean;
  centerLabel?: React.ReactNode;
  right?: React.ReactNode;
}

export function NavbarLight({ withSearch, centerLabel, right }: NavbarLightProps) {
  const { t } = useLang();
  const { data: session } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAdmin = (session?.user as { role?: string })?.role === "admin";
  const NAV_LINKS = [
    { label: t.nav.buy,       href: "/search?contrat=Vente" },
    { label: t.nav.rent,      href: "/search?contrat=Location" },
    { label: t.nav.search,    href: "/search" },
    { label: t.nav.map,       href: "/map" },
    { label: t.nav.recommend, href: "/recommend", accent: true },
    { label: t.nav.legal,     href: "/legal" },
  ];

  return (
    <>
      <nav className="sticky top-0 z-40 border-b border-navy/10 bg-white backdrop-blur-md shadow-sm"
           style={{ borderTop: "3px solid var(--color-gold)" }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-[66px] flex items-center gap-3">

          {/* Logo */}
          <Link href="/" className="shrink-0">
            <img src="/logo.png" alt="EstateMind"
                 style={{ height: "52px", width: "auto", objectFit: "contain" }} />
          </Link>

          {/* Desktop nav links — only when no search / no centerLabel */}
          {!withSearch && !centerLabel && (
            <div className="hidden lg:flex items-center gap-0.5 ml-3">
              {NAV_LINKS.map(({ label, href, accent }) => (
                <Link key={href} href={href}
                      className="px-3.5 py-2 rounded-xl text-sm font-medium transition-colors hover:bg-navy/5"
                      style={accent
                        ? { color: "var(--color-gold)", fontWeight: 600 }
                        : { color: "var(--color-navy)", opacity: 0.65 }}>
                  {label}
                </Link>
              ))}
              {isAdmin && (
                <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer"
                   className="px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors"
                   style={{ color: "var(--color-gold)", border: "1px solid var(--color-gold)", borderRadius: 8 }}>
                  Admin
                </a>
              )}
            </div>
          )}

          {/* Search bar */}
          {withSearch && (
            <div className="flex-1 max-w-2xl mx-4">
              <SearchBar placeholder={t.search.placeholder} />
            </div>
          )}

          {/* Center label (recommend page title etc.) */}
          {centerLabel && (
            <div className="flex-1 flex justify-center">
              <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--color-navy)" }}>
                {centerLabel}
              </div>
            </div>
          )}

          {/* Right side */}
          <div className="flex items-center gap-2 shrink-0 ml-auto">
            <LangSwitcher />
            {right ?? (
              <>
                {session?.user ? (
                  <Link href="/me"
                        className="hidden sm:flex items-center gap-1.5 text-sm font-medium px-3 py-2 rounded-xl hover:bg-navy/5 transition-colors"
                        style={{ color: "var(--color-navy)", opacity: 0.65 }}>
                    <User size={14} /> {session.user.name?.split(" ")[0] ?? t.nav.account}
                  </Link>
                ) : (
                  <Link href="/signin"
                        className="hidden sm:block text-sm font-medium px-4 py-2 rounded-xl border border-navy/15 hover:border-navy/35 transition-colors"
                        style={{ color: "var(--color-navy)" }}>
                    {t.nav.signin}
                  </Link>
                )}
                <Link href="/me/post"
                      className="hidden sm:inline-flex items-center gap-1.5 text-sm font-bold px-4 py-2.5 rounded-xl hover:opacity-90 transition-opacity"
                      style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                  {t.nav.post} <ArrowRight size={13} />
                </Link>
              </>
            )}
            {/* Mobile hamburger (shown when no special center content) */}
            {!centerLabel && (
              <button onClick={() => setMobileOpen(o => !o)}
                      className="lg:hidden flex items-center justify-center w-10 h-10 rounded-xl hover:bg-navy/5 transition-colors"
                      style={{ color: "var(--color-navy)" }}>
                {mobileOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            )}
          </div>
        </div>

        {/* Mobile dropdown */}
        {mobileOpen && (
          <div className="lg:hidden border-t border-navy/8 px-4 pb-5 pt-3 space-y-1 bg-white">
            {NAV_LINKS.map(({ label, href, accent }) => (
              <Link key={href} href={href} onClick={() => setMobileOpen(false)}
                    className="flex items-center px-3 py-2.5 rounded-xl text-sm font-medium"
                    style={accent ? { color: "var(--color-gold)", fontWeight: 600 } : { color: "var(--color-navy)", opacity: 0.7 }}>
                {label}
              </Link>
            ))}
            {isAdmin && (
              <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer"
                 onClick={() => setMobileOpen(false)}
                 className="flex items-center px-3 py-2.5 rounded-xl text-sm font-semibold"
                 style={{ color: "var(--color-gold)", fontWeight: 600 }}>
                Admin
              </a>
            )}
            <div className="pt-3 flex items-center gap-3 border-t border-navy/10">
              {session?.user
                ? <Link href="/me" onClick={() => setMobileOpen(false)} className="text-sm font-medium" style={{ color: "var(--color-navy)", opacity: 0.65 }}>{t.nav.account}</Link>
                : <Link href="/signin" onClick={() => setMobileOpen(false)} className="text-sm font-medium" style={{ color: "var(--color-navy)", opacity: 0.65 }}>{t.nav.signin}</Link>
              }
              <Link href="/me/post" onClick={() => setMobileOpen(false)}
                    className="ml-auto inline-flex items-center gap-1 text-sm font-bold px-4 py-2 rounded-xl"
                    style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                {t.nav.post} <ArrowRight size={12} />
              </Link>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}

/* ── Minimal (dashboard / post pages) ─────────────────────── */
interface NavbarMinimalProps {
  rightLabel: string;
  rightHref: string;
}

export function NavbarMinimal({ rightLabel, rightHref }: NavbarMinimalProps) {
  return (
    <nav className="sticky top-0 z-40 border-b border-navy/10 bg-white shadow-sm"
         style={{ borderTop: "3px solid var(--color-gold)" }}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/">
          <img src="/logo.png" alt="EstateMind" style={{ height: "50px", width: "auto", objectFit: "contain" }} />
        </Link>
        <div className="flex items-center gap-3">
          <LangSwitcher />
          <Link href={rightHref} className="text-sm font-medium hover:underline"
                style={{ color: "var(--color-navy)", opacity: 0.55 }}>
            {rightLabel}
          </Link>
        </div>
      </div>
    </nav>
  );
}

/* ── Auth nav (sign in / sign up pages) ─────────────────────── */
export function NavbarAuth() {
  return (
    <nav className="sticky top-0 z-40 border-b border-navy/10 bg-white shadow-sm"
         style={{ borderTop: "3px solid var(--color-gold)" }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/">
          <img src="/logo.png" alt="EstateMind" style={{ height: "50px", width: "auto", objectFit: "contain" }} />
        </Link>
        <LangSwitcher />
      </div>
    </nav>
  );
}

/* ── Dashboard nav (with sign-out) ──────────────────────────── */
export function NavbarDashboard() {
  const { t } = useLang();
  return (
    <nav className="sticky top-0 z-40 border-b border-navy/10 bg-white shadow-sm"
         style={{ borderTop: "3px solid var(--color-gold)" }}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/">
          <img src="/logo.png" alt="EstateMind" style={{ height: "50px", width: "auto", objectFit: "contain" }} />
        </Link>
        <div className="flex items-center gap-3">
          <LangSwitcher />
          <button onClick={() => signOut({ callbackUrl: "/" })}
                  className="flex items-center gap-2 text-sm font-medium hover:underline"
                  style={{ color: "var(--color-navy)", opacity: 0.5 }}>
            {t.nav.logout}
          </button>
        </div>
      </div>
    </nav>
  );
}
