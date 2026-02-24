import scrapy
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from ..items import MenziliItem

class MenziliSpider(scrapy.Spider):
    name = "menzili"
    allowed_domains = ["menzili.tn"]
    start_urls = ["https://www.menzili.tn/immo/vente-immobilier-tunisie?tri=1"]
    
    stats = {
        'pages_parcourues': 0,
        'annonces_trouvees': 0,
        'total_annonces_attendu': None,
        'total_pages_attendues': None,
        'derniere_page_avec_annonces': None,
        'pages_sans_nouvelles_annonces': 0
    }
    
    annonces_vues = set()
    
    def parse(self, response):
        """Parse la page de liste des annonces avec détection dynamique"""
        self.stats['pages_parcourues'] += 1
        
        # === DÉTECTION DYNAMIQUE DU NOMBRE TOTAL D'ANNONCES ===
        self.detect_total_annonces(response)
        
        # === DÉTECTION DU NOMBRE DE PAGES TOTAL ===
        self.detect_total_pages(response)
        
        print(f"\n📄 PAGE {self.stats['pages_parcourues']}")
        
        # Extraire les annonces
        annonces = response.css('.li-item-list')
        annonces_sur_page = len(annonces)
        print(f"   ✅ Annonces sur cette page: {annonces_sur_page}")
        
        nouvelles_annonces_page = 0
        
        for annonce in annonces:
            url_detail = annonce.css('a.li-item-list-title::attr(href)').get()
            if url_detail:
                url_detail = response.urljoin(url_detail)
                annonce_id = self.extract_annonce_id(url_detail)
                
                if annonce_id and annonce_id not in self.annonces_vues:
                    self.annonces_vues.add(annonce_id)
                    self.stats['annonces_trouvees'] += 1
                    nouvelles_annonces_page += 1
                    
                    # Mettre à jour la dernière page avec des annonces
                    self.stats['derniere_page_avec_annonces'] = self.stats['pages_parcourues']
                    
                    # Créer les données de base
                    base_data = {
                        'annonce_id': annonce_id,
                        'url': url_detail,
                        'titre': annonce.css('a.li-item-list-title::text').get(),
                        'prix': self.clean_price(annonce.css('.item-box-price::text').get()),
                        'est_premium': bool(annonce.css('.strap-premium').get()),
                        'type_annonceur': self.extract_type_annonceur(annonce),
                        'date_scraping': datetime.now().isoformat(),
                        'page_trouvee': self.stats['pages_parcourues']
                    }
                    
                    # Localisation
                    loc = annonce.css('p i.fa-map-marker + ::text').get()
                    if loc:
                        base_data['adresse_complete'] = loc.strip()
                        parts = loc.split(',')
                        if len(parts) >= 2:
                            base_data['ville'] = parts[0].strip()
                            base_data['region'] = parts[1].strip()
                    
                    # Caractéristiques
                    self.extract_caracteristiques(annonce, base_data)
                    
                    yield scrapy.Request(
                        url_detail,
                        callback=self.parse_detail,
                        meta={'base_data': base_data}
                    )
        
        # === GESTION DES PAGES SANS NOUVELLES ANNONCES ===
        if nouvelles_annonces_page == 0:
            self.stats['pages_sans_nouvelles_annonces'] += 1
            print(f"   ⚠️ Aucune nouvelle annonce sur cette page ({self.stats['pages_sans_nouvelles_annonces']} page(s) consécutive(s))")
        else:
            self.stats['pages_sans_nouvelles_annonces'] = 0
        
        # Afficher la progression
        total_connu = self.stats['total_annonces_attendu'] or '???'
        print(f"   📈 Progression: {self.stats['annonces_trouvees']}/{total_connu} (+{nouvelles_annonces_page})")
        
        # === TROUVER LA PAGE SUIVANTE ===
        next_page = self.find_next_page(response)
        
        # === DÉCISION DYNAMIQUE DE CONTINUER ===
        if self.should_continue(next_page, response.url):
            print(f"   ➡️ Page suivante: {next_page}")
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            print("\n" + "="*60)
            print("🏁 ARRÊT DU SCRAPING - RAISONS:")
            if self.stats['total_annonces_attendu'] and self.stats['annonces_trouvees'] >= self.stats['total_annonces_attendu']:
                print(f"   ✅ Toutes les annonces ont été trouvées ({self.stats['annonces_trouvees']}/{self.stats['total_annonces_attendu']})")
            elif self.stats['total_pages_attendues'] and self.stats['pages_parcourues'] >= self.stats['total_pages_attendues']:
                print(f"   ✅ Nombre total de pages atteint ({self.stats['pages_parcourues']}/{self.stats['total_pages_attendues']})")
            elif self.stats['pages_sans_nouvelles_annonces'] >= 3:
                print(f"   ⚠️ 3 pages consécutives sans nouvelles annonces")
            elif not next_page:
                print(f"   🏁 Plus de page suivante disponible")
            elif next_page == response.url:
                print(f"   🔄 Boucle détectée (même URL)")
            
            self.print_final_report()
    
    def detect_total_annonces(self, response):
        """Détecte dynamiquement le nombre total d'annonces"""
        if self.stats['total_annonces_attendu']:
            return
        
        # Méthode 1: Chercher dans le texte de la balise h1
        h1_text = response.css('h1::text').get()
        if h1_text:
            # Pattern: "Les 12345 annonce(s) trouvé(s)"
            match = re.search(r'(\d{1,})\s*annonce', h1_text, re.IGNORECASE)
            if match:
                self.stats['total_annonces_attendu'] = int(match.group(1))
                print(f"\n🎯 TOTAL ANNONCES DÉTECTÉ: {self.stats['total_annonces_attendu']}")
                return
        
        # Méthode 2: Chercher dans les métadonnées
        total_meta = response.css('meta[property="og:description"]::attr(content)').get()
        if total_meta:
            match = re.search(r'(\d{1,})\s*annonces?', total_meta, re.IGNORECASE)
            if match:
                self.stats['total_annonces_attendu'] = int(match.group(1))
                print(f"\n🎯 TOTAL ANNONCES DÉTECTÉ (meta): {self.stats['total_annonces_attendu']}")
                return
        
        # Méthode 3: Chercher dans le texte de la pagination
        pagination_text = response.css('.pagination::text').getall()
        full_text = ' '.join(pagination_text)
        match = re.search(r'sur\s*(\d{1,})\s*pages?', full_text, re.IGNORECASE)
        if match:
            # Si on trouve "sur 1361 pages", on peut estimer le total
            pages = int(match.group(1))
            annonces_par_page = len(response.css('.li-item-list'))
            if annonces_par_page > 0:
                self.stats['total_pages_attendues'] = pages
                self.stats['total_annonces_attendu'] = pages * annonces_par_page
                print(f"\n🎯 TOTAL PAGES DÉTECTÉ: {pages}")
                print(f"🎯 TOTAL ANNONCES ESTIMÉ: {self.stats['total_annonces_attendu']}")
                return
    
    def detect_total_pages(self, response):
        """Détecte dynamiquement le nombre total de pages"""
        if self.stats['total_pages_attendues']:
            return
        
        # Méthode 1: Chercher le lien vers la dernière page dans la pagination
        last_page_link = response.css('.pagination a:contains(">>")::attr(href)').get()
        if last_page_link:
            match = re.search(r'page=(\d+)', last_page_link)
            if match:
                self.stats['total_pages_attendues'] = int(match.group(1))
                print(f"\n📊 TOTAL PAGES DÉTECTÉ: {self.stats['total_pages_attendues']}")
                return
        
        # Méthode 2: Chercher le dernier numéro dans les liens de pagination
        page_links = response.css('.pagination a::text').getall()
        for link_text in page_links:
            if link_text.strip().isdigit():
                page_num = int(link_text.strip())
                if not self.stats['total_pages_attendues'] or page_num > self.stats['total_pages_attendues']:
                    self.stats['total_pages_attendues'] = page_num
        
        if self.stats['total_pages_attendues']:
            print(f"\n📊 TOTAL PAGES DÉTECTÉ (via liens): {self.stats['total_pages_attendues']}")
            return
        
        # Méthode 3: Calculer à partir du nombre total d'annonces
        if self.stats['total_annonces_attendu']:
            annonces_par_page = len(response.css('.li-item-list'))
            if annonces_par_page > 0:
                self.stats['total_pages_attendues'] = (self.stats['total_annonces_attendu'] + annonces_par_page - 1) // annonces_par_page
                print(f"\n📊 TOTAL PAGES ESTIMÉ: {self.stats['total_pages_attendues']} ({annonces_par_page} annonces/page)")
    
    def find_next_page(self, response):
        """Trouve l'URL de la page suivante avec plusieurs méthodes"""
        next_page = None
        
        # Méthode 1: Lien rel="next"
        next_page = response.css('link[rel="next"]::attr(href)').get()
        
        # Méthode 2: Lien avec le symbole ">" ou "Suivant"
        if not next_page:
            next_page = response.css('.pagination a:contains(">")::attr(href)').get()
        
        if not next_page:
            next_page = response.css('.pagination a:contains("Suivant")::attr(href)').get()
        
        # Méthode 3: Construction manuelle
        if not next_page:
            current_url = response.url
            current_page = self.get_current_page_number(response)
            
            if current_page:
                next_page_num = current_page + 1
                if 'page=' in current_url:
                    next_page = re.sub(r'page=\d+', f'page={next_page_num}', current_url)
                else:
                    if '?' in current_url:
                        next_page = current_url + f'&page={next_page_num}'
                    else:
                        next_page = current_url + f'?page={next_page_num}'
        
        return next_page
    
    def get_current_page_number(self, response):
        """Extrait le numéro de la page courante"""
        # Méthode 1: Depuis l'URL
        match = re.search(r'page=(\d+)', response.url)
        if match:
            return int(match.group(1))
        
        # Méthode 2: Depuis la pagination (page active)
        active_page = response.css('.pagination .pag-activated::text').get()
        if active_page and active_page.strip().isdigit():
            return int(active_page.strip())
        
        return 1  # Page par défaut
    
    def should_continue(self, next_page, current_url):
        """Décide dynamiquement si on doit continuer le scraping"""
        
        # Critère 1: Pas de page suivante
        if not next_page:
            return False
        
        # Critère 2: Boucle infinie
        if next_page == current_url:
            return False
        
        # Critère 3: Nombre total d'annonces atteint
        if self.stats['total_annonces_attendu'] and self.stats['annonces_trouvees'] >= self.stats['total_annonces_attendu']:
            return False
        
        # Critère 4: Nombre total de pages atteint
        if self.stats['total_pages_attendues'] and self.stats['pages_parcourues'] >= self.stats['total_pages_attendues']:
            return False
        
        # Critère 5: Pages sans nouvelles annonces (pour détecter la fin)
        if self.stats['pages_sans_nouvelles_annonces'] >= 3:
            return False
        
        # Critère 6: Si on a dépassé de loin l'estimation (sécurité)
        if self.stats['total_pages_attendues'] and self.stats['pages_parcourues'] > self.stats['total_pages_attendues'] + 5:
            return False
        
        return True
    
    def parse_detail(self, response):
        """Parse la page de détail"""
        item = MenziliItem()
        base_data = response.meta['base_data']
        
        # Copier les données de base
        for key, value in base_data.items():
            if value is not None:
                item[key] = value
        
        # Informations supplémentaires
        item['type_offre'] = response.css('.item-box-type::text').get()
        item['categorie'] = response.css('.breadcrumb a:nth-child(2) span::text').get()
        
        # Prix en Euro
        prix_euro = response.css('.product-price span::text').get()
        if prix_euro:
            item['prix_euro'] = self.clean_price(prix_euro)
        
        # Description
        desc = response.css('.block-descr p::text').getall()
        if desc:
            item['description'] = ' '.join(desc).strip()
        
        # Référence et date
        item['ref_annonce'] = response.css('.block-ref span:contains("Rèf:") strong::text').get()
        
        date_pub = response.css('.block-ref time::attr(datetime)').get()
        if not date_pub:
            date_pub = response.css('.block-ref span:contains("Déposée le:") strong::text').get()
        item['date_publication'] = date_pub
        
        # Options
        options = response.css('.span-opts strong::text').getall()
        if options:
            item['options'] = [opt.strip() for opt in options if opt.strip()]
        
        # Images
        images = response.css('.slider-product img::attr(src)').getall()
        if images:
            item['images_urls'] = images
        
        # Détails supplémentaires
        self.extract_details(response, item)
        
        # Informations vendeur
        self.extract_vendeur(response, item)
        
        yield item
    
    def extract_annonce_id(self, url):
        """Extrait l'ID de l'annonce"""
        match = re.search(r'-(\d+)$', url)
        return match.group(1) if match else None
    
    def clean_price(self, price_text):
        """Nettoie le prix"""
        if not price_text:
            return None
        # Supprimer tout sauf les chiffres
        price_text = re.sub(r'[^\d]', '', price_text)
        try:
            return float(price_text)
        except:
            return None
    
    def extract_type_annonceur(self, annonce):
        """Détermine le type d'annonceur"""
        if annonce.css('.badge:contains("PRO")').get():
            return 'PRO'
        elif annonce.css('.badge:contains("Particulier")').get():
            return 'Particulier'
        return None
    
    def extract_caracteristiques(self, annonce, base_data):
        """Extrait les caractéristiques de la liste"""
        info_text = annonce.css('.li-list-item-info-span').get()
        if not info_text:
            return
        
        # Chambres
        match = re.search(r'(\d+)\s*<span[^>]*>Chambres', info_text)
        if match:
            base_data['chambres'] = int(match.group(1))
        
        # Salles de bain
        match = re.search(r'(\d+)\s*<span[^>]*>Salle de bain', info_text)
        if match:
            base_data['salles_bain'] = int(match.group(1))
        
        # Pièces
        match = re.search(r'(\d+)\s*<span[^>]*>Piéces', info_text)
        if match:
            base_data['pieces'] = int(match.group(1))
        
        # Surface habitable
        match = re.search(r'(\d+)<b[^>]*>m²</b>\s*<span[^>]*>Surf habitable', info_text)
        if match:
            base_data['surface_habitable'] = float(match.group(1))
        
        # Surface terrain
        match = re.search(r'(\d+)<b[^>]*>m²</b>\s*<span[^>]*>Surf terrain', info_text)
        if match:
            base_data['surface_terrain'] = float(match.group(1))
    
    def extract_details(self, response, item):
        """Extrait les détails de la page de détail"""
        for detail in response.css('.block-detail .block-over'):
            text = detail.get()
            if not text:
                continue
            
            if 'Surf habitable' in text:
                match = re.search(r'<strong>(\d+)\s*m²', text)
                if match and not item.get('surface_habitable'):
                    item['surface_habitable'] = float(match.group(1))
            elif 'Surf terrain' in text:
                match = re.search(r'<strong>(\d+)\s*m²', text)
                if match and not item.get('surface_terrain'):
                    item['surface_terrain'] = float(match.group(1))
            elif 'Chambres' in text:
                match = re.search(r'<strong>(\d+)', text)
                if match and not item.get('chambres'):
                    item['chambres'] = int(match.group(1))
            elif 'Salle de bain' in text:
                match = re.search(r'<strong>(\d+)', text)
                if match and not item.get('salles_bain'):
                    item['salles_bain'] = int(match.group(1))
            elif 'Piéces' in text:
                match = re.search(r'<strong>(\d+)', text)
                if match and not item.get('pieces'):
                    item['pieces'] = int(match.group(1))
    
    def extract_vendeur(self, response, item):
        """Extrait les infos du vendeur"""
        item['vendeur_nom'] = response.css('.right-bar-userinfo strong::text').get()
        
        if response.css('.badge:contains("PRO")').get():
            item['vendeur_type'] = 'PRO'
        else:
            item['vendeur_type'] = 'Particulier'
        
        tel = response.css('.block-2 i.fa-phone + ::text').get()
        if tel:
            item['vendeur_telephone'] = tel.strip()
        
        url_vendeur = response.css('.right-bar-userinfo a[href*="/agence/"], .right-bar-userinfo a[href*="/membre/"]::attr(href)').get()
        if url_vendeur:
            item['vendeur_url'] = response.urljoin(url_vendeur)
    
    def print_final_report(self):
        """Affiche le rapport final"""
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL DE SCRAPING - VERSION DYNAMIQUE")
        print("="*70)
        print(f"📄 Pages parcourues: {self.stats['pages_parcourues']}")
        print(f"🏠 Annonces trouvées: {self.stats['annonces_trouvees']}")
        print(f"🆔 Annonces uniques: {len(self.annonces_vues)}")
        
        if self.stats['total_annonces_attendu']:
            print(f"🎯 Total annonces détecté: {self.stats['total_annonces_attendu']}")
            pourcentage = (self.stats['annonces_trouvees'] / self.stats['total_annonces_attendu']) * 100
            print(f"📊 Complétude: {pourcentage:.1f}%")
        
        if self.stats['total_pages_attendues']:
            print(f"📑 Total pages détecté: {self.stats['total_pages_attendues']}")
        
        print(f"📈 Moyenne annonces/page: {self.stats['annonces_trouvees'] / max(1, self.stats['pages_parcourues']):.1f}")
        print(f"🔍 Dernière page avec annonces: {self.stats['derniere_page_avec_annonces'] or 0}")
        
        if self.stats['pages_sans_nouvelles_annonces'] > 0:
            print(f"⚠️ Pages sans nouvelles annonces: {self.stats['pages_sans_nouvelles_annonces']}")
        
        print("="*70)