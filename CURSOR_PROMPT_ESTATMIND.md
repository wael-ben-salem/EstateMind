# 🏠 EstateMind — Cursor AI Master Prompt
## Full Stack Rebuild · From Scratch · Production Grade

---

> **COPY THIS ENTIRE PROMPT INTO CURSOR AI COMPOSER (CTRL+I)**

---

## 🎯 CONTEXTE DU PROJET

Tu travailles sur **EstateMind**, une plateforme d'intelligence immobilière pour la Tunisie.
Le projet existe déjà partiellement. Tu dois **reconstruire entièrement le frontend et le backend from scratch** en gardant l'infrastructure existante (Airflow, PostgreSQL, MinIO, Spark).

### Stack existante (NE PAS TOUCHER)
```
EstateMind/
├── airflow/               ← DAGs Airflow orchestrant le pipeline ETL
│   └── dags/
│       └── tayara_ai_agent_pipeline.py   ← DAG principal (scraping Tayara.tn)
├── scraper/               ← Agent de scraping web (Tayara.tn)
├── agent/                 ← Agent ETL basé sur l'IA
├── agent_price/           ← Agent d'estimation de prix
├── spark/                 ← Jobs Spark pour le traitement des données
├── minio_data/            ← Stockage objet (archives raw)
├── output/                ← Données de sortie
└── docker-compose.yaml    ← Orchestration multi-conteneurs
```

### Pipeline ETL Airflow (déjà opérationnel)
Le DAG `tayara_ai_agent_pipeline` fait exactement ceci dans l'ordre :
1. **Fetch URLs** — Crawl de Tayara.tn par catégorie et gouvernerat
2. **Parse HTML** — Agent IA extrait les données structurées de chaque annonce
3. **Validate Data** — Vérification schema, prix, coordonnées géographiques
4. **Deduplicate** — Déduplication par hash URL + contenu sur l'historique
5. **Enrich** — Calcul des distances géo, score bon-entourage, standing
6. **Load to DB** — Upsert PostgreSQL + archivage MinIO
7. **Notify** — Alerte Slack avec résumé du run et rapport d'anomalies

### Base de données PostgreSQL
- **Image Docker** : `azizmaas1999/my-postgres:15`
- **Credentials** : user=`airflow`, password=`airflow`, db=`airflow`, port=`5432`
- **Table principale** : `scraped_properties` avec **204,745 enregistrements réels**
- **Colonnes complètes** :
```sql
id, adresse, annee_constr, bus, caracteristiques, contrat, date_publication,
description, ecole, etage, gouvernerat, has_ascenseur, has_balcon, has_chaffage,
has_climatisation, has_garage, has_gardien, has_jardin, has_parking, has_piscine,
has_terrasse, hopital, images, latitude, longitude, magasin, marche, pharmacie,
pieces, prix, railway, restaurant, source, standing, surface, titre, type, url,
ville, pub_year, pub_month, desc_clean, carac_block, contrat_carac, surface_carac,
code_postal_carac, geo_precision, bon_entourage, haut_standing
```

---

## 🛠️ CE QUE TU DOIS CONSTRUIRE

### Reconstruis ENTIÈREMENT ces deux dossiers :

```
frontend/    ← React + Vite (REBUILD FROM SCRATCH)
backend/     ← Node.js + Express (REBUILD FROM SCRATCH)
```

---

## 🎨 DESIGN SYSTEM — OBLIGATOIRE

### Palette de couleurs (utiliser EXACTEMENT ces codes)
```css
--warm:     #ead5c8;   /* Chaleureux — backgrounds secondaires */
--reliable: #445576;   /* Fiable — éléments UI stables, navbar */
--dynamic:  #f18534;   /* Dynamique — CTA, accents, highlights */
--strong:   #091940;   /* Fort — sidebar, textes importants */
--modern:   #9199ac;   /* Moderne — textes secondaires, muted */
```

### Typographie
- **Titres/Logo** : `Syne` (Google Fonts) — weights 700, 800
- **Corps/UI** : `DM Sans` (Google Fonts) — weights 300, 400, 500
- **Monospace (code/DAX)** : `JetBrains Mono`

