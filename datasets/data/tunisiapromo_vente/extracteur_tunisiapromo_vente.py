"""
Agent d'extraction pour Tunisia Promo - Vente
Extrait TOUS les champs possibles des annonces de vente
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import unicodedata


# ========== CONSTANTES ==========

TYPES_BIENS = [
    'appartement', 'villa', 'maison', 'terrain', 'studio', 'local commercial', 'bureau'
]

ETATS_BIEN = {
    'neuf': 'Neuf',
    'jamais habité': 'Jamais habité',
    'jamais habite': 'Jamais habité',
    'bon état': 'Bon état',
    'très bon état': 'Très bon état',
    'excellent état': 'Excellent état',
    'rénové': 'Rénové',
    'en cours de finition': 'En cours de finition'
}

TITRES_FONCIERS = {
    'titre bleu': 'Titre bleu',
    'titre foncier': 'Titre foncier',
    'titre': 'Titre'
}

OPTIONS_MAPPING = {
    'ascenseur': 'Ascenseur',
    'balcon': 'Balcon',
    'chauffage': 'Chauffage',
    'climatisation': 'Climatisation',
    'cuisine équipée': 'Cuisine équipée',
    'meublé': 'Meublé',
    'parking': 'Parking',
    'terrasse': 'Terrasse',
    'jardin': 'Jardin',
    'piscine': 'Piscine',
    'cheminée': 'Cheminée',
    'interphone': 'Interphone',
    'haut standing': 'Haut standing',
    'vue sur mer': 'Vue sur mer',
    'vue mer': 'Vue sur mer',
    'gardien': 'Gardien',
    'caméras': 'Caméras',
    'digicode': 'Digicode',
    'securisé': 'Sécurisé'
}

VILLES_TUNISIE = [
    'tunis', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'le kram', 'salammbô', 'ariana', 'ennasr', 'manzah', 'soukra',
    'raoued', 'ain zaghouan', 'aouina', 'bhar lazreg', 'jardins de carthage',
    'ben arous', 'boumhel', 'mohammedia', 'nabeul', 'hammamet',
    'sousse', 'hammam sousse', 'monastir', 'mahdia', 'sfax', 'bizerte',
    'tazarka', 'korba', 'kélibia', 'yasmine hammamet', 'hiboun', 'baghdadi'
]

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'tazarka': 'Nabeul', 'korba': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte'
}


# ========== FONCTIONS UTILITAIRES ==========

def normalize_text(text: str) -> str:
    """Normalise le texte"""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_number_from_text(text: str) -> Optional[float]:
    """Extrait le premier nombre d'un texte"""
    if not text:
        return None
    numbers = re.findall(r'\d+[.,]?\d*', text.replace(' ', ''))
    if numbers:
        try:
            return float(numbers[0].replace(',', '.'))
        except:
            return None
    return None


def clean_number(value: Any) -> Optional[float]:
    """Nettoie une valeur numérique"""
    if value is None:
        return None
    
    try:
        if isinstance(value, (int, float)):
            return float(value) if isinstance(value, float) else int(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'\s+', '', value)
            if ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            if cleaned.replace('.', '').replace('-', '').isdigit():
                if '.' in cleaned:
                    return float(cleaned)
                else:
                    return int(cleaned)
    except:
        pass
    
    return None


def clean_date(date_str: str) -> Optional[str]:
    """Nettoie et normalise une date"""
    if not date_str or 'Annonce' in date_str:
        return None
    
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, date_str)
    if match:
        return match.group(1)
    
    return None


# ========== EXTRACTION DES CARACTÉRISTIQUES ==========

