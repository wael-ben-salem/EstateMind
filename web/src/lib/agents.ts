/**
 * Server-side helpers for talking to the 5 (+1) ML agents.
 * These bypass our /api/agents/* gateway (no point in same-process round-trips)
 * but use the same env-var URLs so the swap point is consistent.
 */

export type RecommenderIntent = {
  intent?: string;
  contract?: string | null;
  city?: string | null;
  property_type?: string | null;
  budget_min?: number | null;
  budget_max?: number | null;
  rooms?: number | null;
  min_surface?: number | null;
  amenities?: string[];
  preferences?: string[];
  confidence?: number;
};

export type RecommenderResponse = {
  status: string;
  query: string;
  classification?: { label: string; confidence: number; reason?: string };
  understanding?: RecommenderIntent;
  user_message?: string;
  summary?: string;
  recommendation?: { intent: RecommenderIntent; total_after_filters: number; global_explanation?: string; relaxed_criteria?: string[]; message?: string | null };
  results?: unknown[];
};

export async function recommenderQuery(
  query: string,
  top_k = 5
): Promise<RecommenderResponse | null> {
  const base = process.env.AGENT_RECOMMENDER_URL;
  if (!base) return null;
  try {
    const r = await fetch(`${base}/api/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k }),
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

export type PropertyInput = {
  surface?: number | null;
  pieces?: number | null;
  etage?: number | null;
  gouvernerat?: string | null;
  ville?: string | null;
  type?: string | null;
  contrat?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  has_ascenseur?: boolean | null;
  has_balcon?: boolean | null;
  has_chaffage?: boolean | null;
  has_climatisation?: boolean | null;
  has_garage?: boolean | null;
  has_gardien?: boolean | null;
  has_jardin?: boolean | null;
  has_parking?: boolean | null;
  has_piscine?: boolean | null;
  has_terrasse?: boolean | null;
};

export async function predictPrice(input: PropertyInput) {
  const base = process.env.AGENT_PRICE_URL;
  if (!base) return null;
  try {
    const r = await fetch(`${base}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    if (!r.ok) return null;
    return r.json() as Promise<Record<string, unknown>>;
  } catch {
    return null;
  }
}

export async function scoreAnomaly(input: PropertyInput & { prix: number }) {
  const base = process.env.AGENT_ANOMALY_URL;
  if (!base) return null;
  try {
    const r = await fetch(`${base}/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    if (!r.ok) return null;
    return r.json() as Promise<Record<string, unknown>>;
  } catch {
    return null;
  }
}

import type { Listing } from "@/generated/prisma";

/** Map Prisma's camelCase Listing into the snake_case PropertyInput agents expect. */
export function listingToPropertyInput(l: Listing): PropertyInput {
  return {
    surface: l.surface,
    pieces: l.pieces,
    etage: l.etage,
    gouvernerat: l.gouvernerat,
    ville: l.ville,
    type: l.type,
    contrat: l.contrat,
    latitude: l.latitude,
    longitude: l.longitude,
    has_ascenseur: l.hasAscenseur,
    has_balcon: l.hasBalcon,
    has_chaffage: l.hasChaffage,
    has_climatisation: l.hasClimatisation,
    has_garage: l.hasGarage,
    has_gardien: l.hasGardien,
    has_jardin: l.hasJardin,
    has_parking: l.hasParking,
    has_piscine: l.hasPiscine,
    has_terrasse: l.hasTerrasse,
  };
}

/** Best-effort parse of the price agent's response. */
export function extractPredictedPrice(resp: unknown): number | null {
  if (!resp || typeof resp !== "object") return null;
  const r = resp as Record<string, unknown>;
  for (const k of ["predicted_price", "prediction", "price", "predicted", "value"]) {
    const v = r[k];
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "string") {
      const n = parseFloat(v);
      if (Number.isFinite(n)) return n;
    }
  }
  return null;
}

/**
 * Parse the anomaly agent's response.
 * Real shape from sirinehj's container:
 *   { predicted_price, actual_price, price_gap_pct, is_anomaly (0|1),
 *     opportunity_label ("Normal" | "Opportunity" | "Risk" | ...), anomaly_confidence }
 */
export function extractAnomalyVerdict(resp: unknown): {
  level: "low" | "medium" | "high" | "unknown";
  label: string;
  detail?: string;
} {
  if (!resp || typeof resp !== "object") return { level: "unknown", label: "Indisponible" };
  const r = resp as Record<string, unknown>;

  const isAnom = Number(r.is_anomaly) === 1;
  const conf = typeof r.anomaly_confidence === "number" ? r.anomaly_confidence : null;
  const gap = typeof r.price_gap_pct === "number" ? r.price_gap_pct : null;
  const opp = typeof r.opportunity_label === "string" ? r.opportunity_label : null;

  const detailParts: string[] = [];
  if (gap !== null) {
    detailParts.push(
      gap > 0 ? `+${gap.toFixed(1)}% vs prédit` : `${gap.toFixed(1)}% vs prédit`
    );
  }
  if (conf !== null) detailParts.push(`confiance ${(conf * 100).toFixed(1)}%`);

  if (isAnom) {
    return {
      level: "high",
      label: opp && opp !== "Normal" ? opp : "Anomalie détectée",
      detail: detailParts.join(" · ") || undefined,
    };
  }

  // Not anomaly but maybe still flagged (gap > 15%)
  if (gap !== null && Math.abs(gap) >= 15) {
    return {
      level: "medium",
      label: "À vérifier",
      detail: detailParts.join(" · ") || undefined,
    };
  }

  return {
    level: "low",
    label: opp ?? "Prix conforme",
    detail: detailParts.join(" · ") || undefined,
  };
}
