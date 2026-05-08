import Link from "next/link";
import { Suspense } from "react";
import {
  MapPin,
  BedDouble,
  Maximize,
  Layers,
  Phone,
  Building,
  ExternalLink,
  TrendingUp,
  ArrowLeft,
} from "lucide-react";
import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { getDict, isLocale, type Locale } from "@/i18n/dictionaries";
import { listingImages, formatPrice, listingTitle } from "@/lib/listing";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  AIPriceCard,
  AIPriceCardSkeleton,
  AIAnomalyCard,
  AIAnomalyCardSkeleton,
} from "@/components/listings/ai-cards";
import { ListingCard } from "@/components/listings/listing-card";

const AMENITIES = [
  { key: "hasAscenseur",    label: "Ascenseur",     icon: "🛗" },
  { key: "hasBalcon",       label: "Balcon",         icon: "🏗" },
  { key: "hasChaffage",     label: "Chauffage",      icon: "🔥" },
  { key: "hasClimatisation",label: "Climatisation",  icon: "❄️" },
  { key: "hasGarage",       label: "Garage",         icon: "🚗" },
  { key: "hasGardien",      label: "Gardien",        icon: "🛡" },
  { key: "hasJardin",       label: "Jardin",         icon: "🌳" },
  { key: "hasParking",      label: "Parking",        icon: "🅿️" },
  { key: "hasPiscine",      label: "Piscine",        icon: "🏊" },
  { key: "hasTerrasse",     label: "Terrasse",       icon: "🌇" },
] as const;

const POIS = [
  { key: "ecole",     label: "Écoles" },
  { key: "hopital",   label: "Hôpitaux" },
  { key: "pharmacie", label: "Pharmacies" },
  { key: "magasin",   label: "Magasins" },
  { key: "marche",    label: "Marchés" },
  { key: "restaurant",label: "Restaurants" },
  { key: "bus",       label: "Bus" },
  { key: "railway",   label: "Train" },
] as const;

