import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { listings as api } from "../services/api";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";

const GOVS  = ["","Tunis","Ariana","Ben Arous","La Manouba","Nabeul","Zaghouan","Bizerte","Béja","Jendouba","Le Kef","Siliana","Sousse","Monastir","Mahdia","Sfax","Kairouan","Kasserine","Sidi Bouzid","Gabès","Medenine","Tataouine","Gafsa","Tozeur","Kébili"];
const TYPES = ["","Appartement","Villa","Maison","Studio","Terrain","Bureau","Commerce","Ferme"];

function PropertyImage({ src, style, type }) {
  const [err, setErr] = useState(!src);
  useEffect(() => { setErr(!src); }, [src]);
  if (err) {
    return (
      <div style={{ ...style, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "oklch(0.96 0.012 60)", gap: 6 }}>
        <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="10" y="25" width="32" height="22" rx="2" fill="oklch(0.82 0.035 60)"/>
          <polygon points="5,27 26,9 47,27" fill="oklch(0.76 0.045 60)"/>
          <rect x="21" y="33" width="10" height="14" rx="1" fill="oklch(0.7 0.04 60)"/>
          <rect x="13" y="30" width="7" height="6" rx="1" fill="oklch(0.92 0.015 60)"/>
          <rect x="32" y="30" width="7" height="6" rx="1" fill="oklch(0.92 0.015 60)"/>
        </svg>
        <span style={{ fontSize: 10, color: "oklch(0.62 0.02 60)", fontFamily: "Inter,sans-serif", fontWeight: 500 }}>
          {type || "—"}
        </span>
      </div>
    );
  }
  return <img src={src} alt="" style={style} onError={() => setErr(true)} />;
}

function ScoreBar({ score }) {
  const color = score >= 80 ? "#52c41a" : score >= 60 ? "#f18534" : score >= 40 ? "#445576" : "#ff4d4f";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ flex: 1, height: 4, background: "rgba(9,25,64,0.08)", borderRadius: 2 }}>
        <div style={{ height: 4, width: `${score}%`, background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 600, color, minWidth: 28 }}>{score}</span>
    </div>
  );
}

