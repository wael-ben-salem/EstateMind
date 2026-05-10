import { useState } from "react";
import TopBar from "../components/Layout/TopBar";
import { useLang } from "../contexts/LangContext";

function getSteps(t) {
  return [
    {
      n: 1, title: t.powerbi_page.step1_title,
      content: (
        <div>
          <p style={{ color: "var(--modern)", fontSize: 13, marginBottom: 12 }}>{t.powerbi_page.step1_desc}</p>
          <CodeBlock code={`Serveur:  localhost (ou IP du serveur Docker)
Port:     5432
Base:     airflow
Table:    scraped_properties
User:     airflow
Password: airflow`} />
        </div>
      ),
    },
    {
      n: 2, title: t.powerbi_page.step2_title,
      content: (
        <div>
          <p style={{ color: "var(--modern)", fontSize: 13, marginBottom: 12 }}>{t.powerbi_page.step2_desc}</p>
          <CodeBlock code={`// Convertir prix en nombre
= Table.TransformColumnTypes(Source, {{"prix", type number}, {"surface", type number}})

// Créer colonne Date
= Table.AddColumn(prev, "Date", each #date([pub_year], [pub_month], 1), type date)

// Filtrer lignes vides
= Table.SelectRows(prev, each [gouvernerat] <> null and [gouvernerat] <> "")`} />
        </div>
      ),
    },
    {
      n: 3, title: t.powerbi_page.step3_title,
      content: (
        <div>
          <p style={{ color: "var(--modern)", fontSize: 13, marginBottom: 12 }}>{t.powerbi_page.step3_desc}</p>
          <CodeBlock code={`DateTable =
CALENDAR(
    DATE(2020, 1, 1),
    DATE(2026, 12, 31)
)
// Relation: scraped_properties[Date] → DateTable[Date]`} lang="dax" />
        </div>
      ),
    },
    {
      n: 4, title: t.powerbi_page.step4_title,
      content: (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { name: "Total Listings",     code: `Total Listings = COUNTROWS(scraped_properties)` },
            { name: "Prix Moyen",         code: `Avg Prix = AVERAGEX(FILTER(scraped_properties, scraped_properties[prix] > 0), scraped_properties[prix])` },
            { name: "Prix par m²",        code: `Prix per m² = AVERAGEX(FILTER(scraped_properties, scraped_properties[surface] > 0), DIVIDE([prix], [surface]))` },
            { name: "Haut Standing %",    code: `Haut Standing % = DIVIDE(COUNTROWS(FILTER(scraped_properties, scraped_properties[haut_standing] IN {"1.0","True","1"})), [Total Listings])` },
            { name: "Croissance MoM",     code: `MoM Growth % = VAR curr = [Total Listings] VAR prev = CALCULATE([Total Listings], DATEADD(DateTable[Date], -1, MONTH)) RETURN DIVIDE(curr - prev, prev)` },
            { name: "Part de marché",     code: `Market Share % = DIVIDE(COUNTROWS(scraped_properties), CALCULATE(COUNTROWS(scraped_properties), ALL(scraped_properties[gouvernerat])))` },
            { name: "Bon Entourage",      code: `Bon Entourage Avg = AVERAGE(scraped_properties[bon_entourage])` },
          ].map(m => <DaxBlock key={m.name} name={m.name} code={m.code} />)}
        </div>
      ),
    },
    {
      n: 5, title: t.powerbi_page.step5_title,
      content: (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {[
            { page: "1. Vue d'ensemble",   visuels: "KPIs, Bar Gouvernerat, Donut Types, Line Tendance" },
            { page: "2. Carte",            visuels: "Carte ArcGIS, Clusters, Choroplèthe prix" },
            { page: "3. Prix",             visuels: "Scatter prix/m², Histogramme, Box plot gouvernerat" },
            { page: "4. Équipements",      visuels: "Radar équipements, Barres comparatif %" },
            { page: "5. Temporel",         visuels: "Timeline, Heatmap calendrier, Saisonnalité" },
            { page: "6. Investissement",   visuels: "Radar régions, Rentabilité, Comparaison interrégionale" },
            { page: "7. Executive",        visuels: "KPIs condensés, Index ETREI, Alertes marché" },
          ].map(p => (
            <div key={p.page} style={{ padding: "10px 14px", background: "var(--bg)", borderRadius: 8 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{p.page}</div>
              <div style={{ fontSize: 11, color: "var(--modern)" }}>{p.visuels}</div>
            </div>
          ))}
        </div>
      ),
    },
    {
      n: 6, title: t.powerbi_page.step6_title,
      content: (
        <div>
          <p style={{ color: "var(--modern)", fontSize: 13, marginBottom: 12 }}>{t.powerbi_page.step6_desc}</p>
          <ol style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8, fontSize: 13, color: "var(--strong)" }}>
            <li>{t.powerbi_page.step6_li1}</li>
            <li>{t.powerbi_page.step6_li2}</li>
            <li>{t.powerbi_page.step6_li3}</li>
            <li>{t.powerbi_page.step6_li4}</li>
          </ol>
        </div>
      ),
    },
  ];
}

