import { Sparkles, AlertTriangle, TrendingUp, TrendingDown } from "lucide-react";
import type { Listing } from "@/generated/prisma";
import {
  predictPrice,
  scoreAnomaly,
  listingToPropertyInput,
  extractPredictedPrice,
  extractAnomalyVerdict,
} from "@/lib/agents";
import { formatPrice } from "@/lib/listing";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

const VERDICT_STYLE = {
  low:    { ring: "border-emerald-500/30 bg-emerald-500/5", badge: "bg-emerald-600 text-white" },
  medium: { ring: "border-amber-500/40 bg-amber-500/5",     badge: "bg-amber-500 text-white" },
  high:   { ring: "border-destructive/40 bg-destructive/5", badge: "bg-destructive text-destructive-foreground" },
  unknown:{ ring: "border-dashed",                          badge: "bg-muted text-muted-foreground" },
} as const;

export function AIPriceCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="size-4 text-primary" />
          Prix prédit par l&apos;IA
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-4 w-40" />
      </CardContent>
    </Card>
  );
}

export async function AIPriceCard({ listing, locale }: { listing: Listing; locale: string }) {
  const resp = await predictPrice(listingToPropertyInput(listing));
  const predicted = extractPredictedPrice(resp);
  const asking = listing.prix;
  const formatted = predicted ? formatPrice(predicted, locale) : null;
  const delta =
    predicted && asking ? ((asking - predicted) / predicted) * 100 : null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="size-4 text-primary" />
          Prix prédit par l&apos;IA
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {!predicted ? (
          <p className="text-sm text-muted-foreground">Prédiction indisponible.</p>
        ) : (
          <>
            <p className="text-2xl font-bold text-foreground">{formatted}</p>
            {delta !== null && (
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                {delta > 0 ? (
                  <TrendingUp className="size-3 text-amber-600" />
                ) : (
                  <TrendingDown className="size-3 text-emerald-600" />
                )}
                {Math.abs(delta).toFixed(1)}% {delta > 0 ? "au-dessus" : "en-dessous"} du prix demandé
              </p>
            )}
            <p className="text-xs text-muted-foreground">Modèle <code>price</code></p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function AIAnomalyCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4 text-primary" />
          Détection d&apos;anomalie
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-6 w-28" />
      </CardContent>
    </Card>
  );
}

export async function AIAnomalyCard({ listing }: { listing: Listing }) {
  if (!listing.prix) {
    return (
      <Card className="border-dashed">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="size-4 text-primary" />
            Détection d&apos;anomalie
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          Prix manquant — analyse impossible.
        </CardContent>
      </Card>
    );
  }
  const resp = await scoreAnomaly({ ...listingToPropertyInput(listing), prix: listing.prix });
  const verdict = extractAnomalyVerdict(resp);
  const style = VERDICT_STYLE[verdict.level];

  return (
    <Card className={style.ring}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4 text-primary" />
          Détection d&apos;anomalie
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Badge className={style.badge}>{verdict.label}</Badge>
        {verdict.detail && (
          <p className="text-xs text-muted-foreground">{verdict.detail}</p>
        )}
        <p className="text-xs text-muted-foreground">Modèle <code>anomaly</code></p>
      </CardContent>
    </Card>
  );
}
