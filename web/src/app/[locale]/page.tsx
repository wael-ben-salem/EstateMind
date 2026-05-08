import Link from "next/link";
import { Search, Sparkles, TrendingUp, MapPin, Shield, ArrowRight, Brain, Zap } from "lucide-react";
import { prisma } from "@/lib/prisma";
import { getDict, isLocale } from "@/i18n/dictionaries";
import { notFound } from "next/navigation";
import { ListingCard } from "@/components/listings/listing-card";
import { buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CITY_GRADIENTS = [
  "from-violet-500/20 via-purple-500/8 to-transparent",
  "from-blue-500/20 via-cyan-500/8 to-transparent",
  "from-emerald-500/20 via-green-500/8 to-transparent",
  "from-amber-500/20 via-orange-500/8 to-transparent",
  "from-rose-500/20 via-pink-500/8 to-transparent",
  "from-indigo-500/20 via-blue-500/8 to-transparent",
  "from-teal-500/20 via-cyan-500/8 to-transparent",
  "from-orange-500/20 via-amber-500/8 to-transparent",
];

const CITY_DOTS = [
  "bg-violet-500", "bg-blue-500", "bg-emerald-500", "bg-amber-500",
  "bg-rose-500", "bg-indigo-500", "bg-teal-500", "bg-orange-500",
];

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = await getDict(locale);

  const featured = await prisma.listing.findMany({
    where: {
      images: { startsWith: "http" },
      prix: { not: null, gt: 1000 },
      gouvernerat: { not: null },
    },
    orderBy: { id: "desc" },
    take: 8,
  });

  const [cityCounts, totalCount] = await Promise.all([
    prisma.listing.groupBy({
      by: ["gouvernerat"],
      where: { gouvernerat: { not: null } },
      _count: { _all: true },
      orderBy: { _count: { id: "desc" } },
      take: 8,
    }),
    prisma.listing.count(),
  ]);

  const fmt = (n: number) =>
    n >= 1000 ? `${Math.round(n / 1000)}K+` : `${n}+`;

  return (
    <div className="pb-24">

      {/* ── Hero ── */}
      <section className="relative isolate overflow-hidden bg-[#060810]">
        {/* Gradient blobs — violet-dominant */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10"
          style={{
            background:
              "radial-gradient(ellipse 90% 65% at 15% -5%, oklch(0.42 0.22 272 / 0.40), transparent)," +
              "radial-gradient(ellipse 65% 55% at 85% 105%, oklch(0.50 0.20 300 / 0.30), transparent)," +
              "radial-gradient(ellipse 50% 40% at 55% 50%, oklch(0.38 0.10 268 / 0.12), transparent)",
          }}
        />
        {/* Dot grid */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 opacity-[0.035]"
          style={{
            backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />

        <div className="mx-auto max-w-5xl px-4 pb-24 pt-20 text-center sm:pt-28">

          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-1.5 text-xs font-medium text-white/65 backdrop-blur-sm">
            <Sparkles className="size-3 text-violet-400" />
            {dict.brand.tagline}
          </div>

          {/* Headline */}
          <h1 className="mb-6 text-balance text-4xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
            {dict.hero.title.split(" ").slice(0, -2).join(" ")}{" "}
            <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-fuchsia-400 bg-clip-text text-transparent">
              {dict.hero.title.split(" ").slice(-2).join(" ")}
            </span>
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-balance text-base text-white/50 sm:text-lg">
            {dict.hero.subtitle}
          </p>

          {/* Search */}
          <div className="mx-auto max-w-2xl">
            <form
              method="GET"
              action={`/${locale}/search`}
              className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/6 p-2 shadow-2xl shadow-black/40 backdrop-blur-md"
            >
              <Search className="ms-2 size-4 shrink-0 text-white/35" />
              <Input
                type="search"
                name="q"
                placeholder={dict.hero.searchPlaceholder}
                className="flex-1 border-0 bg-transparent text-white shadow-none placeholder:text-white/28 focus-visible:ring-0"
              />
              <button
                type="submit"
                className={`${buttonVariants({ size: "default" })} shrink-0 rounded-xl border-0 bg-primary font-semibold text-primary-foreground shadow-lg shadow-primary/35 hover:bg-primary/90`}
              >
                {dict.hero.searchAction}
              </button>
            </form>
          </div>

          {/* Stats */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-8">
            {[
              { icon: <TrendingUp className="size-4" />, value: fmt(totalCount), label: "Annonces" },
              { icon: <MapPin className="size-4" />, value: `${cityCounts.length}`, label: "Gouvernorats" },
              { icon: <Shield className="size-4" />, value: "6", label: "Agents IA" },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-2 text-white/55">
                <span className="text-violet-400/90">{s.icon}</span>
                <span className="text-xl font-bold text-white">{s.value}</span>
                <span className="text-sm">{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-background to-transparent" />
      </section>

      {/* ── Featured listings ── */}
      <section className="mx-auto mt-20 max-w-7xl px-4">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2.5">
              <div className="h-4 w-1 rounded-full bg-primary" />
              <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                {dict.home.featured}
              </p>
            </div>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Dernières annonces
            </h2>
          </div>
          <Link
            href={`/${locale}/search`}
            className={`${buttonVariants({ variant: "outline", size: "sm" })} gap-1.5 font-medium`}
          >
            {dict.home.browseAll}
            <ArrowRight className="size-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featured.map((l) => (
            <ListingCard key={l.id} listing={l} locale={locale} dict={dict} />
          ))}
        </div>
      </section>

      {/* ── By city ── */}
      <section className="mx-auto mt-24 max-w-7xl px-4">
        <div className="mb-8">
          <div className="mb-2 flex items-center gap-2.5">
            <div className="h-4 w-1 rounded-full bg-primary" />
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              Explorer
            </p>
          </div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {dict.home.byCity}
          </h2>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {cityCounts.map((c, i) => (
            <Link
              key={c.gouvernerat}
              href={`/${locale}/search?gouvernerat=${encodeURIComponent(c.gouvernerat ?? "")}`}
              className="group relative overflow-hidden rounded-2xl border border-border/60 bg-card p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/8"
            >
              <div
                className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${CITY_GRADIENTS[i % CITY_GRADIENTS.length]} opacity-60 transition-opacity duration-300 group-hover:opacity-100`}
              />
              <div className="relative">
                <div className={`mb-2.5 size-2.5 rounded-full ${CITY_DOTS[i % CITY_DOTS.length]} shadow-sm`} />
                <p className="font-semibold tracking-tight">{c.gouvernerat}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {c._count._all.toLocaleString(
                    locale === "ar" ? "ar-TN" : locale === "en" ? "en-US" : "fr-TN"
                  )}{" "}
                  biens
                </p>
                <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary opacity-0 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0.5">
                  Explorer <ArrowRight className="size-3" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── AI Features ── */}
      <section className="mx-auto mt-28 max-w-7xl px-4">
        <div className="overflow-hidden rounded-3xl border border-primary/15 bg-gradient-to-br from-primary/5 via-card to-violet-500/5 p-10 sm:p-14">

          <div className="mb-10 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/8 px-4 py-1.5 text-xs font-medium text-primary">
              <Sparkles className="size-3" />
              Propulsé par l&apos;IA
            </div>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Intelligence artificielle intégrée
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-sm text-muted-foreground">
              Chaque annonce est analysée en temps réel par 5 agents IA spécialisés pour vous donner une vision complète du marché.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                icon: <TrendingUp className="size-5" />,
                color: "text-violet-500 bg-violet-500/10",
                title: "Prix prédit",
                desc: "Notre modèle LightGBM estime la valeur marchande réelle de chaque bien en quelques millisecondes.",
              },
              {
                icon: <Shield className="size-5" />,
                color: "text-emerald-500 bg-emerald-500/10",
                title: "Anomalies détectées",
                desc: "Les annonces surévaluées ou frauduleuses sont identifiées et signalées automatiquement.",
              },
              {
                icon: <Zap className="size-5" />,
                color: "text-amber-500 bg-amber-500/10",
                title: "Recherche naturelle",
                desc: "Décrivez votre bien idéal en français — l&apos;IA interprète votre intention et filtre pour vous.",
              },
              {
                icon: <Brain className="size-5" />,
                color: "text-blue-500 bg-blue-500/10",
                title: "Analyse juridique",
                desc: "Notre agent droit immobilier répond à vos questions légales et analyse vos contrats.",
              },
              {
                icon: <Sparkles className="size-5" />,
                color: "text-pink-500 bg-pink-500/10",
                title: "Descriptions IA",
                desc: "BLIP-2 génère des descriptions professionnelles à partir des photos de votre annonce.",
              },
              {
                icon: <MapPin className="size-5" />,
                color: "text-cyan-500 bg-cyan-500/10",
                title: "Carte des prix",
                desc: "Heatmap interactive des prix au m² par zone — identifiez les secteurs sous-évalués.",
              },
            ].map((f) => (
              <div key={f.title} className="flex gap-4">
                <div className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${f.color}`}>
                  {f.icon}
                </div>
                <div>
                  <p className="font-semibold">{f.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
