# Data Understanding Mubaweb — Documentation complète

Ce document décrit la structure des données et les attributs de chaque catégorie du projet mubaweb (scraping immobilier Mubawab.tn).

---

## 1. Vue d'ensemble

| Catégorie | Type transaction | Fichier principal | Nb listings (approx.) |
|-----------|------------------|-------------------|------------------------|
| **Location appartements** | Location | `location/appartement/mubawab_location_appartements_complet_*.json` | ~3 900 |
| **Location bureaux** | Location | `location/bureaux/mubawab_location_bureaux_complet_*.json` | ~1 180 |
| **Location locaux commerciaux** | Location | `location/locaux_com/mubawab_location_locaux_commerciaux_*.json` | variable |
| **Location maisons** | Location | `location/maisons/mubawab_location_maisons_*.json` | variable |
| **Location villas** | Location | `location/villas/mubawab_location_villas_complet_*.json` | variable |
| **Location vacances** | Location vacances | `location_vacance/listings_propres.json` | ~137 |
| **Immobilier neuf** | Location/Vente promotions | `locationNeuf/promotions_final.json` | ~75 |
| **Vente appartements** | Vente | `vente_mubaweb/vente_apparrtements/appartements_final.json` | ~8 000+ |
| **Vente locaux commerciaux** | Vente | `vente_mubaweb/vente_locaux_commerciaux/locaux_final.json` | ~121 |
| **Vente maisons** | Vente | `vente_mubaweb/vente_maisons/maisons_final.json` | ~950 |
| **Vente villas** | Vente | `vente_mubaweb/vente_villas/villas_clean.json` | ~1 367 |
| **Vente terrains** | Vente | `vente_mubaweb/Terrain/terrain_clean.json` | ~1 141 |

---

## 2. Structure globale des fichiers JSON

Tous les fichiers ont une structure commune :

```json
{
  "metadata": { ... },
  "listings": [ { ... }, { ... } ]
}
```

### 2.1 Objet `metadata`

| Champ | Type | Description |
|-------|------|-------------|
| `date_export` | string (ISO) | Date d’export du scraping |
| `total_listings` | int | Nombre total de listings |
| `property_type` | string | Type de bien (ex. `location_appartements`, `villas-de-luxe`) |
| `regions` | array[string] | Régions/ville scrapées |
| `scraping_stats` | object | Pages scrapées, annonces trouvées, erreurs, etc. |
| `validation_warnings` | object | Warnings de cohérence (ex. prix texte vs numérique) |
| `extraction_date` / `cleaning_date` | string | Dates d’extraction et de nettoyage |
| `listings_traites` | int | Nombre de listings traités |
| `statistiques_extraction` / `statistiques_nettoyage` | object | Statistiques post-traitement |
| `fields_count` | int | Nombre de champs par listing |

---

## 3. Attributs communs à tous les listings

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Identifiant Mubawab |
| `titre` | string | Titre de l’annonce |
| `url` | string | URL de la page Mubawab |
| `description_courte` | string | Résumé court |
| `description_complete` | string | Description complète |
| `ville` | string | Ville |
| `quartier` | string | Quartier |
| `adresse` | string | Adresse complète |
| `region` | string | Région (Tunis, Nabeul, etc.) |
| `surface` | float | Surface en m² |
| `surface_text` | string | Surface formatée (ex. "140 m²") |
| `images` | array[string] | URLs des images |
| `localisation` | object | `{ latitude, longitude, coordinates }` |
| `page_source` | string | Source de la page (ex. "search") |
| `is_valid` | bool/string | Indique si le listing est valide |
| `date_scraping` | string | Date du scraping |
| `date_publication` | string \| null | Date de publication si disponible |

---

## 4. Structures par catégorie

### 4.1 Location (appartements, bureaux, locaux_com, maisons, villas)

Les fichiers de **location** bruts (non nettoyés) utilisent `loyer` au lieu de `prix`.

#### Champs spécifiques Location

