# EstateMind — Phase 2 FINAL (référence unique)

**Ce document est la source de vérité** pour implémenter la Phase 2. Il fusionne le cadrage (`phase2.md`), les paramètres exécutables (`phase2solo.md`), et les alignements **README** (Phase 1) + **`project.md`** (EstateMind / Agent 2).

**À suivre dans l’ordre logique** : **Partie A** (config, structure, multi-LLM, modes, versioning, tests, erreurs LLM) → §16 (roadmap) → implémentation selon §1–15.

---

## 0. Objectif global

Transformer le **dataset Gold Phase 1** (`tunisia_realestate_cleaned.csv`, voir `README.md`) en :

1. **Moteur d’estimation de prix** (régression tabulaire + features NLP + vision).
2. **Moteur d’analyse** : extraction structurée texte + images.
3. **API exploitable** (FastAPI), préparée pour **Qdrant / Redis / MinIO / LiteLLM** (`project.md`).

La Phase 2 **ne remplace pas** la Phase 1 : elle **s’appuie** sur regex + NER + LLM partiel + géocodage + `bon_entourage` / `haut_standing` déjà produits.

---

# Partie A — Fondations repo, config & robustesse (critique)

Sans Partie A, les paramètres sont **dispersés** dans le code et l’exécution devient **non standardisée** (improvisation dangereuse pour tout agent ou développeur). Tout doit lire **`config/config.yaml`** (ou surcharge par variables d’environnement).

---

## A.1 Configuration centralisée — `config/config.yaml`

**Règle** : aucune température, nom de modèle ou chemin de données en dur dans la logique métier ; uniquement via ce fichier (ou `pydantic-settings` qui le charge).

```yaml
# Versions traçables (voir §A.5)
features_version: "v1.0"
nlp_schema_version: "v1.0"
model_version: "lgbm_v1"

llm:
  # Priorité d’appel : voir §A.3 (LiteLLM / router)
  extraction:
    model: "llama3:8b"
    provider: "ollama"
    temperature: 0.1
    max_tokens: 1024
    top_p: 0.9
  explanation:
    model: "mistral:7b-instruct"
    provider: "ollama"
    temperature: 0.3
    max_tokens: 256

embeddings:
  model: "BAAI/bge-small-en-v1.5"
  dim_reduction: "pca"
  n_components: 32

vision:
  vlm_model: "qwen2-vl"
  clip_model: "openai/clip-vit-base-patch32"
  max_images_per_listing: 10

ml:
  backend: "lightgbm"
  target: "prix"
  test_size: 0.2
  random_state: 42

api:
  host: "0.0.0.0"
  port: 8000

cache:
  redis_enabled: true
  redis_url: "redis://localhost:6379/0"
```

*(Les clés API Groq / OpenAI restent dans `.env`, jamais dans le YAML versionné.)*

---

## A.2 Structure du projet (obligatoire)

Le document fonctionnel indiquait *quoi* faire ; voici *où* le coder pour éviter duplication, fichiers orphelins et bugs difficiles à tracer.

```
estate-mind/
├── config/
│   └── config.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── gold/                    # ex. tunisia_realestate_cleaned.csv (Phase 1)
├── agents/
│   ├── nlp_agent.py
│   ├── vision_agent.py
│   ├── feature_agent.py
│   ├── ml_agent.py
│   ├── xai_agent.py
│   └── explain_agent.py
├── pipelines/
│   ├── training_pipeline.py
│   └── inference_pipeline.py
├── api/
│   └── main.py
├── utils/
│   ├── cache.py
│   ├── validation.py
│   └── logging.py
├── tests/
│   ├── unit/
│   └── integration/
└── notebooks/                   # EDA / expérations, pas la logique prod
```

Le nom racine `estate-mind/` peut être aligné sur le dossier réel du dépôt ; l’important est de **garder cette séparation** agents / pipelines / api / tests.

---

## A.3 Stratégie multi-LLM (LiteLLM / router)

