"""
Import bigfinal_realestate_Cleaned.csv into SQLite.
Run once: python import_data.py
"""
import sqlite3, csv, os, sys, pathlib

csv.field_size_limit(10_000_000)

CSV_PATH = pathlib.Path(__file__).parent.parent / "bigfinal_realestate_Cleaned.csv"
DB_DIR   = pathlib.Path(__file__).parent.parent / "data"
DB_PATH  = DB_DIR / "estatamind.db"

DB_DIR.mkdir(exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS properties (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    adresse         TEXT,
    annee_constr    TEXT,
    bus             REAL,
    caracteristiques TEXT,
    contrat         TEXT,
    date_publication TEXT,
    description     TEXT,
    ecole           REAL,
    etage           TEXT,
    gouvernerat     TEXT,
    has_ascenseur   REAL,
    has_balcon      REAL,
    has_chaffage    REAL,
    has_climatisation REAL,
    has_garage      REAL,
    has_gardien     REAL,
    has_jardin      REAL,
    has_parking     REAL,
    has_piscine     REAL,
    has_terrasse    REAL,
    hopital         REAL,
    images          TEXT,
    latitude        REAL,
    longitude       REAL,
    magasin         REAL,
    marche          REAL,
    pharmacie       REAL,
    pieces          REAL,
    prix            REAL,
    railway         REAL,
    restaurant      REAL,
    source          TEXT,
    standing        TEXT,
    surface         REAL,
    titre           TEXT,
    type            TEXT,
    url             TEXT,
    ville           TEXT,
    pub_year        INTEGER,
    pub_month       INTEGER,
    desc_clean      TEXT,
    carac_block     TEXT,
    contrat_carac   TEXT,
    surface_carac   REAL,
    code_postal_carac TEXT,
    geo_precision   TEXT,
    bon_entourage   REAL,
    haut_standing   TEXT,
    prix_m2         REAL
);
CREATE INDEX IF NOT EXISTS idx_gouvernerat ON properties(gouvernerat);
CREATE INDEX IF NOT EXISTS idx_type        ON properties(type);
CREATE INDEX IF NOT EXISTS idx_contrat     ON properties(contrat);
CREATE INDEX IF NOT EXISTS idx_ville       ON properties(ville);
CREATE INDEX IF NOT EXISTS idx_pub_year    ON properties(pub_year);
CREATE INDEX IF NOT EXISTS idx_prix        ON properties(prix);
"""

COL_MAP = {
    "adresse": "adresse", "annee_constr": "annee_constr",
    "bus": "bus", "caracteristiques": "caracteristiques", "contrat": "contrat",
    "date_publication": "date_publication", "description": "description",
    "ecole": "ecole", "etage": "etage", "gouvernerat": "gouvernerat",
    "has_ascenseur": "has_ascenseur", "has_balcon": "has_balcon",
    "has_chaffage": "has_chaffage", "has_climatisation": "has_climatisation",
    "has_garage": "has_garage", "has_gardien": "has_gardien",
    "has_jardin": "has_jardin", "has_parking": "has_parking",
    "has_piscine": "has_piscine", "has_terrasse": "has_terrasse",
    "hopital": "hopital", "images": "images", "latitude": "latitude",
    "longitude": "longitude", "magasin": "magasin", "marche": "marche",
    "pharmacie": "pharmacie", "pieces": "pieces", "prix": "prix",
    "railway": "railway", "restaurant": "restaurant", "source": "source",
    "standing": "standing", "surface": "surface", "titre": "titre",
    "type": "type", "url": "url", "ville": "ville", "pub_year": "pub_year",
    "pub_month": "pub_month", "desc_clean": "desc_clean",
    "carac_block": "carac_block", "contrat_carac": "contrat_carac",
    "surface_carac": "surface_carac", "code_postal_carac": "code_postal_carac",
    "geo_precision": "geo_precision", "bon_entourage": "bon_entourage",
    "haut_standing": "haut_standing", "prix_m2": "prix_m2",
}

FLOATS = {"bus","ecole","has_ascenseur","has_balcon","has_chaffage","has_climatisation",
          "has_garage","has_gardien","has_jardin","has_parking","has_piscine","has_terrasse",
          "hopital","latitude","longitude","magasin","marche","pharmacie","pieces","prix",
          "railway","restaurant","surface","surface_carac","bon_entourage","prix_m2"}
INTS   = {"pub_year","pub_month"}

def coerce(col, val):
    val = val.strip()
    if val == "" or val.lower() in ("nan","none","null"):
        return None
    if col in FLOATS:
        try: return float(val)
        except: return None
    if col in INTS:
        try: return int(float(val))
        except: return None
    return val

def main():
    if not CSV_PATH.exists():
        sys.exit(f"CSV not found: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()

    existing = cur.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
    if existing > 0:
        print(f"DB already has {existing:,} rows — skipping import. Delete {DB_PATH} to re-import.")
        conn.close()
        return

    db_cols  = list(COL_MAP.keys())
    placeholders = ",".join("?" * len(db_cols))
    insert_sql = f"INSERT INTO properties ({','.join(db_cols)}) VALUES ({placeholders})"

    batch, total, BATCH = [], 0, 500
    print(f"Importing {CSV_PATH} → {DB_PATH} …")

    with open(CSV_PATH, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vals = [coerce(col, row.get(csv_col, "")) for col, csv_col in COL_MAP.items()]
            batch.append(vals)
            if len(batch) >= BATCH:
                cur.executemany(insert_sql, batch)
                conn.commit()
                total += len(batch)
                batch = []
                print(f"  {total:,} rows…", end="\r")

    if batch:
        cur.executemany(insert_sql, batch)
        conn.commit()
        total += len(batch)

    print(f"\nDone — {total:,} rows imported.")
    conn.close()

if __name__ == "__main__":
    main()