export default function Listings() {
  const { t } = useLang();
  const [params, setParams] = useSearchParams();
  const [data, setData]     = useState([]);
  const [total, setTotal]   = useState(0);
  const [pages, setPages]   = useState(1);
  const [loading, setLoading] = useState(true);
  const [view, setView]     = useState("table");
  const [selected, setSelected] = useState(null);
  const [scores, setScores] = useState({});
  const [filtersOpen, setFiltersOpen] = useState(true);

  const page    = parseInt(params.get("page") || "1");
  const limit   = parseInt(params.get("limit") || "25");
  const search  = params.get("search") || "";
  const gov     = params.get("gouvernerat") || "";
  const type    = params.get("type") || "";
  const contrat = params.get("contrat") || "";
  const prixMin = params.get("prix_min") || "";
  const prixMax = params.get("prix_max") || "";
  const surfMin = params.get("surface_min") || "";

  function set(key, val) {
    const next = new URLSearchParams(params);
    if (val) next.set(key, val); else next.delete(key);
    next.set("page", "1");
    setParams(next);
  }

  const load = useCallback(() => {
    setLoading(true);
    const q = { page, limit };
    if (search)  q.search = search;
    if (gov)     q.gouvernerat = gov;
    if (type)    q.type = type;
    if (contrat) q.contrat = contrat;
    if (prixMin) q.prix_min = prixMin;
    if (prixMax) q.prix_max = prixMax;
    if (surfMin) q.surface_min = surfMin;

    api.list(q).then(r => {
      setData(r.data); setTotal(r.total); setPages(r.pages); setLoading(false);
    }).catch(() => setLoading(false));
  }, [page, limit, search, gov, type, contrat, prixMin, prixMax, surfMin]);

  useEffect(() => { load(); }, [load]);

  async function loadScore(id) {
    if (scores[id]) return;
    const s = await api.score(id).catch(() => null);
    if (s) setScores(prev => ({ ...prev, [id]: s }));
  }

  function exportCsv() {
    const q = { gouvernerat: gov, type, contrat, prix_min: prixMin, prix_max: prixMax, search };
    window.open(api.export(q));
  }

  const firstImg = (images) => images?.split("|")[0]?.trim() || null;

  return (
    <div>
      <TopBar title={t.pages.listings.title} subtitle={`${total.toLocaleString("fr-TN")} ${t.pages.listings.subtitle}`} />
      <div style={{ display: "flex", height: "calc(100vh - 64px)" }}>

        {/* Filter panel */}
        <AnimatePresence>
          {filtersOpen && (
            <motion.div initial={{ width: 0 }} animate={{ width: 260 }} exit={{ width: 0 }}
              style={{ background: "#fff", borderRight: "1px solid var(--border)", overflowY: "auto", overflowX: "hidden", flexShrink: 0 }}>
              <div style={{ padding: 20, minWidth: 240 }}>
                <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 700, fontSize: 14, marginBottom: 16 }}>{t.listings_page.filters}</div>

                {[
                  { label: t.analytics_page.label_gov, key: "gouvernerat", options: GOVS, val: gov },
                  { label: t.listings_page.col_type, key: "type", options: TYPES, val: type },
                  { label: t.listings_page.contrat, key: "contrat", options: ["","vente","location"], val: contrat },
                ].map(f => (
                  <div key={f.key} style={{ marginBottom: 14 }}>
                    <label style={{ display: "block", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>{f.label}</label>
                    <select value={f.val} onChange={e => set(f.key, e.target.value)}
                      style={{ width: "100%", padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }}>
                      {f.options.map(o => <option key={o} value={o}>{o || t.listings_page.all}</option>)}
                    </select>
                  </div>
                ))}

                <div style={{ marginBottom: 14 }}>
                  <label style={{ display: "block", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>{t.listings_page.prix_min}</label>
                  <input type="number" value={prixMin} onChange={e => set("prix_min", e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }} />
                </div>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ display: "block", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>{t.listings_page.prix_max}</label>
                  <input type="number" value={prixMax} onChange={e => set("prix_max", e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }} />
                </div>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ display: "block", fontSize: 11, color: "var(--modern)", marginBottom: 4 }}>{t.listings_page.surf_min}</label>
                  <input type="number" value={surfMin} onChange={e => set("surface_min", e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", fontSize: 13, background: "var(--bg)", color: "var(--strong)", fontFamily: "Inter,sans-serif" }} />
                </div>

                <button className="btn btn-outline" style={{ width: "100%", justifyContent: "center", marginTop: 4 }} onClick={() => setParams(new URLSearchParams())}>{t.listings_page.reset}</button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main content */}
        <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
          {/* Toolbar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-outline" style={{ padding: "6px 12px", fontSize: 12 }} onClick={() => setFiltersOpen(f => !f)}>
                ☰ {t.listings_page.filters}
              </button>
              {["table","grid"].map(v => (
                <button key={v} className="btn" onClick={() => setView(v)}
                  style={{ padding: "6px 12px", fontSize: 12, background: view === v ? "var(--dynamic)" : "#fff", color: view === v ? "#fff" : "var(--strong)", border: "1px solid var(--border)" }}>
                  {v === "table" ? `☰ ${t.listings_page.view_table}` : `⊞ ${t.listings_page.view_grid}`}
                </button>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 12, color: "var(--modern)" }}>{total.toLocaleString("fr-TN")} {t.pages.listings.subtitle}</span>
              <button className="btn btn-outline" style={{ padding: "6px 12px", fontSize: 12 }} onClick={exportCsv}>⬇ CSV</button>
            </div>
          </div>

          {/* Table view */}
          {view === "table" && (
            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--border)", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ background: "var(--bg)" }}>
                    {[t.listings_page.col_type,t.listings_page.col_title,t.listings_page.col_city,t.listings_page.col_price,t.listings_page.col_surface,t.listings_page.col_contract,t.listings_page.col_score,t.listings_page.col_date].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "left", color: "var(--modern)", fontWeight: 500, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {loading
                    ? Array(8).fill(0).map((_, i) => (
                      <tr key={i}><td colSpan={8} style={{ padding: "12px 14px" }}><div className="skeleton" style={{ height: 14 }} /></td></tr>
                    ))
                    : data.map(r => (
                      <tr key={r.id} onClick={() => { setSelected(r); loadScore(r.id); }}
                        style={{ cursor: "pointer", borderTop: "1px solid var(--border)", transition: "background 0.15s" }}
                        onMouseEnter={e => e.currentTarget.style.background = "rgba(241,133,52,0.04)"}
                        onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, background: "rgba(68,85,118,0.1)", color: "#445576" }}>{r.type || "—"}</span>
                        </td>
                        <td style={{ padding: "10px 14px", maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: 500 }}>
                          {r.titre || t.listings_page.no_title}
                        </td>
                        <td style={{ padding: "10px 14px", color: "var(--modern)" }}>{r.ville || r.gouvernerat || "—"}</td>
                        <td style={{ padding: "10px 14px", fontWeight: 600, color: "var(--dynamic)" }}>
                          {r.prix ? r.prix.toLocaleString("fr-TN") : "—"}
                        </td>
                        <td style={{ padding: "10px 14px", color: "var(--modern)" }}>{r.surface ? `${r.surface} m²` : "—"}</td>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{ padding: "2px 8px", borderRadius: 12, fontSize: 11, background: r.contrat === "vente" ? "rgba(241,133,52,0.12)" : "rgba(68,85,118,0.1)", color: r.contrat === "vente" ? "var(--dynamic)" : "#445576" }}>
                            {r.contrat || "—"}
                          </span>
                        </td>
                        <td style={{ padding: "10px 14px", minWidth: 80 }}>
                          {scores[r.id] ? <ScoreBar score={scores[r.id].score} /> : <span style={{ fontSize: 11, color: "var(--modern)" }}>—</span>}
                        </td>
                        <td style={{ padding: "10px 14px", color: "var(--modern)", fontSize: 11 }}>{r.date_publication?.slice(0, 10) || "—"}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
            </div>
          )}

          {/* Grid view */}
          {view === "grid" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
              {loading
                ? Array(12).fill(0).map((_, i) => <div key={i} className="skeleton" style={{ height: 240, borderRadius: 12 }} />)
                : data.map(r => (
                  <div key={r.id} className="card" style={{ cursor: "pointer", padding: 0, overflow: "hidden" }}
                    onClick={() => { setSelected(r); loadScore(r.id); }}>
                    <div style={{ height: 140, overflow: "hidden" }}>
                      <PropertyImage src={firstImg(r.images)} type={r.type} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </div>
                    <div style={{ padding: 12 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.titre || t.listings_page.no_title}</div>
                      <div style={{ fontSize: 11, color: "var(--modern)", marginBottom: 6 }}>{r.ville || r.gouvernerat}</div>
                      <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 700, fontSize: 16, color: "var(--dynamic)" }}>
                        {r.prix ? `${(r.prix / 1000).toFixed(0)}K TND` : t.listings_page.price_na}
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {/* Pagination */}
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 24 }}>
            <button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 12 }} onClick={() => set("page", Math.max(1, page - 1))} disabled={page <= 1}>←</button>
            <span style={{ padding: "6px 14px", fontSize: 13, color: "var(--modern)" }}>{page} / {pages}</span>
            <button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 12 }} onClick={() => set("page", Math.min(pages, page + 1))} disabled={page >= pages}>→</button>
          </div>
        </div>
      </div>

      {selected && <ListingModal listing={selected} score={scores[selected.id]} onClose={() => setSelected(null)} />}
    </div>
  );
}

