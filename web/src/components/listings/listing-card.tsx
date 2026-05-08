import Link from "next/link";
import { MapPin, BedDouble, Maximize, Waves, Building2, Home, Trees, Briefcase, Warehouse } from "lucide-react";
import type { Listing } from "@/generated/prisma";
import type { Locale, Dict } from "@/i18n/dictionaries";
import { Badge } from "@/components/ui/badge";
import { listingImages, formatPrice, listingTitle } from "@/lib/listing";
import { FavoriteButton } from "./favorite-button";

type Props = {
  listing: Listing;
  locale: Locale;
  dict: Dict;
  defaultFavorited?: boolean;
};

const TYPE_META: Record<string, { icon: React.ReactNode; from: string; via: string }> = {
  appartement: {
    icon: <Building2 className="size-10 opacity-20" />,
    from: "from-violet-500/25",
    via: "via-violet-400/10",
  },
  villa: {
    icon: <Home className="size-10 opacity-20" />,
    from: "from-emerald-500/25",
    via: "via-emerald-400/10",
  },
  maison: {
    icon: <Home className="size-10 opacity-20" />,
    from: "from-emerald-500/25",
    via: "via-emerald-400/10",
  },
  terrain: {
    icon: <Trees className="size-10 opacity-20" />,
    from: "from-amber-500/25",
    via: "via-amber-400/10",
  },
  ferme: {
    icon: <Trees className="size-10 opacity-20" />,
    from: "from-lime-500/25",
    via: "via-lime-400/10",
  },
  bureau: {
    icon: <Briefcase className="size-10 opacity-20" />,
    from: "from-blue-500/25",
    via: "via-blue-400/10",
  },
  local: {
    icon: <Warehouse className="size-10 opacity-20" />,
    from: "from-orange-500/25",
    via: "via-orange-400/10",
  },
};

function getTypeMeta(type: string | null | undefined) {
  const key = type?.toLowerCase() ?? "";
  return (
    TYPE_META[key] ??
    TYPE_META[Object.keys(TYPE_META).find((k) => key.includes(k)) ?? ""] ?? {
      icon: <Building2 className="size-10 opacity-20" />,
      from: "from-muted",
      via: "via-muted/50",
    }
  );
}

export function ListingCard({ listing, locale, dict, defaultFavorited }: Props) {
  const imgs = listingImages(listing);
  const cover = imgs[0];
  const price = formatPrice(listing.prix, locale);
  const title = listingTitle(listing);
  const isRental = listing.contrat === "location";
  const meta = getTypeMeta(listing.type);
  const location = [listing.ville, listing.gouvernerat].filter(Boolean).join(", ");

  return (
    <Link href={`/${locale}/listings/${listing.id}`} className="group block">
      <div className="overflow-hidden rounded-2xl border border-border/60 bg-card shadow-sm transition-all duration-300 group-hover:-translate-y-1.5 group-hover:border-primary/25 group-hover:shadow-xl group-hover:shadow-primary/8">

        {/* Image */}
        <div className="relative aspect-[4/3] w-full overflow-hidden bg-muted">
          <FavoriteButton listingId={listing.id} defaultFavorited={defaultFavorited} locale={locale} />

          {cover ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={cover}
              alt={title}
              loading="lazy"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
            />
          ) : (
            <div className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${meta.from} ${meta.via} to-transparent bg-muted`}>
              <div className="text-foreground/30">{meta.icon}</div>
            </div>
          )}

          {/* Badges */}
          <div className="absolute start-2.5 top-2.5 flex flex-col gap-1.5">
            {listing.hautStanding && (
              <Badge className="bg-amber-500/90 px-2 py-0.5 text-[10px] text-white shadow backdrop-blur-sm">
                ★ Premium
              </Badge>
            )}
            {listing.contrat && (
              <Badge
                variant={isRental ? "secondary" : "default"}
                className="px-2 py-0.5 text-[10px] capitalize shadow backdrop-blur-sm"
              >
                {listing.contrat}
              </Badge>
            )}
          </div>

          {/* Price overlay */}
          {price && (
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-3.5 pb-3 pt-8">
              <p className="text-base font-bold leading-none text-white tabular-nums">
                {price}
                {isRental && (
                  <span className="ms-1 text-xs font-normal text-white/65">
                    {dict.listing.perMonth}
                  </span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="px-4 py-3.5">
          <h3 className="line-clamp-1 text-sm font-semibold leading-snug tracking-tight">
            {title}
          </h3>

          {location && (
            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin className="size-3 shrink-0" />
              <span className="truncate">{location}</span>
            </p>
          )}

          {/* Stats */}
          <div className="mt-3 flex items-center gap-3 border-t border-border/50 pt-3 text-xs text-muted-foreground">
            {listing.pieces != null && (
              <span className="flex items-center gap-1">
                <BedDouble className="size-3.5 shrink-0" />
                {listing.pieces}
              </span>
            )}
            {listing.surface != null && (
              <span className="flex items-center gap-1">
                <Maximize className="size-3.5 shrink-0" />
                {Math.round(listing.surface)} m²
              </span>
            )}
            {listing.hasPiscine && (
              <span className="flex items-center gap-1 text-cyan-600 dark:text-cyan-400">
                <Waves className="size-3.5 shrink-0" />
                Piscine
              </span>
            )}
            {!price && (
              <span className="ms-auto font-medium text-foreground/60">
                {dict.listing.noPrice}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
