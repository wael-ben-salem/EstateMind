"""
SCRAPER MUBAWAB ULTIMATE - VERSION LOCATION VACANCES
Scraper intelligent pour appartements de vacances à louer avec détection automatique
URL: https://www.mubawab.tn/fr/sc/appartements-vacational
Structure complète avec extraction de toutes les données, images et description détaillée
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
        logging.FileHandler('mubawab_location_vacances_ultimate.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MubawabLocationVacancesUltimateScraper:
    """Scraper ULTIMATE pour appartements de vacances - Extraction complète"""
    
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
        
        # URL de base pour les vacances
        self.base_url = "https://www.mubawab.tn/fr/sc/appartements-vacational"
        self.property_type = 'apartment-vacational'
        
        self.stats = {
            'pages_scraped': 0,
            'listings_found': 0,
            'listings_scraped': 0,
            'errors': 0,
            'total_ads_detected': 0,
            'valid_cards_per_page': [],
            'invalid_cards_per_page': [],
            'cities_stats': {}
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
    
    def build_search_url(self, page: int = 1) -> str:
        """Construit l'URL de recherche pour les vacances"""
        base = "https://www.mubawab.tn"
        
        if page == 1:
            return f"{base}/fr/sc/appartements-vacational"
        else:
            return f"{base}/fr/sc/appartements-vacational:p:{page}"
    
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
            
            # Chercher le span avec id 'numResults'
            total_elem = soup.find('span', id='numResults')
            if total_elem:
                total_text = total_elem.get_text(strip=True)
            
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
            ads_per_page = real_listings if real_listings > 0 else 28  # Mubawab affiche 28 annonces/page
            
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
            return 0, 10, 28
    
    def count_real_listings_on_page(self, soup: BeautifulSoup) -> int:
        """Compte les vraies annonces sur une page"""
        try:
            # Méthode: Chercher les conteneurs d'annonces Mubawab
            listing_boxes = soup.find_all('div', class_='listingBox')
            
            if listing_boxes:
                return len(listing_boxes)
            else:
                # Chercher par structure spécifique
                cards = soup.find_all('div', class_=re.compile(r'(search-listing|property-item)'))
                return len(cards) if cards else 0
            
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
            ('ul', {'class': lambda x: x and 'pagin' in str(x).lower()})
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
                match = re.search(r':p:(\d+)', href)
                if match:
                    page_numbers.append(int(match.group(1)))
                
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
        """Extrait le prix d'un appartement de vacances"""
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
            r'loyer\s*[:\-]?\s*([\d\s\.]+)\s*(?:tnd|dt)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(' ', '').replace('.', '')
                    if price_str.isdigit():
                        price = float(price_str)
                        # Filtre de validité pour vacances (10 à 5000 DT/jour ou 300 à 150000 DT/mois)
                        if 10 <= price <= 150000:
                            return price
                except:
                    continue
        
        return None
    
    def extract_price_per_day(self, text: str) -> Optional[float]:
        """Extrait le prix par jour pour les vacances"""
        if not text:
            return None
        
        text = self.clean_text(text).lower()
        
        # Vérifier si c'est un prix par jour
        if 'par jour' in text or '/jour' in text or 'jour' in text:
            patterns = [
                r'([\d\s\.]+)\s*(?:dt|tnd|dinars?)\s*[\/\s]\s*jour',
                r'([\d\s\.]+)\s*(?:dt|tnd|dinars?).*?jour',
                r'prix.*?([\d\s\.]+)\s*(?:dt|tnd|dinars?).*?jour'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        price_str = match.group(1).replace(' ', '').replace(',', '.')
                        return float(price_str)
                    except:
                        continue
        
        return None
    
    def extract_surface(self, text: str) -> Optional[float]:
        """Extrait la surface d'un appartement"""
        if not text:
            return None
        
        patterns = [
            r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]',
            r'superficie\s*[:\-]?\s*(\d+(?:[,\s]\d+)*)',
            r'(\d+(?:[,\s]\d+)*)\s*mètre',
            r'(\d+)\s*m\b'
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
            r'(\d+)\s*pi[èe]ce',
            r'S(\d+)',  # S1, S2, S3, etc.
            r'(\d+)\s*chambre',
            r'(\d+)\s*room'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def extract_bedrooms(self, text: str) -> Optional[int]:
        """Extrait le nombre de chambres"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*chambre',
            r'(\d+)\s*bedroom',
            r'(\d+)\s*lits?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def extract_bathrooms(self, text: str) -> Optional[int]:
        """Extrait le nombre de salles de bain"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*salle?\s*de?\s*bain',
            r'(\d+)\s*bathroom',
            r'(\d+)\s*SDB',
            r'(\d+)\s*bain'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def extract_id_from_url(self, url: str) -> Optional[str]:
        """Extrait l'ID de l'URL"""
        if not url:
            return None
        
        patterns = [
            r'/a/(\d+)/',
            r'/pa/(\d+)/',
            r'/p/(\d+)/',
            r'id[=_](\d+)',
            r'/(\d{6,})/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_capacity(self, text: str) -> Optional[int]:
        """Extrait la capacité (nombre de personnes)"""
        if not text:
            return None
        
        patterns = [
            r'capacit[ée]\s*[:\-]?\s*(\d+)',
            r'(\d+)\s*personnes?',
            r'(\d+)\s*pers',
            r'(\d+)\s*person'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def extract_min_nights(self, text: str) -> Optional[int]:
        """Extrait le nombre minimum de nuits"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*nuits?\s*min',
            r'minimum\s*(\d+)\s*nuits?',
            r'(\d+)\s*nuit\s*minimum',
            r'min\s*(\d+)\s*nuits?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return None
    
    def extract_vacation_features(self, text: str) -> List[str]:
        """Extrait les caractéristiques spécifiques aux vacances"""
        features = []
        text_lower = text.lower()
        
        feature_mapping = {
            'ascenseur': 'Ascenseur',
            'concierge': 'Concierge',
            'climatisation': 'Climatisation',
            'chauffage central': 'Chauffage central',
            'sécurité': 'Sécurité',
            'double vitrage': 'Double vitrage',
            'porte blindée': 'Porte blindée',
            'cuisine équipée': 'Cuisine équipée',
            'parking': 'Parking',
            'garage': 'Garage',
            'terrasse': 'Terrasse',
            'jardin': 'Jardin',
            'vue sur mer': 'Vue sur mer',
            'piscine': 'Piscine',
            'internet': 'Internet',
            'wifi': 'WiFi',
            'tv': 'TV',
            'satellite': 'Satellite',
            'machine à laver': 'Machine à laver',
            'lave-linge': 'Lave-linge',
            'micro-ondes': 'Micro-ondes',
            'réfrigérateur': 'Réfrigérateur',
            'four': 'Four',
            'animaux autorisés': 'Animaux autorisés',
            'proche plage': 'Proche plage',
            'proche commerces': 'Proche commerces',
            'vue panoramique': 'Vue panoramique',
            'meublé': 'Meublé',
            'non meublé': 'Non meublé',
            'balcon': 'Balcon',
            'salle de sport': 'Salle de sport',
            'spa': 'Spa',
            'sauna': 'Sauna',
            'jacuzzi': 'Jacuzzi'
        }
        
        for fr_key, fr_text in feature_mapping.items():
            if fr_key in text_lower and fr_text not in features:
                features.append(fr_text)
        
        return features
    
    def find_all_listing_cards(self, soup: BeautifulSoup) -> List:
        """Trouve TOUTES les cartes d'annonces d'appartements de vacances"""
        cards = []
        
        # Structure principale Mubawab pour les vacances
        listing_boxes = soup.find_all('div', class_='listingBox')
        
        if listing_boxes:
            cards.extend(listing_boxes)
            logger.debug(f"{len(listing_boxes)} listingBox trouvés")
        
        # Si pas de listingBox, chercher d'autres structures
        if not cards:
            card_selectors = [
                ('div', {'class': 'search-listing'}),
                ('div', {'class': 'property-item'}),
                ('div', {'class': 'listing-item'}),
                ('div', {'class': 'ad-container'}),
                ('div', {'class': re.compile(r'col-\d+')})  # Structure de grille
            ]
            
            for tag, attrs in card_selectors:
                elements = soup.find_all(tag, attrs)
                for elem in elements:
                    # Vérifier que c'est une annonce de vacances
                    text = elem.get_text().lower()
                    if ('vacanc' in text or 'location' in text or 'appartement' in text) and ('louer' in text or 'à louer' in text):
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
        """Valide si une carte est une vraie annonce d'appartement de vacances"""
        try:
            text = card.get_text()
            text_lower = text.lower()
            
            # Critères pour un appartement de vacances
            is_vacation = 'vacanc' in text_lower or 'location' in text_lower
            has_price_marker = any(marker in text for marker in ['DT', 'TND', 'dinars', 'prix', 'par jour', 'par nuit'])
            is_for_rent = 'louer' in text_lower or 'à louer' in text_lower or 'location' in text_lower
            
            # Vérifier la structure Mubawab
            has_title = bool(card.find(['h2', 'h3', 'h4'], class_=re.compile(r'listingTit|title', re.I)))
            has_link = bool(card.find('a', href=re.compile(r'/a/|/pa/|/p/')))
            has_location = bool(card.find('span', class_='listingH3')) or bool(card.find('i', class_='icon-location'))
            
            # Score de validation
            score = 0
            if is_vacation or has_price_marker:
                score += 2
            if is_for_rent:
                score += 1
            if has_title:
                score += 1
            if has_link:
                score += 1
            if has_location:
                score += 1
            
            return score >= 4  # Au moins 4 points sur 5
            
        except Exception as e:
            logger.debug(f"Erreur validation carte: {e}")
            return False
    
    def parse_listing_card(self, card) -> Optional[Dict]:
        """Parse une carte d'annonce d'appartement de vacances"""
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
                'prix_par_jour': 0,
                'surface': 0,
                'surface_text': '',
                'ville': '',
                'quartier': '',
                'adresse': '',
                'type_bien': 'Appartement',
                'type_location': 'Location vacances',
                'nombre_pieces': 0,
                'nombre_chambres': 0,
                'nombre_sdb': 0,
                'capacite': 0,
                'nuits_minimum': 0,
                'etage': '',
                'residence': '',
                'description_courte': '',
                'equipements': [],
                'amenities_vacances': [],
                'date_scraping': datetime.now().isoformat(),
                'page_source': 'search',
                'is_valid': True
            }
            
            # URL et ID
            links = card.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/a/' in href or '/pa/' in href:
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
                titles = card.find_all(['h2', 'h3', 'h4', 'h5'], class_=['listingTit', 'title'])
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
                        data['prix_par_jour'] = self.extract_price_per_day(price_text) or 0
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
            
            # Caractéristiques spécifiques aux vacances
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
                        elif 'icon-house-boxes' in icon_class or 'pièce' in value.lower():
                            data['nombre_pieces'] = self.extract_rooms(value) or 0
                        
                        # Chambres
                        elif 'icon-bed' in icon_class:
                            data['nombre_chambres'] = self.extract_bedrooms(value) or 0
                        
                        # Salles de bain
                        elif 'icon-bath' in icon_class:
                            data['nombre_sdb'] = self.extract_bathrooms(value) or 0
                        
                        # Capacité
                        elif 'icon-house-persons' in icon_class:
                            data['capacite'] = self.extract_capacity(value) or 0
                        
                        # Nuits minimum
                        elif 'icon-sleep' in icon_class:
                            data['nuits_minimum'] = self.extract_min_nights(value) or 0
            
            # Si données manquantes, chercher dans tout le texte
            if data['surface'] == 0:
                surface_match = re.search(r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]', all_text)
                if surface_match:
                    data['surface_text'] = surface_match.group(0)
                    data['surface'] = self.extract_surface(surface_match.group(0)) or 0
            
            if data['nombre_pieces'] == 0:
                data['nombre_pieces'] = self.extract_rooms(all_text) or 0
            
            if data['nombre_chambres'] == 0:
                data['nombre_chambres'] = self.extract_bedrooms(all_text) or 0
            
            if data['nombre_sdb'] == 0:
                data['nombre_sdb'] = self.extract_bathrooms(all_text) or 0
            
            if data['capacite'] == 0:
                data['capacite'] = self.extract_capacity(all_text) or 0
            
            if data['nuits_minimum'] == 0:
                data['nuits_minimum'] = self.extract_min_nights(all_text) or 0
            
            # Type de bien
            if 'studio' in text_lower:
                data['type_bien'] = 'Studio'
            elif 'duplex' in text_lower:
                data['type_bien'] = 'Duplex'
            elif 'villa' in text_lower:
                data['type_bien'] = 'Villa'
            elif 'appartement' in text_lower:
                data['type_bien'] = 'Appartement'
            elif 'maison' in text_lower:
                data['type_bien'] = 'Maison'
            
            # Équipements/Features
            equip_list = []
            features_section = card.find('div', class_='adFeatures')
            if features_section:
                feature_divs = features_section.find_all('div', class_='adFeature')
                for feature in feature_divs:
                    icon = feature.find('i')
                    text_span = feature.find('span')
                    if text_span:
                        equip_list.append(text_span.get_text(strip=True))
                    elif icon:
                        icon_class = icon.get('class', [''])[0]
                        if 'icon-elevator' in icon_class:
                            equip_list.append('Ascenseur')
                        elif 'icon-garage' in icon_class:
                            equip_list.append('Garage')
                        elif 'icon-terrace' in icon_class:
                            equip_list.append('Terrasse')
                        elif 'icon-airConditioning' in icon_class:
                            equip_list.append('Climatisation')
                        elif 'icon-heating' in icon_class:
                            equip_list.append('Chauffage')
                        elif 'icon-fullKitchen' in icon_class:
                            equip_list.append('Cuisine équipée')
                        elif 'icon-security' in icon_class:
                            equip_list.append('Sécurité')
                        elif 'icon-doorman' in icon_class:
                            equip_list.append('Concierge')
                        elif 'icon-doubleGlazing' in icon_class:
                            equip_list.append('Double vitrage')
                        elif 'icon-reinforcedDoor' in icon_class:
                            equip_list.append('Porte blindée')
                        elif 'icon-garden' in icon_class:
                            equip_list.append('Jardin')
                        elif 'icon-pool' in icon_class:
                            equip_list.append('Piscine')
                        elif 'icon-seaViews' in icon_class:
                            equip_list.append('Vue sur mer')
                        elif 'icon-tv' in icon_class:
                            equip_list.append('TV')
                        elif 'icon-washer' in icon_class:
                            equip_list.append('Machine à laver')
                        elif 'icon-internet' in icon_class:
                            equip_list.append('Internet')
                        elif 'icon-satellite' in icon_class:
                            equip_list.append('Satellite')
                        elif 'icon-fridge' in icon_class:
                            equip_list.append('Réfrigérateur')
                        elif 'icon-oven' in icon_class:
                            equip_list.append('Four')
                        elif 'icon-microwave' in icon_class:
                            equip_list.append('Micro-ondes')
            
            # Chercher d'autres équipements spécifiques aux vacances
            vacation_features = self.extract_vacation_features(all_text)
            equip_list.extend([feat for feat in vacation_features if feat not in equip_list])
            
            data['equipements'] = equip_list
            data['amenities_vacances'] = vacation_features
            
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
                    if len(para) > 30 and ('vacanc' in para.lower() or 'location' in para.lower() or 'appartement' in para.lower()):
                        data['description_courte'] = self.clean_text(para[:300])
                        break
            
            # Étage
            if 'étage' in text_lower:
                match = re.search(r'(\d+)\s*[eè]me?\s*étage', text_lower)
                if match:
                    data['etage'] = match.group(1)
            
            # Validation finale
            if not data['url'] or not data['titre']:
                data['is_valid'] = False
                return None
            
            # Vérifier que c'est bien un appartement de vacances
            if data['prix'] == 0 and ('vacanc' not in text_lower and 'location' not in text_lower):
                data['is_valid'] = False
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Erreur parsing carte vacances: {e}")
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
                match = re.search(r':p:(\d+)', next_url)
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
                
                has_next = True
            
            self.stats['pages_scraped'] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping page {page_num}: {e}")
            self.stats['errors'] += 1
        
        return listings, has_next, next_url, next_page_num
    
    def scrape_detailed_listing(self, url: str) -> Dict:
        """Scrape les détails complets d'un appartement de vacances depuis sa page détaillée"""
        details = {
            'description_complete': '',
            'caracteristiques': {},
            'equipements_detaille': [],
            'images': [],
            'localisation': {},
            'informations_supplementaires': {},
            'conditions_location': {},
            'contact_info': {},
            'scraping_timestamp_detail': datetime.now().isoformat()
        }
        
        try:
            time.sleep(0.5)  # Pause pour éviter le blocage
            response = self.make_request(url)
            if not response:
                return details
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Description complète
            desc_div = soup.find('div', class_='blockProp')
            if desc_div:
                paragraphs = desc_div.find_all('p')
                description = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                details['description_complete'] = self.clean_text(description)
            
            # 2. Caractéristiques détaillées
            caract_block = soup.find('div', class_='caractBlockProp')
            if caract_block:
                # Caractéristiques principales
                main_features = caract_block.find_all('div', class_='adMainFeature')
                for feature in main_features:
                    label = feature.find('p', class_='adMainFeatureContentLabel')
                    value = feature.find('p', class_='adMainFeatureContentValue')
                    if label and value:
                        label_text = label.get_text(strip=True).lower()
                        value_text = value.get_text(strip=True)
                        details['caracteristiques'][label_text] = value_text
                
                # Équipements détaillés
                features = caract_block.find_all('div', class_='adFeature')
                for feature in features:
                    text = feature.get_text(strip=True)
                    if text:
                        details['equipements_detaille'].append(text)
            
            # 3. Images complètes (limitées à 20)
            img_tags = soup.find_all('img', src=re.compile(r'mubawab-media\.com'))
            for img in img_tags[:20]:
                src = img.get('src')
                if src and src not in details['images']:
                    details['images'].append(src)
            
            # 4. Localisation (coordonnées)
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
            
            # 5. Informations supplémentaires
            full_text = soup.get_text().lower()
            
            # Disponibilité
            if 'disponible' in full_text:
                match = re.search(r'disponible\s*(?:dès|à partir de|le)?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\d{1,2}\s+\w+\s+\d{4})', full_text)
                if match:
                    details['informations_supplementaires']['date_disponibilite'] = match.group(1)
            
            # Meublé ou non
            if 'meublé' in full_text:
                details['informations_supplementaires']['meuble'] = 'Oui'
            elif 'non meublé' in full_text:
                details['informations_supplementaires']['meuble'] = 'Non'
            
            # Équipements supplémentaires
            if 'ascenseur' in full_text:
                details['informations_supplementaires']['ascenseur'] = 'Oui'
            
            if 'parking' in full_text or 'garage' in full_text:
                details['informations_supplementaires']['parking'] = 'Oui'
            
            if 'piscine' in full_text:
                details['informations_supplementaires']['piscine'] = 'Oui'
            
            if 'jardin' in full_text:
                details['informations_supplementaires']['jardin'] = 'Oui'
            
            if 'vue sur mer' in full_text or 'vue mer' in full_text:
                details['informations_supplementaires']['vue_mer'] = 'Oui'
            
            if 'climatisation' in full_text:
                details['informations_supplementaires']['climatisation'] = 'Oui'
            
            if 'internet' in full_text or 'wifi' in full_text:
                details['informations_supplementaires']['internet'] = 'Oui'
            
            # 6. Conditions de location spécifiques
            details['conditions_location'] = {}
            
            # Caution
            if 'caution' in full_text:
                match = re.search(r'caution\s*[:\-]?\s*(\d[\d\s]*)\s*(?:dt|tnd)', full_text)
                if match:
                    details['conditions_location']['caution'] = match.group(1).replace(' ', '')
            
            # Frais de ménage
            if 'ménage' in full_text or 'nettoyage' in full_text:
                details['conditions_location']['frais_menage'] = 'Oui'
            
            # Animaux acceptés
            if 'animaux acceptés' in full_text or 'animaux autorisés' in full_text:
                details['conditions_location']['animaux_autorises'] = 'Oui'
            elif 'animaux non acceptés' in full_text or 'animaux interdits' in full_text:
                details['conditions_location']['animaux_autorises'] = 'Non'
            
            # 7. Informations de contact
            agence_div = soup.find('div', class_='agencyName')
            if agence_div:
                details['contact_info']['agence'] = agence_div.get_text(strip=True)
            
            # Téléphone (crypté dans la page)
            phone_links = soup.find_all('a', onclick=re.compile(r'sendPhoneLead|showPhone'))
            if phone_links:
                details['contact_info']['telephone_disponible'] = 'Oui'
            
            # Email ou formulaire de contact
            contact_form = soup.find('form', id='leadForm')
            if contact_form:
                details['contact_info']['formulaire_contact'] = 'Disponible'
            
            # 8. Date de publication
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
    
    def scrape_all_ads(self, max_ads: int = 0, get_details: bool = True) -> List[Dict]:
        """Scrape toutes les annonces de vacances"""
        logger.info(f"🚀 DÉBUT SCRAPING COMPLET - APPARTEMENTS DE VACANCES")
        
        all_listings = []
        
        # Détection initiale
        first_url = self.build_search_url(1)
        total_ads, total_pages, ads_per_page = self.detect_total_ads_and_pages(first_url)
        
        if total_ads == 0:
            logger.warning(f"⚠️  AUCUNE ANNONCE DÉTECTÉE")
            return []
        
        self.stats['total_ads_detected'] = total_ads
        
        # Calculer combien scraper
        ads_to_scrape = max_ads if max_ads > 0 else total_ads
        pages_to_scrape = (ads_to_scrape // ads_per_page) + (1 if ads_to_scrape % ads_per_page > 0 else 0)
        pages_to_scrape = min(pages_to_scrape, total_pages)
        
        logger.info(f"📊 TOTAL: {total_ads} annonces détectées")
        logger.info(f"📄 Objectif: {ads_to_scrape} annonces sur {pages_to_scrape}/{total_pages} pages")
        logger.info(f"📈 Estimation: {ads_per_page} annonces par page")
        
        # Scraper page par page
        current_page = 1
        current_url = first_url
        ads_scraped = 0
        consecutive_empty_pages = 0
        total_errors = 0
        
        while (current_page <= pages_to_scrape and 
               ads_scraped < ads_to_scrape and 
               consecutive_empty_pages < 2):
            
            try:
                print(f"\n{'='*50}")
                print(f"📍 PAGE {current_page}/{pages_to_scrape}")
                print(f"📊 Progression: {ads_scraped}/{ads_to_scrape} annonces")
                print(f"{'='*50}")
                
                # Scraper la page
                page_listings, has_next, next_url, next_page_num = self.scrape_page_listings(
                    current_url, current_page
                )
                
                # Vérifier si la page est vide
                if not page_listings:
                    logger.warning(f"⚠️  PAGE {current_page} VIDE")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= 2:
                        logger.error(f"❌ 2 PAGES VIDES CONSÉCUTIVES - ARRÊT")
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
                                    'equipements_detaille': '; '.join(details.get('equipements_detaille', [])),
                                    'images': '; '.join(details.get('images', [])),
                                    'localisation': json.dumps(details.get('localisation', {}), ensure_ascii=False),
                                    'informations_supplementaires': json.dumps(details.get('informations_supplementaires', {}), ensure_ascii=False),
                                    'conditions_location': json.dumps(details.get('conditions_location', {}), ensure_ascii=False),
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
                            total_errors += 1
                            continue
                
                # Ajouter aux résultats
                all_listings.extend(page_listings)
                ads_scraped = len(all_listings)
                
                logger.info(f"📈 {ads_scraped}/{ads_to_scrape} annonces accumulées")
                
                # Vérifier si on continue
                if ads_scraped >= ads_to_scrape:
                    logger.info(f"🎯 OBJECTIF ATTEINT: {ads_scraped} annonces")
                    all_listings = all_listings[:ads_to_scrape]
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
                    logger.info(f"📄 DERNIÈRE PAGE ATTEINTE")
                    break
                
            except KeyboardInterrupt:
                logger.info("⏹️  INTERROMPU PAR UTILISATEUR")
                print(f"\n⚠️  SCRAPING INTERROMPU - SAUVEGARDE...")
                break
            except Exception as e:
                logger.error(f"❌ ERREUR PAGE {current_page}: {e}")
                total_errors += 1
                self.stats['errors'] += 1
                
                # Essayer de continuer
                if current_page < pages_to_scrape:
                    current_page += 1
                    current_url = self.build_search_url(current_page)
                    time.sleep(5)
                else:
                    break
        
        self.stats['listings_scraped'] = len(all_listings)
        
        logger.info(f"✅ FIN SCRAPING: {len(all_listings)} annonces")
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
            
            # Ordre logique pour les vacances
            preferred_order = [
                'id', 'titre', 'url', 'ville', 'quartier', 'adresse',
                'type_bien', 'type_location', 
                'prix', 'prix_text', 'prix_par_jour', 'surface', 'surface_text',
                'nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'capacite', 'nuits_minimum',
                'etage', 'residence', 'description_courte', 'description_complete',
                'equipements', 'amenities_vacances', 'equipements_detaille', 'images',
                'caracteristiques', 'localisation', 'informations_supplementaires',
                'conditions_location', 'contact_info', 'date_scraping', 
                'page_source', 'is_valid'
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
                    'source_url': 'https://www.mubawab.tn/fr/sc/appartements-vacational',
                    'property_type': 'location_vacances',
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
        print("📊 STATISTIQUES FINALES DU SCRAPING LOCATION VACANCES")
        print("="*80)
        
        print(f"\n📍 SOURCE:")
        print("https://www.mubawab.tn/fr/sc/appartements-vacational")
        
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
        
        print("\n" + "="*80)


def main():
    """Programme principal"""
    print("\n" + "="*80)
    print("🏖️  SCRAPER MUBAWAB ULTIMATE - LOCATION VACANCES")
    print("🎯 DÉTECTION AUTOMATIQUE - EXTRACTION COMPLÈTE")
    print("="*80)
    
    # Configuration
    print("\n📋 CONFIGURATION DU SCRAPING")
    
    # Choix du nombre d'annonces
    print("\n📊 NOMBRE D'ANNONCES:")
    print("  0. Toutes les annonces disponibles")
    print("  1. 50 annonces")
    print("  2. 100 annonces")
    print("  3. 200 annonces")
    print("  4. 500 annonces")
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
            max_ads = int(input("Entrez le nombre d'annonces: "))
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
    print(f"   📍 Source: https://www.mubawab.tn/fr/sc/appartements-vacational")
    print(f"   🏖️  Type: Appartements de vacances")
    print(f"   📊 Nombre: {'TOUTES les annonces' if max_ads == 0 else max_ads}")
    print(f"   🔍 Détails: {'✅ OUI' if get_details else '❌ NON'}")
    print("="*80)
    
    if max_ads == 0 or max_ads > 200:
        print("⚠️  ATTENTION: Scraping long en cours!")
        print("   Toutes les pages seront traitées.")
        print("   Durée estimée: 10-30 minutes selon le nombre d'annonces.")
        print("="*80)
    
    # Confirmation
    confirm = input("\n✅ Démarrer le scraping? (O/n): ").strip().lower()
    if confirm in ['n', 'non', 'no']:
        print("❌ Annulé.")
        return
    
    # Lancement
    print(f"\n🚀 LANCEMENT DU SCRAPING...")
    print(f"📁 Les fichiers seront sauvegardés dans le dossier courant")
    print(f"⏳ Veuillez patienter, cela peut prendre du temps...")
    print(f"📊 La détection automatique va calculer le nombre total d'annonces")
    
    try:
        scraper = MubawabLocationVacancesUltimateScraper(delay=0.8)
        
        start_time = datetime.now()
        listings = scraper.scrape_all_ads(max_ads, get_details)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        if listings:
            # Préparer fichiers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"mubawab_location_vacances_complet_{timestamp}"
            
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
            print(f"   {len(listings)} annonces d'appartements de vacances complètement scrapées")
            
            # Aperçu
            print(f"\n📋 APERÇU DES DONNÉES:")
            if listings:
                for i, listing in enumerate(listings[:3]):
                    print(f"  {i+1}. {listing.get('titre', '')[:50]}...")
                    print(f"     📍 {listing.get('ville', '')} - {listing.get('quartier', '')}")
                    print(f"     💰 {listing.get('prix', 0)} TND | 🛏️ {listing.get('nombre_chambres', 0)} chambres")
                    print(f"     📏 {listing.get('surface', 0)} m² | 👥 {listing.get('capacite', 0)} personnes")
                    print()
            
            print(f"\n🔧 POUR EXCEL:")
            print(f"   1. Ouvrez le fichier CSV dans Excel")
            print(f"   2. Utilisez 'Toutes les données' > 'Depuis un fichier texte/CSV'")
            print(f"   3. Encodage: UTF-8")
            print(f"   4. Délimiteur: Virgule")
            print(f"   5. Appliquez des filtres pour analyser par ville/quartier/type")
            
        else:
            print("\n❌ AUCUNE DONNÉE SCRAPÉE")
            print("   Causes possibles:")
            print("   - Site inaccessible")
            print("   - Aucune annonce trouvée")
            print("   - Structure du site modifiée")
            print("   - Problème de connexion internet")
            print("   Vérifiez le fichier log: mubawab_location_vacances_ultimate.log")
    
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