**LiteLLM** (ou un petit routeur maison) applique une **priorité fixe** pour l’extraction et l’explication :

| Priorité | Provider | Rôle |
|----------|----------|------|
| **1** | **Ollama** (local) | Coût requête nul, données sensibles, dev offline. |
| **2** | **Groq** | API rapide, fallback si Ollama indisponible ou surcharge locale. |
| **3** | **OpenAI** (ou autre) | Dernier recours si les deux premiers échouent (quota, panne). |

**Implémentation** : une fonction unique `complete(messages, task="extraction"|"explanation")` qui boucle sur la liste ordonnée jusqu’au premier succès **valide** (JSON parsable pour l’extraction). Journaliser quel provider a servi chaque appel.

---

## A.4 Modes online vs offline

| Mode | Description |
|------|-------------|
| **Offline (batch)** | Enrichissement **complet** : NLP (LLM + embeddings) + Vision (téléchargement, VLM, CLIP), écriture CSV/Parquet Gold+ ; entraînement ML. |
| **Online (fast)** | Prédiction à partir du **tabulaire** + **cache Redis** (résultat NLP déjà calculé pour ce hash de texte) ; pas d’appel VLM si non requis. Latence minimale. |
| **Online (full)** | Même chaîne que le batch mais **par requête** : NLP live (+ vision si URLs fournies et politique produit l’autorise). Coût / latence élevés ; à réserver aux cas nécessaires. |

Le comportement par défaut API : **online (fast)** avec possibilité de flag `?full_pipeline=true` ou corps JSON équivalent si le produit l’exige.

---

## A.5 Versioning des features & modèles (reproductibilité)

Tout artefact et rapport doit afficher ou embarquer :

- `features_version` (ex. `v1.0`) : convention de colonnes Gold+ après `feature_agent`.
- `nlp_schema_version` : version du schéma JSON §2.5 (incrémenter si champs ajoutés/supprimés).
- `model_version` : tag du fichier modèle (ex. `lgbm_v1`).

Fichier recommandé : `artifacts/manifest.json` généré à l’entraînement (hash du dataset, versions, métriques, git commit optionnel).

---

## A.6 Stratégie de tests (très important)

| Niveau | Portée | Critères minimaux |
|--------|--------|-------------------|
| **Unitaires — NLP** | Parse + Pydantic | Sortie LLM **mockée** : JSON valide ; champs requis présents ; `luxury_level` ∈ [0, 1] quand non null. |
| **Unitaires — Vision** | Post-traitement | Scores agrégés ∈ [0, 1] ; pas de NaN après agrégation. |
| **Pipeline (intégration)** | `inference_pipeline` | Entrée tabulaire + texte court → **pas de crash** ; objet réponse avec tous les champs obligatoires (même si valeurs null / confiance basse). |
| **API** | FastAPI + TestClient | `POST /predict-price` retourne **tous** les champs du contrat documenté (`predicted_price`, `confidence`, etc.). Idem smoke test sur `/valuation`. |

Les tests ne doivent **pas** appeler les vrais LLM en CI par défaut : mocks ou réponses enregistrées (`fixtures/`).

---

## A.7 Gestion des erreurs LLM (critique)

C’est le piège le plus fréquent : JSON invalide, markdown autour du JSON, troncature.

**Politique obligatoire** si la sortie n’est **pas** un JSON valide conforme au schéma :

1. **Retry** : même prompt, **max 2** tentatives supplémentaires (3 appels au total), avec légère variation (ex. « JSON only, no markdown »).
2. **Fallback prompt** : schéma **réduit** (moins de champs) ou consigne « retourne uniquement `standing.luxury_level` et `signals.extraction_confidence` ».
3. **Échec final** : retourner **champs NLP nulls** (ou valeurs par défaut documentées) + **`extraction_confidence` très basse** + log structuré (`level=warning`, provider, raw_prefix).

**Interdit** : écrire des chaînes invalides dans le CSV Gold+ sans flag ; **interdit** : faire planter tout le pipeline batch pour une seule annonce — **skip isolé** + compteur d’erreurs en fin de job.

