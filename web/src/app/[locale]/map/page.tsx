import { Map as MapIcon, Database } from "lucide-react";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { Card, CardContent } from "@/components/ui/card";

type Manifest = {
  manifest?: {
    dataset_rows?: number;
    train_rows?: number;
    test_rows?: number;
    metrics?: {
      ridge_mae?: number;
      lgbm_mae?: number;
      arena_best_model?: string;
      stack_mae?: number;
      stack_r2?: number;
      lgbm_rmse?: number;
      lgbm_mape_pct?: number;
    };
  };
  metadata?: { estimator?: string; embeddings_model?: string };
};

async function fetchManifest(): Promise<Manifest | null> {
  const base = process.env.AGENT_ESTATEMIND_URL;
  if (!base) return null;
  try {
    const r = await fetch(`${base}/manifest`, {
      cache: "no-store",
    });
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

export default async function MapPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const manifest = await fetchManifest();
  const m = manifest?.manifest?.metrics;
  const rows = manifest?.manifest?.dataset_rows;
  const best = m?.arena_best_model;

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
          <MapIcon className="size-3 text-primary" /> Agent outliers
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Carte des prix immobiliers en Tunisie</h1>
        <p className="max-w-2xl text-muted-foreground">
          Heatmap interactive générée à partir de l&apos;analyse de {rows?.toLocaleString("fr-TN") ?? "—"} annonces.
          Les zones chaudes indiquent les prix les plus élevés au m².
        </p>
      </header>

      {m && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Lignes dataset" value={rows?.toLocaleString("fr-TN") ?? "—"} />
          <Stat label="Meilleur modèle" value={best ?? "—"} />
          <Stat label="MAPE LightGBM" value={m.lgbm_mape_pct != null ? `${m.lgbm_mape_pct.toFixed(1)}%` : "—"} />
          <Stat label="MAE LightGBM" value={m.lgbm_mae != null ? `${(m.lgbm_mae / 1000).toFixed(1)}k TND` : "—"} />
        </div>
      )}

      <Card className="overflow-hidden p-0">
        <iframe
          src="/api/agents/outliers/map"
          title="Carte des prix immobiliers en Tunisie"
          className="block h-[680px] w-full border-0"
          loading="lazy"
        />
      </Card>

      <p className="text-xs text-muted-foreground">
        <Database className="me-1 inline size-3" />
        Source : agent <code>outliers</code> · Folium HTML servi via{" "}
        <code>/api/agents/outliers/map</code>.
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="px-4 py-3">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
        <div className="mt-1 text-lg font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}