| Champ | Type | Description |
|-------|------|-------------|
| `loyer` | float | Loyer mensuel (TND) |
| `loyer_text` | string | Loyer formaté (ex. "2 500 TND") |
| `loyer_m2` | float | Loyer au m² |
| `type_location` | string | "Location", "Location vacances" |
| `duree_location` | string | "Long terme", "Court terme" |
| `charges_incluses` | bool | Charges comprises dans le loyer |
| `caution` | string | Montant ou conditions de caution |
| `type_appartement` | string | S1, S2, S3, etc. |
| `nombre_pieces` | int | Nombre de pièces |
| `nombre_chambres` | int | Nombre de chambres |
| `nombre_sdb` | int | Nombre de salles de bain |
| `etage` | string \| null | Étage |
| `meuble` | bool | Meublé ou non |
| `equipements` | array[string] | Liste d’équipements |
| `equipements_detaille` | string \| array | Détails équipements (raw: chaîne séparée par ";") |
| `caracteristiques` | string \| object | Type de bien, état, type de sol (raw: chaîne JSON) |
| `informations_supplementaires` | string \| object | parking, cuisine, chauffage (raw: chaîne JSON) |
| `conditions_location` | object | Conditions de location |
| `contact_info` | string \| object | Formulaire contact, téléphone (raw: chaîne JSON) |
| `residence` | string | Nom de résidence |
| `immeuble` | string | Nom immeuble |

**Note :** Dans les fichiers bruts, `caracteristiques`, `localisation`, `informations_supplementaires`, `contact_info` et parfois `images` peuvent être des **chaînes JSON** et non des objets.

---

### 4.2 Location vacances

| Champ | Type | Description |
|-------|------|-------------|
| `prix` | float | Prix (TND ou autre) |
| `prix_text` | string | Prix formaté |
| `prix_par_jour` | float \| null | Prix journalier |
| `capacite` | int | Capacité d’accueil (personnes) |
| `nuits_minimum` | int | Durée minimale de séjour (nuits) |
| `type_bien` | string | Appartement, Villa, etc. |
| `type_location` | string | "Location vacances" |
| `equipements` | array[string] | Liste d’équipements |
| `amenities_vacances` | array[string] | Équipements typiques vacances |
| `equipements_detaille` | array[string] | Liste détaillée |
| `conditions_location` | object | Conditions particulières |
| `informations_supplementaires` | object | meuble, ascenseur, parking, climatisation |

---

### 4.3 Immobilier neuf (promotions)

| Champ | Type | Description |
|-------|------|-------------|
| `promotion_id` | string | ID promotion |
| `prix` | float | Prix de départ |
| `prix_type` | object | `{ code: "starting_from", label: "À partir de" }` |
| `prix_text` | string | Ex. "À partir de 510 000 TND" |
| `prix_m2` | float \| null | Prix au m² |
| `type_bien` | string | Résidence, Bureau, Terrain, Appartement, Villa, Local commercial |
| `standing` | object | `{ code, label }` — Ex. "Haut standing" |
| `statut_construction` | object | `{ code, label }` — Ex. "Finalisé", "En cours" |
| `date_livraison` | string \| null | Date de livraison prévue |
| `nombre_appartements` | int \| null | Nombre de lots dans la promotion |
| `has_video` | bool | Présence de vidéo |
| `logo_agence` | string | URL logo promoteur |
| `nom_agence` | string | Nom promoteur/agence |
| `videos` | array | URLs vidéos |
| `plans` | array | URLs plans |
| `equipements_complets` | array[string] | Spa, etc. |
| `caracteristiques_detaillees` | object | Caractéristiques détaillées |

---

### 4.4 Vente appartements

| Champ | Type | Description |
|-------|------|-------------|
| `prix` | float | Prix (TND), 0 si "Prix à consulter" |
| `prix_text` | string | Ex. "850 000 TND", "Prix à consulter" |
| `prix_m2` | float \| null | Prix au m² |
| `type_appartement` | string | S1, S2, S3, etc. |
| `nombre_pieces` | int | Nombre de pièces |
| `nombre_chambres` | int | Nombre de chambres |
| `nombre_sdb` | int | Nombre de salles de bain |
| `etage` | int \| null | Étage |
| `meuble` | bool | Meublé |
| `reference` | string | Référence agence |
| `nom_agence` | string | Nom de l’agence |
| `residence` | string | Nom résidence |
| `equipements` | array[string] | Liste équipements |
| `caracteristiques` | object | `type_de_bien`, `etat`, `type_sol` |
| `informations_supplementaires` | object | ascenseur, parking, meuble, cuisine, chauffage, climatisation |
| `contact_info` | object | formulaire_contact, etc. |

---

### 4.5 Vente locaux commerciaux