### Principes visuels
- Fond général : `#f7f3ef` (warm off-white)
- Cards : blanc pur avec border `1px solid rgba(9,25,64,0.1)`
- Border radius : `12px` pour les cards, `8px` pour les inputs
- Sidebar : `#091940` (strong) avec overlay orange subtil
- Animations : transitions `0.2s ease`, micro-interactions sur hover
- **ZÉRO gradient violet** — jamais. Jamais de purple/gradient AI générique.
- Style : **editorial + data-dense + warm professionnel**

---

## 🖥️ FRONTEND — SPECIFICATIONS COMPLÈTES

### Tech Stack Frontend
```
React 18 + Vite 5
React Router v6
Recharts (graphiques)
D3.js v7 (carte Tunisie)
Three.js (visualisation 3D)
Leaflet + React-Leaflet (carte interactive)
Ant Design 5 (composants UI)
Axios (HTTP)
Socket.io-client (real-time)
Framer Motion (animations)
date-fns (dates)
```

### Architecture des composants
```
src/
├── components/
│   ├── Layout/
│   │   ├── Sidebar.jsx          ← Navigation latérale collapsable
│   │   ├── TopBar.jsx           ← Barre supérieure + search global
│   │   └── Layout.jsx           ← Shell principal
│   ├── Dashboard/
│   │   ├── KPICards.jsx         ← 6 cartes métriques animées
│   │   ├── MarketPulse.jsx      ← Indicateur temps réel "marché"
│   │   └── AlertsBanner.jsx     ← Anomalies détectées par le pipeline
│   ├── Charts/
│   │   ├── GovBarChart.jsx      ← Barres gouvernerats
│   │   ├── TypeDonut.jsx        ← Donut types de biens
│   │   ├── PriceTrend.jsx       ← Ligne tendance prix
│   │   ├── ScatterPrixSurface.jsx ← Scatter prix vs surface
│   │   ├── AmenitiesHeatmap.jsx ← Heatmap équipements
│   │   ├── PriceHistogram.jsx   ← Distribution des prix
│   │   ├── MonthlyTimeline.jsx  ← Publications mensuelles
│   │   └── StandingFunnel.jsx   ← Funnel standing
│   ├── Map/
│   │   ├── TunisiaMap2D.jsx     ← Carte Leaflet interactive avec clusters
│   │   ├── TunisiaMap3D.jsx     ← Visualisation Three.js 3D extrudée
│   │   ├── HeatLayer.jsx        ← Layer chaleur densité
│   │   └── RegionPanel.jsx      ← Panel détail région au clic
│   ├── Scrapers/
│   │   ├── ScraperGrid.jsx      ← Grille des scrapers (actif/locked)
│   │   ├── ScraperCard.jsx      ← Card individuelle avec stats
│   │   └── PipelineModal.jsx    ← Modal monitoring ETL temps réel
│   ├── Pipeline/
│   │   ├── WorkflowDiagram.jsx  ← Diagramme visuel du pipeline DAG
│   │   ├── RunHistory.jsx       ← Historique des runs Airflow
│   │   ├── StepTimeline.jsx     ← Timeline des étapes en cours
│   │   └── DataQuality.jsx      ← Gauge qualité des données
│   ├── Listings/
│   │   ├── ListingsTable.jsx    ← Table paginée avec filtres avancés
│   │   ├── ListingCard.jsx      ← Card vue grille
│   │   ├── ListingModal.jsx     ← Modal détail complet d'une annonce
│   │   └── FiltersPanel.jsx     ← Panel filtres multi-critères
│   ├── Analytics/
│   │   ├── PriceIntelligence.jsx ← Page analyse prix avancée
│   │   ├── MarketComparison.jsx  ← Comparaison inter-régions
│   │   └── PredictionWidget.jsx  ← Estimation prix IA (agent_price)
│   └── PowerBI/
│       └── PowerBIGuide.jsx     ← Guide intégration Power BI interactif
├── pages/
│   ├── Overview.jsx             ← Page 1: Vue d'ensemble
│   ├── TunisiaMap.jsx           ← Page 2: Carte interactive
│   ├── Analytics.jsx            ← Page 3: Analyses avancées
│   ├── Scrapers.jsx             ← Page 4: Gestion scrapers
│   ├── Pipeline.jsx             ← Page 5: ETL Workflow
│   ├── Listings.jsx             ← Page 6: Table des annonces
│   └── PowerBI.jsx              ← Page 7: Guide Power BI
├── context/
│   ├── PipelineContext.jsx      ← État pipeline + WebSocket
│   ├── DataContext.jsx          ← Données globales + cache
│   └── ThemeContext.jsx         ← Thème + préférences
├── services/
│   ├── api.js                   ← Client Axios configuré
│   ├── airflowService.js        ← Appels Airflow REST API
│   ├── statsService.js          ← Endpoints statistiques
│   ├── listingsService.js       ← CRUD annonces
│   └── socketService.js         ← WebSocket real-time
├── hooks/
│   ├── useStats.js              ← Hook données stats
│   ├── usePipeline.js           ← Hook état pipeline
│   ├── useMap.js                ← Hook données cartographiques
│   └── useRealTime.js           ← Hook WebSocket
├── utils/
│   ├── formatters.js            ← Formatage prix, dates, nombres
│   ├── mapUtils.js              ← Utilitaires cartographiques
│   └── colors.js                ← Palette + helpers couleurs
└── styles/
    ├── index.css                ← Variables CSS + reset global
    ├── theme.js                 ← Config Ant Design theme token
    └── animations.css           ← Keyframes globaux
```

