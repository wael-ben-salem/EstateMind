import Link from "next/link";
import type { Locale, Dict } from "@/i18n/dictionaries";

function OutliersIcon() {
  return (
    <div className="flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-violet-600 shadow-md shadow-primary/30">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <circle cx="5.5" cy="12" r="2" fill="white" fillOpacity="0.80" />
        <circle cx="9.5" cy="13.5" r="2" fill="white" fillOpacity="0.80" />
        <circle cx="7" cy="8.5" r="2" fill="white" fillOpacity="0.80" />
        <circle cx="15" cy="3.5" r="2.4" fill="white" />
        <line x1="8.5" y1="10" x2="15" y2="3.5" stroke="white" strokeWidth="0.8" strokeOpacity="0.35" strokeDasharray="1.8 1.5" />
      </svg>
    </div>
  );
}

export function Footer({ locale, dict }: { locale: Locale; dict: Dict }) {
  const year = new Date().getFullYear();
  const link = (p: string) => `/${locale}${p}`;
  return (
    <footer className="border-t border-border/50 bg-card/50">
      <div className="mx-auto max-w-7xl px-4 py-14">
        <div className="flex flex-col gap-10 sm:flex-row sm:items-start sm:justify-between">

          {/* Brand */}
          <div className="max-w-xs flex-1">
            <Link href={link("/")} className="mb-4 flex items-center gap-2.5">
              <OutliersIcon />
              <span className="text-[15px] font-bold tracking-tight">
                Out<span className="bg-gradient-to-r from-primary to-violet-500 bg-clip-text text-transparent">liers</span>
              </span>
            </Link>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {dict.brand.tagline}
            </p>
            <div className="mt-5 flex items-center gap-1.5">
              <div className="size-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span className="text-xs text-muted-foreground">6 agents IA actifs</span>
            </div>
          </div>

          {/* Platform */}
          <div className="space-y-4">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/50">
              Platform
            </p>
            <nav className="flex flex-col gap-2.5 text-sm">
              <Link href={link("/search")} className="text-muted-foreground transition-colors hover:text-foreground">
                {dict.nav.search}
              </Link>
              <Link href={link("/map")} className="text-muted-foreground transition-colors hover:text-foreground">
                Carte des prix
              </Link>
              <Link href={link("/contract-analyzer")} className="text-muted-foreground transition-colors hover:text-foreground">
                Analyse de contrat
              </Link>
              <Link href={link("/me/post")} className="text-muted-foreground transition-colors hover:text-foreground">
                {dict.nav.post}
              </Link>
            </nav>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/50">
              Company
            </p>
            <nav className="flex flex-col gap-2.5 text-sm">
              <Link href={link("/about")} className="text-muted-foreground transition-colors hover:text-foreground">
                {dict.footer.about}
              </Link>
              <Link href={link("/contact")} className="text-muted-foreground transition-colors hover:text-foreground">
                {dict.footer.contact}
              </Link>
              <Link href={link("/legal")} className="text-muted-foreground transition-colors hover:text-foreground">
                {dict.footer.legal}
              </Link>
            </nav>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-border/50 pt-6 sm:flex-row sm:items-center">
          <p className="text-xs text-muted-foreground/50">
            © {year} {dict.brand.name}. {dict.footer.rights}
          </p>
          <p className="text-xs text-muted-foreground/40">
            Powered by AI · Tunisia 🇹🇳
          </p>
        </div>
      </div>
    </footer>
  );
}
