# Mubaweb Data Pipeline Documentation

Ce document décrit en détail les étapes réalisées et à venir pour les données extraites du site **mubawab**. Il sert de mémoire pour l'agent et permettra à l'équipe de démarrer, analyser et stocker les informations dans une base de données en ligne.

---

## 1. Contexte général

Le dossier `mubaweb` contient plusieurs sous‑répertoires correspondant à des types d'annonces immobilières :

- `location` (appartements, bureaux, locaux commerciaux, maisons, villas)
- `location_vacance` (locations pour les vacances)
- `locationNeuf` (immeubles neufs)
- `vente_mubaweb` (vente d'appartements, locaux, maisons, terrains, villas)

Chaque sous‑dossier contient un script de scraping (`.py`) et deux dumps (`.csv` et `.json`).

Le but est :
1. Documenter la structure des données et les candidats aux colonnes
2. Détailler les techniques de scraping employées
3. Proposer une structure formelle des données (schéma unifié)
4. Indiquer comment extraire des informations depuis la `description` et enrichir le reste des champs
5. Préparer l'insertion des données consolidées dans une base de données en ligne (SQL/NoSQL)

---

## 2. Analyse & compréhension des données

### 2.1 Colonnes communes
Les fichiers JSON et CSV contiennent typiquement les champs suivants :

- `id` : identifiant unique
- `titre`, `url` : métadonnées de l'annonce
- `loyer`/`prix`, `loyer_text`/`prix_text` : valeurs numériques et formatées
- `surface`, `surface_text`
- `ville`, `region`, `quartier`, `adresse`
- `type_appartement`, `type_location`, `duree_location`
- `charges_incluses`, `caution`
- `nombre_pieces`, `nombre_chambres`, `nombre_sdb`
- `description_courte`, `description_complete` (champ riche)
- `etage`, `etage_immeuble`, `immeuble`, `residence`
- `meuble` (booléen)
- `equipements` (liste), `equipements_detaille` (chaîne)
- `date_scraping`, `page_source`, `is_valid`
- `caracteristiques` (JSON comme chaîne)
- `images` (liste ou chaîne séparée par `;`)
- `localisation` (latitude/longitude in JSON)
- `informations_supplementaires` (JSON string)
- `conditions_location` (JSON string)
- `contact_info` (JSON string)

Les dossiers d`location_vacance`, `locationNeuf` et `vente_mubaweb` contiennent une structure très similaire, avec des champs additionnels spécifiques (ex. `date_disponibilite`, `surface_terrain` pour la vente).

### 2.2 Caractéristiques par sous‑dossier

- **location/appartement, bureaux, etc.** : annonces de location longue durée, focus sur `loyer`. Champs identiques à ceux ci‑dessus.
- **location_vacance** : mêmes champs, éventuellement `periode` ou `date_arrivee` et `date_depart`.
- **locationNeuf** : mise en avant de la livraison et du statut "neuf". Peut ajouter `nombre_etages`, `prix_m2`, etc.
- **vente_mubaweb** : remplace `loyer` par `prix`; ajoute `surface_terrain`, `titre_foncier`, `type_vente`.

> 📌 *Objectif : documenter toutes les colonnes présentes dans chaque dossier, lister celles identifiées dans les JSON/CSV.*

### 2.3 Description détaillée

Le champ `description_complete` est très riche : il contient souvent, sur plusieurs lignes, des données telles que :

- nombre de pièces, chambres (`S3`, `S+2`, `S+3`, etc.)
- équipements (`balcon`, `cuisine équipée`, `chauffage`, `climatisation`)
- caractéristiques (`Haute standing`, `rez-de-chaussée`, `jardin`)
- conditions (`référence du bien : Ref202a`)

**Technique de parsing** :
1. Normaliser le texte (suppression des retours à la ligne, accents, ponctuation superflue).
2. Utiliser des expressions régulières ou spaCy pour détecter les motifs suivants :
   - `S[0-9](\+\d)?` pour `type_appartement` ou `nombre_pieces`.
   - `(chambre(s)?|pièce(s)?)` pour extraire `nombre_chambres`, `nombre_pieces`.
   - mots-clés (`balcon`, `garage`, `ascenseur`, `chauffage`, `climatisation`, `jardin`, etc.) pour remplir `equipements`/`equipements_detaille`.
   - `ref(.*?)\d+` pour numéro de référence.
3. Ajouter les résultats aux champs existants en priorité s'ils sont manquants ou incohérents.

Le README doit servir de guide pour écrire un script de transformation.

---

## 3. Technique de scraping

Chaque script Python de chaque sous‑dossier contient :

1. **Requête HTTP** : utilisation de `requests` ou `selenium` (selon besoin) pour charger les pages de recherche.
2. **Parsing** : `BeautifulSoup` ou `lxml` pour extraire les éléments DOM des annonces.
3. **Normalisation** : transformation du texte brut en données structurées (conversion des montants, suppression de caractères non numériques).
4. **Pagination** : boucle sur les pages jusqu'à épuisement des résultats.
5. **Gestion des erreurs** : reprises sur timeouts, vérification de `is_valid`.
6. **Export** : écriture simultanée en JSON et CSV (`pandas` peut être utilisé pour CSV). Les champs de `contact_info` sont généralement laissés sous forme JSON string.

> 🛠️ *À améliorer* : isoler la logique commune dans un module réutilisable pour tous les types d'annonces. 

---

## 4. Schéma formel proposé

Nous définissons un schéma unifié (`mubaweb_schema.json` ou `.sql`) contenant la plupart des colonnes rencontrées partout : 

| Nom du champ | Type | Description | Remarque |
|--------------|------|-------------|----------|
| id | string | Identifiant unique | clé primaire |
| titre | string | Titre de l'annonce | |
| url | string | URL de l'annonce | |
| loyer/prix | float | Montant (loyer ou prix) | dépend du type d'opération |
| surface | float | Surface en m² | |
| surface_terrain | float | (vente) surface du terrain | nullable |
| ville | string | |
| region | string | |
| quartier | string | |
| adresse | string | |
| type_appartement | string | S1, S2, S+3... | |
| type_location | string | Location / Vente / Vacance | |
| duree_location | string | courte/long terme | |
| charges_incluses | bool | |
| caution | string | |
| nombre_pieces | int | |
| nombre_chambres | int | |
| nombre_sdb | int | |
| etage | string | |
| immeuble | string | |
| residence | string | |
| meuble | bool | |
| equipements | array[string] | Liste normalisée | |
| equipements_detaille | string | Texte complet | |
| caracteristiques | json | Champs supplémentaires | |
| images | array[string] | URL des images | |
| latitude | float | géolocalisation | |
| longitude | float | |
| description_courte | string | |
| description_complete | string | |
| date_scraping | datetime | ISO 8601 |
| page_source | string | search / detail / ... |
| is_valid | bool | |
| informations_supplementaires | json | |
| conditions_location | json | |
| contact_info | json | |

> ⚠️ Pour le stockage en SQL, certains champs JSON peuvent être convertis en colonnes relationnelles complémentaires ou maintenus en JSON selon le moteur (PostgreSQL `jsonb`, MongoDB, etc.).

---

## 5. Insertion dans une base de données en ligne

Objectif : déployer une base accessible par le réseau pour l'équipe (MySQL, PostgreSQL, MongoDB Atlas, etc.).

Étapes :
1. Créer un schéma distant (preview du schéma ci-dessus).
2. Écrire un script `load_to_db.py` qui lit les fichiers JSON/CSV, transforme (normalisation, parsing de description) et insère/ met à jour.
3. Gérer les duplicates par clé `id`.
4. Fournir des exemples de requêtes (SQL ou requêtes Mongo) pour extraire des rapports.

---

## 6. Plan détaillé des étapes (proposition)

1. **Documentation initiale** (ce README)
2. **Audit des colonnes** : parcourir chaque dump pour lister toutes les colonnes disponibles et créer un tableau de correspondance.
3. **Écriture d'un module commun de scraping/normalisation**
4. **Analyse exploratoire** : `dataUnderstanding.ipynb` ou script pour décrire chaque colonne (type, pourcentage manquant, valeurs uniques).
5. **Parsing de `description_complete`** : prototype de fonctions d'extraction.
6. **Construction du schéma final** (incl. conversions JSON)
7. **Mise en place de la base de données en ligne** (choix du service, création, sécurité).
8. **Script d'ingestion** et tests.
9. **Validation et documentation** pour les utilisateurs (instructions pour ajouter de nouvelles sources comme tayara).

---

## 7. Notes et bonnes pratiques

- Conserver les fichiers CSV/JSON bruts en lecture seule comme archive.
- Versionner les scripts dans Git (branch `scraping`, `etl`).
- Les transformations sur la `description` doivent être réentrantes et paramétrables.
- Étendre le schéma lorsque de nouveaux attributs sont détectés.

---

## 8. À confirmer

Avant de commencer le travail, merci de relire ce README et de valider que :

- les étapes proposées correspondent à vos besoins
- le schéma couvre les colonnes essentielles
- la base de données cible est acceptable (indiquer la solution préférée)

Une fois confirmé, on pourra démarrer la mise en oeuvre et générer les scripts requis.


---

*Date de génération : 16 février 2026*  
*Auteur : Agent Copilot*