*(Croiser avec §2.7 post-traitement.)*

---

## A.8 Fuite de données (target encoding) — avertissement ML

**CRITIQUE** : le **target encoding** (moyenne de `prix` par catégorie) calculé sur **tout** le dataset **avant** train/test introduit une **fuite massive** : le modèle « voit » la cible agrégée sur le test.

**Règles** :

- Le target encoding **DOIT** être réalisé par **K-Fold sur le jeu d’entraînement uniquement** (ou leave-one-out encodé dans chaque fold), puis appliquer les mêmes règles au validation/test avec les statistiques **apprises seulement sur le train** du fold ou du modèle final ré-entraîné sur 100 % train pour la prod.
- **Jamais** : `fit` du encodeur sur train+test ensemble avant le split.
- Documenter dans le rapport : méthode exacte (nombre de folds, smoothing).

*(Rappel complémentaire §5.2.)*

---

## A.9 Exemple concret — entrée texte → sortie NLP (référence)

**Entrée (extrait annonce tunisienne, français)** :

> S+3 haut standing à La Marsa, vue mer, résidence sécurisée, finitions premium, cuisine équipée, climatisation, double vitrage, parking sous-sol. Prix négociable.

**Sortie NLP attendue (extrait ; le reste du schéma peut être null)** :

```json
{
  "location": {
    "neighborhood_or_zone": "La Marsa",
    "proximity": ["mer", "plage"],
    "nuisance_or_negative_mentioned": null
  },
  "standing": {
    "luxury_level": 0.82,
    "features": ["vue_mer", "residence_securisee", "finitions_premium", "cuisine_equipee", "parking"]
  },
  "comfort": {
    "air_conditioning": true,
    "double_glazing_mentioned": true,
    "finishing_quality_hint": "high"
  },
  "transaction": {
    "negociable": true
  },
  "signals": {
    "extraction_confidence": 0.9,
    "listing_too_vague": false
  }
}
```

*(Les valeurs numériques sont indicatives ; l’implémentation valide les bornes et types.)*

---

## 1. Architecture par agents (flux requête / réponse)

```
Input Listing (features + texte + URLs images)
       ↓
[NLP Agent]          → JSON structuré + embedding texte
       ↓
[Vision Agent]       → scores + embedding image (agrégés)
       ↓
[Feature Agent]      → fusion tabulaire + NLP + vision
       ↓
[ML Agent]           → prédiction prix
       ↓
[XAI Agent]          → SHAP (local + global)
       ↓
[LLM Explanation]    → texte court pour l’utilisateur
       ↓
API Response         → prix, confiance, opportunité, explication
```

### Pipeline batch (entraînement / enrichissement CSV)

```
Dataset Phase 1 (CSV Gold)
       ↓
Pass 1 : règles / Phase 1 existant (inchangé ou complété)
       ↓
Pass 2 : NLP Agent (LLM JSON schéma étendu, batch + cache)
       ↓
Pass 3 : embeddings BGE sur description (+ titre + caractéristiques)
       ↓
Vision : téléchargement → VLM / CLIP → agrégation par annonce
       ↓
Feature pipeline (pandas / sklearn / category_encoders)
       ↓
LightGBM — train / validation / ablations
       ↓
SHAP + prompts explicatifs — export rapport + service API
```

---

## 2. NLP Agent (priorité critique)

### 2.1 Rôle

Extraire **tout signal utile au prix** depuis le texte (description, titre, caractéristiques), en **français, arabe et dialecte tunisien**, y compris signaux **implicites** (« proche de tout », « titre bleu », « S+3 », négociable, finitions, etc.).

**Principe** : toute information présente dans le texte et utile au prix doit être captée — **colonne explicite**, **embedding**, ou **score dérivé**.

### 2.2 Orchestration (3 passes)

