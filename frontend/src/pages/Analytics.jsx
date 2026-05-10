import { useEffect, useState } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, CartesianGrid,
} from "recharts";
import { stats } from "../services/api";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";

const COLORS = ["#f18534","#445576","#091940","#9199ac","#ead5c8","#e07b28","#3a4a6e"];

export default function Analytics() {
  const { t } = useLang();
  const [scatter, setScatter]   = useState([]);
  const [heatmap, setHeatmap]   = useState([]);
  const [amenity, setAmenity]   = useState([]);
  const [dist, setDist]         = useState([]);
  const [trend, setTrend]       = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      stats.priceHeatmap(), stats.amenities(), stats.priceDistribution(), stats.monthlyTrend(),
    ]).then(([hm, am, pd, tr]) => {
      setHeatmap(hm);
      setAmenity(Object.entries(am).map(([k, v]) => ({
        subject: k.replace("has_", "").replace("_", " "),
        value: v,
      })));
      setDist(pd);
      const last24 = tr.slice(-24).map(r => ({ ...r, label: `${r.year}-${String(r.month).padStart(2,"0")}` }));
      setTrend(last24);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const govs = [...new Set(heatmap.map(r => r.gouvernerat))].slice(0, 8);
  const types = [...new Set(heatmap.map(r => r.type))].slice(0, 5);

  return (
    <div>
      <TopBar title={t.pages.analytics.title} subtitle={t.pages.analytics.subtitle} />
      <div style={{ padding: 28 }}>

        {/* Price Distribution */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.analytics_page.price_dist}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 220 }} /> : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={dist}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(9,25,64,0.06)" />
                  <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#9199ac" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#9199ac" }} />
                  <Tooltip formatter={v => v.toLocaleString("fr-TN")} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {dist.map((_, i) => <Cell key={i} fill={i < 4 ? "#f18534" : i < 8 ? "#445576" : "#091940"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="card">
            <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.analytics_page.amenities_profile}</h3></div>
            {loading ? <div className="skeleton" style={{ height: 220 }} /> : (
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={amenity}>
                  <PolarGrid stroke="rgba(9,25,64,0.08)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: "#091940" }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
                  <Radar name="%" dataKey="value" stroke="#f18534" fill="#f18534" fillOpacity={0.18} />
                  <Tooltip formatter={v => `${v}%`} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Heatmap matrix */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.analytics_page.heatmap}</h3></div>
          {loading ? <div className="skeleton" style={{ height: 200 }} /> : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ borderCollapse: "collapse", minWidth: "100%", fontSize: 12 }}>
                <thead>
                  <tr>
                    <th style={{ padding: "8px 12px", textAlign: "left", color: "var(--modern)", fontWeight: 500 }}>Gouvernerat</th>
                    {types.map(typ => <th key={typ} style={{ padding: "8px 12px", color: "var(--modern)", fontWeight: 500, textAlign: "center" }}>{typ}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {govs.map(g => {
                    const maxP = Math.max(...heatmap.filter(r => r.gouvernerat === g).map(r => r.avg_prix || 0));
                    return (
                      <tr key={g}>
                        <td style={{ padding: "7px 12px", fontWeight: 500, color: "var(--strong)" }}>{g}</td>
                        {types.map(typ => {
                          const cell = heatmap.find(r => r.gouvernerat === g && r.type === typ);
                          const val  = cell?.avg_prix;
                          const pct  = maxP && val ? val / maxP : 0;
                          return (
                            <td key={typ} style={{
                              padding: "7px 12px", textAlign: "center",
                              background: val ? `rgba(241,133,52,${0.1 + pct * 0.75})` : "transparent",
                              borderRadius: 4, color: "var(--strong)",
                            }}>
                              {val ? `${(val / 1000).toFixed(0)}K` : "—"}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Monthly timeline */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{t.analytics_page.timeline}</h3></div>
          {loading ? <div className="skeleton" style={{ height: 200 }} /> : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(9,25,64,0.06)" />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#9199ac" }} />
                <YAxis tick={{ fontSize: 10, fill: "#9199ac" }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#445576" strokeWidth={2} dot={false} name={t.analytics_page.publications} />
                <Line type="monotone" dataKey="avg_prix" stroke="var(--dynamic)" strokeWidth={1.5} dot={false} name={t.analytics_page.avg_price} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Price estimation widget */}
        <PriceEstimator />
      </div>
    </div>
  );
}

function PriceEstimator() {
  const { t } = useLang();
  const ap = t.analytics_page;
  const [form, setForm] = useState({ gouvernerat: "", type: "Appartement", surface: 100, pieces: 3 });
  const [result, setResult] = useState(null);

  const GOVS = ["Tunis","Ariana","Ben Arous","La Manouba","Nabeul","Zaghouan","Bizerte","Béja","Jendouba","Le Kef","Siliana","Sousse","Monastir","Mahdia","Sfax","Kairouan","Kasserine","Sidi Bouzid","Gabès","Medenine","Tataouine","Gafsa","Tozeur","Kébili"];
  const TYPES = ["Appartement","Villa","Maison","Studio","Terrain","Bureau","Commerce","Ferme"];

  function estimate() {
    const basePrice = { Tunis: 3200, Ariana: 2800, "Ben Arous": 2600, Nabeul: 2400, Sousse: 2200, Sfax: 1800, Monastir: 2000 };
    const typeCoeff = { Appartement: 1, Villa: 1.5, Maison: 1.2, Studio: 0.9, Terrain: 0.4, Bureau: 1.3, Commerce: 1.4, Ferme: 0.6 };
    const ppm = (basePrice[form.gouvernerat] || 1500) * (typeCoeff[form.type] || 1);
    const est = Math.round(ppm * form.surface);
    setResult({ estimation: est, min: Math.round(est * 0.85), max: Math.round(est * 1.15), ppm: Math.round(ppm) });
  }

  return (
    <div className="card">
      <div className="section-header"><h3 style={{ margin: 0, fontSize: 15 }}>{ap.estimator_title}</h3></div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 16 }}>
        {[
          { label: ap.label_gov,     key: "gouvernerat", type: "select", options: GOVS },
          { label: ap.label_type,    key: "type",        type: "select", options: TYPES },
          { label: ap.label_surface, key: "surface",     type: "number" },
          { label: ap.label_pieces,  key: "pieces",      type: "number" },
        ].map(f => (
          <div key={f.key}>
            <label style={{ display: "block", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>{f.label}</label>
            {f.type === "select" ? (
              <select value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }}>
                <option value="">—</option>
                {f.options.map(o => <option key={o}>{o}</option>)}
              </select>
            ) : (
              <input type="number" value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: +e.target.value }))}
                style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }} />
            )}
          </div>
        ))}
      </div>
      <button className="btn btn-primary" onClick={estimate}>{ap.estimator_btn}</button>
      {result && (
        <div style={{ marginTop: 16, padding: "16px 20px", background: "var(--bg)", borderRadius: 10, display: "flex", gap: 32 }}>
          <div>
            <div style={{ fontSize: 11, color: "var(--modern)" }}>{ap.estimation}</div>
            <div style={{ fontFamily: "Playfair Display,serif", fontSize: 26, fontWeight: 800, color: "var(--dynamic)" }}>
              {result.estimation.toLocaleString("fr-TN")} TND
            </div>
          </div>
          <div style={{ display: "flex", gap: 20 }}>
            <div><div style={{ fontSize: 11, color: "var(--modern)" }}>{ap.range_low}</div><div style={{ fontWeight: 600 }}>{result.min.toLocaleString("fr-TN")}</div></div>
            <div><div style={{ fontSize: 11, color: "var(--modern)" }}>{ap.range_high}</div><div style={{ fontWeight: 600 }}>{result.max.toLocaleString("fr-TN")}</div></div>
            <div><div style={{ fontSize: 11, color: "var(--modern)" }}>{ap.price_m2}</div><div style={{ fontWeight: 600 }}>{result.ppm.toLocaleString("fr-TN")} TND</div></div>
          </div>
        </div>
      )}
    </div>
  );
}
