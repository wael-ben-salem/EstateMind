"use client";
import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, Loader2, CheckCircle2 } from "lucide-react";
import { useLang } from "@/contexts/lang";

interface Props {
  listingId: number; prix: number | null; surface: number | null;
  pieces: number | null; gouvernerat: string | null;
  type: string | null; contrat: string | null;
}

interface PriceResult {
  predicted_price?: number;
  model_name?: string;
  error?: string;
}
interface AnomalyResult {
  is_anomaly?: number;           // 0 or 1
  opportunity_label?: string;   // human-readable label from agent
  anomaly_confidence?: number;
  predicted_price?: number;
  actual_price?: number;
  price_gap_pct?: number;
  error?: string;
}

const NUM_LOCALE: Record<string, string> = { fr: "fr-TN", ar: "ar-TN", en: "en-US" };

export function AiAnalysis({ listingId, prix, surface, pieces, gouvernerat, type, contrat }: Props) {
  const { t, locale } = useLang();
  const [price,   setPrice]   = useState<PriceResult | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalyResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const payload = { surface, pieces, gouvernerat, type, contrat, ...(prix ? { prix } : {}) };
    const fmtPayload = JSON.stringify(payload);
    const headers = { "Content-Type": "application/json" };

    const priceReq = fetch("/api/agents/price/predict", { method: "POST", headers, body: fmtPayload })
      .then(r => r.json())
      .then(d => setPrice(d))
      .catch(() => setPrice({ error: "unavailable" }));

    // Anomaly requires prix — skip if null
    const anomalyReq = prix
      ? fetch("/api/agents/anomaly/score", { method: "POST", headers, body: fmtPayload })
          .then(r => r.json())
          .then(d => setAnomaly(d))
          .catch(() => setAnomaly({ error: "unavailable" }))
      : Promise.resolve(setAnomaly(null));

    Promise.allSettled([priceReq, anomalyReq]).finally(() => setLoading(false));
  }, [listingId]);

  const fmtNum = (n: number) =>
    new Intl.NumberFormat(NUM_LOCALE[locale] ?? "fr-TN").format(Math.round(n));

  const isAnomaly = !!anomaly?.is_anomaly;

  return (
    <div className="rounded-2xl bg-white border border-navy/8 p-5 shadow-sm">
      <h3 className="font-semibold text-sm mb-4" style={{ color: "var(--color-navy)" }}>{t.listing.ai_title}</h3>
      <div className="space-y-3">

        {/* ── Price prediction ── */}
        <div className="rounded-xl p-4" style={{ background: "oklch(0.47 0.18 22 / 0.07)" }}>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={14} style={{ color: "var(--color-primary)" }} />
            <span className="text-xs font-semibold" style={{ color: "var(--color-navy)" }}>{t.listing.ai_price_title}</span>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              <Loader2 size={12} className="animate-spin" /> {t.listing.ai_price_loading}
            </div>
          ) : price?.error ? (
            <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{t.listing.ai_unavailable}</p>
          ) : price?.predicted_price ? (
            <>
              <p className="font-bold text-base" style={{ color: "var(--color-primary)" }}>
                {fmtNum(price.predicted_price)} TND
              </p>
              {price.model_name && (
                <p className="text-[10px] mt-0.5" style={{ color: "var(--color-navy)", opacity: 0.35 }}>
                  {price.model_name}
                </p>
              )}
              {prix && price.predicted_price && (
                <p className="text-xs mt-1.5 font-medium"
                   style={{ color: prix > price.predicted_price * 1.1 ? "var(--color-terra)"
                                 : prix < price.predicted_price * 0.9 ? "oklch(0.5 0.15 145)"
                                 : "var(--color-navy)" }}>
                  {prix > price.predicted_price * 1.1 ? t.listing.ai_overpriced
                   : prix < price.predicted_price * 0.9 ? t.listing.ai_good_deal
                   : t.listing.ai_fair_price}
                </p>
              )}
            </>
          ) : (
            <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{t.listing.ai_no_data}</p>
          )}
        </div>

        {/* ── Anomaly detection ── */}
        <div className="rounded-xl p-4" style={{ background: "oklch(0.50 0.20 18 / 0.07)" }}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} style={{ color: "var(--color-terra)" }} />
            <span className="text-xs font-semibold" style={{ color: "var(--color-navy)" }}>{t.listing.ai_anomaly_title}</span>
          </div>
          {!prix ? (
            <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              {locale === "ar" ? "السعر مطلوب للتحليل" : locale === "en" ? "Price required for analysis" : "Prix requis pour l'analyse"}
            </p>
          ) : loading ? (
            <div className="flex items-center gap-2 text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              <Loader2 size={12} className="animate-spin" /> {t.listing.ai_anomaly_loading}
            </div>
          ) : anomaly?.error ? (
            <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{t.listing.ai_unavailable}</p>
          ) : anomaly ? (
            <>
              <div className="flex items-center gap-2">
                {isAnomaly
                  ? <AlertTriangle size={13} style={{ color: "var(--color-terra)", flexShrink: 0 }} />
                  : <CheckCircle2 size={13} style={{ color: "oklch(0.5 0.15 145)", flexShrink: 0 }} />}
                <span className="text-xs font-medium" style={{ color: "var(--color-navy)" }}>
                  {isAnomaly ? t.listing.ai_anomaly_detected : t.listing.ai_normal}
                </span>
              </div>
              {anomaly.opportunity_label && (
                <p className="text-xs mt-1.5 font-medium" style={{ color: isAnomaly ? "var(--color-terra)" : "oklch(0.5 0.15 145)" }}>
                  {anomaly.opportunity_label}
                </p>
              )}
              {anomaly.price_gap_pct !== undefined && (
                <p className="text-xs mt-1" style={{ color: "var(--color-navy)", opacity: 0.45 }}>
                  {anomaly.price_gap_pct > 0 ? "+" : ""}{anomaly.price_gap_pct.toFixed(1)}%{" "}
                  {locale === "ar" ? "عن السعر المتوقع" : locale === "en" ? "vs. predicted price" : "vs. prix estimé"}
                </p>
              )}
              {anomaly.anomaly_confidence !== undefined && (
                <p className="text-xs mt-0.5" style={{ color: "var(--color-navy)", opacity: 0.35 }}>
                  {locale === "ar" ? "ثقة" : locale === "en" ? "Confidence" : "Confiance"}: {Math.round(anomaly.anomaly_confidence * 100)}%
                </p>
              )}
            </>
          ) : (
            <p className="text-xs" style={{ color: "var(--color-navy)", opacity: 0.4 }}>{t.listing.ai_no_data}</p>
          )}
        </div>
      </div>
    </div>
  );
}
