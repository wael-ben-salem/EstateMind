# 🧾 EstateMind – Contract Scanner Agent
## ⚖️ Intelligent Legal Contract Validator (Tunisia-focused)

---

## 🎯 Objectif du document

Ce document constitue le **cahier des charges complet** pour la conception, le développement et l’évolution de l’agent d’analyse de contrats immobiliers.

Il est destiné à :
- Développeurs
- Data scientists
- Product managers
- Éventuels investisseurs / incubateurs

---

## 📌 Table des matières

1. [Contexte et problème métier](#1-contexte-et-problème-métier)
2. [Objectifs de l’agent](#2-objectifs-de-lagent)
3. [Architecture globale](#3-architecture-globale)
4. [Choix techniques détaillés et justifiés](#4-choix-techniques-détaillés-et-justifiés)
5. [Pipeline détaillé](#5-pipeline-détaillé)
6. [Format de sortie (JSON + Markdown)](#6-format-de-sortie-json--markdown)
7. [Innovations clés](#7-innovations-clés)
8. [Améliorations critiques (robustesse)](#8-améliorations-critiques-robustesse)
9. [Fonctionnalités avancées (niveau produit)](#9-fonctionnalités-avancées-niveau-produit)
10. [Exemple de prompt LLM](#10-exemple-de-prompt-llm)
11. [Structure du notebook Jupyter](#11-structure-du-notebook-jupyter)
12. [Fonctions métier](#12-fonctions-métier)
13. [Tests et validation (KPI détaillés)](#13-tests-et-validation-kpi-détaillés)
14. [Livrables](#14-livrables)
15. [Roadmap produit](#15-roadmap-produit)

---

## 1. 🧠 Contexte et problème métier

### 1.1 Contexte

En Tunisie, les contrats immobiliers sont souvent :
- Rédigés sans expertise juridique
- Copiés depuis des modèles génériques
- Incomplets ou déséquilibrés
- Non relus par un professionnel (coût élevé : 200-500 DT par contrat)

### 1.2 Risques majeurs

Les utilisateurs s’exposent à :
- Clauses abusives non détectées
- Absence de garanties essentielles (garantie décennale, conditions suspensives)
- Vices cachés non couverts
- Litiges longs et coûteux (2 à 5 ans en moyenne)

### 1.3 Solution proposée

Un agent IA capable de :
- Analyser automatiquement un contrat (PDF, DOCX, image)
- Identifier les risques avec extraction précise
- Expliquer chaque problème en langage clair
- Proposer des corrections conformes au droit tunisien
- Générer un score de risque global (0 à 1)

---

## 2. 🎯 Objectifs de l’agent

### 2.1 Objectifs métier

| Objectif | Cible |
|----------|-------|
| Détection de risques | > 85% |
| Temps d’analyse | < 15 secondes (10 pages) |
| Accessibilité | Interface simple (fichier → rapport) |
| Adaptation locale | Référence au Code des Obligations et des Contrats tunisien |

### 2.2 Objectifs techniques

| Objectif | Description |
|----------|-------------|
| Support multi-format | PDF (texte + scanné), DOCX, JPEG, PNG |
| Multilingue | Français et arabe |
| Explicabilité forte | Chaque risque cite l'extrait exact du contrat |
| Exécution locale | Confidentialité totale (aucune donnée quitte la machine) |
| Performance | Tourne sur CPU (16 Go RAM suffisant) |

### 2.3 Objectifs data science

- Extraction robuste via OCR performant
- Détection sémantique (pas uniquement par mots-clés)
- Scoring intelligent pondéré par type de contrat
- Recommandations exploitables et actionnables

---

## 3. 🏗️ Architecture globale
Input Contract (PDF/DOCX/JPEG/PNG)
↓
Validation (format, taille)
↓
Text Extraction (OCR si PDF scanné ou image)
↓
Cleaning & Normalisation (suppression entêtes, bruit)
↓
Language Detection (français / arabe)
↓
Clause Segmentation (découpage intelligent)
↓
Embeddings (BGE-small)
↓
Semantic Matching (comparaison avec clauses de référence)
↓
Hybrid Analysis (Règles déterministes + LLM Mixtral)
↓
Risk Scoring (pondéré par type contrat)
↓
Report Generation (Markdown + JSON)
↓
Cache (hash MD5 du fichier)

text

---

## 4. ⚙️ Choix techniques détaillés et justifiés

### 4.1 LLM : Mixtral 8x7B (via Ollama)

**Pourquoi Mixtral plutôt que GPT-4 ou LLaMA ?**

| Critère | Mixtral 8x7B | GPT-4 | LLaMA 7B |
|---------|--------------|-------|----------|
| Open source | ✅ | ❌ | ✅ |
| Confidentialité (local) | ✅ | ❌ | ✅ |
| Performance juridique FR | Très bon | Excellent | Moyen |
| Taille mémoire | 47 GB | N/A | 13 GB |
| Vitesse inférence | Rapide | Lent (API) | Rapide |
| Coût | 0€ | ~0.03$/1k tokens | 0€ |

**Décision :** Mixtral offre le meilleur compromis qualité / confidentialité / coût.

**Pourquoi Ollama ?**
- Gestion simplifiée des modèles (une commande pour télécharger)
- API locale REST (http://localhost:11434)
- Pas de dépendance cloud

### 4.2 OCR : PaddleOCR

**Pourquoi PaddleOCR plutôt que Tesseract ?**

| Critère | PaddleOCR | Tesseract |
|---------|-----------|-----------|
| Support arabe natif | ✅ | ❌ (paramétrage complexe) |
| Support français | ✅ | ✅ |
| Précision PDF scanné | 92% | 78% |
| Détection de layout | ✅ (titres, paragraphes) | ❌ |
| Maintenance | Active | Stable mais peu évolutive |

**Décision :** PaddleOCR indispensable pour les contrats tunisiens souvent bilingues (arabe/français).

### 4.3 Embeddings : BGE-small-fr

**Pourquoi BGE-small plutôt que d'autres modèles ?**

| Modèle | Dimension | Temps CPU (1000 clauses) | Score MTEB France |
|--------|-----------|--------------------------|-------------------|
| BGE-small-fr | 384 | 0.02s | 58.2 |
| BGE-large-fr | 1024 | 0.08s | 61.5 |
| OpenAI ada | 1536 | 0.15s (API) | 62.1 |
| CamemBERT | 768 | 0.06s | 57.8 |

**Décision :** BGE-small-fr car :
- Suffisamment performant pour la similarité de clauses (58.2)
- Très rapide sur CPU
- Open source et local
- Spécifiquement entraîné pour le français

### 4.4 Stockage : Local JSON (Phase 1)

**Pourquoi cette approche ?**
- Simplicité d'implémentation
- Pas d'infrastructure supplémentaire
- Suffisant pour un agent autonome
- Migration facile vers PostgreSQL en Phase 2

### 4.5 Vector Database : Qdrant (Phase 2)

**Pourquoi Qdrant plutôt que Pinecone ou Weaviate ?**
- Open source et auto-hébergeable
- Support natif du filtrage par métadonnées (type contrat, date)
- Interface REST simple
- Performant sur CPU

### 4.6 Cache : dictionnaire Python avec hash MD5

**Principe :**
- Hash MD5 du fichier = clé unique
- Stockage en mémoire (dictionnaire)
- Si même contrat analysé deux fois → retour instantané
- Économie de temps et d'appels LLM

---

## 5. 🔄 Pipeline détaillé

### Étape 1 : Upload
Fichier utilisateur (localement ou via API)

### Étape 2 : Validation
- Vérifier l'extension (`.pdf`, `.docx`, `.jpg`, `.png`, `.jpeg`)
- Vérifier la taille (< 20 Mo)

### Étape 3 : Extraction texte
- **PDF texte** : extraction directe (PyPDF2)
- **PDF scanné** : conversion en images → PaddleOCR
- **DOCX** : lecture des paragraphes (python-docx)
- **Image** : PaddleOCR direct

### Étape 4 : Nettoyage
- Supprimer les répétitions de "Page X"
- Supprimer les lignes vides multiples
- Normaliser les espaces
- Supprimer les entêtes/pieds de page récurrents

### Étape 5 : Détection langue
- Analyser les 500 premiers caractères (langdetect)
- Défaut = français

### Étape 6 : Segmentation en clauses
- Chercher les motifs : "Article X", "Clause X", "X.", "–"
- Détection sémantique (si regex échoue)
- Fallback : garder le texte entier comme une clause

### Étape 7 : Embedding
- Chaque clause est transformée en vecteur (384 dimensions)

### Étape 8 : Similarité sémantique
- Comparer chaque clause avec une base de référence (clauses standards)
- Garder les 2-3 plus similaires avec leur score

### Étape 9 : Analyse hybride (Règles + LLM)
- **Règles déterministes** : absence de signature, délai nul, montant manquant
- **LLM** : interprétation fine des clauses complexes

### Étape 10 : Scoring pondéré
- Chaque clause : score (faible=0.2, moyen=0.5, élevé=0.9)
- Pondération selon type contrat (vente vs location)
- Score global = moyenne pondérée

### Étape 11 : Génération rapport
- **Markdown** : lisible par un humain
- **JSON** : exploitable par une machine

### Étape 12 : Cache
- Calculer hash MD5 du fichier original
- Stocker le résultat dans un dictionnaire

---

## 6. 📤 Format de sortie (JSON + Markdown)

### 6.1 Format JSON

```json
{
  "contract_id": "a3f5c2e8d1b4a7c9e5f2d4b6a8c1e3f5",
  "filename": "contrat_vente_tunis.pdf",
  "contract_type": "vente",
  "language": "fr",
  "risk_score": 0.35,
  "compliance_percent": 78.5,
  "num_clauses": 12,
  "missing_clauses": [
    "Garantie décennale",
    "Conditions suspensives de prêt"
  ],
  "risky_clauses": [
    {
      "clause_num": 3,
      "extrait": "Le vendeur décline toute responsabilité après la livraison",
      "risk_level": "élevé",
      "suggestion": "Ajouter : 'Le vendeur garantit le bien contre tous vices cachés pendant 10 ans conformément à l'article 1792 du Code civil'",
      "explanation": "La garantie décennale est obligatoire en Tunisie pour les vices cachés"
    }
  ],
  "contradictions": [],
  "summary": "Contrat à risque modéré. Absence de garantie décennale critique.",
  "recommendation": "Faire modifier la clause 3 avant signature",
  "timestamp": "2025-01-15T14:30:00Z"
}
6.2 Format Markdown (rapport humain)
markdown
# Rapport d'analyse contractuelle

**Fichier** : contrat_vente_tunis.pdf  
**Type** : Vente  
**Date** : 2025-01-15 14:30:00  

## 📊 Score global
- **Risque** : 35%  
- **Conformité** : 78.5%  

## ⚠️ Clauses à risque

### Clause 3 (Risque élevé)
**Extrait** : "Le vendeur décline toute responsabilité après la livraison"  
**Problème** : Absence de garantie décennale  
**Suggestion** : Ajouter la garantie légale obligatoire  

## 📝 Résumé
Contrat à risque modéré. Absence de garantie décennale critique.

## 🔧 Recommandations
- Faire modifier la clause 3 avant signature
- Consulter un avocat pour les conditions suspensives
7. 💡 Innovations clés
7.1 Similarité sémantique (pas de mots-clés)
Au lieu de chercher "garantie décennale" exacte, l'agent cherche des concepts proches : "assurance décennale", "garantie 10 ans", "couverture constructeur".
Avantage : robuste face aux variations de rédaction.

7.2 Score dynamique pondéré
Chaque clause a un poids différent selon le type de contrat :

Vente : garantie décennale = 40% du score

Location : dépôt de garantie = 30% du score
Avantage : le score reflète la criticité réelle.

7.3 Explicabilité intégrée
Pour chaque risque, l'agent retourne :

La clause concernée

L'extrait exact du contrat

Une suggestion de reformulation

Un niveau de risque (faible/moyen/élevé)
Avantage : l'utilisateur comprend pourquoi et quoi modifier.

7.4 Détection de contradictions
L'agent identifie si deux clauses se contredisent (ex: "livraison 30 jours" vs "livraison 6 mois").
Avantage : évite les contrats incohérents.

7.5 Mode simple / expert
Simple : résumé + score + recommandations principales

Expert : analyse clause par clause avec citations complètes
Avantage : adapté aux profils utilisateurs (particulier vs avocat).

7.6 Cache intelligent par hash
Même contrat analysé deux fois → retour instantané du résultat précédent.
Avantage : gain de temps et d'appels LLM.

7.7 Anonymisation automatique (optionnelle)
Avant analyse, l'agent peut remplacer noms, adresses et montants par des variables.
Avantage : confidentialité renforcée.

8. ⚠️ Améliorations critiques (robustesse)
8.1 Hybrid AI (RÈGLES + LLM)
Essentiel pour la fiabilité

Exemples de règles déterministes :

Absence de signature → critique automatique

Délai de livraison nul ou négatif → critique

Montant manquant → critique

Date antérieure à aujourd'hui → anomalie

8.2 Segmentation intelligente
Détection par regex (Article X, Clause X)

Fallback sémantique (embedding + clustering)

Fallback OCR layout (si PaddleOCR détecte des blocs)

8.3 Score évolutif
Ajustable par l'utilisateur (seuils personnalisables)

Potentiellement apprenant (feedback → ajustement pondérations)

8.4 Gestion des erreurs LLM
Si Mixtral ne répond pas en JSON → retry avec prompt plus simple

Si échec persistant → fallback sur règles uniquement

Logging des erreurs pour amélioration

9. 🚀 Fonctionnalités avancées (niveau produit)
9.1 Legal Copilot (chat avec contrat)
L'utilisateur peut poser des questions en langage naturel :

"Explique cette clause"

"Est-ce que ce contrat est risqué pour l'acheteur ?"

"Que dit la loi tunisienne sur les vices cachés ?"

9.2 Simulation de litige 🔥
L'agent explique les conséquences réelles en cas de problème :

"Si vous signez sans garantie décennale et qu'un vice apparaît dans 2 ans, vous devrez payer vous-même les réparations (environ 20 000 DT)."

9.3 Génération de contrat corrigé 🔥
L'agent produit une version optimisée du contrat avec :

Clauses manquantes ajoutées

Clauses risquées reformulées

Version avant/après

9.4 Benchmark
Comparaison avec d'autres contrats :

"Ce contrat est plus risqué que 70% des contrats analysés"

9.5 Détection de déséquilibre
Analyse de la répartition des obligations entre les parties :

"Ce contrat est très déséquilibré : 80% des obligations pèsent sur l'acheteur"

9.6 Timeline contractuelle
Extraction et visualisation des dates clés et obligations :

Date de signature

Date de livraison

Date de paiement

Période de garantie

9.7 Risk Heatmap
Visualisation par couleur :

🔴 Critique (score > 0.7)

🟠 Moyen (0.4 - 0.7)

🟢 Faible (< 0.4)

9.8 Mode négociation
Conseils pour la négociation :

"Proposez d'ajouter une garantie décennale : cela réduirait le risque de 40% à 15%"

9.9 Comparaison de versions
Avant / après modification :

Affichage des différences

Évolution du score de risque

9.10 Mode batch
Analyser plusieurs contrats d'un coup (dossier) :

Tableau comparatif des scores

Classement par risque

Rapport de synthèse

10. 🧪 Exemple de prompt LLM
Voici le prompt exact qui sera envoyé à Mixtral pour chaque clause :

text
Tu es un expert juridique spécialisé en droit immobilier tunisien (Code des Obligations et des Contrats).

Type de contrat : vente

Clause à analyser :
"""
{clause_extraite}
"""

Clauses de référence (bonnes pratiques) :
- {clause_similaire_1}
- {clause_similaire_2}

Instructions :
1. Vérifie si la clause respecte les standards légaux tunisiens
2. Identifie les risques potentiels
3. Propose une reformulation si nécessaire

Réponds STRICTEMENT au format JSON suivant :
{
  "is_valid": true/false,
  "risk_level": "faible/moyen/élevé",
  "missing_elements": ["élément1", "élément2"],
  "suggestion": "reformulation proposée",
  "explanation": "justification courte (max 50 mots)"
}

Ne réponds que ce JSON, rien d'autre.
11. 📓 Structure du notebook Jupyter
Le notebook contract_scanner_agent.ipynb contiendra 10 sections :

Section 1 : Installation des dépendances
bash
pip install paddlepaddle paddleocr pypdf2 python-docx sentence-transformers ollama langdetect pandas numpy pdf2image pillow
Section 2 : Import des librairies
Tous les imports nécessaires

Section 3 : Configuration initiale
Initialisation OCR (PaddleOCR)

Chargement embeddings (BGE-small)

Cache (dictionnaire)

Base de référence des clauses standards

Pondérations des risques

Section 4 : Extraction texte
Fonctions pour chaque format (PDF texte, PDF scanné, DOCX, image)

Section 5 : Prétraitement et découpage
Nettoyage, détection langue, segmentation en clauses

Section 6 : Embedding et similarité
Vectorisation et recherche de clauses similaires

Section 7 : Appel LLM (Mixtral)
Construction du prompt, appel Ollama, parsing JSON

Section 8 : Calcul du score de risque
Pondération selon type contrat

Section 9 : Pipeline complet
Fonction orchestrant toutes les étapes

Section 10 : Exemple et visualisation
Test sur contrat exemple, affichage rapport, graphique radar

12. 🔧 Fonctions métier
Fonction	Rôle	Entrée	Sortie
extract_text	Extraction brute multi-format	Chemin fichier	(texte, type_fichier)
clean_text	Nettoyage du texte	Texte brut	Texte nettoyé
detect_language	Détection langue	Texte	"fr", "ar", "en"
split_into_clauses	Segmentation intelligente	Texte	Liste de clauses
embed_clause	Vectorisation	Clause	Vecteur (384 dim)
find_similar_clauses	Matching sémantique	Clause + base ref	Liste (clause, score)
build_prompt	Construction prompt	Clause + similar	Prompt string
analyze_clause_with_llm	Appel Mixtral	Clause	JSON d'analyse
compute_risk_score	Scoring global	Analyses clauses	Score (0-1)
analyze_contract	Pipeline complet	Fichier + type	Rapport (JSON + MD)
visualize_risk	Graphique radar	Rapport	Figure matplotlib
13. 🧪 Tests et validation (KPI détaillés)
13.1 Contrats de test (3 cas minimaux)
Contrat	Type	Caractéristique	Risque attendu
Contrat A	Vente	Complet (prix, livraison, garantie décennale, description)	Faible (~0.2)
Contrat B	Vente	Sans garantie, sans délai de livraison	Élevé (>0.7)
Contrat C	Location	Durée absente, dépôt non mentionné	Moyen (~0.6)
13.2 KPI de succès
KPI	Cible	Comment mesurer
Précision détection clauses manquantes	> 85%	Comparaison avec expert humain sur 50 contrats
Temps d'analyse (10 pages)	< 15 secondes	Chronométrage sur machine standard (16 Go RAM, CPU)
Taux de JSON valide (bien formé)	> 95%	Parsing automatique sur 100 analyses
Corrélation score avec expert	> 0.8	Coefficient de corrélation de Pearson
Cache fonctionnel	100%	Même contrat → retour < 1s
Support formats	100%	PDF, DOCX, JPG, PNG fonctionnels
13.3 Commandes de validation
bash
# Vérifier que Mixtral est disponible
ollama list | grep mixtral

# Tester l'OCR sur un PDF scanné
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(); print('OCR OK')"

# Exécuter le notebook complet
jupyter nbconvert --to notebook --execute contract_scanner_agent.ipynb
14. 📦 Livrables
Fichier	Description	Format
contract_scanner_agent.ipynb	Notebook complet avec toutes les sections	Jupyter (.ipynb)
contract_scanner_agent.py	Version script Python (exporté)	Python (.py)
requirements.txt	Liste des dépendances avec versions	Texte
README_AGENT4.md	Ce guide complet	Markdown
sample_contracts/	Dossier avec 3 contrats exemple (vente, location, scanné)	PDF/DOCX
requirements.txt (exemple)
text
paddlepaddle>=2.5.0
paddleocr>=2.7.0
pypdf2>=3.0.0
python-docx>=0.8.11
sentence-transformers>=2.2.0
ollama>=0.1.0
langdetect>=1.0.9
pandas>=2.0.0
numpy>=1.24.0
pdf2image>=1.16.0
pillow>=10.0.0
matplotlib>=3.7.0
15. 🛣️ Roadmap produit
Phase 1 (2-3 semaines) - Agent local fonctionnel
Notebook Jupyter complet

Support PDF, DOCX, images

OCR fonctionnel (PaddleOCR)

Appel Mixtral via Ollama

Scoring et rapport Markdown

Phase 2 (2 semaines) - API + Base données
Exposition via FastAPI (endpoint /analyze-contract)

Stockage PostgreSQL (rapports)

Vector DB Qdrant (RAG juridique)

Cache Redis

Phase 3 (3 semaines) - Interface web + Chatbot
Interface utilisateur (Streamlit ou React)

Legal Copilot (chat avec contrat)

Visualisation heatmap

Mode batch

Phase 4 (1 mois) - SaaS
Authentification multi-utilisateurs

Dashboard personnel

Historique des analyses

Paiement (Stripe)

Phase 5 (continu) - Startup / Data moat
Apprentissage continu (feedback utilisateur)

Dataset propriétaire de contrats tunisiens

Benchmark marché (comparaison concurrents)

Fine-tuning Mixtral sur données annotées

✅ Conclusion
EstateMind Contract Scanner est :

✔ Un outil IA concret répondant à un problème réel

✔ Basé sur des choix techniques justifiés (Mixtral, BGE-small, PaddleOCR)

✔ Innovant (similarité sémantique, score pondéré, explicabilité)

✔ Robust (hybrid rules + LLM, cache, fallbacks)

✔ Extensible vers un produit SaaS avec roadmap claire

Prochaine action immédiate : Développer le notebook Jupyter selon la structure définie en section 11.

Fin du cahier des charges – Prêt pour implémentation 🚀

text

---

Ce fichier fusionné contient **tout** :
- La structure pro et la roadmap de ton fichier
- Les justifications techniques détaillées
- Le format JSON, le prompt LLM, le cache, les KPI précis
- Les exemples concrets

Tu peux le sauvegarder comme `README_AGENT4_COMPLET.md` et l'utiliser comme **document unique de référence** pour toute la phase Contract Scanner.


////////////////////////////////////////////////////////

Les éléments QUI MANQUENT encore (importants)
🔴 2.1 Sécurité & conformité (TRÈS important en legal)

👉 Tu n’en parles presque pas, et c’est critique.

➜ Ajoute une section :
16. 🔐 Sécurité et confidentialité

Contenu à ajouter :

Données sensibles (contrats, noms, montants)
Traitement 100% local (aucun envoi cloud)
Option anonymisation activable
Logs sans données personnelles
Hash des fichiers (pas stockage brut obligatoire)
Conformité RGPD-like (même si Tunisie)

👉 Ça rassure énormément :

clients
profs
recruteurs
🟠 2.2 Limitations du système (TRÈS pro)

👉 Un vrai produit doit reconnaître ses limites.

➜ Ajoute :
17. ⚠️ Limitations connues

Ex :

OCR peut échouer sur documents de mauvaise qualité
LLM peut générer des erreurs (hallucinations)
Ne remplace pas un avocat
Base juridique limitée (pas toutes lois tunisiennes)
Performance dépend de la qualité du texte

👉 Ça donne une image honnête et crédible

🟡 2.3 Monitoring & logging (niveau pro)

👉 Tu as des KPI mais pas de monitoring runtime.

➜ Ajoute :
18. 📊 Monitoring et logging
Temps par étape (OCR, LLM, total)
Taux d’erreur LLM
Taux de fallback (rules only)
Logs des anomalies
Suivi des performances

👉 Utile pour debug + scale

🟢 2.4 UX / Output utilisateur (petit mais important)

👉 Tu as JSON + Markdown, mais pas UX final.

Ajoute :

téléchargement PDF du rapport
résumé “1 page”
indicateur visuel clair (score + couleur)
🔵 2.5 Versioning / évolution modèle

👉 Très important si tu veux faire du SaaS.

➜ Ajoute :
19. 🔄 Versioning
version du modèle LLM
version des règles
version du scoring

👉 permet :

reproductibilité
audit
🚀 3. Les 3 ajouts qui vont te faire passer en MODE EXPERT

Si tu ajoutes juste ça → ton projet devient exceptionnel

💡 3.1 Confidence score (🔥 très important)

Ajoute dans JSON :

"confidence_score": 0.87

👉 basé sur :

qualité OCR
similarité embeddings
cohérence LLM

👉 Ça change tout en pratique

💡 3.2 Classification du type de contrat (auto)

Aujourd’hui :

type = donné

👉 Amélioration :

classification automatique :
vente
location
mixte

👉 utile si utilisateur ne sait pas

💡 3.3 “Critical blocking issues”

👉 Ajoute :

"blocking_issues": [
  "Absence de signature",
  "Absence de prix"
]

👉 différent de “risk”
→ ce sont des erreurs non négociables

🧠 4. Petit détail technique à corriger
❗ Dans ton JSON exemple :
"article 1792 du Code civil"

👉 ⚠️ En Tunisie → c’est plutôt :

Code des Obligations et des Contrats (COC)

👉 Corrige pour crédibilité juridique