export default async function ListingPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  if (!isLocale(locale)) notFound();
  const numId = Number(id);
  if (!Number.isInteger(numId)) notFound();

  const listing = await prisma.listing.findUnique({ where: { id: numId } });
  if (!listing) notFound();

  const comparables = await prisma.listing.findMany({
    where: {
      id: { not: numId },
      gouvernerat: listing.gouvernerat ?? undefined,
      type: listing.type ?? undefined,
      contrat: listing.contrat ?? undefined,
      ...(listing.prix ? { prix: { gte: listing.prix * 0.5, lte: listing.prix * 1.5 } } : {}),
    },
    orderBy: { createdAt: "desc" },
    take: 4,
  });

  const dict = await getDict(locale);
  const images = listingImages(listing);
  const cover = images[0];
  const price = formatPrice(listing.prix, locale);
  const title = listingTitle(listing);
  const market = formatPrice(listing.prixQ75Contrat, locale);
  const isRental = listing.contrat === "location";

  const activeAmenities = AMENITIES.filter((a) => (listing as Record<string, unknown>)[a.key] === true);
  const activePois = POIS.filter((p) => {
    const v = (listing as Record<string, unknown>)[p.key];
    return typeof v === "number" && v > 0;
  });

  const location = [listing.adresse, listing.localite, listing.ville, listing.gouvernerat]
    .filter(Boolean)
    .join(", ");

  return (
    <div className="mx-auto max-w-6xl px-4 pb-20 pt-6">

      {/* Back */}
      <Link
        href={`/${locale}/search`}
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="size-3.5" />
        {dict.home.browseAll}
      </Link>

      {/* Gallery */}
      <section className="mb-8">
        {cover ? (
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="overflow-hidden rounded-2xl bg-muted sm:col-span-2 sm:row-span-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={cover}
                alt={title}
                className="aspect-video h-full w-full object-cover sm:aspect-auto"
              />
            </div>
            {images.slice(1, 5).map((u, i) => (
              <div key={i} className="overflow-hidden rounded-2xl bg-muted">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={u}
                  alt={`${title} ${i + 2}`}
                  className="aspect-video w-full object-cover sm:aspect-square"
                  loading="lazy"
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex aspect-video w-full items-center justify-center rounded-2xl bg-muted text-sm text-muted-foreground">
            {dict.listing.noPhoto}
          </div>
        )}
      </section>

      {/* Main grid */}
      <section className="grid gap-8 lg:grid-cols-3">

        {/* Left: details */}
        <div className="lg:col-span-2 space-y-8">

          {/* Title & location */}
          <div>
            <div className="mb-2 flex flex-wrap gap-2">
              {listing.hautStanding && (
                <Badge className="bg-amber-500/90 text-white text-[10px] px-2 py-0.5">★ Premium</Badge>
              )}
              {listing.contrat && (
                <Badge variant={isRental ? "secondary" : "default"} className="capitalize text-[10px] px-2 py-0.5">
                  {listing.contrat}
                </Badge>
              )}
              {listing.type && (
                <Badge variant="outline" className="capitalize text-[10px] px-2 py-0.5">
                  {listing.type}
                </Badge>
              )}
            </div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
            {location && (
              <p className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
                <MapPin className="size-4 shrink-0" />
                {location}
              </p>
            )}
          </div>

          {/* Quick stats */}
          <div className="flex flex-wrap gap-2.5">
            {listing.pieces != null && (
              <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm">
                <BedDouble className="size-4 text-muted-foreground" />
                <span className="font-medium">{listing.pieces}</span>
                <span className="text-muted-foreground">pièces</span>
              </div>
            )}
            {listing.surface != null && (
              <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm">
                <Maximize className="size-4 text-muted-foreground" />
                <span className="font-medium">{Math.round(listing.surface)}</span>
                <span className="text-muted-foreground">m²</span>
              </div>
            )}
            {listing.etage != null && (
              <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm">
                <Layers className="size-4 text-muted-foreground" />
                <span className="text-muted-foreground">Étage</span>
                <span className="font-medium">{listing.etage}</span>
              </div>
            )}
            {listing.anneeConstr != null && (
              <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm">
                <span className="text-muted-foreground">Construit en</span>
                <span className="font-medium">{listing.anneeConstr}</span>
              </div>
            )}
          </div>

          {/* Amenities */}
          {activeAmenities.length > 0 && (
            <div>
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                Équipements
              </p>
              <div className="flex flex-wrap gap-2">
                {activeAmenities.map((a) => (
                  <div
                    key={a.key}
                    className="flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-2 text-xs font-medium"
                  >
                    <span>{a.icon}</span>
                    {a.label}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* POIs */}
          {activePois.length > 0 && (
            <div>
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                À proximité
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {activePois.map((p) => {
                  const v = (listing as Record<string, unknown>)[p.key] as number;
                  return (
                    <div key={p.key} className="rounded-xl border border-border bg-card px-3 py-2.5">
                      <div className="text-xs text-muted-foreground">{p.label}</div>
                      <div className="mt-0.5 text-sm font-semibold">{v}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Description */}
          {listing.descClean && (
            <div>
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                Description
              </p>
              <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                {listing.descClean}
              </p>
            </div>
          )}
        </div>

        {/* Right: price card + AI cards */}
        <div className="space-y-4">

          {/* Price card */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
            <div className="bg-gradient-to-r from-blue-500/10 to-violet-500/10 px-5 pt-5 pb-4">
              <div className="text-3xl font-bold tracking-tight text-foreground">
                {price ?? <span className="text-muted-foreground text-base">{dict.listing.noPrice}</span>}
              </div>
              {isRental && price && (
                <div className="mt-0.5 text-xs text-muted-foreground">{dict.listing.perMonth}</div>
              )}
              {listing.prixM2 != null && (
                <div className="mt-1 text-xs text-muted-foreground">
                  {Math.round(listing.prixM2).toLocaleString("fr-TN")} TND / m²
                </div>
              )}
            </div>
            <div className="px-5 pb-5 space-y-3">
              {market && (
                <div className="rounded-xl bg-secondary/50 px-3 py-2.5 text-xs">
                  <span className="text-muted-foreground">Marché Q75 ({listing.contrat}) : </span>
                  <strong className="text-foreground">{market}</strong>
                </div>
              )}
              <Separator />
              {listing.tel && (
                <a
                  href={`tel:${listing.tel}`}
                  className="flex items-center gap-2.5 rounded-xl border border-border bg-background px-3 py-2.5 text-sm font-medium hover:border-primary/40 hover:text-primary transition-colors"
                >
                  <Phone className="size-4 text-muted-foreground shrink-0" />
                  {listing.tel}
                </a>
              )}
              {listing.agence && (
                <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
                  <Building className="size-4 shrink-0" />
                  {listing.agence}
                </div>
              )}
              {listing.url && (
                <a
                  href={listing.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary transition-colors"
                >
                  <ExternalLink className="size-3" />
                  Annonce d&apos;origine
                </a>
              )}
            </div>
          </div>

          {/* AI price prediction */}
          <Suspense fallback={<AIPriceCardSkeleton />}>
            <AIPriceCard listing={listing} locale={locale as Locale} />
          </Suspense>

          {/* AI anomaly detection */}
          <Suspense fallback={<AIAnomalyCardSkeleton />}>
            <AIAnomalyCard listing={listing} />
          </Suspense>
        </div>
      </section>

      {/* Comparables */}
      {comparables.length > 0 && (
        <section className="mt-16">
          <div className="mb-6">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Similaires
            </p>
            <h2 className="flex items-center gap-2 text-xl font-bold tracking-tight">
              <TrendingUp className="size-5 text-primary" />
              Biens comparables
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {comparables.map((c) => (
              <ListingCard key={c.id} listing={c} locale={locale as Locale} dict={dict} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
