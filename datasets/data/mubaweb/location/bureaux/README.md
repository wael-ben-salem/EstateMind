# Location - Bureaux

## Documentation du Scraper

### Fichiers
- **bureaux.py** : Scraper pour bureaux à louer sur Mubawab
- **mubawab_location_bureaux_complet_*.json** : Données scrapées

### Techniques de Scraping Utilisées

#### 1. **Infrastructure**
- Session requests, User-Agent rotation, cookies TN/fr
- Retry 3x, gestion 403/429, délai 0.8s

#### 2. **Extraction Spécifique Bureaux**
| Donnée | Patterns / Logique |
|--------|-------------------|
| Prix | Filtre 100-50,000 DT |
| Type bureau | Open Space, A1, A2, A3, Siège, Cabinet, Boutique... |
| Type contrat | Bail commercial, Bail professionnel, Co-working |

#### 3. **Features Bureaux**
- `extract_office_type()` : Open Space, A1-A4, Siège, Cabinet
- `extract_contract_type()` : Bail commercial/professionnel
- `extract_office_features()` : Salle réunion, Kitchenette, Vidéo surveillance

---

## Structure des Données JSON

### Metadata
- **property_type** : `location_bureaux`
- **regions** : La Marsa, Tunis, Cité El Khadra, La Soukra, Ariana Ville, El Menzah

### Attributs par Listing

| Attribut | Type | Description |
|----------|------|-------------|
| id, titre, url | string | Identifiants |
| loyer, loyer_text, loyer_m2 | float/string | Loyer |
| surface, surface_text | float/string | Surface |
| ville, region, quartier, adresse | string | Localisation |
| type_bureau | string | Bureau, Open Space, A2... |
| type_contrat | string | Bail commercial, Standard |
| type_location | string | "Location" |
| nombre_pieces, nombre_bureaux | int | Pièces/bureaux |
| nombre_sdb | int | Salles de bain |
| etage, batiment, residence | string | Infos bâtiment |
| equipements | array | Ascenseur, Garage, Terrasse... |
| amenities_bureaux | array | Features spécifiques |
| description_courte, description_complete | string | Descriptions |

### Format URL
- `{base}/fr/st/{region}/bureaux-et-commerces-a-louer`
- `{base}/fr/st/{region}/bureaux-et-commerces-a-louer:p:{page}`
