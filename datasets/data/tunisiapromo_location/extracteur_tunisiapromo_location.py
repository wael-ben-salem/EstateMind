"""
Agent d'extraction pour Tunisia Promo - Location
Extrait TOUS les champs possibles des annonces de location
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
    'appartement', 'villa', 'maison', 'bureau', 'studio', 'local commercial'
]

TYPES_LOCATION = {
    'annuelle': 'Annuelle',
    'annuel': 'Annuelle',
    'long terme': 'Long terme',
    'courte durée': 'Courte durée',
    'temporaire': 'Temporaire',
    'saisonnier': 'Saisonnier',
    'vacances': 'Vacances'
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
    'vue sur lac': 'Vue sur lac',
    'au bord de mer': 'Au bord de mer',
    'gardien': 'Gardien',
    'alarme': 'Alarme'
}

EQUIPEMENTS_MAPPING = {
    'four': 'Four',
    'lave-linge': 'Lave-linge',
    'micro-onde': 'Micro-ondes',
    'micro-ondes': 'Micro-ondes',
    'récepteur satellite': 'Parabole/TV',
    'réfrigérateur': 'Réfrigérateur',
    'tv': 'TV',
    'tv plasma': 'TV Plasma',
    'tv lcd': 'TV LCD',
    'télévision': 'TV'
}

VILLES_TUNISIE = [
    'tunis', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'le kram', 'salammbô', 'ariana', 'ennasr', 'manzah', 'soukra',
    'raoued', 'ain zaghouan', 'aouina', 'bhar lazreg', 'jardins de carthage',
    'ben arous', 'boumhel', 'mohammedia', 'nabeul', 'hammamet',
    'sousse', 'hammam sousse', 'monastir', 'mahdia', 'sfax', 'bizerte',
    'berge du lac', 'lac', 'mahdia hiboun', 'mahdia ville'
]

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte', 'medenine': 'Médenine', 'djerba': 'Médenine'
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
    
    # Essayer de trouver une date dans le format YYYY-MM-DD
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, date_str)
    if match:
        return match.group(1)
    
    return None


# ========== EXTRACTION DU PRIX ==========

def extract_prix_from_text(description: str) -> Optional[float]:
    """Extrait le prix depuis la description (si différent)"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'prix\s*[:\-]?\s*(\d[\d\s]*(?:\.?\d*)?)\s*(?:dt|tnd)',
        r'(\d[\d\s]*(?:\.?\d*)?)\s*dt\s*/mois',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                prix_str = m.group(1).replace(' ', '').replace(',', '.')
                return float(prix_str)
            except:
                pass
    
    return None


# ========== EXTRACTION DES CHARGES ==========

def extract_charges(description: str) -> Dict[str, Any]:
    """Extrait les informations sur les charges"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    charges = {}
    
    # Frais de syndic
    syndic_patterns = [
        r'syndic\s*[:\-]?\s*(\d+)\s*dt\s*/\s*an',
        r'frais\s+du\s+syndic\s*[:\-]?\s*(\d+)\s*dt',
    ]
    
    for pattern in syndic_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            charges['syndic_annuel'] = float(m.group(1))
            break
    
    # Charges incluses
    if 'charges comprises' in desc_lower or 'rien à payer' in desc_lower:
        charges['charges_incluses'] = True
        details = []
        if 'électricité' in desc_lower or 'electricite' in desc_lower:
            details.append('Électricité')
        if 'eau' in desc_lower:
            details.append('Eau')
        if 'gaz' in desc_lower:
            details.append('Gaz')
        if details:
            charges['charges_details'] = details
    
    return charges


# ========== EXTRACTION DU TYPE DE LOCATION ==========

def extract_type_location(type_location: str, description: str) -> str:
    """Détermine le type de location"""
    if type_location and type_location != "Non spécifié":
        type_lower = type_location.lower()
        for key, value in TYPES_LOCATION.items():
            if key in type_lower:
                return value
        return type_location
    
    if description:
        desc_lower = description.lower()
        if 'à l\'année' in desc_lower or 'annuelle' in desc_lower:
            return 'Annuelle'
        elif 'temporaire' in desc_lower or 'jusqu' in desc_lower:
            return 'Temporaire'
        elif 'vacances' in desc_lower or 'saison' in desc_lower:
            return 'Saisonnier'
    
    return 'Non spécifié'


# ========== EXTRACTION DEPUIS LA DESCRIPTION ==========

def extract_etage(description: str) -> Optional[int]:
    """Extrait le numéro d'étage depuis la description"""
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


def extract_est_dernier_etage(description: str) -> bool:
    """Détecte si c'est un dernier étage"""
    if not description:
        return False
    
    desc_lower = description.lower()
    return 'dernier étage' in desc_lower or 'dernier etage' in desc_lower


