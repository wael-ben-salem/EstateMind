"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Upload,
  Sparkles,
  Loader2,
  X,
  ImagePlus,
  Send,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { buttonVariants } from "@/components/ui/button";

const AMENITIES = [
  ["hasAscenseur", "Ascenseur"],
  ["hasBalcon", "Balcon"],
  ["hasChaffage", "Chauffage"],
  ["hasClimatisation", "Climatisation"],
  ["hasGarage", "Garage"],
  ["hasGardien", "Gardien"],
  ["hasJardin", "Jardin"],
  ["hasParking", "Parking"],
  ["hasPiscine", "Piscine"],
  ["hasTerrasse", "Terrasse"],
] as const;
type AmenityKey = (typeof AMENITIES)[number][0];

const TYPES = ["Appartement", "Villa", "Maison", "Studio", "Duplex", "Terrain", "Local commercial"];
const GOUVERNERATS = [
  "Tunis", "Ariana", "Ben Arous", "Manouba", "Nabeul", "Zaghouan", "Bizerte",
  "Béja", "Jendouba", "Le Kef", "Siliana", "Sousse", "Monastir", "Mahdia",
  "Sfax", "Kairouan", "Kasserine", "Sidi Bouzid", "Gabès", "Médenine",
  "Tataouine", "Gafsa", "Tozeur", "Kébili",
];

const PROGRESS_HINTS = [
  "Téléchargement des photos vers le service IA…",
  "Analyse visuelle des images (BLIP-2 sur GPU)…",
  "Génération de la description française (Llama 3)…",
  "Extraction des caractéristiques structurées…",
];

