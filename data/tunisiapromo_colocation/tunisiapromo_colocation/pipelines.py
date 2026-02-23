import json
import csv
import os
import re
from datetime import datetime

class TunisiapromoColocationPipeline:
    """Pipeline avec gestion incrémentale pour les colocations"""
    
    def __init__(self):
        self.json_file = 'tunisiapromo_colocation.json'
        self.csv_file = 'tunisiapromo_colocation.csv'
        self.stats_file = 'colocation_stats.json'
        self.existing_annonces = {}
        self.new_annonces = []
        self.updated_annonces = []
        self.stats = {
            'date_dernier_scraping': None,
            'total_annonces': 0,
            'nouvelles_annonces': 0,
            'annonces_modifiees': 0,
            'annonces_inchangees': 0,
            'pages_parcourues': 0
        }
        
        self.load_existing()
    
    def load_existing(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for annonce in data:
                        annonce_id = annonce.get('annonce_id')
                        if annonce_id:
                            self.existing_annonces[annonce_id] = annonce
                print(f"📂 {len(self.existing_annonces)} colocations existantes chargées")
            except Exception as e:
                print(f"⚠️ Erreur chargement: {e}")
    
    def process_item(self, item, spider):
        self.stats['pages_parcourues'] = spider.stats.get('pages_parcourues', 0)
        
        item_dict = dict(item)
        item_dict['date_scraping'] = datetime.now().isoformat()
        
        annonce_id = item_dict.get('annonce_id')
        
        if annonce_id in self.existing_annonces:
            existing = self.existing_annonces[annonce_id]
            if self.has_changed(existing, item_dict):
                item_dict['statut'] = 'modifié'
                self.updated_annonces.append(item_dict)
                print(f"🔄 Colocation modifiée: {annonce_id}")
            else:
                existing['statut'] = 'inchangé'
                self.updated_annonces.append(existing)
                return existing
        else:
            item_dict['statut'] = 'nouveau'
            self.new_annonces.append(item_dict)
            print(f"🆕 Nouvelle colocation: {annonce_id}")
        
        return item_dict
    
    def has_changed(self, old, new):
        fields = ['prix', 'titre', 'description']
        for field in fields:
            if old.get(field) != new.get(field):
                return True
        return False
    
    def close_spider(self, spider):
        self.stats['date_dernier_scraping'] = datetime.now().isoformat()
        self.stats['total_annonces'] = len(self.existing_annonces) + len(self.new_annonces)
        self.stats['nouvelles_annonces'] = len(self.new_annonces)
        self.stats['annonces_modifiees'] = len(self.updated_annonces)
        self.stats['annonces_inchangees'] = len(self.existing_annonces) - len(self.updated_annonces)
        
        all_annonces = []
        for annonce in self.existing_annonces.values():
            if annonce not in self.updated_annonces and annonce not in self.new_annonces:
                annonce['statut'] = 'inchangé'
                all_annonces.append(annonce)
        all_annonces.extend(self.updated_annonces)
        all_annonces.extend(self.new_annonces)
        
        self.save_json(all_annonces)
        self.save_csv(all_annonces)
        self.save_stats()
        self.print_report()
    
    def save_json(self, data):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON: {self.json_file}")
    
    def save_csv(self, data):
        if not data:
            return
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames), delimiter=';')
            writer.writeheader()
            for item in data:
                row = {}
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        row[k] = v
                writer.writerow(row)
    
    def save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
    
    def print_report(self):
        print("\n" + "="*60)
        print("📊 RAPPORT TUNISIAPROMO COLOCATION")
        print("="*60)
        print(f"📅 Date: {self.stats['date_dernier_scraping']}")
        print(f"📄 Pages: {self.stats['pages_parcourues']}")
        print(f"📂 Total colocations: {self.stats['total_annonces']}")
        print(f"🆕 Nouvelles: {self.stats['nouvelles_annonces']}")
        print(f"🔄 Modifiées: {self.stats['annonces_modifiees']}")
        print(f"✅ Inchangées: {self.stats['annonces_inchangees']}")
        print("="*60)