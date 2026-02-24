# 📍 Location - Data Understanding & Architecture

Documentation complète du projet de scraping immobilier (location) - Mubawab et autres sources.

---

## 📁 Structure des dossiers

```
location/
├── appartement/      # Appartements à louer
├── bureaux/          # Bureaux à louer
├── locaux_com/       # Locaux commerciaux à louer
├── maisons/          # Maisons à louer
├── villas/           # Villas et maisons de luxe à louer
├── utils/            # Utilitaires partagés
│   └── description_extractor.py
├── database/         # Schéma et scripts base de données
└── README.md         # Ce fichier
```

---

## 📊 Data Understanding - Vue d'ensemble

### Types de biens et volumes

| Dossier | Type | Régions | Volumétrie typique |
|---------|------|---------|-------------------|
| **appartement** | Appartements | 8 régions | ~3900 annonces |
| **bureaux** | Bureaux | 6 régions | ~1180 annonces |
| **locaux_com** | Locaux commerciaux | La Marsa | ~160 annonces |
| **maisons** | Maisons | La Marsa | ~320 annonces |
| **villas** | Villas/Maisons luxe | 4 régions | ~1240 annonces |

### Champs communs à tous les types

| Champ | Type | Description |
|-------|------|-------------|
| id | string | ID unique (extrait de l'URL) |
| titre | string | Titre de l'annonce |
| url | string | URL source |
| loyer | float | Loyer en DT |
| loyer_text | string | Texte brut du loyer |
| surface | float | Surface en m² |
| ville, region, quartier, adresse | string | Localisation |
| description_courte | string | Extrait liste |
| description_complete | string | Description page détail |
| equipements | array | Liste d'équipements |
| images | string | URLs séparées par ; |
| date_scraping | string | ISO8601 |
| is_valid | bool | Validation scraping |

### Champs spécifiques par type

| Type | Champs spécifiques |
|------|--------------------|
| **Appartement** | type_appartement, nombre_pieces, nombre_chambres, nombre_sdb, meuble, charges_incluses, duree_location |
| **Bureaux** | type_bureau, type_contrat, nombre_bureaux |
| **Locaux com** | type_local, activites_possibles, amenities_commercial |
| **Maisons** | type_maison, amenities_maison |
| **Villas** | type_villa, surface_terrain, jardin, piscine, niveaux, annee_construction |

---

## 🗄️ Structure de données unifiée (proposition)

Structure qui peut accueillir tous les types de biens :

```json
{
  "id": "string",
  "source_site": "string",
  "source_url": "string",
  "property_category": "appartement|bureaux|locaux_com|maisons|villas",
  "titre": "string",
  "region": "string",
  "ville": "string",
  "quartier": "string",
  "adresse": "string",
  "latitude": "float",
  "longitude": "float",
  
  "type_bien": "string",
  "loyer": "float",
  "loyer_text": "string",
  "loyer_m2": "float",
  "surface": "float",
  "surface_terrain": "float",
  
  "nombre_pieces": "int",
  "nombre_chambres": "int",
  "nombre_sdb": "int",
  "etage": "string",
  
  "description_courte": "string",
  "description_complete": "string",
  "equipements": ["array"],
  "images": ["array"],
  
  "meuble": "bool",
  "charges_incluses": "bool",
  "caution": "string",
  "conditions_location": "object",
  "contact_info": "object",
  
  "caracteristiques": "object",
  "informations_supplementaires": "object",
  
  "date_scraping": "string",
  "scraped_by": "string"
}
```

### Mapping par catégorie

| Catégorie | type_bien | Champs additionnels |
|-----------|-----------|---------------------|
| appartement | type_appartement | duree_location |
| bureaux | type_bureau | type_contrat |
| locaux_com | type_local | activites_possibles |
| maisons | type_maison | - |
| villas | type_villa | jardin, piscine, niveaux |

---

## 🔧 Extraction depuis la description

Le champ `description` contient souvent des informations structurées. Exemple :

> "L'agence immobilière Premier Déclic vous propose à la location Un **Appartement S3** Très Haut Standing au **10ème étage** à **jardin de Carthage** se compose: Un salon Avec Balcon, **Deux Chambres** à coucher, Une Suite Parentale, Une cuisine bien équipée, **Une salle de bain**, Une salle d'eau, **Une place de parking** au sous sol. L'appartement est entièrement Chauffé et climatisé. Référence: Ref202a"

### Données extractibles

| Extraction | Exemple → Résultat |
|------------|-------------------|
| type_appartement | S3 |
| etage | 10 |
| quartier | jardin de Carthage |
| nombre_chambres | 2 (+ suite parentale) |
| nombre_sdb | 1 |
| parking | true |
| standing | Haut standing |
| reference | Ref202a |

### Module `utils/description_extractor.py`

```python
# Depuis la racine du projet (mubaweb) :
from location.utils.description_extractor import extract_from_description, enrich_listing_with_description

# Ou import direct :
from utils.description_extractor import extract_from_description, enrich_listing_with_description

# Extraction directe
result = extract_from_description(description_text, property_category="appartement")
# → {'type_appartement': 'S3', 'etage': '10', 'quartier_extrait': 'jardin de Carthage', ...}

# Enrichissement d'un listing
enriched = enrich_listing_with_description(listing_dict)
# Complète les champs vides avec les données extraites de la description
```

Voir `utils/description_extractor.py` pour les patterns utilisés.

---

## 🗃️ Solution base de données en ligne

### Option recommandée : Supabase (PostgreSQL)

- Gratuit jusqu'à 500 Mo
- API REST + temps réel
- Authentification intégrée
- Chacun peut insérer ses propres données (avec authentification)

### Schéma SQL (Supabase/PostgreSQL)

```sql
-- Table principale unifiée
CREATE TABLE location_listings (
  id TEXT PRIMARY KEY,
  source_site TEXT NOT NULL,
  source_url TEXT UNIQUE,
  property_category TEXT NOT NULL,
  titre TEXT,
  region TEXT,
  ville TEXT,
  quartier TEXT,
  adresse TEXT,
  latitude DECIMAL,
  longitude DECIMAL,
  
  type_bien TEXT,
  loyer DECIMAL,
  loyer_text TEXT,
  loyer_m2 DECIMAL,
  surface DECIMAL,
  surface_terrain DECIMAL,
  
  nombre_pieces INT,
  nombre_chambres INT,
  nombre_sdb INT,
  etage TEXT,
  
  description_courte TEXT,
  description_complete TEXT,
  equipements JSONB,
  images JSONB,
  
  meuble BOOLEAN,
  charges_incluses BOOLEAN,
  caution TEXT,
  conditions_location JSONB,
  contact_info JSONB,
  caracteristiques JSONB,
  
  date_scraping TIMESTAMPTZ,
  scraped_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les recherches
CREATE INDEX idx_location_category ON location_listings(property_category);
CREATE INDEX idx_location_ville ON location_listings(ville);
CREATE INDEX idx_location_region ON location_listings(region);
CREATE INDEX idx_location_loyer ON location_listings(loyer);
CREATE INDEX idx_location_surface ON location_listings(surface);
```

### Insertion depuis Python (Supabase)

```python
from supabase import create_client
import json

SUPABASE_URL = "https://votre-projet.supabase.co"
SUPABASE_KEY = "votre-cle-anon"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Charger les listings
with open("appartement/mubawab_location_appartements_complet_xxx.json") as f:
    data = json.load(f)

for listing in data["listings"]:
    row = {
        "id": f"mubawab_{listing['id']}",
        "source_site": "mubawab.tn",
        "source_url": listing["url"],
        "property_category": "appartement",
        "titre": listing["titre"],
        "ville": listing.get("ville"),
        "region": listing.get("region"),
        "quartier": listing.get("quartier"),
        "loyer": listing.get("loyer") or 0,
        "surface": listing.get("surface") or 0,
        "nombre_chambres": listing.get("nombre_chambres") or 0,
        "description_complete": listing.get("description_complete"),
        # ... autres champs
    }
    supabase.table("location_listings").upsert(row).execute()
```

### Partage avec amis

1. Créer un projet Supabase
2. Activer l'authentification (email ou social)
3. RLS (Row Level Security) : chacun peut insérer uniquement ses lignes (`scraped_by = auth.uid()`)
4. Partager l’URL du projet et les clés API

### Alternatives

| Solution | Avantages |
|----------|-----------|
| **Supabase** | PostgreSQL, temps réel, auth, gratuit |
| **Firebase Firestore** | NoSQL, temps réel, facile à démarrer |
| **Airtable** | Interface simple, API REST |
| **Google Sheets** | Très simple, partage direct |

---

## 📋 Workflow recommandé

1. Lancer les scrapers par type (`appartement.py`, `bureaux.py`, etc.)
2. Enrichir avec `enrich_listing_with_description()`
3. Normaliser vers la structure unifiée
4. Insérer dans Supabase (ou autre DB)
5. Partager le projet pour que d’autres puissent ajouter leurs données

---

## 📚 Documentation par dossier

- [appartement/README.md](appartement/README.md)
- [bureaux/README.md](bureaux/README.md)
- [locaux_com/README.md](locaux_com/README.md)
- [maisons/README.md](maisons/README.md)
- [villas/README.md](villas/README.md)