export function PostWizard({ locale }: { locale: string }) {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressIdx, setProgressIdx] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form fields
  const [titre, setTitre] = useState("");
  const [description, setDescription] = useState("");
  const [prix, setPrix] = useState("");
  const [contrat, setContrat] = useState<"vente" | "location">("vente");
  const [type, setType] = useState("Appartement");
  const [gouvernerat, setGouvernerat] = useState("Tunis");
  const [ville, setVille] = useState("");
  const [adresse, setAdresse] = useState("");
  const [surface, setSurface] = useState("");
  const [pieces, setPieces] = useState("");
  const [etage, setEtage] = useState("");
  const [tel, setTel] = useState("");
  const [amenities, setAmenities] = useState<Record<AmenityKey, boolean>>(
    Object.fromEntries(AMENITIES.map(([k]) => [k, false])) as Record<AmenityKey, boolean>
  );

  // Cycle progress hints + count elapsed seconds while analyzing
  useEffect(() => {
    if (!analyzing) return;
    setProgressIdx(0);
    setElapsed(0);
    const tick = setInterval(() => setElapsed((s) => s + 1), 1000);
    const cycle = setInterval(() => setProgressIdx((i) => (i + 1) % PROGRESS_HINTS.length), 25000);
    return () => {
      clearInterval(tick);
      clearInterval(cycle);
    };
  }, [analyzing]);

  // Revoke object URLs when files change
  useEffect(() => () => previews.forEach(URL.revokeObjectURL), [previews]);

  function pickFiles(picked: FileList | null) {
    if (!picked) return;
    const arr = Array.from(picked).slice(0, 10);
    setFiles(arr);
    setPreviews(arr.map((f) => URL.createObjectURL(f)));
    setAnalyzed(false);
  }

  function removeFile(i: number) {
    const next = files.filter((_, j) => j !== i);
    setFiles(next);
    URL.revokeObjectURL(previews[i]);
    setPreviews(previews.filter((_, j) => j !== i));
    setAnalyzed(false);
  }

  async function analyze() {
    if (!files.length) return;
    setAnalyzing(true);
    setError(null);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      const r = await fetch("/api/agents/captioner/caption-listing", {
        method: "POST",
        body: fd,
      });
      if (!r.ok) {
        if (r.status === 502 || r.status === 503)
          throw new Error("Le service de description IA est en cours de démarrage, réessayez dans 30 secondes.");
        if (r.status === 504)
          throw new Error("L'analyse a pris trop longtemps. Réessayez avec moins de photos (1-3 recommandé) ou patientez quelques instants.");
        throw new Error(`Captioner HTTP ${r.status}`);
      }
      const data = await r.json();

      if (data.description_fr && !description) setDescription(data.description_fr);
      const f = data.fields ?? {};
      if (f.type) setType(f.type);
      if (f.pieces_min && !pieces) setPieces(String(f.pieces_min));
      // Amenities from captioner
      const newAmen = { ...amenities };
      for (const [key] of AMENITIES) {
        const k = key.replace(/^has/, "has_").replace(/([A-Z])/g, "_$1").toLowerCase().replace("has__", "has_");
        if (f[k] === true || f[k] === 1) newAmen[key] = true;
      }
      // Direct mapping for common ones
      if (f.has_piscine) newAmen.hasPiscine = true;
      if (f.has_jardin) newAmen.hasJardin = true;
      if (f.has_balcon) newAmen.hasBalcon = true;
      if (f.has_terrasse) newAmen.hasTerrasse = true;
      if (f.has_climatisation) newAmen.hasClimatisation = true;
      if (f.has_parking) newAmen.hasParking = true;
      if (f.has_garage) newAmen.hasGarage = true;
      setAmenities(newAmen);

      setAnalyzed(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAnalyzing(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!files.length) {
      setError("Ajoutez au moins une photo.");
      return;
    }
    if (!titre || !type || !contrat || !gouvernerat) {
      setError("Titre, type, contrat et gouvernorat sont obligatoires.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      // 1. Upload photos
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      const upR = await fetch("/api/uploads", { method: "POST", body: fd });
      if (!upR.ok) {
        const err = await upR.json().catch(() => ({}));
        throw new Error(err.error ?? `Upload échoué (${upR.status})`);
      }
      const { urls } = await upR.json();

      // 2. Create listing
      const body = {
        titre,
        description: description || undefined,
        prix: prix ? Number(prix) : null,
        contrat,
        type,
        gouvernerat,
        ville: ville || null,
        adresse: adresse || null,
        surface: surface ? Number(surface) : null,
        pieces: pieces ? Number(pieces) : null,
        etage: etage ? Number(etage) : null,
        tel: tel || null,
        ...amenities,
        images: urls,
      };
      const r = await fetch("/api/listings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error ?? `Création échouée (${r.status})`);
      }
      const { id } = await r.json();
      router.push(`/${locale}/listings/${id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Publier une annonce</h1>
        <p className="text-sm text-muted-foreground">
          Téléchargez vos photos, l&apos;IA pré-remplit la description et les caractéristiques. Vous pouvez tout éditer avant publication.
        </p>
      </header>

      {/* Step 1: Photos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <span className="grid size-6 place-items-center rounded-full bg-primary text-primary-foreground text-xs">1</span>
            Photos ({files.length}/10)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="grid cursor-pointer place-items-center rounded-lg border-2 border-dashed border-border bg-secondary/20 p-8 text-center transition-colors hover:border-primary/40 hover:bg-secondary/40"
          >
            <Upload className="mb-2 size-6 text-muted-foreground" />
            <p className="text-sm font-medium">Cliquez pour ajouter des photos</p>
            <p className="text-xs text-muted-foreground">JPG, PNG, WebP — max 10 MB par photo, 10 photos</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp,image/avif"
              className="hidden"
              onChange={(e) => pickFiles(e.target.files)}
            />
          </div>

          {previews.length > 0 && (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
              {previews.map((url, i) => (
                <div key={i} className="group relative aspect-square overflow-hidden rounded-md bg-muted">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt={`photo ${i + 1}`} className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeFile(i)}
                    className="absolute right-1 top-1 rounded-full bg-background/80 p-0.5 opacity-0 transition-opacity group-hover:opacity-100"
                    aria-label="Supprimer"
                  >
                    <X className="size-3" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="grid aspect-square place-items-center rounded-md border-2 border-dashed border-border text-muted-foreground hover:border-primary/40 hover:text-primary"
              >
                <ImagePlus className="size-5" />
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 2: AI analysis */}
      {files.length > 0 && (
        <Card className={analyzed ? "border-emerald-500/30 bg-emerald-500/5" : ""}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <span className="grid size-6 place-items-center rounded-full bg-primary text-primary-foreground text-xs">2</span>
              <Sparkles className="size-4 text-primary" />
              Analyse IA
              {analyzed && <Badge className="ms-1 bg-emerald-600 text-white">Terminé</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!analyzing && !analyzed && (
              <>
                <p className="text-sm text-muted-foreground">
                  L&apos;agent <code>captioner</code> va analyser vos photos pour pré-remplir la description et les équipements.
                  {" "}
                  <strong>Compter ~2-3 minutes</strong> (le modèle BLIP-2 tourne sur GPU local).
                </p>
                <button
                  type="button"
                  onClick={analyze}
                  className={buttonVariants()}
                >
                  <Sparkles className="size-4" />
                  Analyser avec l&apos;IA
                </button>
                <p className="text-xs text-muted-foreground">Étape facultative — vous pouvez aussi remplir le formulaire à la main.</p>
              </>
            )}
            {analyzing && (
              <div className="rounded-md border border-border bg-card p-4">
                <div className="flex items-center gap-3">
                  <Loader2 className="size-5 animate-spin text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{PROGRESS_HINTS[progressIdx]}</p>
                    <p className="text-xs text-muted-foreground">{elapsed}s écoulées · première inférence ~2-3 min</p>
                  </div>
                </div>
              </div>
            )}
            {analyzed && !analyzing && (
              <div className="flex items-start gap-2 text-sm text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                <p>Description et équipements pré-remplis ci-dessous. Vérifiez et ajustez.</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 3: Form */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <span className="grid size-6 place-items-center rounded-full bg-primary text-primary-foreground text-xs">3</span>
            Détails de l&apos;annonce
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="titre">Titre *</Label>
            <Input id="titre" value={titre} onChange={(e) => setTitre(e.target.value)} required placeholder="Ex: Appartement S+2 vue mer Hammamet" />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Contrat *</Label>
              <div className="mt-1 flex gap-2">
                {(["vente", "location"] as const).map((c) => (
                  <button
                    type="button"
                    key={c}
                    onClick={() => setContrat(c)}
                    className={`${buttonVariants({ variant: contrat === c ? "default" : "outline", size: "sm" })} flex-1 capitalize`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="prix">Prix (TND) {contrat === "location" && <span className="text-xs text-muted-foreground">/ mois</span>}</Label>
              <Input id="prix" type="number" min="0" value={prix} onChange={(e) => setPrix(e.target.value)} />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="type">Type *</Label>
              <select id="type" value={type} onChange={(e) => setType(e.target.value)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-2 text-sm">
                {TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <Label htmlFor="gouv">Gouvernorat *</Label>
              <select id="gouv" value={gouvernerat} onChange={(e) => setGouvernerat(e.target.value)} className="mt-1 w-full rounded-md border border-input bg-background px-2 py-2 text-sm">
                {GOUVERNERATS.map((g) => <option key={g}>{g}</option>)}
              </select>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="ville">Ville</Label>
              <Input id="ville" value={ville} onChange={(e) => setVille(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="adresse">Adresse</Label>
              <Input id="adresse" value={adresse} onChange={(e) => setAdresse(e.target.value)} />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <Label htmlFor="surface">Surface (m²)</Label>
              <Input id="surface" type="number" min="0" value={surface} onChange={(e) => setSurface(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="pieces">Pièces</Label>
              <Input id="pieces" type="number" min="0" value={pieces} onChange={(e) => setPieces(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="etage">Étage</Label>
              <Input id="etage" type="number" value={etage} onChange={(e) => setEtage(e.target.value)} />
            </div>
          </div>

          <div>
            <Label htmlFor="tel">Téléphone</Label>
            <Input id="tel" type="tel" value={tel} onChange={(e) => setTel(e.target.value)} placeholder="+216 …" />
          </div>

          <Separator />

          <div>
            <Label>Équipements</Label>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
              {AMENITIES.map(([k, label]) => (
                <label key={k} className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm hover:bg-secondary/30">
                  <input
                    type="checkbox"
                    checked={amenities[k]}
                    onChange={(e) => setAmenities({ ...amenities, [k]: e.target.checked })}
                    className="accent-primary"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              placeholder="Décrivez votre bien…"
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
            />
            {analyzed && (
              <p className="mt-1 text-xs text-muted-foreground">
                <Sparkles className="me-1 inline size-3 text-primary" />
                Pré-rempli par l&apos;IA — éditez librement.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-end gap-2">
        <button type="submit" disabled={submitting || !files.length} className={buttonVariants({ size: "lg" })}>
          {submitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Publier l&apos;annonce
        </button>
      </div>
    </form>
  );
}
