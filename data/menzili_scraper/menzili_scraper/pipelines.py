import json
import csv
import os
from datetime import datetime
from collections import defaultdict

class MenziliPipeline:
    """
    Pipeline qui gère la mise à jour incrémentale des données
    """
    
    def __init__(self):
        self.csv_file = 'menzili_annonces.csv'
        self.json_file = 'menzili_annonces.json'
        self.stats_file = 'scraping_stats.json'
        self.existing_annonces = {}
        self.new_annonces = []
        self.updated_annonces = []
        self.scraping_stats = {
            'date_dernier_scraping': None,
            'total_annonces': 0,
            'nouvelles_annonces': 0,
            'annonces_modifiees': 0,
            'annonces_inchangees': 0,
            'pages_parcourues': 0
        }
        
        # Charger les annonces existantes
        self.load_existing_annonces()
        
        # Charger les stats précédentes
        self.load_stats()
    
    def load_existing_annonces(self):
        """Charge les annonces existantes depuis le fichier JSON"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for annonce in data:
                        annonce_id = annonce.get('annonce_id')
                        if annonce_id:
                            self.existing_annonces[annonce_id] = annonce
                print(f"📂 {len(self.existing_annonces)} annonces existantes chargées")
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement du fichier existant: {e}")
    
    def load_stats(self):
        """Charge les statistiques précédentes"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.scraping_stats.update(json.load(f))
            except:
                pass
    
    def process_item(self, item, spider):
        """Traite chaque item"""
        
        # Ajouter les stats du spider
        if hasattr(spider, 'stats'):
            self.scraping_stats['pages_parcourues'] = spider.stats.get('pages_parcourues', 0)
        
        # Convertir l'item en dictionnaire
        item_dict = dict(item)
        item_dict['date_scraping'] = datetime.now().isoformat()
        
        annonce_id = item_dict.get('annonce_id')
        
        # Vérifier si l'annonce existe déjà
        if annonce_id in self.existing_annonces:
            existing = self.existing_annonces[annonce_id]
            
            # Comparer les données importantes
            if self.has_changed(existing, item_dict):
                item_dict['statut'] = 'modifié'
                self.updated_annonces.append(item_dict)
                print(f"🔄 Annonce modifiée: {annonce_id}")
            else:
                # Pas de changement, garder l'ancienne version
                existing['statut'] = 'inchangé'
                self.updated_annonces.append(existing)
                return existing
        else:
            item_dict['statut'] = 'nouveau'
            self.new_annonces.append(item_dict)
            print(f"🆕 Nouvelle annonce: {annonce_id}")
        
        return item_dict
    
    def has_changed(self, old, new):
        """Vérifie si une annonce a changé"""
        fields_to_check = ['prix', 'titre', 'description', 'options']
        
        for field in fields_to_check:
            if old.get(field) != new.get(field):
                return True
        return False
    
    def close_spider(self, spider):
        """Fermeture du spider"""
        
        # Mettre à jour les stats
        self.scraping_stats['date_dernier_scraping'] = datetime.now().isoformat()
        self.scraping_stats['total_annonces'] = len(self.existing_annonces) + len(self.new_annonces)
        self.scraping_stats['nouvelles_annonces'] = len(self.new_annonces)
        self.scraping_stats['annonces_modifiees'] = len(self.updated_annonces)
        self.scraping_stats['annonces_inchangees'] = len(self.existing_annonces) - len(self.updated_annonces)
        
        if hasattr(spider, 'stats'):
            self.scraping_stats['pages_parcourues'] = spider.stats.get('pages_parcourues', 0)
        
        # Fusionner toutes les annonces
        all_annonces = self.merge_all_annonces()
        
        # Sauvegarder
        self.save_json(all_annonces)
        self.save_csv(all_annonces)
        self.save_stats()
        self.print_report()
    
    def merge_all_annonces(self):
        """Fusionne toutes les annonces"""
        all_annonces = []
        
        # Ajouter les annonces existantes non modifiées
        for annonce_id, annonce in self.existing_annonces.items():
            if annonce not in self.updated_annonces and annonce not in self.new_annonces:
                annonce['statut'] = 'inchangé'
                all_annonces.append(annonce)
        
        # Ajouter les annonces mises à jour
        all_annonces.extend(self.updated_annonces)
        
        # Ajouter les nouvelles annonces
        all_annonces.extend(self.new_annonces)
        
        # Trier par date
        all_annonces.sort(
            key=lambda x: x.get('date_publication', ''), 
            reverse=True
        )
        
        return all_annonces
    
    def save_json(self, data):
        """Sauvegarde en format JSON"""
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON: {self.json_file}")
    
    def save_csv(self, data):
        """Sauvegarde en format CSV"""
        if not data:
            return
        
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for item in data:
                row = {}
                for key, value in item.items():
                    if isinstance(value, list):
                        row[key] = ', '.join(str(v) for v in value)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        print(f"💾 CSV: {self.csv_file}")
    
    def save_stats(self):
        """Sauvegarde les statistiques"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraping_stats, f, ensure_ascii=False, indent=2)
    
    def print_report(self):
        """Affiche le rapport"""
        print("\n" + "="*60)
        print("📊 RAPPORT DE SCRAPING")
        print("="*60)
        print(f"📅 Date: {self.scraping_stats['date_dernier_scraping']}")
        print(f"📄 Pages parcourues: {self.scraping_stats['pages_parcourues']}")
        print(f"📂 Total annonces: {self.scraping_stats['total_annonces']}")
        print(f"🆕 Nouvelles: {self.scraping_stats['nouvelles_annonces']}")
        print(f"🔄 Modifiées: {self.scraping_stats['annonces_modifiees']}")
        print(f"✅ Inchangées: {self.scraping_stats['annonces_inchangees']}")
        print("="*60)