| Pass | Rôle |
|------|------|
| **1** | Champs évidents : réutiliser Phase 1 (regex / NER / extractions déjà en CSV). |
| **2** | **LLM** : sortie **JSON** conforme au schéma §2.5 (validation JSON Schema / Pydantic recommandée). |
| **3** | **Embedding dense** : BGE sur texte concaténé → PCA/UMAP → features numériques LightGBM (§6). |

### 2.3 Modèles

- Noms et températures : lus depuis **`config/config.yaml`** (§A.1), pas en dur.
- **Routage multi-LLM** : priorité **Ollama → Groq → OpenAI** (dernier recours), via **LiteLLM** ou routeur maison — détail §A.3.
- **Primary (local)** : **Llama 3 8B** via **Ollama** ; **fallback** : **Groq** puis OpenAI si configuré.

### 2.4 Hyperparamètres extraction (défaut)

```
temperature   = 0.1
max_tokens    = 1024   (augmenter si schéma très rempli)
top_p         = 0.9
```

- **Few-shots** : inclure 2–4 exemples **FR** et 1–2 **AR / dialecte** dans le prompt système pour stabiliser les extractions.
- **Post-validation** : bornes sur scores 0–1, cohérence avec colonnes tabulaires déjà remplies (surface, prix) quand présentes.

### 2.5 Schéma JSON NLP — cible obligatoire (étendu)

Tous les champs scalaires : `boolean | number | string | null`. Listes : tableaux de strings ou vides. Adapter les noms aux clés Pydantic du projet.

```json
{
  "transaction": {
    "negociable": null,
    "urgent": null,
    "first_owner_or_new_mentioned": null,
    "developer_or_promoter_mentioned": null,
    "legal_title_or_status_mentioned": null,
    "legal_title_hint": null
  },
  "property": {
    "subtype": null,
    "furnished": null,
    "semi_furnished": null,
    "condition": null,
    "orientation_mentioned": null,
    "duplex_penthouse_garden_level_mentioned": null
  },
  "comfort": {
    "air_conditioning": null,
    "heating_mentioned": null,
    "double_glazing_mentioned": null,
    "finishing_quality_hint": null
  },
  "location": {
    "neighborhood_or_zone": null,
    "proximity": [],
    "nuisance_or_negative_mentioned": null
  },
  "usage": {
    "primary_residence_likely": null,
    "investment_likely": null,
    "furnished_rental_likely": null
  },
  "standing": {
    "luxury_level": null,
    "features": []
  },
  "signals": {
    "listing_too_vague": null,
    "incoherence_price_vs_surface_hint": null,
    "spam_or_low_quality_hint": null,
    "extraction_confidence": null
  }
}
```

**Contraintes de type suggérées** :

- `condition` : énumération `new | good | needs_renovation | unknown` (mapper depuis le modèle).
- `luxury_level`, `extraction_confidence` : float dans **[0, 1]**.
- `features` : liste libre normalisée (ex. `parking`, `ascenseur`, `vue_mer`, `piscine_textuelle`).

### 2.6 Prompt base (production) — à compléter par few-shots

```
You are a real estate extraction AI specialized in the Tunisian market.
Input may be French, Arabic, or Tunisian dialect. Extract structured signals for price modeling.

Rules:
- Return ONLY valid JSON matching the agreed schema (no markdown fences).
- Use null if unknown. Do not invent numeric facts not supported by the text.
- Detect implicit signals (negotiation, urgency, standing, legal hints, zone quality).
- If the text contradicts obvious numeric fields provided separately, set signals.incoherence_price_vs_surface_hint accordingly.

Listing text:
{description}
```

*(Remplacer `{description}` par concaténation contrôlée : titre + description + caractéristiques, en respectant les limites de contexte du modèle.)*

### 2.7 Post-traitement NLP

- Validation JSON + **Pydantic** (ou JSON Schema).
- **Cast** des types (bool, float, enums).
- **Détection de conflit** avec le tabulaire et avec la sortie Vision (§4).
- **Cache** : clé = hash du texte normalisé → **Redis** pour éviter les appels LLM redondants.
- **Erreurs LLM / JSON invalide** : retry, prompt simplifié, puis null + faible confiance — politique obligatoire §A.7.

