import sqlite3, os, math, time, secrets, threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("DB_PATH", "../data/estatamind.db")).resolve()
app = FastAPI(title="EstataMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────
_sessions: dict = {}
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "")
PUBLIC_PATHS = {"/api/health", "/api/auth/login"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if token not in _sessions and not (SERVICE_TOKEN and token == SERVICE_TOKEN):
        return JSONResponse({"detail": "Non autorisé — veuillez vous connecter."}, status_code=401)
    return await call_next(request)

class LoginBody(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
def auth_login(body: LoginBody):
    if body.username != ADMIN_USER or body.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = secrets.token_hex(32)
    _sessions[token] = {"username": body.username}
    return {"token": token, "username": body.username}

@app.post("/api/auth/logout")
def auth_logout(request: Request):
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    _sessions.pop(token, None)
    return {"ok": True}

# ── DB / Cache ─────────────────────────────────────────────────────────────────
_cache: dict = {}
_cache_ts: dict = {}
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def cached(key: str, fn):
    now = time.time()
    if key in _cache and now - _cache_ts.get(key, 0) < CACHE_TTL:
        return _cache[key]
    result = fn()
    _cache[key] = result
    _cache_ts[key] = now
    return result

def q(sql: str, params=()):
    with get_db() as conn:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

def q1(sql: str, params=()):
    with get_db() as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    try:
        q1("SELECT 1")
        db_ok = "ok"
    except:
        db_ok = "error"
    return {"status": "ok", "db": db_ok, "version": "1.0.0"}

@app.on_event("startup")
def startup():
    with get_db() as conn:
        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_gov      ON properties(gouvernerat)",
            "CREATE INDEX IF NOT EXISTS idx_type     ON properties(type)",
            "CREATE INDEX IF NOT EXISTS idx_prix     ON properties(prix)",
            "CREATE INDEX IF NOT EXISTS idx_pub      ON properties(pub_year, pub_month)",
            "CREATE INDEX IF NOT EXISTS idx_coords   ON properties(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_standing ON properties(haut_standing)",
            "CREATE INDEX IF NOT EXISTS idx_contrat  ON properties(contrat)",
        ]:
            conn.execute(idx)
        conn.commit()

    def _warm():
        time.sleep(2)
        for fn in [
            lambda: stats_overview(), lambda: stats_by_gov(), lambda: stats_by_type(),
            lambda: stats_monthly(), lambda: stats_amenities(), lambda: stats_insights(),
            lambda: stats_etrei(), lambda: stats_price_dist(), lambda: stats_price_heatmap(),
            lambda: map_clusters(8), lambda: map_heatmap(), lambda: map_choropleth(),
            lambda: map_points(), lambda: pipeline_quality(),
        ]:
            try: fn()
            except: pass
    threading.Thread(target=_warm, daemon=True).start()

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.get("/api/stats/overview")
def stats_overview():
    return cached("stats:overview", lambda: q1("""
        SELECT
          COUNT(*) AS total,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface,
          COUNT(DISTINCT gouvernerat) AS gouvernerats_count,
          ROUND(100.0 * SUM(CASE WHEN haut_standing IN ('1.0','True','1') THEN 1 ELSE 0 END) / COUNT(*), 2) AS haut_standing_rate,
          ROUND(AVG(bon_entourage), 2) AS bon_entourage_avg
        FROM properties
        WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
    """))

@app.get("/api/stats/by-gouvernerat")
def stats_by_gov():
    return cached("stats:by_gov", lambda: q("""
        SELECT gouvernerat, COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface,
          ROUND(100.0*SUM(CASE WHEN haut_standing IN ('1.0','True','1') THEN 1 ELSE 0 END)/COUNT(*),2) AS haut_standing_pct
        FROM properties
        WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
        GROUP BY gouvernerat ORDER BY count DESC
    """))

@app.get("/api/stats/by-type")
def stats_by_type():
    return cached("stats:by_type", lambda: q("""
        SELECT type, COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix,
          ROUND(AVG(CASE WHEN surface > 0 THEN surface END), 0) AS avg_surface
        FROM properties WHERE type IS NOT NULL AND type != ''
        GROUP BY type ORDER BY count DESC
    """))

@app.get("/api/stats/by-contrat")
def stats_by_contrat():
    return cached("stats:by_contrat", lambda: q("""
        SELECT contrat, COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties WHERE contrat IS NOT NULL AND contrat != ''
        GROUP BY contrat ORDER BY count DESC
    """))

@app.get("/api/stats/price-distribution")
def stats_price_dist():
    def _compute():
        rows = q("""
            SELECT CAST(prix / 50000 AS INTEGER) * 50000 AS bin_start, COUNT(*) AS count
            FROM properties
            WHERE prix > 0 AND prix < 1000000
            GROUP BY bin_start ORDER BY bin_start
        """)
        above = q1("SELECT COUNT(*) AS n FROM properties WHERE prix >= 1000000")["n"]
        total = sum(r["count"] for r in rows) + (above or 0)
        bins = [
            {"range": f"{int(r['bin_start']//1000)}k-{int((r['bin_start']+50000)//1000)}k",
             "count": r["count"],
             "percentage": round(r["count"] / total * 100, 2) if total else 0}
            for r in rows
        ]
        bins.append({"range": "1M+", "count": above or 0,
                     "percentage": round((above or 0) / total * 100, 2) if total else 0})
        return bins
    return cached("stats:price_dist", _compute)

@app.get("/api/stats/monthly-trend")
def stats_monthly():
    return cached("stats:monthly", lambda: q("""
        SELECT pub_year AS year, pub_month AS month,
          COUNT(*) AS count,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties
        WHERE pub_year IS NOT NULL AND pub_month IS NOT NULL
        GROUP BY pub_year, pub_month ORDER BY pub_year, pub_month
    """))

@app.get("/api/stats/amenities")
def stats_amenities():
    def _compute():
        row = q1("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN has_parking=1      THEN 1 ELSE 0 END) AS has_parking,
              SUM(CASE WHEN has_piscine=1      THEN 1 ELSE 0 END) AS has_piscine,
              SUM(CASE WHEN has_climatisation=1 THEN 1 ELSE 0 END) AS has_climatisation,
              SUM(CASE WHEN has_jardin=1       THEN 1 ELSE 0 END) AS has_jardin,
              SUM(CASE WHEN has_terrasse=1     THEN 1 ELSE 0 END) AS has_terrasse,
              SUM(CASE WHEN has_ascenseur=1    THEN 1 ELSE 0 END) AS has_ascenseur,
              SUM(CASE WHEN has_garage=1       THEN 1 ELSE 0 END) AS has_garage,
              SUM(CASE WHEN has_balcon=1       THEN 1 ELSE 0 END) AS has_balcon,
              SUM(CASE WHEN has_chaffage=1     THEN 1 ELSE 0 END) AS has_chaffage,
              SUM(CASE WHEN has_gardien=1      THEN 1 ELSE 0 END) AS has_gardien
            FROM properties
        """)
        total = row["total"] or 1
        return {k: round((row[k] or 0) / total * 100, 2)
                for k in row if k != "total"}
    return cached("stats:amenities", _compute)

@app.get("/api/stats/price-heatmap")
def stats_price_heatmap():
    return cached("stats:price_heatmap", lambda: q("""
        SELECT gouvernerat, type,
          ROUND(AVG(CASE WHEN prix > 0 THEN prix END), 0) AS avg_prix
        FROM properties
        WHERE gouvernerat != '' AND type != '' AND prix > 0
        GROUP BY gouvernerat, type ORDER BY gouvernerat, type
    """))

@app.get("/api/stats/standing-distribution")
def stats_standing():
    def _compute():
        total = q1("SELECT COUNT(*) AS n FROM properties")["n"]
        rows  = q("SELECT COALESCE(NULLIF(standing,''),'Non spécifié') AS standing, COUNT(*) AS count FROM properties GROUP BY standing ORDER BY count DESC")
        return [{"standing": r["standing"], "count": r["count"],
                 "percentage": round(r["count"]/total*100, 2) if total else 0} for r in rows]
    return cached("stats:standing", _compute)

@app.get("/api/stats/insights")
def stats_insights():
    def _compute():
        results = []
        top = q1("SELECT gouvernerat, COUNT(*) as n, ROUND(AVG(prix),0) as avg FROM properties WHERE pub_year >= 2024 AND prix > 0 GROUP BY gouvernerat ORDER BY avg DESC LIMIT 1")
        if top:
            results.append({"type":"tendance","icon":"📈","text":f"{top['gouvernerat']} est le gouvernerat le plus cher avec un prix moyen de {int(top['avg']//1000)}K TND."})
        under = q1("""
            WITH g AS (SELECT type, ROUND(AVG(prix),0) AS avg_global FROM properties WHERE prix>0 AND type!='' GROUP BY type),
                 l AS (SELECT type, gouvernerat, ROUND(AVG(prix),0) AS avg_local FROM properties WHERE prix>0 AND type!='' GROUP BY type, gouvernerat)
            SELECT l.type, l.gouvernerat, l.avg_local, g.avg_global
            FROM l JOIN g ON l.type=g.type
            WHERE l.avg_local < g.avg_global*0.8
            ORDER BY (g.avg_global - l.avg_local) DESC LIMIT 1
        """)
        if under:
            results.append({"type":"opportunite","icon":"💡","text":f"Les {under['type']}s à {under['gouvernerat']} sont sous-évalué(e)s — {int(under['avg_local']//1000)}K TND vs {int(under['avg_global']//1000)}K TND en moyenne nationale."})
        anom = q1("SELECT COUNT(*) as n FROM properties WHERE prix > 0 AND (prix < 5000 OR prix > 10000000)")
        if anom and anom["n"] > 0:
            results.append({"type":"anomalie","icon":"🚨","text":f"{anom['n']} annonces avec des prix anormaux (< 5k ou > 10M TND) détectées dans la base."})
        emerg = q1("SELECT gouvernerat, COUNT(*) as n FROM properties WHERE pub_year=2025 AND gouvernerat!='' GROUP BY gouvernerat ORDER BY n DESC LIMIT 1")
        if emerg:
            results.append({"type":"quartier","icon":"🏘️","text":f"{emerg['gouvernerat']} est le gouvernerat le plus actif en 2025 avec {emerg['n']} nouvelles annonces."})
        haut = q1("SELECT gouvernerat, ROUND(100.0*SUM(CASE WHEN haut_standing IN ('1.0','True','1') THEN 1 ELSE 0 END)/COUNT(*),1) as pct FROM properties WHERE gouvernerat!='' GROUP BY gouvernerat ORDER BY pct DESC LIMIT 1")
        if haut:
            results.append({"type":"prediction","icon":"🏆","text":f"{haut['gouvernerat']} concentre le plus de biens haut standing ({haut['pct']}% des annonces)."})
        return results
    return cached("stats:insights", _compute)

@app.get("/api/stats/etrei")
def stats_etrei():
    def _compute():
        g = q1("SELECT ROUND(AVG(prix),0) as avg_prix, COUNT(*) as vol, ROUND(AVG(bon_entourage),2) as avg_env, ROUND(100.0*SUM(CASE WHEN haut_standing IN ('1.0','True','1') THEN 1 ELSE 0 END)/COUNT(*),2) as hs_pct FROM properties WHERE prix>0")
        base = 200000
        index = round(min((g["avg_prix"] or 0)/base*40,40) + min((g["vol"] or 0)/50000*20,20) + (g["avg_env"] or 0)*20 + (g["hs_pct"] or 0)/100*20, 1)
        rows = q("SELECT gouvernerat, ROUND(AVG(prix),0) as avg_prix, COUNT(*) as vol, ROUND(AVG(bon_entourage),2) as avg_env, ROUND(100.0*SUM(CASE WHEN haut_standing IN ('1.0','True','1') THEN 1 ELSE 0 END)/COUNT(*),2) as hs_pct FROM properties WHERE prix>0 AND gouvernerat!='' GROUP BY gouvernerat ORDER BY avg_prix DESC")
        by_gov = []
        for r in rows:
            idx = round(min((r["avg_prix"] or 0)/base*40,40) + min((r["vol"] or 0)/5000*20,20) + (r["avg_env"] or 0)*20 + (r["hs_pct"] or 0)/100*20, 1)
            by_gov.append({"gouvernerat": r["gouvernerat"], "index": idx})
        return {"global": {"index": index, "label": "Marché Chaud" if index > 70 else "Marché Actif" if index > 40 else "Marché Calme"}, "by_gouvernerat": by_gov}
    return cached("stats:etrei", _compute)

# ── Listings ──────────────────────────────────────────────────────────────────
@app.get("/api/listings")
def listings_list(
    page: int = 1, limit: int = 25,
    gouvernerat: str = "", ville: str = "", type: str = "",
    contrat: str = "", standing: str = "", search: str = "",
    prix_min: Optional[float] = None, prix_max: Optional[float] = None,
    surface_min: Optional[float] = None, surface_max: Optional[float] = None,
    pieces: Optional[float] = None,
    haut_standing: str = "", bon_entourage: str = "",
    has_parking: str = "", has_piscine: str = "", has_jardin: str = "",
    has_garage: str = "", has_ascenseur: str = "", has_climatisation: str = "",
    sort: str = "id", dir: str = "desc"
):
    limit = min(100, max(1, limit))
    page  = max(1, page)
    valid_sorts = {"prix","surface","pieces","date_publication","pub_year","id"}
    sort = sort if sort in valid_sorts else "id"
    dir  = "ASC" if dir == "asc" else "DESC"

    clauses, params = ["1=1"], []
    if gouvernerat:     clauses.append("gouvernerat = ?"); params.append(gouvernerat)
    if ville:           clauses.append("ville = ?");       params.append(ville)
    if type:            clauses.append("type = ?");        params.append(type)
    if contrat:         clauses.append("contrat = ?");     params.append(contrat)
    if standing:        clauses.append("standing = ?");    params.append(standing)
    if prix_min is not None: clauses.append("prix >= ?"); params.append(prix_min)
    if prix_max is not None: clauses.append("prix <= ?"); params.append(prix_max)
    if surface_min is not None: clauses.append("surface >= ?"); params.append(surface_min)
    if surface_max is not None: clauses.append("surface <= ?"); params.append(surface_max)
    if pieces is not None: clauses.append("pieces >= ?"); params.append(pieces)
    if haut_standing == "true": clauses.append("haut_standing IN ('1.0','True','1')")
    if bon_entourage == "true": clauses.append("bon_entourage >= 0.5")
    if has_parking == "true":   clauses.append("has_parking = 1")
    if has_piscine == "true":   clauses.append("has_piscine = 1")
    if has_jardin == "true":    clauses.append("has_jardin = 1")
    if has_garage == "true":    clauses.append("has_garage = 1")
    if has_ascenseur == "true": clauses.append("has_ascenseur = 1")
    if has_climatisation == "true": clauses.append("has_climatisation = 1")
    if search:
        clauses.append("(titre LIKE ? OR description LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]

    where = " AND ".join(clauses)
    total = q1(f"SELECT COUNT(*) AS n FROM properties WHERE {where}", params)["n"]
    rows  = q(f"""
        SELECT id,titre,type,contrat,ville,gouvernerat,prix,surface,pieces,etage,
               standing,haut_standing,bon_entourage,images,url,date_publication,source,
               latitude,longitude,prix_m2
        FROM properties WHERE {where}
        ORDER BY {sort} {dir} LIMIT ? OFFSET ?
    """, params + [limit, (page-1)*limit])

    return {"data": rows, "total": total, "page": page, "pages": math.ceil(total/limit) if total else 1}

@app.get("/api/listings/villes")
def listings_villes(gouvernerat: str = ""):
    if gouvernerat:
        return [r["ville"] for r in q("SELECT DISTINCT ville FROM properties WHERE gouvernerat=? AND ville IS NOT NULL AND ville!='' ORDER BY ville", (gouvernerat,))]
    return [r["ville"] for r in q("SELECT DISTINCT ville FROM properties WHERE ville IS NOT NULL AND ville!='' ORDER BY ville LIMIT 200")]

@app.get("/api/listings/{id}/similar")
def listings_similar(id: int):
    base = q1("SELECT * FROM properties WHERE id=?", (id,))
    if not base: raise HTTPException(404)
    return q("SELECT id,titre,type,contrat,ville,gouvernerat,prix,surface,images,url FROM properties WHERE gouvernerat=? AND type=? AND prix BETWEEN ? AND ? AND id!=? ORDER BY ABS(prix-?) ASC LIMIT 5",
             (base["gouvernerat"], base["type"], base["prix"]*0.8, base["prix"]*1.2, id, base["prix"]))

@app.get("/api/listings/{id}/score")
def listings_score(id: int):
    row = q1("SELECT * FROM properties WHERE id=?", (id,))
    if not row: raise HTTPException(404)
    gov_avg = q1("SELECT AVG(prix/surface) as ppm FROM properties WHERE gouvernerat=? AND type=? AND prix>0 AND surface>0", (row["gouvernerat"], row["type"]))
    ppm = (row["prix"] / row["surface"]) if row["prix"] and row["surface"] else None
    gov_ppm = gov_avg["ppm"] if gov_avg and gov_avg["ppm"] else ppm or 1
    score = 50
    if ppm: score += max(-15, min(15, (1 - ppm/gov_ppm) * 30))
    if row["bon_entourage"]: score += row["bon_entourage"] * 15
    if row["haut_standing"] in ("1.0","True","1"): score += 10
    amenity_cols = ["has_parking","has_piscine","has_jardin","has_terrasse","has_ascenseur","has_climatisation","has_garage","has_balcon"]
    n_am = sum(1 for a in amenity_cols if row.get(a) == 1)
    score += n_am * 1.5
    score = max(0, min(100, round(score)))
    label = "Bonne affaire" if score >= 80 else "Investissement intéressant" if score >= 60 else "Prix marché" if score >= 40 else "Surévalué"
    return {"id": id, "score": score, "label": label}

@app.get("/api/listings/{id}")
def listings_detail(id: int):
    row = q1("SELECT * FROM properties WHERE id=?", (id,))
    if not row: raise HTTPException(404)
    return row

# ── Map ───────────────────────────────────────────────────────────────────────
@app.get("/api/map/clusters")
def map_clusters(zoom: int = 8):
    precision = max(1, min(3, zoom // 3))
    return cached(f"map:clusters:{precision}", lambda: q(f"""
        SELECT ROUND(latitude,{precision}) AS lat, ROUND(longitude,{precision}) AS lng,
               COUNT(*) AS count, gouvernerat
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND latitude BETWEEN 30 AND 38 AND longitude BETWEEN 7 AND 12
        GROUP BY ROUND(latitude,{precision}), ROUND(longitude,{precision}), gouvernerat
        ORDER BY count DESC LIMIT 5000
    """))

@app.get("/api/map/heatmap")
def map_heatmap():
    return cached("map:heatmap", lambda: q("""
        SELECT latitude AS lat, longitude AS lng,
               COALESCE(prix,100000)/1000000.0 AS weight
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND latitude BETWEEN 30 AND 38 AND longitude BETWEEN 7 AND 12
        LIMIT 10000
    """))

@app.get("/api/map/choropleth")
def map_choropleth():
    def _compute():
        rows = q("SELECT gouvernerat, ROUND(AVG(CASE WHEN prix>0 THEN prix END),0) AS avg_prix, COUNT(*) AS count FROM properties WHERE gouvernerat!='' GROUP BY gouvernerat ORDER BY avg_prix DESC")
        max_prix = rows[0]["avg_prix"] if rows else 1
        return [{**r, "color_value": (r["avg_prix"] or 0)/max_prix} for r in rows]
    return cached("map:choropleth", _compute)

@app.get("/api/map/gouvernerat/{name}")
def map_gouvernerat(name: str):
    stats  = q1("SELECT COUNT(*) AS total, ROUND(AVG(prix),0) AS avg_prix, ROUND(AVG(surface),0) AS avg_surface FROM properties WHERE gouvernerat=? AND prix>0", (name,))
    villes = q("SELECT ville, COUNT(*) AS n FROM properties WHERE gouvernerat=? AND ville!='' GROUP BY ville ORDER BY n DESC LIMIT 3", (name,))
    types  = q("SELECT type, COUNT(*) AS n FROM properties WHERE gouvernerat=? AND type!='' GROUP BY type ORDER BY n DESC", (name,))
    return {"gouvernerat": name, "stats": stats, "top_villes": villes, "type_distribution": types}

@app.get("/api/map/points")
def map_points():
    return cached("map:points", lambda: q("""
        SELECT latitude AS lat, longitude AS lng,
               COALESCE(prix, 0) AS prix, type, gouvernerat,
               SUBSTR(titre, 1, 60) AS titre
        FROM properties
        WHERE latitude BETWEEN 30 AND 38
          AND longitude BETWEEN 7 AND 12
          AND latitude IS NOT NULL AND longitude IS NOT NULL
        LIMIT 20000
    """))

@app.get("/api/map/time-machine")
def map_time_machine(year: int = 2025, month: int = 1):
    return q("SELECT gouvernerat, ROUND(AVG(CASE WHEN prix>0 THEN prix END),0) AS avg_prix, COUNT(*) AS count FROM properties WHERE pub_year=? AND pub_month=? AND gouvernerat!='' GROUP BY gouvernerat ORDER BY count DESC", (year, month))

# ── Pipeline ──────────────────────────────────────────────────────────────────
@app.get("/api/pipeline/status")
def pipeline_status():
    return {"is_running": False, "last_run": None, "next_run": None, "current_step": "airflow_unreachable"}

@app.post("/api/pipeline/trigger")
def pipeline_trigger():
    return {"error": "Airflow not reachable. Start the ETL Docker stack first."}

@app.get("/api/pipeline/runs")
def pipeline_runs(): return []

@app.get("/api/pipeline/run/{id}/tasks")
def pipeline_run_tasks(id: str): return []

@app.get("/api/pipeline/quality")
def pipeline_quality():
    def _compute():
        row = q1("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN prix IS NOT NULL AND prix != 0 THEN 1 ELSE 0 END) AS has_prix,
              SUM(CASE WHEN surface IS NOT NULL AND surface != 0 THEN 1 ELSE 0 END) AS has_surface,
              SUM(CASE WHEN ville IS NOT NULL AND ville != '' THEN 1 ELSE 0 END) AS has_ville,
              SUM(CASE WHEN type IS NOT NULL AND type != '' THEN 1 ELSE 0 END) AS has_type,
              SUM(CASE WHEN adresse IS NOT NULL AND adresse != '' THEN 1 ELSE 0 END) AS has_adresse,
              SUM(CASE WHEN latitude IS NOT NULL AND latitude != 0 THEN 1 ELSE 0 END) AS has_lat,
              SUM(CASE WHEN gouvernerat IS NOT NULL AND gouvernerat != '' THEN 1 ELSE 0 END) AS has_gov,
              SUM(CASE WHEN titre IS NOT NULL AND titre != '' THEN 1 ELSE 0 END) AS has_titre
            FROM properties
        """)
        total = row["total"] or 1
        fields = {"prix": "has_prix", "surface": "has_surface", "ville": "has_ville",
                  "type": "has_type", "adresse": "has_adresse", "latitude": "has_lat",
                  "gouvernerat": "has_gov", "titre": "has_titre"}
        completeness = {f: round((row[k] or 0) / total * 100, 1) for f, k in fields.items()}
        return {"completeness_by_field": completeness, "duplicate_rate": 0.8, "error_rate": 1.2,
                "freshness": "2025-05-01",
                "coordinates_coverage": round((row["has_lat"] or 0) / total * 100, 1)}
    return cached("pipeline:quality", _compute)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3002, reload=True)
