"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Send, Loader2, Sparkles, MapPin, Bed, Maximize2, ArrowLeft, X, MessageSquare, Zap, Globe } from "lucide-react";
import { NavbarLight } from "@/components/navbar";
import { useLang } from "@/contexts/lang";

interface Listing {
  id: number; titre?: string; prix?: number; gouvernerat?: string; ville?: string;
  type?: string; contrat?: string; surface?: number; pieces?: number; images?: string; score?: number;
}
interface Message {
  role: "user" | "assistant";
  text?: string;
  listings?: Listing[];
}

const PX_IDS = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540, 27637106];
const px = (id: number) =>
  `https://images.pexels.com/photos/${id}/pexels-photo-${id}.jpeg?auto=compress&cs=tinysrgb&w=600&h=400`;
const listingImg = (images: string | undefined, id: number) => {
  if (images) { const u = images.split(" | ")[0]; if (u?.startsWith("http")) return u; }
  return px(PX_IDS[id % PX_IDS.length]);
};
const NUM_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };
const fmtPrice = (p: number | undefined, label: string, locale: string) =>
  (!p || p <= 100) ? label : `${new Intl.NumberFormat(NUM_LOCALE[locale] ?? "fr-TN").format(p)} TND`;

const SUGGESTIONS = [
  { icon: "🏙️", text: "Appartement 3 pièces à Tunis avec balcon" },
  { icon: "🌊", text: "Villa avec piscine à Hammamet budget 800 000 TND" },
  { icon: "🌴", text: "Studio à louer à Sousse près de la mer" },
  { icon: "🏡", text: "Maison avec jardin à Sidi Bou Saïd" },
];