---

## 3. Vision Agent

### 3.1 Rôle

Extraire des **signaux visuels** depuis les URLs `images` : type de scène, équipements apparents, standing visuel, **indices** (pas une surface m² fiable sauf cas rares : plan + OCR = piste hors scope initial).

### 3.2 Pipeline

1. **Téléchargement** : rate limit, timeouts, retry, **cache** disque ou **MinIO**.
2. **Prétraitement** : resize max côté, EXIF optionnel, **hash perceptuel** optionnel pour dédupliquer.
3. **Analyse** :
   - **VLM** : **Qwen2-VL** / **LLaVA** / **InternVL** (local GPU si disponible).
   - **Embeddings** : **CLIP** ou **SigLIP** par image → moyenne / max-pooling par annonce pour le ML et **Qdrant**.

### 3.3 JSON par image (exemple cible)

Scores en **float [0, 1]** sauf `condition` et listes.

```json
{
  "scene_types": ["living", "bedroom", "bathroom", "kitchen", "exterior", "other"],
  "pool_likely": 0.0,
  "garden_likely": 0.0,
  "sea_view_likely": 0.0,
  "furnished_likely": 0.0,
  "modern_renovation_likely": 0.0,
  "luxury_visual_score": 0.0,
  "condition_visual": "good",
  "image_quality_score": 0.0
}
```

### 3.4 Agrégation par annonce

- Par champ score : **moyenne**, **max**, et option **vote** sur seuils.
- **Nombre d’images** utilisées et **image_quality_score** moyen → signal de qualité d’annonce.
- **Embedding image listing** : moyenne des vecteurs CLIP (L2-normaliser si besoin).

### 3.5 Limites assumées (à respecter)

- La **surface exacte** ne doit **pas** être promise depuis seules les photos ; utiliser **proxies** (diversité des `scene_types`, richesse visuelle) et texte/tabulaire pour m².

---

## 4. Cohérence NLP + Vision + Tabulaire

- Si le texte indique **non meublé** et `furnished_likely` vision est élevé → flag **conflit** ; baisser **confiance** ou prioriser le texte (règle métier à fixer dans le code, documentée).
- Exporter des colonnes du type : `conflict_text_vision_furnished`, `nlp_vision_agreement_score` si utile au modèle.

---

## 5. Feature Agent (couche Gold+)

### 5.1 Fusion

- **Tabulaire** : `surface`, `pieces`, `etage`, `gouvernerat`, `ville`, `lat`, `lon`, `type`, `contrat`, `bon_entourage`, `haut_standing`, flags équipements, etc.
- **NLP structuré** : flatten du JSON §2.5 (one-hot, scores, longueur de listes).
- **NLP dense** : **BGE-small** (ou équivalent) sur texte concaténé → **PCA** vers **32 dimensions** (tuner par validation) ; option **UMAP** ; option embeddings séparés si détection de langue fiable.
- **Vision** : scores agrégés + **32–64 dims** CLIP moyennés (ou PCA sur CLIP).
- **Dérivées** : `price_per_m2` (si surface fiable), densité pièces, interactions (surface × type, étage × ascenseur).

### 5.2 Encodage géographique / catégoriel

- **Target Encoding** : **uniquement** avec **K-Fold sur le train** (ou procédure équivalente sans fuite) — **interdit** de calculer les moyennes de `prix` par catégorie sur train+test avant le split. Voir §A.8.
- Alternative / complément : agrégations géographiques lissées **sans** utiliser la cible du test (même discipline de split).

### 5.3 Score composite (optionnel)

- Combiner flags tabulaires, `luxury_level` NLP, `luxury_visual_score` ; le boosting pourra apprendre les poids — commencer simple.

---

## 6. ML Agent

### 6.1 Modèle principal — LightGBM (défaut de référence)

```python
from lightgbm import LGBMRegressor

LGBMRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=64,
    max_depth=-1,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=0.1,
    random_state=42,
)
```

