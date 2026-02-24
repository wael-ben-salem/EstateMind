# Location - Maisons

## Documentation du Scraper

### Fichiers
- **maison.py** : Scraper pour maisons à louer sur Mubawab
- **mubawab_location_maisons_la_marsa_*.json** : Données scrapées

### Techniques de Scraping Utilisées

#### 1. **Infrastructure**
- Même base que les autres scrapers (Session, User-Agent, retry)

#### 2. **Extraction Spécifique Maisons**
| Donnée | Patterns / Logique |
|--------|-------------------|
| Prix | Filtre 200-50,000 DT |
| Type maison | Villa, Duplex, Triplex, Pavillon, Fermette, Riad, Chalet |

#### 3. **Features Maisons**
- `extract_house_type()` : Villa, Duplex, Chalet, Riad...
- `extract_house_features()` : Jardin, Piscine, Vue sur mer, Cheminée...

---

## Structure des Données JSON

### Metadata
- **property_type** : `location_maisons`
- **regions** : La Marsa

### Attributs par Listing

| Attribut | Type | Description |
|----------|------|-------------|
| id, titre, url | string | Identifiants |
| loyer, loyer_text, loyer_m2 | float/string | Loyer |
| surface, surface_text | float/string | Surface |
| ville, region, quartier, adresse | string | Localisation |
| type_maison | string | Maison, Villa, Duplex... |
| nombre_pieces, nombre_chambres, nombre_sdb | int | Pièces |
| etage, batiment, residence | string | Infos bâtiment |
| equipements | array | Jardin, Terrasse, Piscine... |
| amenities_maison | array | Features spécifiques |

### Format URL
- `{base}/fr/st/la-marsa/maisons-a-louer`
- `{base}/fr/st/la-marsa/maisons-a-louer:p:{page}`