function ListingModal({ listing: r, score, onClose }) {
  const { t } = useLang();
  const [similar, setSimilar] = useState([]);
  useEffect(() => { api.similar(r.id).then(setSimilar).catch(() => {}); }, [r.id]);

  const imgs = r.images?.split("|").map(s => s.trim()).filter(Boolean) || [];
  const [imgIdx, setImgIdx] = useState(0);

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(9,25,64,0.55)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
      <div style={{ background: "#fff", borderRadius: 16, width: "100%", maxWidth: 820, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(9,25,64,0.25)" }}>
        {/* Image gallery */}
        <div style={{ position: "relative", height: 280, borderRadius: "16px 16px 0 0", overflow: "hidden" }}>
          <PropertyImage
            src={imgs[imgIdx] || null}
            type={r.type}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
          {imgs.length > 1 && (
            <>
              <button onClick={() => setImgIdx(i => Math.max(0, i - 1))} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", background: "rgba(9,25,64,0.5)", border: "none", color: "#fff", borderRadius: "50%", width: 32, height: 32, cursor: "pointer", fontSize: 16 }}>‹</button>
              <button onClick={() => setImgIdx(i => Math.min(imgs.length - 1, i + 1))} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "rgba(9,25,64,0.5)", border: "none", color: "#fff", borderRadius: "50%", width: 32, height: 32, cursor: "pointer", fontSize: 16 }}>›</button>
              <div style={{ position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)", background: "rgba(9,25,64,0.6)", color: "#fff", padding: "2px 10px", borderRadius: 12, fontSize: 11 }}>{imgIdx + 1}/{imgs.length}</div>
            </>
          )}
        </div>

        <div style={{ padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <h2 style={{ margin: "0 0 6px", fontSize: 20 }}>{r.titre || t.listings_page.no_title}</h2>
              <div style={{ color: "var(--modern)", fontSize: 13 }}>{r.adresse || `${r.ville || ""}, ${r.gouvernerat || ""}`}</div>
            </div>
            <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "var(--modern)" }}>✕</button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 24 }}>
            <div>
              {/* Key stats */}
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginBottom: 16 }}>
                {[
                  ["💰", r.prix ? `${r.prix.toLocaleString("fr-TN")} TND` : "—", t.listings_page.lbl_price],
                  ["📐", r.surface ? `${r.surface} m²` : "—", t.listings_page.lbl_surface],
                  ["🚪", r.pieces || "—", t.listings_page.lbl_rooms],
                  ["🏢", r.etage || "—", t.listings_page.lbl_floor],
                  ["⭐", r.standing || "—", t.listings_page.lbl_standing],
                ].map(([icon, val, lbl]) => (
                  <div key={lbl} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 18 }}>{icon}</div>
                    <div style={{ fontWeight: 700, fontSize: 15, color: "var(--strong)" }}>{val}</div>
                    <div style={{ fontSize: 10, color: "var(--modern)" }}>{lbl}</div>
                  </div>
                ))}
              </div>

              {/* Amenities */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
                {[
                  ["Parking", r.has_parking], ["Piscine", r.has_piscine], ["Jardin", r.has_jardin],
                  ["Ascenseur", r.has_ascenseur], ["Climatisation", r.has_climatisation],
                  ["Terrasse", r.has_terrasse], ["Balcon", r.has_balcon], ["Garage", r.has_garage],
                  ["Gardien", r.has_gardien], ["Chauffage", r.has_chaffage],
                ].filter(([, v]) => v == 1 || v === "1" || v === 1).map(([label]) => (
                  <span key={label} className="badge badge-dynamic">{label}</span>
                ))}
              </div>

              {r.description && (
                <div style={{ fontSize: 12, color: "var(--modern)", lineHeight: 1.6, maxHeight: 100, overflowY: "auto" }}>{r.description.slice(0, 400)}…</div>
              )}
            </div>

            {/* Price card + score */}
            <div style={{ minWidth: 160 }}>
              <div style={{ background: "var(--bg)", borderRadius: 12, padding: "16px", marginBottom: 12 }}>
                <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 22, color: "var(--dynamic)", marginBottom: 4 }}>
                  {r.prix ? `${r.prix.toLocaleString("fr-TN")} TND` : t.listings_page.price_na}
                </div>
                {r.prix_m2 && <div style={{ fontSize: 11, color: "var(--modern)" }}>{Math.round(r.prix_m2).toLocaleString("fr-TN")} TND/m²</div>}
                <div style={{ marginTop: 10 }}>
                  <div style={{ display: "flex", gap: 6 }}>
                    <span className="badge badge-warm">{r.contrat || "—"}</span>
                    <span className="badge badge-reliable">{r.type || "—"}</span>
                  </div>
                </div>
              </div>

              {score && (
                <div style={{ background: "var(--bg)", borderRadius: 12, padding: 14, marginBottom: 12 }}>
                  <div style={{ fontSize: 10, color: "var(--modern)", marginBottom: 6 }}>SMART SCORE</div>
                  <div style={{ fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 28, color: score.score >= 70 ? "#52c41a" : score.score >= 40 ? "#f18534" : "#ff4d4f" }}>{score.score}<span style={{ fontSize: 14, fontWeight: 400 }}>/100</span></div>
                  <div style={{ fontSize: 11, color: "var(--strong)", fontWeight: 500 }}>{score.label}</div>
                </div>
              )}

              {r.url && (
                <a href={r.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ width: "100%", justifyContent: "center", fontSize: 12 }}>
                  {t.listings_page.view_on} {r.source || "Tayara"} ↗
                </a>
              )}
            </div>
          </div>

          {/* Similar listings */}
          {similar.length > 0 && (
            <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--strong)", marginBottom: 10 }}>{t.listings_page.similar}</div>
              <div style={{ display: "flex", gap: 10, overflowX: "auto" }}>
                {similar.map(s => (
                  <div key={s.id} style={{ minWidth: 160, background: "var(--bg)", borderRadius: 10, padding: 12, flexShrink: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.titre || t.listings_page.no_title}</div>
                    <div style={{ fontWeight: 700, color: "var(--dynamic)", fontSize: 14 }}>{s.prix ? `${(s.prix / 1000).toFixed(0)}K` : "—"}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
