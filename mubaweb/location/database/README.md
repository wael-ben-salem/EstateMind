# Base de données Location

## Setup Supabase

1. Créer un projet sur [supabase.com](https://supabase.com)
2. Aller dans SQL Editor et exécuter `schema.sql`
3. Récupérer l'URL et la clé "anon" dans Settings > API

## Variables d'environnement

```bash
export SUPABASE_URL="https://votre-projet.supabase.co"
export SUPABASE_KEY="votre-cle-anon"
```

## Insertion des données

```bash
cd location/database
pip install supabase

# Dry-run (prévisualisation)
python insert_to_supabase.py -f ../appartement/mubawab_location_appartements_complet_xxx.json -c appartement --dry-run

# Insertion réelle
python insert_to_supabase.py -f ../appartement/mubawab_location_appartements_complet_xxx.json -c appartement

# Limiter à 10 pour test
python insert_to_supabase.py -f ../villas/mubawab_location_villas_complet_xxx.json -c villas -l 10
```

## Partage multi-utilisateurs

Chaque ami peut :
1. Créer son propre compte Supabase (ou utiliser le projet partagé)
2. Lancer les scrapers sur son site
3. Exécuter `insert_to_supabase.py` avec `--source` pour identifier la source
4. Remplir `scraped_by` avec son identifiant

Pour activer RLS (chaque utilisateur ne modifie que ses données), décommentez les lignes RLS dans `schema.sql`.