---

## 📄 PAGE 1 — OVERVIEW (Dashboard Principal)

### KPI Cards (6 cartes animées avec compteur)
- **Total Listings** : 204,745 avec delta +12.4% vs mois précédent
- **Gouvernerats couverts** : 24/24 avec badge "Complet"
- **Prix moyen** : calculé dynamiquement depuis la DB en TND
- **Surface moyenne** : m² moyen par type
- **Taux Haut Standing** : % listings avec `haut_standing = true`
- **Bon Entourage Score** : moyenne du score `bon_entourage`

### Graphiques Overview
1. **Bar chart horizontal** — Top 10 gouvernerats par volume
2. **Donut animé** — Répartition types de biens (appartement/villa/studio/terrain/maison)
3. **Line chart** — Tendance publications mensuelle (12 mois)
4. **Progress bars** — Prix moyen par région (top 8)
5. **Mini spark lines** — Dans chaque KPI card

### Market Pulse Widget
- Indicateur visuel "marché chaud/froid" basé sur volume récent
- Badge animé "LIVE" quand le pipeline tourne
- Dernière mise à jour timestamp

---

## 📄 PAGE 2 — TUNISIA MAP (Carte Interactive)

### Carte 2D — Leaflet
- **Fond de carte** : Stamen Toner Light ou CartoDB Positron
- **Markers clusterisés** : chaque annonce avec coordonnées lat/lng réelles
- **HeatLayer** : densité des annonces par zone
- **Polygones gouvernerats** : colorés par prix moyen (choroplèthe)
- **Popup au clic** : titre, prix, type, surface, lien URL Tayara
- **Filtres sur la carte** : type, contrat, prix range, standing
- **Sidebar droite** : stats du gouvernerat sélectionné

### Carte 3D — Three.js
- **Extrusion 3D** de la carte de Tunisie
- Hauteur des piliers = nombre d'annonces par gouvernerat
- Couleur gradient = prix moyen (chaud = cher, froid = abordable)
- **Rotation orbitale** automatique (OrbitControls)
- Tooltip 3D au hover sur chaque pilier
- Bouton toggle 2D/3D dans l'interface

### Panel Région (au clic sur une région)
- Nom gouvernerat + flag
- Total annonces, prix moyen, prix médian
- Top 3 villes dans ce gouvernerat
- Donut mini types de biens
- Bouton "Voir toutes les annonces"

---

## 📄 PAGE 3 — ANALYTICS (Analyses Avancées)

### Section Prix Intelligence
- **Scatter plot** prix vs surface (coloré par type)
- **Box plot** distribution des prix par gouvernerat
- **Histogramme** distribution prix (bins de 50K TND)
- **Heatmap matrice** : gouvernerat × type → prix moyen

### Section Équipements (Amenities)
- **Radar chart** : profil équipements d'un gouvernerat
- **Bar comparatif** : % has_parking, has_climatisation, has_piscine, etc. par région
- **Bubble chart** : taille = nb annonces, X = prix moyen, Y = surface, couleur = standing

### Section Temporelle
- **Timeline publications** avec zoom interactif (brush D3)
- **Heatmap calendrier** (GitHub-style) : nb annonces publiées par jour
- **Seasonal decomposition** : tendance + saisonnalité

