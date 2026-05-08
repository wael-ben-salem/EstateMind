"use client";

import { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Sparkles, Send, Loader2, MapPin, Home, Bed, Banknote,
  FileText, ArrowRight, Bot,
} from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";

type Understanding = {
  intent?: string;
  contract?: string | null;
  city?: string | null;
  property_type?: string | null;
  budget_max?: number | null;
  budget_min?: number | null;
  rooms?: number | null;
  min_surface?: number | null;
  confidence?: number;
  amenities?: string[];
};

type BotMessage = {
  role: "user" | "assistant";
  text: string;
  understanding?: Understanding;
  explanation?: string;
  searchUrl?: string;
};

function titleCase(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

function buildSearchUrl(locale: string, query: string, u: Understanding): string {
  const p = new URLSearchParams({ q: query });
  if (u.city) p.set("gouvernerat", titleCase(u.city));
  if (u.property_type) p.set("type", titleCase(u.property_type));
  if (u.contract) p.set("contrat", u.contract);
  if (u.rooms) p.set("pieces", String(u.rooms));
  if (u.budget_max) p.set("priceMax", String(u.budget_max));
  if (u.budget_min) p.set("priceMin", String(u.budget_min));
  return `/${locale}/search?${p.toString()}`;
}

function UnderstandingChips({ u }: { u: Understanding }) {
  const chips: { icon: React.ReactNode; label: string }[] = [];
  if (u.city) chips.push({ icon: <MapPin className="size-3" />, label: titleCase(u.city) });
  if (u.property_type) chips.push({ icon: <Home className="size-3" />, label: titleCase(u.property_type) });
  if (u.contract) chips.push({ icon: <FileText className="size-3" />, label: titleCase(u.contract) });
  if (u.rooms) chips.push({ icon: <Bed className="size-3" />, label: `${u.rooms}+ pièces` });
  if (u.budget_max) chips.push({ icon: <Banknote className="size-3" />, label: `≤ ${u.budget_max.toLocaleString("fr-TN")} TND` });
  if (u.budget_min) chips.push({ icon: <Banknote className="size-3" />, label: `≥ ${u.budget_min.toLocaleString("fr-TN")} TND` });
  if (!chips.length) return null;
  return (
    <div className="flex flex-wrap gap-1 pt-1">
      {chips.map((c, i) => (
        <Badge key={i} variant="secondary" className="gap-1 text-[11px]">
          {c.icon}{c.label}
        </Badge>
      ))}
    </div>
  );
}

const SUGGESTIONS = [
  "Villa avec piscine à La Marsa",
  "Studio à louer à Sfax moins de 1000 TND",
  "Appartement S+2 à Sousse bord de mer",
];

export function SearchChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const pathname = usePathname();
  const locale = pathname.split("/")[1] || "fr";

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(e: React.FormEvent, overrideText?: string) {
    e.preventDefault();
    const q = (overrideText ?? input).trim();
    if (!q || loading) return;

    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);

    try {
      const r = await fetch("/api/chat/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 5 }),
        signal: AbortSignal.timeout(95_000),
      });

      if (r.status === 502 || r.status === 503 || r.status === 504) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: "Le service de recommandation est en cours de démarrage (premier appel ~60 s). Renvoyez votre message dans quelques secondes.",
          },
        ]);
        return;
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();

      const u: Understanding = data.understanding ?? {};
      const hasUnderstanding = !!(u.city || u.property_type || u.contract || u.rooms || u.budget_max);

      const text = hasUnderstanding
        ? "Voici ce que j'ai compris — je cherche dans notre base :"
        : (data.summary ?? data.user_message ?? "Je n'ai pas pu interpréter cette recherche. Pouvez-vous reformuler ?");

      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text,
          understanding: hasUnderstanding ? u : undefined,
          explanation: data.recommendation?.global_explanation ?? undefined,
          searchUrl: hasUnderstanding ? buildSearchUrl(locale, q, u) : undefined,
        },
      ]);
    } catch (err) {
      const isTimeout = err instanceof Error && (err.name === "TimeoutError" || err.name === "AbortError");
      const msg = isTimeout
        ? "Le service n'a pas répondu à temps. Réessayez — il est peut-être en train de démarrer."
        : `Erreur : ${err instanceof Error ? err.message : "inconnue"}`;
      setMessages((m) => [...m, { role: "assistant", text: msg }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        className={`${buttonVariants({ size: "lg" })} fixed bottom-5 start-5 z-50 size-12 rounded-full p-0 shadow-lg`}
        aria-label="Recherche IA"
      >
        <Sparkles className="size-5" />
      </SheetTrigger>

      <SheetContent side="left" className="flex w-full max-w-md flex-col p-0 sm:max-w-md">
        <SheetHeader className="border-b border-border px-4 py-3 text-start">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            Recherche intelligente
          </SheetTitle>
          <SheetDescription className="text-xs">
            Décrivez le bien que vous cherchez en langage naturel.
          </SheetDescription>
        </SheetHeader>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
          {messages.length === 0 && !loading && (
            <div className="space-y-3">
              <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
                <Bot className="mb-2 size-4 text-primary" />
                Essayez par exemple :
              </div>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={(e) => send(e as unknown as React.FormEvent, s)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-left text-sm hover:border-primary/40 hover:bg-secondary/40"
                >
                  <Sparkles className="me-1.5 inline size-3 text-primary" />
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={msg.role === "user"
              ? "ms-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-3 py-2 text-sm text-primary-foreground"
              : "max-w-[95%] space-y-2 rounded-2xl rounded-tl-sm bg-secondary px-3 py-2 text-sm"
            }>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>

              {msg.understanding && <UnderstandingChips u={msg.understanding} />}

              {msg.explanation && (
                <p className="text-xs text-muted-foreground">{msg.explanation}</p>
              )}

              {msg.searchUrl && (
                <Link
                  href={msg.searchUrl}
                  onClick={() => setOpen(false)}
                  className={`${buttonVariants({ size: "sm" })} mt-1 w-full gap-1`}
                >
                  Voir les résultats
                  <ArrowRight className="size-3.5" />
                </Link>
              )}
            </div>
          ))}

          {loading && (
            <div className="rounded-2xl rounded-tl-sm bg-secondary px-3 py-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Loader2 className="size-3.5 animate-spin" />
                Analyse en cours…
              </div>
            </div>
          )}
        </div>

        <form
          onSubmit={send}
          className="flex items-center gap-2 border-t border-border bg-card px-3 py-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Décrivez votre recherche…"
            disabled={loading}
            className="flex-1"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className={`${buttonVariants({ size: "sm" })} h-9 w-9 p-0`}
            aria-label="Envoyer"
          >
            <Send className="size-4" />
          </button>
        </form>
      </SheetContent>
    </Sheet>
  );
}
