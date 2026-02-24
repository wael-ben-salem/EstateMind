import scrapy
import re
import json
import os
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin
from ..items import TunisiapromoVenteItem

class VenteSpider(scrapy.Spider):
    name = "vente"
    allowed_domains = ["tunisiapromo.com"]
    start_urls = ["https://www.tunisiapromo.com/vente"]
    
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
        'annonces_nouvelles': 0,
        'pages_ignorees_500': 0
    }
    
    custom_settings = {
        # VITESSE MAXIMALE - MAIS SANS RIEN SAUTER
        'RETRY_TIMES': 10,  # Augmenté pour être sûr de réussir
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403, 404],  # Tous les codes d'erreur
        'RETRY_PRIORITY_ADJUST': -1,
        'DOWNLOAD_TIMEOUT': 30,  # Temps suffisant pour charger
        'CONCURRENT_REQUESTS': 32,  # MAXIMUM
        'DOWNLOAD_DELAY': 0.5,  # MINIMUM
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,
        'RANDOMIZE_DOWNLOAD_DELAY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # OPTIMISATIONS
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',  # Garder les logs pour suivre
        'COMPRESSION_ENABLED': True,
        'MEMUSAGE_ENABLED': False,
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': False,  # Pas de cache pour éviter les interférences
        'REDIRECT_ENABLED': True,  # GARDER les redirections
        'AJAXCRAWL_ENABLED': False,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_file = 'vente_checkpoint.json'
        self.last_scraped_info = self.load_checkpoint()
        self.last_scraped_page = self.last_scraped_info.get('last_page', 0)
        self.last_scraped_date = self.last_scraped_info.get('date', 'jamais')
        self.scraped_annonces_ids = set(self.last_scraped_info.get('annonces_ids', []))
        
        print(f"\n" + "="*70)
        print("🚀 MODE TURBO - SCRAPING COMPLET 🚀")
        print("="*70)
        print(f"📌 REPRISE INTELLIGENTE DU SCRAPING VENTE")
        print(f"📅 Dernier scraping: {self.last_scraped_date}")
        print(f"📄 Dernière page atteinte: {self.last_scraped_page}")
        print(f"🏠 Annonces déjà scrapées: {len(self.scraped_annonces_ids)}")
        print(f"⚡ Configuration: 32 requêtes/s, délai 0.5s, retry 10x")
        print(f"➡️ Reprise à partir de la page {self.last_scraped_page + 1}")
        print("="*70)
    
    def load_checkpoint(self):
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
        try:
            recent_ids = list(self.scraped_annonces_ids)[-1000:] if len(self.scraped_annonces_ids) > 1000 else list(self.scraped_annonces_ids)
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'last_page': self.stats['derniere_page_avec_annonces'],
                    'date': datetime.now().isoformat(),
                    'annonces_ids': recent_ids,
                    'total_annonces': self.stats['annonces_trouvees'],
                    'pages_parcourues': self.stats['pages_parcourues']
                }, f, indent=2)
        except:
            pass
    
    def start_requests(self):
        start_page = self.last_scraped_page + 1
        start_url = f"https://www.tunisiapromo.com/recherche?page={start_page}&listing_type=4&"
        print(f"🚀 Démarrage TURBO à la page {start_page}")
        yield scrapy.Request(start_url, callback=self.parse, dont_filter=True, errback=self.handle_pagination_error)
    
    def parse(self, response):
        # Vérifier si la réponse est valide
        if response.status >= 400:
            print(f"\n⚠️ ERREUR HTTP {response.status} sur page {self.extract_current_page_number(response.url)}")
            # On ne passe pas à la suivante, on réessaie
            return self.handle_http_error(response)
        
        self.stats['pages_parcourues'] += 1
        current_page_num = self.extract_current_page_number(response.url)
        
        # Log toutes les 20 pages pour suivre la progression
        log_this = (current_page_num % 20 == 0)
        
        annonces = response.css('article.short_ad_panel')
        annonces_valides = [a for a in annonces if not a.css('ins.adsbygoogle').get()]
        
        if log_this:
            print(f"\n📄 PAGE {current_page_num} | Annonces: {len(annonces_valides)} | Pages/h: {self.stats['pages_parcourues']*60/(time.time() - self.start_time if hasattr(self, 'start_time') else 1):.0f}")
        
        # Traitement des annonces
        nouvelles = 0
        for annonce in annonces_valides:
            url_rel = annonce.css('h2 a::attr(href)').get()
            if not url_rel:
                continue
                
            url_detail = response.urljoin(url_rel)
            annonce_id = self.extract_annonce_id(url_detail)
            
            if annonce_id and annonce_id in self.scraped_annonces_ids:
                self.stats['annonces_deja_vues'] += 1
                continue
            
            nouvelles += 1
            if annonce_id:
                self.scraped_annonces_ids.add(annonce_id)
            
            # Extraction des infos de base
            titre = annonce.css('h2 a::text').get()
            type_bien = annonce.css('span.ticket.property_type::text').get()
            prix_text = annonce.css('span.price::text').get()
            location = annonce.css('div.property_location b::text').get()
            description = annonce.css('p.listing-description::text').get()
            date_pub = annonce.css('span.listing_added::text').get()
            
            base_data = {
                'annonce_id': annonce_id,
                'url': url_detail,
                'titre': titre.strip() if titre else '',
                'type_bien': type_bien.strip() if type_bien else '',
                'prix': self.clean_price(prix_text),
                'region': None,
                'ville': None,
                'adresse': location.strip() if location else '',
                'description': description.strip() if description else '',
                'date_publication': date_pub.strip() if date_pub else '',
                'date_scraping': datetime.now().isoformat(),
                'page_trouvee': current_page_num
            }
            
            # Extraction de la localisation
            if location and '/' in location:
                parts = location.split('/')
                base_data['region'] = parts[0].strip()
                base_data['ville'] = parts[1].strip() if len(parts) > 1 else None
            
            yield scrapy.Request(
                url_detail,
                callback=self.parse_detail,
                errback=self.handle_detail_error,
                priority=10,
                meta={'base_data': base_data, 'tentative': 1, 'page_num': current_page_num}
            )
        
        self.stats['annonces_nouvelles'] += nouvelles
        self.stats['annonces_trouvees'] += nouvelles
        
        if log_this and nouvelles > 0:
            print(f"   🆕 +{nouvelles} nouvelles annonces")
        
        # Détection de la fin
        if len(annonces_valides) == 0:
            self.stats['pages_vides_consecutives'] += 1
            if log_this:
                print(f"   ⚠️ Page vide #{self.stats['pages_vides_consecutives']}")
            
            # Arrêt après 10 pages vides consécutives (pour être sûr)
            if self.stats['pages_vides_consecutives'] >= 10:
                print(f"\n🛑 FIN DÉTECTÉE - {self.stats['pages_vides_consecutives']} pages vides consécutives")
                self.print_final_report()
                return
        else:
            self.stats['pages_vides_consecutives'] = 0
            self.stats['derniere_page_avec_annonces'] = current_page_num
            
            # Checkpoint toutes les 50 pages
            if current_page_num % 50 == 0:
                self.save_checkpoint()
        
        # Page suivante
        next_page = self.get_next_page(response)
        if next_page and next_page != response.url:
            next_num = self.extract_current_page_number(next_page)
            if log_this:
                print(f"   ➡️ Prochaine page: {next_num}")
            yield scrapy.Request(
                next_page,
                callback=self.parse,
                errback=self.handle_pagination_error,
                dont_filter=True,
                priority=0,
                meta={'page_num': next_num, 'tentative': 1}
            )
        else:
            self.print_final_report()
    
    def handle_http_error(self, response):
        """Gère les erreurs HTTP avec retry"""
        current_page_num = self.extract_current_page_number(response.url)
        meta = response.request.meta
        tentative = meta.get('tentative', 1)
        
        print(f"\n⚠️ PAGE {current_page_num} - Tentative {tentative} - Erreur {response.status}")
        
        if tentative >= 10:  # 10 tentatives maximum
            print(f"   🛑 ABANDON après 10 tentatives - on passe à la page suivante")
            self.stats['pages_erreur'] += 1
            next_page = self.construct_next_page(response.url)
            if next_page:
                yield scrapy.Request(
                    next_page,
                    callback=self.parse,
                    errback=self.handle_pagination_error,
                    dont_filter=True,
                    priority=0,
                    meta={'page_num': self.extract_current_page_number(next_page), 'tentative': 1}
                )
            return
        
        # Attente exponentielle
        delai = min(2 ** tentative, 30)
        print(f"   ⏳ Nouvelle tentative dans {delai}s")
        time.sleep(delai)
        
        # Réessayer la même page
        yield scrapy.Request(
            response.url,
            callback=self.parse,
            errback=self.handle_pagination_error,
            dont_filter=True,
            priority=100 + tentative,
            meta={'page_num': current_page_num, 'tentative': tentative + 1}
        )
    
    def handle_pagination_error(self, failure):
        """Gère les erreurs de pagination avec retry"""
        self.stats['pages_erreur'] += 1
        request = failure.request
        meta = request.meta
        tentative = meta.get('tentative', 1)
        page_num = meta.get('page_num', 'inconnue')
        
        print(f"\n⚠️ PAGE {page_num} - Tentative {tentative} - Échec: {failure.value}")
        
        if tentative >= 10:  # 10 tentatives maximum
            print(f"   🛑 ABANDON après 10 tentatives - on passe à la page suivante")
            next_page = self.construct_next_page(request.url)
            if next_page:
                yield scrapy.Request(
                    next_page,
                    callback=self.parse,
                    errback=self.handle_pagination_error,
                    dont_filter=True,
                    priority=0,
                    meta={'page_num': self.extract_current_page_number(next_page), 'tentative': 1}
                )
            return
        
        delai = min(2 ** tentative, 30)
        print(f"   ⏳ Nouvelle tentative dans {delai}s")
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
        page_num = meta.get('page_num', '?')
        
        print(f"\n⚠️ DÉTAIL {annonce_id} page {page_num} - Tentative {tentative}")
        
        if tentative >= 5:  # 5 tentatives pour les détails
            print(f"   🛑 ABANDON après {tentative} tentatives")
            return
        
        delai = min(2 ** tentative, 20)
        print(f"   ⏳ Nouvelle tentative dans {delai}s")
        time.sleep(delai)
        
        yield scrapy.Request(
            request.url,
            callback=self.parse_detail,
            errback=self.handle_detail_error,
            dont_filter=True,
            priority=20 + tentative,
            meta={'base_data': base_data, 'tentative': tentative + 1, 'page_num': page_num}
        )
    
    def get_next_page(self, response):
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
        
        return self.construct_next_page(response.url)
    
    def construct_next_page(self, url):
        current = self.extract_current_page_number(url)
        next_page_num = current + 1
        
        if 'page=' in url:
            return re.sub(r'page=\d+', f'page={next_page_num}', url)
        else:
            return f"{url}&page={next_page_num}" if '?' in url else f"{url}?page={next_page_num}"
    
    def extract_current_page_number(self, url):
        match = re.search(r'page=(\d+)', url)
        return int(match.group(1)) if match else 1
    
    def parse_detail(self, response):
        """Parse complet des détails"""
        item = TunisiapromoVenteItem()
        base = response.meta['base_data']
        
        for k, v in base.items():
            if v:
                item[k] = v
        
        item['type_offre'] = 'Vente'
        
        # Référence
        ref = response.xpath('//span[contains(text(), "Référence")]/following-sibling::span/text()').get()
        if ref:
            match = re.search(r'(\d+)', ref)
            if match:
                item['reference'] = match.group(1)
        if not item.get('reference'):
            item['reference'] = base.get('annonce_id')
        
        # Prix en Euro
        prix_euro = response.css('span.property_price::text').get()
        if prix_euro and '€' in prix_euro:
            item['prix_euro'] = self.clean_price(prix_euro)
        
        # Toutes les caractéristiques
        mappings = [
            ('Surface habitable', 'surface_habitable', float),
            ('Surface Terrain', 'surface_terrain', float),
            ('Nombre de pièce', 'pieces', int),
            ('Chambres', 'chambres', int),
            ('Salle de bain', 'salles_bain', int),
            ("Salle d'eau", 'salles_eau', int),
            ('place de Voiture', 'places_voiture', int),
            ('Année de Construction', 'annee_construction', int),
            ('Numéro', 'etage', int),
        ]
        
        for label, field, cast in mappings:
            val = response.xpath(f'//span[contains(text(), "{label}")]/following-sibling::span/text()').get()
            if val:
                match = re.search(r'(\d+)', val)
                if match:
                    item[field] = cast(match.group(1))
        
        # Description complète
        desc = response.css('div.clear p::text').getall()
        if desc:
            item['description'] = ' '.join(desc).strip()
        
        # Options et équipements
        options = response.xpath('//span[contains(text(), "Caractéristiques")]/following-sibling::text()').get()
        if options:
            item['options'] = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        equipements = response.xpath('//span[contains(text(), "Equipements")]/following-sibling::text()').get()
        if equipements:
            item['equipements'] = [eq.strip() for eq in equipements.split(',') if eq.strip()]
        
        # Toutes les images
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
        
        # Annonceur
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
        
        # Code postal
        adresse = response.xpath('//span[contains(text(), "Adresse")]/following-sibling::text()').get()
        if adresse:
            cp_match = re.search(r'\b(\d{4,5})\b', adresse)
            if cp_match:
                item['code_postal'] = cp_match.group(1)
        
        yield item
    
    def extract_annonce_id(self, url):
        match = re.search(r'-z(\d+)\.html', url)
        return match.group(1) if match else None
    
    def clean_price(self, price_text):
        if not price_text:
            return None
        price_text = re.sub(r'[^\d]', '', price_text)
        try:
            return float(price_text)
        except:
            return None
    
    def print_final_report(self):
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL - SCRAPING COMPLET")
        print("="*70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📄 PAGES:")
        print(f"   ├─ Total parcourues: {self.stats['pages_parcourues']}")
        print(f"   ├─ Nouvelles: {self.stats['pages_nouvelles']}")
        print(f"   └─ Déjà scrapées: {self.stats['pages_deja_scrapees']}")
        print(f"\n🏠 ANNONCES:")
        print(f"   ├─ Nouvelles trouvées: {self.stats['annonces_nouvelles']}")
        print(f"   ├─ Déjà vues: {self.stats['annonces_deja_vues']}")
        print(f"   └─ Total cumulé: {len(self.scraped_annonces_ids)}")
        print(f"\n⚠️ ERREURS:")
        print(f"   ├─ Pages en erreur: {self.stats['pages_erreur']}")
        print(f"   └─ Tentatives totales: {self.stats['tentatives_total']}")
        print(f"\n📌 STATUT:")
        print(f"   ├─ Dernière page avec annonces: {self.stats['derniere_page_avec_annonces']}")
        print(f"   └─ Pages vides consécutives: {self.stats['pages_vides_consecutives']}")
        print("="*70)
        
        self.save_checkpoint()
        print(f"\n💾 Checkpoint final: page {self.stats['derniere_page_avec_annonces']}")