def extract_surfaces(description: str) -> Dict[str, Any]:
    """Extrait les surfaces de la description"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    result = {}
    
    # Surface habitable
    habitable_patterns = [
        r'surface\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m[²2]',
        r'(\d+)\s*m[²2]\s*(?:habitables?)?',
        r'superficie\s*(?:couverte)?\s*[:\-]?\s*(\d+)\s*m²',
        r'metrage\s*(\d+)\s*m2',
        r'superficie\s+bâtie\s*[:\-]?\s*(\d+)\s*m²'
    ]
    
    for pattern in habitable_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['surface_habitable'] = float(m.group(1))
                break
            except:
                pass
    
    # Surface terrain
    terrain_patterns = [
        r'terrain\s+de\s*(\d+)\s*m[²2]',
        r'terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+du\s+terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'superficie\s+terrain\s*[:\-]?\s*(\d+)\s*m²'
    ]
    
    for pattern in terrain_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['surface_terrain'] = float(m.group(1))
                break
            except:
                pass
    
    return result


def extract_nombres(description: str) -> Dict[str, Any]:
    """Extrait les nombres de pièces, chambres, salles de bain"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    result = {}
    
    # Nombre de pièces
    pieces_patterns = [
        r'(\d+)\s*pi[èe]ces?',
        r'(\d+)\s*pièces?'
    ]
    
    for pattern in pieces_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['pieces'] = int(m.group(1))
                break
            except:
                pass
    
    # Nombre de chambres
    chambres_patterns = [
        r'(\d+)\s*chambres?',
        r'(\d+)\s*chambres?\s*à\s*coucher'
    ]
    
    for pattern in chambres_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['chambres'] = int(m.group(1))
                break
            except:
                pass
    
    # Nombre de salles de bain
    sdb_patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'(\d+)\s*sdb',
        r'(\d+)\s*salles?\s*de\s*douche'
    ]
    
    for pattern in sdb_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['salles_bain'] = int(m.group(1))
                break
            except:
                pass
    
    return result


def extract_etage(description: str) -> Optional[int]:
    """Extrait le numéro d'étage"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'au\s+(\d+)[eè]me?\s*[eé]tage',
        r'(\d+)[eè]me?\s*[eé]tage',
        r'(\d+)è\s*étage',
        r'(\d+)er\s*étage',
        r'(\d+)eme?\s*étage',
        r'rez-de-chaussée',
        r'rdc'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            if 'rez' in pattern or 'rdc' in pattern:
                return 0
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_etat_bien(description: str) -> Optional[str]:
    """Extrait l'état du bien"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for key, value in ETATS_BIEN.items():
        if key in desc_lower:
            return value
    
    return None


def extract_titre_foncier(description: str) -> Optional[str]:
    """Extrait le type de titre foncier"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for key, value in TITRES_FONCIERS.items():
        if key in desc_lower:
            return value
    
    return None


def extract_annee_construction(description: str) -> Optional[int]:
    """Extrait l'année de construction"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'construit[e]?\s+en\s+(\d{4})',
        r'construction\s+(\d{4})',
        r'(\d{4})\s*construction',
        r'neuve\s+(\d{4})'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_presence_ascenseur(description: str) -> bool:
    """Détecte la présence d'un ascenseur"""
    return 'ascenseur' in description.lower()


def extract_presence_parking(description: str) -> bool:
    """Détecte la présence de parking"""
    desc_lower = description.lower()
    return 'parking' in desc_lower or 'place parking' in desc_lower


