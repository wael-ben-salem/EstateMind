"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Camera, Loader2, CheckCircle2, Upload, X } from "lucide-react";
import { useLang } from "@/contexts/lang";
import { LangSwitcher } from "@/components/lang-switcher";
import { NavbarMinimal } from "@/components/navbar";

const TYPES    = ["Appartement","Villa","Maison","Terrain","Bureau","Local commercial","Studio","Ferme"];
const CONTRATS = ["Vente","Location","Location saisonnière"];
const GOVS     = ["Tunis","Ariana","Ben Arous","Manouba","Nabeul","Sousse","Sfax","Monastir","Mahdia","Bizerte","Béja","Jendouba","Siliana","Kef","Kairouan","Kasserine","Sidi Bouzid","Gafsa","Tozeur","Kébili","Gabès","Médenine","Tataouine","Zaghouan"];

interface Fields {
  titre: string; type: string; contrat: string; gouvernerat: string; ville: string; adresse: string;
  surface: string; pieces: string; prix: string; description: string; tel: string;
  hasBalcon: boolean; hasParking: boolean; hasJardin: boolean; hasPiscine: boolean;
  hasTerrasse: boolean; hasGarage: boolean; hasClimatisation: boolean; hasAscenseur: boolean;
  images: string;
}

const EMPTY: Fields = {
  titre: "", type: "", contrat: "Vente", gouvernerat: "", ville: "", adresse: "",
  surface: "", pieces: "", prix: "", description: "", tel: "",
  hasBalcon: false, hasParking: false, hasJardin: false, hasPiscine: false,
  hasTerrasse: false, hasGarage: false, hasClimatisation: false, hasAscenseur: false,
  images: "",
};

const AMENITY_LABELS: [keyof Fields, string, string, string][] = [
  ["hasBalcon",        "Balcon",     "شرفة",  "Balcony"],
  ["hasParking",       "Parking",    "موقف",  "Parking"],
  ["hasJardin",        "Jardin",     "حديقة", "Garden"],
  ["hasPiscine",       "Piscine",    "مسبح",  "Pool"],
  ["hasTerrasse",      "Terrasse",   "تراس",  "Terrace"],
  ["hasGarage",        "Garage",     "مرآب",  "Garage"],
  ["hasClimatisation", "Clim.",      "تكييف", "A/C"],
  ["hasAscenseur",     "Ascenseur",  "مصعد",  "Elevator"],
];

