import scrapy
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from ..items import LocationItem

class LocationSpider(scrapy.Spider):
    name = "location"
    allowed_domains = ["menzili.tn"]
    start_urls = ["https://www.menzili.tn/immo/location-immobilier-tunisie?tri=1"]
    
    stats = {
        'pages_parcourues': 0,
        'annonces_trouvees': 0,
        'total_annonces_attendu': None
    }
    
    def parse(self, response):
        self.stats['pages_parcourues'] += 1
        
        # === DÉTECTION AUTO DU NOMBRE TOTAL ===
        if not self.stats['total_annonces_attendu']:
            h1_text = response.css('h1::text').get()
            if h1_text:
                match = re.search(r'(\d+)\s*annonce', h1_text)
                if match:
                    self.stats['total_annonces_attendu'] = int(match.group(1))
                    print(f"\n🎯 TOTAL LOCATIONS DÉTECTÉ: {self.stats['total_annonces_attendu']}")
        
        print(f"\n📄 PAGE LOCATION {self.stats['pages_parcourues']}")
        
        # Extraire les annonces de location
        annonces = response.css('.li-item-list')
        annonces_sur_page = len(annonces)
        print(f"   ✅ Locations sur cette page: {annonces_sur_page}")
        print(f"   📈 Progression: {self.stats['annonces_trouvees']}/{self.stats['total_annonces_attendu'] or '???'}")
        
        for annonce in annonces:
            self.stats['annonces_trouvees'] += 1
            
            url_detail = annonce.css('a.li-item-list-title::attr(href)').get()
            if url_detail:
                url_detail = response.urljoin(url_detail)
                annonce_id = self.extract_id(url_detail)
                
                # Extraire le prix avec sa période
                prix_complet = annonce.css('.item-box-price::text').get()
                prix_data = self.parse_prix_location(prix_complet)
                
                base_data = {
                    'annonce_id': annonce_id,
                    'url': url_detail,
                    'titre': annonce.css('a.li-item-list-title::text').get(),
                    'prix': prix_data,
                    'est_premium': bool(annonce.css('.strap-premium').get()),
                    'type_annonceur': self.get_type_annonceur(annonce),
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
                self.extract_caracs(annonce, base_data)
                
                yield scrapy.Request(
                    url_detail,
                    callback=self.parse_detail,
                    meta={'base_data': base_data}
                )
        
        # === PAGINATION ROBUSTE ===
        next_page = None
        next_page = response.css('link[rel="next"]::attr(href)').get()
        
        if not next_page:
            next_page = response.css('.pagination a:contains("Suivant")::attr(href)').get()
        
        if not next_page:
            current_url = response.url
            if 'page=' in current_url:
                match = re.search(r'page=(\d+)', current_url)
                if match:
                    next_page_num = int(match.group(1)) + 1
                    next_page = re.sub(r'page=\d+', f'page={next_page_num}', current_url)
            else:
                if '?' in current_url:
                    next_page = current_url + '&page=2'
                else:
                    next_page = current_url + '?page=2'
        
        # Décision de continuer
        continuer = True
        if self.stats['total_annonces_attendu'] and self.stats['annonces_trouvees'] >= self.stats['total_annonces_attendu']:
            print(f"\n✅ TOUTES LES LOCATIONS SCRAPPÉES: {self.stats['annonces_trouvees']}")
            continuer = False
        
        if continuer and next_page and response.url != next_page:
            print(f"   ➡️ Page suivante: {next_page}")
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            self.print_final_report()
    
    def parse_detail(self, response):
        """Parse les détails d'une location"""
        item = LocationItem()
        base = response.meta['base_data']
        
        for k, v in base.items():
            if v is not None:
                item[k] = v
        
        # Infos spécifiques à la location
        item['type_offre'] = 'Louer'
        item['categorie'] = response.css('.breadcrumb a:nth-child(2) span::text').get()
        
        # Prix Euro
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
            item['options'] = [o.strip() for o in options if o.strip()]
        
        # Images
        images = response.css('.slider-product img::attr(src)').getall()
        if images:
            item['images_urls'] = images
        
        # Détails supplémentaires
        self.extract_details(response, item)
        
        # Vendeur
        self.extract_vendeur(response, item)
        
        # Déterminer le type de location d'après le prix
        if item.get('prix') and isinstance(item['prix'], dict):
            item['type_location'] = item['prix'].get('periode')
        
        yield item
    
    def parse_prix_location(self, prix_text):
        """Parse le prix spécial location (ex: '800 DT / Mois')"""
        if not prix_text:
            return None
        
        prix_text = prix_text.strip()
        
        # Pattern: "800 DT / Mois" ou "2 500 DT / Nuit" etc.
        match = re.match(r'([\d\s]+)\s*DT\s*\/?\s*([a-zA-Z]+)', prix_text)
        if match:
            montant = match.group(1).replace(' ', '')
            periode = match.group(2).strip()
            try:
                return {
                    'montant': float(montant),
                    'periode': periode
                }
            except:
                pass
        
        # Si pas de période, juste le montant
        montant = re.sub(r'[^\d]', '', prix_text)
        try:
            return {
                'montant': float(montant),
                'periode': 'inconnue'
            }
        except:
            return None
    
    def extract_id(self, url):
        match = re.search(r'-(\d+)$', url)
        return match.group(1) if match else None
    
    def clean_price(self, text):
        if not text:
            return None
        text = re.sub(r'[^\d]', '', text)
        try:
            return float(text)
        except:
            return None
    
    def get_type_annonceur(self, annonce):
        if annonce.css('.badge:contains("PRO")').get():
            return 'PRO'
        elif annonce.css('.badge:contains("Particulier")').get():
            return 'Particulier'
        return None
    
    def extract_caracs(self, annonce, base):
        info = annonce.css('.li-list-item-info-span').get()
        if not info:
            return
        
        patterns = {
            'chambres': r'(\d+)\s*<span[^>]*>Chambres',
            'salles_bain': r'(\d+)\s*<span[^>]*>Salle de bain',
            'pieces': r'(\d+)\s*<span[^>]*>Piéces',
            'surface_habitable': r'(\d+)<b[^>]*>m²</b>\s*<span[^>]*>Surf habitable',
            'surface_terrain': r'(\d+)<b[^>]*>m²</b>\s*<span[^>]*>Surf terrain'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, info)
            if match:
                base[key] = float(match.group(1)) if 'surface' in key else int(match.group(1))
    
    def extract_details(self, response, item):
        for detail in response.css('.block-detail .block-over'):
            text = detail.get()
            if not text:
                continue
            
            if 'Surf habitable' in text and not item.get('surface_habitable'):
                match = re.search(r'<strong>(\d+)\s*m²', text)
                if match:
                    item['surface_habitable'] = float(match.group(1))
            elif 'Surf terrain' in text and not item.get('surface_terrain'):
                match = re.search(r'<strong>(\d+)\s*m²', text)
                if match:
                    item['surface_terrain'] = float(match.group(1))
            elif 'Chambres' in text and not item.get('chambres'):
                match = re.search(r'<strong>(\d+)', text)
                if match:
                    item['chambres'] = int(match.group(1))
            elif 'Salle de bain' in text and not item.get('salles_bain'):
                match = re.search(r'<strong>(\d+)', text)
                if match:
                    item['salles_bain'] = int(match.group(1))
            elif 'Piéces' in text and not item.get('pieces'):
                match = re.search(r'<strong>(\d+)', text)
                if match:
                    item['pieces'] = int(match.group(1))
    
    def extract_vendeur(self, response, item):
        item['vendeur_nom'] = response.css('.right-bar-userinfo strong::text').get()
        item['vendeur_type'] = 'PRO' if response.css('.badge:contains("PRO")').get() else 'Particulier'
        
        tel = response.css('.block-2 i.fa-phone + ::text').get()
        if tel:
            item['vendeur_telephone'] = tel.strip()
        
        url_vendeur = response.css('.right-bar-userinfo a[href*="/agence/"], .right-bar-userinfo a[href*="/membre/"]::attr(href)').get()
        if url_vendeur:
            item['vendeur_url'] = response.urljoin(url_vendeur)
    
    def print_final_report(self):
        print("\n" + "="*60)
        print="📊 RAPPORT FINAL LOCATION"
        print("="*60)
        print(f"📄 Pages parcourues: {self.stats['pages_parcourues']}")
        print(f"🏠 Locations trouvées: {self.stats['annonces_trouvees']}")
        
        if self.stats['total_annonces_attendu']:
            print(f"🎯 Total attendu: {self.stats['total_annonces_attendu']}")
            if self.stats['annonces_trouvees'] == self.stats['total_annonces_attendu']:
                print("✅ SUCCÈS: Toutes les locations sont scrappées!")
        
        if self.stats['pages_parcourues'] > 0:
            print(f"📊 Moyenne: {self.stats['annonces_trouvees']/self.stats['pages_parcourues']:.1f} locations/page")
        print("="*60)