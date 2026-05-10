"use client";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Scale, X, Send, Loader2, MessageCircle } from "lucide-react";
import { useLang } from "@/contexts/lang";

interface Message { role: "user" | "assistant"; text: string; }

export function LegalChat() {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(Math.random().toString(36).slice(2));
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener("open-legal-chat", handler);
    return () => window.removeEventListener("open-legal-chat", handler);
  }, []);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("query", text);
      fd.append("session_id", sessionId.current);
      const res = await fetch("/api/agents/lawagent/agent/ask", {
        method: "POST", body: fd,
        signal: AbortSignal.timeout(240_000),
      });
      const data = await res.json();
      setMessages(m => [...m, { role: "assistant", text: data.result ?? data.answer ?? data.response ?? data.error ?? t.legal.error }]);
    } catch {
      setMessages(m => [...m, { role: "assistant", text: t.legal.unavailable }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Toggle button */}
      <button onClick={() => setOpen(o => !o)}
              className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gold text-navy
                         flex items-center justify-center shadow-xl hover:scale-110 transition-transform">
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 flex flex-col rounded-2xl
                        overflow-hidden shadow-2xl border border-white/20"
             style={{ height: "480px", background: "oklch(0.18 0.065 260)" }}>
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gold/10 border-b border-white/10">
            <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center">
              <Scale size={16} className="text-gold" />
            </div>
            <div>
              <p className="text-white text-sm font-semibold">{t.legal.title}</p>
              <p className="text-white/40 text-xs">{t.legal.subtitle}</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* Greeting shown when no messages yet */}
            {messages.length === 0 && !loading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed bg-white/10 text-white/90">
                  {t.legal.greeting}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`rounded-xl text-sm leading-relaxed
                  ${m.role === "user"
                    ? "max-w-[80%] px-3.5 py-2.5 bg-gold text-navy font-medium"
                    : "w-full px-3.5 py-2.5 bg-white/10 text-white/90"}`}>
                  {m.role === "user" ? m.text : (
                    <ReactMarkdown
                      components={{
                        h1: ({ children }) => <p style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, color: "white" }}>{children}</p>,
                        h2: ({ children }) => <p style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, color: "white", borderBottom: "1px solid rgba(255,255,255,0.15)", paddingBottom: 4, marginTop: 10 }}>{children}</p>,
                        h3: ({ children }) => <p style={{ fontWeight: 600, fontSize: 12, marginBottom: 3, color: "rgba(255,255,255,0.9)" }}>{children}</p>,
                        p: ({ children }) => <p style={{ marginBottom: 6, fontSize: 13, lineHeight: 1.65, color: "rgba(255,255,255,0.88)" }}>{children}</p>,
                        strong: ({ children }) => <strong style={{ fontWeight: 700, color: "white" }}>{children}</strong>,
                        ul: ({ children }) => <ul style={{ paddingLeft: 16, marginBottom: 6 }}>{children}</ul>,
                        ol: ({ children }) => <ol style={{ paddingLeft: 16, marginBottom: 6 }}>{children}</ol>,
                        li: ({ children }) => <li style={{ fontSize: 12, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", marginBottom: 2 }}>{children}</li>,
                        table: ({ children }) => <div style={{ overflowX: "auto", marginBottom: 8 }}><table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>{children}</table></div>,
                        th: ({ children }) => <th style={{ padding: "5px 8px", textAlign: "left", fontWeight: 700, color: "white", borderBottom: "1px solid rgba(255,255,255,0.25)" }}>{children}</th>,
                        td: ({ children }) => <td style={{ padding: "4px 8px", color: "rgba(255,255,255,0.8)", borderBottom: "1px solid rgba(255,255,255,0.08)", verticalAlign: "top", lineHeight: 1.5 }}>{children}</td>,
                        hr: () => <hr style={{ border: "none", borderTop: "1px solid rgba(255,255,255,0.12)", margin: "8px 0" }} />,
                        code: ({ children }) => <code style={{ background: "rgba(255,255,255,0.1)", padding: "1px 4px", borderRadius: 3, fontSize: 11 }}>{children}</code>,
                      }}
                    >
                      {m.text}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/10 text-white/60 px-3.5 py-2.5 rounded-xl text-sm flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin" /> {t.legal.loading}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={send} className="flex gap-2 p-3 border-t border-white/10">
            <input value={input} onChange={e => setInput(e.target.value)}
                   placeholder={t.legal.placeholder}
                   className="flex-1 bg-white/10 text-white placeholder:text-white/30 text-sm
                              rounded-xl px-3 py-2 outline-none focus:ring-1 focus:ring-gold/50" />
            <button type="submit" disabled={loading || !input.trim()}
                    className="w-9 h-9 rounded-xl bg-gold/20 hover:bg-gold/40 flex items-center
                               justify-center text-gold disabled:opacity-40 transition-colors">
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