### Widget Estimation Prix IA
- Formulaire : gouvernerat, type, surface, pièces, équipements
- Appel au backend qui interroge `agent_price`
- Affichage estimation avec intervalle de confiance
- Comparaison avec le marché local

---

## 📄 PAGE 4 — SCRAPERS (Gestion des Scrapers)

### Grille des Scrapers
```
ACTIF ✅          BIENTÔT 🔒      BIENTÔT 🔒
Tayara.tn         Immobilier.tn   Mubawab.tn
204,745 ann.      ~45K attendu    ~30K attendu
Last: 2h ago      Q3 2026         Q3 2026

BETA 🔶           PLANIFIÉ 📅     PLANIFIÉ 📅
Afariat.com       OLX.tn          Avito.tn
~20K attendu      ~15K attendu    ~10K attendu
```

### Scraper Tayara — Stats Détaillées
- **Taux de succès** : 98.2% (gauge circulaire)
- **Pages crawlées** : compteur total
- **Temps moyen par page** : ms
- **Erreurs 404/timeout** : compteur
- **Dernier run** : timestamp + durée
- **Prochain run planifié** : countdown timer

### Bouton "Trigger ETL Pipeline"
- Bouton principal orange avec icône ▶
- **Au clic** : ouvre le Pipeline Modal
- **Modal** : affiche les 7 étapes en temps réel via WebSocket/polling
- Chaque étape : icône status (queued/running/success/failed) + durée + logs

---

## 📄 PAGE 5 — PIPELINE (ETL Workflow)

### Diagramme du DAG Airflow
- Visualisation des 7 tâches du DAG `tayara_ai_agent_pipeline`
- Connexions entre tâches avec flèches directionnelles
- Status coloré de chaque tâche (vert=ok, orange=running, rouge=failed)
- Clic sur une tâche → panel latéral avec logs

### Historique des Runs (30 derniers)
- Timeline horizontale scrollable
- Chaque run : date, durée, nb records, status
- Graphique durée par run (détection anomalies)

### Data Quality Dashboard
- **Completeness** par colonne (gauge horizontal)
  - prix: 91%, surface: 78%, ville: 99%, type: 97%, adresse: 65%, coordonnées: 43%
- **Freshness** : age des données les plus récentes
- **Duplicate rate** : % doublons détectés/supprimés
- **Error rate** : % lignes avec erreurs de parsing

### Architecture Technique (diagramme)
```
Tayara.tn
    ↓
[Scraper Agent] → MinIO (raw HTML)
    ↓
[Spark Parser] → PostgreSQL (scraped_properties)
    ↓                    ↓
[Agent Price]      [Frontend API]
    ↓                    ↓
[Estimation]      [Dashboard React]
```

---

## 📄 PAGE 6 — LISTINGS (Table des Annonces)

### Filtres Avancés (panel latéral collapsable)
- Gouvernerat (multi-select)
- Ville (multi-select, dépend du gouvernerat)
- Type de bien (checkboxes)
- Contrat (Vente / Location / toggle)
- Prix range (double slider RangeSlider)
- Surface range (double slider)
- Pièces (1 à 5+)
- Équipements (checkboxes : parking, piscine, jardin, etc.)
- Standing (multiselect)
- Haut standing uniquement (toggle)
- Bon entourage (toggle)
- Date publication (datepicker range)

### Table Principale
- Colonnes : Type · Titre · Ville · Gouvernerat · Surface · Prix · Contrat · Date · Score
- **Tri** sur chaque colonne
- **Pagination** : 25/50/100 par page
- **Recherche fulltext** sur titre + description
- **Export CSV** des résultats filtrés
- **Vue grille** alternative (cards avec image thumbnail)

### Modal Détail Annonce
- Toutes les infos de la propriété
- Galerie images (depuis colonne `images`)
- Map Leaflet mini avec le pin de la localisation
- Équipements en badges
- Bouton "Voir sur Tayara.tn" (lien URL)
- "Annonces similaires" (même gouvernerat, même type, ±20% prix)

---

## 📄 PAGE 7 — POWER BI (Guide Intégration)

