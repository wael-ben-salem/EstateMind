# Location - Appartements

## Documentation du Scraper

### Fichiers
- **appartement.py** : Scraper pour appartements à louer sur Mubawab
- **mubawab_location_appartements_complet_*.json** : Données scrapées

### Techniques de Scraping Utilisées

#### 1. **Infrastructure HTTP**
- Session `requests`, rotation User-Agent, cookies TN/fr
- Retry 3x, gestion 403/429, délai 0.8s, timeout 30s

#### 2. **Parsing HTML**
- Structure principale : `div.listingBox`
- Fallback : `search-listing`, `property-item`, `col-6`

#### 3. **Extraction par Regex**
| Donnée | Patterns |
|--------|----------|
| Prix | `([\d\s\.]+)\s*(?:tnd|dt)`, filtre 100-10,000 DT |
| Surface | `(\d+)\s*m[²2]` |
| Pièces | `(\d+)\s*pi[èe]ce`, `S(\d+)` |
| Chambres | `(\d+)\s*chambre` |
| SDB | `(\d+)\s*salle?\s*de?\s*bain` |
| Type appart | S1, S2, S3, S4, S+, Studio, Duplex, Meublé |

#### 4. **Fonctions Spécifiques**
- `extract_apartment_type()` : S1→Studio, S2→S2, S3→S3...
- `extract_duration()` : Court terme, Long terme, À la journée
- `extract_charges_incluses()` : charges comprises / hors charges

#### 5. **Structure des cartes**
- Prix : `span.priceTag`, `div.priceBar`
- Localisation : `span.listingH3`, `i.icon-location`
- Features : `div.adDetails` > `adDetailFeature` (icon-triangle=surface, icon-bed=chambres, icon-bath=SDB)
- Équipements : `div.adFeatures` > `adFeature` + mapping icônes

---

## Structure des Données JSON

### Metadata
- **property_type** : `location_appartements`
- **regions** : La Marsa, Le Kram, La Soukra, Hammamet, Ariana Ville, Hammam Sousse, Nabeul, Carthage

### Attributs par Listing

| Attribut | Type | Description |
|----------|------|-------------|
| id, titre, url | string | Identifiants |
| loyer, loyer_text, loyer_m2 | float/string | Prix |
| surface, surface_text | float/string | Surface |
| ville, region, quartier, adresse | string | Localisation |
| type_appartement | string | S2, S3, Studio, Duplex... |
| type_location | string | "Location" |
| duree_location | string | Long terme, Court terme |
| charges_incluses | bool | Charges comprises |
| caution | string | Montant caution |
| nombre_pieces | int | Pièces |
| nombre_chambres | int | Chambres |
| nombre_sdb | int | Salles de bain |
| description_courte | string | Extrait liste |
| etage, etage_immeuble | string | Étage |
| immeuble, residence | string | Bâtiment |
| meuble | bool | Meublé ou vide |
| equipements | array | Ascenseur, Garage, Terrasse... |
| description_complete | string | Détail page |
| caracteristiques, localisation | JSON string | Détails structurés |
| conditions_location, contact_info | JSON string | Conditions, contact |

### Format URL
- `{base}/fr/st/{region}/appartements-a-louer`
- `{base}/fr/st/{region}/appartements-a-louer:p:{page}`
