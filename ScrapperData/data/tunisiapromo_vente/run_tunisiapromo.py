#!/usr/bin/env python
"""
Script principal pour exécuter le scraper Tunisiapromo Vente
"""
import os
import sys
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == "__main__":
    print("="*60)
    print("🚀 DÉMARRAGE DU SCRAPER TUNISIAPROMO VENTE")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl('vente')
    process.start()

    print("\n" + "="*60)
    print("✅ SCRAPING TUNISIAPROMO VENTE TERMINÉ")
    print("📊 Fichiers générés:")
    print("   - tunisiapromo_vente.json")
    print("   - tunisiapromo_vente.csv")
    print("   - tunisiapromo_stats.json")
    print("="*60)