function CodeBlock({ code, lang = "sql" }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <div style={{ position: "relative" }}>
      <pre style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 12, background: "#091940", color: "#ead5c8", padding: "14px 16px", borderRadius: 8, overflowX: "auto", lineHeight: 1.7, margin: 0 }}>
        <code>{code}</code>
      </pre>
      <button onClick={copy} style={{ position: "absolute", top: 8, right: 8, background: copied ? "#52c41a" : "rgba(255,255,255,0.1)", border: "none", color: "#fff", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer" }}>
        {copied ? "✓ Copié" : "Copier"}
      </button>
    </div>
  );
}

function DaxBlock({ name, code }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ background: "var(--bg)", borderRadius: 10, padding: "10px 14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>{name}</span>
        <button onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
          style={{ background: copied ? "#52c41a" : "var(--dynamic)", border: "none", color: "#fff", borderRadius: 6, padding: "3px 10px", fontSize: 11, cursor: "pointer" }}>
          {copied ? "✓" : "Copier"}
        </button>
      </div>
      <pre style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: "#445576", margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{code}</pre>
    </div>
  );
}

export default function PowerBI() {
  const { t } = useLang();
  const STEPS = getSteps(t);
  const [activeStep, setActiveStep] = useState(1);

  return (
    <div>
      <TopBar title={t.pages.powerbi.title} subtitle={t.pages.powerbi.subtitle} />
      <div style={{ display: "flex", height: "calc(100vh - 64px)" }}>

        {/* Stepper sidebar */}
        <div style={{ width: 200, background: "#fff", borderRight: "1px solid var(--border)", padding: 16, flexShrink: 0 }}>
          {STEPS.map(s => (
            <button key={s.n} onClick={() => setActiveStep(s.n)}
              style={{
                display: "flex", gap: 10, alignItems: "center", width: "100%",
                padding: "10px 12px", borderRadius: 8, border: "none", cursor: "pointer", marginBottom: 4,
                background: activeStep === s.n ? "rgba(241,133,52,0.1)" : "transparent",
                color: activeStep === s.n ? "var(--dynamic)" : "var(--strong)",
                textAlign: "left",
              }}>
              <div style={{
                width: 24, height: 24, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 12, fontWeight: 700, flexShrink: 0,
                background: activeStep === s.n ? "var(--dynamic)" : "var(--bg)",
                color: activeStep === s.n ? "#fff" : "var(--modern)",
              }}>{s.n}</div>
              <span style={{ fontSize: 12, fontWeight: activeStep === s.n ? 600 : 400, lineHeight: 1.3 }}>{s.title}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: 32 }}>
          {STEPS.filter(s => s.n === activeStep).map(s => (
            <div key={s.n}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
                <div style={{ width: 40, height: 40, borderRadius: "50%", background: "var(--dynamic)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "Playfair Display,serif", fontWeight: 800, fontSize: 18 }}>{s.n}</div>
                <h2 style={{ margin: 0, fontSize: 22 }}>{s.title}</h2>
              </div>
              {s.content}
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 32 }}>
                {activeStep > 1 && <button className="btn btn-outline" onClick={() => setActiveStep(n => n - 1)}>{t.powerbi_page.prev}</button>}
                {activeStep < STEPS.length && <button className="btn btn-primary" style={{ marginLeft: "auto" }} onClick={() => setActiveStep(n => n + 1)}>{t.powerbi_page.next}</button>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