| Champ | Type | Description |
|-------|------|-------------|
| `type_transaction` | string | "Vente" |
| `prix` | float | Prix (TND) |
| `prix_text` | string | Prix formaté |
| `prix_m2` | float | Prix au m² |
| `surface_mezzanine` | float \| null | Surface mezzanine (m²) |
| `surface_terrasse` | float \| null | Surface terrasse (m²) |
| `type_local` | string | Local commercial, Bureau, etc. |
| `nombre_sdb` | int | Nombre de salles de bain |
| `etage` | int \| null | Étage |
| `nombre_vitrines` | int \| null | Nombre de vitrines |
| `parking_nombre` | int \| null | Nombre de places de parking |
| `a_mezzanine` | bool | Présence mezzanine |
| `double_hauteur` | bool | Local en double hauteur |
| `a_terrasse` | bool | Terrasse |
| `acces_livraison` | bool | Accès livraison |
| `possibilite_enseigne` | bool | Possibilité d’enseigne |
| `a_alarme` | bool | Alarme |
| `a_monte_charge` | bool | Monte-charge |
| `accessibilite_pmr` | bool | Accessibilité PMR |
| `zone_activite` | string \| null | Zone d’activité |
| `largeur_facade` | float \| null | Largeur façade (m) |
| `equipements` | array[string] | Équipements |
| `amenities_commercial` | array[string] | Équipements commerciaux |
| `caracteristiques` | object | type_de_bien, etat, annees, type_sol |
| `conditions_vente` | object \| null | Conditions de vente |

---

### 4.6 Vente maisons

| Champ | Type | Description |
|-------|------|-------------|
| `type_transaction` | string | "Vente" |
| `type_maison` | string | Duplex, Maison, etc. |
| `surface_terrain` | float \| null | Surface terrain (m²) |
| `surface_jardin` | float \| null | Surface jardin (m²) |
| `surface_terrasse` | float \| null | Surface terrasse (m²) |
| `surface_piscine` | float \| null | Surface piscine (m²) |
| `nombre_pieces` | int | Nombre de pièces |
| `nombre_chambres` | int | Nombre de chambres |
| `nombre_sdb` | int | Nombre de salles de bain |
| `nombre_niveaux` | int \| null | Nombre d’étages |
| `garage_nombre` | int \| null | Nombre de places garage |
| `annee_construction` | int \| null | Année de construction |
| `etat_maison` | string \| null | État du bien |
| `a_jardin` | bool | Jardin |
| `a_piscine` | bool | Piscine |
| `a_terrasse` | bool | Terrasse |
| `a_garage` | bool | Garage |
| `a_cave` | bool | Cave |
| `a_cheminee` | bool | Cheminée |
| `a_alarme` | bool | Alarme |
| `a_buanderie` | bool | Buanderie |
| `a_dressing` | bool | Dressing |
| `a_placards` | bool | Placards |
| `potentiel_extension` | bool | Extension possible |
| `orientation` | string | Nord, Sud, Est, Ouest |
| `vue_type` | string \| null | Type de vue |
| `chauffage_type` | string \| null | Type chauffage |
| `climatisation_type` | string \| null | Type climatisation |
| `proximites` | array | Proximités |
| `equipements` | array[string] | Équipements |
| `amenities_maison` | array[string] | Commodités maison |

---

### 4.7 Vente villas

| Champ | Type | Description |
|-------|------|-------------|
| `type_villa` | string | Villa |
| `style_architectural` | string | Classique, Moderne, etc. |
| `niveau_standing` | string | Standard, Haut standing, etc. |
| `surface_terrain` | float | Surface terrain (m²) |
| `surface_jardin` | float \| null | Surface jardin |
| `surface_terrasse` | float \| null | Surface terrasse |
| `surface_piscine` | float \| null | Surface piscine |
| `nombre_pieces` | int | Nombre de pièces |
| `nombre_chambres` | int | Nombre de chambres |
| `nombre_sdb` | int | Nombre de salles de bain |
| `nombre_etages` | int \| null | Nombre d’étages |
| `nombre_suites` | int \| null | Nombre de suites |
| `garage_nombre` | int \| null | Places garage |
| `annee_construction` | int \| null | Année construction |
| `etat_bien` | string | État du bien |
| `a_piscine` | bool | Piscine |
| `a_spa` | bool | Spa |
| `a_hammam` | bool | Hammam |
| `a_jardin` | bool | Jardin |
| `a_terrasse` | bool | Terrasse |
| `a_garage` | bool | Garage |
| `a_cheminee` | bool | Cheminée |
| `a_home_cinema` | bool | Home cinéma |
| `a_cave_vin` | bool | Cave à vin |
| `a_bureau` | bool | Bureau |
| `a_dressing` | bool | Dressing |
| `a_buanderie` | bool | Buanderie |
| `a_cellier` | bool | Cellier |
| `a_alarme` | bool | Alarme |
| `a_panneaux_solaires` | bool | Panneaux solaires |
| `type_piscine` | string | Standard, etc. |
| `equipements` | array[string] | Équipements |

