"""
Agent d'extraction pour Tunisia Promo - Location Vacances
Extrait TOUS les champs possibles des annonces de location vacances
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
    'appartement', 'villa', 'maison', 'duplex', 'studio'
]

PERIODES = {
    'été': 'Été',
    'hiver': 'Hiver',
    'printemps': 'Printemps',
    'automne': 'Automne',
    'saison': 'Saison',
    'vacances': 'Vacances',
    'juin': 'Juin',
    'juillet': 'Juillet',
    'août': 'Août',
    'septembre': 'Septembre'
}

UNITES_PRIX = {
    'semaine': 'Semaine',
    'jour': 'Jour',
    'nuit': 'Nuit',
    'mois': 'Mois'
}

OPTIONS_MAPPING = {
    'piscine': 'Piscine',
    'vue sur mer': 'Vue sur mer',
    'vue mer': 'Vue sur mer',
    'climatisation': 'Climatisation',
    'chauffage': 'Chauffage',
    'cuisine équipée': 'Cuisine équipée',
    'meublé': 'Meublé',
    'terrasse': 'Terrasse',
    'balcon': 'Balcon',
    'jardin': 'Jardin',
    'parking': 'Parking',
    'garage': 'Garage',
    'ascenseur': 'Ascenseur',
    'gardien': 'Gardien',
    'interphone': 'Interphone',
    'haut standing': 'Haut standing',
    'au bord de mer': 'Au bord de mer',
    'bord de mer': 'Au bord de mer',
    'pieds dans l\'eau': 'Pieds dans l\'eau',
    'connexion internet': 'Internet',
    'internet': 'Internet',
    'wifi': 'Wifi'
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
    'télévision': 'TV',
    'lave-vaisselle': 'Lave-vaisselle'
}

VILLES_TUNISIE = [
    'hammamet', 'nabeul', 'sousse', 'monastir', 'mahdia', 'sfax',
    'djerba', 'tunis', 'la marsa', 'carthage', 'gammarth',
    'yasmine hammamet', 'hammamet nord', 'hammamet sud', 'port el kantaoui'
]

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul',
    'sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'djerba': 'Médenine'
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

def extract_prix_details(description: str, prix_original: float) -> Dict[str, Any]:
    """
    Extrait les détails du prix (montant et unité)
    """
    result = {
        'prix': prix_original,
        'prix_unite': 'Non spécifié',
        'prix_semaine': None,
        'prix_jour': None
    }
    
    if not description:
        return result
    
    desc_lower = description.lower()
    
    # Chercher le prix dans la description
    prix_patterns = [
        (r'(\d+[.,]?\d*)\s*dt\s*/\s*semaine', 'Semaine'),
        (r'(\d+[.,]?\d*)\s*dt\s*/ semaine', 'Semaine'),
        (r'(\d+[.,]?\d*)\s*dt\s*/\s*jour', 'Jour'),
        (r'(\d+[.,]?\d*)\s*dt\s*/ jour', 'Jour'),
        (r'(\d+[.,]?\d*)\s*dt\s*/\s*nuit', 'Nuit'),
        (r'(\d+[.,]?\d*)\s*dt\s*/ mois', 'Mois')
    ]
    
    for pattern, unite in prix_patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                montant = float(m.group(1).replace(',', '.'))
                result['prix'] = montant
                result['prix_unite'] = unite
                if unite == 'Semaine':
                    result['prix_semaine'] = montant
                    result['prix_jour'] = round(montant / 7, 2)
                elif unite == 'Jour':
                    result['prix_jour'] = montant
                    result['prix_semaine'] = montant * 7
                break
            except:
                pass
    
    return result


# ========== EXTRACTION DE LA DISTANCE À LA MER ==========

def extract_distance_mer(description: str) -> Dict[str, Any]:
    """Extrait la distance à la mer"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    result = {}
    
    # Types de proximité
    if 'pieds dans l\'eau' in desc_lower or 'pieds dans leau' in desc_lower:
        result['proximite_mer'] = 'Pieds dans l\'eau'
        result['distance_mer_m'] = 0
    elif 'bord de mer' in desc_lower or 'au bord de mer' in desc_lower:
        result['proximite_mer'] = 'Bord de mer'
        result['distance_mer_m'] = 50
    elif 'front de mer' in desc_lower:
        result['proximite_mer'] = 'Front de mer'
        result['distance_mer_m'] = 0
    else:
        # Distance en mètres
        distance_patterns = [
            r'à\s*(\d+)\s*m[èe]tres?\s*de\s*la\s*plage',
            r'à\s*(\d+)\s*m\s*de\s*la\s*plage',
            r'(\d+)\s*m[èe]tres?\s*de\s*la\s*plage',
            r'proche\s*de\s*la\s*plage',
            r'près\s*de\s*la\s*plage'
        ]
        
        for pattern in distance_patterns:
            m = re.search(pattern, desc_lower)
            if m:
                if 'proche' in pattern or 'près' in pattern:
                    result['proximite_mer'] = 'Proche'
                else:
                    try:
                        distance = int(m.group(1))
                        result['distance_mer_m'] = distance
                        if distance <= 100:
                            result['proximite_mer'] = 'Très proche'
                        elif distance <= 500:
                            result['proximite_mer'] = 'Proche'
                        else:
                            result['proximite_mer'] = 'Accessible'
                    except:
                        result['proximite_mer'] = 'Proche'
                break
    
    return result


