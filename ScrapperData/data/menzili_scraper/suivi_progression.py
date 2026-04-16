#!/usr/bin/env python
"""
Script pour suivre la progression du scraping en temps réel
"""
import json
import os
from datetime import datetime
from collections import Counter

def suivre_progression():
    """Affiche la progression du scraping"""
    
    print("\n" + "="*60)
    print("📊 SUIVEUR DE PROGRESSION MENZILI.TN")
    print("="*60)
    
    try:
        # Lire les stats
        if os.path.exists('scraping_stats.json'):
            with open('scraping_stats.json', 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print(f"\n📈 STATISTIQUES GLOBALES:")
            print(f"   Total annonces: {stats.get('total_annonces', 0)}")
            print(f"   Pages parcourues: {stats.get('pages_parcourues', 0)}")
            print(f"   Nouvelles: {stats.get('nouvelles_annonces', 0)}")
            print(f"   Modifiées: {stats.get('annonces_modifiees', 0)}")
            print(f"   Inchangées: {stats.get('annonces_inchangees', 0)}")
            print(f"   Dernier scraping: {stats.get('date_dernier_scraping', 'Inconnu')}")
        
        # Lire les annonces
        if os.path.exists('menzili_annonces.json'):
            with open('menzili_annonces.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n🏠 DÉTAIL DES ANNONCES ({len(data)}):")
            
            # Stats par statut
            stats_status = Counter()
            regions = Counter()
            categories = Counter()
            types_vendeur = Counter()
            
            for annonce in data:
                stats_status[annonce.get('statut', 'inconnu')] += 1
                if annonce.get('region'):
                    regions[annonce['region']] += 1
                if annonce.get('categorie'):
                    categories[annonce['categorie']] += 1
                if annonce.get('vendeur_type'):
                    types_vendeur[annonce['vendeur_type']] += 1
            
            print(f"\n   📌 Par statut:")
            for status, count in stats_status.most_common():
                print(f"      {status}: {count}")
            
            print(f"\n   📍 Top 5 régions:")
            for region, count in regions.most_common(5):
                print(f"      {region}: {count}")
            
            print(f"\n   🏷️ Top 5 catégories:")
            for cat, count in categories.most_common(5):
                print(f"      {cat}: {count}")
            
            print(f"\n   👤 Type vendeur:")
            for vtype, count in types_vendeur.most_common():
                print(f"      {vtype}: {count}")
            
            # Prix moyen
            prix_list = [a['prix'] for a in data if a.get('prix')]
            if prix_list:
                print(f"\n   💰 Prix moyen: {sum(prix_list)/len(prix_list):,.0f} DT")
                print(f"      Min: {min(prix_list):,.0f} DT")
                print(f"      Max: {max(prix_list):,.0f} DT")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("="*60)

if __name__ == "__main__":
    suivre_progression()