---

### 4.8 Vente terrains

| Champ | Type | Description |
|-------|------|-------------|
| `type_terrain` | string | "Terrain" |
| `vocation` | string | Vocation principale (texte brut) |
| `situation_juridique` | string | Situation juridique (texte brut) |
| `types_terrain` | array[string] | Terrain constructible, Agricole, Lots de villa, Terrain de promotion |
| `vocations` | array[string] | Résidentiel, Commercial, etc. |
| `situations_juridiques` | array[string] | Claire, etc. |
| `viabilisation` | array[string] | Électricité, Eau, Assainissement, etc. |
| `constructibilite` | array[string] | Constructible, etc. |
| `topographie` | string | Déscription topographique |
| `orientation` | string | Nord, Sud, Est, Ouest |
| `vue` | string | Type de vue |
| `zone` | string | Zone (activité, etc.) |
| `acces` | array | Conditions d’accès |
| `proximites` | array[string] | Mer, plage, etc. |
| `cloture` | bool | Terrain clôturé |
| `front_mer` | bool | En bord de mer |
| `caracteristiques` | object | type_de_bien, type_terrain |
| `informations_supplementaires` | object | type_precis (Constructible, etc.) |

---

## 5. Normalisations et valeurs typiques

### 5.1 Prix

- Unité : **TND** (Dinars tunisiens).
- `prix = 0` ou `null` signifie souvent "Prix à consulter" (vérifier `prix_text`).
- `validation_warnings` signale les incohérences entre `prix` (numérique) et `prix_text`.

### 5.2 Localisation

```json
{
  "latitude": 36.876389,
  "longitude": 10.325278,
  "coordinates": [10.325278, 36.876389]
}
```

- `coordinates` : format [longitude, latitude] (GeoJSON).

### 5.3 Équipements

Noms standardisés en PascalCase, exemples :  
Antenne Parabolique, Ascenseur, Chauffage Central, Climatisation, Concierge, Cuisine Équipée, Double Vitrage, Garage, Jardin, Meublé, Parking, Porte Blindée, Piscine, Sécurité, Terrasse, Tv, Vue sur mer.

### 5.4 Régions

Régions principales : Tunis, Nabeul, Sousse, Sfax.  
Villes fréquentes : La Marsa, Hammamet, La Soukra, Ariana Ville, Djerba, El Menzah, Carthage, Le Kram.

---

## 6. Base de données Supabase

Schéma utilisé :

```sql
CREATE TABLE mubawab_listings (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  source_id TEXT NOT NULL,
  data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(category, source_id)
);
```

### Mapping catégorie → fichier

| category | Fichier source |
|----------|----------------|
| `location_vacance` | `location_vacance/listings_propres.json` |
| `locationNeuf` | `locationNeuf/promotions_final.json` |
| `vente_appartements` | `vente_mubaweb/vente_apparrtements/appartements_final.json` |
| `vente_locaux_commerciaux` | `vente_mubaweb/vente_locaux_commerciaux/locaux_final.json` |
| `vente_maisons` | `vente_mubaweb/vente_maisons/maisons_final.json` |
| `vente_villas` | `vente_mubaweb/vente_villas/villas_clean.json` |

Chaque listing est inséré dans `data` en conservant sa structure JSON d’origine.

---

## 7. Fichiers intermédiaires

| Suffixe | Description |
|---------|-------------|
| `*_complet_*.json` | Export brut du scraper |
| `*_extrait.json` | Après extraction enrichie (descriptions, prix, etc.) |
| `*_final.json` / `*_clean.json` | Version nettoyée et normalisée |

Les versions `_final` et `_clean` sont à privilégier pour les analyses.

---

## 8. Points d’attention pour l’analyse

1. **Données manquantes** : Beaucoup de champs optionnels peuvent être `null`, `""` ou absents.
2. **Incohérences** : Consulter `metadata.validation_warnings` pour les incohérences de prix.
3. **Champs brut vs nettoyé** : Les fichiers bruts peuvent contenir des chaînes JSON dans des champs qui sont des objets après nettoyage.
4. **Types** : Certains champs booléens sont stockés en string ("True"/"False") dans les anciens exports.
