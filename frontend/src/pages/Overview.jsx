import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend,
} from "recharts";
import { stats } from "../services/api";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";

const COLORS = ["#f18534","#445576","#091940","#9199ac","#ead5c8","#e07b28","#3a4a6e","#6b7a9a"];

function KPICard({ label, value, delta, icon, loading }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (!value) return;
    const target = typeof value === "number" ? value : 0;
    let start = 0;
    const step = target / 60;
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setDisplay(target); clearInterval(timer); }
      else setDisplay(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <motion.div className="card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
      style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
      {loading ? (
        <>
          <div className="skeleton" style={{ height: 14, width: "60%" }} />
          <div className="skeleton" style={{ height: 32, width: "80%" }} />
        </>
      ) : (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <span style={{ fontSize: 11, color: "var(--modern)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</span>
            <span style={{ fontSize: 20 }}>{icon}</span>
          </div>
          <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 28, color: "var(--strong)" }}>
            {typeof value === "number" ? display.toLocaleString("fr-TN") : value}
          </div>
          {delta !== undefined && (
            <div style={{ fontSize: 12, color: delta >= 0 ? "#52c41a" : "#ff4d4f" }}>
              {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}%
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}

function InsightCard({ insight }) {
  const colors = { tendance: "#445576", opportunite: "#52c41a", anomalie: "#ff4d4f", quartier: "#f18534", prediction: "#9b59b6" };
  return (
    <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
      style={{ display: "flex", gap: 12, padding: "12px 16px", background: "#fff", borderRadius: 10, border: "1px solid var(--border)", alignItems: "flex-start" }}>
      <span style={{ fontSize: 20, flexShrink: 0 }}>{insight.icon}</span>
      <div>
        <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", color: colors[insight.type] || "var(--modern)", fontWeight: 600, marginBottom: 3 }}>{insight.type}</div>
        <div style={{ fontSize: 13, color: "var(--strong)", lineHeight: 1.5 }}>{insight.text}</div>
      </div>
    </motion.div>
  );
}

export default function Overview() {
  const { t } = useLang();
  const [ov, setOv]         = useState(null);
  const [govData, setGov]   = useState([]);
  const [typeData, setType] = useState([]);
  const [trend, setTrend]   = useState([]);
  const [insightData, setInsights] = useState([]);
  const [etrei, setEtrei]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      stats.overview(), stats.byGouvernerat(), stats.byType(),
      stats.monthlyTrend(), stats.insights(), stats.etrei(),
    ]).then(([o, g, t, tr, ins, et]) => {
      setOv(o); setGov(g.slice(0, 10)); setType(t.slice(0, 6));
      const last12 = tr.slice(-12).map(r => ({ ...r, label: `${r.year}-${String(r.month).padStart(2,"0")}` }));
      setTrend(last12); setInsights(ins); setEtrei(et);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const kpis = [
    { label: t.kpis.total,         value: ov?.total,              icon: "🏠", delta: 12.4 },
    { label: t.kpis.gouvernerats,  value: ov?.gouvernerats_count, icon: "🗺️" },
    { label: t.kpis.avg_prix,      value: ov?.avg_prix,            icon: "💰" },
    { label: t.kpis.avg_surface,   value: ov?.avg_surface,         icon: "📐" },
    { label: t.kpis.haut_standing, value: ov?.haut_standing_rate,  icon: "⭐" },
    { label: t.kpis.entourage,     value: ov?.bon_entourage_avg,   icon: "🏘️" },
  ];

  return (
    <div>
      <TopBar title={t.pages.overview.title} subtitle={t.pages.overview.subtitle} />
      <div style={{ padding: 28 }}>

        {/* ETREI index */}
        {etrei && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{ background: "var(--strong)", borderRadius: 12, padding: "16px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 20 }}>
            <div>
              <div style={{ color: "#9199ac", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>{t.sections.etrei}</div>
              <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 36, color: "var(--dynamic)", marginTop: 4 }}>{etrei.global?.index}</div>
              <div style={{ color: "#fff", fontSize: 13 }}>{etrei.global?.label}</div>
            </div>
            <div style={{ flex: 1, height: 4, background: "rgba(255,255,255,0.1)", borderRadius: 2, marginLeft: 20 }}>
              <div style={{ height: 4, width: `${Math.min(etrei.global?.index, 100)}%`, background: "var(--dynamic)", borderRadius: 2 }} />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#52c41a", animation: "pulse 2s infinite" }} />
              <span style={{ color: "#9199ac", fontSize: 12 }}>{t.common.live}</span>
            </div>
          </motion.div>
        )}

        {/* KPI grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 28 }}>
          {kpis.map((k, i) => <KPICard key={i} {...k} loading={loading} />)}
        </div>

        {/* Charts row 1 */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20, marginBottom: 20 }}>
          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.overview_page.top10}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 240 }} /> : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={govData} layout="vertical" margin={{ left: 60 }}>
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#9199ac" }} />
                  <YAxis dataKey="gouvernerat" type="category" tick={{ fontSize: 11, fill: "#091940" }} width={90} />
                  <Tooltip formatter={v => v.toLocaleString("fr-TN")} />
                  <Bar dataKey="count" fill="var(--dynamic)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.overview_page.by_type}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 240 }} /> : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={typeData} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={85} innerRadius={45} paddingAngle={3}>
                    {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => v.toLocaleString("fr-TN")} />
                  <Legend iconSize={10} formatter={v => <span style={{ fontSize: 11 }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Charts row 2 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.overview_page.monthly}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 200 }} /> : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(9,25,64,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#9199ac" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#9199ac" }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="var(--dynamic)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.overview_page.avg_price_gov}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 200 }} /> : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 200, overflowY: "auto" }}>
                {govData.slice(0, 8).map(g => {
                  const maxP = Math.max(...govData.map(x => x.avg_prix || 0));
                  const pct  = maxP ? (g.avg_prix / maxP) * 100 : 0;
                  return (
                    <div key={g.gouvernerat} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                      <div style={{ width: 80, fontSize: 11, color: "var(--strong)", flexShrink: 0 }}>{g.gouvernerat}</div>
                      <div style={{ flex: 1, height: 8, background: "rgba(9,25,64,0.06)", borderRadius: 4 }}>
                        <div style={{ height: 8, width: `${pct}%`, background: "var(--dynamic)", borderRadius: 4 }} />
                      </div>
                      <div style={{ width: 80, fontSize: 11, color: "var(--modern)", textAlign: "right" }}>
                        {(g.avg_prix / 1000).toFixed(0)}K
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* AI Insights */}
        <div className="card">
          <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.overview_page.insights}</h3></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 10 }}>
            {loading
              ? Array(4).fill(0).map((_, i) => <div key={i} className="skeleton" style={{ height: 72 }} />)
              : insightData.map((ins, i) => <InsightCard key={i} insight={ins} />)
            }
          </div>
        </div>
      </div>
    </div>
  );
}
