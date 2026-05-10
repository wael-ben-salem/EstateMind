const { getDb } = require("../config/database");
const { cached } = require("../services/cacheService");

function clusters(req, res, next) {
  try {
    const precision = Math.max(1, Math.min(3, parseInt(req.query.zoom || "2")));
    const key = `map:clusters:${precision}`;
    const data = cached(key, () =>
      getDb().prepare(`
        SELECT
          ROUND(latitude, ${precision}) AS lat,
          ROUND(longitude, ${precision}) AS lng,
          COUNT(*) AS count,
          gouvernerat
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND latitude != 0 AND longitude != 0
          AND latitude BETWEEN 30 AND 38
          AND longitude BETWEEN 7 AND 12
        GROUP BY ROUND(latitude, ${precision}), ROUND(longitude, ${precision}), gouvernerat
        HAVING count > 0
        ORDER BY count DESC
        LIMIT 5000
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function heatmap(req, res, next) {
  try {
    const data = cached("map:heatmap", () =>
      getDb().prepare(`
        SELECT latitude AS lat, longitude AS lng,
               COALESCE(prix, 100000) / 1000000.0 AS weight
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND latitude BETWEEN 30 AND 38 AND longitude BETWEEN 7 AND 12
        LIMIT 10000
      `).all()
    );
    res.json(data);
  } catch (err) { next(err); }
}

function gouverneratStats(req, res, next) {
  try {
    const name = req.params.name;
    const db = getDb();
    const stats = db.prepare(`
      SELECT COUNT(*) AS total, ROUND(AVG(prix),0) AS avg_prix,
             prix AS median_prix, ROUND(AVG(surface),0) AS avg_surface
      FROM properties WHERE gouvernerat = ? AND prix > 0
    `).get(name);
    const top_villes = db.prepare(`
      SELECT ville, COUNT(*) AS n FROM properties WHERE gouvernerat = ? AND ville != ''
      GROUP BY ville ORDER BY n DESC LIMIT 3
    `).all(name);
    const types = db.prepare(`
      SELECT type, COUNT(*) AS n FROM properties WHERE gouvernerat = ? AND type != ''
      GROUP BY type ORDER BY n DESC
    `).all(name);
    res.json({ gouvernerat: name, stats, top_villes, type_distribution: types });
  } catch (err) { next(err); }
}

function choropleth(req, res, next) {
  try {
    const data = cached("map:choropleth", () => {
      const rows = getDb().prepare(`
        SELECT gouvernerat,
               ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
               COUNT(*) AS count
        FROM properties
        WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
        GROUP BY gouvernerat
        ORDER BY avg_prix DESC
      `).all();
      const maxPrix = rows[0]?.avg_prix || 1;
      return rows.map(r => ({
        ...r,
        color_value: r.avg_prix / maxPrix,
      }));
    });
    res.json(data);
  } catch (err) { next(err); }
}

function timeMachine(req, res, next) {
  try {
    const year  = parseInt(req.query.year  || "2025");
    const month = parseInt(req.query.month || "1");
    const data = getDb().prepare(`
      SELECT gouvernerat,
             ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
             COUNT(*) AS count
      FROM properties
      WHERE pub_year = ? AND pub_month = ? AND gouvernerat != ''
      GROUP BY gouvernerat ORDER BY count DESC
    `).all(year, month);
    res.json(data);
  } catch (err) { next(err); }
}

module.exports = { clusters, heatmap, gouverneratStats, choropleth, timeMachine };
