"use client";
import Link from "next/link";
import { Map, AlertCircle } from "lucide-react";
import { useLang } from "@/contexts/lang";
import { NavbarLight } from "@/components/navbar";

export default function MapPage() {
  const { t } = useLang();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--color-cream)" }}>
      <NavbarLight />

      {/* Page hero */}
      <div className="shrink-0" style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260) 0%, oklch(0.22 0.055 255) 100%)" }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                 style={{ background: "rgba(255,255,255,0.1)" }}>
              <Map size={18} style={{ color: "var(--color-gold)" }} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white" style={{ fontFamily: "var(--font-display)" }}>
                {t.map.title}
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.45)" }}>{t.map.info}</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            {[
              { color: "var(--color-gold)",    label: t.map.for_sale },
              { color: "var(--color-primary)", label: t.map.for_rent },
              { color: "var(--color-terra)",   label: t.map.anomaly },
            ].map(({ color, label }) => (
              <span key={label} className="flex items-center gap-1.5 text-xs font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                {label}
              </span>
            ))}
            <Link href="/search"
                  className="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:bg-white/20"
                  style={{ background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.75)", border: "1px solid rgba(255,255,255,0.15)" }}>
              {t.map.listings}
            </Link>
          </div>
        </div>
      </div>

      {/* Map iframe */}
      <div className="flex-1 relative" style={{ minHeight: "calc(100vh - 170px)" }}>
        <iframe
          src="/api/agents/outliers/map"
          className="absolute inset-0 w-full h-full border-0"
          title={t.map.title}
          loading="lazy"
        />
        <noscript>
          <div className="absolute inset-0 flex items-center justify-center" style={{ background: "var(--color-sand)" }}>
            <div className="text-center">
              <Map size={40} style={{ color: "var(--color-gold)", margin: "0 auto 12px" }} />
              <p className="font-semibold" style={{ color: "var(--color-navy)" }}>{t.map.noscript}</p>
            </div>
          </div>
        </noscript>
      </div>
    </div>
  );
}
