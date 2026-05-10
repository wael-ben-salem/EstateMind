import { NextRequest, NextResponse } from "next/server";

const RECOMMENDER    = process.env.AGENT_RECOMMENDER_URL ?? "https://estatemind-recommender.onrender.com";
const BACKEND        = process.env.BACKEND_API_URL ?? "http://localhost:3002";
const SERVICE_TOKEN  = process.env.BACKEND_SERVICE_TOKEN ?? "";

function titleCase(s: string) { return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase(); }

async function localFallback(understanding: Record<string, unknown>, top_k: number) {
  const params = new URLSearchParams({ limit: String(top_k), offset: "0" });
  if (understanding.city)          params.set("gouvernerat", titleCase(String(understanding.city)));
  if (understanding.property_type) params.set("type",        titleCase(String(understanding.property_type)));
  if (understanding.contract)      params.set("contrat",     String(understanding.contract));
  if (understanding.rooms)         params.set("pieces",      String(understanding.rooms));
  if (understanding.budget_max)    params.set("max_prix",    String(understanding.budget_max));

  try {
    const r = await fetch(`${BACKEND}/api/listings?${params.toString()}`, {
      headers: SERVICE_TOKEN ? { Authorization: `Bearer ${SERVICE_TOKEN}` } : {},
      signal: AbortSignal.timeout(8_000),
    });
    if (!r.ok) return [];
    const d = await r.json();
    return Array.isArray(d.data) ? d.data : Array.isArray(d.listings) ? d.listings : Array.isArray(d) ? d : [];
  } catch {
    return [];
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  try {
    const upstream = await fetch(`${RECOMMENDER}/api/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: body.query, top_k: body.top_k ?? 12 }),
      signal: AbortSignal.timeout(95_000),
    });
    const data = await upstream.json();

    // If the remote recommender found nothing but did parse intent, fall back to local DB
    const results = data.results ?? data.listings ?? [];
    if (results.length === 0 && data.understanding) {
      const fallback = await localFallback(data.understanding, body.top_k ?? 5);
      if (fallback.length > 0) {
        return NextResponse.json({ ...data, results: fallback, _fallback: true }, { status: upstream.status });
      }
    }

    return NextResponse.json(data, { status: upstream.status });
  } catch (e) {
    const isTimeout = e instanceof Error && e.name === "TimeoutError";
    return NextResponse.json(
      { error: isTimeout ? "Recommender is cold-starting, please retry in 30s" : "Recommender unreachable" },
      { status: isTimeout ? 504 : 502 }
    );
  }
}
