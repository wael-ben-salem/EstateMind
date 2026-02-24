#!/usr/bin/env python
"""
Script principal pour exécuter le scraper Menzili
"""
import os
import sys
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == "__main__":
    print("="*60)
    print("🚀 DÉMARRAGE DU SCRAPER MENZILI.TN")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    # Configuration du processus
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    # Lancer le spider
    process.crawl('menzili')
    
    # Démarrer le scraping
    process.start()
    
    print("\n" + "="*60)
    print("✅ SCRAPING TERMINÉ")
    print("📊 Vérifiez les fichiers générés:")
    print("   - menzili_annonces.json")
    print("   - menzili_annonces.csv")
    print("   - scraping_stats.json")
    print("="*60)