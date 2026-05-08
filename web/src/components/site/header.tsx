import Link from "next/link";
import { Search, Plus, Map as MapIcon, FileSearch } from "lucide-react";
import type { Locale, Dict } from "@/i18n/dictionaries";
import { buttonVariants } from "@/components/ui/button";
import { LocaleSwitcher } from "./locale-switcher";
import { UserMenu } from "./user-menu";

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

const NAV_LINKS = (link: (p: string) => string, dict: Dict) => [
  { href: link("/search"), icon: <Search className="size-3.5" />, label: dict.nav.search },
  { href: link("/map"), icon: <MapIcon className="size-3.5" />, label: "Carte" },
  { href: link("/contract-analyzer"), icon: <FileSearch className="size-3.5" />, label: "Contrat" },
];

export function Header({ locale, dict }: { locale: Locale; dict: Dict }) {
  const link = (path: string) => `/${locale}${path}`;
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4">

        {/* Brand */}
        <Link href={link("/")} className="flex items-center gap-2.5 me-2 shrink-0 group">
          <OutliersIcon />
          <span className="text-[15px] font-bold tracking-tight">
            Out<span className="bg-gradient-to-r from-primary to-violet-500 bg-clip-text text-transparent">liers</span>
          </span>
        </Link>

        {/* Separator */}
        <div className="hidden h-5 w-px bg-border sm:block" />

        {/* Nav */}
        <nav className="hidden items-center gap-0.5 sm:flex">
          {NAV_LINKS(link, dict).map(({ href, icon, label }) => (
            <Link
              key={href}
              href={href}
              className={`${buttonVariants({ variant: "ghost", size: "sm" })} gap-1.5 text-muted-foreground hover:text-foreground font-medium`}
            >
              {icon}
              {label}
            </Link>
          ))}
        </nav>

        <div className="ms-auto flex items-center gap-2">
          <LocaleSwitcher current={locale} />

          <Link
            href={link("/me/post")}
            className={`${buttonVariants({ size: "sm" })} hidden sm:inline-flex gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground border-0 shadow-sm shadow-primary/25 font-medium`}
          >
            <Plus className="size-3.5" />
            {dict.nav.post}
          </Link>

          <UserMenu locale={locale} />
        </div>
      </div>
    </header>
  );
}