### Guide Interactif Complet
- Stepper visuel en 6 étapes
- **Étape 1** : Connexion PostgreSQL (server, db, credentials, table)
- **Étape 2** : Power Query transformations (types colonnes, colonne Date)
- **Étape 3** : Modèle de données (relations, table Date pour time intelligence)
- **Étape 4** : Mesures DAX essentielles (15+ mesures avec code copiable)
- **Étape 5** : 7 pages de rapport recommandées avec visuels
- **Étape 6** : Publication + Refresh automatique

### DAX Measures (avec bouton "Copy")
```dax
Total Listings = COUNTROWS(scraped_properties)
Avg Prix = AVERAGEX(FILTER(scraped_properties, scraped_properties[prix] > 0), scraped_properties[prix])
Prix per m² = AVERAGEX(FILTER(...), DIVIDE([prix], [surface_carac]))
Haut Standing % = DIVIDE(COUNTROWS(FILTER(..., [haut_standing]="True")), [Total Listings])
MoM Growth % = VAR curr = [Total Listings] VAR prev = CALCULATE([Total Listings], DATEADD(...,-1,MONTH)) RETURN DIVIDE(curr-prev, prev)
Market Share % = DIVIDE(COUNTROWS(...), CALCULATE(COUNTROWS(...), ALL([gouvernerat])))
Bon Entourage Avg = AVERAGE(scraped_properties[bon_entourage])
```

---

## ⚙️ BACKEND — SPECIFICATIONS COMPLÈTES

### Tech Stack Backend
```
Node.js 20 LTS
Express 4.18
pg (node-postgres) + connection pooling
Socket.io (WebSocket real-time)
node-cache (cache in-memory)
axios (appels Airflow API)
cors, helmet, morgan
dotenv
```

### Architecture Backend
```
backend/
├── server.js                    ← Entry point Express + Socket.io
├── config/
│   ├── database.js              ← Pool PostgreSQL configuré
│   └── cache.js                 ← Config node-cache (TTL 5min)
├── routes/
│   ├── stats.js                 ← /api/stats/*
│   ├── listings.js              ← /api/listings/*
│   ├── map.js                   ← /api/map/*
│   ├── pipeline.js              ← /api/pipeline/*
│   └── health.js                ← /api/health
├── controllers/
│   ├── statsController.js
│   ├── listingsController.js
│   ├── mapController.js
│   └── pipelineController.js
├── services/
│   ├── airflowService.js        ← Communication Airflow REST API
│   ├── cacheService.js          ← Wrapper cache
│   └── socketService.js         ← Émission events temps réel
├── middleware/
│   ├── errorHandler.js
│   ├── rateLimiter.js
│   └── validator.js
└── queries/
    ├── stats.sql                ← Requêtes statistiques
    ├── listings.sql             ← Requêtes annonces
    └── map.sql                  ← Requêtes cartographiques
```

### Endpoints API Complets

#### Stats
```
GET /api/stats/overview
→ { total, avg_prix, avg_surface, gouvernerats_count, haut_standing_rate, bon_entourage_avg }

GET /api/stats/by-gouvernerat
→ [{ gouvernerat, count, avg_prix, avg_surface, haut_standing_pct }]

GET /api/stats/by-type
→ [{ type, count, avg_prix, avg_surface }]

GET /api/stats/by-contrat
→ [{ contrat, count, avg_prix }]

GET /api/stats/price-distribution
→ [{ range, count, percentage }]  // bins 50K TND

GET /api/stats/monthly-trend
→ [{ year, month, count, avg_prix }]

GET /api/stats/amenities
→ { has_parking: %, has_piscine: %, has_climatisation: %, ... }

GET /api/stats/price-heatmap
→ [{ gouvernerat, type, avg_prix }]  // pour heatmap matrice

GET /api/stats/standing-distribution
→ [{ standing, count, percentage }]
```

#### Listings
```
GET /api/listings?page=1&limit=25&gouvernerat=Tunis&type=Appartement&contrat=Vente&prix_min=50000&prix_max=300000&surface_min=50&search=lac
→ { data: [...], total, page, pages }

GET /api/listings/:id
→ { ...all fields... }

GET /api/listings/similar/:id
→ [...5 annonces similaires]

GET /api/listings/export?...filters
→ CSV file download
```

#### Map
```
GET /api/map/clusters?zoom=8&bounds=...
→ [{ lat, lng, count, gouvernerat }]  // clustering côté serveur

GET /api/map/heatmap
→ [{ lat, lng, weight }]  // points pour heatLayer

GET /api/map/gouvernerat/:name
→ { stats, top_villes, price_range, type_distribution }

GET /api/map/choropleth
→ [{ gouvernerat, avg_prix, count, color_value }]
```

