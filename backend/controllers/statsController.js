const { getDb } = require("../config/database");
const { cached } = require("../services/cacheService");

function overview(req, res, next) {
  try {
    const data = cached("stats:overview", () => {
      const db = getDb();
      const row = db.prepare(`
        SELECT
          COUNT(*) AS total,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface,
          COUNT(DISTINCT gouvernerat) AS gouvernerats_count,
          ROUND(100.0 * SUM(CASE WHEN haut_standing = '1.0' OR haut_standing = 'True' OR haut_standing = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) AS haut_standing_rate,
          ROUND(AVG(CASE WHEN bon_entourage IS NOT NULL THEN bon_entourage END), 2) AS bon_entourage_avg
        FROM properties
        WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
      `).get();
      return row;
    });
    res.json(data);
  } catch (err) { next(err); }
}

function byGouvernerat(req, res, next) {
  try {
    const data = cached("stats:by_gouvernerat", () =>
      getDb().prepare(`
        SELECT
          gouvernerat,
          COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface,
          ROUND(100.0 * SUM(CASE WHEN haut_standing = '1.0' OR haut_standing = 'True' OR haut_standing = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) AS haut_standing_pct
        FROM properties
        WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
        GROUP BY gouvernerat
        ORDER BY count DESC
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function byType(req, res, next) {
  try {
    const data = cached("stats:by_type", () =>
      getDb().prepare(`
        SELECT
          type,
          COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface
        FROM properties
        WHERE type IS NOT NULL AND type != ''
        GROUP BY type
        ORDER BY count DESC
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function byContrat(req, res, next) {
  try {
    const data = cached("stats:by_contrat", () =>
      getDb().prepare(`
        SELECT contrat, COUNT(*) AS count, ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties
        WHERE contrat IS NOT NULL AND contrat != ''
        GROUP BY contrat ORDER BY count DESC
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function priceDistribution(req, res, next) {
  try {
    const data = cached("stats:price_dist", () => {
      const db = getDb();
      const bins = [];
      const step = 50000;
      const max  = 1000000;
      const total = db.prepare("SELECT COUNT(*) AS n FROM properties WHERE prix > 0 AND prix < 5000000").get().n;
      for (let lo = 0; lo < max; lo += step) {
        const hi  = lo + step;
        const cnt = db.prepare(
          "SELECT COUNT(*) AS n FROM properties WHERE prix >= ? AND prix < ?"
        ).get(lo, hi).n;
        bins.push({ range: `${lo/1000}k-${hi/1000}k`, count: cnt, percentage: total ? +(cnt/total*100).toFixed(2) : 0 });
      }
      const above = db.prepare("SELECT COUNT(*) AS n FROM properties WHERE prix >= ?").get(max).n;
      bins.push({ range: `1M+`, count: above, percentage: total ? +(above/total*100).toFixed(2) : 0 });
      return bins;
    });
    res.json(data);
  } catch (err) { next(err); }
}

function monthlyTrend(req, res, next) {
  try {
    const data = cached("stats:monthly_trend", () =>
      getDb().prepare(`
        SELECT pub_year AS year, pub_month AS month, COUNT(*) AS count,
               ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties
        WHERE pub_year IS NOT NULL AND pub_month IS NOT NULL
        GROUP BY pub_year, pub_month
        ORDER BY pub_year, pub_month
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function amenities(req, res, next) {
  try {
    const data = cached("stats:amenities", () => {
      const db = getDb();
      const total = db.prepare("SELECT COUNT(*) AS n FROM properties").get().n;
      const cols = ["has_parking","has_piscine","has_climatisation","has_jardin",
                    "has_terrasse","has_ascenseur","has_garage","has_balcon",
                    "has_chaffage","has_gardien"];
      const result = {};
      for (const col of cols) {
        const n = db.prepare(`SELECT COUNT(*) AS n FROM properties WHERE ${col} = 1`).get().n;
        result[col] = total ? +(n/total*100).toFixed(2) : 0;
      }
      return result;
    });
    res.json(data);
  } catch (err) { next(err); }
}

function priceHeatmap(req, res, next) {
  try {
    const data = cached("stats:price_heatmap", () =>
      getDb().prepare(`
        SELECT gouvernerat, type, ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties
        WHERE gouvernerat != '' AND type != '' AND prix > 0
        GROUP BY gouvernerat, type
        ORDER BY gouvernerat, type
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function standingDistribution(req, res, next) {
  try {
    const data = cached("stats:standing", () => {
      const db = getDb();
      const total = db.prepare("SELECT COUNT(*) AS n FROM properties").get().n;
      const rows  = db.prepare(`
        SELECT COALESCE(NULLIF(standing,''), 'Non spécifié') AS standing, COUNT(*) AS count
        FROM properties GROUP BY standing ORDER BY count DESC
      `).all();
      return rows.map(r => ({ ...r, percentage: total ? +(r.count/total*100).toFixed(2) : 0 }));
    });
    res.json(data);
  } catch (err) { next(err); }
}

function insights(req, res, next) {
  try {
    const data = cached("stats:insights", () => {
      const db = getDb();
      const results = [];

      const topGov = db.prepare(`
        SELECT gouvernerat, COUNT(*) as n, ROUND(AVG(prix),0) as avg
        FROM properties WHERE pub_year >= 2024 AND prix > 0 GROUP BY gouvernerat ORDER BY avg DESC LIMIT 1
      `).get();
      if (topGov) results.push({ type: "tendance", icon: "📈", text: `${topGov.gouvernerat} est le gouvernerat le plus cher avec un prix moyen de ${(topGov.avg/1000).toFixed(0)}K TND.` });

      const undervalued = db.prepare(`
        SELECT type, gouvernerat, ROUND(AVG(prix),0) as avg_local,
          (SELECT ROUND(AVG(prix),0) FROM properties WHERE type = p.type AND prix > 0) as avg_global
        FROM properties p
        WHERE prix > 0 AND type != ''
        GROUP BY type, gouvernerat
        HAVING avg_local < avg_global * 0.8
        ORDER BY (avg_global - avg_local) DESC LIMIT 1
      `).get();
      if (undervalued) results.push({ type: "opportunite", icon: "💡", text: `Les ${undervalued.type}s à ${undervalued.gouvernerat} sont sous-évalué(e)s — ${(undervalued.avg_local/1000).toFixed(0)}K TND vs ${(undervalued.avg_global/1000).toFixed(0)}K TND en moyenne nationale.` });

      const anomaly = db.prepare(`
        SELECT COUNT(*) as n FROM properties
        WHERE prix > 0 AND (prix < 5000 OR prix > 10000000)
      `).get();
      if (anomaly.n > 0) results.push({ type: "anomalie", icon: "🚨", text: `${anomaly.n} annonces avec des prix anormaux (< 5k ou > 10M TND) détectées dans la base.` });

      const emerging = db.prepare(`
        SELECT gouvernerat, COUNT(*) as n FROM properties
        WHERE pub_year = 2025 AND gouvernerat != ''
        GROUP BY gouvernerat ORDER BY n DESC LIMIT 1
      `).get();
      if (emerging) results.push({ type: "quartier", icon: "🏘️", text: `${emerging.gouvernerat} est le gouvernerat le plus actif en 2025 avec ${emerging.n} nouvelles annonces.` });

      const haut = db.prepare(`
        SELECT gouvernerat, ROUND(100.0*SUM(CASE WHEN haut_standing='1.0' OR haut_standing='True' OR haut_standing='1' THEN 1 ELSE 0 END)/COUNT(*),1) as pct
        FROM properties WHERE gouvernerat != '' GROUP BY gouvernerat ORDER BY pct DESC LIMIT 1
      `).get();
      if (haut) results.push({ type: "prediction", icon: "🏆", text: `${haut.gouvernerat} concentre le plus de biens haut standing (${haut.pct}% des annonces).` });

      return results;
    });
    res.json(data);
  } catch (err) { next(err); }
}

function etrei(req, res, next) {
  try {
    const data = cached("stats:etrei", () => {
      const db = getDb();
      const global = db.prepare(`
        SELECT ROUND(AVG(prix),0) as avg_prix, COUNT(*) as vol,
          ROUND(AVG(bon_entourage),2) as avg_env,
          ROUND(100.0*SUM(CASE WHEN haut_standing='1.0' OR haut_standing='True' OR haut_standing='1' THEN 1 ELSE 0 END)/COUNT(*),2) as hs_pct
        FROM properties WHERE prix > 0
      `).get();

      const base_prix = 200000;
      const prix_norm = Math.min((global.avg_prix / base_prix) * 40, 40);
      const vol_norm  = Math.min((global.vol / 50000) * 20, 20);
      const env_norm  = (global.avg_env || 0) * 20;
      const hs_norm   = (global.hs_pct || 0) / 100 * 20;
      const index     = +(prix_norm + vol_norm + env_norm + hs_norm).toFixed(1);

      const byGov = db.prepare(`
        SELECT gouvernerat,
          ROUND(AVG(prix),0) as avg_prix, COUNT(*) as vol,
          ROUND(AVG(bon_entourage),2) as avg_env,
          ROUND(100.0*SUM(CASE WHEN haut_standing='1.0' OR haut_standing='True' OR haut_standing='1' THEN 1 ELSE 0 END)/COUNT(*),2) as hs_pct
        FROM properties WHERE prix > 0 AND gouvernerat != ''
        GROUP BY gouvernerat ORDER BY avg_prix DESC
      `).all();

      return {
        global: { index, label: index > 70 ? "Marché Chaud" : index > 40 ? "Marché Actif" : "Marché Calme" },
        by_gouvernerat: byGov.map(r => {
          const pn = Math.min((r.avg_prix / base_prix) * 40, 40);
          const vn = Math.min((r.vol / 5000) * 20, 20);
          const en = (r.avg_env || 0) * 20;
          const hn = (r.hs_pct || 0) / 100 * 20;
          return { gouvernerat: r.gouvernerat, index: +(pn+vn+en+hn).toFixed(1) };
        }),
      };
    });
    res.json(data);
  } catch (err) { next(err); }
}

module.exports = { overview, byGouvernerat, byType, byContrat, priceDistribution, monthlyTrend, amenities, priceHeatmap, standingDistribution, insights, etrei };
