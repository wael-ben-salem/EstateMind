import { isLocale } from "@/i18n/dictionaries";
import { notFound } from "next/navigation";
import { Sparkles, Brain, FileSearch, TrendingUp, AlertTriangle, MessageSquare, Map } from "lucide-react";

const AGENTS = [
  {
    icon: <Sparkles className="size-4" />,
    color: "text-pink-500 bg-pink-500/10",
    name: "Captioner",
    desc: "Génère des descriptions professionnelles à partir des photos (BLIP-2 + Llama).",
  },
  {
    icon: <Map className="size-4" />,
    color: "text-violet-500 bg-violet-500/10",
    name: "Outliers",
    desc: "Détection de zones sous-évaluées, comparables marché, scoring POI.",
  },
  {
    icon: <FileSearch className="size-4" />,
    color: "text-blue-500 bg-blue-500/10",
    name: "Law Agent",
    desc: "Q&A juridique tunisien et analyse de contrats immobiliers (Qdrant + Cohere).",
  },
  {
    icon: <TrendingUp className="size-4" />,
    color: "text-emerald-500 bg-emerald-500/10",
    name: "Price",
    desc: "Prédiction de prix au m² (LightGBM + Gradient Boosting + log-transform).",
  },
  {
    icon: <AlertTriangle className="size-4" />,
    color: "text-amber-500 bg-amber-500/10",
    name: "Anomaly",
    desc: "Détection d'annonces suspectes, surévaluées ou frauduleuses.",
  },
  {
    icon: <MessageSquare className="size-4" />,
    color: "text-cyan-500 bg-cyan-500/10",
    name: "Recommender",
    desc: "Recherche en langage naturel français — interprète l'intention et filtre les annonces.",
  },
];

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">

      {/* Header */}
      <div className="mb-12">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/6 px-4 py-1.5 text-xs font-medium text-primary">
          <Brain className="size-3" />
          Projet académique
        </div>
        <h1 className="text-4xl font-bold tracking-tight">À propos d&apos;Outliers</h1>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          Outliers est une plateforme immobilière pour le marché tunisien, augmentée par 6 agents d&apos;intelligence artificielle spécialisés.
        </p>
      </div>

      {/* Agents grid */}
      <div className="mb-12">
        <h2 className="mb-6 text-lg font-semibold">Les 6 agents IA</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {AGENTS.map((a) => (
            <div
              key={a.name}
              className="flex gap-3.5 rounded-2xl border border-border/60 bg-card p-4 transition-all hover:border-primary/25 hover:shadow-md hover:shadow-primary/5"
            >
              <div className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg ${a.color}`}>
                {a.icon}
              </div>
              <div>
                <p className="font-semibold">{a.name}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{a.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer note */}
      <p className="rounded-2xl border border-border/50 bg-muted/40 px-5 py-4 text-sm text-muted-foreground">
        Projet académique — données issues du marché public tunisien. Toutes les analyses sont produites automatiquement par les modèles et ne constituent pas des conseils financiers.
      </p>
    </div>
  );
}
