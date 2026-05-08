"use client";

import { useState, useRef, useEffect } from "react";
import { Scale, Send, Loader2, BookOpen, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";

type Article = { id: string; text: string };
type Message = {
  role: "user" | "assistant";
  content: string;
  refs?: Article[];
  steps?: string[];
};

export function LegalChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;

    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);

    try {
      const fd = new FormData();
      fd.append("query", q);
      if (sessionIdRef.current) fd.append("session_id", sessionIdRef.current);

      const r = await fetch("/api/agents/lawagent/agent/ask", { method: "POST", body: fd });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();

      if (data.session_id) sessionIdRef.current = data.session_id;
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: data.result ?? data.error ?? "(réponse vide)",
          refs: data.reference_articles,
          steps: data.reasoning_steps,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Erreur : ${err instanceof Error ? err.message : "inconnue"}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        className={`${buttonVariants({ size: "lg" })} fixed bottom-5 end-5 z-50 size-12 rounded-full p-0 shadow-lg`}
        aria-label="Assistant juridique"
      >
        <Scale className="size-5" />
      </SheetTrigger>

      <SheetContent side="right" className="flex w-full max-w-md flex-col p-0 sm:max-w-md">
        <SheetHeader className="border-b border-border px-4 py-3 text-start">
          <SheetTitle className="flex items-center gap-2">
            <Scale className="size-4 text-primary" />
            Assistant juridique
          </SheetTitle>
          <SheetDescription className="text-xs">
            Q&amp;A sur le droit immobilier tunisien — propulsé par l&apos;agent <code>lawagent</code>.
          </SheetDescription>
        </SheetHeader>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
          {messages.length === 0 && !loading && (
            <div className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground">
              Posez une question : <em>Quelles sont les démarches pour acheter un bien en Tunisie ?</em>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={msg.role === "user"
                ? "ms-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-3 py-2 text-sm text-primary-foreground"
                : "max-w-[92%] space-y-2 rounded-2xl rounded-tl-sm bg-secondary px-3 py-2 text-sm"
              }
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

              {msg.role === "assistant" && msg.steps && msg.steps.length > 0 && (
                <details className="text-xs text-muted-foreground">
                  <summary className="cursor-pointer hover:text-foreground">
                    <Sparkles className="me-1 inline size-3" />
                    Raisonnement ({msg.steps.length} étapes)
                  </summary>
                  <ul className="mt-1 space-y-0.5 ps-4">
                    {msg.steps.map((s, j) => <li key={j}>· {s}</li>)}
                  </ul>
                </details>
              )}

              {msg.role === "assistant" && msg.refs && msg.refs.length > 0 && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-primary">
                    <BookOpen className="me-1 inline size-3" />
                    {msg.refs.length} articles référencés
                  </summary>
                  <ul className="mt-1 space-y-2">
                    {msg.refs.map((a) => (
                      <li key={a.id} className="rounded-md border border-border bg-card p-2">
                        <span className="text-[10px] font-mono text-muted-foreground">Art. {a.id}</span>
                        <p className="mt-0.5 line-clamp-3 text-xs">{a.text}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm bg-secondary px-3 py-2 text-sm text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Recherche dans le corpus juridique…
            </div>
          )}
        </div>

        <form onSubmit={send} className="flex items-center gap-2 border-t border-border bg-card px-3 py-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Votre question juridique…"
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
