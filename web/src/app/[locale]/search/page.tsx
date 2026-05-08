import { Sparkles, Search, SlidersHorizontal } from "lucide-react";
import { notFound } from "next/navigation";
import type { Prisma } from "@/generated/prisma";
import { prisma } from "@/lib/prisma";
import { isLocale, getDict } from "@/i18n/dictionaries";
import { recommenderQuery } from "@/lib/agents";
import { ListingCard } from "@/components/listings/listing-card";
import { FilterSidebar, type SearchFilters } from "@/components/search/filter-sidebar";
import { Pagination } from "@/components/search/pagination";
import { SortSelect } from "@/components/search/sort-select";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { buttonVariants } from "@/components/ui/button";

const PAGE_SIZE = 24;

function titleCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

export default async function SearchPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = await getDict(locale);
  const sp = await searchParams;
  const get = (k: string) => {
    const v = sp[k];
    return Array.isArray(v) ? v[0] : v;
  };

  const filters: SearchFilters = {
    q: get("q"),
    gouvernerat: get("gouvernerat"),
    type: get("type"),
    contrat: get("contrat"),
    pieces: get("pieces"),
    priceMin: get("priceMin"),
    priceMax: get("priceMax"),
    sort: get("sort") ?? "newest",
    photos: get("photos") ?? "0",
  };
  const page = Math.max(1, parseInt(get("page") ?? "1", 10) || 1);

  const [gouvernerats, types, intentResp] = await Promise.all([
    prisma.listing.groupBy({
      by: ["gouvernerat"],
      where: { gouvernerat: { not: null } },
      _count: true,
      orderBy: { _count: { id: "desc" } },
    }).then((rows) => rows.map((r) => r.gouvernerat).filter((x): x is string => !!x).slice(0, 24)),
    prisma.listing.groupBy({
      by: ["type"],
      where: { type: { not: null } },
      _count: true,
      orderBy: { _count: { id: "desc" } },
    }).then((rows) => rows.map((r) => r.type).filter((x): x is string => !!x).slice(0, 12)),
    filters.q ? recommenderQuery(filters.q, 5) : Promise.resolve(null),
  ]);

  const intent = intentResp?.understanding ?? null;

  const effective = {
    gouvernerat: filters.gouvernerat ?? (intent?.city ? titleCase(intent.city) : undefined),
    type: filters.type ?? (intent?.property_type ? titleCase(intent.property_type) : undefined),
    contrat: filters.contrat ?? intent?.contract ?? undefined,
    pieces: filters.pieces ? Number(filters.pieces) : intent?.rooms ?? undefined,
    priceMin: filters.priceMin ? Number(filters.priceMin) : undefined,
    priceMax: filters.priceMax ? Number(filters.priceMax) : intent?.budget_max ?? undefined,
    amenities: intent?.amenities ?? [],
  };

  const where: Prisma.ListingWhereInput = {};
  if (effective.gouvernerat) {
    where.OR = [
      { gouvernerat: { equals: effective.gouvernerat } },
      { ville: { equals: effective.gouvernerat } },
    ];
  }
  if (effective.type) where.type = { equals: effective.type };
  if (effective.contrat) where.contrat = { equals: effective.contrat };
  if (effective.pieces) where.pieces = { gte: effective.pieces };
  if (effective.priceMin || effective.priceMax) {
    where.prix = {
      ...(effective.priceMin ? { gte: effective.priceMin } : {}),
      ...(effective.priceMax ? { lte: effective.priceMax } : {}),
    };
  }
  const photosOnly = get("photos") === "1";
  if (photosOnly) where.images = { startsWith: "http" };
  if (effective.amenities.includes("piscine")) where.hasPiscine = true;
  if (effective.amenities.includes("jardin")) where.hasJardin = true;
  if (effective.amenities.includes("parking")) where.hasParking = true;
  if (effective.amenities.includes("ascenseur")) where.hasAscenseur = true;

  const orderBy: Prisma.ListingOrderByWithRelationInput =
    filters.sort === "price-asc" ? { prix: "asc" }
    : filters.sort === "price-desc" ? { prix: "desc" }
    : { id: "desc" };

  const [total, results] = await Promise.all([
    prisma.listing.count({ where }),
    prisma.listing.findMany({ where, orderBy, skip: (page - 1) * PAGE_SIZE, take: PAGE_SIZE }),
  ]);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const chips: { label: string; from: "url" | "ai" }[] = [];
  if (effective.contrat) chips.push({ label: `Contrat: ${effective.contrat}`, from: filters.contrat ? "url" : "ai" });
  if (effective.type) chips.push({ label: `Type: ${effective.type}`, from: filters.type ? "url" : "ai" });
  if (effective.gouvernerat) chips.push({ label: `Lieu: ${effective.gouvernerat}`, from: filters.gouvernerat ? "url" : "ai" });
  if (effective.pieces) chips.push({ label: `${effective.pieces}+ pièces`, from: filters.pieces ? "url" : "ai" });
  if (effective.priceMin) chips.push({ label: `≥ ${effective.priceMin.toLocaleString("fr-TN")} TND`, from: "url" });
  if (effective.priceMax) chips.push({ label: `≤ ${effective.priceMax.toLocaleString("fr-TN")} TND`, from: filters.priceMax ? "url" : "ai" });
  effective.amenities.forEach((a) => chips.push({ label: a, from: "ai" }));

  const sortHidden = Object.fromEntries(
    Object.entries(filters).filter(([k, v]) => k !== "sort" && !!v) as [string, string][]
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">

      {/* Search bar */}
      <div className="mb-5 overflow-hidden rounded-2xl border border-border bg-card/60 shadow-sm backdrop-blur-sm">
        <form method="GET" action={`/${locale}/search`} className="flex items-center gap-2 px-4 py-3">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <Input
            type="search"
            name="q"
            defaultValue={filters.q}
            placeholder={dict.hero.searchPlaceholder}
            className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0 text-sm"
          />
          {filters.gouvernerat && <input type="hidden" name="gouvernerat" value={filters.gouvernerat} />}
          {filters.type && <input type="hidden" name="type" value={filters.type} />}
          {filters.contrat && <input type="hidden" name="contrat" value={filters.contrat} />}
          {filters.pieces && <input type="hidden" name="pieces" value={filters.pieces} />}
          {filters.priceMin && <input type="hidden" name="priceMin" value={filters.priceMin} />}
          {filters.priceMax && <input type="hidden" name="priceMax" value={filters.priceMax} />}
          {filters.photos && <input type="hidden" name="photos" value={filters.photos} />}
          <button
            type="submit"
            className={`${buttonVariants({ size: "sm" })} shrink-0 bg-gradient-to-r from-blue-500 to-violet-600 text-white border-0 hover:from-blue-400 hover:to-violet-500`}
          >
            {dict.hero.searchAction}
          </button>
        </form>
      </div>

      {/* AI intent banner */}
      {intent && (
        <div className="mb-5 overflow-hidden rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3">
          <div className="flex items-center gap-2 text-sm">
            <div className="flex size-6 items-center justify-center rounded-lg bg-primary/15">
              <Sparkles className="size-3.5 text-primary" />
            </div>
            <strong className="text-foreground">Recherche IA</strong>
            {intent.confidence != null && (
              <span className="ms-auto rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                {Math.round(intent.confidence * 100)}% confiance
              </span>
            )}
          </div>
          {(intentResp?.recommendation?.global_explanation ?? intentResp?.summary) && (
            <p className="mt-1.5 text-sm text-muted-foreground">
              {intentResp?.recommendation?.global_explanation ?? intentResp?.summary}
            </p>
          )}
          {((intentResp?.recommendation as Record<string, unknown>)?.relaxed_criteria as string[] | undefined)?.length ? (
            <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
              ⚠ Critères assouplis : {((intentResp?.recommendation as Record<string, unknown>)?.relaxed_criteria as string[]).join(", ")}
            </p>
          ) : null}
        </div>
      )}

      {/* Active filter chips */}
      {chips.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          {chips.map((c, i) => (
            <Badge
              key={i}
              variant={c.from === "ai" ? "default" : "secondary"}
              className={`gap-1 text-xs ${c.from === "ai" ? "bg-primary/15 text-primary border-primary/20 hover:bg-primary/20" : ""}`}
            >
              {c.from === "ai" && <Sparkles className="size-2.5" />}
              {c.label}
            </Badge>
          ))}
        </div>
      )}

      {/* Result count + sort */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="size-3.5 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{total.toLocaleString("fr-TN")}</span> résultats
          </p>
        </div>
        <SortSelect defaultValue={filters.sort ?? "newest"} hidden={sortHidden} action={`/${locale}/search`} />
      </div>

      {/* Sidebar + results */}
      <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <FilterSidebar locale={locale} filters={filters} gouvernerats={gouvernerats} types={types} />
        </aside>

        <section>
          {results.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border bg-card/40 py-16 text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-muted">
                <Search className="size-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium">Aucun bien trouvé</p>
              <p className="text-xs text-muted-foreground">Essayez d&apos;assouplir vos filtres.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {results.map((l) => (
                <ListingCard key={l.id} listing={l} locale={locale} dict={dict} />
              ))}
            </div>
          )}
          <Pagination
            basePath={`/${locale}/search`}
            searchParams={Object.fromEntries(
              Object.entries(filters).filter(([, v]) => !!v) as [string, string][]
            )}
            currentPage={page}
            totalPages={totalPages}
          />
        </section>
      </div>
    </div>
  );
}