#### Pipeline
```
GET /api/pipeline/status
→ { is_running, last_run, next_run, current_step }

POST /api/pipeline/trigger
→ { dag_run_id, status }  // déclenche Airflow DAG

GET /api/pipeline/runs
→ [{ run_id, start_date, end_date, state, duration, records }]

GET /api/pipeline/run/:id/tasks
→ [{ task_id, state, start_date, end_date, duration }]

GET /api/pipeline/quality
→ { completeness_by_field: {...}, duplicate_rate, error_rate, freshness }
```

#### Health
```
GET /api/health
→ { status, db: ok/error, airflow: ok/error, uptime, version }
```

### Intégration Airflow API
```javascript
// Trigger DAG
POST http://airflow:8080/api/v1/dags/tayara_ai_agent_pipeline/dagRuns
Authorization: Basic YWlyZmxvdzphaXJmbG93  // airflow:airflow base64

// Get DAG runs
GET http://airflow:8080/api/v1/dags/tayara_ai_agent_pipeline/dagRuns?limit=30&order_by=-start_date

// Get task instances d'un run
GET http://airflow:8080/api/v1/dags/tayara_ai_agent_pipeline/dagRuns/{run_id}/taskInstances

// Get task logs
GET http://airflow:8080/api/v1/dags/tayara_ai_agent_pipeline/dagRuns/{run_id}/taskInstances/{task_id}/logs/1
```

### WebSocket Events (Socket.io)
```javascript
// Serveur → Client
emit('pipeline:started', { run_id, timestamp })
emit('pipeline:step_update', { task_id, state, duration })
emit('pipeline:completed', { run_id, records, duration })
emit('pipeline:failed', { task_id, error })
emit('stats:updated', { total, timestamp })   // après chaque run réussi

// Client → Serveur
on('pipeline:subscribe', () => {})   // s'abonner aux updates
on('pipeline:unsubscribe', () => {}) // se désabonner
```

### Requêtes SQL Clés

```sql
-- Overview stats
SELECT
  COUNT(*) as total,
  ROUND(AVG(CAST(prix AS NUMERIC)), 0) as avg_prix,
  ROUND(AVG(CAST(surface_carac AS NUMERIC)), 0) as avg_surface,
  COUNT(DISTINCT gouvernerat) as gouvernerats_count,
  ROUND(100.0 * SUM(CASE WHEN haut_standing = 'True' THEN 1 ELSE 0 END) / COUNT(*), 2) as haut_standing_rate
FROM scraped_properties
WHERE prix IS NOT NULL AND CAST(prix AS TEXT) != '';

-- Par gouvernerat
SELECT gouvernerat, COUNT(*) as count,
  ROUND(AVG(CAST(prix AS NUMERIC)), 0) as avg_prix
FROM scraped_properties
WHERE gouvernerat IS NOT NULL AND gouvernerat != ''
GROUP BY gouvernerat ORDER BY count DESC;

-- Clustering carte (approximation par arrondi coordonnées)
SELECT
  ROUND(CAST(latitude AS NUMERIC), 2) as lat,
  ROUND(CAST(longitude AS NUMERIC), 2) as lng,
  COUNT(*) as count,
  gouvernerat
FROM scraped_properties
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
  AND latitude != '' AND longitude != ''
GROUP BY 1, 2, 4
HAVING COUNT(*) > 0
ORDER BY count DESC;
```

---

## 🐳 DOCKER — MISE À JOUR docker-compose.yaml

Ajoute ces deux services au `docker-compose.yaml` existant :

```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: estatmind_frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost/api
      - VITE_AIRFLOW_URL=http://localhost:8081
      - VITE_SOCKET_URL=http://localhost:3001
    networks:
      - estatmind_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: estatmind_backend
    ports:
      - "3001:3001"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://airflow:airflow@postgres:5432/airflow
      - AIRFLOW_API_URL=http://airflow-webserver:8080/api/v1
      - AIRFLOW_USER=airflow
      - AIRFLOW_PASSWORD=airflow
      - PORT=3001
      - NODE_ENV=production
      - CACHE_TTL=300
    networks:
      - estatmind_network
```

