"use client";
import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import {
  Scale, Upload, Loader2, FileText, Sparkles,
  AlertTriangle, CheckCircle2, ChevronRight, ImageIcon, X, FileScan,
  ShieldAlert, ShieldCheck, ClipboardList, Info, ChevronDown, Copy, Check,
} from "lucide-react";
import { useLang } from "@/contexts/lang";
import { NavbarLight } from "@/components/navbar";

/* ── Polished result renderer ──────────────────────────────────────────── */

type Section = { heading: string; body: string };

function parseSections(md: string): Section[] {
  const lines = md.split("\n");
  const sections: Section[] = [];
  let current: Section | null = null;
  for (const line of lines) {
    if (/^##\s/.test(line)) {
      if (current) sections.push(current);
      current = { heading: line.replace(/^##\s*/, "").trim(), body: "" };
    } else if (/^#\s/.test(line)) {
      // top-level h1 — skip as section heading but keep in first section body
      if (current) current.body += line + "\n";
    } else {
      if (current) current.body += line + "\n";
      else { current = { heading: "", body: line + "\n" }; }
    }
  }
  if (current) sections.push(current);
  return sections.filter(s => s.heading || s.body.trim());
}

function sectionMeta(heading: string) {
  const h = heading.toLowerCase();
  if (h.includes("risque"))    return { icon: ShieldAlert,    color: "#dc2626", bg: "oklch(0.97 0.01 27)",  badge: "oklch(0.60 0.22 27 / 0.1)",  label: "Risques" };
  if (h.includes("recomman"))  return { icon: ClipboardList,  color: "#16a34a", bg: "oklch(0.97 0.01 145)", badge: "oklch(0.50 0.15 145 / 0.1)", label: "Recommandations" };
  if (h.includes("conclusion")) return { icon: ShieldCheck,   color: "var(--color-gold)", bg: "oklch(0.97 0.015 70)", badge: "oklch(0.68 0.17 47 / 0.1)", label: "Conclusion" };
  if (h.includes("clause"))    return { icon: FileText,       color: "var(--color-navy)", bg: "white",                badge: "oklch(0.18 0.065 260 / 0.07)", label: "Clauses" };
  return                               { icon: Info,           color: "var(--color-navy)", bg: "white",                badge: "oklch(0.18 0.065 260 / 0.07)", label: "" };
}

function riskLevel(row: string): "high" | "medium" | "low" {
  const t = row.toLowerCase();
  if (/nullit|annul|majeur|nul |perte|void|fraud/.test(t)) return "high";
  if (/risque|absent|manqu|insuffis|non.pr|flou|incert/.test(t)) return "medium";
  return "low";
}

const RISK_COLOR: Record<string, string> = {
  high:   "oklch(0.60 0.22 27)",
  medium: "oklch(0.68 0.17 47)",
  low:    "oklch(0.40 0.12 260)",
};
const RISK_BG: Record<string, string> = {
  high:   "oklch(0.97 0.01 27)",
  medium: "oklch(0.97 0.015 70)",
  low:    "oklch(0.96 0.008 260)",
};
const RISK_LABEL: Record<string, string> = { high: "Élevé", medium: "Modéré", low: "Faible" };

function MdTable({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ overflowX: "auto", marginBottom: 12 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>{children}</table>
    </div>
  );
}

function mdComponents(isRisks: boolean, isRecs: boolean) {
  let recIdx = 0;
  return {
    h1: ({ children }: { children?: React.ReactNode }) => (
      <p style={{ fontWeight: 800, fontSize: 16, color: "var(--color-navy)", marginBottom: 12, fontFamily: "var(--font-display)" }}>{children}</p>
    ),
    h3: ({ children }: { children?: React.ReactNode }) => (
      <p style={{ fontWeight: 700, fontSize: 13, color: "var(--color-navy)", marginBottom: 6, marginTop: 14 }}>{children}</p>
    ),
    h4: ({ children }: { children?: React.ReactNode }) => (
      <p style={{ fontWeight: 600, fontSize: 12, color: "var(--color-navy)", marginBottom: 4, marginTop: 10, opacity: 0.8 }}>{children}</p>
    ),
    p: ({ children }: { children?: React.ReactNode }) => (
      <p style={{ fontSize: 13, lineHeight: 1.75, color: "var(--color-navy)", opacity: 0.82, marginBottom: 8 }}>{children}</p>
    ),
    strong: ({ children }: { children?: React.ReactNode }) => (
      <strong style={{ fontWeight: 700, color: "var(--color-navy)" }}>{children}</strong>
    ),
    ul: ({ children }: { children?: React.ReactNode }) => (
      <ul style={{ listStyle: "none", padding: 0, margin: "0 0 10px 0", display: "flex", flexDirection: "column", gap: 5 }}>{children}</ul>
    ),
    ol: ({ children }: { children?: React.ReactNode }) => (
      <ol style={{ listStyle: "none", padding: 0, margin: "0 0 10px 0", display: "flex", flexDirection: "column", gap: 8 }}>{children}</ol>
    ),
    li: ({ children }: { children?: React.ReactNode }) => {
      if (isRecs) {
        recIdx++;
        const n = recIdx;
        return (
          <li style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <span style={{ width: 24, height: 24, borderRadius: "50%", background: "var(--color-navy)", color: "white", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1 }}>{n}</span>
            <span style={{ fontSize: 13, lineHeight: 1.65, color: "var(--color-navy)", opacity: 0.85 }}>{children}</span>
          </li>
        );
      }
      return (
        <li style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 13, lineHeight: 1.65, color: "var(--color-navy)", opacity: 0.85 }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--color-gold)", flexShrink: 0, marginTop: 7 }} />
          <span>{children}</span>
        </li>
      );
    },
    table: ({ children }: { children?: React.ReactNode }) => <MdTable>{children}</MdTable>,
    thead: ({ children }: { children?: React.ReactNode }) => (
      <thead style={{ background: "oklch(0.18 0.065 260 / 0.06)" }}>{children}</thead>
    ),
    th: ({ children }: { children?: React.ReactNode }) => (
      <th style={{ padding: "9px 14px", textAlign: "left", fontWeight: 700, fontSize: 12, color: "var(--color-navy)", borderBottom: "2px solid oklch(0.68 0.17 47 / 0.35)", whiteSpace: "nowrap" }}>{children}</th>
    ),
    td: ({ children }: { children?: React.ReactNode }) => (
      <td style={{ padding: "8px 14px", fontSize: 12.5, color: "var(--color-navy)", opacity: 0.85, borderBottom: "1px solid oklch(0.18 0.065 260 / 0.07)", verticalAlign: "top", lineHeight: 1.6 }}>{children}</td>
    ),
    tr: ({ children, ...props }: { children?: React.ReactNode; [k: string]: unknown }) => {
      // color-code risk rows
      if (isRisks && props.node && (props.node as { type?: string }).type !== "tableHead") {
        const text = String(children);
        const lvl = riskLevel(text);
        if (lvl !== "low") {
          return (
            <tr style={{ background: RISK_BG[lvl], borderLeft: `3px solid ${RISK_COLOR[lvl]}` }}>
              {children}
            </tr>
          );
        }
      }
      return <tr>{children}</tr>;
    },
    blockquote: ({ children }: { children?: React.ReactNode }) => (
      <blockquote style={{ borderLeft: "3px solid var(--color-gold)", paddingLeft: 12, margin: "8px 0", opacity: 0.75, fontStyle: "italic", fontSize: 13 }}>{children}</blockquote>
    ),
    hr: () => <hr style={{ border: "none", borderTop: "1px solid oklch(0.18 0.065 260 / 0.1)", margin: "12px 0" }} />,
    code: ({ children }: { children?: React.ReactNode }) => (
      <code style={{ background: "oklch(0.18 0.065 260 / 0.06)", padding: "1px 5px", borderRadius: 4, fontSize: 11, fontFamily: "monospace" }}>{children}</code>
    ),
  };
}

