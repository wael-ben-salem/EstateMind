import scrapy
import re
import json
import os
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin
from ..items import TunisiapromoColocationItem

class ColocationSpider(scrapy.Spider):
    name = "colocation"
    allowed_domains = ["tunisiapromo.com"]
    start_urls = ["https://www.tunisiapromo.com/colocation"]
    
    stats = {
        'pages_parcourues': 0,
        'annonces_trouvees': 0,
        'pages_erreur': 0,
        'tentatives_total': 0,
        'pages_vides_consecutives': 0,
        'derniere_page_avec_annonces': 0,
        'pages_nouvelles': 0,
        'pages_deja_scrapees': 0,
        'annonces_deja_vues': 0,
        'annonces_nouvelles': 0
    }
    
    custom_settings = {
        # OPTIMISATIONS POUR LA VITESSE
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'RETRY_PRIORITY_ADJUST': -1,
        'DOWNLOAD_TIMEOUT': 30,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # AJOUTS POUR ACCÉLÉRER
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
        'COMPRESSION_ENABLED': True,
        'MEMUSAGE_ENABLED': False,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_file = 'colocation_checkpoint.json'
        self.last_scraped_info = self.load_checkpoint()
        self.last_scraped_page = self.last_scraped_info.get('last_page', 0)
        self.last_scraped_date = self.last_scraped_info.get('date', 'jamais')
        self.scraped_annonces_ids = set(self.last_scraped_info.get('annonces_ids', []))
        
        print(f"\n" + "="*60)
        print("📌 REPRISE INTELLIGENTE DU SCRAPING COLOCATION")
        print("="*60)
        print(f"📅 Dernier scraping: {self.last_scraped_date}")
        print(f"📄 Dernière page atteinte: {self.last_scraped_page}")
        print(f"🏠 Annonces déjà scrapées: {len(self.scraped_annonces_ids)}")
        print(f"➡️ Reprise à partir de la page {self.last_scraped_page + 1}")
        print("="*60)
    
    def load_checkpoint(self):
        """Charge les informations du dernier scraping"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    return {
                        'last_page': data.get('last_page', 0),
                        'date': data.get('date', 'jamais'),
                        'annonces_ids': data.get('annonces_ids', [])
                    }
            except:
                pass
        return {'last_page': 0, 'date': 'jamais', 'annonces_ids': []}
    
    def save_checkpoint(self):
        """Sauvegarde l'état actuel du scraping"""
        try:
            # Ne garder que les 1000 derniers IDs pour éviter un fichier trop gros
            recent_ids = list(self.scraped_annonces_ids)[-1000:] if len(self.scraped_annonces_ids) > 1000 else list(self.scraped_annonces_ids)
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'last_page': self.stats['derniere_page_avec_annonces'],
                    'date': datetime.now().isoformat(),
                    'annonces_ids': recent_ids,
                    'total_annonces': self.stats['annonces_trouvees'],
                    'pages_parcourues': self.stats['pages_parcourues']
                }, f, indent=2)
            print(f"💾 Checkpoint auto sauvegardé: page {self.stats['derniere_page_avec_annonces']}")
        except:
            pass
    
    def parse(self, response):
        # Si on reçoit une réponse, on incrémente les pages parcourues
        self.stats['pages_parcourues'] += 1
        current_page_num = self.extract_current_page_number(response.url)
        
        # Détection automatique : si la page est plus petite que la dernière connue
        if current_page_num <= self.last_scraped_page:
            self.stats['pages_deja_scrapees'] += 1
            
            # Log toutes les 50 pages pour ne pas spammer
            if current_page_num % 50 == 0:
                print(f"\n⏭️ PAGE COLOCATION {current_page_num} déjà scrapée le {self.last_scraped_date}")
                print(f"   🔍 Recherche de la page {self.last_scraped_page + 1}...")
            
            # Chercher la page suivante
            next_page = self.get_next_page(response)
            if next_page:
                next_page_num = self.extract_current_page_number(next_page)
                
                # Si la page suivante est aussi déjà scrapée, on continue
                if next_page_num <= self.last_scraped_page:
                    yield scrapy.Request(
                        next_page,
                        callback=self.parse,
                        dont_filter=True,
                        priority=0
                    )
                else:
                    # Trouvé la première page non scrapée !
                    print(f"\n✅ PREMIÈRE PAGE NOUVELLE TROUVÉE: {next_page_num}")
                    print(f"   📅 Dernier scraping: page {self.last_scraped_page}")
                    print(f"   ➡️ Reprise du scraping à partir d'ici\n")
                    yield scrapy.Request(
                        next_page,
                        callback=self.parse,
                        dont_filter=True,
                        priority=1
                    )
            return
        
        # Page nouvelle - on scrape normalement
        self.stats['pages_nouvelles'] += 1
        
        # Log toutes les 10 pages
        if current_page_num % 10 == 0:
            print(f"\n📄 PAGE COLOCATION {current_page_num}")
            print(f"   ⏱️ Pages nouvelles: {self.stats['pages_nouvelles']}, Déjà scrapées: {self.stats['pages_deja_scrapees']}")
        
        # Extraire les annonces (ignorer les pubs)
        annonces = response.css('article.short_ad_panel')
        annonces_valides = []
        nouvelles_annonces_page = 0
        
        for annonce in annonces:
            if not annonce.css('ins.adsbygoogle').get():
                annonces_valides.append(annonce)
        
        if current_page_num % 10 == 0:
            print(f"   ✅ Colocations sur cette page: {len(annonces_valides)}")
        
        for annonce in annonces_valides:
            # URL de détail
            url_rel = annonce.css('h2 a::attr(href)').get()
            if url_rel:
                url_detail = response.urljoin(url_rel)
                annonce_id = self.extract_annonce_id(url_detail)
                
                # Vérifier si l'annonce est déjà scrapée
                if annonce_id and annonce_id in self.scraped_annonces_ids:
                    self.stats['annonces_deja_vues'] += 1
                    continue  # Ignorer les annonces déjà vues
                
                # Nouvelle annonce !
                self.stats['annonces_nouvelles'] += 1
                nouvelles_annonces_page += 1
                if annonce_id:
                    self.scraped_annonces_ids.add(annonce_id)
                
                # Extraire les infos de base
                titre = annonce.css('h2 a::text').get()
                if titre:
                    titre = titre.strip()
                
                # Type de bien
                type_bien = annonce.css('span.ticket.property_type::text').get()
                if type_bien:
                    type_bien = type_bien.strip()
                
                # Type d'annonce (Offre ou Demande)
                type_annonce = 'Offre'
                if annonce.css('.isearch').get() or 'recherch' in titre.lower():
                    type_annonce = 'Demande'
                
                # Prix
                prix_text = annonce.css('span.price::text').get()
                prix = self.clean_price(prix_text)
                
                # Localisation
                location = annonce.css('div.property_location b::text').get()
                region, ville = self.extract_location(location)
                
                # Quartier (parfois dans le titre ou la localisation)
                quartier = self.extract_quartier(titre, location)
                
                # Description courte
                description = annonce.css('p.listing-description::text').get()
                if description:
                    description = description.strip()
                
                # Date publication
                date_pub = annonce.css('span.listing_added::text').get()
                if date_pub:
                    date_pub = date_pub.strip()
                
                # Genre recherché (d'après la description)
                genre = self.detect_genre(titre, description)
                
                base_data = {
                    'annonce_id': annonce_id,
                    'url': url_detail,
                    'titre': titre,
                    'type_bien': type_bien,
                    'type_annonce': type_annonce,
                    'prix': prix,
                    'region': region,
                    'ville': ville,
                    'quartier': quartier,
                    'adresse': location,
                    'description': description,
                    'date_publication': date_pub,
                    'genre_recherche': genre,
                    'date_scraping': datetime.now().isoformat(),
                    'page_trouvee': current_page_num
                }
                
                yield scrapy.Request(
                    url_detail,
                    callback=self.parse_detail,
                    errback=self.handle_detail_error,
                    priority=10,
                    meta={'base_data': base_data, 'tentative': 1}
                )
        
        if current_page_num % 10 == 0 and nouvelles_annonces_page > 0:
            print(f"   🆕 Nouvelles colocations sur cette page: {nouvelles_annonces_page}")
        
        # Mise à jour des stats
        self.stats['annonces_trouvees'] += nouvelles_annonces_page
        
        # DÉTECTION INTELLIGENTE DE LA FIN
        if len(annonces_valides) == 0:
            self.stats['pages_vides_consecutives'] += 1
            if current_page_num % 10 == 0:
                print(f"   ⚠️ Page {current_page_num} sans annonces (vide #{self.stats['pages_vides_consecutives']})")
            
            # Critères d'arrêt
            if self.stats['pages_vides_consecutives'] >= 5:
                print(f"\n🛑 ARRÊT DÉTECTÉ : {self.stats['pages_vides_consecutives']} pages vides consécutives")
                print(f"   Dernière page avec annonces : {self.stats['derniere_page_avec_annonces']}")
                self.print_final_report()
                return
            
            if current_page_num > self.stats['derniere_page_avec_annonces'] + 10 and self.stats['derniere_page_avec_annonces'] > 0:
                print(f"\n🛑 ARRÊT DÉTECTÉ : Plus de 10 pages sans annonces après la dernière page {self.stats['derniere_page_avec_annonces']}")
                self.print_final_report()
                return
            
            if current_page_num > 2000:  # Limite de sécurité pour colocation
                print(f"\n🛑 ARRÊT DE SÉCURITÉ : Page {current_page_num} > 2000")
                self.print_final_report()
                return
        else:
            # Réinitialiser le compteur de pages vides
            self.stats['pages_vides_consecutives'] = 0
            self.stats['derniere_page_avec_annonces'] = current_page_num
            
            # Sauvegarder le checkpoint toutes les 20 pages
            if current_page_num % 20 == 0:
                self.save_checkpoint()
        
        # === GESTION PAGINATION ===
        # Ne pas continuer si on a déjà détecté la fin
        if self.stats['pages_vides_consecutives'] >= 5:
            return
        
        next_page = self.get_next_page(response)
        
        if next_page and next_page != response.url:
            next_page_num = self.extract_current_page_number(next_page)
            
            if current_page_num % 10 == 0:
                print(f"   ➡️ Prochaine page: {next_page_num}")
            
            yield scrapy.Request(
                next_page,
                callback=self.parse,
                errback=self.handle_pagination_error,
                dont_filter=True,
                priority=0,
                meta={'page_num': next_page_num, 'tentative': 1}
            )
        else:
            self.print_final_report()
            self.save_checkpoint()
    
    def handle_pagination_error(self, failure):
        """Gère les erreurs de pagination"""
        self.stats['pages_erreur'] += 1
        request = failure.request
        meta = request.meta
        tentative = meta.get('tentative', 1)
        page_num = meta.get('page_num', 'inconnue')
        
        self.stats['tentatives_total'] += 1
        
        if tentative > 5:
            print(f"\n🛑 ABANDON PAGE {page_num} après {tentative} tentatives")
            return
        
        delai = min(2 * (2 ** (tentative - 1)), 60)
        
        print(f"\n⚠️ ERREUR PAGE COLOCATION {page_num} - Tentative {tentative} - Attente {delai}s")
        time.sleep(delai)
        
        yield scrapy.Request(
            request.url,
            callback=self.parse,
            errback=self.handle_pagination_error,
            dont_filter=True,
            priority=100 + tentative,
            meta={'page_num': page_num, 'tentative': tentative + 1}
        )
    
    def handle_detail_error(self, failure):
        """Gère les erreurs sur les pages de détail"""
        request = failure.request
        meta = request.meta
        tentative = meta.get('tentative', 1)
        base_data = meta.get('base_data', {})
        annonce_id = base_data.get('annonce_id', 'inconnu')
        
        if tentative > 3:
            print(f"   🛑 ABANDON annonce {annonce_id} après {tentative} tentatives")
            return
        
        delai = min(2 * (2 ** (tentative - 1)), 30)
        print(f"   ⚠️ Erreur détail colocation {annonce_id} - Tentative {tentative} - Attente {delai}s")
        time.sleep(delai)
        
        yield scrapy.Request(
            request.url,
            callback=self.parse_detail,
            errback=self.handle_detail_error,
            dont_filter=True,
            priority=20 + tentative,
            meta={'base_data': base_data, 'tentative': tentative + 1}
        )
    
    def get_next_page(self, response):
        """Trouve l'URL de la page suivante"""
        # Méthode rapide : chercher le lien "Suivant"
        next_selectors = [
            'a:contains("Suivant")::attr(href)',
            'a:contains("Suivante")::attr(href)',
            'a.pagination_next::attr(href)',
            'li.next a::attr(href)',
        ]
        
        for selector in next_selectors:
            next_link = response.css(selector).get()
            if next_link:
                return response.urljoin(next_link)
        
        # Construction manuelle rapide
        return self.construct_next_page(response.url)
    
    def construct_next_page(self, url):
        current_page = self.extract_current_page_number(url)
        next_page_num = current_page + 1
        
        if 'page=' in url:
            return re.sub(r'page=\d+', f'page={next_page_num}', url)
        else:
            if '?' in url:
                return f"{url}&page={next_page_num}"
            else:
                return f"{url}?page={next_page_num}"
    
    def extract_current_page_number(self, url):
        match = re.search(r'page=(\d+)', url)
        if match:
            return int(match.group(1))
        return 1
    
    def parse_detail(self, response):
        """Parse les détails d'une annonce de colocation"""
        item = TunisiapromoColocationItem()
        base = response.meta['base_data']
        
        for k, v in base.items():
            if v is not None:
                item[k] = v
        
        # Type d'offre
        item['type_offre'] = 'Colocation'
        
        # Référence (optimisé)
        ref_text = response.xpath('//span[contains(text(), "Référence")]/following-sibling::span/text()').get()
        if ref_text:
            match = re.search(r'(\d+)', ref_text)
            if match:
                item['reference'] = match.group(1)
        else:
            item['reference'] = base.get('annonce_id')
        
        # Prix en Euro
        prix_euro = response.css('span.property_price::text').get()
        if prix_euro and '€' in prix_euro:
            item['prix_euro'] = self.clean_price(prix_euro)
        
        # Caractéristiques (optimisé)
        self.extract_caracteristiques(response, item)
        
        # Description complète (optimisé)
        desc_blocks = response.css('div.clear p::text').getall()
        if desc_blocks:
            item['description'] = ' '.join(desc_blocks).strip()
        
        # Options et équipements
        options = response.xpath('//span[contains(text(), "Caractéristiques")]/following-sibling::text()').get()
        if options:
            item['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        equipements = response.xpath('//span[contains(text(), "Equipements")]/following-sibling::text()').get()
        if equipements:
            item['equipements'] = [eq.strip() for eq in equipements.split(',') if eq.strip()]
        
        # Images (optimisé)
        images = []
        main_img = response.css('img#mygallery::attr(src)').get()
        if main_img and not main_img.startswith('data:'):
            images.append(response.urljoin(main_img))
        
        for img in response.css('#wowslider-container1 img::attr(src)').getall():
            if img and not img.startswith('data:'):
                full_url = response.urljoin(img)
                if full_url not in images:
                    images.append(full_url)
        
        if images:
            item['images_urls'] = images
            item['nombre_photos'] = len(images)
        
        # Annonceur (optimisé)
        self.extract_annonceur(response, item)
        
        # Code postal
        adresse_complete = response.xpath('//span[contains(text(), "Adresse")]/following-sibling::text()').get()
        if adresse_complete:
            item['adresse'] = adresse_complete.strip()
            cp_match = re.search(r'\b(\d{4,5})\b', adresse_complete)
            if cp_match:
                item['code_postal'] = cp_match.group(1)
        
        # Détails supplémentaires de colocation
        self.extract_colocation_details(response, item)
        
        yield item
    
    def extract_annonce_id(self, url):
        match = re.search(r'-z(\d+)\.html', url)
        if match:
            return match.group(1)
        return None
    
    def clean_price(self, price_text):
        if not price_text:
            return None
        price_text = re.sub(r'[^\d]', '', price_text)
        try:
            return float(price_text)
        except:
            return None
    
    def extract_location(self, location_text):
        if not location_text:
            return None, None
        parts = location_text.split('/')
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
        return None, None
    
    def extract_quartier(self, titre, location):
        if location and '/' in location:
            parts = location.split('/')
            if len(parts) >= 2:
                return parts[1].strip()
        return None
    
    def detect_genre(self, titre, description):
        texte = f"{titre} {description}".upper()
        
        if 'JF' in texte or 'FILLE' in texte or 'FEMME' in texte or 'JEUNE FILLE' in texte:
            return 'F'
        elif 'JH' in texte or 'HOMME' in texte or 'GARÇON' in texte or 'JEUNE HOMME' in texte:
            return 'H'
        elif 'MIXTE' in texte or 'HF' in texte or 'INDIFFÉRENT' in texte:
            return 'Mixte'
        else:
            return 'Non spécifié'
    
    def extract_caracteristiques(self, response, item):
        mappings = [
            ('Surface habitable', 'surface_habitable', float),
            ('Nombre de pièce', 'pieces', int),
            ('Chambres', 'chambres', int),
            ('Salle de bain', 'salles_bain', int),
            ("Salle d'eau", 'salles_eau', int),
            ('place de Voiture', 'places_voiture', int),
            ('Année de Construction', 'annee_construction', int),
            ('Numéro', 'etage', int),
        ]
        
        for label, field, cast_func in mappings:
            value = response.xpath(f'//span[contains(text(), "{label}")]/following-sibling::span/text()').get()
            if value:
                match = re.search(r'(\d+)', value)
                if match:
                    item[field] = cast_func(match.group(1))
        
        if not item.get('chambres'):
            chambres = response.css('div[style*="float:left"] span.bed + ::text').get()
            if chambres:
                match = re.search(r'(\d+)', chambres)
                if match:
                    item['chambres'] = int(match.group(1))
    
    def extract_annonceur(self, response, item):
        nom = response.css('div.realtor_logo_div + img::attr(alt)').get()
        if nom:
            item['annonceur_nom'] = nom.strip()
        
        if response.css('strong:contains("Particulier")').get():
            item['annonceur_type'] = 'Particulier'
        elif response.css('strong:contains("Agence")').get():
            item['annonceur_type'] = 'Agence'
        
        tel = response.css('span.phone + img::attr(alt)').get()
        if tel:
            item['annonceur_telephone'] = tel.strip()
    
    def extract_colocation_details(self, response, item):
        desc = item.get('description', '')
        
        # Nombre de personnes
        nb_match = re.search(r'(\d+)\s*(?:personne|colocataire|cherche|célibataire)', desc, re.IGNORECASE)
        if nb_match:
            item['nb_personnes'] = int(nb_match.group(1))
        
        # Type de logement
        if 'chambre' in desc.lower():
            item['type_logement'] = 'Chambre privée'
        elif 'studio' in desc.lower():
            item['type_logement'] = 'Studio partagé'
        elif 'appartement' in desc.lower():
            item['type_logement'] = 'Appartement partagé'
        elif 'maison' in desc.lower():
            item['type_logement'] = 'Maison partagée'
        elif 'bureau' in desc.lower():
            item['type_logement'] = 'Bureau partagé'
    
    def print_final_report(self):
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL - SCRAPING COLOCATION INTELLIGENT")
        print("="*70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📄 PAGES:")
        print(f"   ├─ Total parcourues: {self.stats['pages_parcourues']}")
        print(f"   ├─ Nouvelles: {self.stats['pages_nouvelles']}")
        print(f"   └─ Déjà scrapées: {self.stats['pages_deja_scrapees']}")
        print(f"\n🏠 ANNONCES:")
        print(f"   ├─ Nouvelles trouvées: {self.stats['annonces_nouvelles']}")
        print(f"   ├─ Déjà vues (ignorées): {self.stats['annonces_deja_vues']}")
        print(f"   └─ Total cumulé: {len(self.scraped_annonces_ids)}")
        print(f"\n📌 STATUT:")
        print(f"   ├─ Dernière page avec annonces: {self.stats['derniere_page_avec_annonces']}")
        print(f"   ├─ Pages vides consécutives: {self.stats['pages_vides_consecutives']}")
        print(f"   ├─ Pages en erreur: {self.stats['pages_erreur']}")
        print(f"   └─ Tentatives totales: {self.stats['tentatives_total']}")
        print("="*70)
        
        # Sauvegarde finale
        self.save_checkpoint()
        print(f"\n💾 Checkpoint final sauvegardé dans: {self.checkpoint_file}")
        print(f"📁 Pour le prochain run, reprise à la page {self.stats['derniere_page_avec_annonces'] + 1}")