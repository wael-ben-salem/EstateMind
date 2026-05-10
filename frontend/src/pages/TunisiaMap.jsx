import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { map as mapApi, stats } from "../services/api";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";
import "leaflet/dist/leaflet.css";

function CanvasOverlay({ points, color = "#f18534", opacity = 0.18, radius = 4 }) {
  const mapInstance = useMap();
  const layerRef = useRef(null);

  useEffect(() => {
    if (!points.length) return;
    import("leaflet").then(L => {
      if (layerRef.current) mapInstance.removeLayer(layerRef.current);
      const renderer = L.canvas({ padding: 0.5 });
      const group = L.layerGroup(
        points.map(p =>
          L.circleMarker([p.lat, p.lng], {
            renderer,
            radius,
            color: "transparent",
            fillColor: color,
            fillOpacity: opacity,
          })
        )
      );
      group.addTo(mapInstance);
      layerRef.current = group;
    });
    return () => { if (layerRef.current) mapInstance.removeLayer(layerRef.current); };
  }, [points, mapInstance, color, opacity, radius]);

  return null;
}

export default function TunisiaMap() {
  const { t } = useLang();
  const [clusters, setClusters] = useState([]);
  const [heat, setHeat]         = useState([]);
  const [points, setPoints]     = useState([]);
  const [choropleth, setChoro]  = useState([]);
  const [selected, setSelected] = useState(null);
  const [govDetails, setGovD]   = useState(null);
  const [mode, setMode]         = useState("cluster");
  const [loading, setLoading]   = useState(true);
  const [pointsLoading, setPL]  = useState(false);
  const [timeMachine, setTM]    = useState({ year: 2025, month: 5 });
  const [tmData, setTmData]     = useState([]);
  const [showTM, setShowTM]     = useState(false);

  useEffect(() => {
    Promise.all([mapApi.clusters(8), mapApi.heatmap(), mapApi.choropleth()])
      .then(([cl, ht, ch]) => { setClusters(cl); setHeat(ht); setChoro(ch); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (mode !== "listings" || points.length) return;
    setPL(true);
    mapApi.points().then(d => { setPoints(d); setPL(false); }).catch(() => setPL(false));
  }, [mode]);

  useEffect(() => {
    if (!selected) return;
    mapApi.gouvernerat(selected).then(setGovD).catch(() => {});
  }, [selected]);

  async function loadTimeMachine() {
    const d = await mapApi.timeMachine(timeMachine.year, timeMachine.month);
    setTmData(d);
    setShowTM(true);
  }

  const maxCount = Math.max(...clusters.map(c => c.count), 1);

  function clusterColor(count) {
    const ratio = count / maxCount;
    if (ratio > 0.6) return "#091940";
    if (ratio > 0.3) return "#445576";
    return "#f18534";
  }

  const displayData = showTM ? tmData : choropleth;

  return (
    <div>
      <TopBar title={t.pages.map.title} subtitle={t.pages.map.subtitle} />
      <div style={{ display: "flex", height: "calc(100vh - 64px)" }}>
        <div style={{ flex: 1, position: "relative" }}>
          {/* Controls */}
          <div style={{ position: "absolute", top: 14, left: 14, zIndex: 1000, display: "flex", gap: 8, flexWrap: "wrap" }}>
            {[
              { id: "cluster",  label: "Clusters" },
              { id: "listings", label: `20K Annonces${pointsLoading ? " …" : points.length ? ` (${(points.length/1000).toFixed(0)}K)` : ""}` },
              { id: "heat",     label: "Heatmap" },
              { id: "choropleth", label: "Choroplèthe" },
            ].map(({ id, label }) => (
              <button key={id} onClick={() => setMode(id)} className="btn"
                style={{ padding: "6px 14px", fontSize: 12, background: mode === id ? "var(--dynamic)" : "#fff", color: mode === id ? "#fff" : "var(--strong)", border: "1px solid var(--border)" }}>
                {label}
              </button>
            ))}
          </div>

          {loading ? (
            <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#f7f3ef" }}>
              <div style={{ textAlign: "center" }}>
                <div className="skeleton" style={{ width: 200, height: 20, marginBottom: 8 }} />
                <div style={{ color: "var(--modern)", fontSize: 13 }}>Chargement de la carte…</div>
              </div>
            </div>
          ) : (
            <MapContainer center={[33.9, 9.5]} zoom={7} style={{ height: "100%", width: "100%" }}>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" attribution="CartoDB" />

              {mode === "cluster" && clusters.map((c, i) => (
                <CircleMarker key={i} center={[c.lat, c.lng]}
                  radius={Math.max(4, Math.min(22, Math.sqrt(c.count / maxCount) * 18))}
                  color={clusterColor(c.count)} fillColor={clusterColor(c.count)} fillOpacity={0.6} weight={1}
                  eventHandlers={{ click: () => setSelected(c.gouvernerat) }}>
                  <Popup>
                    <strong>{c.gouvernerat}</strong><br />
                    {c.count.toLocaleString("fr-TN")} annonces
                  </Popup>
                </CircleMarker>
              ))}

              {mode === "listings" && <CanvasOverlay points={points} color="#091940" opacity={0.55} radius={3} />}

              {mode === "heat" && <CanvasOverlay points={heat} color="#f18534" opacity={0.22} radius={5} />}

              {mode === "choropleth" && displayData.map((g, i) => (
                <CircleMarker key={i} center={[33.9 + (i % 5) * 0.4, 9.5 + Math.floor(i / 5) * 0.5]}
                  radius={14} fillOpacity={0.7}
                  color={`rgba(241,133,52,${0.2 + (g.color_value || 0) * 0.8})`}
                  fillColor={`rgba(241,133,52,${0.2 + (g.color_value || 0) * 0.8})`}
                  eventHandlers={{ click: () => setSelected(g.gouvernerat) }}>
                  <Popup><strong>{g.gouvernerat}</strong><br />Prix moyen: {g.avg_prix?.toLocaleString("fr-TN")} TND<br />{g.count?.toLocaleString("fr-TN")} annonces</Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          )}

          {/* Time machine */}
          <div style={{ position: "absolute", bottom: 20, left: "50%", transform: "translateX(-50%)", zIndex: 1000, background: "#fff", borderRadius: 12, padding: "12px 20px", border: "1px solid var(--border)", display: "flex", gap: 16, alignItems: "center", boxShadow: "var(--shadow)" }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--strong)" }}>⏱️ Time Machine</span>
            <select value={timeMachine.year} onChange={e => setTM(p => ({ ...p, year: +e.target.value }))}
              style={{ padding: "4px 8px", borderRadius: 6, border: "1px solid var(--border)", fontSize: 12, color: "var(--strong)" }}>
              {[2022,2023,2024,2025].map(y => <option key={y}>{y}</option>)}
            </select>
            <select value={timeMachine.month} onChange={e => setTM(p => ({ ...p, month: +e.target.value }))}
              style={{ padding: "4px 8px", borderRadius: 6, border: "1px solid var(--border)", fontSize: 12, color: "var(--strong)" }}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map(m => <option key={m}>{m}</option>)}
            </select>
            <button className="btn btn-primary" style={{ padding: "5px 14px", fontSize: 12 }} onClick={loadTimeMachine}>Afficher</button>
            {showTM && <button className="btn btn-outline" style={{ padding: "5px 14px", fontSize: 12 }} onClick={() => setShowTM(false)}>Réinitialiser</button>}
          </div>
        </div>

        {/* Side panel */}
        <div style={{ width: 300, background: "#fff", borderLeft: "1px solid var(--border)", padding: 20, overflowY: "auto" }}>
          {selected && govDetails ? (
            <>
              <h3 style={{ marginBottom: 4, fontSize: 16 }}>{selected}</h3>
              <div style={{ color: "var(--modern)", fontSize: 12, marginBottom: 16 }}>Données du gouvernerat</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  ["Total annonces", govDetails.stats?.total?.toLocaleString("fr-TN")],
                  ["Prix moyen", `${govDetails.stats?.avg_prix?.toLocaleString("fr-TN")} TND`],
                  ["Surface moy.", `${govDetails.stats?.avg_surface} m²`],
                ].map(([l, v]) => (
                  <div key={l} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                    <span style={{ fontSize: 12, color: "var(--modern)" }}>{l}</span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{v}</span>
                  </div>
                ))}
              </div>
              {govDetails.top_villes?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, color: "var(--modern)", marginBottom: 8, textTransform: "uppercase" }}>Top villes</div>
                  {govDetails.top_villes.map(v => (
                    <div key={v.ville} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", fontSize: 12 }}>
                      <span>{v.ville}</span><span style={{ color: "var(--dynamic)", fontWeight: 600 }}>{v.n}</span>
                    </div>
                  ))}
                </div>
              )}
              {govDetails.type_distribution?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, color: "var(--modern)", marginBottom: 8, textTransform: "uppercase" }}>Types de biens</div>
                  {govDetails.type_distribution.slice(0, 4).map(t => (
                    <div key={t.type} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", fontSize: 12 }}>
                      <span>{t.type}</span><span style={{ color: "var(--reliable)", fontWeight: 600 }}>{t.n}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ color: "var(--modern)", fontSize: 13, textAlign: "center", marginTop: 40 }}>
              Cliquez sur un cluster pour voir les détails du gouvernerat
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
