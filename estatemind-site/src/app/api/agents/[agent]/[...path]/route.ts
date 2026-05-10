import { NextRequest, NextResponse } from "next/server";

const AGENT_BASE: Record<string, string | undefined> = {
  captioner:  process.env.AGENT_CAPTIONER_URL,
  outliers:   process.env.AGENT_ESTATEMIND_URL,
  lawagent:   process.env.AGENT_LAWAGENT_URL,
  price:      process.env.AGENT_PRICE_URL,
  anomaly:    process.env.AGENT_ANOMALY_URL,
  recommender: process.env.AGENT_RECOMMENDER_URL,
};

const HOP = new Set(["host","connection","keep-alive","transfer-encoding","upgrade","expect","content-length"]);

async function handler(req: NextRequest, ctx: { params: Promise<{ agent: string; path: string[] }> }) {
  const { agent, path } = await ctx.params;
  const base = AGENT_BASE[agent];
  if (!base) return NextResponse.json({ error: `unknown agent: ${agent}` }, { status: 404 });

  const url = new URL(req.url);
  const target = `${base.replace(/\/$/, "")}/${path.join("/")}${url.search}`;
  const headers = new Headers();
  req.headers.forEach((v, k) => { if (!HOP.has(k.toLowerCase())) headers.set(k, v); });

  const timeoutMs = agent === "captioner" ? 300_000 : agent === "lawagent" ? 240_000 : 90_000;
  const init: RequestInit & { signal?: AbortSignal } = {
    method: req.method, headers, redirect: "manual",
    signal: AbortSignal.timeout(timeoutMs),
  };
  if (!["GET","HEAD"].includes(req.method)) init.body = await req.arrayBuffer();

  try {
    const upstream = await fetch(target, init);
    const respHeaders = new Headers();
    upstream.headers.forEach((v, k) => { if (!HOP.has(k.toLowerCase())) respHeaders.set(k, v); });
    return new NextResponse(upstream.body, { status: upstream.status, headers: respHeaders });
  } catch (e) {
    const isTimeout = e instanceof Error && e.name === "TimeoutError";
    return NextResponse.json({ error: isTimeout ? "agent timeout" : "agent unreachable", agent },
      { status: isTimeout ? 504 : 502 });
  }
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE, handler as OPTIONS };
