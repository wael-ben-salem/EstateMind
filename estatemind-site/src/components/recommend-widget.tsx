"use client";
import { useState, useRef, useEffect } from "react";
import { Sparkles, X, Send, Loader2, MapPin, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useLang } from "@/contexts/lang";

interface Listing { id: number; titre?: string; prix?: number; gouvernerat?: string; ville?: string; type?: string; contrat?: string; surface?: number; pieces?: number; images?: string; score?: number; }
interface Understanding { city?: string | null; property_type?: string | null; contract?: string | null; rooms?: number | null; budget_max?: number | null; budget_min?: number | null; }
interface Msg { role: "user" | "assistant"; text: string; listings?: Listing[]; understanding?: Understanding; searchUrl?: string; }

const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number) => `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=400&h=260`;
const listingImg = (images: string | undefined, id: number) => {
  if (images) { const u = images.split(" | ")[0]; if (u?.startsWith("http")) return u; }
  return px(PX_IDS[id % PX_IDS.length]);
};
const fmtPrice = (p?: number) => p ? `${new Intl.NumberFormat("fr-TN").format(p)} TND` : "—";

function titleCase(s: string) { return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase(); }
function buildSearchUrl(u: Understanding, q: string) {
  const p = new URLSearchParams({ q });
  if (u.city) p.set("gouvernerat", titleCase(u.city));
  if (u.property_type) p.set("type", titleCase(u.property_type));
  if (u.contract) p.set("contrat", u.contract);
  if (u.rooms) p.set("pieces", String(u.rooms));
  if (u.budget_max) p.set("max_prix", String(u.budget_max));
  return `/search?${p.toString()}`;
}

