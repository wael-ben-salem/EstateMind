#!/usr/bin/env python
"""
Script pour suivre la progression du scraping des locations
"""
import json
import os
from collections import Counter

def suivre_location():
    print("\n" + "="*60)
    print="📊 SUIVEUR LOCATION MENZILI.TN"
    print("="*60)
    
    try:
        # Lire les stats
        if os.path.exists('location_stats.json'):
            with open('location_stats.json', 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print(f"\n📈 STATISTIQUES LOCATION:")
            print(f"   Total annonces: {stats.get('total_annonces', 0)}")
            print(f"   Pages parcourues: {stats.get('pages_parcourues', 0)}")
            print(f"   Nouvelles locations: {stats.get('nouvelles_annonces', 0)}")
            print(f"   Dernier scraping: {stats.get('date_dernier_scraping', 'Inconnu')}")
        
        # Lire les annonces
        if os.path.exists('menzili_location.json'):
            with open('menzili_location.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n🏠 ANNONCES LOCATION ({len(data)}):")
            
            # Statistiques
            types_location = Counter()
            regions = Counter()
            
            for annonce in data:
                # Type de location (mensuel, annuel, etc.)
                if 'prix' in annonce and isinstance(annonce['prix'], dict):
                    types_location[annonce['prix'].get('periode', 'inconnu')] += 1
                if annonce.get('region'):
                    regions[annonce['region']] += 1
            
            print(f"\n   📅 Types de location:")
            for periode, count in types_location.most_common():
                print(f"      {periode}: {count}")
            
            print(f"\n   📍 Top 5 régions:")
            for region, count in regions.most_common(5):
                print(f"      {region}: {count}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("="*60)

if __name__ == "__main__":
    suivre_location()