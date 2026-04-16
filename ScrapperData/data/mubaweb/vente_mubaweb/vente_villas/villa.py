"""
SCRAPER MUBAWAB ULTIMATE - VERSION VILLAS DE LUXE
Scraper intelligent pour villas avec détection automatique du nombre d'annonces
Régions: Hammamet, La Marsa, La Soukra, Ariana Ville, Djerba, El Menzah
Structure adaptée pour villas et maisons de luxe
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time
import os
import sys
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Optional, Tuple, Set
import logging
import random

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mubawab_villas_ultimate.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MubawabVillasUltimateScraper:
    """Scraper ULTIMATE pour villas de luxe - Structure adaptée"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    ]
    
    def __init__(self, delay: float = 1.0, timeout: int = 30):
        self.session = requests.Session()
        self.delay = delay
        self.timeout = timeout
        self.scraped_urls = set()
        self.scraped_ids = set()
        
        # Régions à scraper (URL format)
        self.regions_config = {
            'Hammamet': 'hammamet',
            'La Marsa': 'la-marsa',
            'La Soukra': 'la-soukra',
            'Ariana Ville': 'ariana-ville',
            'Djerba': 'djerba',
            'El Menzah': 'el-menzah'
        }
        
        # Type de bien = Villa de luxe
        self.property_type = 'villa-sale'
        
        self.stats = {
            'pages_scraped': 0,
            'listings_found': 0,
            'listings_scraped': 0,
            'errors': 0,
            'total_ads_detected': 0,
            'valid_cards_per_page': [],
            'invalid_cards_per_page': [],
            'regions_stats': {}
        }
        
        self._setup_session()
    
    def _setup_session(self):
        """Configure la session"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.mubawab.tn/'
        }
        
        headers['User-Agent'] = random.choice(self.USER_AGENTS)
        self.session.headers.update(headers)
        
        self.session.cookies.update({
            'country': 'TN',
            'language': 'fr'
        })
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Effectue une requête HTTP"""
        for attempt in range(max_retries):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, timeout=self.timeout, verify=True)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
                elif response.status_code == 429:
                    logger.warning("Trop de requêtes, pause de 20 secondes...")
                    time.sleep(20)
                
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1} échouée pour {url}: {e}")
                time.sleep(3)
        
        logger.error(f"Échec de toutes les tentatives pour {url}")
        return None
    
    def build_search_url(self, region: str, page: int = 1) -> str:
        """Construit l'URL de recherche pour une région (villas de luxe)"""
        base = "https://www.mubawab.tn"
        region_key = self.regions_config.get(region, region.lower().replace(' ', '-'))
        
        # Format spécifique pour villas de luxe
        if page == 1:
            return f"{base}/fr/st/{region_key}/villas-et-maisons-de-luxe-a-vendre"
        else:
            return f"{base}/fr/st/{region_key}/villas-et-maisons-de-luxe-a-vendre:p:{page}"
    
    def detect_total_ads_and_pages(self, url: str) -> Tuple[int, int, int]:
        """Détecte le nombre total d'annonces, pages et annonces par page"""
        try:
            logger.info(f"Détection pour: {url}")
            response = self.make_request(url)
            if not response:
                return 0, 0, 0
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Chercher le nombre total de résultats
            total_text = ""
            
            # Essayer plusieurs méthodes
            selectors = [
                ('span', {'id': 'numResults'}),
                ('span', {'class': 'resultNum'}),
                ('div', {'class': 'searchTitle'}),
                ('span', {'string': re.compile(r'\d+\s+résultats?', re.I)})
            ]
            
            for tag, attrs in selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    total_text = elem.get_text(strip=True)
                    if total_text:
                        break
            
            if not total_text:
                # Chercher dans tout le texte de la page
                all_text = soup.get_text()
                match = re.search(r'(\d+)\s+résultats?', all_text, re.I)
                if match:
                    total_text = match.group(0)
            
            # Extraire le nombre
            if total_text:
                match = re.search(r'(\d[\d\s]*)\s*résultats?', total_text, re.I)
                if match:
                    total_ads = int(match.group(1).replace(' ', ''))
                    logger.info(f"✅ Détecté: {total_ads} annonces au total")
                else:
                    total_ads = 0
            else:
                total_ads = 0
            
            # 2. Compter les annonces réelles sur la première page
            real_listings = self.count_real_listings_on_page(soup)
            ads_per_page = real_listings if real_listings > 0 else 20
            
            # 3. Calculer le nombre de pages
            if total_ads > 0 and ads_per_page > 0:
                pages = (total_ads // ads_per_page) + (1 if total_ads % ads_per_page > 0 else 0)
                logger.info(f"📊 Estimation: {pages} pages à {ads_per_page} annonces/page")
            else:
                # Estimer basé sur la pagination visible
                pagination = self.find_pagination(soup)
                if pagination:
                    max_page = self.extract_max_page_from_pagination(pagination)
                    if max_page > 0:
                        pages = max_page
                        if total_ads == 0:
                            total_ads = pages * ads_per_page
                    else:
                        pages = 1
                else:
                    pages = 1
            
            return total_ads, pages, ads_per_page
            
        except Exception as e:
            logger.error(f"❌ Erreur détection: {e}")
            return 0, 10, 20
    
    def count_real_listings_on_page(self, soup: BeautifulSoup) -> int:
        """Compte les vraies annonces sur une page"""
        try:
            # Méthode 1: Chercher les vrais conteneurs d'annonces
            listing_boxes = soup.find_all('div', class_='listingBox')
            if listing_boxes:
                return len(listing_boxes)
            
            # Méthode 2: Chercher par structure spécifique villa
            cards = []
            
            # Chercher toutes les divs avec du contenu
            for div in soup.find_all('div', class_=re.compile(r'col-\d+')):
                # Vérifier si c'est une annonce de villa
                text = div.get_text()
                if ('villa' in text.lower() or 'maison' in text.lower() or 'chambre' in text.lower()) and ('DT' in text or 'TND' in text or 'prix' in text.lower()):
                    # Vérifier la structure
                    has_title = div.find(['h2', 'h3', 'h4'], class_=re.compile(r'listingTit|title', re.I))
                    has_price = div.find('span', class_='priceTag')
                    if has_title or has_price:
                        cards.append(div)
            
            if cards:
                return len(cards)
            
            # Méthode 3: Compter par structure de grille
            grid_items = soup.find_all('div', class_=re.compile(r'(listingBox|search-listing|property-item)'))
            return len(grid_items) if grid_items else 0
            
        except Exception as e:
            logger.error(f"Erreur comptage annonces: {e}")
            return 0
    
    def find_pagination(self, soup: BeautifulSoup):
        """Trouve la pagination"""
        pagination_selectors = [
            ('nav', {'class': 'pagination'}),
            ('div', {'class': 'pagination'}),
            ('ul', {'class': 'pagination'}),
            ('div', {'class': lambda x: x and 'pagin' in str(x).lower()}),
            ('ul', {'class': lambda x: x and 'pagin' in str(x).lower()}),
            ('div', {'class': 'paginationContainer'})
        ]
        
        for tag, attrs in pagination_selectors:
            pagination = soup.find(tag, attrs)
            if pagination:
                return pagination
        
        return None
    
    def extract_max_page_from_pagination(self, pagination) -> int:
        """Extrait le numéro de page maximum"""
        try:
            page_numbers = []
            
            # Chercher dans les liens
            page_links = pagination.find_all('a', href=True)
            for link in page_links:
                href = link.get('href', '')
                
                # Extraire le numéro de page de l'URL
                patterns = [
                    r'[:=]p[:=](\d+)',
                    r'page[=_](\d+)',
                    r'/p/(\d+)',
                    r'page-(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, href)
                    if match:
                        page_numbers.append(int(match.group(1)))
                        break
                
                # Extraire du texte
                text = link.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            # Chercher dans les spans
            all_spans = pagination.find_all('span')
            for span in all_spans:
                text = span.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            if page_numbers:
                max_page = max(page_numbers)
                logger.info(f"Pages trouvées dans pagination: max={max_page}")
                return max_page
            
        except Exception as e:
            logger.error(f"Erreur extraction pages: {e}")
        
        return 0
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', str(text).strip())
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return text
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extrait le prix d'une villa"""
        if not text:
            return None
        
        text = self.clean_text(text).lower()
        
        # Phrases qui indiquent "prix à consulter"
        if any(phrase in text for phrase in ['à consulter', 'sur demande', 'négociable', 'prix sur demande']):
            return None
        
        # Chercher prix en TND/DT
        patterns = [
            r'([\d\s\.]+)\s*(?:tnd|dt|dinars?)\b',
            r'prix\s*[:\-]?\s*([\d\s\.]+)\s*(?:tnd|dt)',
            r'([\d\s\.]+)\s*mille\s*(?:tnd|dt|dinars?)',
            r'([\d\s\.]+)\s*million\s*(?:tnd|dt|dinars?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(' ', '').replace('.', '')
                    if price_str.isdigit():
                        price = float(price_str)
                        # Filtre de validité pour villas (100,000 à 50 millions)
                        if 100000 <= price <= 50000000:
                            return price
                except:
                    continue
        
        return None
    
    def extract_price_per_m2(self, text: str) -> Optional[float]:
        """Extrait le prix au m² pour villas"""
        if not text:
            return None
        
        text = self.clean_text(text).lower()
        
        patterns = [
            r'([\d\s\.]+)\s*(?:dt|tnd|dinars?)\s*[\/\s]\s*m[²2]',
            r'([\d\s\.]+)\s*(?:dt|tnd|dinars?).*?m[²2]',
            r'prix.*?([\d\s\.]+)\s*(?:dt|tnd|dinars?).*?m[²2]',
            r'([\d\s\.]+)\s*dt.*?mètre'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(' ', '').replace(',', '.')
                    # Gérer les décimales
                    if '.' in price_str:
                        parts = price_str.split('.')
                        if len(parts) == 2 and len(parts[1]) > 2:
                            price_str = parts[0] + parts[1][:2]
                    return float(price_str)
                except:
                    continue
        
        return None
    
    def extract_surface(self, text: str) -> Optional[float]:
        """Extrait la surface d'une villa"""
        if not text:
            return None
        
        patterns = [
            r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]',
            r'superficie\s*[:\-]?\s*(\d+(?:[,\s]\d+)*)',
            r'(\d+(?:[,\s]\d+)*)\s*mètre',
            r'(\d+)\s*m\b',
            r'surface\s*[:\-]?\s*(\d+(?:[,\s]\d+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    surface_str = match.group(1).replace(' ', '').replace(',', '.')
                    # Nettoyer la chaîne
                    if surface_str.endswith('.'):
                        surface_str = surface_str[:-1]
                    return float(surface_str)
                except:
                    continue
        
        return None
    
    def extract_rooms(self, text: str) -> Optional[int]:
        """Extrait le nombre de pièces"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*pi[èe]ces?',
            r'(\d+)\s*pce',
            r'(\d+)\s*pièces',
            r'(\d+)\s*chambres?',
            r'(\d+)\s*chbr'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    rooms = int(match.group(1))
                    return rooms
                except:
                    continue
        
        return None
    
    def extract_bedrooms(self, text: str) -> Optional[int]:
        """Extrait le nombre de chambres"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*chambres?',
            r'(\d+)\s*chbr',
            r'(\d+)\s*bedrooms?',
            r'(\d+)\s*ch.'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    bedrooms = int(match.group(1))
                    return bedrooms
                except:
                    continue
        
        return None
    
    def extract_bathrooms(self, text: str) -> Optional[int]:
        """Extrait le nombre de salles de bain"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*salles?\s*de?\s*bain',
            r'(\d+)\s*sdb',
            r'(\d+)\s*bathrooms?',
            r'(\d+)\s*s\.?\s*b\.?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    bathrooms = int(match.group(1))
                    return bathrooms
                except:
                    continue
        
        return None
    
    def extract_villa_type(self, text: str) -> str:
        """Détermine le type de villa"""
        if not text:
            return "Villa"
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['luxe', 'luxueuse', 'prestige', 'haut standing', 'haute standing']):
            return "Villa de Luxe"
        elif any(word in text_lower for word in ['moderne', 'contemporaine', 'design', 'architecte']):
            return "Villa Moderne"
        elif any(word in text_lower for word in ['traditionnelle', 'arabe', 'mauresque', 'andalouse']):
            return "Villa Traditionnelle"
        elif any(word in text_lower for word in ['pleine mer', 'bord de mer', 'vue mer', 'plage']):
            return "Villa Vue Mer"
        elif any(word in text_lower for word in ['rez-de-jardin', 'plain-pied', 'un étage']):
            return "Villa Plain-pied"
        elif any(word in text_lower for word in ['étages', 'duplex', 'triplex']):
            return "Villa à Étages"
        elif any(word in text_lower for word in ['clos', 'murée', 'privée']):
            return "Villa Clos"
        else:
            return "Villa"
    
    def extract_id_from_url(self, url: str) -> Optional[str]:
        """Extrait l'ID de l'URL"""
        if not url:
            return None
        
        patterns = [
            r'/a/(\d+)/',
            r'/p/(\d+)/',
            r'id[=_](\d+)',
            r'/(\d{6,})/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def find_all_listing_cards(self, soup: BeautifulSoup) -> List:
        """Trouve TOUTES les cartes d'annonces de villas"""
        cards = []
        
        # 1. Structure principale Mubawab
        listing_boxes = soup.find_all('div', class_='listingBox')
        if listing_boxes:
            cards.extend(listing_boxes)
            logger.debug(f"{len(listing_boxes)} listingBox trouvés")
        
        # 2. Recherche par structure de carte
        card_selectors = [
            ('div', {'class': 'search-listing'}),
            ('div', {'class': 'property-item'}),
            ('div', {'class': 'listing-item'}),
            ('div', {'class': 'ad-container'}),
            ('div', {'class': 'col-6'})  # Structure de grille
        ]
        
        for tag, attrs in card_selectors:
            elements = soup.find_all(tag, attrs)
            for elem in elements:
                # Vérifier que c'est une annonce de villa
                text = elem.get_text()
                if (('villa' in text.lower() or 'maison' in text.lower()) and 
                    ('m²' in text or 'chambre' in text.lower() or 'DT' in text or 'TND' in text)) and elem not in cards:
                    cards.append(elem)
        
        # Filtrer les doublons
        unique_cards = []
        seen = set()
        for card in cards:
            card_str = str(card)[:500]  # Prendre un hash partiel
            if card_str not in seen:
                seen.add(card_str)
                unique_cards.append(card)
        
        logger.info(f"Total cartes uniques trouvées: {len(unique_cards)}")
        return unique_cards
    
    def validate_listing_card(self, card) -> bool:
        """Valide si une carte est une vraie annonce de villa"""
        try:
            text = card.get_text()
            text_lower = text.lower()
            
            # Critères pour une villa
            is_villa = 'villa' in text_lower or 'maison' in text_lower
            has_rooms_or_surface = ('m²' in text or 'chambre' in text_lower or 'pièce' in text_lower)
            has_price_marker = any(marker in text for marker in ['DT', 'TND', 'dinars', 'prix'])
            
            # Vérifier la structure
            has_title = bool(card.find(['h2', 'h3', 'h4'], class_=re.compile(r'listingTit|title', re.I)))
            has_link = bool(card.find('a', href=re.compile(r'/a/|/p/|/st/')))
            has_location = bool(card.find('span', class_='listingH3')) or bool(card.find('i', class_='icon-location'))
            
            # Score de validation
            score = 0
            if is_villa:
                score += 2
            if has_rooms_or_surface:
                score += 1
            if has_price_marker:
                score += 1
            if has_title:
                score += 1
            if has_link:
                score += 1
            if has_location:
                score += 1
            
            return score >= 4  # Au moins 4 points sur 6
            
        except Exception as e:
            logger.debug(f"Erreur validation carte: {e}")
            return False
    
    def parse_listing_card(self, card) -> Optional[Dict]:
        """Parse une carte d'annonce de villa"""
        try:
            # Valider d'abord
            if not self.validate_listing_card(card):
                return None
            
            data = {
                'id': '',
                'titre': '',
                'url': '',
                'prix': 0,
                'prix_text': '',
                'prix_m2': 0,
                'surface': 0,
                'surface_terrain': 0,
                'surface_text': '',
                'nombre_pieces': 0,
                'nombre_chambres': 0,
                'nombre_sdb': 0,
                'ville': '',
                'region': '',
                'quartier': '',
                'adresse': '',
                'type_villa': 'Villa',
                'style_architectural': '',
                'niveau_standing': '',
                'annee_construction': '',
                'etat_bien': '',
                'description_courte': '',
                'equipements': [],
                'amenities': [],
                'date_scraping': datetime.now().isoformat(),
                'page_source': 'search',
                'is_valid': True
            }
            
            # URL et ID
            links = card.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/a/' in href or '/p/' in href:
                    full_url = urljoin('https://www.mubawab.tn', href)
                    data['url'] = full_url
                    data['id'] = self.extract_id_from_url(full_url)
                    
                    # Titre depuis le lien
                    title_text = link.get_text(strip=True)
                    if title_text and len(title_text) > 5:
                        data['titre'] = self.clean_text(title_text)
                    break
            
            # Si pas de titre depuis le lien
            if not data['titre']:
                titles = card.find_all(['h2', 'h3', 'h4', 'h5'])
                for title in titles:
                    title_text = title.get_text(strip=True)
                    if title_text and len(title_text) > 5:
                        data['titre'] = self.clean_text(title_text)
                        break
            
            # Texte complet de la carte
            all_text = card.get_text()
            text_lower = all_text.lower()
            
            # Prix
            price_selectors = [
                ('span', {'class': 'priceTag'}),
                ('div', {'class': 'priceBar'}),
                ('span', {'class': lambda x: x and 'price' in str(x).lower()}),
                ('div', {'class': lambda x: x and 'price' in str(x).lower()})
            ]
            
            for tag, attrs in price_selectors:
                price_elem = card.find(tag, attrs)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text:
                        data['prix_text'] = price_text
                        data['prix'] = self.extract_price(price_text) or 0
                        break
            
            # Localisation
            location_selectors = [
                ('span', {'class': 'listingH3'}),
                ('div', {'class': 'contactBar'}),
                ('span', {'class': lambda x: x and 'location' in str(x).lower()}),
                ('i', {'class': 'icon-location'})
            ]
            
            for tag, attrs in location_selectors:
                location_elem = card.find(tag, attrs)
                if location_elem:
                    # Si c'est une icône, prendre le texte parent
                    if tag == 'i':
                        parent = location_elem.parent
                        if parent:
                            location_text = parent.get_text(strip=True)
                    else:
                        location_text = location_elem.get_text(strip=True)
                    
                    if location_text:
                        data['adresse'] = self.clean_text(location_text)
                        
                        # Extraire ville et quartier
                        if ',' in location_text:
                            parts = location_text.split(',')
                            if len(parts) > 1:
                                data['quartier'] = parts[0].strip()
                                data['ville'] = parts[1].strip()
                            else:
                                data['ville'] = parts[0].strip()
                        else:
                            data['ville'] = location_text.strip()
                        break
            
            # Caractéristiques détaillées (spécifiques aux villas)
            features_div = card.find('div', class_='adDetails')
            if features_div:
                features = features_div.find_all('div', class_='adDetailFeature')
                for feature in features:
                    icon = feature.find('i')
                    value_span = feature.find('span')
                    
                    if icon and value_span:
                        icon_class = ' '.join(icon.get('class', []))
                        value = value_span.get_text(strip=True)
                        
                        # Surface
                        if 'icon-triangle' in icon_class or 'm²' in value or 'm2' in value:
                            data['surface_text'] = value
                            data['surface'] = self.extract_surface(value) or 0
                        
                        # Pièces
                        elif 'icon-house-boxes' in icon_class:
                            data['nombre_pieces'] = self.extract_rooms(value) or 0
                        
                        # Chambres
                        elif 'icon-bed' in icon_class:
                            data['nombre_chambres'] = self.extract_bedrooms(value) or 0
                        
                        # Salles de bain
                        elif 'icon-bath' in icon_class:
                            data['nombre_sdb'] = self.extract_bathrooms(value) or 0
            
            # Si surface non trouvée, chercher dans tout le texte
            if data['surface'] == 0:
                surface_match = re.search(r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]', all_text)
                if surface_match:
                    data['surface_text'] = surface_match.group(0)
                    data['surface'] = self.extract_surface(surface_match.group(0)) or 0
            
            # Si pièces/chambres/sdb non trouvées
            if data['nombre_pieces'] == 0:
                data['nombre_pieces'] = self.extract_rooms(all_text) or 0
            if data['nombre_chambres'] == 0:
                data['nombre_chambres'] = self.extract_bedrooms(all_text) or 0
            if data['nombre_sdb'] == 0:
                data['nombre_sdb'] = self.extract_bathrooms(all_text) or 0
            
            # Surface du terrain
            if data['surface'] > 0:
                # Chercher surface terrain séparément
                terrain_match = re.search(r'terrain\s*[:\-]?\s*(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]', all_text, re.I)
                if terrain_match:
                    data['surface_terrain'] = self.extract_surface(terrain_match.group(0)) or 0
                else:
                    # Si pas de terrain spécifié, on suppose que c'est la même surface
                    data['surface_terrain'] = data['surface']
            
            # Prix au m²
            data['prix_m2'] = self.extract_price_per_m2(all_text) or 0
            
            # Si pas de prix au m² mais on a prix et surface
            if data['prix_m2'] == 0 and data['prix'] > 0 and data['surface'] > 0:
                try:
                    data['prix_m2'] = data['prix'] / data['surface']
                except:
                    pass
            
            # Type de villa
            data['type_villa'] = self.extract_villa_type(all_text)
            
            # Style architectural
            if 'moderne' in text_lower or 'contemporain' in text_lower:
                data['style_architectural'] = 'Moderne'
            elif 'traditionnel' in text_lower or 'arabe' in text_lower or 'mauresque' in text_lower:
                data['style_architectural'] = 'Traditionnel'
            elif 'classique' in text_lower or 'européen' in text_lower:
                data['style_architectural'] = 'Classique'
            
            # Niveau de standing
            if any(word in text_lower for word in ['luxe', 'prestige', 'haut standing', 'haute standing']):
                data['niveau_standing'] = 'Luxe'
            elif any(word in text_lower for word in ['moyen standing', 'bon standing']):
                data['niveau_standing'] = 'Moyen'
            else:
                data['niveau_standing'] = 'Standard'
            
            # État du bien
            if any(word in text_lower for word in ['neuf', 'nouveau', 'jamais habité']):
                data['etat_bien'] = 'Neuf'
            elif any(word in text_lower for word in ['bon état', 'excellent état', 'très bon état']):
                data['etat_bien'] = 'Bon état'
            elif any(word in text_lower for word in ['à rénover', 'rénovation']):
                data['etat_bien'] = 'À rénover'
            else:
                data['etat_bien'] = 'Non spécifié'
            
            # Description courte
            desc_elements = card.find_all(['p', 'div'], class_=['listingP', 'descLi', 'description'])
            for elem in desc_elements:
                desc_text = elem.get_text(strip=True)
                if desc_text and len(desc_text) > 10:
                    data['description_courte'] = self.clean_text(desc_text[:300])
                    break
            
            # Si pas de description dans les éléments spécifiques
            if not data['description_courte']:
                # Prendre un extrait du texte
                paragraphs = re.split(r'[.!?]', all_text)
                for para in paragraphs:
                    if len(para) > 30 and ('villa' in para.lower() or 'maison' in para.lower() or 'chambre' in para.lower()):
                        data['description_courte'] = self.clean_text(para[:300])
                        break
            
            # Équipements et amenities
            equip_list = []
            amenities_list = []
            
            # Chercher les icônes d'équipements
            equip_icons = card.find_all('div', class_='adFeature')
            for equip in equip_icons:
                icon = equip.find('i')
                text_elem = equip.find('span', class_='fSize11')
                if icon and text_elem:
                    equip_text = text_elem.get_text(strip=True)
                    if equip_text:
                        amenities_list.append(equip_text)
            
            # Mapping des équipements spécifiques aux villas
            equip_mapping = {
                'jardin': 'Jardin',
                'terrasse': 'Terrasse',
                'garage': 'Garage',
                'piscine': 'Piscine',
                'vue sur mer': 'Vue sur mer',
                'vue mer': 'Vue sur mer',
                'concierge': 'Concierge',
                'chambre rangement': 'Chambre de rangement',
                'chauffage': 'Chauffage',
                'chauffage central': 'Chauffage central',
                'climatisation': 'Climatisation',
                'air conditionné': 'Climatisation',
                'cuisine équipée': 'Cuisine équipée',
                'double vitrage': 'Double vitrage',
                'porte blindée': 'Porte blindée',
                'sécurité': 'Système de sécurité',
                'alarme': 'Système d\'alarme',
                'gaz de ville': 'Gaz de ville',
                'fibre optique': 'Fibre optique',
                'ascenseur': 'Ascenseur',
                'sauna': 'Sauna',
                'jacuzzi': 'Jacuzzi',
                'home cinéma': 'Home cinéma',
                'véranda': 'Véranda',
                'barbecue': 'Barbecue',
                'éclairage extérieur': 'Éclairage extérieur',
                'portail électrique': 'Portail électrique'
            }
            
            for fr_key, fr_text in equip_mapping.items():
                if fr_key in text_lower:
                    equip_list.append(fr_text)
            
            data['equipements'] = equip_list
            data['amenities'] = amenities_list
            
            # Année de construction (approximative)
            year_match = re.search(r'(?:construite?|année)\s*(?:en|:)?\s*(\d{4})', all_text, re.I)
            if year_match:
                data['annee_construction'] = year_match.group(1)
            
            # Validation finale
            if not data['url'] or not data['titre']:
                data['is_valid'] = False
                return None
            
            # Vérifier que c'est bien une villa/maison
            if data['nombre_chambres'] == 0 and 'villa' not in text_lower and 'maison' not in text_lower:
                data['is_valid'] = False
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Erreur parsing carte villa: {e}")
            return None
    
    def scrape_page_listings(self, url: str, page_num: int) -> Tuple[List[Dict], bool, Optional[str], int]:
        """Scrape toutes les annonces d'une page"""
        listings = []
        has_next = False
        next_url = None
        next_page_num = page_num + 1
        
        try:
            logger.info(f"📄 SCRAPING PAGE {page_num}: {url}")
            
            response = self.make_request(url)
            if not response:
                return [], False, None, next_page_num
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver les cartes
            cards = self.find_all_listing_cards(soup)
            logger.info(f"Page {page_num}: {len(cards)} cartes trouvées")
            
            # Parser et valider
            valid_count = 0
            invalid_count = 0
            
            for i, card in enumerate(cards):
                try:
                    listing_data = self.parse_listing_card(card)
                    
                    if listing_data and listing_data.get('is_valid', False):
                        listing_url = listing_data.get('url', '')
                        listing_id = listing_data.get('id', '')
                        
                        # Vérifier doublons
                        if listing_url and listing_url not in self.scraped_urls:
                            self.scraped_urls.add(listing_url)
                            if listing_id:
                                self.scraped_ids.add(listing_id)
                            
                            listings.append(listing_data)
                            valid_count += 1
                            self.stats['listings_found'] += 1
                            
                            if valid_count % 5 == 0:
                                logger.debug(f"  {valid_count} annonces valides")
                        else:
                            invalid_count += 1
                            logger.debug(f"  Doublon ou invalide: {listing_url}")
                    else:
                        invalid_count += 1
                        
                except Exception as e:
                    invalid_count += 1
                    logger.debug(f"Erreur carte {i}: {e}")
                    continue
            
            # Statistiques
            self.stats['valid_cards_per_page'].append(valid_count)
            self.stats['invalid_cards_per_page'].append(invalid_count)
            
            logger.info(f"✅ PAGE {page_num}: {valid_count} annonces valides, {invalid_count} invalides")
            
            # Trouver la page suivante
            # Méthode 1: Chercher le lien "suivant"
            next_link = soup.find('a', class_='next')
            if not next_link:
                next_link = soup.find('a', string=re.compile(r'suivant|next', re.I))
            
            if next_link and next_link.get('href'):
                href = next_link.get('href')
                next_url = urljoin('https://www.mubawab.tn', href)
                
                # Extraire le numéro de page
                match = re.search(r'[:=]p[:=](\d+)', next_url)
                if match:
                    next_page_num = int(match.group(1))
                
                has_next = True
                logger.info(f"↪️  Lien suivant trouvé: page {next_page_num}")
            else:
                # Méthode 2: Construire l'URL suivante
                if ':p:' in url:
                    next_url = re.sub(r':p:(\d+)', f':p:{next_page_num}', url)
                else:
                    next_url = f"{url}:p:{next_page_num}"
                
                # Vérifier si on dépasse le nombre estimé de pages
                # (sera vérifié au prochain tour)
                has_next = True
            
            self.stats['pages_scraped'] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping page {page_num}: {e}")
            self.stats['errors'] += 1
        
        return listings, has_next, next_url, next_page_num
    
    def scrape_detailed_listing(self, url: str) -> Dict:
        """Scrape les détails complets d'une villa depuis sa page"""
        details = {
            'description_complete': '',
            'caracteristiques': {},
            'caracteristiques_detaillees': {},
            'equipements_detaille': [],
            'amenities_detaille': [],
            'images': [],
            'localisation': {},
            'informations_supplementaires': {},
            'contact_info': {},
            'scraping_timestamp_detail': datetime.now().isoformat()
        }
        
        try:
            time.sleep(0.5)  # Pause pour éviter le blocage
            response = self.make_request(url)
            if not response:
                return details
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Description complète
            desc_div = soup.find('div', class_='blockProp')
            if desc_div:
                paragraphs = desc_div.find_all('p')
                description = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                details['description_complete'] = self.clean_text(description)
            
            # Caractéristiques principales (bloc à gauche)
            caract_block = soup.find('div', class_='caractBlockProp')
            if caract_block:
                # Caractéristiques principales (adMainFeature)
                main_features = caract_block.find_all('div', class_='adMainFeature')
                for feature in main_features:
                    label = feature.find('p', class_='adMainFeatureContentLabel')
                    value = feature.find('p', class_='adMainFeatureContentValue')
                    if label and value:
                        label_text = label.get_text(strip=True).lower()
                        value_text = value.get_text(strip=True)
                        details['caracteristiques'][label_text] = value_text
                
                # Caractéristiques détaillées (adFeature avec valeurs)
                detail_features = caract_block.find_all('div', class_='adFeature')
                for feature in detail_features:
                    # Chercher s'il y a un label et une valeur
                    label = feature.find('span', class_='adFeatureLabel')
                    value = feature.find('span', class_='adFeatureValue')
                    if label and value:
                        label_text = label.get_text(strip=True)
                        value_text = value.get_text(strip=True)
                        details['caracteristiques_detaillees'][label_text] = value_text
                    else:
                        # Sinon prendre tout le texte
                        text = feature.get_text(strip=True)
                        if text:
                            details['amenities_detaille'].append(text)
            
            # Images
            img_tags = soup.find_all('img', src=re.compile(r'mubawab-media\.com'))
            for img in img_tags[:20]:  # Limiter à 20 images
                src = img.get('src')
                if src and src not in details['images']:
                    details['images'].append(src)
            
            # Localisation (coordonnées)
            lat_input = soup.find('input', id='latField')
            lng_input = soup.find('input', id='lngField')
            
            if lat_input:
                details['localisation']['latitude'] = lat_input.get('value', '')
            if lng_input:
                details['localisation']['longitude'] = lng_input.get('value', '')
            
            # Adresse textuelle
            address_div = soup.find('div', class_='greyTit')
            if address_div:
                details['localisation']['adresse'] = address_div.get_text(strip=True)
            
            # Informations supplémentaires depuis le texte complet
            full_text = soup.get_text().lower()
            
            # Équipements spécifiques
            equip_list = []
            equip_mapping_villa = {
                'piscine': 'Piscine',
                'jacuzzi': 'Jacuzzi',
                'sauna': 'Sauna',
                'hammam': 'Hammam',
                'home cinéma': 'Home cinéma',
                'salle de sport': 'Salle de sport',
                'cave à vin': 'Cave à vin',
                'buanderie': 'Buanderie',
                'cellier': 'Cellier',
                'véranda': 'Véranda',
                'portail électrique': 'Portail électrique',
                'interphone': 'Interphone',
                'visiophone': 'Visiophone',
                'alarme': 'Système d\'alarme',
                'vidéosurveillance': 'Vidéosurveillance',
                'gaz de ville': 'Gaz de ville',
                'chauffe-eau solaire': 'Chauffe-eau solaire',
                'panneau solaire': 'Panneaux solaires',
                'puits': 'Puits',
                'forage': 'Forage',
                'réseau irrigation': 'Réseau d\'irrigation',
                'éclairage extérieur': 'Éclairage extérieur',
                'arrosage automatique': 'Arrosage automatique'
            }
            
            for fr_key, fr_text in equip_mapping_villa.items():
                if fr_key in full_text:
                    equip_list.append(fr_text)
            
            details['equipements_detaille'] = equip_list
            
            # Informations sur le jardin
            if 'jardin' in full_text:
                if 'paysager' in full_text:
                    details['informations_supplementaires']['type_jardin'] = 'Jardin paysager'
                elif 'potager' in full_text:
                    details['informations_supplementaires']['type_jardin'] = 'Jardin potager'
                elif 'arbres fruitiers' in full_text or 'oliviers' in full_text:
                    details['informations_supplementaires']['type_jardin'] = 'Avec arbres fruitiers'
                else:
                    details['informations_supplementaires']['type_jardin'] = 'Jardin'
            
            # Nombre d'étages
            if 'étage' in full_text or 'niveau' in full_text:
                etage_match = re.search(r'(\d+)\s*(?:étages?|niveaux?)', full_text)
                if etage_match:
                    details['informations_supplementaires']['nombre_etages'] = etage_match.group(1)
            
            # Année de construction précise
            year_match = re.search(r'(?:construite?|année|date.*construction)\s*(?:en|:)?\s*(\d{4})', full_text, re.I)
            if year_match:
                details['informations_supplementaires']['annee_construction'] = year_match.group(1)
            
            # Type de chauffage
            if 'chauffage' in full_text:
                if 'central' in full_text:
                    details['informations_supplementaires']['type_chauffage'] = 'Chauffage central'
                elif 'gaz' in full_text:
                    details['informations_supplementaires']['type_chauffage'] = 'Chauffage au gaz'
                elif 'électrique' in full_text:
                    details['informations_supplementaires']['type_chauffage'] = 'Chauffage électrique'
                elif 'sol' in full_text:
                    details['informations_supplementaires']['type_chauffage'] = 'Chauffage au sol'
            
            # Informations de contact (agence)
            agence_div = soup.find('div', class_='agencyName')
            if agence_div:
                details['contact_info']['agence'] = agence_div.get_text(strip=True)
            
            # Téléphone (crypté dans la page)
            phone_links = soup.find_all('a', onclick=re.compile(r'sendPhoneLead|showPhone'))
            if phone_links:
                details['contact_info']['telephone_disponible'] = 'Oui'
            
            # Nombre de photos
            num_pics = soup.find('div', class_='numPics')
            if num_pics:
                num_text = num_pics.find('span')
                if num_text:
                    details['informations_supplementaires']['nombre_photos'] = num_text.get_text(strip=True)
            
            # Date de publication approximative
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if 'datePublished' in json_data:
                        details['informations_supplementaires']['date_publication'] = json_data['datePublished']
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Erreur détails {url}: {e}")
        
        return details
    
    def scrape_region_ads(self, region: str, max_ads: int, get_details: bool) -> List[Dict]:
        """Scrape toutes les annonces d'une région"""
        logger.info(f"🚀 DÉBUT SCRAPING RÉGION: {region}")
        
        all_listings = []
        
        # Détection initiale
        first_url = self.build_search_url(region, 1)
        total_ads, total_pages, ads_per_page = self.detect_total_ads_and_pages(first_url)
        
        if total_ads == 0:
            logger.warning(f"⚠️  AUCUNE ANNONCE DÉTECTÉE POUR {region}")
            return []
        
        self.stats['total_ads_detected'] += total_ads
        
        # Calculer combien scraper pour cette région
        region_max_ads = max_ads if max_ads > 0 else total_ads
        pages_to_scrape = (region_max_ads // ads_per_page) + (1 if region_max_ads % ads_per_page > 0 else 0)
        pages_to_scrape = min(pages_to_scrape, total_pages)
        
        logger.info(f"📊 {region}: {total_ads} annonces détectées")
        logger.info(f"📄 Objectif: {region_max_ads} annonces sur {pages_to_scrape}/{total_pages} pages")
        logger.info(f"📈 Estimation: {ads_per_page} annonces par page")
        
        # Scraper page par page
        current_page = 1
        current_url = first_url
        region_ads_scraped = 0
        consecutive_empty_pages = 0
        region_errors = 0
        
        while (current_page <= pages_to_scrape and 
               region_ads_scraped < region_max_ads and 
               consecutive_empty_pages < 2):
            
            try:
                print(f"\n{'='*50}")
                print(f"📍 {region.upper()} - Page {current_page}/{pages_to_scrape}")
                print(f"📊 Progression: {region_ads_scraped}/{region_max_ads} annonces")
                print(f"{'='*50}")
                
                # Scraper la page
                page_listings, has_next, next_url, next_page_num = self.scrape_page_listings(
                    current_url, current_page
                )
                
                # Vérifier si la page est vide
                if not page_listings:
                    logger.warning(f"⚠️  PAGE {current_page} VIDE pour {region}")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= 2:
                        logger.error(f"❌ 2 PAGES VIDES CONSÉCUTIVES - ARRÊT {region}")
                        break
                    
                    # Essayer la page suivante si disponible
                    if has_next and next_url:
                        current_page = next_page_num
                        current_url = next_url
                        time.sleep(3)
                        continue
                    else:
                        break
                
                consecutive_empty_pages = 0  # Réinitialiser
                
                logger.info(f"✅ Page {current_page}: {len(page_listings)} annonces trouvées")
                
                # Ajouter les détails si demandé
                if get_details and page_listings:
                    logger.info(f"🔍 Extraction des détails pour {len(page_listings)} annonces...")
                    
                    total_details = len(page_listings)
                    for i, listing in enumerate(page_listings):
                        try:
                            if listing.get('url'):
                                details = self.scrape_detailed_listing(listing['url'])
                                
                                # Fusionner les données
                                listing.update({
                                    'description_complete': details.get('description_complete', ''),
                                    'caracteristiques': json.dumps(details.get('caracteristiques', {}), ensure_ascii=False),
                                    'caracteristiques_detaillees': json.dumps(details.get('caracteristiques_detaillees', {}), ensure_ascii=False),
                                    'equipements_detaille': '; '.join(details.get('equipements_detaille', [])),
                                    'amenities_detaille': '; '.join(details.get('amenities_detaille', [])),
                                    'images': '; '.join(details.get('images', [])[:15]),  # Limiter à 15 images
                                    'localisation': json.dumps(details.get('localisation', {}), ensure_ascii=False),
                                    'informations_supplementaires': json.dumps(details.get('informations_supplementaires', {}), ensure_ascii=False),
                                    'contact_info': json.dumps(details.get('contact_info', {}), ensure_ascii=False)
                                })
                                
                                # Afficher progression
                                if (i + 1) % 5 == 0 or (i + 1) == total_details:
                                    progress = ((i + 1) / total_details) * 100
                                    logger.info(f"  📊 Détails: {i+1}/{total_details} ({progress:.0f}%)")
                                
                                # Pause entre les détails
                                time.sleep(0.3)
                                
                        except Exception as e:
                            logger.warning(f"Erreur détails annonce {i}: {e}")
                            region_errors += 1
                            continue
                
                # Ajouter aux résultats
                all_listings.extend(page_listings)
                region_ads_scraped = len(all_listings)
                
                logger.info(f"📈 {region}: {region_ads_scraped}/{region_max_ads} annonces accumulées")
                
                # Vérifier si on continue
                if region_ads_scraped >= region_max_ads:
                    logger.info(f"🎯 OBJECTIF ATTEINT POUR {region}: {region_ads_scraped} annonces")
                    all_listings = all_listings[:region_max_ads]
                    break
                
                # Préparer la page suivante
                if has_next and next_url and current_page < pages_to_scrape:
                    current_page = next_page_num
                    current_url = next_url
                    
                    # Pause entre les pages
                    pause_time = 2 if current_page % 5 != 0 else 4
                    logger.info(f"⏳ Pause de {pause_time}s avant page {current_page}...")
                    time.sleep(pause_time)
                else:
                    logger.info(f"📄 DERNIÈRE PAGE ATTEINTE POUR {region}")
                    break
                
            except KeyboardInterrupt:
                logger.info("⏹️  INTERROMPU PAR UTILISATEUR")
                print(f"\n⚠️  SCRAPING {region} INTERROMPU - SAUVEGARDE...")
                break
            except Exception as e:
                logger.error(f"❌ ERREUR PAGE {current_page} {region}: {e}")
                region_errors += 1
                self.stats['errors'] += 1
                
                # Essayer de continuer
                if current_page < pages_to_scrape:
                    current_page += 1
                    current_url = self.build_search_url(region, current_page)
                    time.sleep(5)
                else:
                    break
        
        # Enregistrer les statistiques de la région
        self.stats['regions_stats'][region] = {
            'annonces_scrapees': len(all_listings),
            'annonces_detectees': total_ads,
            'pages_scrapees': current_page,
            'erreurs': region_errors
        }
        
        logger.info(f"✅ FIN SCRAPING {region}: {len(all_listings)} annonces")
        return all_listings
    
    def scrape_all_regions(self, max_ads_per_region: int = 0, get_details: bool = True) -> List[Dict]:
        """Scrape toutes les régions configurées"""
        logger.info(f"🚀 DÉBUT SCRAPING COMPLET - {len(self.regions_config)} RÉGIONS")
        
        all_listings = []
        
        for region_name in self.regions_config.keys():
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"🎯 DÉBUT RÉGION: {region_name}")
                logger.info(f"{'='*60}")
                
                # Scraper la région
                region_listings = self.scrape_region_ads(
                    region=region_name,
                    max_ads=max_ads_per_region,
                    get_details=get_details
                )
                
                all_listings.extend(region_listings)
                
                logger.info(f"✅ {region_name}: {len(region_listings)} annonces scrapées")
                
                # Pause entre les régions
                if region_name != list(self.regions_config.keys())[-1]:
                    pause = 5
                    logger.info(f"⏳ Pause de {pause}s avant région suivante...")
                    time.sleep(pause)
                    
            except Exception as e:
                logger.error(f"❌ ERREUR MAJEURE RÉGION {region_name}: {e}")
                self.stats['errors'] += 1
                continue
        
        self.stats['listings_scraped'] = len(all_listings)
        
        return all_listings
    
    def save_to_csv(self, listings: List[Dict], filename: str):
        """Sauvegarde en CSV"""
        if not listings:
            logger.warning("Aucune donnée à sauvegarder")
            return None
        
        try:
            # Préparer colonnes
            all_columns = set()
            for listing in listings:
                all_columns.update(listing.keys())
            
            # Ordre logique pour les villas
            preferred_order = [
                'id', 'titre', 'url', 'region', 'ville', 'quartier', 'adresse',
                'type_villa', 'style_architectural', 'niveau_standing', 'etat_bien',
                'prix', 'prix_text', 'prix_m2', 'surface', 'surface_terrain', 'surface_text',
                'nombre_pieces', 'nombre_chambres', 'nombre_sdb',
                'annee_construction', 'description_courte', 'description_complete',
                'equipements', 'amenities', 'equipements_detaille', 'amenities_detaille',
                'caracteristiques', 'caracteristiques_detaillees', 'images', 'localisation',
                'informations_supplementaires', 'contact_info',
                'date_scraping', 'page_source', 'is_valid'
            ]
            
            # Autres colonnes
            other_columns = sorted([col for col in all_columns if col not in preferred_order])
            columns = preferred_order + other_columns
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                
                for listing in listings:
                    row = {}
                    for col in columns:
                        value = listing.get(col, '')
                        
                        if isinstance(value, list):
                            row[col] = '; '.join(str(v) for v in value)
                        elif value is None:
                            row[col] = ''
                        else:
                            row[col] = str(value)
                    
                    writer.writerow(row)
            
            logger.info(f"✅ CSV SAUVEGARDÉ: {filename}")
            print(f"💾 Fichier CSV créé: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ ERREUR CSV: {e}")
            return None
    
    def save_to_json(self, listings: List[Dict], filename: str):
        """Sauvegarde en JSON"""
        if not listings:
            return None
        
        try:
            data = {
                'metadata': {
                    'date_export': datetime.now().isoformat(),
                    'total_listings': len(listings),
                    'regions': list(self.regions_config.keys()),
                    'property_type': 'villas-de-luxe',
                    'scraping_stats': self.stats,
                    'fields_count': len(listings[0]) if listings else 0
                },
                'listings': listings
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ JSON SAUVEGARDÉ: {filename}")
            print(f"📁 Fichier JSON créé: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ ERREUR JSON: {e}")
            return None
    
    def display_final_stats(self):
        """Affiche les statistiques finales du scraping"""
        print("\n" + "="*80)
        print("🏰 STATISTIQUES FINALES DU SCRAPING VILLAS DE LUXE")
        print("="*80)
        
        print(f"\n📍 RÉGIONS SCRAPÉES ({len(self.regions_config)}):")
        print(", ".join(self.regions_config.keys()))
        
        print(f"\n📈 PERFORMANCE GÉNÉRALE:")
        print(f"   Pages scrapées: {self.stats['pages_scraped']}")
        print(f"   Annonces détectées: {self.stats['total_ads_detected']}")
        print(f"   Annonces trouvées: {self.stats['listings_found']}")
        print(f"   Annonces finales: {self.stats['listings_scraped']}")
        print(f"   Erreurs: {self.stats['errors']}")
        
        if self.stats['valid_cards_per_page']:
            avg_valid = sum(self.stats['valid_cards_per_page']) / len(self.stats['valid_cards_per_page'])
            total_invalid = sum(self.stats['invalid_cards_per_page'])
            print(f"\n📈 QUALITÉ DU SCRAPING:")
            print(f"   Moyenne annonces/page: {avg_valid:.1f}")
            print(f"   Total éléments invalides: {total_invalid}")
            if self.stats['listings_found'] > 0:
                taux_valid = (self.stats['listings_found'] / (self.stats['listings_found'] + total_invalid)) * 100
                print(f"   Taux de validité: {taux_valid:.1f}%")
        
        if self.stats['regions_stats']:
            print(f"\n📍 STATISTIQUES PAR RÉGION:")
            for region, stats in self.stats['regions_stats'].items():
                taux = (stats['annonces_scrapees'] / stats['annonces_detectees'] * 100) if stats['annonces_detectees'] > 0 else 0
                print(f"   {region}:")
                print(f"     Scrapées: {stats['annonces_scrapees']}/{stats['annonces_detectees']} ({taux:.1f}%)")
                print(f"     Pages: {stats['pages_scrapees']}")
                print(f"     Erreurs: {stats['erreurs']}")
        
        print("\n" + "="*80)


def main():
    """Programme principal"""
    print("\n" + "="*80)
    print("🏰 SCRAPER MUBAWAB ULTIMATE - VILLAS DE LUXE")
    print("🎯 DÉTECTION AUTOMATIQUE - SPÉCIALISÉ POUR VILLAS")
    print("="*80)
    
    # Configuration
    print("\n📋 CONFIGURATION DU SCRAPING")
    
    # Choix du nombre d'annonces
    print("\n📊 NOMBRE D'ANNONCES PAR RÉGION:")
    print("  0. Toutes les annonces disponibles")
    print("  1. 50 annonces par région")
    print("  2. 100 annonces par région")
    print("  3. 200 annonces par région")
    print("  4. 500 annonces par région")
    print("  5. Personnalisé")
    
    ads_choice = input("\n🎯 Choisissez (0-5): ").strip()
    
    if ads_choice == '0':
        max_ads = 0  # Toutes
    elif ads_choice == '1':
        max_ads = 50
    elif ads_choice == '2':
        max_ads = 100
    elif ads_choice == '3':
        max_ads = 200
    elif ads_choice == '4':
        max_ads = 500
    elif ads_choice == '5':
        try:
            max_ads = int(input("Entrez le nombre d'annonces par région: "))
        except:
            max_ads = 100
    else:
        max_ads = 100
    
    # Détails
    details_choice = input("\n🔍 Extraire les détails complets? (o/n, recommandé: o): ").strip().lower()
    get_details = details_choice in ['o', 'oui', 'y', 'yes', '']
    
    # Résumé
    print("\n" + "="*80)
    print("🚀 RÉSUMÉ DE LA CONFIGURATION")
    print("="*80)
    print(f"   📍 Régions: {', '.join(['Hammamet', 'La Marsa', 'La Soukra', 'Ariana Ville', 'Djerba', 'El Menzah'])}")
    print(f"   🏰 Type: Villas et maisons de luxe à vendre")
    print(f"   📊 Nombre: {'TOUTES les annonces' if max_ads == 0 else max_ads} par région")
    print(f"   🔍 Détails: {'✅ OUI' if get_details else '❌ NON'}")
    print("="*80)
    
    if max_ads == 0 or max_ads > 200:
        print("⚠️  ATTENTION: Scraping long en cours!")
        print("   Toutes les pages seront traitées.")
        print("   Durée estimée: 20-60 minutes selon le nombre d'annonces.")
        print("="*80)
    
    # Confirmation
    confirm = input("\n✅ Démarrer le scraping? (O/n): ").strip().lower()
    if confirm in ['n', 'non', 'no']:
        print("❌ Annulé.")
        return
    
    # Lancement
    print(f"\n🚀 LANCEMENT DU SCRAPING...")
    print(f"📍 Régions: {len(['Hammamet', 'La Marsa', 'La Soukra', 'Ariana Ville', 'Djerba', 'El Menzah'])}")
    print(f"📁 Les fichiers seront sauvegardés dans le dossier courant")
    print(f"⏳ Veuillez patienter, cela peut prendre du temps...")
    print(f"📊 La détection automatique va calculer le nombre total d'annonces")
    
    try:
        scraper = MubawabVillasUltimateScraper(delay=0.8)
        
        start_time = datetime.now()
        listings = scraper.scrape_all_regions(max_ads, get_details)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        if listings:
            # Préparer fichiers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"mubawab_villas_luxe_complet_{timestamp}"
            
            # Sauvegarder
            csv_file = scraper.save_to_csv(listings, f"{base_name}.csv")
            json_file = scraper.save_to_json(listings, f"{base_name}.json")
            
            # Statistiques
            scraper.display_final_stats()
            
            print(f"\n💾 FICHIERS CRÉÉS:")
            if csv_file:
                csv_size = os.path.getsize(csv_file) / 1024
                print(f"   📄 CSV: {csv_file}")
                print(f"     Taille: {csv_size:.1f} KB")
                print(f"     Lignes: {len(listings)}")
                print(f"     Colonnes: {len(listings[0]) if listings else 0}")
            
            if json_file:
                json_size = os.path.getsize(json_file) / 1024
                print(f"   📁 JSON: {json_file}")
                print(f"     Taille: {json_size:.1f} KB")
            
            print(f"\n⏱️  DURÉE TOTALE: {duration:.0f} secondes")
            print(f"   Soit {duration/60:.1f} minutes")
            
            print(f"\n✅ SCRAPING RÉUSSI!")
            print(f"   {len(listings)} annonces de villas complètement scrapées")
            
            # Aperçu
            print(f"\n📋 APERÇU DES DONNÉES:")
            if listings:
                df_preview = []
                for i, listing in enumerate(listings[:3]):
                    df_preview.append({
                        'Région': listing.get('region', ''),
                        'Titre': listing.get('titre', '')[:40] + '...' if len(listing.get('titre', '')) > 40 else listing.get('titre', ''),
                        'Ville': listing.get('ville', ''),
                        'Type': listing.get('type_villa', ''),
                        'Prix': f"{listing.get('prix', 0):,.0f} TND" if listing.get('prix', 0) > 0 else listing.get('prix_text', ''),
                        'Surface': f"{listing.get('surface', 0):,.0f} m²" if listing.get('surface', 0) > 0 else listing.get('surface_text', ''),
                        'Chambres': listing.get('nombre_chambres', 'N/A')
                    })
                
                for item in df_preview:
                    print(f"  • {item['Région']} - {item['Titre']}")
                    print(f"    {item['Ville']} | {item['Type']} | {item['Prix']} | {item['Surface']} | {item['Chambres']} ch.")
                    print()
            
            print(f"\n🔧 POUR EXCEL:")
            print(f"   1. Ouvrez le fichier CSV dans Excel")
            print(f"   2. Utilisez 'Toutes les données' > 'Depuis un fichier texte/CSV'")
            print(f"   3. Encodage: UTF-8")
            print(f"   4. Délimiteur: Virgule")
            print(f"   5. Appliquez des filtres pour analyser par région/ville/type")
            
        else:
            print("\n❌ AUCUNE DONNÉE SCRAPÉE")
            print("   Causes possibles:")
            print("   - Site inaccessible")
            print("   - Aucune annonce trouvée")
            print("   - Structure du site modifiée")
            print("   - Problème de connexion internet")
            print("   Vérifiez le fichier log: mubawab_villas_ultimate.log")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  SCRAPING INTERROMPU PAR L'UTILISATEUR")
        print("   Les données scrapées seront sauvegardées si disponibles")
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("👋 PROGRAMME TERMINÉ")
    print("="*80)


if __name__ == "__main__":
    # Vérifier dépendances
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("\n❌ DÉPENDANCES MANQUANTES!")
        print("💡 Installation:")
        print("   pip install requests beautifulsoup4")
        sys.exit(1)
    
    # Lancer
    main()
    
    # Pause
    input("\nAppuyez sur Entrée pour quitter...")