export function RecommendWidget() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { t } = useLang();

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs, loading]);

  async function send(e: React.FormEvent, override?: string) {
    e.preventDefault();
    const q = (override ?? input).trim();
    if (!q || loading) return;
    setInput("");
    setMsgs(m => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const r = await fetch("/api/chat/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 5 }),
        signal: AbortSignal.timeout(95_000),
      });
      if (r.status >= 500) {
        setMsgs(m => [...m, { role: "assistant", text: t.recommend.cold_start }]);
        return;
      }
      const data = await r.json();
      const u: Understanding = data.understanding ?? {};
      const hasU = !!(u.city || u.property_type || u.contract || u.rooms || u.budget_max);
      const listings: Listing[] = data.results ?? data.listings ?? [];
      const hasListings = listings.length > 0;
      setMsgs(m => [...m, {
        role: "assistant",
        text: hasListings ? (hasU ? t.recommend.understood : (data.summary ?? t.recommend.no_result))
                          : (data.summary ?? data.user_message ?? (hasU ? t.recommend.understood : t.recommend.no_result)),
        listings: hasListings ? listings : undefined,
        understanding: hasU ? u : undefined,
        searchUrl: hasU ? buildSearchUrl(u, q) : undefined,
      }]);
    } catch {
      setMsgs(m => [...m, { role: "assistant", text: t.recommend.service_error }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Toggle */}
      <button onClick={() => setOpen(o => !o)}
              className="fixed bottom-6 left-6 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-xl hover:scale-110 transition-transform"
              style={{ background: "var(--color-primary)", color: "white" }}
              aria-label={t.recommend.title}>
        {open ? <X size={22} /> : <Sparkles size={22} />}
      </button>

      {/* Panel */}
      {open && (
        <div className="fixed bottom-24 left-6 z-50 w-80 sm:w-96 flex flex-col rounded-2xl overflow-hidden shadow-2xl border border-white/20"
             style={{ height: "500px", background: "white" }}>
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b"
               style={{ background: "var(--color-primary)", borderColor: "oklch(0.60 0.22 27 / 0.3)" }}>
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <Sparkles size={15} className="text-white" />
            </div>
            <div>
              <p className="text-white text-sm font-semibold">{t.recommend.title}</p>
              <p className="text-white/60 text-xs">{t.recommend.subtitle}</p>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3" style={{ background: "oklch(0.98 0.005 85)" }}>
            {msgs.length === 0 && !loading && (
              <div className="space-y-3">
                <div className="rounded-xl px-3 py-2.5 text-sm" style={{ background: "white", color: "var(--color-navy)" }}>
                  <Sparkles size={13} style={{ color: "var(--color-primary)", display: "inline", marginRight: 6 }} />
                  {t.recommend.greet}
                </div>
                {t.recommend.widget_suggestions.map(s => (
                  <button key={s} onClick={e => send(e as unknown as React.FormEvent, s)}
                          className="w-full text-left px-3 py-2.5 rounded-xl text-xs border hover:border-primary/40 transition-colors"
                          style={{ background: "white", borderColor: "oklch(0.18 0.065 260 / 0.15)", color: "var(--color-navy)" }}>
                    <Sparkles size={10} style={{ color: "var(--color-primary)", display: "inline", marginRight: 5 }} />{s}
                  </button>
                ))}
              </div>
            )}

            {msgs.map((m, i) => (
              <div key={i}>
                {m.role === "user" ? (
                  <div className="flex justify-end">
                    <div className="max-w-[80%] px-3 py-2 rounded-xl rounded-tr-sm text-sm text-white font-medium"
                         style={{ background: "var(--color-primary)" }}>
                      {m.text}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="max-w-[90%] px-3 py-2.5 rounded-xl rounded-tl-sm text-sm"
                         style={{ background: "white", color: "var(--color-navy)" }}>
                      <p>{m.text}</p>
                      {m.understanding && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {[m.understanding.city, m.understanding.property_type, m.understanding.contract].filter(Boolean).map(v => (
                            <span key={v} className="px-2 py-0.5 rounded-full text-xs font-medium"
                                  style={{ background: "oklch(0.60 0.22 27 / 0.1)", color: "var(--color-primary)" }}>
                              {titleCase(v!)}
                            </span>
                          ))}
                          {m.understanding.rooms && (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: "oklch(0.60 0.22 27 / 0.1)", color: "var(--color-primary)" }}>
                              {m.understanding.rooms}+ {t.recommend.rooms_plus}
                            </span>
                          )}
                          {m.understanding.budget_max && (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: "oklch(0.60 0.22 27 / 0.1)", color: "var(--color-primary)" }}>
                              {t.recommend.budget_max} {m.understanding.budget_max.toLocaleString("fr-TN")} TND
                            </span>
                          )}
                        </div>
                      )}
                      {m.searchUrl && (
                        <Link href={m.searchUrl} onClick={() => setOpen(false)}
                              className="flex items-center gap-1 mt-2 text-xs font-semibold hover:underline"
                              style={{ color: "var(--color-primary)" }}>
                          {t.recommend.see_results} <ArrowRight size={11} />
                        </Link>
                      )}
                    </div>
                    {m.listings && m.listings.length > 0 && (
                      <div className="space-y-2">
                        {m.listings.slice(0, 3).map(l => (
                          <Link key={l.id} href={`/listings/${l.id}`} onClick={() => setOpen(false)}
                                className="flex gap-3 items-center p-2.5 rounded-xl border hover:border-primary/30 transition-colors"
                                style={{ background: "white", borderColor: "oklch(0.18 0.065 260 / 0.1)" }}>
                            <img src={listingImg(l.images, l.id)} alt="" className="w-14 h-12 rounded-lg object-cover flex-shrink-0" />
                            <div className="min-w-0">
                              <p className="text-xs font-semibold line-clamp-1" style={{ color: "var(--color-navy)" }}>{l.titre ?? t.listing.unnamed}</p>
                              <p className="text-xs flex items-center gap-0.5 mt-0.5" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                                <MapPin size={9} />{[l.ville, l.gouvernerat].filter(Boolean).join(", ")}
                              </p>
                              <p className="text-xs font-bold mt-0.5" style={{ color: "var(--color-gold)" }}>{fmtPrice(l.prix)}</p>
                            </div>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl w-fit text-sm"
                   style={{ background: "white", color: "var(--color-navy)", opacity: 0.5 }}>
                <Loader2 size={13} className="animate-spin" /> {t.recommend.loading}
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={send} className="flex gap-2 p-3 border-t" style={{ borderColor: "oklch(0.18 0.065 260 / 0.1)" }}>
            <input value={input} onChange={e => setInput(e.target.value)} placeholder={t.recommend.placeholder}
                   disabled={loading}
                   className="flex-1 text-sm px-3 py-2 rounded-xl border outline-none"
                   style={{ borderColor: "oklch(0.18 0.065 260 / 0.15)", color: "var(--color-navy)" }} />
            <button type="submit" disabled={loading || !input.trim()}
                    className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors disabled:opacity-40"
                    style={{ background: "var(--color-primary)", color: "white" }}>
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
