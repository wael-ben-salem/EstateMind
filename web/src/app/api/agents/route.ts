import { NextResponse } from "next/server";

/**
 * Discovery endpoint: lists the agents this gateway proxies, with a one-line
 * notes field. Useful for the frontend to render an "agent status" badge.
 */
const AGENTS = [
  {
    name: "captioner",
    base: "/api/agents/captioner",
    upstream: process.env.AGENT_CAPTIONER_URL,
    description: "Photo → French listing description (BLIP-2 + Ollama)",
    examples: ["POST /caption-listing (multipart files)"],
  },
  {
    name: "outliers",
    base: "/api/agents/outliers",
    upstream: process.env.AGENT_ESTATEMIND_URL,
    description: "Market intel: pocket detection, RAG comparables, POI scoring, price map",
    examples: ["GET /artifacts", "POST /detect-pocket", "GET /map"],
  },
  {
    name: "lawagent",
    base: "/api/agents/lawagent",
    upstream: process.env.AGENT_LAWAGENT_URL,
    description: "Tunisian property law Q&A + contract analysis (Qdrant + Cohere)",
    examples: ["POST /agent/ask (multipart query)", "POST /analyze/contract (multipart file)"],
  },
  {
    name: "price",
    base: "/api/agents/price",
    upstream: process.env.AGENT_PRICE_URL,
    description: "Price prediction (LightGBM + GradientBoosting+log)",
    examples: ["POST /predict (see /docs)"],
  },
  {
    name: "anomaly",
    base: "/api/agents/anomaly",
    upstream: process.env.AGENT_ANOMALY_URL,
    description: "Listing anomaly / under-valuation detection",
    examples: ["POST /detect (see /docs)"],
  },
  {
    name: "recommender",
    base: "/api/agents/recommender",
    upstream: process.env.AGENT_RECOMMENDER_URL,
    description: "NLP free-text search over listings (FR queries, intent extraction)",
    examples: ["POST /api/recommend {query, top_k}"],
  },
];

export async function GET() {
  return NextResponse.json({ agents: AGENTS });
}
