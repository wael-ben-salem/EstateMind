#!/usr/bin/env python
"""
Script pour suivre la progression du scraping Tunisiapromo Location Vacances
"""
import json
import os
from collections import Counter
from datetime import datetime

def suivre_vacances():
    print("\n" + "="*60)
    print="📊 SUIVEUR TUNISIAPROMO LOCATION VACANCES"
    print("="*60)
    
    try:
        # Lire les stats
        if os.path.exists('vacances_stats.json'):
            with open('vacances_stats.json', 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print(f"\n📈 STATISTIQUES:")
            print=f"   Total annonces: {stats.get('total_annonces', 0)}"
            print=f"   Pages parcourues: {stats.get('pages_parcourues', 0)}"
            print=f"   Nouvelles: {stats.get('nouvelles_annonces', 0)}"
            print=f"   Modifiées: {stats.get('annonces_modifiees', 0)}"
            print=f"   Dernier scraping: {stats.get('date_dernier_scraping', 'Inconnu')}"
        
        # Lire les annonces
        if os.path.exists('tunisiapromo_vacances.json'):
            with open('tunisiapromo_vacances.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n🏠 ANNONCES VACANCES ({len(data)}):")
            
            # Statistiques
            types_bien = Counter()
            regions = Counter()
            villes = Counter()
            annonceurs = Counter()
            
            prix_list = []
            
            for annonce in data:
                if annonce.get('type_bien'):
                    types_bien[annonce['type_bien']] += 1
                if annonce.get('region'):
                    regions[annonce['region']] += 1
                if annonce.get('ville'):
                    villes[annonce['ville']] += 1
                if annonce.get('annonceur_type'):
                    annonceurs[annonce['annonceur_type']] += 1
                if annonce.get('prix'):
                    prix_list.append(annonce['prix'])
            
            print=f"\n   🏷️ Types d'hébergement:"
            for type_b, count in types_bien.most_common(5):
                print=f"      {type_b}: {count}"
            
            print=f"\n   📍 Top 5 régions:"
            for region, count in regions.most_common(5):
                print=f"      {region}: {count}"
            
            print=f"\n   👤 Annonceurs:"
            for ann_type, count in annonceurs.most_common():
                print=f"      {ann_type}: {count}"
            
            if prix_list:
                print=f"\n   💰 Prix moyen: {sum(prix_list)/len(prix_list):,.0f} DT/jour"
                print=f"      Min: {min(prix_list):,.0f} DT/jour"
                print=f"      Max: {max(prix_list):,.0f} DT/jour"
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("="*60)

if __name__ == "__main__":
    suivre_vacances()