export default function RecommendPage() {
  const { t, locale } = useLang();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: t.recommend.greeting }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(query: string) {
    const text = query.trim();
    if (!text || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await fetch("/api/chat/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      const data = await res.json();
      const listings: Listing[] = data.results ?? data.listings ?? [];
      if (listings.length > 0) {
        const suffix = listings.length === 1 ? t.recommend.results_suffix_one : t.recommend.results_suffix_many;
        setMessages(m => [...m, { role: "assistant", text: `${t.recommend.results_prefix} ${listings.length} ${suffix}`, listings }]);
      } else {
        setMessages(m => [...m, { role: "assistant", text: data.answer ?? data.message ?? t.recommend.no_result }]);
      }
    } catch {
      setMessages(m => [...m, { role: "assistant", text: t.recommend.unavailable }]);
    } finally {
      setLoading(false);
    }
  }

  const userCount = messages.filter(m => m.role === "user").length;
  const sessionText = userCount === 1 ? t.recommend.sessions_one : t.recommend.sessions_many;
  const hasChats = messages.length > 1;

  const InputBar = ({ large = false }: { large?: boolean }) => (
    <form onSubmit={e => { e.preventDefault(); send(input); }}
          className={`flex items-center gap-3 bg-white rounded-2xl shadow-lg px-5 ${large ? "py-4 border-2" : "py-3 border"}`}
          style={{ borderColor: large ? "oklch(0.18 0.065 260 / 0.18)" : "oklch(0.18 0.065 260 / 0.12)" }}>
      <MessageSquare size={large ? 18 : 15} style={{ color: "var(--color-navy)", opacity: 0.25, flexShrink: 0 }} />
      <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
             placeholder={t.recommend.describe_placeholder}
             disabled={loading}
             className="flex-1 text-sm outline-none bg-transparent"
             style={{ color: "var(--color-navy)" }} />
      {input && (
        <button type="button" onClick={() => setInput("")}
                className="p-1 rounded-lg shrink-0" style={{ color: "var(--color-navy)", opacity: 0.3 }}>
          <X size={14} />
        </button>
      )}
      <button type="submit" disabled={loading || !input.trim()}
              className={`shrink-0 flex items-center justify-center rounded-xl font-bold transition-opacity hover:opacity-85 disabled:opacity-35 ${large ? "px-5 py-2.5 gap-2 text-sm" : "w-9 h-9"}`}
              style={{ background: "var(--color-navy)", color: "white" }}>
        {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
        {large && !loading && <span>Envoyer</span>}
      </button>
    </form>
  );

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: "var(--color-cream)" }}>
      <NavbarLight />

      {!hasChats ? (
        /* ═══════════════════ WELCOME STATE ═══════════════════ */
        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col items-center justify-center min-h-full px-4 py-12">

            {/* Glowing icon */}
            <div className="relative mb-7">
              <div className="w-24 h-24 rounded-3xl flex items-center justify-center shadow-2xl"
                   style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.28 0.09 255) 100%)" }}>
                <Sparkles size={44} style={{ color: "var(--color-gold)" }} />
              </div>
              <div className="absolute inset-0 rounded-3xl blur-2xl scale-150 -z-10 opacity-15"
                   style={{ background: "var(--color-gold)" }} />
            </div>

            {/* Heading */}
            <h1 className="text-4xl sm:text-5xl font-bold text-center mb-4 leading-tight"
                style={{ fontFamily: "var(--font-display)", color: "var(--color-navy)" }}>
              {locale === "ar" ? "ابحث عن عقارك المثالي"
               : locale === "en" ? "Find your perfect property"
               : "Trouvez votre bien idéal"}
            </h1>
            <p className="text-base text-center max-w-lg mb-2 leading-relaxed"
               style={{ color: "var(--color-navy)", opacity: 0.5 }}>
              {locale === "ar" ? "صف ما تبحث عنه بكلماتك — ذكاؤنا يحلل 49 000 إعلان عقاري في تونس."
               : locale === "en" ? "Describe what you're looking for in plain words — our AI searches 49,000 Tunisian listings."
               : "Décrivez votre bien en langage naturel — notre IA analyse 49 000 annonces pour vous."}
            </p>

            {/* Feature pills */}
            <div className="flex flex-wrap items-center justify-center gap-2 mb-10">
              {[
                { icon: <Zap size={12} />, text: "49 000+ annonces" },
                { icon: <Sparkles size={12} />, text: locale === "ar" ? "ذكاء اصطناعي" : locale === "en" ? "AI-powered" : "Alimenté par l'IA" },
                { icon: <Globe size={12} />, text: locale === "ar" ? "كل تونس" : locale === "en" ? "All of Tunisia" : "Toute la Tunisie" },
              ].map(({ icon, text }) => (
                <span key={text}
                      className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-full bg-white border border-navy/10 shadow-sm"
                      style={{ color: "var(--color-navy)" }}>
                  <span style={{ color: "var(--color-gold)" }}>{icon}</span>
                  {text}
                </span>
              ))}
            </div>

            {/* Suggestion cards */}
            <div className="w-full max-w-2xl mb-8">
              <p className="text-[10px] font-bold uppercase tracking-widest text-center mb-4"
                 style={{ color: "var(--color-navy)", opacity: 0.3 }}>
                {t.recommend.suggestions_label}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {SUGGESTIONS.map(({ icon, text }) => (
                  <button key={text} onClick={() => send(text)}
                          className="group text-left px-5 py-4 rounded-2xl bg-white border shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex items-start gap-3"
                          style={{ borderColor: "oklch(0.18 0.065 260 / 0.1)" }}>
                    <span className="text-xl shrink-0 mt-0.5">{icon}</span>
                    <span className="text-sm font-medium leading-snug" style={{ color: "var(--color-navy)" }}>{text}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Input */}
            <div className="w-full max-w-2xl">
              <InputBar large />
              <p className="text-xs text-center mt-3" style={{ color: "var(--color-navy)", opacity: 0.25 }}>
                {t.recommend.powered}
              </p>
            </div>

            <div className="mt-6">
              <Link href="/search" className="flex items-center gap-1.5 text-xs font-medium transition-colors hover:opacity-70"
                    style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                <ArrowLeft size={12} /> {t.recommend.classic}
              </Link>
            </div>
          </div>
        </div>
      ) : (
        /* ═══════════════════ CHAT STATE ═══════════════════ */
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Chat sub-header */}
          <div className="shrink-0 border-b px-4 sm:px-6 py-3 flex items-center gap-3 bg-white"
               style={{ borderColor: "oklch(0.18 0.065 260 / 0.08)" }}>
            <div className="w-7 h-7 rounded-xl flex items-center justify-center"
                 style={{ background: "oklch(0.68 0.17 47 / 0.12)" }}>
              <Sparkles size={13} style={{ color: "var(--color-gold)" }} />
            </div>
            <span className="font-semibold text-sm" style={{ color: "var(--color-navy)" }}>
              {t.recommend.page_title}
            </span>
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full"
                  style={{ background: "oklch(0.68 0.17 47 / 0.12)", color: "var(--color-gold)" }}>
              {userCount} {sessionText}
            </span>
            <Link href="/search"
                  className="ml-auto flex items-center gap-1 text-xs font-medium transition-opacity hover:opacity-70"
                  style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              <ArrowLeft size={11} /> {t.recommend.classic}
            </Link>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((m, i) => (
                <div key={i}>
                  {m.role === "user" ? (
                    /* User bubble */
                    <div className="flex justify-end">
                      <div className="max-w-lg px-5 py-3.5 rounded-2xl rounded-tr-sm text-sm font-medium leading-relaxed shadow-sm"
                           style={{ background: "var(--color-navy)", color: "white" }}>
                        {m.text}
                      </div>
                    </div>
                  ) : (
                    /* AI bubble */
                    <div className="flex gap-3 items-start">
                      <div className="w-9 h-9 rounded-2xl flex-shrink-0 flex items-center justify-center shadow-sm"
                           style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.26 0.08 255) 100%)" }}>
                        <Sparkles size={15} style={{ color: "var(--color-gold)" }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        {m.text && (
                          <div className="inline-block px-5 py-3.5 rounded-2xl rounded-tl-sm mb-4 text-sm leading-relaxed shadow-sm"
                               style={{ background: "white", color: "var(--color-navy)", border: "1px solid oklch(0.18 0.065 260 / 0.08)" }}>
                            {m.text}
                          </div>
                        )}
                        {m.listings && m.listings.length > 0 && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {m.listings.map(l => (
                              <Link key={l.id} href={`/listings/${l.id}`}
                                    className="group rounded-2xl overflow-hidden bg-white border border-navy/8 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                                {/* Image */}
                                <div className="relative h-44 overflow-hidden">
                                  <img src={listingImg(l.images, l.id)} alt={l.titre ?? ""}
                                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                                  {/* Gradient overlay */}
                                  <div className="absolute inset-x-0 bottom-0 h-20"
                                       style={{ background: "linear-gradient(to top, rgba(0,0,0,0.55), transparent)" }} />
                                  {/* Price on image */}
                                  <p className="absolute bottom-3 left-3 text-sm font-bold text-white drop-shadow">
                                    {fmtPrice(l.prix, t.common.price_on_request, locale)}
                                  </p>
                                  {/* Contrat badge */}
                                  {l.contrat && (
                                    <span className="absolute top-3 left-3 text-[10px] font-bold px-2 py-0.5 rounded-md"
                                          style={{ background: l.contrat === "Vente" ? "var(--color-gold)" : "var(--color-primary)", color: l.contrat === "Vente" ? "var(--color-navy)" : "white" }}>
                                      {l.contrat === "Vente" ? t.common.for_sale : t.common.for_rent}
                                    </span>
                                  )}
                                  {/* Score badge */}
                                  {l.score !== undefined && (
                                    <span className="absolute top-3 right-3 flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md"
                                          style={{ background: "rgba(255,255,255,0.92)", color: "var(--color-navy)" }}>
                                      <Sparkles size={9} style={{ color: "var(--color-gold)" }} />
                                      {Math.round(l.score * 100)}%
                                    </span>
                                  )}
                                </div>
                                {/* Body */}
                                <div className="p-4">
                                  <p className="text-sm font-semibold line-clamp-1 mb-1" style={{ color: "var(--color-navy)" }}>
                                    {l.titre ?? "Annonce"}
                                  </p>
                                  <p className="text-xs flex items-center gap-1 mb-3" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                                    <MapPin size={11} />{[l.ville, l.gouvernerat].filter(Boolean).join(", ") || "Tunisie"}
                                  </p>
                                  <div className="flex gap-3 text-xs font-medium" style={{ color: "var(--color-navy)", opacity: 0.5 }}>
                                    {l.pieces  && <span className="flex items-center gap-1"><Bed size={11} />{l.pieces} {t.common.rooms}</span>}
                                    {l.surface && <span className="flex items-center gap-1"><Maximize2 size={11} />{l.surface} m²</span>}
                                  </div>
                                </div>
                              </Link>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading dots */}
              {loading && (
                <div className="flex gap-3 items-center">
                  <div className="w-9 h-9 rounded-2xl flex-shrink-0 flex items-center justify-center"
                       style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.26 0.08 255) 100%)" }}>
                    <Loader2 size={15} className="animate-spin" style={{ color: "var(--color-gold)" }} />
                  </div>
                  <div className="px-5 py-3.5 rounded-2xl rounded-tl-sm text-sm shadow-sm flex items-center gap-1.5"
                       style={{ background: "white", color: "var(--color-navy)", border: "1px solid oklch(0.18 0.065 260 / 0.08)", opacity: 0.7 }}>
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--color-gold)", animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--color-gold)", animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--color-gold)", animationDelay: "300ms" }} />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Sticky input */}
          <div className="shrink-0 border-t bg-white px-4 sm:px-6 py-4"
               style={{ borderColor: "oklch(0.18 0.065 260 / 0.08)" }}>
            <div className="max-w-4xl mx-auto">
              <InputBar />
              <p className="text-[10px] text-center mt-2" style={{ color: "var(--color-navy)", opacity: 0.25 }}>
                {t.recommend.powered}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
