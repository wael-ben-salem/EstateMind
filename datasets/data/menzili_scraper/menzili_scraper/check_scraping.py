#!/usr/bin/env python
"""
Script pour vérifier qu'on a bien scrappé toutes les annonces
"""
import json
import requests
from bs4 import BeautifulSoup
import re

def check_total_annonces():
    """
    Va chercher le nombre total d'annonces directement sur le site
    """
    url = "https://www.menzili.tn/immo/vente-immobilier-tunisie?tri=1"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher le texte avec le nombre d'annonces
        h1_text = soup.find('h1')
        if h1_text:
            match = re.search(r'(\d+)\s*annonce', h1_text.text)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"Erreur: {e}")
    
    return None

def verify_scraped_data():
    """
    Vérifie les données scrappées
    """
    print("🔍 VÉRIFICATION DES DONNÉES SCRAPPÉES")
    print("="*60)
    
    # Lire le fichier JSON
    try:
        with open('menzili_annonces.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Annonces dans le fichier: {len(data)}")
        
        # Vérifier le site
        total_site = check_total_annonces()
        if total_site:
            print(f"🌐 Annonces sur le site: {total_site}")
            
            if len(data) == total_site:
                print("✅ SUCCÈS: Toutes les annonces sont présentes!")
            else:
                diff = total_site - len(data)
                print(f"⚠️ Attention: Il manque {diff} annonces")
        
        # Statistiques sur les données
        stats = {
            'avec_prix': 0,
            'avec_description': 0,
            'avec_images': 0,
            'premium': 0,
            'pro': 0
        }
        
        for annonce in data:
            if annonce.get('prix'):
                stats['avec_prix'] += 1
            if annonce.get('description'):
                stats['avec_description'] += 1
            if annonce.get('images_urls'):
                stats['avec_images'] += len(annonce['images_urls'])
            if annonce.get('est_premium'):
                stats['premium'] += 1
            if annonce.get('vendeur_type') == 'PRO':
                stats['pro'] += 1
        
        print("\n📈 QUALITÉ DES DONNÉES:")
        print(f"   Annonces avec prix: {stats['avec_prix']}")
        print(f"   Annonces avec description: {stats['avec_description']}")
        print(f"   Total images: {stats['avec_images']}")
        print(f"   Annonces Premium: {stats['premium']}")
        print(f"   Annonces PRO: {stats['pro']}")
        
    except FileNotFoundError:
        print("❌ Fichier menzili_annonces.json non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    verify_scraped_data()