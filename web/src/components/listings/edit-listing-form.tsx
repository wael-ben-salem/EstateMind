"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, Loader2, X, ImagePlus, Save, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { buttonVariants } from "@/components/ui/button";
import type { Listing } from "@/generated/prisma";

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

export function EditListingForm({ listing, locale }: { listing: Listing; locale: string }) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const existingUrls = listing.images
    ? listing.images.split(" | ").map((s) => s.trim()).filter(Boolean)
    : [];

  const [keptUrls, setKeptUrls] = useState<string[]>(existingUrls);
  const [newFiles, setNewFiles] = useState<File[]>([]);
  const [newPreviews, setNewPreviews] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [titre, setTitre] = useState(listing.titre ?? "");
  const [description, setDescription] = useState(listing.description ?? "");
  const [prix, setPrix] = useState(listing.prix != null ? String(listing.prix) : "");
  const [contrat, setContrat] = useState<"vente" | "location">(
    listing.contrat === "location" ? "location" : "vente"
  );
  const [type, setType] = useState(listing.type ?? "Appartement");
  const [gouvernerat, setGouvernerat] = useState(listing.gouvernerat ?? "Tunis");
  const [ville, setVille] = useState(listing.ville ?? "");
  const [adresse, setAdresse] = useState(listing.adresse ?? "");
  const [surface, setSurface] = useState(listing.surface != null ? String(listing.surface) : "");
  const [pieces, setPieces] = useState(listing.pieces != null ? String(listing.pieces) : "");
  const [etage, setEtage] = useState(listing.etage != null ? String(listing.etage) : "");
  const [tel, setTel] = useState(listing.tel ?? "");
  const [amenities, setAmenities] = useState<Record<AmenityKey, boolean>>(
    Object.fromEntries(
      AMENITIES.map(([k]) => [k, Boolean((listing as Record<string, unknown>)[k])])
    ) as Record<AmenityKey, boolean>
  );

  function pickFiles(picked: FileList | null) {
    if (!picked) return;
    const arr = Array.from(picked).slice(0, 10 - keptUrls.length);
    setNewFiles((prev) => [...prev, ...arr].slice(0, 10 - keptUrls.length));
    setNewPreviews((prev) => [...prev, ...arr.map((f) => URL.createObjectURL(f))]);
  }

  function removeKept(i: number) {
    setKeptUrls((prev) => prev.filter((_, j) => j !== i));
  }

  function removeNew(i: number) {
    URL.revokeObjectURL(newPreviews[i]);
    setNewFiles((prev) => prev.filter((_, j) => j !== i));
    setNewPreviews((prev) => prev.filter((_, j) => j !== i));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (keptUrls.length + newFiles.length === 0) {
      setError("Conservez ou ajoutez au moins une photo.");
      return;
    }
    if (!titre || !type || !contrat || !gouvernerat) {
      setError("Titre, type, contrat et gouvernorat sont obligatoires.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      let uploadedUrls: string[] = [];
      if (newFiles.length > 0) {
        const fd = new FormData();
        newFiles.forEach((f) => fd.append("files", f));
        const upR = await fetch("/api/uploads", { method: "POST", body: fd });
        if (!upR.ok) {
          const err = await upR.json().catch(() => ({}));
          throw new Error(err.error ?? `Upload échoué (${upR.status})`);
        }
        const { urls } = await upR.json();
        uploadedUrls = urls;
      }

      const body = {
        titre,
        description: description || null,
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
        images: [...keptUrls, ...uploadedUrls],
      };
      const r = await fetch(`/api/listings/${listing.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error ?? `Mise à jour échouée (${r.status})`);
      }
      router.push(`/${locale}/listings/${listing.id}`);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSubmitting(false);
    }
  }

  const totalPhotos = keptUrls.length + newFiles.length;

  return (
    <form onSubmit={submit} className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Modifier l&apos;annonce</h1>
        <p className="text-sm text-muted-foreground">Modifiez les informations et enregistrez.</p>
      </header>

      {/* Photos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Photos ({totalPhotos}/10)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {(keptUrls.length > 0 || newPreviews.length > 0) && (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
              {keptUrls.map((url, i) => (
                <div key={`kept-${i}`} className="group relative aspect-square overflow-hidden rounded-md bg-muted">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt="" className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeKept(i)}
                    className="absolute right-1 top-1 rounded-full bg-background/80 p-0.5 opacity-0 transition-opacity group-hover:opacity-100"
                    aria-label="Supprimer"
                  >
                    <X className="size-3" />
                  </button>
                </div>
              ))}
              {newPreviews.map((url, i) => (
                <div key={`new-${i}`} className="group relative aspect-square overflow-hidden rounded-md bg-muted ring-2 ring-primary/40">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt="" className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeNew(i)}
                    className="absolute right-1 top-1 rounded-full bg-background/80 p-0.5 opacity-0 transition-opacity group-hover:opacity-100"
                    aria-label="Supprimer"
                  >
                    <X className="size-3" />
                  </button>
                </div>
              ))}
              {totalPhotos < 10 && (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="grid aspect-square place-items-center rounded-md border-2 border-dashed border-border text-muted-foreground hover:border-primary/40 hover:text-primary"
                >
                  <ImagePlus className="size-5" />
                </button>
              )}
            </div>
          )}
          {totalPhotos === 0 && (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="grid cursor-pointer place-items-center rounded-lg border-2 border-dashed border-border bg-secondary/20 p-8 text-center transition-colors hover:border-primary/40"
            >
              <Upload className="mb-2 size-6 text-muted-foreground" />
              <p className="text-sm font-medium">Ajouter des photos</p>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp,image/avif"
            className="hidden"
            onChange={(e) => pickFiles(e.target.files)}
          />
        </CardContent>
      </Card>

      {/* Details */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Détails</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="titre">Titre *</Label>
            <Input id="titre" value={titre} onChange={(e) => setTitre(e.target.value)} required />
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
              <Label htmlFor="prix">Prix (TND)</Label>
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
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
            />
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
        <button
          type="button"
          onClick={() => router.back()}
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          Annuler
        </button>
        <button type="submit" disabled={submitting} className={buttonVariants({ size: "lg" })}>
          {submitting ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
          Enregistrer
        </button>
      </div>
    </form>
  );
}
