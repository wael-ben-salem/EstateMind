import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { pipeline as pipeApi, stats } from "../services/api";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";

const SCRAPERS = [
  { name: "Tayara.tn",      status: "active",  count: 204745, last: "2h ago",  icon: "✅" },
  { name: "Immobilier.tn",  status: "locked",  count: 45000,  eta: "Q3 2026",  icon: "🔒" },
  { name: "Mubawab.tn",     status: "locked",  count: 30000,  eta: "Q3 2026",  icon: "🔒" },
  { name: "Afariat.com",    status: "beta",    count: 20000,  eta: "Beta",     icon: "🔶" },
  { name: "OLX.tn",         status: "planned", count: 15000,  eta: "Q4 2026",  icon: "📅" },
  { name: "Avito.tn",       status: "planned", count: 10000,  eta: "Q4 2026",  icon: "📅" },
];

const STATUS_COLOR = { active: "#52c41a", locked: "#9199ac", beta: "var(--dynamic)", planned: "#445576" };

export default function Scrapers() {
  const { t } = useLang();
  const [pipeStatus, setPipeStatus] = useState(null);
  const [showModal, setShowModal]   = useState(false);
  const [overview, setOverview]     = useState(null);

  useEffect(() => {
    pipeApi.status().then(setPipeStatus).catch(() => {});
    stats.overview().then(setOverview).catch(() => {});
  }, []);

  async function triggerPipeline() {
    try {
      await pipeApi.trigger();
      setShowModal(true);
    } catch {
      alert(t.scrapers_page.airflow_error);
    }
  }

  return (
    <div>
      <TopBar title={t.pages.scrapers.title} subtitle={t.pages.scrapers.subtitle} />
      <div style={{ padding: 28 }}>

        {/* Stats banner */}
        {overview && (
          <div style={{ background: "var(--strong)", borderRadius: 12, padding: "16px 24px", marginBottom: 24, display: "flex", gap: 40 }}>
            {[
              { label: t.scrapers_page.total,        value: overview.total?.toLocaleString("fr-TN") },
              { label: t.scrapers_page.sources,      value: "1 / 6" },
              { label: t.scrapers_page.success_rate, value: "98.2%" },
              { label: t.scrapers_page.last_update,  value: "2h ago" },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ color: "#9199ac", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
                <div style={{ color: "#fff", fontFamily: "Playfair Display,serif", fontWeight: 700, fontSize: 22, marginTop: 2 }}>{value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Scraper grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 28 }}>
          {SCRAPERS.map((s, i) => (
            <motion.div key={s.name} className="card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              style={{ opacity: s.status !== "active" ? 0.75 : 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{s.name}</div>
                  <span style={{ display: "inline-block", padding: "2px 10px", borderRadius: 12, fontSize: 11, fontWeight: 600, background: `${STATUS_COLOR[s.status]}20`, color: STATUS_COLOR[s.status] }}>
                    {s.icon} {t.scrapers_page[`status_${s.status}`]}
                  </span>
                </div>
                {s.status === "active" && (
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#52c41a", boxShadow: "0 0 6px #52c41a", marginTop: 4 }} />
                )}
              </div>

              <div style={{ display: "flex", gap: 20 }}>
                <div>
                  <div style={{ fontSize: 10, color: "var(--modern)" }}>{t.scrapers_page.listings}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--dynamic)" }}>~{(s.count / 1000).toFixed(0)}K</div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "var(--modern)" }}>{s.status === "active" ? t.scrapers_page.last_run : t.scrapers_page.available}</div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "var(--strong)" }}>{s.last || s.eta}</div>
                </div>
              </div>

              {s.status === "active" && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>
                    <span>{t.scrapers_page.success_label}</span><span style={{ color: "#52c41a", fontWeight: 600 }}>98.2%</span>
                  </div>
                  <div style={{ height: 4, background: "rgba(9,25,64,0.06)", borderRadius: 2 }}>
                    <div style={{ height: 4, width: "98.2%", background: "#52c41a", borderRadius: 2 }} />
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Tayara detailed stats */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.scrapers_page_extra.tayara_stats}</h3></div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {[
                { icon: "📄", label: t.scrapers_page_extra.pages_crawled, value: "12,847" },
                { icon: "⚡", label: t.scrapers_page_extra.avg_time, value: "1.2s" },
                { icon: "❌", label: t.scrapers_page_extra.errors_404, value: "124" },
                { icon: "⏱️", label: t.scrapers_page_extra.last_duration, value: "4h 32m" },
              ].map(({ icon, label, value }) => (
                <div key={label} style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 10, display: "flex", gap: 12, alignItems: "center" }}>
                  <span style={{ fontSize: 22 }}>{icon}</span>
                  <div>
                    <div style={{ fontSize: 11, color: "var(--modern)" }}>{label}</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "var(--strong)" }}>{value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 13, color: "var(--modern)", marginBottom: 4 }}>{t.scrapers_page_extra.next_run}</div>
              <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 28, color: "var(--strong)" }}>06:00</div>
              <div style={{ fontSize: 12, color: "var(--modern)" }}>{t.scrapers_page_extra.tomorrow_morning}</div>
            </div>
            <button onClick={triggerPipeline} className="btn btn-primary" style={{ width: "100%", justifyContent: "center", gap: 8, fontSize: 14 }}>
              ▶ {t.scrapers_page_extra.run_pipeline}
            </button>
            {pipeStatus && (
              <div style={{ fontSize: 11, color: pipeStatus.is_running ? "#52c41a" : "var(--modern)", textAlign: "center" }}>
                {pipeStatus.is_running ? `🟢 ${t.scrapers_page_extra.pipeline_running}` : `${t.scrapers_page_extra.last_run_label} ${pipeStatus.last_run || "—"}`}
              </div>
            )}
          </div>
        </div>
      </div>

      {showModal && <PipelineModal onClose={() => setShowModal(false)} />}
    </div>
  );
}

function PipelineModal({ onClose }) {
  const { t } = useLang();
  const STEPS = [
    { id: "fetch_urls",    label: "Fetch URLs",      desc: t.scrapers_page_extra.step_fetch_desc },
    { id: "parse_html",    label: "Parse HTML",      desc: t.scrapers_page_extra.step_parse_desc },
    { id: "validate",      label: "Validate Data",   desc: t.scrapers_page_extra.step_validate_desc },
    { id: "deduplicate",   label: "Deduplicate",     desc: t.scrapers_page_extra.step_dedup_desc },
    { id: "enrich",        label: "Enrich",          desc: t.scrapers_page_extra.step_enrich_desc },
    { id: "load_db",       label: "Load to DB",      desc: t.scrapers_page_extra.step_load_desc },
    { id: "notify",        label: "Notify",          desc: t.scrapers_page_extra.step_notify_desc },
  ];
  const [statuses, setStatuses] = useState(STEPS.map(() => "queued"));

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i >= STEPS.length) { clearInterval(timer); return; }
      setStatuses(s => s.map((st, idx) => idx === i ? "running" : idx < i ? "success" : "queued"));
      setTimeout(() => {
        setStatuses(s => s.map((st, idx) => idx === i ? "success" : st));
        i++;
      }, 2000);
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  const color = { queued: "#9199ac", running: "#f18534", success: "#52c41a", failed: "#ff4d4f" };
  const icon  = { queued: "○", running: "⟳", success: "✓", failed: "✗" };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(9,25,64,0.5)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="card" style={{ width: 520, maxHeight: "80vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0 }}>{t.scrapers_page_extra.modal_title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 18, color: "var(--modern)" }}>✕</button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {STEPS.map((step, i) => (
            <div key={step.id} style={{ display: "flex", gap: 14, alignItems: "center", padding: "10px 14px", background: statuses[i] === "running" ? "rgba(241,133,52,0.08)" : "var(--bg)", borderRadius: 8, border: `1px solid ${statuses[i] === "running" ? "rgba(241,133,52,0.3)" : "var(--border)"}`, transition: "all 0.3s" }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: `${color[statuses[i]]}20`, color: color[statuses[i]], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, flexShrink: 0 }}>
                {icon[statuses[i]]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--strong)" }}>{step.label}</div>
                <div style={{ fontSize: 11, color: "var(--modern)" }}>{step.desc}</div>
              </div>
              <span style={{ fontSize: 11, color: color[statuses[i]], fontWeight: 600 }}>{statuses[i].toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
