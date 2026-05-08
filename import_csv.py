import sqlite3, csv, datetime, sys, ast, re
csv.field_size_limit(10_000_000)

def normalize_images(raw: str) -> str | None:
    """Normalise both pipe-joined and stringified-list image columns to 'url | url | ...'"""
    raw = raw.strip()
    if not raw or raw in ('nan', 'None', 'null', '[]'):
        return None
    if raw.startswith('['):
        # Python list string: "['url1', 'url2', ...]"
        try:
            urls = ast.literal_eval(raw)
            if isinstance(urls, list):
                clean = [u.strip().strip("'\"") for u in urls if u and str(u).strip().startswith('http')]
                return ' | '.join(clean) if clean else None
        except Exception:
            urls = re.findall(r'https?://[^\s\'\",\]]+', raw)
            return ' | '.join(urls) if urls else None
    # Already pipe-joined or single URL
    if raw.startswith('http'):
        return raw
    return None

DB  = r"C:\Users\21650\Desktop\DeepL\web\prisma\prisma\dev.db"
CSV = r"C:\Users\21650\Desktop\DeepL\bigfinal_realestate_Cleaned.csv"

FLOAT_COLS = {
    'prix','prix_original','prix_m2','prix_q75_contrat',
    'surface','surface_original','superficie_terrain','latitude','longitude',
}
INT_COLS = {
    'pieces','pieces_original','etage','etage_original','annee_constr',
    'bus','railway','ecole','hopital','pharmacie','magasin','marche',
    'restaurant','pub_year','pub_month',
}
BOOL_COLS = {
    'has_ascenseur','has_balcon','has_chaffage','has_climatisation',
    'has_garage','has_gardien','has_jardin','has_parking','has_piscine',
    'has_terrasse','haut_standing','bon_entourage',
}

CSV_COLS = [
    'adresse','agence','annee_constr','chauffage','climatisation','codep',
    'constructible','cuisine','date_publication','delegation','description',
    'fonds','gouvernerat','installations_sportives','url','localite','pieces',
    'other_data','plein_air','prix','reference','salle_de_bain','service',
    'surface','superficie_terrain','tel','type','contrat','ville',
    'prix_original','surface_original','pieces_original','etage','etage_original',
    'pub_year','pub_month','has_ascenseur','has_balcon','has_chaffage',
    'has_climatisation','has_garage','has_gardien','has_jardin','has_parking',
    'has_piscine','has_terrasse','bus','railway','ecole','hopital','pharmacie',
    'magasin','marche','restaurant','standing','titre','prix_m2','desc_clean',
    'carac_block','bon_entourage_llm','latitude','longitude','geo_precision',
    'bon_entourage','prix_q75_contrat','haut_standing','caracteristiques',
    'images','source','contrat_carac','surface_carac','code_postal_carac',
]

NOW = datetime.datetime.utcnow().isoformat()
BATCH = 5000

def cv(v, col):
    v = v.strip() if v else ''
    if not v:
        return None
    if col in FLOAT_COLS:
        try: return float(v)
        except: return None
    if col in INT_COLS:
        try: return int(float(v))
        except: return None
    if col in BOOL_COLS:
        try: return 1 if float(v) else 0
        except: return None
    if col == 'images':
        return normalize_images(v)
    return v.replace('\x00', '')

INSERT_COLS = CSV_COLS + ['createdAt','updatedAt','isUserCreated','ownerId']
SQL = (
    f"INSERT INTO Listing ({','.join(INSERT_COLS)}) "
    f"VALUES ({','.join(['?']*len(INSERT_COLS))})"
)

db = sqlite3.connect(DB)
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA synchronous=NORMAL")

print("Clearing old scraped rows…")
db.execute("DELETE FROM Listing WHERE isUserCreated=0 OR isUserCreated IS NULL")
db.commit()

print("Importing CSV…")
batch, total, errors = [], 0, 0

with open(CSV, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            vals = [cv(row.get(c,''), c) for c in CSV_COLS]
            vals += [NOW, NOW, 0, None]
            batch.append(vals)
        except Exception as e:
            errors += 1
            continue

        if len(batch) >= BATCH:
            db.executemany(SQL, batch)
            db.commit()
            total += len(batch)
            print(f"  {total:,} rows…", end='\r', flush=True)
            batch = []

if batch:
    db.executemany(SQL, batch)
    db.commit()
    total += len(batch)

db.close()
print(f"\nDone — {total:,} rows imported, {errors} skipped.")
