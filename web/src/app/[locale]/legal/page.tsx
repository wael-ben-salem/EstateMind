import { isLocale } from "@/i18n/dictionaries";
import { notFound } from "next/navigation";
import { Scale } from "lucide-react";

export default async function LegalPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <div className="mb-8">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/6 px-4 py-1.5 text-xs font-medium text-primary">
          <Scale className="size-3" />
          Mentions légales
        </div>
        <h1 className="text-4xl font-bold tracking-tight">Mentions légales</h1>
      </div>

      <div className="space-y-4 rounded-2xl border border-border/60 bg-card p-8 text-sm leading-relaxed text-muted-foreground">
        <p>
          <strong className="text-foreground">Outliers</strong> est un projet étudiant à but non commercial développé dans le cadre d&apos;un cours d&apos;intelligence artificielle appliquée.
        </p>
        <p>
          Les données affichées proviennent de sources publiques tunisiennes. Aucune garantie n&apos;est donnée quant à leur exactitude, exhaustivité ou actualité.
        </p>
        <p>
          Les analyses produites par les agents IA (prix prédits, détection d&apos;anomalies, recommandations) sont fournies à titre indicatif uniquement et ne constituent pas des conseils financiers ou juridiques.
        </p>
        <p>
          Les images sont la propriété de leurs auteurs respectifs et restent hébergées chez leurs sources d&apos;origine.
        </p>
      </div>
    </div>
  );
}
