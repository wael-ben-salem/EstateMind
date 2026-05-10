"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";
import { SlidersHorizontal } from "lucide-react";
import { useLang } from "@/contexts/lang";

interface Props {
  types: string[]; contrat: string; gov: string;
  minP: string; maxP: string; pieces: string;
  TYPES: string[]; CONTRATS: string[]; GOVS: string[];
}

const CONTRAT_LABELS: Record<string, [string, string, string]> = {
  "Vente":                ["Vente",                "بيع",          "For sale"],
  "Location":             ["Location",             "إيجار",        "For rent"],
  "Location saisonnière": ["Location saisonnière", "إيجار موسمي",  "Seasonal"],
};
const TYPE_LABELS: Record<string, [string, string, string]> = {
  "Appartement":      ["Appartement", "شقة",       "Apartment"],
  "Villa":            ["Villa",       "فيلا",      "Villa"],
  "Maison":           ["Maison",      "منزل",       "House"],
  "Terrain":          ["Terrain",     "أرض",        "Land"],
  "Studio":           ["Studio",      "ستوديو",     "Studio"],
  "Bureau":           ["Bureau",      "مكتب",       "Office"],
  "Local commercial": ["Local comm.", "محل تجاري", "Commercial"],
};

export function SearchFilters({ types, contrat, gov, minP, maxP, pieces, TYPES, CONTRATS, GOVS }: Props) {
  const router = useRouter();
  const sp = useSearchParams();
  const [, startT] = useTransition();
  const { t, locale } = useLang();
  const li = locale === "ar" ? 1 : locale === "en" ? 2 : 0;
  const tContrat = (c: string) => CONTRAT_LABELS[c]?.[li] ?? c;
  const tType    = (tp: string) => TYPE_LABELS[tp]?.[li] ?? tp;

  function update(key: string, value: string | null) {
    const p = new URLSearchParams(sp.toString());
    if (value === null) p.delete(key); else p.set(key, value);
    p.set("page", "1");
    startT(() => router.push(`/search?${p.toString()}`));
  }

  function toggleType(type: string) {
    const p = new URLSearchParams(sp.toString());
    const existing = p.getAll("type");
    p.delete("type");
    if (existing.includes(type)) { existing.filter(x => x !== type).forEach(x => p.append("type", x)); }
    else { [...existing, type].forEach(x => p.append("type", x)); }
    p.set("page", "1");
    startT(() => router.push(`/search?${p.toString()}`));
  }

  const label = "block text-xs font-semibold uppercase tracking-wide mb-2";
  const chip  = "px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-colors";

  return (
    <div className="space-y-5 text-sm">
      <div className="flex items-center gap-2 mb-4">
        <SlidersHorizontal size={16} style={{ color: "var(--color-gold)" }} />
        <span className="font-semibold text-sm" style={{ color: "var(--color-navy)" }}>{t.search.filters}</span>
      </div>

      {/* Contrat */}
      <div>
        <p className={label} style={{ color: "var(--color-navy)", opacity: 0.5 }}>{t.search.contract}</p>
        <div className="flex flex-wrap gap-2">
          {CONTRATS.map(c => (
            <button key={c} onClick={() => update("contrat", contrat === c ? null : c)}
                    className={chip}
                    style={contrat === c
                      ? { background: "var(--color-navy)", color: "white", borderColor: "var(--color-navy)" }
                      : { background: "transparent", color: "var(--color-navy)", borderColor: "oklch(0.18 0.065 260 / 0.2)" }}>
              {tContrat(c)}
            </button>
          ))}
        </div>
      </div>

      {/* Type */}
      <div>
        <p className={label} style={{ color: "var(--color-navy)", opacity: 0.5 }}>{t.search.property_type}</p>
        <div className="flex flex-col gap-1.5">
          {TYPES.map(type => (
            <label key={type} className="flex items-center gap-2 cursor-pointer group">
              <span className="w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors"
                    style={types.includes(type)
                      ? { background: "var(--color-gold)", borderColor: "var(--color-gold)" }
                      : { background: "transparent", borderColor: "oklch(0.18 0.065 260 / 0.3)" }}
                    onClick={() => toggleType(type)}>
                {types.includes(type) && <svg viewBox="0 0 12 12" fill="none" className="w-2.5 h-2.5"><path d="M2 6l3 3 5-5" stroke="var(--color-navy)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>}
              </span>
              <span className="text-xs" style={{ color: "var(--color-navy)" }} onClick={() => toggleType(type)}>{tType(type)}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Gouvernorat */}
      <div>
        <p className={label} style={{ color: "var(--color-navy)", opacity: 0.5 }}>{t.search.governorate}</p>
        <select value={gov} onChange={e => update("gouvernerat", e.target.value || null)}
                className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)", background: "white" }}>
          <option value="">{t.search.all_govs}</option>
          {GOVS.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>

      {/* Prix */}
      <div>
        <p className={label} style={{ color: "var(--color-navy)", opacity: 0.5 }}>{t.search.price}</p>
        <div className="flex gap-2">
          <input type="number" placeholder="Min" value={minP}
                 onChange={e => update("min_prix", e.target.value || null)}
                 className="w-1/2 px-2 py-2 rounded-xl border text-xs outline-none"
                 style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)", background: "white" }} />
          <input type="number" placeholder="Max" value={maxP}
                 onChange={e => update("max_prix", e.target.value || null)}
                 className="w-1/2 px-2 py-2 rounded-xl border text-xs outline-none"
                 style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)", background: "white" }} />
        </div>
      </div>

      {/* Pièces */}
      <div>
        <p className={label} style={{ color: "var(--color-navy)", opacity: 0.5 }}>{t.search.rooms_min}</p>
        <div className="flex gap-2 flex-wrap">
          {["1","2","3","4","5"].map(n => (
            <button key={n} onClick={() => update("pieces", pieces === n ? null : n)}
                    className={chip}
                    style={pieces === n
                      ? { background: "var(--color-gold)", color: "var(--color-navy)", borderColor: "var(--color-gold)" }
                      : { background: "transparent", color: "var(--color-navy)", borderColor: "oklch(0.18 0.065 260 / 0.2)" }}>
              {n}+
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