def extract_vue(description: str) -> Optional[str]:
    """Extrait le type de vue"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'vue sur mer' in desc_lower:
        return 'Mer'
    elif 'vue mer' in desc_lower:
        return 'Mer'
    elif 'vue sur lac' in desc_lower:
        return 'Lac'
    elif 'vue dégagée' in desc_lower:
        return 'Dégagée'
    elif 'vue sur piscine' in desc_lower:
        return 'Piscine'
    elif 'vue sur jardin' in desc_lower:
        return 'Jardin'
    
    return None


def extract_presence_piscine(description: str) -> bool:
    """Détecte la présence d'une piscine"""
    return 'piscine' in description.lower()


def extract_presence_jardin(description: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in description.lower()


def extract_presence_ascenseur(description: str) -> bool:
    """Détecte la présence d'un ascenseur"""
    return 'ascenseur' in description.lower()


def extract_presence_gardien(description: str) -> bool:
    """Détecte la présence d'un gardien"""
    desc_lower = description.lower()
    return 'gardien' in desc_lower or 'gardiennage' in desc_lower


def extract_presence_parking(description: str) -> bool:
    """Détecte la présence de parking"""
    return 'parking' in description.lower() or 'place parking' in description.lower()


def extract_nombre_parking(description: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'(\d+)\s*place[s]?\s*(?:de)?\s*parking',
        r'parking\s*(\d+)\s*places?',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
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
    
    if 'sous-sol' in desc_lower:
        return 'Sous-sol'
    elif 'couvert' in desc_lower:
        return 'Couvert'
    elif 'abrité' in desc_lower or 'abri' in desc_lower:
        return 'Abrité'
    
    return None


def extract_presence_terrasse(description: str) -> bool:
    """Détecte la présence d'une terrasse"""
    return 'terrasse' in description.lower()


def extract_surface_terrasse(description: str) -> Optional[float]:
    """Extrait la surface de la terrasse"""
    if not description:
        return None
    
    patterns = [
        r'terrasse\s+de\s*(\d+)\s*m[²2]',
        r'terrasse\s+(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_presence_balcon(description: str) -> bool:
    """Détecte la présence d'un balcon"""
    return 'balcon' in description.lower()


def extract_presence_climatisation(description: str) -> bool:
    """Détecte la présence de climatisation"""
    return 'climatisation' in description.lower()


def extract_type_climatisation(description: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'climatisation centrale' in desc_lower:
        return 'Centrale'
    elif 'climatiseurs' in desc_lower:
        return 'Split'
    
    return None


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
    elif 'chauffage individuel' in desc_lower:
        return 'Individuel'
    
    return None


def extract_presence_meuble(description: str) -> bool:
    """Détecte si le bien est meublé"""
    return 'meublé' in description.lower() or 'meuble' in description.lower()


def extract_presence_cuisine_equipee(description: str) -> bool:
    """Détecte si la cuisine est équipée"""
    desc_lower = description.lower()
    return 'cuisine équipée' in desc_lower or 'cuisine equipee' in desc_lower


def extract_proximites(description: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    if not description:
        return []
    
    desc_lower = description.lower()
    proximites = []
    
    keywords = {
        'plage': 'Plage',
        'mer': 'Mer',
        'commerces': 'Commerces',
        'supermarché': 'Supermarché',
        'monoprix': 'Monoprix',
        'école': 'École',
        'lycée': 'Lycée',
        'transport': 'Transports',
        'bus': 'Bus',
        'métro': 'Métro'
    }
    
    for keyword, label in keywords.items():
        if keyword in desc_lower:
            if label not in proximites:
                proximites.append(label)
    
    return sorted(proximites)


def extract_disponibilite(description: str) -> Optional[str]:
    """Extrait la disponibilité"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'disponible immédiatement' in desc_lower:
        return 'Immédiate'
    elif 'libre de suite' in desc_lower:
        return 'Immédiate'
    
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


# ========== EXTRACTION DEPUIS LES OPTIONS ET ÉQUIPEMENTS ==========

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


def normalize_equipements(equipements: List[str]) -> List[str]:
    """Normalise la liste des équipements"""
    if not equipements:
        return []
    
    normalized = []
    
    for equip in equipements:
        if not isinstance(equip, str):
            continue
        
        equip_lower = equip.lower().strip()
        
        for key, value in EQUIPEMENTS_MAPPING.items():
            if key in equip_lower:
                if value not in normalized:
                    normalized.append(value)
                break
        else:
            normalized.append(equip.strip().title())
    
    return sorted(normalized)


# ========== EXTRACTION DEPUIS L'URL ==========

def extract_reference_from_url(url: str) -> Optional[str]:
    """Extrait la référence depuis l'URL"""
    if not url:
        return None
    
    # Format: ...-z156090.html
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
    Extrait TOUS les champs possibles d'une annonce de location Tunisia Promo
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
    extracted['type_offre'] = annonce.get('type_offre', 'Location')
    
    # ===== 2. PRIX =====
    prix = clean_number(annonce.get('prix'))
    extracted['prix'] = prix if prix and prix > 0 else 0
    if prix and prix > 0:
        extracted['prix_text'] = f"{int(prix):,} TND/mois".replace(',', ' ')
    else:
        extracted['prix_text'] = "Prix à consulter"
    
    # ===== 3. LOCALISATION =====
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
    
    # ===== 4. TYPE DE BIEN =====
    extracted['type_bien'] = annonce.get('type_bien', '')
    
    # ===== 5. TYPE DE LOCATION =====
    type_location = annonce.get('type_location', '')
    description = annonce.get('description', '')
    extracted['type_location'] = extract_type_location(type_location, description)
    
    # ===== 6. DESCRIPTION =====
    description = annonce.get('description', '')
    extracted['description'] = normalize_text(description)
    
    # ===== 7. CARACTÉRISTIQUES DU BIEN =====
    extracted['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
    extracted['pieces'] = clean_number(annonce.get('pieces'))
    extracted['etage'] = clean_number(annonce.get('etage'))
    extracted['places_voiture'] = clean_number(annonce.get('places_voiture'))
    
    # ===== 8. EXTRACTIONS DEPUIS LA DESCRIPTION =====
    if description:
        # Étage (si non fourni)
        if not extracted.get('etage'):
            etage_desc = extract_etage(description)
            if etage_desc is not None:
                extracted['etage_desc'] = etage_desc
        
        extracted['dernier_etage'] = extract_est_dernier_etage(description)
        
        # Vue
        vue = extract_vue(description)
        if vue:
            extracted['vue'] = vue
        
        # Équipements
        extracted['a_piscine'] = extract_presence_piscine(description)
        extracted['a_jardin'] = extract_presence_jardin(description)
        extracted['a_ascenseur'] = extract_presence_ascenseur(description)
        extracted['a_gardien'] = extract_presence_gardien(description)
        extracted['a_terrasse'] = extract_presence_terrasse(description)
        extracted['a_balcon'] = extract_presence_balcon(description)
        extracted['a_climatisation'] = extract_presence_climatisation(description)
        extracted['a_chauffage'] = extract_presence_chauffage(description)
        extracted['a_meuble'] = extract_presence_meuble(description)
        extracted['a_cuisine_equipee'] = extract_presence_cuisine_equipee(description)
        
        # Type de climatisation
        clim_type = extract_type_climatisation(description)
        if clim_type:
            extracted['climatisation_type'] = clim_type
        
        # Type de chauffage
        chauffage_type = extract_type_chauffage(description)
        if chauffage_type:
            extracted['chauffage_type'] = chauffage_type
        
        # Parking
        extracted['a_parking'] = extract_presence_parking(description)
        nb_parking = extract_nombre_parking(description)
        if nb_parking:
            extracted['parking_nombre'] = nb_parking
        parking_type = extract_type_parking(description)
        if parking_type:
            extracted['parking_type'] = parking_type
        
        # Surface terrasse
        surface_terrasse = extract_surface_terrasse(description)
        if surface_terrasse:
            extracted['surface_terrasse'] = surface_terrasse
        
        # Proximités
        proximites = extract_proximites(description)
        if proximites:
            extracted['proximites'] = proximites
        
        # Disponibilité
        dispo = extract_disponibilite(description)
        if dispo:
            extracted['disponibilite'] = dispo
        
        # Charges
        charges = extract_charges(description)
        if charges:
            extracted['charges'] = charges
        
        # Téléphone
        telephone = extract_telephone(description)
        if telephone:
            extracted['telephone'] = telephone
        
        # Email
        email = extract_email(description)
        if email:
            extracted['email'] = email
        
        # Site web
        site_web = extract_site_web(description)
        if site_web:
            extracted['site_web'] = site_web
    
    # ===== 9. OPTIONS ET ÉQUIPEMENTS =====
    options = annonce.get('options', [])
    if options:
        extracted['options_brutes'] = options
        extracted['options_normalisees'] = normalize_options(options)
    
    equipements = annonce.get('equipements', [])
    if equipements:
        extracted['equipements_bruts'] = equipements
        extracted['equipements_normalises'] = normalize_equipements(equipements)
    
    # Fusionner options et équipements
    all_equip = []
    if extracted.get('options_normalisees'):
        all_equip.extend(extracted['options_normalisees'])
    if extracted.get('equipements_normalises'):
        all_equip.extend(extracted['equipements_normalises'])
    if all_equip:
        extracted['tous_equipements'] = sorted(list(set(all_equip)))
    
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


def extraire_tunisiapromo_location(annonce: Dict) -> Dict:
    """
    Fonction principale d'extraction pour une annonce de location Tunisia Promo
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
            extracted = extraire_tunisiapromo_location(annonce)
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
                extracted = extraire_tunisiapromo_location(annonce)
                annonces_traitees.append(extracted)
                stats['nouvelles'] += 1
    
    annonces_traitees.sort(key=lambda x: x.get('annonce_id', ''))
    
    metadata = {
        'date_extraction': datetime.now().isoformat(),
        'total_annonces': len(annonces_traitees),
        'statistiques': stats,
        'version': '1.0',
        'type': 'location'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_traitees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES D'EXTRACTION - TUNISIA PROMO LOCATION")
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
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Tunisia Promo Location")
    parser.add_argument('--file', '-f', default='tunisiapromo_location.json', help='Fichier JSON des annonces')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_extrait.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_extract(args.file, args.output)


if __name__ == '__main__':
    main()