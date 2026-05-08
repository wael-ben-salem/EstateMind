"use client";

import { useRef, useState } from "react";
import {
  Upload, FileText, Loader2, AlertTriangle, ShieldCheck,
  ShieldAlert, ShieldX, ChevronDown, ChevronRight, Lightbulb,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";

type Loophole = Record<string, string>;
type Suggestion = Record<string, string>;

interface AnalysisResult {
  status: string;
  file_name: string;
  overall_risk_score: number;
  risk_level: "Low" | "Medium" | "High" | "Critical";
  loopholes: Loophole[];
  errors: Loophole[];
  missing_elements: string[];
  suggestions: Suggestion[];
  summary?: string | null;
  error?: string | null;
}

const RISK_CONFIG = {
  Low: { label: "Risque faible", color: "text-emerald-600", bg: "bg-emerald-500", badge: "bg-emerald-100 text-emerald-700", Icon: ShieldCheck },
  Medium: { label: "Risque modéré", color: "text-amber-600", bg: "bg-amber-500", badge: "bg-amber-100 text-amber-700", Icon: ShieldAlert },
  High: { label: "Risque élevé", color: "text-orange-600", bg: "bg-orange-500", badge: "bg-orange-100 text-orange-700", Icon: ShieldAlert },
  Critical: { label: "Risque critique", color: "text-red-600", bg: "bg-red-500", badge: "bg-red-100 text-red-700", Icon: ShieldX },
};

function Section({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  if (count === 0) return null;
  return (
    <div className="rounded-lg border border-border">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium"
      >
        <span>{title} <span className="ms-1 rounded-full bg-secondary px-2 py-0.5 text-xs font-normal">{count}</span></span>
        {open ? <ChevronDown className="size-4 text-muted-foreground" /> : <ChevronRight className="size-4 text-muted-foreground" />}
      </button>
      {open && <div className="border-t border-border px-4 pb-4 pt-3">{children}</div>}
    </div>
  );
}

function ObjList({ items }: { items: Record<string, string>[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item, i) => (
        <li key={i} className="rounded-md bg-secondary/30 p-3 text-sm">
          {Object.entries(item).map(([k, v]) => (
            <p key={k}><span className="font-medium capitalize">{k.replace(/_/g, " ")}:</span> {v}</p>
          ))}
        </li>
      ))}
    </ul>
  );
}

export function ContractAnalyzer() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch("/api/agents/lawagent/analyze/contract", {
        method: "POST",
        body: fd,
      });
      if (!r.ok) {
        if (r.status === 502) throw new Error("Le service d'analyse est en cours de démarrage, réessayez dans 30 secondes.");
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail ?? err.error ?? `HTTP ${r.status}`);
      }
      const data: AnalysisResult = await r.json();
      if (data.error) throw new Error(data.error);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const cfg = result ? RISK_CONFIG[result.risk_level] ?? RISK_CONFIG.Medium : null;
  const pct = result ? Math.round(result.overall_risk_score * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Analyse de contrat</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Téléchargez un contrat immobilier (PDF) pour détecter les risques juridiques, lacunes et anomalies.
        </p>
      </header>

      {/* Upload */}
      <Card>
        <CardContent className="pt-5">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="grid cursor-pointer place-items-center rounded-lg border-2 border-dashed border-border bg-secondary/20 p-10 text-center transition-colors hover:border-primary/40 hover:bg-secondary/30"
          >
            {file ? (
              <>
                <FileText className="mb-2 size-8 text-primary" />
                <p className="font-medium text-sm">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} Ko · Cliquez pour changer</p>
              </>
            ) : (
              <>
                <Upload className="mb-2 size-8 text-muted-foreground" />
                <p className="text-sm font-medium">Cliquez pour sélectionner un contrat</p>
                <p className="text-xs text-muted-foreground">PDF, PNG, JPEG — max 20 MB</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(null); }}
          />
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={analyze}
              disabled={!file || loading}
              className={buttonVariants({ size: "lg" })}
            >
              {loading ? <Loader2 className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />}
              {loading ? "Analyse en cours…" : "Analyser le contrat"}
            </button>
          </div>
          {loading && (
            <p className="mt-2 text-center text-xs text-muted-foreground">
              L&apos;agent juridique examine le document (~30-60s)…
            </p>
          )}
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && cfg && (
        <div className="space-y-4">
          {/* Score card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <cfg.Icon className={`size-5 ${cfg.color}`} />
                <span>{cfg.label}</span>
                <Badge className={`ms-auto ${cfg.badge} border-0`}>{result.risk_level}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                  <span>Score de risque</span>
                  <span className={cfg.color}>{pct}%</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-secondary">
                  <div
                    className={`h-2.5 rounded-full transition-all ${cfg.bg}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
              {result.summary && (
                <p className="rounded-md bg-secondary/30 p-3 text-sm leading-relaxed">{result.summary}</p>
              )}
            </CardContent>
          </Card>

          {/* Sections */}
          <Section title="Failles juridiques (loopholes)" count={result.loopholes.length}>
            <ObjList items={result.loopholes} />
          </Section>

          <Section title="Erreurs détectées" count={result.errors.length}>
            <ObjList items={result.errors} />
          </Section>

          <Section title="Éléments manquants" count={result.missing_elements.length}>
            <ul className="space-y-1">
              {result.missing_elements.map((m, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="mt-1 size-1.5 shrink-0 rounded-full bg-muted-foreground" />
                  {m}
                </li>
              ))}
            </ul>
          </Section>

          <Section title="Suggestions d'amélioration" count={result.suggestions.length}>
            <ul className="space-y-3">
              {result.suggestions.map((s, i) => (
                <li key={i} className="flex items-start gap-2 rounded-md bg-secondary/30 p-3 text-sm">
                  <Lightbulb className="mt-0.5 size-4 shrink-0 text-primary" />
                  <div>
                    {Object.entries(s).map(([k, v]) => (
                      <p key={k}><span className="font-medium capitalize">{k.replace(/_/g, " ")}:</span> {v}</p>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </Section>

          <p className="text-center text-xs text-muted-foreground">
            Fichier analysé : <strong>{result.file_name}</strong> · Cette analyse est indicative et ne remplace pas un avis juridique professionnel.
          </p>
        </div>
      )}
    </div>
  );
}