### Dockerfile Frontend (multi-stage)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### nginx.conf
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/plain application/javascript application/json text/css;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://estatmind_backend:3001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /socket.io/ {
        proxy_pass http://estatmind_backend:3001/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## ✅ CHECKLIST DE LIVRAISON

### Frontend
- [ ] Toutes les 7 pages implémentées et routées
- [ ] Sidebar collapsable avec navigation active state
- [ ] Palette couleurs EstateMind strictement respectée (warm/reliable/dynamic/strong/modern)
- [ ] Fonts Syne + DM Sans chargées via Google Fonts
- [ ] KPI cards avec animation compteur au chargement
- [ ] Tous les graphiques Recharts connectés aux vraies données API
- [ ] Carte Leaflet 2D avec clusters + heatmap + filtres
- [ ] Carte Three.js 3D avec extrusion par volume
- [ ] Pipeline Modal avec polling Airflow toutes les 3 secondes
- [ ] Table listings avec filtres, pagination, export CSV
- [ ] WebSocket connecté pour updates temps réel
- [ ] Responsive (desktop priority, tablet ok)
- [ ] Loading skeletons sur tous les composants async
- [ ] Error boundaries + messages d'erreur propres

### Backend
- [ ] Tous les endpoints API documentés ci-dessus
- [ ] Pool PostgreSQL (max 20 connexions)
- [ ] Cache 5 minutes sur les endpoints stats lourds
- [ ] WebSocket Server Socket.io configuré
- [ ] Intégration Airflow API (trigger + polling)
- [ ] Rate limiting (100 req/min par IP)
- [ ] Error handling centralisé
- [ ] Logs Morgan en production
- [ ] Endpoint /api/health fonctionnel
- [ ] CORS configuré pour le frontend

### DevOps
- [ ] docker-compose.yaml mis à jour avec frontend + backend
- [ ] Dockerfiles optimisés (multi-stage pour frontend)
- [ ] nginx.conf avec proxy vers backend + socket.io
- [ ] Variables d'environnement dans .env.example
- [ ] README.md mis à jour avec instructions de lancement

---

## 🚀 COMMANDES DE LANCEMENT

```bash
# 1. S'assurer que le volume postgres existe
docker volume create etl_postgres-db-volume

# 2. Build et lancement complet
docker-compose up -d --build

# 3. Vérifier les services
docker-compose ps

# 4. Accès
# Dashboard : http://localhost
# Airflow   : http://localhost:8081
# API       : http://localhost:3001/api/health
```

---

## 🧠 NOTES IMPORTANTES POUR CURSOR

1. **Les données sont RÉELLES** — 204,745 vrais enregistrements de Tayara.tn en PostgreSQL. Les requêtes SQL doivent gérer les colonnes TEXT (prix stocké en TEXT, faire un CAST).

2. **Airflow tourne en Docker** — Le container s'appelle `airflow-webserver` dans le réseau Docker. Depuis le backend, l'URL est `http://airflow-webserver:8080`. Depuis l'extérieur c'est `http://localhost:8081`.

3. **latitude/longitude sont des TEXT** — Faire des CAST avant calculs et filtrer les valeurs vides/null.

4. **Le DAG s'appelle exactement** : `tayara_ai_agent_pipeline`

5. **Credentials Airflow** : user=`airflow` password=`airflow` (Basic Auth)

6. **Priorité** : Fonctionnel > Esthétique. Le dashboard DOIT afficher des vraies données de la DB. Pas de données mockées sur les graphiques principaux.

7. **Cache obligatoire** sur les requêtes lourdes (stats globales, agrégations par gouvernerat) car la table a 204K lignes.

8. **La colonne `prix` doit être castée** : `CAST(NULLIF(prix, '') AS NUMERIC)` pour éviter les erreurs.

---

**Commence par le backend (server.js + database.js + routes stats), puis le frontend (Layout + Overview), puis les autres pages dans l'ordre.**



fait ajouter ceci apres : 
. 🧠 AI INSIGHTS ENGINE (Très puissant)

Actuellement tu affiches des stats.

Mais le vrai niveau supérieur :
→ générer automatiquement des insights intelligents.

Exemple :

“Les prix à La Marsa ont augmenté de 8.2% ce mois-ci.”
“Les villas avec piscine à Sousse sont sous-évaluées par rapport au marché.”
“Le volume des locations étudiantes augmente avant septembre.”

