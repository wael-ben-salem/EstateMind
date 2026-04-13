# Location - Locaux Commerciaux

## Documentation du Scraper

### Fichiers
- **locaux.py** : Scraper principal pour les locaux commerciaux à louer sur Mubawab
- **mubawab_location_locaux_commerciaux_la_marsa_*.json** : Données scrapées

### Techniques de Scraping Utilisées

#### 1. **Infrastructure HTTP**
- `requests.Session()` : Session persistante pour optimiser les requêtes
- Rotation des User-Agent pour éviter le blocage
- Gestion des cookies (country: TN, language: fr)
- Retry automatique (3 tentatives) avec gestion 403/429
- Délai configurable entre requêtes (default: 0.8-1s)
- Timeout de 30 secondes

#### 2. **Parsing HTML**
- **BeautifulSoup** avec parser HTML
- Sélecteurs : `div.listingBox` (structure principale Mubawab)
- Fallback : `search-listing`, `property-item`, `col-6` avec validation du contenu

#### 3. **Détection & Pagination**
- `numResults` / `resultNum` pour le nombre total d'annonces
- `count_real_listings_on_page()` : comptage des cartes valides
- Patterns URL pagination : `:p:(\d+)`, `page=`, `/p/`
- Détection du lien "suivant" : `a.next` ou texte "suivant"

#### 4. **Extraction par Regex**
| Donnée | Patterns |
|--------|----------|
| Prix | `([\d\s\.]+)\s*(?:tnd|dt|dinars?)`, filtres 100-100,000 DT |
| Surface | `(\d+)\s*m[²2]`, `superficie\s*[:\-]?\s*(\d+)` |
| Loyer/m² | `([\d\s\.]+)\s*(?:dt|tnd)\s*[\/\s]\s*m[²2]` |
| ID URL | `/a/(\d+)/`, `/pa/(\d+)/` |
| Type local | Mapping par mots-clés (open space, bureau, boutique, magasin...) |
| Activités | Mapping coiffure, restaurant, pharmacie, etc. |

#### 5. **Validation des Cartes**
- Score de validation (≥4/6) : surface, prix, titre, lien, localisation
- Détection doublons via `scraped_urls` et `scraped_ids`
- Vérification structure : h2.listingTit, span.priceTag, span.listingH3

#### 6. **Scraping Détails**
- Visite de chaque page annonce pour description complète
- Extraction : blockProp, caractBlockProp, adMainFeature, adFeature
- Images : img src mubawab-media.com
- Coordonnées : latField, lngField
- JSON-LD pour datePublished

---

## Structure des Données JSON

### Metadata
```json
{
  "metadata": {
    "date_export": "ISO8601",
    "total_listings": 159,
    "regions": ["La Marsa"],
    "property_type": "location_locaux_commerciaux",
    "scraping_stats": {...},
    "fields_count": 34
  }
}
```

### Attributs par Listing (34 champs)

| Attribut | Type | Description |
|----------|------|-------------|
| id | string | ID extrait de l'URL |
| titre | string | Titre de l'annonce |
| url | string | URL complète |
| loyer | float | Loyer en DT (0 si "à consulter") |
| loyer_text | string | Texte brut du loyer |
| loyer_m2 | float | Loyer par m² |
| surface | float | Surface en m² |
| surface_text | string | Surface brute |
| ville | string | Ville |
| region | string | Région |
| quartier | string | Quartier |
| adresse | string | Adresse complète |
| type_local | string | Local commercial, Open Space, Bureau, etc. |
| type_location | string | "Location" |
| activites_possibles | array | Coiffure, Esthétique, etc. |
| nombre_sdb | int | Salles de bain |
| etage | string | RDC, 1, 2... |
| batiment, residence, complexe | string | Infos bâtiment |
| description_courte | string | Extrait liste |
| equipements | array | Ascenseur, Climatisation... |
| amenities_commercial | array | Features commerciales |
| description_complete | string | Page détail |
| caracteristiques | JSON string | type, état, standing... |
| equipements_detaille | string | Liste séparée ; |
| images | string | URLs séparées ; |
| localisation | JSON string | latitude, longitude |
| informations_supplementaires | JSON string | terrasse, ascenseur... |
| conditions_location | JSON string | charges, caution, bail |
| contact_info | JSON string | agence, formulaire |
| date_scraping | string | ISO8601 |
| page_source | string | "search" |
| is_valid | bool | Validation |

### Régions
- **La Marsa** : `/fr/st/la-marsa/locaux-a-louer`

### Format URL
- Page 1 : `{base}/fr/st/{region}/locaux-a-louer`
- Page N : `{base}/fr/st/{region}/locaux-a-louer:p:{page}`
