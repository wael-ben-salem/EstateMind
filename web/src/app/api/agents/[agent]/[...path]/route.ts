import { NextRequest, NextResponse } from "next/server";

/**
 * Catch-all proxy for the 5 (+1) microservice agents. The React client only
 * ever talks to `/api/agents/<name>/...` on this app's own origin — no CORS,
 * one base URL, swappable backend.
 *
 * Whitelist + base URLs come from env vars (.env at project root).
 */
const AGENT_BASE: Record<string, string | undefined> = {
  captioner: process.env.AGENT_CAPTIONER_URL,
  outliers: process.env.AGENT_ESTATEMIND_URL,
  lawagent: process.env.AGENT_LAWAGENT_URL,
  price: process.env.AGENT_PRICE_URL,
  anomaly: process.env.AGENT_ANOMALY_URL,
  recommender: process.env.AGENT_RECOMMENDER_URL,
};

const HOP_HEADERS = new Set([
  "host",
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-proto",
  "x-real-ip",
  "expect",
  "content-length",
]);

async function handler(
  req: NextRequest,
  ctx: { params: Promise<{ agent: string; path: string[] }> }
) {
  const { agent, path } = await ctx.params;
  const base = AGENT_BASE[agent];
  if (!base) {
    return NextResponse.json(
      { error: `unknown agent: ${agent}`, knownAgents: Object.keys(AGENT_BASE) },
      { status: 404 }
    );
  }

  const url = new URL(req.url);
  const target = `${base.replace(/\/$/, "")}/${path.join("/")}${url.search}`;

  const headers = new Headers();
  req.headers.forEach((v, k) => {
    if (!HOP_HEADERS.has(k.toLowerCase())) headers.set(k, v);
  });

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.arrayBuffer();
  }

  // captioner can take 3-4 min (BLIP-2 × N images + LLM); other agents just need cold-start cover.
  const timeoutMs = agent === "captioner" ? 300_000 : 90_000;
  (init as RequestInit & { signal?: AbortSignal }).signal = AbortSignal.timeout(timeoutMs);

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    const isTimeout = e instanceof Error && e.name === "TimeoutError";
    return NextResponse.json(
      {
        error: isTimeout ? "agent timeout" : "agent unreachable",
        agent,
        target,
        detail: isTimeout ? "Service did not respond within 90 s — it may be cold-starting, try again." : msg,
      },
      { status: isTimeout ? 504 : 502 }
    );
  }

  const respHeaders = new Headers();
  upstream.headers.forEach((v, k) => {
    if (!HOP_HEADERS.has(k.toLowerCase())) respHeaders.set(k, v);
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: respHeaders,
  });
}

export {
  handler as GET,
  handler as POST,
  handler as PUT,
  handler as PATCH,
  handler as DELETE,
  handler as OPTIONS,
};