def extract_nombre_parking(description: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'(\d+)\s*place[s]?\s*(?:de)?\s*parking',
        r'parking\s*(\d+)\s*places?',
        r'parking\s*sous[\s-]*sol'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            if 'sous-sol' in pattern:
                return 1
            try:
                return int(m.group(1))
            except:
                pass
    
    return 1 if extract_presence_parking(description) else None


def extract_type_parking(description: str) -> Optional[str]:
    """Extrait le type de parking"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'sous-sol' in desc_lower or 'sous sol' in desc_lower:
        return 'Sous-sol'
    elif 'couvert' in desc_lower:
        return 'Couvert'
    
    return None


def extract_presence_piscine(description: str) -> bool:
    """Détecte la présence d'une piscine"""
    return 'piscine' in description.lower()


def extract_presence_jardin(description: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in description.lower()


def extract_presence_terrasse(description: str) -> bool:
    """Détecte la présence d'une terrasse"""
    return 'terrasse' in description.lower()


def extract_presence_balcon(description: str) -> bool:
    """Détecte la présence d'un balcon"""
    return 'balcon' in description.lower()


def extract_presence_climatisation(description: str) -> bool:
    """Détecte la présence de climatisation"""
    return 'climatisation' in description.lower() or 'climatisé' in description.lower()


def extract_presence_chauffage(description: str) -> bool:
    """Détecte la présence de chauffage"""
    return 'chauffage' in description.lower()


def extract_type_chauffage(description: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'chauffage central' in desc_lower:
        return 'Central'
    
    return None


def extract_presence_securite(description: str) -> bool:
    """Détecte la présence de sécurité"""
    desc_lower = description.lower()
    keywords = ['gardien', 'caméras', 'surveillance', 'digicode', 'sécurisé', 'securise']
    return any(keyword in desc_lower for keyword in keywords)


def extract_vue(description: str) -> Optional[str]:
    """Extrait le type de vue"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'vue sur mer' in desc_lower:
        return 'Mer'
    elif 'vue mer' in desc_lower:
        return 'Mer'
    elif 'vue sur piscine' in desc_lower:
        return 'Piscine'
    elif 'vue sur jardin' in desc_lower:
        return 'Jardin'
    elif 'vue dégagée' in desc_lower:
        return 'Dégagée'
    
    return None


def extract_distance_mer(description: str) -> Optional[str]:
    """Extrait la distance à la mer"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'à\s*(\d+[.,]?\d*)\s*km\s*de\s*la\s*plage',
        r'à\s*(\d+[.,]?\d*)\s*m\s*de\s*la\s*plage',
        r'(\d+[.,]?\d*)\s*km\s*de\s*la\s*plage',
        r'proche\s*de\s*la\s*plage',
        r'près\s*de\s*la\s*plage'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            if 'proche' in pattern or 'près' in pattern:
                return 'Proche'
            try:
                distance = float(m.group(1).replace(',', '.'))
                if distance < 1:
                    return f"{int(distance * 1000)}m"
                else:
                    return f"{distance}km"
            except:
                return 'Proche'
    
    return None


def extract_proximites(description: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    if not description:
        return []
    
    desc_lower = description.lower()
    proximites = []
    
    keywords = {
        'plage': 'Plage',
        'mer': 'Mer',
        'centre ville': 'Centre-ville',
        'centre-ville': 'Centre-ville',
        'commerces': 'Commerces',
        'magasins': 'Commerces',
        'école': 'École',
        'lycée': 'Lycée',
        'collège': 'Collège',
        'transport': 'Transports',
        'bus': 'Bus',
        'route': 'Route'
    }
    
    for keyword, label in keywords.items():
        if keyword in desc_lower:
            if label not in proximites:
                proximites.append(label)
    
    return sorted(proximites)


def extract_est_promoteur_direct(description: str) -> bool:
    """Détecte si la vente est directe promoteur"""
    desc_lower = description.lower()
    keywords = ['direct promoteur', 'directement promoteur', 'promoteur direct']
    return any(keyword in desc_lower for keyword in keywords)


def extract_frais_enregistrement(description: str) -> Optional[str]:
    """Extrait les frais d'enregistrement"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'frais\s*d\'enregistrement\s*(\d+)\s*%',
        r'enregistrement\s*(\d+)\s*%',
        r'droit\s*d\'enregistrement\s*(\d+)\s*%'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            return f"{m.group(1)}%"
    
    return None


def extract_telephone(description: str) -> Optional[str]:
    """Extrait le numéro de téléphone de la description"""
    if not description:
        return None
    
    patterns = [
        r'(?:\+216|00216|216)?\s*(\d[\d\s]{7,})',
        r't[eé]l[eé]phone\s*[:\-]?\s*(\d[\d\s]{7,})',
        r'contact\s*(?:\s*:)?\s*(\d[\d\s]{7,})',
        r'whatsapp[:\s]*(\d[\d\s]{7,})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description)
        if m:
            tel = re.sub(r'\s', '', m.group(1))
            if len(tel) >= 8:
                if not tel.startswith('+216') and len(tel) == 8:
                    return f"+216{tel}"
                return tel
    
    return None


def extract_email(description: str) -> Optional[str]:
    """Extrait l'email de la description"""
    if not description:
        return None
    
    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    m = re.search(pattern, description)
    if m:
        return m.group(0)
    
    return None


def extract_site_web(description: str) -> Optional[str]:
    """Extrait le site web de la description"""
    if not description:
        return None
    
    patterns = [
        r'www\.[a-zA-Z0-9\.\-]+\.(?:com|tn|fr|net|org)',
        r'https?://[^\s]+'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description)
        if m:
            url = m.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    
    return None


def extract_ville_from_description(description: str) -> Optional[str]:
    """Extrait la ville depuis la description"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for ville in VILLES_TUNISIE:
        if ville in desc_lower:
            return ville.title()
    
    return None


# ========== EXTRACTION POUR LES TERRAINS ==========

def extract_caracteristiques_terrain(description: str) -> Dict[str, Any]:
    """Extrait les caractéristiques spécifiques aux terrains"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    result = {}
    
    # Forme du terrain
    if 'carré' in desc_lower or 'carre' in desc_lower:
        result['forme_terrain'] = 'Carré'
    elif 'rectangulaire' in desc_lower:
        result['forme_terrain'] = 'Rectangulaire'
    
    # Façade
    facade_patterns = [
        r'façade\s+de\s*(\d+)\s*m',
        r'façade\s+(\d+)\s*m',
        r'largeur\s+(\d+)\s*m'
    ]
    
    for pattern in facade_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                result['façade_m'] = float(m.group(1))
                break
            except:
                pass
    
    # Accès à la route
    if 'route goudronnée' in desc_lower or 'route secondaire' in desc_lower:
        result['acces_route'] = 'Oui'
    
    # Clôture
    if 'clôturé' in desc_lower or 'cloture' in desc_lower:
        result['cloture'] = True
    
    # Réseaux
    result['reseau_eau'] = 'eau' in desc_lower or 'puit' in desc_lower
    result['reseau_electricite'] = 'électricité' in desc_lower or 'electricite' in desc_lower
    result['reseau_assainissement'] = 'assainissement' in desc_lower
    
    # Puits
    if 'puit' in desc_lower:
        result['a_puit'] = True
    
    return result


# ========== EXTRACTION DEPUIS LES OPTIONS ==========

def normalize_options(options: List[str]) -> List[str]:
    """Normalise la liste des options"""
    if not options:
        return []
    
    normalized = []
    
    for option in options:
        if not isinstance(option, str):
            continue
        
        option_lower = option.lower().strip()
        
        for key, value in OPTIONS_MAPPING.items():
            if key in option_lower:
                if value not in normalized:
                    normalized.append(value)
                break
        else:
            normalized.append(option.strip().title())
    
    return sorted(normalized)


# ========== EXTRACTION DEPUIS L'URL ==========

def extract_reference_from_url(url: str) -> Optional[str]:
    """Extrait la référence depuis l'URL"""
    if not url:
        return None
    
    match = re.search(r'-z(\d+)\.html', url)
    if match:
        return match.group(1)
    
    return None


# ========== EXTRACTION DES IMAGES ==========

def extract_images_list(images_urls: Any, nombre_photos: Any) -> List[str]:
    """Extrait la liste des images"""
    if images_urls and isinstance(images_urls, list):
        return images_urls
    
    return []


# ========== FONCTION PRINCIPALE D'EXTRACTION ==========

def extract_all_from_annonce(annonce: Dict) -> Dict[str, Any]:
    """
    Extrait TOUS les champs possibles d'une annonce de vente Tunisia Promo
    """
    extracted = {}
    
    # ===== 1. DONNÉES DE BASE =====
    extracted['annonce_id'] = str(annonce.get('annonce_id', ''))
    extracted['url'] = annonce.get('url', '')
    extracted['titre'] = normalize_text(annonce.get('titre', ''))
    extracted['date_scraping'] = annonce.get('date_scraping', '')
    extracted['page_trouvee'] = annonce.get('page_trouvee', 0)
    extracted['statut'] = annonce.get('statut', 'inchangé')
    extracted['reference'] = annonce.get('reference', '') or extract_reference_from_url(extracted['url'])
    extracted['type_offre'] = annonce.get('type_offre', 'Vente')
    
    # ===== 2. TYPE DE BIEN =====
    extracted['type_bien'] = annonce.get('type_bien', '')
    
    # ===== 3. PRIX =====
    prix = clean_number(annonce.get('prix'))
    extracted['prix'] = prix if prix and prix > 0 else 0
    if prix and prix > 0:
        extracted['prix_text'] = f"{int(prix):,} TND".replace(',', ' ')
    else:
        extracted['prix_text'] = "Prix à consulter"
    
    # ===== 4. LOCALISATION =====
    extracted['region'] = annonce.get('region', '')
    extracted['ville'] = annonce.get('ville', '')
    extracted['adresse'] = normalize_text(annonce.get('adresse', ''))
    extracted['code_postal'] = annonce.get('code_postal', '')
    
    # Si ville manquante, essayer de l'extraire de l'adresse
    if not extracted['ville'] and extracted['adresse']:
        adresse_lower = extracted['adresse'].lower()
        for ville in VILLES_TUNISIE:
            if ville in adresse_lower:
                extracted['ville'] = ville.title()
                break
    
    # ===== 5. ÉTAT DU BIEN =====
    if annonce.get('etat_bien'):
        extracted['etat_bien'] = annonce.get('etat_bien')
    
    # ===== 6. DESCRIPTION =====
    description = annonce.get('description', '')
    extracted['description'] = normalize_text(description)
    
    # ===== 7. CARACTÉRISTIQUES DU BIEN =====
    # Surfaces
    surfaces = extract_surfaces(description)
    if surfaces.get('surface_habitable'):
        extracted['surface_habitable'] = surfaces['surface_habitable']
    elif annonce.get('surface_habitable'):
        extracted['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
    
    if surfaces.get('surface_terrain'):
        extracted['surface_terrain'] = surfaces['surface_terrain']
    
    # Nombres
    nombres = extract_nombres(description)
    if nombres.get('pieces'):
        extracted['pieces'] = nombres['pieces']
    elif annonce.get('pieces'):
        extracted['pieces'] = clean_number(annonce.get('pieces'))
    
    if nombres.get('chambres'):
        extracted['chambres'] = nombres['chambres']
    
    if nombres.get('salles_bain'):
        extracted['salles_bain'] = nombres['salles_bain']
    
    # Places voiture
    if annonce.get('places_voiture'):
        extracted['places_voiture'] = clean_number(annonce.get('places_voiture'))
    
    # Année construction
    if annonce.get('annee_construction'):
        extracted['annee_construction'] = clean_number(annonce.get('annee_construction'))
    
    # ===== 8. EXTRACTIONS DEPUIS LA DESCRIPTION =====
    if description:
        # Étage
        etage = extract_etage(description)
        if etage is not None:
            extracted['etage'] = etage
        elif annonce.get('etage'):
            extracted['etage'] = clean_number(annonce.get('etage'))
        
        # État (si non fourni)
        if not extracted.get('etat_bien'):
            etat = extract_etat_bien(description)
            if etat:
                extracted['etat_bien'] = etat
        
        # Titre foncier
        titre_foncier = extract_titre_foncier(description)
        if titre_foncier:
            extracted['titre_foncier'] = titre_foncier
        
        # Année construction (si non fournie)
        if not extracted.get('annee_construction'):
            annee = extract_annee_construction(description)
            if annee:
                extracted['annee_construction'] = annee
        
        # Équipements
        extracted['a_ascenseur'] = extract_presence_ascenseur(description)
        extracted['a_piscine'] = extract_presence_piscine(description)
        extracted['a_jardin'] = extract_presence_jardin(description)
        extracted['a_terrasse'] = extract_presence_terrasse(description)
        extracted['a_balcon'] = extract_presence_balcon(description)
        extracted['a_climatisation'] = extract_presence_climatisation(description)
        extracted['a_chauffage'] = extract_presence_chauffage(description)
        extracted['a_securite'] = extract_presence_securite(description)
        
        # Parking
        extracted['a_parking'] = extract_presence_parking(description)
        nb_parking = extract_nombre_parking(description)
        if nb_parking:
            extracted['parking_nombre'] = nb_parking
        parking_type = extract_type_parking(description)
        if parking_type:
            extracted['parking_type'] = parking_type
        
        # Type de chauffage
        chauffage_type = extract_type_chauffage(description)
        if chauffage_type:
            extracted['chauffage_type'] = chauffage_type
        
        # Vue
        vue = extract_vue(description)
        if vue:
            extracted['vue'] = vue
        
        # Distance mer
        distance_mer = extract_distance_mer(description)
        if distance_mer:
            extracted['distance_mer'] = distance_mer
        
        # Proximités
        proximites = extract_proximites(description)
        if proximites:
            extracted['proximites'] = proximites
        
        # Promoteur direct
        extracted['promoteur_direct'] = extract_est_promoteur_direct(description)
        
        # Frais d'enregistrement
        frais = extract_frais_enregistrement(description)
        if frais:
            extracted['frais_enregistrement'] = frais
        
        # Contact
        telephone = extract_telephone(description)
        if telephone:
            extracted['telephone'] = telephone
        
        email = extract_email(description)
        if email:
            extracted['email'] = email
        
        site_web = extract_site_web(description)
        if site_web:
            extracted['site_web'] = site_web
        
        # Caractéristiques spécifiques aux terrains
        if extracted['type_bien'] == 'Terrain':
            terrain_caracs = extract_caracteristiques_terrain(description)
            extracted.update(terrain_caracs)
    
    # ===== 9. OPTIONS =====
    options = annonce.get('options', [])
    if options:
        extracted['options_brutes'] = options
        extracted['options_normalisees'] = normalize_options(options)
    
    # ===== 10. IMAGES =====
    images = extract_images_list(
        annonce.get('images_urls', []),
        annonce.get('nombre_photos')
    )
    extracted['images'] = images
    extracted['nombre_images'] = len(images)
    
    # ===== 11. ANNONCEUR =====
    extracted['annonceur_nom'] = annonce.get('annonceur_nom', '')
    extracted['annonceur_type'] = annonce.get('annonceur_type', '')
    
    telephone_annonceur = annonce.get('annonceur_telephone')
    if telephone_annonceur and telephone_annonceur != '#':
        extracted['annonceur_telephone'] = telephone_annonceur
    
    # ===== 12. DATE DE PUBLICATION =====
    date_pub = annonce.get('date_publication', '')
    if date_pub and 'Annonce' not in date_pub:
        extracted['date_publication'] = clean_date(date_pub)
    else:
        extracted['date_publication'] = None
    
    # ===== 13. MÉTADONNÉES =====
    if annonce.get('nombre_photos'):
        extracted['nombre_photos_annonce'] = annonce.get('nombre_photos')
    
    return extracted


def extraire_tunisiapromo_vente(annonce: Dict) -> Dict:
    """
    Fonction principale d'extraction pour une annonce de vente Tunisia Promo
    """
    return extract_all_from_annonce(annonce)


def load_existing_annonces(filepath: Path) -> Dict[str, Dict]:
    """Charge les annonces existantes depuis un fichier JSON"""
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {str(a.get('annonce_id')): a for a in data if a.get('annonce_id')}
        elif isinstance(data, dict) and 'annonces' in data:
            return {str(a.get('annonce_id')): a for a in data['annonces'] if a.get('annonce_id')}
    except json.JSONDecodeError:
        print(f"⚠️ Fichier {filepath} corrompu")
    
    return {}


def process_tunisiapromo_file_extract(input_path: str, output_path: Optional[str] = None):
    """
    Traite le fichier JSON de Tunisia Promo (extraction uniquement)
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    output_file = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_extrait.json"
    
    existing_dict = load_existing_annonces(output_file)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    if isinstance(new_data, list):
        nouvelles_annonces = new_data
    else:
        nouvelles_annonces = []
    
    stats = {
        'total_original': len(nouvelles_annonces),
        'nouvelles': 0,
        'modifiees': 0,
        'inchangées': 0,
        'ignorees': 0
    }
    
    annonces_traitees = []
    
    for annonce in nouvelles_annonces:
        annonce_id = str(annonce.get('annonce_id', ''))
        statut = annonce.get('statut', 'inchangé')
        
        if not annonce_id:
            stats['ignorees'] += 1
            continue
        
        existing = existing_dict.get(annonce_id)
        
        doit_traiter = (
            statut in ['nouveau', 'modifié'] or
            not existing
        )
        
        if doit_traiter:
            extracted = extraire_tunisiapromo_vente(annonce)
            annonces_traitees.append(extracted)
            
            if statut == 'nouveau':
                stats['nouvelles'] += 1
            elif statut == 'modifié':
                stats['modifiees'] += 1
            else:
                stats['nouvelles'] += 1
        else:
            if existing:
                annonces_traitees.append(existing)
                stats['inchangées'] += 1
            else:
                extracted = extraire_tunisiapromo_vente(annonce)
                annonces_traitees.append(extracted)
                stats['nouvelles'] += 1
    
    annonces_traitees.sort(key=lambda x: x.get('annonce_id', ''))
    
    metadata = {
        'date_extraction': datetime.now().isoformat(),
        'total_annonces': len(annonces_traitees),
        'statistiques': stats,
        'version': '1.0',
        'type': 'vente'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_traitees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES D'EXTRACTION - TUNISIA PROMO VENTE")
    print("="*60)
    print(f"📥 Annonces lues: {stats['total_original']}")
    print(f"🆕 Nouvelles annonces extraites: {stats['nouvelles']}")
    print(f"✏️ Annonces modifiées extraites: {stats['modifiees']}")
    print(f"⏸️ Annonces inchangées conservées: {stats['inchangées']}")
    print(f"⚠️ Annonces ignorées: {stats['ignorees']}")
    print(f"📊 Total après extraction: {len(annonces_traitees)}")
    print("="*60)
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    return len(annonces_traitees)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Tunisia Promo Vente")
    parser.add_argument('--file', '-f', default='tunisiapromo_vente.json', help='Fichier JSON des annonces')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_extrait.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_extract(args.file, args.output)


if __name__ == '__main__':
    main()