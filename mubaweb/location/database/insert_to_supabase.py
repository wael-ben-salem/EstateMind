"""
Script d'insertion des listings scrapés vers Supabase.
Usage:
  pip install supabase
  python insert_to_supabase.py --file ../appartement/mubawab_location_appartements_complet_xxx.json --category appartement
"""
import json
import argparse
import os
from pathlib import Path


def load_listings(filepath: str) -> list:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('listings', [])


def normalize_listing(raw: dict, category: str, source_site: str = "mubawab.tn") -> dict:
    """Convertit un listing brut vers la structure unifiée."""
    id_val = raw.get('id', '')
    if id_val and not id_val.startswith(source_site):
        id_val = f"{source_site}_{id_val}"
    
    # Parser JSON strings si nécessaire
    def parse_json_field(val):
        if isinstance(val, str) and val.startswith('{'):
            try:
                return json.loads(val)
            except:
                return {}
        return val or {}
    
    def parse_images(val):
        if isinstance(val, str):
            return [u.strip() for u in val.split(';') if u.strip() and 'mubawab-media' in u]
        return val or []
    
    type_bien = raw.get('type_appartement') or raw.get('type_villa') or raw.get('type_maison') or raw.get('type_bureau') or raw.get('type_local') or ''
    
    localisation = parse_json_field(raw.get('localisation', {}))
    
    row = {
        'id': id_val or f"{source_site}_{hash(str(raw.get('url','')))}",
        'source_site': source_site,
        'source_url': raw.get('url'),
        'property_category': category,
        'titre': raw.get('titre'),
        'region': raw.get('region'),
        'ville': raw.get('ville'),
        'quartier': raw.get('quartier'),
        'adresse': raw.get('adresse'),
        'latitude': float(localisation.get('latitude')) if localisation.get('latitude') else None,
        'longitude': float(localisation.get('longitude')) if localisation.get('longitude') else None,
        'type_bien': type_bien,
        'loyer': float(raw.get('loyer', 0) or 0),
        'loyer_text': raw.get('loyer_text'),
        'loyer_m2': float(raw.get('loyer_m2', 0) or 0),
        'surface': float(raw.get('surface', 0) or 0),
        'surface_terrain': float(raw.get('surface_terrain', 0) or 0),
        'nombre_pieces': int(raw.get('nombre_pieces', 0) or raw.get('nombre_bureaux', 0) or 0),
        'nombre_chambres': int(raw.get('nombre_chambres', 0) or 0),
        'nombre_sdb': int(raw.get('nombre_sdb', 0) or 0),
        'etage': raw.get('etage'),
        'description_courte': raw.get('description_courte'),
        'description_complete': raw.get('description_complete'),
        'equipements': raw.get('equipements') if isinstance(raw.get('equipements'), list) else [],
        'images': parse_images(raw.get('images')),
        'meuble': bool(raw.get('meuble', False)),
        'charges_incluses': raw.get('charges_incluses') if isinstance(raw.get('charges_incluses'), bool) else None,
        'caution': raw.get('caution'),
        'conditions_location': parse_json_field(raw.get('conditions_location')),
        'contact_info': parse_json_field(raw.get('contact_info')),
        'caracteristiques': parse_json_field(raw.get('caracteristiques')),
        'informations_supplementaires': parse_json_field(raw.get('informations_supplementaires')),
        'date_scraping': raw.get('date_scraping'),
    }
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', required=True, help='Chemin du fichier JSON')
    parser.add_argument('--category', '-c', required=True,
                        choices=['appartement', 'bureaux', 'locaux_com', 'maisons', 'villas'])
    parser.add_argument('--source', '-s', default='mubawab.tn')
    parser.add_argument('--limit', '-l', type=int, default=0, help='Limite le nombre d\'insertions (0=illimité)')
    parser.add_argument('--dry-run', action='store_true', help='Affiche sans insérer')
    args = parser.parse_args()
    
    listings = load_listings(args.file)
    if args.limit:
        listings = listings[:args.limit]
    
    rows = [normalize_listing(l, args.category, args.source) for l in listings]
    
    if args.dry_run:
        print(f"Dry-run: {len(rows)} lignes à insérer")
        print("Exemple:", json.dumps(rows[0], indent=2, ensure_ascii=False)[:500])
        return
    
    try:
        from supabase import create_client
    except ImportError:
        print("Installez supabase: pip install supabase")
        return
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        print("Configurez SUPABASE_URL et SUPABASE_KEY (variables d'environnement)")
        print("Exemple: export SUPABASE_URL=https://xxx.supabase.co SUPABASE_KEY=eyJ...")
        return
    
    client = create_client(url, key)
    
    # Insertion par lots (Supabase limite ~1000 par requête)
    batch_size = 100
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        try:
            client.table('location_listings').upsert(batch, on_conflict='id').execute()
            total += len(batch)
            print(f"Inserté: {total}/{len(rows)}")
        except Exception as e:
            print(f"Erreur lot {i//batch_size}: {e}")
    
    print(f"Terminé: {total} listings insérés.")


if __name__ == '__main__':
    main()
