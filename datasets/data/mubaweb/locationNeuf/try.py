"""
SCRAPER MUBAWAB ULTIMATE - VERSION IMMOBILIER NEUF FINALE
Scraper intelligent pour immobilier neuf avec détection automatique et extraction optimisée
URL: https://www.mubawab.tn/fr/listing-promotion
Structure complète avec extraction de toutes les données, images, vidéos et description détaillée
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
from urllib.parse import urljoin, urlparse, parse_qs, unquote
from typing import List, Dict, Optional, Tuple, Set
import logging
import random

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mubawab_immobilier_neuf_ultimate.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MubawabImmobilierNeufUltimateScraper:
    """Scraper ULTIMATE pour immobilier neuf - Extraction complète et optimisée"""
    
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
        
        # URL de base pour immobilier neuf
        self.base_url = "https://www.mubawab.tn/fr/listing-promotion"
        
        self.stats = {
            'pages_scraped': 0,
            'listings_found': 0,
            'listings_scraped': 0,
            'errors': 0,
            'total_ads_detected': 0,
            'valid_cards_per_page': [],
            'invalid_cards_per_page': [],
            'types_stats': {},
            'videos_found': 0,
            'images_found': 0
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
                elif response.status_code == 404:
                    logger.warning(f"Page non trouvée: {url}")
                    return None
                
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1} échouée pour {url}: {e}")
                time.sleep(3)
        
        logger.error(f"Échec de toutes les tentatives pour {url}")
        return None
    
    def build_search_url(self, filters: Dict = None, page: int = 1) -> str:
        """Construit l'URL de recherche avec filtres"""
        base = self.base_url
        
        if filters:
            params = []
            
            # Ville
            if filters.get('city'):
                city_slug = filters['city'].lower().replace(' ', '-')
                base = f"https://www.mubawab.tn/fr/pl/{city_slug}/listing-promotion"
            
            # Type de bien
            if filters.get('property_type'):
                type_map = {
                    'appartements': 'apartments-for-sale',
                    'maisons': 'houses-for-sale',
                    'villas': 'villas-and-luxury-homes-for-sale',
                    'bureaux': 'offices-for-sale',
                    'terrains': 'land-for-sale',
                    'locaux-commerciaux': 'commercial-property-for-sale'
                }
                type_slug = type_map.get(filters['property_type'], filters['property_type'])
                params.append(f"scat:{type_slug}")
            
            # Prix minimum
            if filters.get('min_price'):
                params.append(f"prmn:{filters['min_price']}")
            
            # Prix maximum
            if filters.get('max_price'):
                params.append(f"prmx:{filters['max_price']}")
            
            if params:
                base = f"{base}:{':'.join(params)}"
        
        # Pagination
        if page > 1:
            base = f"{base}:p:{page}"
        
        return base
    
    def detect_total_ads_and_pages(self, url: str) -> Tuple[int, int, int]:
        """Détecte le nombre total d'annonces, pages et annonces par page"""
        try:
            logger.info(f"Détection pour: {url}")
            response = self.make_request(url)
            if not response:
                return 0, 0, 0
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Chercher le nombre total de résultats
            total_ads = 0
            
            # Chercher le conteneur de résultats
            listing_ul = soup.find('ul', id='listingUl')
            if listing_ul:
                listings = listing_ul.find_all('li', class_='promotionListing')
                total_ads = len(listings)
                logger.info(f"✅ Détecté: {total_ads} annonces directement dans listingUl")
            
            # Si pas trouvé, chercher par structure
            if total_ads == 0:
                all_listings = soup.find_all('li', class_=re.compile(r'promotionListing|listingBox'))
                total_ads = len(all_listings)
                if total_ads > 0:
                    logger.info(f"✅ Détecté: {total_ads} annonces via recherche générale")
            
            # 2. Compter les annonces réelles sur la première page
            real_listings = self.count_real_listings_on_page(soup)
            ads_per_page = real_listings if real_listings > 0 else 20
            
            # 3. Chercher la pagination
            pagination = self.find_pagination(soup)
            if pagination:
                max_page = self.extract_max_page_from_pagination(pagination)
                if max_page > 0:
                    pages = max_page
                    logger.info(f"📊 Pagination trouvée: {pages} pages")
                else:
                    pages = 1 if total_ads > 0 else 0
            else:
                # Si pas de pagination mais des annonces, une seule page
                pages = 1 if total_ads > 0 else 0
            
            # Si on a trouvé des annonces mais pas de pagination, estimer
            if total_ads > 0 and ads_per_page > 0 and pages == 1:
                pages = (total_ads // ads_per_page) + (1 if total_ads % ads_per_page > 0 else 0)
                logger.info(f"📊 Estimation: {pages} pages à {ads_per_page} annonces/page")
            
            return total_ads, pages, ads_per_page
            
        except Exception as e:
            logger.error(f"❌ Erreur détection: {e}")
            return 0, 10, 20
    
    def count_real_listings_on_page(self, soup: BeautifulSoup) -> int:
        """Compte les vraies annonces sur une page"""
        try:
            # Méthode spécifique pour immobilier neuf
            listing_boxes = soup.find_all('li', class_='promotionListing')
            if listing_boxes:
                valid_count = 0
                for box in listing_boxes:
                    # Vérifier que c'est une vraie annonce
                    if box.get('promotion-id'):
                        valid_count += 1
                return valid_count
            
            # Méthode alternative
            all_cards = soup.find_all('div', class_='listingBox')
            return len(all_cards) if all_cards else 0
            
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
        text = re.sub(r'[^\x00-\x7FÀ-ÿ\s\.\,\-\:\;\!\?\(\)\[\]\'\"\\\/]', '', text)
        return text
    
    def extract_price(self, text: str) -> Tuple[Optional[float], str]:
        """Extrait le prix et le type de prix"""
        if not text:
            return None, ""
        
        text = self.clean_text(text).lower()
        
        # "Prix à consulter" - AMÉLIORÉ: reconnaître et garder comme texte
        if any(phrase in text for phrase in ['à consulter', 'sur demande', 'négociable', 'prix sur demande', 'prix à consulter']):
            return 0, "À consulter"  # Changé de None à 0 pour garder l'annonce
        
        # "À partir de X TND"
        if 'à partir de' in text:
            match = re.search(r'à partir de\s*([\d\s\.]+)\s*(?:tnd|dt|dinars?)', text, re.I)
            if match:
                try:
                    price_str = match.group(1).replace(' ', '').replace('.', '')
                    if price_str.isdigit():
                        return float(price_str), "À partir de"
                except:
                    pass
        
        # Prix normal
        patterns = [
            r'([\d\s\.]+)\s*(?:tnd|dt|dinars?)\b',
            r'prix\s*[:\-]?\s*([\d\s\.]+)\s*(?:tnd|dt)',
            r'([\d\s\.]+)\s*mille\s*(?:tnd|dt|dinars?)',
            r'([\d\s\.]+)\s*(?:€|eur|euro)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(' ', '').replace('.', '')
                    if price_str.isdigit():
                        price = float(price_str)
                        return price, "Prix fixe"
                except:
                    continue
        
        return 0, "Non spécifié"  # Changé de None à 0 pour garder l'annonce
    
    def extract_price_per_m2(self, text: str) -> Optional[float]:
        """Extrait le prix au m²"""
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
                    if '.' in price_str:
                        parts = price_str.split('.')
                        if len(parts) == 2 and len(parts[1]) > 2:
                            price_str = parts[0] + parts[1][:2]
                    return float(price_str)
                except:
                    continue
        
        return None
    
    def extract_surface(self, text: str) -> Optional[float]:
        """Extrait la surface"""
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
            r'A(\d+)',
            r'S(\d+)',
            r'(\d+)\s*chambre',
            r'(\d+)\s*room',
            r'(\d+)\s*salon'
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
            r'/p/(\d+)/',
            r'promotion-id="(\d+)"',
            r'id[=_](\d+)',
            r'/(\d{4,})/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_property_type(self, text: str) -> str:
        """Détermine le type de bien - VERSION AMÉLIORÉE"""
        if not text:
            return "Immobilier neuf"
        
        text_lower = text.lower()
        
        # Vérifier d'abord les types spécifiques
        if 'résidence' in text_lower and 'appartement' not in text_lower:
            return "Résidence"
        elif 'appartement' in text_lower:
            return "Appartement"
        elif 'maison' in text_lower and 'villa' not in text_lower:
            return "Maison"
        elif 'villa' in text_lower:
            return "Villa"
        elif 'bureau' in text_lower or 'bureautique' in text_lower:
            return "Bureau"
        elif 'local commercial' in text_lower or ('commercial' in text_lower and 'résidence' not in text_lower):
            return "Local commercial"
        elif 'terrain' in text_lower or 'lotissement' in text_lower:
            return "Terrain"
        elif 'immeuble' in text_lower:
            return "Immeuble"
        elif 'complexe' in text_lower:
            return "Complexe"
        else:
            # Par défaut, si c'est un projet immobilier, c'est probablement une résidence
            if any(word in text_lower for word in ['promotion', 'neuf', 'livraison', 'en cours']):
                return "Résidence"
            return "Immobilier neuf"
    
    def extract_standing(self, text: str) -> str:
        """Extrait le standing"""
        if not text:
            return "Standard"
        
        text_lower = text.lower()
        
        if 'haut standing' in text_lower or 'premium' in text_lower or 'luxe' in text_lower or 'très haut standing' in text_lower:
            return "Haut standing"
        elif 'moyen standing' in text_lower or 'standard' in text_lower:
            return "Moyen standing"
        elif 'économique' in text_lower or 'entrée de gamme' in text_lower:
            return "Économique"
        else:
            return "Standard"
    
    def extract_construction_status(self, text: str) -> str:
        """Extrait le statut de construction"""
        if not text:
            return "Non spécifié"
        
        text_lower = text.lower()
        
        if 'finalisé' in text_lower or 'livré' in text_lower or 'terminé' in text_lower:
            return "Finalisé"
        elif 'en cours de construction' in text_lower or 'en construction' in text_lower:
            return "En cours de construction"
        elif 'en projet' in text_lower or 'projet' in text_lower:
            return "En projet"
        elif 'livraison' in text_lower:
            return "Livraison prévue"
        else:
            return "Non spécifié"
    
    def extract_delivery_date(self, text: str) -> str:
        """Extrait la date de livraison"""
        if not text:
            return ""
        
        patterns = [
            r'livraison\s*(?:prévue|prévisionnelle)?\s*[:\-]?\s*(\w+\s+\d{4})',
            r'délivrable\s*(?:en|le)?\s*(\w+\s+\d{4})',
            r'disponible\s*(?:en|le)?\s*(\w+\s+\d{4})',
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            r'(\w+\s+\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_city_from_location(self, location_text: str) -> str:
        """Extrait la ville d'un texte de localisation - VERSION AMÉLIORÉE"""
        if not location_text:
            return ""
        
        # Liste des villes tunisiennes courantes
        tunisian_cities = [
            'Tunis', 'Sousse', 'Sfax', 'Bizerte', 'Nabeul', 'Monastir',
            'Mahdia', 'Kairouan', 'Gafsa', 'Gabès', 'La Marsa', 'Carthage',
            'Le Kram', 'Ariana', 'Ben Arous', 'Manouba', 'Ezzahra', 'Hammamet',
            'Yasmine Hammamet', 'Djerba', 'Tozeur', 'Sidi Bou Said', 'Mégrine',
            'Radès', 'Mohammedia', 'Mornag', 'Zaghouan', 'Beja', 'Jendouba',
            'Siliana', 'Kef', 'Kasserine', 'Sidi Hassine', 'Ennasr', 'El Menzah',
            'El Menzeh', 'Ariana Ville', 'Tunis Ville', 'Sousse Ville', 'Mohamedia'
        ]
        
        location_lower = location_text.lower()
        
        # Recherche exacte
        for city in tunisian_cities:
            if city.lower() in location_lower:
                return city
        
        # Si on trouve "à" dans le texte
        if 'à' in location_text:
            parts = location_text.split('à')
            if len(parts) > 1:
                potential_city = parts[1].strip().split(' ')[0]
                # Nettoyer
                potential_city = potential_city.replace(',', '').replace(';', '').strip()
                if potential_city and len(potential_city) > 2:
                    # Vérifier si c'est une ville connue
                    for city in tunisian_cities:
                        if city.lower().startswith(potential_city.lower()[:3]):
                            return city
                    return potential_city
        
        # Chercher le dernier mot significatif
        words = location_text.split()
        if words:
            last_word = words[-1].replace(',', '').strip()
            if last_word and len(last_word) > 2:
                for city in tunisian_cities:
                    if city.lower() == last_word.lower():
                        return city
        
        return ""
    
    def extract_neighborhood(self, location_text: str) -> str:
        """Extrait le quartier d'un texte de localisation"""
        if not location_text:
            return ""
        
        # Si le texte contient "à", ce qui précède est souvent le quartier
        if 'à' in location_text:
            parts = location_text.split('à')
            if len(parts) > 0:
                quartier = parts[0].strip()
                # Nettoyer
                quartier = quartier.replace('Les', '').replace('le', '').replace('la', '').replace('à', '').strip()
                if quartier and len(quartier) > 2:
                    return self.clean_text(quartier)
        
        return ""
    
    def extract_promotion_features(self, text: str) -> List[str]:
        """Extrait les caractéristiques de la promotion"""
        features = []
        text_lower = text.lower()
        
        feature_mapping = {
            'piscine': 'Piscine',
            'jardin': 'Jardin',
            'terrasse': 'Terrasse',
            'parking': 'Parking',
            'garage': 'Garage',
            'ascenseur': 'Ascenseur',
            'climatisation': 'Climatisation',
            'chauffage': 'Chauffage',
            'chauffage central': 'Chauffage central',
            'sécurité': 'Sécurité 24h/24',
            'vidéo surveillance': 'Vidéo surveillance',
            'concierge': 'Concierge',
            'salle de sport': 'Salle de sport',
            'spa': 'Spa',
            'hammam': 'Hammam',
            'jacuzzi': 'Jacuzzi',
            'aire de jeux': 'Aire de jeux',
            'piste cyclable': 'Piste cyclable',
            'vue sur mer': 'Vue sur mer',
            'vue panoramique': 'Vue panoramique',
            'double vitrage': 'Double vitrage',
            'isolation thermique': 'Isolation thermique',
            'isolation phonique': 'Isolation phonique',
            'cuisine équipée': 'Cuisine équipée',
            'salle de bain marbre': 'Salle de bain marbre',
            'domotique': 'Domotique',
            'fibre optique': 'Fibre optique'
        }
        
        for fr_key, fr_text in feature_mapping.items():
            if fr_key in text_lower and fr_text not in features:
                features.append(fr_text)
        
        return features
    
    def extract_video_url(self, card) -> Optional[str]:
        """Extrait l'URL de la vidéo YouTube si présente"""
        try:
            # Chercher iframe YouTube
            iframe = card.find('iframe', src=re.compile(r'youtube\.com|youtu\.be'))
            if iframe and iframe.get('src'):
                return iframe.get('src')
            
            # Chercher dans les divs avec onclick loadVideo
            video_divs = card.find_all('div', onclick=re.compile(r'loadVideo'))
            for div in video_divs:
                onclick = div.get('onclick', '')
                match = re.search(r"loadVideo\s*\(\s*'([^']+)'", onclick)
                if match:
                    return match.group(1)
            
            # Chercher dans les liens
            video_links = card.find_all('a', onclick=re.compile(r'loadVideo'))
            for link in video_links:
                onclick = link.get('onclick', '')
                match = re.search(r"loadVideo\s*\(\s*'([^']+)'", onclick)
                if match:
                    return match.group(1)
            
        except Exception as e:
            logger.debug(f"Erreur extraction vidéo: {e}")
        
        return None
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extrait l'ID YouTube d'une URL"""
        if not url:
            return None
        
        patterns = [
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/v/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def find_all_listing_cards(self, soup: BeautifulSoup) -> List:
        """Trouve TOUTES les cartes d'annonces d'immobilier neuf"""
        cards = []
        
        # 1. Structure principale pour immobilier neuf
        promotion_listings = soup.find_all('li', class_='promotionListing')
        if promotion_listings:
            cards.extend(promotion_listings)
            logger.debug(f"{len(promotion_listings)} promotionListing trouvés")
        
        # 2. Recherche par structure de listingBox
        listing_boxes = soup.find_all('li', class_='listingBox')
        for box in listing_boxes:
            if 'promotion-id' in box.attrs and box not in cards:
                cards.append(box)
        
        # 3. Recherche alternative
        all_listings = soup.find_all('div', class_=re.compile(r'(listingBox|search-listing|property-item)'))
        for listing in all_listings:
            text = listing.get_text()
            if ('neuf' in text.lower() or 'promotion' in text.lower() or 'livraison' in text.lower()) and listing not in cards:
                cards.append(listing)
        
        # Filtrer les doublons
        unique_cards = []
        seen = set()
        for card in cards:
            card_id = card.get('promotion-id')
            if card_id and card_id not in seen:
                seen.add(card_id)
                unique_cards.append(card)
            elif card_id is None:
                # Utiliser un hash du contenu
                card_hash = hash(str(card)[:300])
                if card_hash not in seen:
                    seen.add(card_hash)
                    unique_cards.append(card)
        
        logger.info(f"Total cartes uniques trouvées: {len(unique_cards)}")
        return unique_cards
    
    def extract_url_from_card(self, card) -> str:
        """Extrait l'URL d'une carte d'annonce"""
        try:
            # Méthode 1: Via promotion-id
            promotion_id = card.get('promotion-id', '')
            if promotion_id:
                return f"https://www.mubawab.tn/fr/p/{promotion_id}/details"
            
            # Méthode 2: Chercher dans les liens
            links = card.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href and ('/p/' in href or '/promotion/' in href):
                    full_url = urljoin('https://www.mubawab.tn', href)
                    return full_url
            
            # Méthode 3: Construire à partir du titre si on peut trouver un ID
            text = card.get_text()
            import re
            id_match = re.search(r'[Pp]romotion[:\s]*(\d+)', text)
            if id_match:
                return f"https://www.mubawab.tn/fr/p/{id_match.group(1)}/details"
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur extraction URL: {e}")
            return ""
    
    def validate_listing_card(self, card) -> bool:
        """Valide si une carte est une vraie annonce d'immobilier neuf - VERSION OPTIMISÉE"""
        try:
            # Vérifier si c'est une promotionListing
            classes = card.get('class', [])
            if 'promotionListing' in classes:
                # Avoir un promotion-id
                promotion_id = card.get('promotion-id', '')
                if promotion_id and promotion_id.strip():
                    return True
                
                # Sinon, vérifier si on a des éléments d'annonce
                has_title = bool(card.find('h2'))
                has_price = bool(card.find('span', class_='priceTag'))
                has_location = bool(card.find('h3'))
                
                if has_title or has_price or has_location:
                    return True
            
            # Vérifier le contenu texte
            text = card.get_text().lower()
            keywords = ['tnd', 'prix', 'à partir', 'm²', 'm2', 'surface', 'appartement', 'maison', 'villa', 'terrain', 'résidence']
            
            keyword_count = sum(1 for keyword in keywords if keyword in text)
            if keyword_count >= 2:
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Erreur validation carte: {e}")
            return True  # Accepter par défaut pour voir ce qu'il y a dedans
    
    def parse_listing_card(self, card) -> Optional[Dict]:
        """Parse une carte d'annonce d'immobilier neuf - VERSION FINALE AVEC GESTION DES PRIX À CONSULTER"""
        try:
            data = {
                'id': '',
                'promotion_id': '',
                'titre': '',
                'url': '',
                'prix': 0,
                'prix_text': '',
                'prix_type': '',
                'prix_m2': 0,
                'surface': 0,
                'surface_text': '',
                'ville': '',
                'region': '',
                'quartier': '',
                'adresse': '',
                'type_bien': 'Immobilier neuf',
                'standing': 'Standard',
                'statut_construction': 'Non spécifié',
                'date_livraison': '',
                'nombre_pieces': 0,
                'nombre_chambres': 0,
                'nombre_sdb': 0,
                'description_courte': '',
                'caracteristiques': [],
                'equipements': [],
                'images': [],
                'video_url': '',
                'video_id': '',
                'logo_agence': '',
                'nom_agence': '',
                'date_scraping': datetime.now().isoformat(),
                'page_source': 'search',
                'has_video': False,
                'is_valid': True
            }
            
            # 1. Promotion ID
            promotion_id = card.get('promotion-id', '')
            if promotion_id:
                data['promotion_id'] = promotion_id
                data['id'] = promotion_id
            
            # 2. URL - Utiliser la nouvelle méthode
            data['url'] = self.extract_url_from_card(card)
            
            # 3. Titre - AMÉLIORÉ pour éviter les points de suspension artificiels
            title_elem = card.find('h2')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Nettoyer les points de suspension multiples
                title_text = re.sub(r'\.{2,}', '...', title_text)
                data['titre'] = self.clean_text(title_text)
            
            # 4. Prix - chercher dans tout le texte
            all_text = card.get_text()
            
            # Chercher "À partir de X TND" - PATTERN AMÉLIORÉ
            price_patterns = [
                r'À partir de\s+([\d\s\.]+)\s+TND',
                r'Prix[\s:]*([\d\s\.]+)\s+TND',
                r'([\d\s\.]+)\s+TND'
            ]
            
            # D'abord chercher "Prix à consulter"
            if 'Prix à consulter' in all_text:
                data['prix_text'] = 'Prix à consulter'
                data['prix'] = 0
                data['prix_type'] = 'À consulter'
            else:
                # Chercher un prix numérique
                for pattern in price_patterns:
                    price_match = re.search(pattern, all_text)
                    if price_match:
                        price_text = price_match.group(0).strip()
                        data['prix_text'] = price_text
                        data['prix'], data['prix_type'] = self.extract_price(price_text)
                        if data['prix'] > 0:
                            break
                # Si pas de prix trouvé, mettre à consulter
                if not data['prix_text']:
                    data['prix_text'] = 'Prix non spécifié'
                    data['prix_type'] = 'Non spécifié'
            
            # 5. Standing et statut - AMÉLIORÉ pour gérer les virgules
            standing_elem = card.find('h4')
            if standing_elem:
                standing_text = standing_elem.get_text(strip=True)
                if standing_text:
                    # Nettoyer le texte
                    standing_text = standing_text.replace(',,', ',').strip()
                    
                    if ',' in standing_text:
                        parts = [part.strip() for part in standing_text.split(',')]
                        if len(parts) >= 2:
                            data['standing'] = self.extract_standing(parts[0])
                            data['statut_construction'] = self.extract_construction_status(parts[1])
                        elif len(parts) == 1:
                            data['standing'] = self.extract_standing(parts[0])
                    else:
                        # Vérifier si le texte contient à la fois standing et statut
                        if any(word in standing_text.lower() for word in ['haut', 'moyen', 'économique']):
                            data['standing'] = self.extract_standing(standing_text)
                        if any(word in standing_text.lower() for word in ['finalisé', 'en cours', 'projet', 'livraison']):
                            data['statut_construction'] = self.extract_construction_status(standing_text)
            
            # 6. Localisation - AMÉLIORÉ avec extraction de ville et quartier
            location_elem = card.find('h3')
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if location_text:
                    data['adresse'] = self.clean_text(location_text)
                    
                    # Extraire ville et quartier
                    data['ville'] = self.extract_city_from_location(location_text)
                    data['quartier'] = self.extract_neighborhood(location_text)
            
            # 7. Images
            img_tags = card.find_all('img')
            for img in img_tags[:10]:  # Limiter à 10 images
                src = img.get('src', '')
                
                if src and 'mubawab-media.com' in src:
                    if src not in data['images']:
                        data['images'].append(src)
                
                # Logo agence - DÉTECTION AMÉLIORÉE
                if 'logo' in src.lower() or '/logo/' in src or src.endswith('logo') or 'logo' in img.get('alt', '').lower():
                    data['logo_agence'] = src
            
            # 8. Surface - RECHERCHE AMÉLIORÉE
            # Chercher dans tout le texte avec différents patterns
            surface_patterns = [
                r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]',
                r'superficie\s*[:\-]?\s*(\d+(?:[,\s]\d+)*)',
                r'surface\s*[:\-]?\s*(\d+(?:[,\s]\d+)*)',
                r'(\d+(?:[,\s]\d+)*)\s*mètre'
            ]
            
            for pattern in surface_patterns:
                surface_match = re.search(pattern, all_text, re.IGNORECASE)
                if surface_match:
                    data['surface_text'] = surface_match.group(0)
                    data['surface'] = self.extract_surface(surface_match.group(0)) or 0
                    if data['surface'] > 0:
                        break
            
            # 9. Type de bien - AMÉLIORÉ
            data['type_bien'] = self.extract_property_type(all_text)
            
            # 10. Prix au m²
            data['prix_m2'] = self.extract_price_per_m2(all_text) or 0
            
            # 11. Calcul prix au m² si nécessaire
            if data['prix_m2'] == 0 and data['prix'] and data['prix'] > 0 and data['surface'] > 0:
                try:
                    data['prix_m2'] = data['prix'] / data['surface']
                except:
                    pass
            
            # 12. Description courte - AMÉLIORÉ pour éviter "En savoir plus"
            # Chercher les paragraphes descriptifs
            description_parts = []
            
            # Prendre les paragraphes qui ne sont pas des boutons
            paragraphs = card.find_all('p')
            for p in paragraphs[:3]:
                text = p.get_text(strip=True)
                if text and len(text) > 20 and 'En savoir plus' not in text and 'Contacter' not in text:
                    description_parts.append(text)
            
            if description_parts:
                description = ' '.join(description_parts)
                # Nettoyer "En savoir plus" à la fin
                description = re.sub(r'\s*En savoir plus\s*$', '', description, flags=re.IGNORECASE)
                data['description_courte'] = self.clean_text(description[:500])
            else:
                # Sinon, prendre les premières lignes du texte
                lines = all_text.split('\n')
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped and len(line_stripped) > 30:
                        if 'TND' not in line_stripped and 'm²' not in line_stripped:
                            data['description_courte'] = self.clean_text(line_stripped[:300])
                            break
            
            # 13. Caractéristiques
            data['caracteristiques'] = self.extract_promotion_features(all_text)
            
            # 14. Nombre de pièces
            data['nombre_pieces'] = self.extract_rooms(all_text) or 0
            
            # 15. Date de livraison - RECHERCHE AMÉLIORÉE
            data['date_livraison'] = self.extract_delivery_date(all_text)
            
            # 16. Vidéo
            video_url = self.extract_video_url(card)
            if video_url:
                data['video_url'] = video_url
                data['video_id'] = self.extract_youtube_id(video_url)
                data['has_video'] = True
            
            # Validation finale - BEAUCOUP PLUS FLEXIBLE
            # Accepter même les annonces avec "Prix à consulter"
            has_essential_data = data['promotion_id'] and data['titre']
            
            if has_essential_data:
                data['is_valid'] = True
                logger.debug(f"✅ Annonce validée: {data['promotion_id']} - {data['titre'][:50]}...")
                return data
            else:
                logger.debug(f"❌ Annonce rejetée: données insuffisantes (ID: {data['promotion_id']}, Titre: {data['titre'][:30]})")
                return None
                
        except Exception as e:
            logger.error(f"Erreur parsing carte: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
            
            # Statistiques images/vidéos
            total_images = 0
            total_videos = 0
            
            # Parser et valider
            valid_count = 0
            invalid_count = 0
            
            for i, card in enumerate(cards):
                try:
                    # Debug détaillé pour les premières cartes
                    if page_num == 1 and i < 3:
                        print(f"\n{'='*60}")
                        print(f"ANALYSE CARTE {i+1}")
                        print(f"{'='*60}")
                        
                        # Afficher promotion-id
                        promotion_id = card.get('promotion-id', 'N/A')
                        print(f"Promotion ID: {promotion_id}")
                        
                        # Afficher le texte complet
                        text_content = card.get_text(strip=True)
                        print(f"TEXTE COMPLET:\n{text_content}\n")
                    
                    # Valider et parser
                    if self.validate_listing_card(card):
                        listing_data = self.parse_listing_card(card)
                        
                        if listing_data and listing_data.get('is_valid', False):
                            listing_url = listing_data.get('url', '')
                            listing_id = listing_data.get('id', '')
                            
                            # Vérifier doublons
                            if listing_url and listing_url not in self.scraped_urls:
                                self.scraped_urls.add(listing_url)
                                if listing_id:
                                    self.scraped_ids.add(listing_id)
                                
                                # Compter images et vidéos
                                total_images += len(listing_data.get('images', []))
                                if listing_data.get('has_video'):
                                    total_videos += 1
                                
                                listings.append(listing_data)
                                valid_count += 1
                                self.stats['listings_found'] += 1
                                
                                # Afficher les données extraites pour debug
                                if page_num == 1 and i < 3:
                                    print(f"📊 DONNÉES EXTRACTES:")
                                    print(f"   ID: {listing_data.get('promotion_id', 'N/A')}")
                                    print(f"   Titre: {listing_data.get('titre', 'N/A')}")
                                    print(f"   Prix: {listing_data.get('prix', 'N/A')} {listing_data.get('prix_text', '')}")
                                    print(f"   Ville: {listing_data.get('ville', 'N/A')}")
                                    print(f"   Quartier: {listing_data.get('quartier', 'N/A')}")
                                    print(f"   Type: {listing_data.get('type_bien', 'N/A')}")
                                    print(f"   Standing: {listing_data.get('standing', 'N/A')}")
                                    print(f"   Statut: {listing_data.get('statut_construction', 'N/A')}")
                                    print(f"   Surface: {listing_data.get('surface', 'N/A')} {listing_data.get('surface_text', '')}")
                                    print(f"   URL: {listing_data.get('url', 'N/A')}")
                                    print()
                            
                            else:
                                invalid_count += 1
                                if page_num == 1 and i < 3:
                                    print(f"❌ Doublon: {listing_url}")
                        else:
                            invalid_count += 1
                            if page_num == 1 and i < 3:
                                print(f"❌ Carte {i+1} parsée mais non validée (ID: {card.get('promotion-id', 'N/A')})")
                    else:
                        invalid_count += 1
                        if page_num == 1 and i < 3:
                            print(f"❌ Carte {i+1} non validée par validate_listing_card()")
                            
                except Exception as e:
                    invalid_count += 1
                    logger.debug(f"Erreur carte {i}: {e}")
                    if page_num == 1 and i < 3:
                        print(f"💥 Erreur traitement carte {i}: {e}")
                    continue
            
            # Mettre à jour les statistiques
            self.stats['images_found'] += total_images
            self.stats['videos_found'] += total_videos
            self.stats['valid_cards_per_page'].append(valid_count)
            self.stats['invalid_cards_per_page'].append(invalid_count)
            
            logger.info(f"✅ PAGE {page_num}: {valid_count} annonces valides, {invalid_count} invalides")
            if total_images > 0:
                logger.info(f"📸 {total_images} images trouvées sur cette page")
            if total_videos > 0:
                logger.info(f"🎥 {total_videos} vidéos trouvées sur cette page")
            
            # Trouver la page suivante
            # Méthode 1: Chercher le lien "suivant" dans la pagination
            pagination = self.find_pagination(soup)
            if pagination:
                next_link = pagination.find('a', class_='next')
                if not next_link:
                    next_link = pagination.find('a', string=re.compile(r'suivant|next', re.I))
                
                if next_link and next_link.get('href'):
                    href = next_link.get('href')
                    next_url = urljoin('https://www.mubawab.tn', href)
                    
                    # Extraire le numéro de page
                    match = re.search(r'[:=]p[:=](\d+)', next_url)
                    if match:
                        next_page_num = int(match.group(1))
                    
                    has_next = True
                    logger.info(f"↪️  Lien suivant trouvé: page {next_page_num}")
            
            # Méthode 2: Construire l'URL suivante si pas trouvée
            if not has_next:
                if ':p:' in url:
                    next_url = re.sub(r':p:(\d+)', f':p:{next_page_num}', url)
                    has_next = True
                elif page_num == 1:
                    next_url = f"{url}:p:{next_page_num}"
                    has_next = True
            
            self.stats['pages_scraped'] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping page {page_num}: {e}")
            self.stats['errors'] += 1
        
        return listings, has_next, next_url, next_page_num
    
    def scrape_detailed_promotion(self, url: str) -> Dict:
        """Scrape les détails complets d'une promotion immobilière - VERSION AMÉLIORÉE"""
        details = {
            'description_complete': '',
            'caracteristiques_detaillees': {},
            'equipements_complets': [],
            'images_completes': [],
            'plans': [],
            'localisation_exacte': {},
            'informations_promotion': {},
            'conditions_vente': {},
            'promoteur_info': {},
            'contact_info': {},
            'videos_completes': [],
            'scraping_timestamp_detail': datetime.now().isoformat()
        }
        
        try:
            time.sleep(0.5)  # Pause pour éviter le blocage
            response = self.make_request(url)
            if not response:
                return details
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Description complète - AMÉLIORÉE
            desc_div = soup.find('div', class_='blockProp')
            if not desc_div:
                # Chercher d'autres conteneurs de description
                desc_div = soup.find('div', class_=re.compile(r'description|descBlock|propertyDesc|promotionDesc'))
            
            if desc_div:
                # Essayer d'extraire le texte sans les éléments indésirables
                # Supprimer les boutons "En savoir plus"
                for btn in desc_div.find_all(['button', 'a'], class_=re.compile(r'more|expand')):
                    btn.decompose()
                
                paragraphs = desc_div.find_all('p')
                if paragraphs:
                    description = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                else:
                    description = desc_div.get_text(strip=True)
                
                # Nettoyer les espaces multiples
                description = re.sub(r'\s+', ' ', description)
                details['description_complete'] = self.clean_text(description)
            
            # 2. Caractéristiques détaillées
            # Chercher dans la page de détail
            main_container = soup.find('div', class_='promotionPage')
            if main_container:
                # Extraire les badges (standing, statut, livraison)
                badge_divs = main_container.find_all('div', class_='immoBadge')
                for badge in badge_divs:
                    text = badge.get_text(strip=True)
                    if 'standing' in text.lower():
                        details['informations_promotion']['standing_detail'] = text
                    elif 'livraison' in text.lower():
                        details['informations_promotion']['date_livraison_detail'] = text
                    elif 'statut' in text.lower():
                        details['informations_promotion']['statut_detail'] = text
            
            # 3. Images complètes
            # Chercher dans le slider
            slider_div = soup.find('div', class_='picturesGallery')
            if slider_div:
                img_tags = slider_div.find_all('img', src=re.compile(r'mubawab-media\.com'))
            else:
                # Chercher dans toute la page
                img_tags = soup.find_all('img', src=re.compile(r'mubawab-media\.com/promotion/'))
            
            for img in img_tags[:30]:  # Limiter à 30 images
                src = img.get('src')
                if src and src not in details['images_completes']:
                    # Convertir en URL complète si nécessaire
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.mubawab.tn' + src
                    details['images_completes'].append(src)
            
            # 4. Vidéos
            iframe_tags = soup.find_all('iframe', src=re.compile(r'youtube\.com|youtu\.be'))
            for iframe in iframe_tags:
                src = iframe.get('src')
                if src and src not in details['videos_completes']:
                    details['videos_completes'].append(src)
                    youtube_id = self.extract_youtube_id(src)
                    if youtube_id and f"https://www.youtube.com/watch?v={youtube_id}" not in details['videos_completes']:
                        details['videos_completes'].append(f"https://www.youtube.com/watch?v={youtube_id}")
            
            # 5. Localisation exacte
            map_div = soup.find('div', class_='mapContainer')
            if map_div:
                # Chercher les coordonnées
                lat_input = soup.find('input', id='latField')
                lng_input = soup.find('input', id='lngField')
                
                if lat_input:
                    details['localisation_exacte']['latitude'] = lat_input.get('value', '')
                if lng_input:
                    details['localisation_exacte']['longitude'] = lng_input.get('value', '')
            
            # Adresse textuelle - RECHERCHE AMÉLIORÉE
            address_selectors = [
                ('h3', {'class': 'address'}),
                ('div', {'class': 'address'}),
                ('p', {'class': 'address'}),
                ('div', {'class': 'location'}),
                ('span', {'class': 'address'}),
                ('div', {'class': 'adresse'})
            ]
            
            for tag, attrs in address_selectors:
                address_elem = soup.find(tag, attrs)
                if address_elem:
                    address_text = address_elem.get_text(strip=True)
                    if address_text and len(address_text) > 5:
                        details['localisation_exacte']['adresse'] = address_text
                        break
            
            # 6. Informations sur le promoteur - AMÉLIORÉ
            agency_div = soup.find('div', class_='agencyLogoContainer')
            if agency_div:
                logo_img = agency_div.find('img')
                if logo_img and logo_img.get('src'):
                    details['promoteur_info']['logo'] = logo_img.get('src')
            
            agency_name_div = soup.find('div', class_='agencyName')
            if agency_name_div:
                details['promoteur_info']['nom'] = agency_name_div.get_text(strip=True)
            else:
                # Chercher ailleurs
                agency_span = soup.find('span', class_='agencyName')
                if agency_span:
                    details['promoteur_info']['nom'] = agency_span.get_text(strip=True)
            
            # 7. Caractéristiques architecturales
            full_text = soup.get_text().lower()
            
            # Nombre d'étages
            if 'étage' in full_text or 'niveau' in full_text:
                match = re.search(r'(\d+)\s*(?:étages|niveaux)', full_text)
                if match:
                    details['caracteristiques_detaillees']['nombre_etages'] = match.group(1)
            
            # Nombre d'appartements
            if 'appartement' in full_text:
                match = re.search(r'(\d+)\s*appartements', full_text)
                if match:
                    details['caracteristiques_detaillees']['nombre_appartements'] = match.group(1)
            
            # Surface des lots
            surface_matches = re.findall(r'(\d+(?:[,\s]\d+)*\.?\d*)\s*m[²2]', full_text)
            if surface_matches:
                surfaces = []
                for surf in surface_matches[:5]:  # Prendre les 5 premières surfaces
                    try:
                        surface_val = self.extract_surface(surf)
                        if surface_val:
                            surfaces.append(surface_val)
                    except:
                        pass
                if surfaces:
                    details['caracteristiques_detaillees']['surfaces_disponibles'] = surfaces
            
            # 8. Équipements - AMÉLIORÉ
            equip_list = []
            
            # Équipements standards
            standard_equip = [
                'ascenseur', 'parking', 'jardin', 'piscine', 'terrasse',
                'climatisation', 'chauffage', 'sécurité', 'vidéo surveillance',
                'concierge', 'salle de sport', 'spa', 'hammam', 'jacuzzi',
                'double vitrage', 'isolation', 'domotique', 'fibre optique',
                'cuisine équipée', 'salle de bain', 'garage'
            ]
            
            for equip in standard_equip:
                if equip in full_text:
                    # Formater correctement
                    if equip == 'salle de sport':
                        equip_fr = 'Salle de sport'
                    elif equip == 'vidéo surveillance':
                        equip_fr = 'Vidéo surveillance'
                    elif equip == 'cuisine équipée':
                        equip_fr = 'Cuisine équipée'
                    elif equip == 'salle de bain':
                        equip_fr = 'Salle de bain'
                    elif equip == 'fibre optique':
                        equip_fr = 'Fibre optique'
                    elif equip == 'double vitrage':
                        equip_fr = 'Double vitrage'
                    else:
                        equip_fr = equip.capitalize()
                    
                    if equip_fr not in equip_list:
                        equip_list.append(equip_fr)
            
            details['equipements_complets'] = list(set(equip_list))
            
            # 9. Conditions de vente
            if 'facilité' in full_text or 'paiement' in full_text or 'crédit' in full_text:
                details['conditions_vente']['facilites_paiement'] = 'Disponibles'
            
            if 'apport' in full_text:
                match = re.search(r'apport\s*[:\-]?\s*(\d[\d\s]*)\s*%', full_text)
                if match:
                    details['conditions_vente']['pourcentage_apport'] = match.group(1).replace(' ', '')
            
            # 10. Informations de contact
            contact_form = soup.find('form', id='leadForm')
            if contact_form:
                details['contact_info']['formulaire_contact'] = 'Disponible'
            
            phone_links = soup.find_all('a', onclick=re.compile(r'showPhone|sendPhone'))
            if phone_links:
                details['contact_info']['telephone_disponible'] = 'Oui'
            
            # 11. Plans (si disponibles)
            plan_imgs = soup.find_all('img', src=re.compile(r'plan|schéma|layout', re.I))
            for img in plan_imgs[:5]:  # Limiter à 5 plans
                src = img.get('src')
                if src and src not in details['plans']:
                    details['plans'].append(src)
            
        except Exception as e:
            logger.error(f"Erreur détails {url}: {e}")
        
        return details
    
    def scrape_all_promotions(self, max_pages: int = 0, get_details: bool = True, filters: Dict = None) -> List[Dict]:
        """Scrape toutes les promotions immobilières"""
        logger.info(f"🚀 DÉBUT SCRAPING IMMOBILIER NEUF")
        
        all_listings = []
        
        # Détection initiale
        first_url = self.build_search_url(filters, 1)
        total_ads, total_pages, ads_per_page = self.detect_total_ads_and_pages(first_url)
        
        if total_ads == 0:
            logger.warning(f"⚠️  AUCUNE ANNONCE DÉTECTÉE")
            return []
        
        self.stats['total_ads_detected'] = total_ads
        
        # Calculer combien scraper
        if max_pages > 0:
            pages_to_scrape = min(max_pages, total_pages)
        else:
            pages_to_scrape = total_pages
        
        max_ads = pages_to_scrape * ads_per_page
        
        logger.info(f"📊 DÉTECTION: {total_ads} annonces au total")
        logger.info(f"📄 Objectif: {pages_to_scrape}/{total_pages} pages")
        logger.info(f"📈 Estimation: {ads_per_page} annonces par page")
        logger.info(f"🎯 Maximum: {max_ads} annonces")
        
        # Scraper page par page
        current_page = 1
        current_url = first_url
        ads_scraped = 0
        consecutive_empty_pages = 0
        errors_count = 0
        
        while (current_page <= pages_to_scrape and 
               ads_scraped < max_ads and 
               consecutive_empty_pages < 3):
            
            try:
                print(f"\n{'='*50}")
                print(f"🏢 IMMOBILIER NEUF - Page {current_page}/{pages_to_scrape}")
                print(f"📊 Progression: {ads_scraped}/{max_ads} annonces")
                print(f"{'='*50}")
                
                # Scraper la page
                page_listings, has_next, next_url, next_page_num = self.scrape_page_listings(
                    current_url, current_page
                )
                
                # Vérifier si la page est vide
                if not page_listings:
                    logger.warning(f"⚠️  PAGE {current_page} VIDE")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= 3:
                        logger.error(f"❌ 3 PAGES VIDES CONSÉCUTIVES - ARRÊT")
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
                                details = self.scrape_detailed_promotion(listing['url'])
                                
                                # Fusionner les données
                                listing.update({
                                    'description_complete': details.get('description_complete', ''),
                                    'caracteristiques_detaillees': json.dumps(details.get('caracteristiques_detaillees', {}), ensure_ascii=False),
                                    'equipements_complets': '; '.join(details.get('equipements_complets', [])),
                                    'images_completes': '; '.join(details.get('images_completes', [])[:20]),  # Limiter à 20
                                    'plans': '; '.join(details.get('plans', [])),
                                    'localisation_exacte': json.dumps(details.get('localisation_exacte', {}), ensure_ascii=False),
                                    'informations_promotion': json.dumps(details.get('informations_promotion', {}), ensure_ascii=False),
                                    'conditions_vente': json.dumps(details.get('conditions_vente', {}), ensure_ascii=False),
                                    'promoteur_info': json.dumps(details.get('promoteur_info', {}), ensure_ascii=False),
                                    'contact_info': json.dumps(details.get('contact_info', {}), ensure_ascii=False),
                                    'videos_completes': '; '.join(details.get('videos_completes', []))
                                })
                                
                                # Afficher progression
                                if (i + 1) % 5 == 0 or (i + 1) == total_details:
                                    progress = ((i + 1) / total_details) * 100
                                    logger.info(f"  📊 Détails: {i+1}/{total_details} ({progress:.0f}%)")
                                
                                # Pause entre les détails
                                time.sleep(0.5)
                                
                        except Exception as e:
                            logger.warning(f"Erreur détails annonce {i}: {e}")
                            errors_count += 1
                            continue
                
                # Ajouter aux résultats
                all_listings.extend(page_listings)
                ads_scraped = len(all_listings)
                
                logger.info(f"📈 Total: {ads_scraped}/{max_ads} annonces accumulées")
                
                # Vérifier si on continue
                if ads_scraped >= max_ads:
                    logger.info(f"🎯 OBJECTIF ATTEINT: {ads_scraped} annonces")
                    all_listings = all_listings[:max_ads]
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
                errors_count += 1
                self.stats['errors'] += 1
                
                # Essayer de continuer
                if current_page < pages_to_scrape:
                    current_page += 1
                    current_url = self.build_search_url(filters, current_page)
                    time.sleep(5)
                else:
                    break
        
        # Statistiques par type de bien
        type_counts = {}
        for listing in all_listings:
            prop_type = listing.get('type_bien', 'Inconnu')
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
        
        self.stats['types_stats'] = type_counts
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
            
            # Ordre logique pour immobilier neuf
            preferred_order = [
                'id', 'promotion_id', 'titre', 'url', 'ville', 'region', 'quartier', 'adresse',
                'type_bien', 'standing', 'statut_construction', 'date_livraison',
                'prix', 'prix_text', 'prix_type', 'prix_m2', 'surface', 'surface_text',
                'nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'description_courte', 'description_complete',
                'caracteristiques', 'equipements', 'equipements_complets', 'images', 'images_completes',
                'video_url', 'video_id', 'videos_completes', 'has_video', 'plans',
                'logo_agence', 'nom_agence',
                'caracteristiques_detaillees', 'localisation_exacte', 'informations_promotion',
                'conditions_vente', 'promoteur_info', 'contact_info', 'date_scraping', 
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
                    'scraping_stats': self.stats,
                    'fields_count': len(listings[0]) if listings else 0,
                    'source_url': self.base_url,
                    'scraping_type': 'immobilier_neuf'
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
        print("📊 STATISTIQUES FINALES DU SCRAPING IMMOBILIER NEUF")
        print("="*80)
        
        print(f"\n📈 PERFORMANCE GÉNÉRALE:")
        print(f"   Pages scrapées: {self.stats['pages_scraped']}")
        print(f"   Annonces détectées: {self.stats['total_ads_detected']}")
        print(f"   Annonces trouvées: {self.stats['listings_found']}")
        print(f"   Annonces finales: {self.stats['listings_scraped']}")
        print(f"   Erreurs: {self.stats['errors']}")
        
        if self.stats.get('images_found', 0) > 0:
            print(f"\n🖼️  MÉDIAS:")
            print(f"   Images trouvées: {self.stats['images_found']}")
            if self.stats.get('videos_found', 0) > 0:
                print(f"   Vidéos trouvées: {self.stats['videos_found']}")
        
        if self.stats['valid_cards_per_page']:
            avg_valid = sum(self.stats['valid_cards_per_page']) / len(self.stats['valid_cards_per_page'])
            total_invalid = sum(self.stats['invalid_cards_per_page'])
            print(f"\n📈 QUALITÉ DU SCRAPING:")
            print(f"   Moyenne annonces/page: {avg_valid:.1f}")
            print(f"   Total éléments invalides: {total_invalid}")
            if self.stats['listings_found'] > 0:
                taux_valid = (self.stats['listings_found'] / (self.stats['listings_found'] + total_invalid)) * 100
                print(f"   Taux de validité: {taux_valid:.1f}%")
        
        if self.stats.get('types_stats'):
            print(f"\n🏘️  RÉPARTITION PAR TYPE DE BIEN:")
            total = self.stats['listings_scraped']
            for prop_type, count in sorted(self.stats['types_stats'].items(), key=lambda x: x[1], reverse=True):
                pourcentage = (count / total) * 100 if total > 0 else 0
                print(f"   {prop_type}: {count} ({pourcentage:.1f}%)")
        
        print("\n" + "="*80)


def main():
    """Programme principal"""
    print("\n" + "="*80)
    print("🏢 SCRAPER MUBAWAB ULTIMATE - IMMOBILIER NEUF (VERSION FINALE)")
    print("🎯 URL: https://www.mubawab.tn/fr/listing-promotion")
    print("🎯 DÉTECTION AUTOMATIQUE - EXTRACTION COMPLÈTE")
    print("="*80)
    
    # Configuration
    print("\n📋 CONFIGURATION DU SCRAPING")
    
    # Filtres optionnels
    print("\n🎯 FILTRES DISPONIBLES (laisser vide pour tous):")
    
    filters = {}
    
    ville = input("Ville (ex: La Marsa, Tunis, Sousse): ").strip()
    if ville:
        filters['city'] = ville
    
    print("\n🏠 TYPES DE BIEN:")
    print("  1. Tous les types")
    print("  2. Appartements")
    print("  3. Maisons")
    print("  4. Villas")
    print("  5. Bureaux")
    print("  6. Terrains")
    print("  7. Locaux commerciaux")
    
    type_choice = input("\nChoisissez (1-7): ").strip()
    type_map = {
        '2': 'appartements',
        '3': 'maisons',
        '4': 'villas',
        '5': 'bureaux',
        '6': 'terrains',
        '7': 'locaux-commerciaux'
    }
    if type_choice in type_map:
        filters['property_type'] = type_map[type_choice]
    
    min_price = input("\n💰 Prix minimum (en TND, laisser vide pour aucun): ").strip()
    if min_price and min_price.isdigit():
        filters['min_price'] = min_price
    
    max_price = input("💰 Prix maximum (en TND, laisser vide pour aucun): ").strip()
    if max_price and max_price.isdigit():
        filters['max_price'] = max_price
    
    # Nombre de pages à scraper
    print("\n📊 NOMBRE DE PAGES À SCRAPER:")
    print("  0. Toutes les pages disponibles")
    print("  1. 5 pages")
    print("  2. 10 pages")
    print("  3. 20 pages")
    print("  4. 50 pages")
    print("  5. Personnalisé")
    
    pages_choice = input("\n🎯 Choisissez (0-5): ").strip()
    
    if pages_choice == '0':
        max_pages = 0  # Toutes
    elif pages_choice == '1':
        max_pages = 5
    elif pages_choice == '2':
        max_pages = 10
    elif pages_choice == '3':
        max_pages = 20
    elif pages_choice == '4':
        max_pages = 50
    elif pages_choice == '5':
        try:
            max_pages = int(input("Entrez le nombre de pages: "))
        except:
            max_pages = 10
    else:
        max_pages = 10
    
    # Détails
    details_choice = input("\n🔍 Extraire les détails complets? (o/n, recommandé: o): ").strip().lower()
    get_details = details_choice in ['o', 'oui', 'y', 'yes', '']
    
    # Résumé
    print("\n" + "="*80)
    print("🚀 RÉSUMÉ DE LA CONFIGURATION")
    print("="*80)
    
    if filters:
        print(f"   🔍 Filtres appliqués:")
        if filters.get('city'):
            print(f"      Ville: {filters['city']}")
        if filters.get('property_type'):
            print(f"      Type: {filters['property_type']}")
        if filters.get('min_price'):
            print(f"      Prix min: {filters['min_price']} TND")
        if filters.get('max_price'):
            print(f"      Prix max: {filters['max_price']} TND")
    else:
        print(f"   🔍 Filtres: Aucun (tous les biens)")
    
    print(f"   📊 Pages: {'TOUTES' if max_pages == 0 else max_pages}")
    print(f"   🔍 Détails: {'✅ OUI' if get_details else '❌ NON'}")
    print(f"   🌐 URL: https://www.mubawab.tn/fr/listing-promotion")
    print("="*80)
    
    if max_pages == 0 or max_pages > 20:
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
    print(f"📍 Source: Immobilier neuf Mubawab")
    print(f"📁 Les fichiers seront sauvegardés dans le dossier courant")
    print(f"⏳ Veuillez patienter, cela peut prendre du temps...")
    print(f"📊 La détection automatique va calculer le nombre total d'annonces")
    
    try:
        scraper = MubawabImmobilierNeufUltimateScraper(delay=1.0)
        
        start_time = datetime.now()
        listings = scraper.scrape_all_promotions(max_pages, get_details, filters)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        if listings:
            # Préparer fichiers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"mubawab_immobilier_neuf_complet_{timestamp}"
            
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
            print(f"   {len(listings)} annonces d'immobilier neuf complètement scrapées")
            
            # Aperçu
            print(f"\n📋 APERÇU DES DONNÉES:")
            if listings:
                df_preview = []
                for i, listing in enumerate(listings[:3]):
                    df_preview.append({
                        'ID': listing.get('promotion_id', listing.get('id', '')),
                        'Titre': listing.get('titre', '')[:40] + '...' if len(listing.get('titre', '')) > 40 else listing.get('titre', ''),
                        'Ville': listing.get('ville', ''),
                        'Quartier': listing.get('quartier', ''),
                        'Type': listing.get('type_bien', ''),
                        'Standing': listing.get('standing', ''),
                        'Statut': listing.get('statut_construction', ''),
                        'Surface': f"{listing.get('surface', 0):,.0f} m²" if listing.get('surface', 0) > 0 else listing.get('surface_text', ''),
                        'Prix': f"{listing.get('prix', 0):,.0f} TND" if listing.get('prix', 0) > 0 else listing.get('prix_text', ''),
                        'Livraison': listing.get('date_livraison', '')
                    })
                
                for item in df_preview:
                    print(f"  • {item['ID']} - {item['Titre']}")
                    print(f"    {item['Ville']} ({item['Quartier']}) | {item['Type']} | {item['Standing']} | {item['Statut']}")
                    print(f"    {item['Surface']} | {item['Prix']} | Livraison: {item['Livraison']}")
                    print()
            
            print(f"\n🔧 POUR EXCEL:")
            print(f"   1. Ouvrez le fichier CSV dans Excel")
            print(f"   2. Utilisez 'Toutes les données' > 'Depuis un fichier texte/CSV'")
            print(f"   3. Encodage: UTF-8")
            print(f"   4. Délimiteur: Virgule")
            print(f"   5. Appliquez des filtres pour analyser par type/ville/standing")
            
            print(f"\n🎯 CARACTÉRISTIQUES EXTRITES:")
            print(f"   • Informations de base (titre, prix, surface, localisation)")
            print(f"   • Détails de construction (standing, statut, date livraison)")
            print(f"   • Images et vidéos (URLs complètes)")
            print(f"   • Caractéristiques et équipements")
            print(f"   • Informations promoteur et contact")
            print(f"   • Conditions de vente et facilités de paiement")
            
        else:
            print("\n❌ AUCUNE DONNÉE SCRAPÉE")
            print("   Causes possibles:")
            print("   - Site inaccessible")
            print("   - Aucune annonce trouvée avec les filtres sélectionnés")
            print("   - Structure du site modifiée")
            print("   - Problème de connexion internet")
            print("   Vérifiez le fichier log: mubawab_immobilier_neuf_ultimate.log")
    
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