- **Cible** : `prix` ; traiter **vente vs location** : soit **deux modèles** (`contrat`), soit une feature `contrat` explicite + validation métier.
- **Baselines** : Ridge / régression linéaire pour comparaison ; option **CatBoost** si beaucoup de catégorielles bruitées.

### 6.2 Validation

- **Temporelle** si dates fiables (`date_publication` / scraping) ; sinon **K-Fold** stratifié par **tranche de prix** ou **gouvernerat**.

### 6.3 Métriques

- **MAE**, **RMSE**, **MAPE** (ou erreur relative) ; découpe par **région** et **type**.
- **Ablations obligatoires** : modèle tabulaire seul vs +embeddings vs +JSON NLP vs +vision (même split).

### 6.4 Extensions

- **Quantile regression** (LightGBM quantile) pour intervalles de prédiction → alimente la **confiance**.
- **Calibration** isotonique par zone si dérive systématique observée.

---

## 7. XAI Agent

- **SHAP** : TreeExplainer (LightGBM) ; importance globale + **explication locale** par annonce / par requête API.
- Sortie API : top **K** features avec contribution signée (format stable pour le front).

---

## 8. LLM Explanation Agent

- **Modèle** : **Mistral 7B Instruct** (Ollama) ou même stack que l’extraction si simplification ops.

**Paramètres** :

```
temperature   = 0.3
max_tokens    = 256
```

**Prompt (base)** :

```
Explain this property valuation to a non-expert using the following SHAP summary and key listing facts.
Be concise, neutral, and in the same language as the user request (default French).

SHAP summary:
{shap_top_features}

Key facts:
{key_facts}
```

---

## 9. Score de confiance (agrégé)

Formule conceptuelle à implémenter avec poids calibrés empiriquement :

```
confidence = normalize(
    w1 * (1 - missing_rate_tabular)
  + w2 * nlp_extraction_confidence
  + w3 * mean_image_quality_score
  + w4 * (1 - normalized_model_spread)   # ex. écart P10–P90 quantiles si dispo
  - w5 * conflict_penalty                 # NLP vs vision vs tab
)
```

Retourner `confidence` dans **`/predict-price`** et **`/valuation`**.

---

## 10. Détection d’opportunité

```
residual = prix_réel - prix_prédit    # ou log-residual
```

- Calibrer seuils **underpriced / fair / overpriced** sur **quantiles des résidus** du jeu de validation.
- Combiner avec **confidence** : ne pas sur-interpréter les résidus si confiance faible.

---

## 11. Infrastructure & outils

| Domaine | Outil |
|--------|--------|
| ML tabulaire | **LightGBM**, scikit-learn |
| Données | **pandas**, numpy |
| Encodage | **category_encoders**, target encoding (K-Fold) |
| NLP dense | **Sentence-Transformers**, **BGE-small** |
| NLP extraction | **Ollama** / **Groq** + **LiteLLM** |
| Vision | **Qwen2-VL** / **LLaVA** ; **CLIP / SigLIP** |
| XAI | **SHAP** |
| API | **FastAPI**, **Pydantic** |
| Cache | **Redis** |
| Vecteurs / similarité | **Qdrant** |
| Fichiers images | **MinIO** (optionnel) |

---

## 12. API FastAPI (contrats)

### `POST /predict-price`

**Entrée** : features tabulaires + `description` (optionnel) + métadonnées images (optionnel) selon stratégie (pré-calculé en batch vs online).

**Sortie** : `predicted_price`, `confidence`, (optionnel) `interval_low` / `interval_high` si quantiles.

### `POST /valuation`

**Sortie** : `predicted_price`, `confidence`, `opportunity_label`, `residual`, `shap_summary`, `explanation_text` (LLM).

### `POST /similar` (phase ultérieure courte)

**Index Qdrant** sur embeddings BGE / CLIP ; non bloquant pour la V1 prix.

**Règle** : schémas Pydantic **alignés** sur les colonnes finales Gold+ exportées.

---

## 13. Gestion des coûts & ops