function SectionCard({ section, defaultOpen = true }: { section: Section; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const meta = sectionMeta(section.heading);
  const Icon = meta.icon;
  const isRisks = /risque/i.test(section.heading);
  const isRecs  = /recomman/i.test(section.heading);

  return (
    <div style={{ borderRadius: 16, border: "1px solid oklch(0.18 0.065 260 / 0.1)", overflow: "hidden", marginBottom: 12, background: meta.bg }}>
      {/* Header */}
      <button onClick={() => setOpen(o => !o)}
              style={{ width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "14px 18px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}>
        <span style={{ width: 32, height: 32, borderRadius: 8, background: meta.badge, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon size={16} style={{ color: meta.color }} />
        </span>
        <span style={{ flex: 1, fontSize: 14, fontWeight: 700, color: "var(--color-navy)" }}>{section.heading}</span>
        {isRisks && (
          <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 20, background: "oklch(0.60 0.22 27 / 0.12)", color: "#dc2626" }}>
            Vérifier
          </span>
        )}
        <ChevronDown size={16} style={{ color: "var(--color-navy)", opacity: 0.4, transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s", flexShrink: 0 }} />
      </button>

      {/* Body */}
      {open && (
        <div style={{ padding: "0 18px 16px 18px", borderTop: "1px solid oklch(0.18 0.065 260 / 0.07)" }}>
          <div style={{ paddingTop: 14 }}>
            <ReactMarkdown components={mdComponents(isRisks, isRecs) as never}>
              {section.body.trim()}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

function LegalResult({ result }: { result: string }) {
  const [copied, setCopied] = useState(false);
  const sections = parseSections(result);

  // quick stats
  const riskSection = sections.find(s => /risque/i.test(s.heading));
  const riskCount = riskSection ? (riskSection.body.match(/^\|[^|]+\|/gm) ?? []).length - 1 : 0;
  const recSection = sections.find(s => /recomman/i.test(s.heading));
  const recCount = recSection ? (recSection.body.match(/^[\d]+\./gm) ?? []).length || (recSection.body.match(/^[-*]\s/gm) ?? []).length : 0;

  function copy() {
    navigator.clipboard.writeText(result).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  }

  return (
    <div>
      {/* Summary bar */}
      <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
        {riskCount > 0 && (
          <div style={{ flex: 1, minWidth: 100, padding: "10px 14px", borderRadius: 12, background: "oklch(0.97 0.01 27)", border: "1px solid oklch(0.60 0.22 27 / 0.2)", display: "flex", alignItems: "center", gap: 8 }}>
            <ShieldAlert size={16} style={{ color: "#dc2626", flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: "#dc2626", lineHeight: 1 }}>{riskCount}</div>
              <div style={{ fontSize: 10, color: "#dc2626", opacity: 0.75, fontWeight: 600 }}>risques</div>
            </div>
          </div>
        )}
        {recCount > 0 && (
          <div style={{ flex: 1, minWidth: 100, padding: "10px 14px", borderRadius: 12, background: "oklch(0.97 0.01 145)", border: "1px solid oklch(0.50 0.15 145 / 0.25)", display: "flex", alignItems: "center", gap: 8 }}>
            <CheckCircle2 size={16} style={{ color: "#16a34a", flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: "#16a34a", lineHeight: 1 }}>{recCount}</div>
              <div style={{ fontSize: 10, color: "#16a34a", opacity: 0.75, fontWeight: 600 }}>actions</div>
            </div>
          </div>
        )}
        <button onClick={copy}
                style={{ padding: "10px 14px", borderRadius: 12, border: "1px solid oklch(0.18 0.065 260 / 0.15)", background: "white", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "var(--color-navy)", opacity: 0.7 }}>
          {copied ? <Check size={13} style={{ color: "#16a34a" }} /> : <Copy size={13} />}
          {copied ? "Copié" : "Copier"}
        </button>
      </div>

      {/* Sections */}
      {sections.map((s, i) => (
        <SectionCard key={i} section={s} defaultOpen={i < 2} />
      ))}
    </div>
  );
}

const EXAMPLE_CONTRACTS = {
  fr: [
    "Contrat de bail d'habitation",
    "Promesse de vente",
    "Compromis de vente",
    "Contrat de location saisonnière",
  ],
  ar: [
    "عقد إيجار سكني",
    "وعد بالبيع",
    "عقد بيع ابتدائي",
    "عقد إيجار موسمي",
  ],
  en: [
    "Residential lease agreement",
    "Promise to sell",
    "Preliminary sale contract",
    "Seasonal rental contract",
  ],
};

async function extractPdfText(file: File): Promise<string> {
  const pdfjsLib = await import("pdfjs-dist");
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const pages: string[] = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = (content.items as { str?: string }[])
      .map(item => item.str ?? "")
      .join(" ");
    pages.push(text);
  }
  return pages.join("\n\n").trim();
}

export default function LegalPage() {
  const { t, locale } = useLang();
  const [contract, setContract] = useState("");
  const [question, setQuestion] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"contract" | "question">("contract");
  const sessionId = useRef(Math.random().toString(36).slice(2));
  const fileRef = useRef<HTMLInputElement>(null);

  function clearFile() {
    setImageFile(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    setContract("");
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    clearFile();
    setError("");

    const name = file.name.toLowerCase();

    if (file.type === "text/plain" || name.endsWith(".txt")) {
      const reader = new FileReader();
      reader.onload = ev => setContract((ev.target?.result as string) ?? "");
      reader.readAsText(file, "utf-8");
      return;
    }

    if (file.type === "application/pdf" || name.endsWith(".pdf")) {
      setExtracting(true);
      try {
        const text = await extractPdfText(file);
        if (text.length > 10) {
          setContract(text);
        } else {
          // PDF has no embedded text (scanned) — fall back to image send
          setImageFile(file);
          setImagePreview(null);
        }
      } catch {
        setError(
          locale === "ar" ? "فشل استخراج نص PDF" :
          locale === "en" ? "Failed to extract PDF text" :
          "Impossible d'extraire le texte du PDF"
        );
      } finally {
        setExtracting(false);
      }
      return;
    }

    if (file.type.startsWith("image/") || name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg")) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      return;
    }

    setError(
      locale === "ar" ? "صيغة غير مدعومة. استخدم TXT أو PDF أو PNG" :
      locale === "en" ? "Unsupported format. Use TXT, PDF or PNG" :
      "Format non supporté. Utilisez TXT, PDF ou PNG"
    );
  }

  async function analyze() {
    const isImage = !!imageFile;
    const text = mode === "contract" ? contract.trim() : question.trim();
    if (!isImage && !text) return;

    setAnalyzing(true);
    setResult("");
    setError("");

    const fd = new FormData();
    fd.append("session_id", sessionId.current);

    if (mode === "contract" && isImage) {
      const imgLabel =
        locale === "ar" ? "حلل العقد في هذه الصورة:" :
        locale === "en" ? "Analyze the contract in this image:" :
        "Analyse le contrat dans cette image :";
      fd.append("query", `${t.legal.query_prefix}\n\n${imgLabel}`);
      fd.append("file", imageFile);
    } else {
      fd.append("query", mode === "contract" ? `${t.legal.query_prefix}\n\n${text}` : text);
    }

    try {
      const res = await fetch("/api/agents/lawagent/agent/ask", {
        method: "POST", body: fd,
        signal: AbortSignal.timeout(240_000),
      });
      const data = await res.json();
      setResult(data.result ?? data.answer ?? data.response ?? data.error ?? t.legal.error);
    } catch {
      setError(t.legal.unavailable);
    } finally {
      setAnalyzing(false);
    }
  }

  const inputStyle = {
    borderColor: "oklch(0.18 0.065 260 / 0.15)",
    color: "var(--color-navy)",
    background: "white",
  };

  const isImage = !!imageFile;
  const examples = EXAMPLE_CONTRACTS[locale] ?? EXAMPLE_CONTRACTS.fr;
  const uploadLabel =
    locale === "ar" ? "رفع ملف (TXT، PDF، PNG)" :
    locale === "en" ? "Upload file (TXT, PDF, PNG)" :
    "Importer (TXT, PDF, PNG)";
  const canSubmit = !analyzing && !extracting && (
    mode === "question" ? question.trim().length > 3 :
    isImage ? true :
    contract.trim().length > 20
  );

  return (
    <div className="min-h-screen" style={{ background: "var(--color-cream)" }}>
      <NavbarLight />

      {/* Hero */}
      <div className="px-4 sm:px-6 py-10"
           style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}>
        <div className="max-w-6xl mx-auto flex items-center gap-5">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
               style={{ background: "oklch(0.68 0.17 47 / 0.18)", border: "1px solid oklch(0.68 0.17 47 / 0.3)" }}>
            <Scale size={28} style={{ color: "var(--color-gold)" }} />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white"
                style={{ fontFamily: "var(--font-display)" }}>
              {t.legal.title}
            </h1>
            <p className="text-sm mt-1.5 max-w-2xl leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>
              {t.legal.page_subtitle}
            </p>
          </div>
        </div>
      </div>

      {/* Main */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">

        {/* Mode tabs */}
        <div className="flex gap-2 mb-8">
          <button onClick={() => setMode("contract")}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all"
                  style={mode === "contract"
                    ? { background: "var(--color-navy)", color: "white" }
                    : { background: "white", color: "var(--color-navy)", border: "1px solid oklch(0.18 0.065 260 / 0.15)" }}>
            <FileText size={15} />
            {t.legal.paste_label}
          </button>
          <button onClick={() => setMode("question")}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all"
                  style={mode === "question"
                    ? { background: "var(--color-navy)", color: "white" }
                    : { background: "white", color: "var(--color-navy)", border: "1px solid oklch(0.18 0.065 260 / 0.15)" }}>
            <Sparkles size={15} />
            {t.legal.chat_label}
          </button>
        </div>

        <div className="grid lg:grid-cols-5 gap-8">

          {/* Left: Input */}
          <div className="lg:col-span-3 space-y-4">

            {mode === "contract" ? (
              <>
                {/* Image preview (PNG / scanned PDF) */}
                {isImage && imagePreview && (
                  <div className="relative rounded-2xl overflow-hidden border border-navy/10 bg-white">
                    <img src={imagePreview} alt="contract" className="w-full max-h-72 object-contain" />
                    <button onClick={clearFile}
                            className="absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center shadow"
                            style={{ background: "var(--color-navy)", color: "white" }}>
                      <X size={14} />
                    </button>
                    <div className="flex items-center gap-2 px-4 py-2 border-t border-navy/8"
                         style={{ color: "var(--color-navy)", opacity: 0.5 }}>
                      <ImageIcon size={13} />
                      <span className="text-xs">{imageFile?.name}</span>
                    </div>
                  </div>
                )}

                {/* Image file but no preview (scanned PDF fallback) */}
                {isImage && !imagePreview && (
                  <div className="flex items-center gap-3 px-4 py-3 rounded-2xl border border-navy/10 bg-white">
                    <FileScan size={20} style={{ color: "var(--color-gold)" }} />
                    <div className="flex-1">
                      <p className="text-sm font-medium" style={{ color: "var(--color-navy)" }}>{imageFile?.name}</p>
                      <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                        {locale === "ar" ? "PDF ممسوح — سيُرسل للتحليل" :
                         locale === "en" ? "Scanned PDF — will be sent for analysis" :
                         "PDF scanné — sera envoyé à l'analyse"}
                      </p>
                    </div>
                    <button onClick={clearFile} style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                      <X size={16} />
                    </button>
                  </div>
                )}

                {/* Textarea (only when no image) */}
                {!isImage && (
                  <div>
                    <label className="block text-sm font-semibold mb-2" style={{ color: "var(--color-navy)" }}>
                      {t.legal.paste_label}
                    </label>
                    <textarea
                      value={contract}
                      onChange={e => setContract(e.target.value)}
                      placeholder={t.legal.paste_placeholder}
                      rows={18}
                      className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none leading-relaxed"
                      style={{ ...inputStyle, fontFamily: "var(--font-inter)" }}
                    />
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <input ref={fileRef} type="file"
                         accept=".txt,.text,.pdf,application/pdf,image/png,image/jpeg,image/jpg,.png,.jpg,.jpeg"
                         className="hidden" onChange={onFile} />
                  <button onClick={() => fileRef.current?.click()} disabled={extracting}
                          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-colors hover:border-navy/40 disabled:opacity-50"
                          style={{ borderColor: "oklch(0.18 0.065 260 / 0.2)", color: "var(--color-navy)", background: "white" }}>
                    {extracting
                      ? <><Loader2 size={14} className="animate-spin" style={{ color: "var(--color-gold)" }} />
                          {locale === "ar" ? "استخراج النص…" : locale === "en" ? "Extracting…" : "Extraction…"}</>
                      : <><Upload size={14} style={{ color: "var(--color-gold)" }} />{uploadLabel}</>}
                  </button>
                  {!isImage && contract && (
                    <span className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                      {contract.length.toLocaleString()} {locale === "ar" ? "حرف" : locale === "en" ? "chars" : "caractères"}
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-semibold mb-2" style={{ color: "var(--color-navy)" }}>
                  {t.legal.chat_label}
                </label>
                <textarea
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder={t.legal.placeholder}
                  rows={8}
                  className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none leading-relaxed"
                  style={{ ...inputStyle, fontFamily: "var(--font-inter)" }}
                />
              </div>
            )}

            <button onClick={analyze} disabled={!canSubmit}
                    className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-base transition-all hover:opacity-90 disabled:opacity-40"
                    style={{ background: "var(--color-navy)", color: "white" }}>
              {analyzing
                ? <><Loader2 size={18} className="animate-spin" /> {t.legal.analyzing}</>
                : <><Scale size={18} /> {t.legal.analyze}</>}
            </button>

            {/* Example contracts */}
            <div className="rounded-2xl border border-navy/8 bg-white p-5">
              <p className="text-xs font-bold uppercase tracking-widest mb-3"
                 style={{ color: "var(--color-gold)" }}>
                {locale === "ar" ? "أنواع العقود الشائعة" : locale === "en" ? "Common contract types" : "Types de contrats courants"}
              </p>
              <div className="space-y-1">
                {examples.map((ex) => (
                  <button key={ex}
                          onClick={() => { setMode("question"); setQuestion(ex); }}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-left hover:bg-navy/4 transition-colors"
                          style={{ color: "var(--color-navy)", opacity: 0.7 }}>
                    <ChevronRight size={12} style={{ color: "var(--color-gold)", flexShrink: 0 }} />
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Result */}
          <div className="lg:col-span-2">
            <div className="sticky top-24">
              {error && (
                <div className="flex items-start gap-3 p-4 rounded-2xl mb-4"
                     style={{ background: "oklch(0.60 0.22 27 / 0.08)", border: "1px solid oklch(0.60 0.22 27 / 0.2)" }}>
                  <AlertTriangle size={16} style={{ color: "var(--color-terra)", flexShrink: 0, marginTop: 2 }} />
                  <p className="text-sm" style={{ color: "var(--color-terra)" }}>{error}</p>
                </div>
              )}

              {analyzing && (
                <div className="rounded-2xl border border-navy/8 bg-white p-8 text-center">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                       style={{ background: "oklch(0.68 0.17 47 / 0.1)" }}>
                    <Scale size={24} className="animate-pulse" style={{ color: "var(--color-gold)" }} />
                  </div>
                  <p className="font-semibold mb-1" style={{ color: "var(--color-navy)" }}>{t.legal.analyzing}</p>
                  <p className="text-sm" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                    {locale === "ar" ? "قد يستغرق هذا لحظة…" : locale === "en" ? "This may take a moment…" : "Cela peut prendre un moment…"}
                  </p>
                </div>
              )}

              {result && !analyzing && (
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div style={{ width: 32, height: 32, borderRadius: 10, background: "oklch(0.68 0.17 47 / 0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Scale size={16} style={{ color: "var(--color-gold)" }} />
                    </div>
                    <p className="font-bold text-sm" style={{ color: "var(--color-navy)" }}>{t.legal.result_title}</p>
                  </div>
                  <div className="max-h-[72vh] overflow-y-auto pr-1">
                    <LegalResult result={result} />
                  </div>
                </div>
              )}

              {!result && !analyzing && !error && (
                <div className="rounded-2xl border border-dashed border-navy/15 p-10 text-center">
                  <FileText size={40} className="mx-auto mb-4" style={{ color: "var(--color-navy)", opacity: 0.15 }} />
                  <p className="text-sm" style={{ color: "var(--color-navy)", opacity: 0.35 }}>
                    {t.legal.empty_hint}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