export default function PostPage() {
  const router = useRouter();
  const { t, locale } = useLang();
  const [step, setStep] = useState(0);
  const [fields, setFields] = useState<Fields>(EMPTY);
  const [captioning, setCaptioning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const set = (k: keyof Fields, v: string | boolean) => setFields(f => ({ ...f, [k]: v }));
  const amenityLabel = ([, fr, ar, en]: typeof AMENITY_LABELS[number]) =>
    locale === "ar" ? ar : locale === "en" ? en : fr;

  /* ─── AI Captioner ─── */
  async function runCaptioner(file: File) {
    setCaptioning(true);
    try {
      const fd = new FormData();
      fd.append("files", file); // Python: files: list[UploadFile]
      const res = await fetch("/api/agents/captioner/caption-listing", { method: "POST", body: fd });
      if (!res.ok) return;
      const data = await res.json();

      const f       = data.fields || {};
      const type    = (f.type || "").trim();
      const pieces  = f.pieces_min ? String(f.pieces_min) : "";
      const topo    = (f.topology_hint || "").trim();

      // Always start from description_fr (LLM-humanized prose), then translate if needed
      const baseFr = (data.description_fr || data.description_en_text || "").trim();
      let desc = baseFr;
      if (baseFr && locale !== "fr") {
        const target = locale === "ar" ? "ar" : "en";
        try {
          const tr = await fetch("/api/translate", {
            method: "POST",
            body: JSON.stringify({ texts: [baseFr], target }),
          });
          const { translations } = await tr.json() as { translations: string[] };
          desc = translations?.[0]?.trim() || baseFr;
        } catch { /* keep French */ }
      }

      setFields(prev => {
        // Auto-generate a title if none yet
        let autoTitle = prev.titre;
        if (!autoTitle && type) {
          const loc = prev.ville || prev.gouvernerat || "";
          autoTitle = [type, topo, loc ? `à ${loc}` : ""].filter(Boolean).join(" ");
        }
        return {
          ...prev,
          titre:            autoTitle,
          description:      prev.description || desc,
          type:             prev.type        || type,
          pieces:           prev.pieces      || pieces,
          hasBalcon:        prev.hasBalcon        || !!f.has_balcon,
          hasParking:       prev.hasParking       || !!f.has_parking,
          hasJardin:        prev.hasJardin        || !!f.has_jardin,
          hasPiscine:       prev.hasPiscine       || !!f.has_piscine,
          hasTerrasse:      prev.hasTerrasse      || !!f.has_terrasse,
          hasGarage:        prev.hasGarage        || !!f.has_garage,
          hasClimatisation: prev.hasClimatisation || !!f.has_climatisation,
          hasAscenseur:     prev.hasAscenseur     || !!f.has_ascenseur,
        };
      });
    } catch { /* ignore captioner errors silently */ }
    finally { setCaptioning(false); }
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    // Add blob URLs for all selected files
    const urls = files.map(f => URL.createObjectURL(f));
    setFields(f => ({ ...f, images: [...(f.images ? f.images.split(" | ") : []), ...urls].join(" | ") }));
    // Run AI captioner only on the first new file
    if (!captioning) runCaptioner(files[0]);
    // Reset input so same files can be re-selected
    e.target.value = "";
  }

  /* ─── Upload blobs → real server URLs ─── */
  async function uploadImages(): Promise<string> {
    const urls = fields.images ? fields.images.split(" | ").filter(Boolean) : [];
    if (!urls.length) return "";
    const real: string[] = [];
    for (const url of urls) {
      if (!url.startsWith("blob:")) { real.push(url); continue; }
      try {
        const blob = await fetch(url).then(r => r.blob());
        const fd = new FormData();
        fd.append("file", blob, "photo.jpg");
        const res = await fetch("/api/upload", { method: "POST", body: fd });
        const data = await res.json() as { url?: string };
        if (data.url) real.push(data.url);
      } catch { /* skip failed uploads */ }
    }
    return real.join(" | ");
  }

  /* ─── Submit ─── */
  async function publish() {
    setSubmitting(true);
    setError("");
    try {
      const images = await uploadImages();
      const body: Record<string, unknown> = {
        titre:       fields.titre,
        type:        fields.type || undefined,
        contrat:     fields.contrat || undefined,
        gouvernerat: fields.gouvernerat || undefined,
        ville:       fields.ville || undefined,
        adresse:     fields.adresse || undefined,
        surface:     fields.surface ? parseFloat(fields.surface) : undefined,
        pieces:      fields.pieces ? parseInt(fields.pieces, 10) : undefined,
        prix:        fields.prix ? parseFloat(fields.prix) : undefined,
        description: fields.description || undefined,
        tel:         fields.tel || undefined,
        images:      images || undefined,
        hasBalcon: fields.hasBalcon, hasParking: fields.hasParking, hasJardin: fields.hasJardin,
        hasPiscine: fields.hasPiscine, hasTerrasse: fields.hasTerrasse, hasGarage: fields.hasGarage,
        hasClimatisation: fields.hasClimatisation, hasAscenseur: fields.hasAscenseur,
      };
      const res = await fetch("/api/listings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? t.post.error_generic); setSubmitting(false); return; }
      router.push(`/listings/${data.id}`);
    } catch {
      setError(t.post.error_unavailable);
      setSubmitting(false);
    }
  }

  const inputCls = "w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white";
  const inputStyle = { borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)" };
  const labelCls = "block text-sm font-medium mb-1.5";
  const steps = t.post.steps;

  return (
    <div className="min-h-screen" style={{ background: "var(--color-cream)" }}>
      <NavbarMinimal rightLabel={t.post.my_account} rightHref="/me" />

      {/* Page hero */}
      <div className="px-4 sm:px-6 py-7"
           style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}>
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: "var(--font-display)" }}>{t.post.title}</h1>
          <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.5)" }}>{t.post.subtitle}</p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">

        {/* Step indicators */}
        <div className="flex items-center gap-0 mb-10">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center flex-1 last:flex-none">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
                     style={i < step
                       ? { background: "var(--color-gold)", color: "var(--color-navy)" }
                       : i === step
                       ? { background: "var(--color-navy)", color: "white" }
                       : { background: "oklch(0.18 0.065 260 / 0.1)", color: "var(--color-navy)", opacity: 0.4 }}>
                  {i < step ? <CheckCircle2 size={16} /> : i + 1}
                </div>
                <span className="text-xs font-medium hidden sm:block"
                      style={{ color: "var(--color-navy)", opacity: i === step ? 1 : 0.4 }}>{s}</span>
              </div>
              {i < steps.length - 1 && (
                <div className="flex-1 h-px mx-3" style={{ background: i < step ? "var(--color-gold)" : "oklch(0.18 0.065 260 / 0.15)" }} />
              )}
            </div>
          ))}
        </div>

        {/* Step 0 — Location & Type */}
        {step === 0 && (
          <div className="rounded-2xl bg-white border border-navy/8 p-8 shadow-sm space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.property_type}</label>
                <select value={fields.type} onChange={e => set("type", e.target.value)} className={inputCls} style={inputStyle}>
                  <option value="">{t.post.choose}</option>
                  {TYPES.map(tp => <option key={tp}>{tp}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.contract}</label>
                <select value={fields.contrat} onChange={e => set("contrat", e.target.value)} className={inputCls} style={inputStyle}>
                  {CONTRATS.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.governorate}</label>
                <select value={fields.gouvernerat} onChange={e => set("gouvernerat", e.target.value)} className={inputCls} style={inputStyle}>
                  <option value="">{t.post.choose}</option>
                  {GOVS.map(g => <option key={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.city}</label>
                <input value={fields.ville} onChange={e => set("ville", e.target.value)} placeholder={t.post.city_placeholder} className={inputCls} style={inputStyle} />
              </div>
            </div>
            <div>
              <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.address}</label>
              <input value={fields.adresse} onChange={e => set("adresse", e.target.value)} placeholder={t.post.address_placeholder} className={inputCls} style={inputStyle} />
            </div>
            <div>
              <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.phone}</label>
              <input type="tel" value={fields.tel} onChange={e => set("tel", e.target.value)} placeholder="+216 XX XXX XXX" className={inputCls} style={inputStyle} />
            </div>
          </div>
        )}

        {/* Step 1 — Photos & AI */}
        {step === 1 && (
          <div className="rounded-2xl bg-white border border-navy/8 p-8 shadow-sm space-y-6">

            {/* Thumbnails grid */}
            {fields.images && (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                {fields.images.split(" | ").map((url, i) => (
                  <div key={i} className="relative rounded-xl overflow-hidden border border-navy/10"
                       style={{ aspectRatio: "4/3" }}>
                    <img src={url} alt="" className="w-full h-full object-cover" />
                    {i === 0 && (
                      <span className="absolute bottom-1 left-1 text-[10px] font-bold px-1.5 py-0.5 rounded-md"
                            style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                        {locale === "ar" ? "رئيسية" : locale === "en" ? "Main" : "Principale"}
                      </span>
                    )}
                    <button onClick={() => setFields(f => ({ ...f, images: f.images.split(" | ").filter((_, j) => j !== i).join(" | ") }))}
                            className="absolute top-1 right-1 w-6 h-6 rounded-full flex items-center justify-center shadow-md"
                            style={{ background: "oklch(0.18 0.065 260 / 0.75)", color: "white" }}>
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Upload zone — always visible */}
            <label className="flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-2xl p-8 cursor-pointer transition-colors"
                   style={{ borderColor: captioning ? "var(--color-gold)" : "oklch(0.18 0.065 260 / 0.2)" }}>
              {captioning
                ? <Loader2 size={28} className="animate-spin" style={{ color: "var(--color-gold)" }} />
                : <Upload size={28} style={{ color: "var(--color-gold)" }} />}
              <span className="text-sm font-medium" style={{ color: "var(--color-navy)" }}>
                {captioning ? t.post.ai_analyzing : fields.images ? (locale === "ar" ? "إضافة المزيد من الصور" : locale === "en" ? "Add more photos" : "Ajouter d'autres photos") : t.post.upload}
              </span>
              <span className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{t.post.upload_hint}</span>
              <input type="file" accept="image/*" multiple className="hidden" onChange={onFileChange} />
            </label>

            {captioning && (
              <div className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ background: "oklch(0.77 0.18 68 / 0.1)" }}>
                <Loader2 size={16} className="animate-spin" style={{ color: "var(--color-gold)" }} />
                <span className="text-sm" style={{ color: "var(--color-navy)" }}>{t.post.ai_caption}</span>
              </div>
            )}

            <div className="rounded-xl p-4 border border-navy/10 bg-sand/50 space-y-3">
              <div className="flex items-center gap-2">
                <Camera size={14} style={{ color: "var(--color-gold)" }} />
                <span className="text-xs font-semibold" style={{ color: "var(--color-navy)" }}>{t.post.ai_review}</span>
              </div>
              {/* Editable fields */}
              <div className="grid grid-cols-3 gap-3">
                {([["type", t.post.ai_type, fields.type], ["pieces", t.post.ai_rooms, fields.pieces], ["surface", t.post.ai_surface, fields.surface]] as [keyof Fields, string, string][]).map(([k, label, val]) => (
                  <div key={k}>
                    <p className="text-xs mb-1" style={{ color: "var(--color-navy)", opacity: 0.5 }}>{label}</p>
                    <input value={val} onChange={e => set(k, e.target.value)} className="w-full px-3 py-2 rounded-lg border text-xs outline-none bg-white" style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)" }} />
                  </div>
                ))}
              </div>
              {/* Detected amenities */}
              {AMENITY_LABELS.some(([k]) => fields[k]) && (
                <div>
                  <p className="text-xs mb-2" style={{ color: "var(--color-navy)", opacity: 0.5 }}>
                    {locale === "ar" ? "مرافق مكتشفة" : locale === "en" ? "Detected amenities" : "Équipements détectés"}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {AMENITY_LABELS.filter(([k]) => fields[k]).map(entry => (
                      <span key={entry[0]} className="px-2.5 py-1 rounded-lg text-xs font-medium"
                            style={{ background: "var(--color-gold)", color: "var(--color-navy)" }}>
                        {amenityLabel(entry)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 2 — Description & Price */}
        {step === 2 && (
          <div className="rounded-2xl bg-white border border-navy/8 p-8 shadow-sm space-y-5">
            <div>
              <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.listing_title}</label>
              <input value={fields.titre} onChange={e => set("titre", e.target.value)} placeholder={t.post.title_placeholder} className={inputCls} style={inputStyle} />
            </div>
            <div>
              <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.description}</label>
              <textarea value={fields.description} onChange={e => set("description", e.target.value)}
                        placeholder={t.post.desc_placeholder} rows={6}
                        className={inputCls + " resize-none"} style={inputStyle} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.price}</label>
                <input type="number" value={fields.prix} onChange={e => set("prix", e.target.value)} placeholder="350000" className={inputCls} style={inputStyle} />
              </div>
              <div>
                <label className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.surface}</label>
                <input type="number" value={fields.surface} onChange={e => set("surface", e.target.value)} placeholder="120" className={inputCls} style={inputStyle} />
              </div>
            </div>
            <div>
              <p className={labelCls} style={{ color: "var(--color-navy)" }}>{t.post.amenities}</p>
              <div className="grid grid-cols-4 gap-3">
                {AMENITY_LABELS.map(entry => {
                  const [k] = entry;
                  const label = amenityLabel(entry);
                  return (
                    <button key={k} type="button" onClick={() => set(k, !fields[k])}
                            className="px-3 py-2 rounded-xl text-xs font-medium border transition-colors"
                            style={fields[k]
                              ? { background: "var(--color-gold)", color: "var(--color-navy)", borderColor: "var(--color-gold)" }
                              : { background: "transparent", color: "var(--color-navy)", borderColor: "oklch(0.18 0.065 260 / 0.2)" }}>
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Step 3 — Preview & Publish */}
        {step === 3 && (
          <div className="rounded-2xl bg-white border border-navy/8 p-8 shadow-sm">
            <h2 className="font-semibold text-lg mb-6" style={{ color: "var(--color-navy)" }}>{t.post.preview_title}</h2>
            {fields.images && (
              <div className="h-52 rounded-2xl overflow-hidden mb-5 bg-sand">
                <img src={fields.images.split(" | ")[0]} alt="" className="w-full h-full object-cover" />
              </div>
            )}
            <h3 className="text-xl font-bold mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--color-navy)" }}>
              {fields.titre || t.post.untitled}
            </h3>
            <p className="text-sm mb-4" style={{ color: "var(--color-navy)", opacity: 0.5 }}>
              {[fields.ville, fields.gouvernerat].filter(Boolean).join(", ")} · {fields.type} · {fields.contrat}
            </p>
            {fields.prix && (
              <p className="text-2xl font-bold mb-4" style={{ color: "var(--color-gold)", fontFamily: "var(--font-display)" }}>
                {new Intl.NumberFormat("fr-TN").format(parseFloat(fields.prix))} TND
              </p>
            )}
            {fields.description && (
              <p className="text-sm leading-relaxed mb-6 line-clamp-4" style={{ color: "var(--color-navy)", opacity: 0.7 }}>{fields.description}</p>
            )}
            {error && <p className="text-sm font-medium mb-4" style={{ color: "var(--color-terra)" }}>{error}</p>}
            <button onClick={publish} disabled={submitting || !fields.titre}
                    className="w-full py-4 rounded-xl font-bold text-base transition-opacity hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                    style={{ background: "var(--color-navy)", color: "white" }}>
              {submitting && <Loader2 size={18} className="animate-spin" />}
              {submitting ? t.post.publishing : t.post.publish}
            </button>
          </div>
        )}

        {/* Nav buttons */}
        <div className="flex items-center justify-between mt-8">
          <button onClick={() => setStep(s => Math.max(0, s - 1))} disabled={step === 0}
                  className="flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-sm border transition-colors disabled:opacity-30"
                  style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)" }}>
            <ArrowLeft size={15} /> {t.post.prev}
          </button>
          {step < 3 && (
            <button onClick={() => setStep(s => Math.min(3, s + 1))}
                    className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-opacity hover:opacity-90"
                    style={{ background: "var(--color-navy)", color: "white" }}>
              {t.post.next} <ArrowRight size={15} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