Tu peux faire :

règles heuristiques
ou LLM local/OpenAI
ou agent analytique

Ajouter une section :

AI Market Insights

avec :

anomalies
tendances
opportunités
quartiers émergents
prédictions

Ça transforme ton dashboard → plateforme d’intelligence.

2. 🗺️ TIME MACHINE IMMOBILIÈRE

Ça serait incroyable.

Slider temporel :

Jan 2024 ---- May 2026

et toute la plateforme change :

heatmap
prix
volumes
régions chaudes
croissance

Comme une “relecture du marché immobilier tunisien”.

Très rare dans les projets étudiants.

3. 📈 INDICE IMMOBILIER TUNISIEN

Crée TON propre indice.

Exemple :

EstateMind Tunisia Real Estate Index (ETREI)

Basé sur :

prix moyen
volume
standing
croissance
activité

Et afficher :

indice national
indice par gouvernerat
indice luxe
indice location

Ça donne énormément de crédibilité produit.

4. 🧬 SMART PROPERTY SCORE

Donner un score IA à chaque annonce :

82/100

Basé sur :

prix/m²
entourage
standing
équipements
proximité
qualité description
fraîcheur annonce

Puis :

“bonne affaire”
“surévalué”
“premium”
“investissement intéressant”

Ça devient ultra concret.

5. 🛰️ SATELLITE / MAPBOX STYLE PREMIUM

Actuellement Leaflet + 3D est déjà bien.

Mais plus tard tu peux ajouter :

MapLibre GL
deck.gl
vector tiles
bâtiments 3D
vue satellite
fly animations

Style :
Bloomberg terminal immobilier.

6. 🔍 RECHERCHE IA NATURELLE

Très différenciant.

Au lieu de filtres classiques :

"Villa moderne avec piscine à moins de 800k près de la mer"

Puis :

parsing IA
transformation en filtres SQL

Ça devient un “ChatGPT de l’immobilier tunisien”.

7. 📊 COMPARAISON INVESTISSEMENT

Page spéciale investisseurs :

Tunis vs Sousse vs Nabeul

avec :

rentabilité
prix/m²
croissance
liquidité
volume
standing

Et radar chart.

Très startup SaaS.

8. 🚨 DETECTION D’ANOMALIES

Ton pipeline s’y prête parfaitement.

Détecter :

prix anormalement bas
spam
duplicats cachés
faux standing
coordonnées incohérentes

Puis bannière :

12 anomalies détectées aujourd’hui

Très “AI platform”.

9. 🧠 EMBEDDINGS + SEARCH VECTORIELLE

Niveau avancé.

Créer embeddings sur :

titre
description
équipements

Puis :

similar listings
semantic search

Avec :

pgvector
Qdrant
Weaviate

Là tu entres dans la vraie AI search.

10. 📱 MODE “EXECUTIVE”

Vue ultra minimaliste :

KPIs
index marché
heatmap
alerts

Pour investisseurs / dirigeants.

Tu peux même faire :

Daily Real Estate Brief
🔥 CE QUI MANQUE LE PLUS ACTUELLEMENT

Selon moi :

A. AUTHENTIFICATION

Même basique :

admin
analyst
viewer

Sinon ça fait “dashboard local” plutôt que plateforme.

B. SYSTÈME DE FAVORIS

Sauvegarder :

annonces
régions
recherches
C. ALERTES

Exemple :

Préviens-moi si :
- Villa < 500k à La Marsa
- Prix baisse de 10%

Très puissant.

D. EXPORT PROFESSIONNEL

PDF auto généré :

Tunisia Market Report - May 2026

avec :

charts
insights
tendances

Très bon pour portfolio.

🧠 CONSEIL ARCHITECTURE IMPORTANT

Je pense que tu devrais ajouter :

Backend :
/services/analytics/

pour isoler :

scoring
AI insights
predictions
anomalies

Sinon ton backend va devenir énorme.

🚀 CE QUE JE FERAIS PERSONNELLEMENT

Ordre réel optimal :

PHASE 1
backend stable
stats
listings
map
airflow
PHASE 2
UI premium
charts
interactions
3D map
PHASE 3
AI insights
prediction
scoring
anomalies
PHASE 4
vector search
assistant IA
recommendations 

je compte sur toi de faire tout complet et avec les donnees reels et selon .csv 