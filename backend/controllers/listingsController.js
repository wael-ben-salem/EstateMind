const { getDb } = require("../config/database");

function buildWhere(q) {
  const clauses = ["1=1"];
  const params  = [];

  if (q.gouvernerat) { clauses.push("gouvernerat = ?"); params.push(q.gouvernerat); }
  if (q.ville)       { clauses.push("ville = ?");       params.push(q.ville); }
  if (q.type)        { clauses.push("type = ?");        params.push(q.type); }
  if (q.contrat)     { clauses.push("contrat = ?");     params.push(q.contrat); }
  if (q.standing)    { clauses.push("standing = ?");    params.push(q.standing); }
  if (q.prix_min)    { clauses.push("prix >= ?");       params.push(+q.prix_min); }
  if (q.prix_max)    { clauses.push("prix <= ?");       params.push(+q.prix_max); }
  if (q.surface_min) { clauses.push("surface >= ?");    params.push(+q.surface_min); }
  if (q.surface_max) { clauses.push("surface <= ?");    params.push(+q.surface_max); }
  if (q.pieces)      { clauses.push("pieces >= ?");     params.push(+q.pieces); }
  if (q.haut_standing === "true") {
    clauses.push("(haut_standing = '1.0' OR haut_standing = 'True' OR haut_standing = '1')");
  }
  if (q.bon_entourage === "true") { clauses.push("bon_entourage >= 0.5"); }
  if (q.has_parking  === "true")  { clauses.push("has_parking = 1"); }
  if (q.has_piscine  === "true")  { clauses.push("has_piscine = 1"); }
  if (q.has_jardin   === "true")  { clauses.push("has_jardin = 1"); }
  if (q.has_garage   === "true")  { clauses.push("has_garage = 1"); }
  if (q.has_ascenseur=== "true")  { clauses.push("has_ascenseur = 1"); }
  if (q.has_climatisation==="true"){ clauses.push("has_climatisation = 1"); }
  if (q.search) {
    clauses.push("(titre LIKE ? OR description LIKE ?)");
    const like = `%${q.search}%`;
    params.push(like, like);
  }
  return { where: clauses.join(" AND "), params };
}

function list(req, res, next) {
  try {
    const db    = getDb();
    const page  = Math.max(1, parseInt(req.query.page  || "1"));
    const limit = Math.min(100, Math.max(1, parseInt(req.query.limit || "25")));
    const sort  = ["prix","surface","pieces","date_publication","pub_year"].includes(req.query.sort) ? req.query.sort : "id";
    const dir   = req.query.dir === "asc" ? "ASC" : "DESC";

    const { where, params } = buildWhere(req.query);
    const total = db.prepare(`SELECT COUNT(*) AS n FROM properties WHERE ${where}`).get(...params).n;
    const rows  = db.prepare(
      `SELECT id,titre,type,contrat,ville,gouvernerat,prix,surface,pieces,etage,standing,
              haut_standing,bon_entourage,images,url,date_publication,source,latitude,longitude,prix_m2
       FROM properties WHERE ${where}
       ORDER BY ${sort} ${dir} LIMIT ? OFFSET ?`
    ).all(...params, limit, (page - 1) * limit);

    res.json({ data: rows, total, page, pages: Math.ceil(total / limit) });
  } catch (err) { next(err); }
}

function detail(req, res, next) {
  try {
    const row = getDb().prepare("SELECT * FROM properties WHERE id = ?").get(req.params.id);
    if (!row) return res.status(404).json({ error: "Not found" });
    res.json(row);
  } catch (err) { next(err); }
}

function similar(req, res, next) {
  try {
    const base = getDb().prepare("SELECT * FROM properties WHERE id = ?").get(req.params.id);
    if (!base) return res.status(404).json({ error: "Not found" });
    const rows = getDb().prepare(`
      SELECT id,titre,type,contrat,ville,gouvernerat,prix,surface,images,url
      FROM properties
      WHERE gouvernerat = ? AND type = ? AND prix BETWEEN ? AND ? AND id != ?
      ORDER BY ABS(prix - ?) ASC LIMIT 5
    `).all(base.gouvernerat, base.type, base.prix*0.8, base.prix*1.2, base.id, base.prix);
    res.json(rows);
  } catch (err) { next(err); }
}

function exportCsv(req, res, next) {
  try {
    const { where, params } = buildWhere(req.query);
    const rows = getDb().prepare(
      `SELECT titre,type,contrat,ville,gouvernerat,prix,surface,pieces,standing,url,date_publication
       FROM properties WHERE ${where} LIMIT 5000`
    ).all(...params);

    const header = "titre,type,contrat,ville,gouvernerat,prix,surface,pieces,standing,url,date_publication\n";
    const body   = rows.map(r =>
      [r.titre,r.type,r.contrat,r.ville,r.gouvernerat,r.prix,r.surface,r.pieces,r.standing,r.url,r.date_publication]
        .map(v => `"${String(v ?? "").replace(/"/g, '""')}"`)
        .join(",")
    ).join("\n");

    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", `attachment; filename="estatamind_export.csv"`);
    res.send(header + body);
  } catch (err) { next(err); }
}

function villes(req, res, next) {
  try {
    const db = getDb();
    const q = req.query.gouvernerat
      ? db.prepare("SELECT DISTINCT ville FROM properties WHERE gouvernerat = ? AND ville IS NOT NULL AND ville != '' ORDER BY ville").all(req.query.gouvernerat)
      : db.prepare("SELECT DISTINCT ville FROM properties WHERE ville IS NOT NULL AND ville != '' ORDER BY ville LIMIT 200").all();
    res.json(q.map(r => r.ville));
  } catch (err) { next(err); }
}

function score(req, res, next) {
  try {
    const row = getDb().prepare("SELECT * FROM properties WHERE id = ?").get(req.params.id);
    if (!row) return res.status(404).json({ error: "Not found" });

    const db = getDb();
    const govAvg = db.prepare(
      "SELECT AVG(prix/surface) as ppm FROM properties WHERE gouvernerat=? AND type=? AND prix>0 AND surface>0"
    ).get(row.gouvernerat, row.type);

    const ppm = row.prix && row.surface ? row.prix / row.surface : null;
    const govPpm = govAvg?.ppm || ppm || 1;

    let score = 50;
    if (ppm) score += Math.max(-15, Math.min(15, (1 - ppm / govPpm) * 30));
    if (row.bon_entourage) score += row.bon_entourage * 15;
    if (row.haut_standing === "1.0" || row.haut_standing === "True") score += 10;
    const amenityCount = ["has_parking","has_piscine","has_jardin","has_terrasse","has_ascenseur","has_climatisation","has_garage","has_balcon"]
      .filter(a => row[a] == 1).length;
    score += amenityCount * 1.5;
    score = Math.max(0, Math.min(100, Math.round(score)));

    const label = score >= 80 ? "Bonne affaire" : score >= 60 ? "Investissement intéressant" : score >= 40 ? "Prix marché" : "Surévalué";
    res.json({ id: row.id, score, label, details: { prix_m2: ppm, gov_prix_m2: govPpm, bon_entourage: row.bon_entourage, amenities: amenityCount } });
  } catch (err) { next(err); }
}

module.exports = { list, detail, similar, exportCsv, villes, score };