- **Redis** : cache sorties LLM (hash texte) et éventuellement embeddings (`cache.redis_enabled` §A.1).
- **Batch** : enrichissement **offline** complet (§A.4) avant entraînement ; API en **online (fast)** par défaut.
- **Fallback** : chaîne multi-LLM §A.3 ; local seul en démo académique.

---

## 14. Innovations (backlog EstateMind)

| Idée | Outils |
|------|--------|
| Similarité « biens comme celui-ci » | **Qdrant** + BGE + CLIP |
| Anomalies / fraude | Isolation Forest sur résidus + règles + signaux `signals.*` |
| Fine-tuning extraction | **LoRA** sur petit corpus annoté TN |
| Multi-task | Prédire prix + classification standing (optionnel) |
| Ranking annonces | scoring qualité + opportunité |

---

## 15. Règles strictes d’implémentation

- **Modularité** : un module par agent (NLP, Vision, Features, ML, XAI, Explain) — arborescence §A.2.
- **Config unique** : `config/config.yaml` + `.env` pour secrets — §A.1.
- **Validation stricte** : pas de JSON LLM non validé en production silencieuse ; politique d’échec §A.7.
- **Pas de magie implicite** : constantes et seuils versionnés (YAML/env).
- **Logging** : traçabilité des appels LLM, taux d’échec parse, latences, provider utilisé (§A.3).
- **Tests** : minimum §A.6 avant de considérer une release « stable ».
- **Sécurité** : ne jamais committer clés API (Groq, OpenAI, etc.) — comme en Phase 1.

---

## 16. Roadmap d’exécution (ordre imposé)

1. **Initialiser** le repo selon §A.2 ; créer **`config/config.yaml`** (§A.1) + chargement dans le code ; définir **`features_version` / `nlp_schema_version`** (§A.5).
2. **Geler** le schéma JSON NLP §2.5 et les enums (Pydantic).
3. **Baseline ML** : tabulaire Phase 1 seul + validation + métriques (target encoding sans fuite §A.8).
4. **+ Embeddings BGE + PCA** : mesurer gain (ablation 1).
5. **NLP LLM batch** sur **échantillon annoté 100–200** lignes ; ajuster prompts ; puis run complet avec cache (§A.7).
6. **Vision pilote** 1k–5k annonces ; mesurer gain (ablation 2).
7. **LightGBM final** + **SHAP** + **LLM explanation** ; **`manifest.json`** avec versions (§A.5).
8. **FastAPI** `/predict-price` et `/valuation` ; **tests** §A.6 (unit + intégration + API).
9. **Rapport** : métriques, ablations, exemples d’erreurs, limites (géoloc, biais sources).
10. (Optionnel) **Qdrant** + `/similar`.

---

## 17. Livrables Phase 2

- Pipeline reproductible (`pipelines/` + notebooks d’exploration seulement).
- **`config/config.yaml`** + `.env.example` (sans secrets).
- Artefacts : modèle versionné, **`manifest.json`** (versions features / schéma NLP / modèle), rapport d’évaluation.
- Suite **tests** `tests/` (§A.6).
- Service **FastAPI** minimal documenté (OpenAPI) ; modes online documentés §A.4.
- (Optionnel) Index **Qdrant** et script d’ingestion.

---

## 18. Synthèse — les trois leviers

1. **NLP / LLM** : schéma **large** + passes règles/LLM/embedding ; multilingue TN ; **robustesse** §A.7.
2. **Vision** : VLM + CLIP ; agrégation ; **pas de promesse de m² exact** depuis photo seule.
3. **ML + XAI + LLM** : LightGBM, SHAP, explication contrôlée ; **confiance** et **opportunités** calibrées.

**Transversal** : **Partie A** (config YAML, arborescence, multi-LLM, modes online/offline, versioning, tests, **anti-fuite** target encoding) conditionne une exécution **reproductible** et non improvisée.

---

*Document **Phase 2 FINAL** — à utiliser comme référence unique pour la réalisation.*
