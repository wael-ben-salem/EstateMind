# Location - Villas

## Documentation du Scraper

### Fichiers
- **villas.py** : Scraper pour villas et maisons de luxe à louer
- **mubawab_location_villas_complet_*.json** : Données scrapées

### Techniques de Scraping Utilisées

#### 1. **Extraction Spécifique Villas**
| Donnée | Patterns / Logique |
|--------|-------------------|
| Prix | Filtre 1,000-100,000 DT |
| Surface terrain | `terrain\s*[:\-]?\s*(\d+)\s*m[²2]` |
| Type villa | Villa S3-S6, Duplex, Plain-pied, Luxe, Moderne |

#### 2. **Features Villas**
- `extract_villa_type()` : Villa S3-S6, Duplex, Chalet, Riad
- `extract_villa_features()` : Piscine, Jardin, Spa, Jacuzzi, Court tennis...
- Champs booléens : jardin, piscine, garage, parking, meuble

#### 3. **Données Spécifiques**
- surface_terrain, niveaux, annee_construction

---

## Structure des Données JSON

### Metadata
- **property_type** : `location_villas`
- **regions** : La Marsa, Carthage, Hammamet, La Soukra

### Attributs par Listing (40 champs)

| Attribut | Type | Description |
|----------|------|-------------|
| surface_terrain | float | Surface terrain en m² |
| niveaux | int | Nombre d'étages |
| annee_construction | string | Année |
| jardin, piscine, garage, parking, meuble | bool | Caractéristiques |
| type_villa | string | Villa S3, Villa S4, Duplex... |
| duree_location | string | Long/Court terme |

### Format URL
- `{base}/fr/st/{region}/villas-et-maisons-de-luxe-a-louer`
- `{base}/fr/st/{region}/villas-et-maisons-de-luxe-a-louer:p:{page}`