# ========== EXTRACTION DE LA PÉRIODE DISPONIBLE ==========

def extract_periode(description: str, periode_original: str) -> str:
    """Extrait la période de disponibilité"""
    if periode_original and periode_original != "Non spécifié":
        return periode_original
    
    if not description:
        return "Non spécifié"
    
    desc_lower = description.lower()
    
    for key, value in PERIODES.items():
        if key in desc_lower:
            return value
    
    return "Non spécifié"


# ========== EXTRACTION DE LA CAPACITÉ ==========

def extract_capacite(description: str) -> Optional[int]:
    """Extrait la capacité (nombre de personnes)"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'(\d+)\s*personnes?',
        r'(\d+)\s*couchages?',
        r'(\d+)\s*lits?',
        r'pour\s*(\d+)\s*personnes?'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


# ========== EXTRACTION DES CHAMBRES ==========

def extract_nombre_chambres(description: str) -> Optional[int]:
    """Extrait le nombre de chambres"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'(\d+)\s*chambres?',
        r'(\d+)\s*pi[èe]ces?',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


# ========== EXTRACTION DES SALLES DE BAIN ==========

def extract_nombre_sdb(description: str) -> Optional[int]:
    """Extrait le nombre de salles de bain"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'(\d+)\s*sdb',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


# ========== EXTRACTION DEPUIS LA DESCRIPTION ==========

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
    return 'climatisation' in description.lower()


def extract_presence_chauffage(description: str) -> bool:
    """Détecte la présence de chauffage"""
    return 'chauffage' in description.lower()


def extract_presence_meuble(description: str) -> bool:
    """Détecte si le bien est meublé"""
    return 'meublé' in description.lower()


def extract_presence_cuisine_equipee(description: str) -> bool:
    """Détecte si la cuisine est équipée"""
    desc_lower = description.lower()
    return 'cuisine équipée' in desc_lower or 'cuisine equipee' in desc_lower


def extract_presence_parking(description: str) -> bool:
    """Détecte la présence de parking"""
    return 'parking' in description.lower() or 'place parking' in description.lower()


def extract_presence_gardien(description: str) -> bool:
    """Détecte la présence d'un gardien"""
    desc_lower = description.lower()
    return 'gardien' in desc_lower or 'sécurisée' in desc_lower or 'securisee' in desc_lower


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
        'restaurants': 'Restaurants',
        'cafés': 'Cafés',
        'loisirs': 'Loisirs',
        'médina': 'Médina',
        'carthage land': 'Carthage Land',
        'port': 'Port',
        'marina': 'Marina'
    }
    
    for keyword, label in keywords.items():
        if keyword in desc_lower:
            if label not in proximites:
                proximites.append(label)
    
    return sorted(proximites)


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
    
    # Format: ...-z142304.html
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
    Extrait TOUS les champs possibles d'une annonce de location vacances Tunisia Promo
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
    extracted['type_offre'] = annonce.get('type_offre', 'Location vacances')
    
    # ===== 2. TYPE DE BIEN =====
    extracted['type_bien'] = annonce.get('type_bien', '')
    
    # ===== 3. PRIX =====
    prix_original = clean_number(annonce.get('prix'))
    description = annonce.get('description', '')
    prix_details = extract_prix_details(description, prix_original or 0)
    extracted.update(prix_details)
    
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
    
    # ===== 5. DESCRIPTION =====
    description = annonce.get('description', '')
    extracted['description'] = normalize_text(description)
    
    # ===== 6. EXTRACTIONS SPÉCIFIQUES VACANCES =====
    if description:
        # Distance à la mer
        distance_info = extract_distance_mer(description)
        if distance_info:
            extracted.update(distance_info)
        
        # Période disponible
        periode_originale = annonce.get('periode_disponible', '')
        extracted['periode_disponible'] = extract_periode(description, periode_originale)
        
        # Capacité
        capacite = extract_capacite(description)
        if capacite:
            extracted['capacite'] = capacite
        
        # Nombre de chambres (si non fourni)
        if not annonce.get('pieces'):
            chambres = extract_nombre_chambres(description)
            if chambres:
                extracted['chambres'] = chambres
        
        # Nombre de salles de bain
        sdb = extract_nombre_sdb(description)
        if sdb:
            extracted['salles_bain'] = sdb
        
        # Étage
        etage = extract_etage(description)
        if etage is not None:
            extracted['etage'] = etage
        
        # Vue
        vue = extract_vue(description)
        if vue:
            extracted['vue'] = vue
        
        # Équipements
        extracted['a_piscine'] = extract_presence_piscine(description)
        extracted['a_jardin'] = extract_presence_jardin(description)
        extracted['a_terrasse'] = extract_presence_terrasse(description)
        extracted['a_balcon'] = extract_presence_balcon(description)
        extracted['a_climatisation'] = extract_presence_climatisation(description)
        extracted['a_chauffage'] = extract_presence_chauffage(description)
        extracted['a_meuble'] = extract_presence_meuble(description)
        extracted['a_cuisine_equipee'] = extract_presence_cuisine_equipee(description)
        extracted['a_parking'] = extract_presence_parking(description)
        extracted['a_gardien'] = extract_presence_gardien(description)
        
        # Proximités
        proximites = extract_proximites(description)
        if proximites:
            extracted['proximites'] = proximites
        
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
    
    # ===== 7. CARACTÉRISTIQUES DU BIEN =====
    extracted['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
    extracted['pieces'] = clean_number(annonce.get('pieces'))
    extracted['places_voiture'] = clean_number(annonce.get('places_voiture'))
    extracted['annee_construction'] = clean_number(annonce.get('annee_construction'))
    
    # ===== 8. OPTIONS ET ÉQUIPEMENTS =====
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
    
    # ===== 9. IMAGES =====
    images = extract_images_list(
        annonce.get('images_urls', []),
        annonce.get('nombre_photos')
    )
    extracted['images'] = images
    extracted['nombre_images'] = len(images)
    
    # ===== 10. ANNONCEUR =====
    extracted['annonceur_type'] = annonce.get('annonceur_type', '')
    
    telephone_annonceur = annonce.get('annonceur_telephone')
    if telephone_annonceur and telephone_annonceur != '#':
        extracted['annonceur_telephone'] = telephone_annonceur
    
    # ===== 11. PROXIMITÉ MER (champ original) =====
    if annonce.get('proximite_mer'):
        extracted['proximite_mer_original'] = annonce.get('proximite_mer')
    
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


def extraire_tunisiapromo_vacances(annonce: Dict) -> Dict:
    """
    Fonction principale d'extraction pour une annonce de location vacances Tunisia Promo
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
            extracted = extraire_tunisiapromo_vacances(annonce)
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
                extracted = extraire_tunisiapromo_vacances(annonce)
                annonces_traitees.append(extracted)
                stats['nouvelles'] += 1
    
    annonces_traitees.sort(key=lambda x: x.get('annonce_id', ''))
    
    metadata = {
        'date_extraction': datetime.now().isoformat(),
        'total_annonces': len(annonces_traitees),
        'statistiques': stats,
        'version': '1.0',
        'type': 'vacances'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_traitees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES D'EXTRACTION - TUNISIA PROMO VACANCES")
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
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Tunisia Promo Vacances")
    parser.add_argument('--file', '-f', default='tunisiapromo_vacances.json', help='Fichier JSON des annonces')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_extrait.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_extract(args.file, args.output)


if __name__ == '__main__':
    main()