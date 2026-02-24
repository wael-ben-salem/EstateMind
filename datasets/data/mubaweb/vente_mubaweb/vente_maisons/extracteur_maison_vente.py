"""
Agent d'extraction pour Vente de Maisons
Extrait TOUS les champs spécifiques aux maisons/villas
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES AUX MAISONS ==========

TYPES_MAISONS = [
    'villa', 'duplex', 'triplex', 'maison', 'maison individuelle',
    'maison de ville', 'maison de standing', 'villa jumelée',
    'villa indépendante', 'chalet', 'riad', 'dar'
]

EQUIPEMENTS_MAISON = [
    'jardin', 'piscine', 'terrasse', 'balcon', 'garage', 'parking',
    'cave', 'cellier', 'buanderie', 'séchoir', 'débarras',
    'cheminée', 'véranda', 'pergola', 'climatisation', 'climatisation centrale',
    'chauffage central', 'chauffage au sol', 'double vitrage',
    'porte blindée', 'alarme', 'caméras', 'sécurité', 'interphone',
    'visiophone', 'portail électrique', 'portail automatique',
    'cuisine équipée', 'cuisine américaine', 'placards', 'dressing',
    'salle de bain', 'salle d\'eau', 'wc séparés', 'toilettes',
    'buanderie', 'lingerie', 'atelier', 'bureau', 'bibliothèque',
    'salon', 'salle à manger', 'séjour', 'hall', 'entrée',
    'vue sur mer', 'vue dégagée', 'vue panoramique', 'vue sur jardin',
    'proche commodités', 'quartier calme', 'résidentiel', 'sécurisé'
]

ZONES_MAISONS = [
    'quartier calme', 'quartier résidentiel', 'proche plage',
    'proche commerces', 'proche écoles', 'vue mer', 'vue montagne'
]

VILLES_TUNISIE = [
    'tunis', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'le kram', 'salammbô', 'ariana', 'ennasr', 'manzah', 'soukra',
    'raoued', 'ain zaghouan', 'aouina', 'bhar lazreg', 'jardins de carthage',
    'ben arous', 'boumhel', 'mohammedia', 'nabeul', 'hammamet',
    'sousse', 'hammam sousse', 'monastir', 'mahdia', 'sfax', 'bizerte'
]

REGIONS_MAPPING = {
    "tunis": "Tunis", "la marsa": "Tunis", "carthage": "Tunis", "le kram": "Tunis",
    "ariana": "Ariana", "ennasr": "Ariana", "manzah": "Ariana", "soukra": "Ariana", "raoued": "Ariana",
    "ben arous": "Ben Arous", "boumhel": "Ben Arous", "mohammedia": "Ben Arous",
    "nabeul": "Nabeul", "hammamet": "Nabeul",
    "sousse": "Sousse", "hammam sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte"
}

ETAT_MAISON_MAPPING = {
    "jamais habité": "Jamais habité",
    "jamais habité / rénové": "Jamais habité / Rénové",
    "neuf": "Neuf",
    "à rénover": "À rénover",
    "bon état": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état"
}


# ========== FONCTIONS UTILITAIRES ==========

def normalize_text(text: str) -> str:
    """Normalise le texte"""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
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


def extract_date_from_url(url: str) -> Optional[str]:
    """Extrait une date depuis une URL d'image"""
    if not url:
        return None
    
    try:
        decoded = unquote(url)
    except:
        decoded = url
    
    # Pattern WhatsApp Image
    whatsapp_pattern = r'WhatsApp%20Image%20(\d{4}-\d{2}-\d{2})|WhatsApp\s+Image\s+(\d{4}-\d{2}-\d{2})'
    m = re.search(whatsapp_pattern, url)
    if m:
        date_str = m.group(1) or m.group(2)
        if date_str:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except:
                pass
    
    # Pattern date simple
    date_pattern = r'/(\d{4}-\d{2}-\d{2})/|(\d{4}-\d{2}-\d{2})'
    m = re.search(date_pattern, decoded)
    if m:
        date_str = m.group(1) or m.group(2)
        if date_str:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except:
                pass
    
    return None


# ========== EXTRACTION DEPUIS LES TEXTES DESCRIPTIFS ==========

def extract_titre_ameliore(description_courte: str, description_complete: str) -> Optional[str]:
    """Extrait un titre amélioré"""
    text = f"{description_courte} {description_complete}"
    lines = text.split('.')
    if lines and len(lines[0]) < 150:
        return normalize_text(lines[0])
    return None


def extract_prix_from_text(text: str) -> Dict[str, Any]:
    """Extraction du prix"""
    result = {}
    text_lower = text.lower()
    
    if any(phrase in text_lower for phrase in ['prix à consulter', 'prix sur demande', 'nous consulter']):
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        return result
    
    prix_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 1),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)', 1),
        (r'(\d+)\s*tnd', 1),
        (r'(\d+)\s*dt\b', 1),
    ]
    
    for pattern, group in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                if 50000 <= val <= 10000000:
                    result['prix'] = val
                    break
            except:
                continue
    
    return result


def extract_surface_habitable_from_text(text: str) -> Optional[float]:
    """Extrait la surface habitable"""
    patterns = [
        r'surface\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m[²2]',
        r'(\d+)\s*m[²2]\s*(?:habitable)?',
        r'superficie\s*[:\-]?\s*(\d+)\s*m²',
        r'bâti\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 30 <= val <= 2000:
                    return val
            except:
                pass
    
    return None


def extract_surface_terrain_from_text(text: str) -> Optional[float]:
    """Extrait la surface du terrain"""
    patterns = [
        r'terrain\s+de\s*(\d+)\s*m[²2]',
        r'terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+du\s+terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'parcelle\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+de la parcelle\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_nombre_niveaux(text: str) -> Optional[int]:
    """Extrait le nombre de niveaux"""
    patterns = [
        r'sur\s+(\d+)\s*niveaux',
        r'(\d+)\s*niveaux',
        r'r\s*\+\s*(\d+)',
        r'rez-de-chaussée\s*et\s*(\d+)\s*étages?',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_type_maison_from_text(text: str) -> Optional[str]:
    """Extrait le type de maison"""
    text_lower = text.lower()
    
    for type_maison in TYPES_MAISONS:
        if type_maison in text_lower:
            return type_maison.title()
    
    return None


def extract_presence_jardin(text: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in text.lower()


def extract_surface_jardin(text: str) -> Optional[float]:
    """Extrait la surface du jardin"""
    patterns = [
        r'jardin\s+de\s*(\d+)\s*m[²2]',
        r'jardin\s+(\d+)\s*m²',
        r'jardin\s+(\d+)\s*m',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_presence_piscine(text: str) -> bool:
    """Détecte la présence d'une piscine"""
    return 'piscine' in text.lower()


def extract_surface_piscine(text: str) -> Optional[float]:
    """Extrait la surface/dimensions de la piscine"""
    patterns = [
        r'piscine\s+de\s*(\d+)\s*m[²2]',
        r'piscine\s+(\d+)\s*m²',
        r'piscine\s+(\d+)[x\*]\s*(\d+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                if m.lastindex == 2:
                    # Dimensions longueur x largeur
                    return float(m.group(1)) * float(m.group(2))
                else:
                    return float(m.group(1))
            except:
                pass
    
    return None


def extract_presence_terrasse(text: str) -> bool:
    """Détecte la présence d'une terrasse"""
    return 'terrasse' in text.lower()


def extract_surface_terrasse(text: str) -> Optional[float]:
    """Extrait la surface de la terrasse"""
    patterns = [
        r'terrasse\s+de\s*(\d+)\s*m[²2]',
        r'terrasse\s+(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_presence_garage(text: str) -> bool:
    """Détecte la présence d'un garage"""
    return 'garage' in text.lower()


def extract_nombre_garage(text: str) -> Optional[int]:
    """Extrait le nombre de places de garage"""
    patterns = [
        r'(\d+)\s*garage[s]?',
        r'garage\s+(\d+)\s*places?',
        r'(\d+)\s*places?\s*de\s*garage',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return 1 if 'garage' in text_lower else None


def extract_presence_cave(text: str) -> bool:
    """Détecte la présence d'une cave/cellier"""
    text_lower = text.lower()
    keywords = ['cave', 'cellier', 'débarras']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_cheminée(text: str) -> bool:
    """Détecte la présence d'une cheminée"""
    return 'cheminée' in text.lower() or 'cheminee' in text.lower()


def extract_annee_construction(text: str) -> Optional[int]:
    """Extrait l'année de construction"""
    patterns = [
        r'construit[e]?\s+en\s+(\d{4})',
        r'construction\s+(\d{4})',
        r'(\d{4})\s*construction',
        r'construite\s+en\s+(\d{4})',
        r'construite\s+(\d{4})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_etat_maison(text: str) -> Optional[str]:
    """Extrait l'état de la maison"""
    text_lower = text.lower()
    
    if 'jamais habité' in text_lower:
        return "Jamais habité"
    elif 'à rénover' in text_lower:
        return "À rénover"
    elif 'neuf' in text_lower:
        return "Neuf"
    elif 'bon état' in text_lower:
        return "Bon état"
    elif 'très bon état' in text_lower:
        return "Très bon état"
    elif 'excellent état' in text_lower:
        return "Excellent état"
    
    return None


def extract_orientation(text: str) -> Optional[str]:
    """Extrait l'orientation principale"""
    text_lower = text.lower()
    
    orientations = ['nord', 'sud', 'est', 'ouest', 'nord-est', 'nord-ouest', 'sud-est', 'sud-ouest']
    
    for orientation in orientations:
        if orientation in text_lower:
            return orientation.title()
    
    return None


def extract_vue(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower:
        return "Mer"
    elif 'vue mer' in text_lower:
        return "Mer"
    elif 'vue sur lac' in text_lower:
        return "Lac"
    elif 'vue dégagée' in text_lower:
        return "Dégagée"
    elif 'vue panoramique' in text_lower:
        return "Panoramique"
    elif 'vue sur jardin' in text_lower:
        return "Jardin"
    elif 'vue sur montagne' in text_lower:
        return "Montagne"
    
    return None


def extract_chauffage_type(text: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    text_lower = text.lower()
    
    if 'chauffage central' in text_lower:
        return "Central"
    elif 'chauffage au sol' in text_lower:
        return "Au sol"
    elif 'chauffage électrique' in text_lower:
        return "Électrique"
    
    return None


def extract_climatisation_type(text: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    text_lower = text.lower()
    
    if 'climatisation centrale' in text_lower:
        return "Centrale"
    elif 'climatisation split' in text_lower:
        return "Split"
    
    return None


def extract_presence_alarme(text: str) -> bool:
    """Détecte la présence d'une alarme/sécurité"""
    text_lower = text.lower()
    keywords = ['alarme', 'sécurité', 'caméras', 'surveillance']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_buanderie(text: str) -> bool:
    """Détecte la présence d'une buanderie"""
    text_lower = text.lower()
    keywords = ['buanderie', 'lingerie', 'séchoir']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_dressing(text: str) -> bool:
    """Détecte la présence de dressing"""
    return 'dressing' in text.lower()


def extract_presence_placards(text: str) -> bool:
    """Détecte la présence de placards"""
    text_lower = text.lower()
    keywords = ['placard', 'placards', 'rangement', 'armoires']
    return any(keyword in text_lower for keyword in keywords)


def extract_potentiel_extension(text: str) -> bool:
    """Détecte la possibilité d'extension"""
    text_lower = text.lower()
    keywords = ['possibilité de construire', 'extension possible', 'étage supplémentaire']
    return any(keyword in text_lower for keyword in keywords)


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    text_lower = text.lower()
    proximites = []
    
    keywords = {
        'plage': 'Plage',
        'mer': 'Mer',
        'commerces': 'Commerces',
        'écoles': 'Écoles',
        'école': 'Écoles',
        'collège': 'Collège',
        'lycée': 'Lycée',
        'hôpital': 'Hôpital',
        'clinique': 'Clinique',
        'transports': 'Transports',
        'bus': 'Bus',
        'autoroute': 'Autoroute',
        'aéroport': 'Aéroport',
        'restaurants': 'Restaurants',
        'cafés': 'Cafés',
        'centre ville': 'Centre-ville',
        'centre-ville': 'Centre-ville'
    }
    
    for keyword, label in keywords.items():
        if keyword in text_lower:
            proximites.append(label)
    
    return list(set(proximites))


def extract_telephone_from_text(text: str) -> Optional[str]:
    """Extrait le numéro de téléphone"""
    patterns = [
        r'(?:\+216|00216|216)?\s*(\d[\d\s]{7,})',
        r't[eé]l[eé]phone\s*[:\-]?\s*(\d[\d\s]{7,})',
        r'contact\s*(?:\s*:)?\s*(\d[\d\s]{7,})',
        r'whatsapp[:\s]*(\d[\d\s]{7,})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            tel = re.sub(r'\s', '', m.group(1))
            if len(tel) >= 8:
                if not tel.startswith('+216') and len(tel) == 8:
                    return f"+216{tel}"
                return tel
    
    return None


def extract_equipements_from_text(text: str) -> List[str]:
    """Extrait la liste des équipements depuis le texte"""
    equip_found = []
    text_lower = text.lower()
    
    for eq in EQUIPEMENTS_MAISON:
        if eq in text_lower:
            equip_found.append(eq.title())
    
    seen = set()
    unique_equip = []
    for e in equip_found:
        if e not in seen:
            seen.add(e)
            unique_equip.append(e)
    
    return sorted(unique_equip)


# ========== EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS ==========

def extract_from_caracteristiques(caracteristiques_json: Any) -> Dict[str, Any]:
    """Extrait depuis caracteristiques (JSON)"""
    result = {}
    
    if not caracteristiques_json:
        return result
    
    try:
        if isinstance(caracteristiques_json, str):
            cleaned = caracteristiques_json.replace("'", '"')
            caracs = json.loads(cleaned)
        else:
            caracs = caracteristiques_json
        
        if isinstance(caracs, dict):
            mapping = {
                'type de bien': 'type_bien',
                'etat': 'etat_bien',
                'surface de la parcelle': 'surface_terrain',
                'années': 'age_bien'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    val = caracs[old_key]
                    if 'surface' in old_key and isinstance(val, str):
                        num = extract_number_from_text(val)
                        if num:
                            result[new_key] = num
                        else:
                            result[new_key] = val
                    else:
                        result[new_key] = val
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_informations_supplementaires(info_json: Any) -> Dict[str, Any]:
    """Extrait depuis informations_supplementaires (JSON)"""
    result = {}
    
    if not info_json:
        return result
    
    try:
        if isinstance(info_json, str):
            info = json.loads(info_json) if info_json != "{}" else {}
        else:
            info = info_json
        
        if isinstance(info, dict):
            for key, value in info.items():
                key_clean = key.lower().strip().replace(' ', '_')
                
                if isinstance(value, str):
                    if value.lower() in ['oui', 'yes', 'true', 'disponible']:
                        result[key_clean] = True
                    elif value.lower() in ['non', 'no', 'false']:
                        result[key_clean] = False
                    else:
                        result[key_clean] = value
                else:
                    result[key_clean] = value
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_conditions_vente(conditions_json: Any) -> Dict[str, Any]:
    """Extrait depuis conditions_vente (JSON)"""
    result = {}
    
    if not conditions_json:
        return result
    
    try:
        if isinstance(conditions_json, str):
            conditions = json.loads(conditions_json) if conditions_json != "{}" else {}
        else:
            conditions = conditions_json
        
        if isinstance(conditions, dict):
            for key, value in conditions.items():
                key_clean = key.lower().strip().replace(' ', '_')
                result[key_clean] = value
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_amenities_maison(amenities: Any) -> List[str]:
    """Extrait la liste des amenities maison"""
    if not amenities:
        return []
    
    if isinstance(amenities, list):
        return amenities
    
    if isinstance(amenities, str):
        if ';' in amenities:
            return [a.strip() for a in amenities.split(';') if a.strip()]
        else:
            return [amenities.strip()]
    
    return []


def extract_from_equipements_detaille(equip_det: Any) -> Dict[str, Any]:
    """Extrait depuis equipements_detaille (string avec ;)"""
    result = {
        'equipements_detaille_list': [],
        'terrasse_surface': None,
        'jardin_surface': None,
        'garage_nombre': None
    }
    
    if not equip_det:
        return result
    
    if isinstance(equip_det, str):
        items = [item.strip() for item in equip_det.split(';') if item.strip()]
    elif isinstance(equip_det, list):
        items = equip_det
    else:
        return result
    
    equip_list = []
    
    for item in items:
        if not isinstance(item, str):
            continue
        
        item_lower = item.lower()
        
        if 'terrasse' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['terrasse_surface'] = surface
            equip_list.append('Terrasse')
        elif 'jardin' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['jardin_surface'] = surface
            equip_list.append('Jardin')
        elif 'garage' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['garage_nombre'] = int(nombre)
            equip_list.append('Garage')
        else:
            equip_list.append(item.title())
    
    result['equipements_detaille_list'] = sorted(list(set(equip_list)))
    
    return result


def extract_from_contact_info(contact_json: Any) -> Dict[str, Any]:
    """Extrait depuis contact_info (JSON)"""
    result = {}
    
    if not contact_json:
        return result
    
    try:
        if isinstance(contact_json, str):
            contact = json.loads(contact_json) if contact_json != "{}" else {}
        else:
            contact = contact_json
        
        if isinstance(contact, dict):
            for key, value in contact.items():
                key_clean = key.lower().strip().replace(' ', '_')
                
                if 'formulaire' in key_clean:
                    if isinstance(value, str):
                        result['formulaire_contact'] = value.lower() in ['disponible', 'oui', 'true']
                else:
                    result[key_clean] = value
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_localisation(localisation_json: Any) -> Dict[str, Any]:
    """Extrait depuis localisation (JSON)"""
    result = {}
    
    if not localisation_json:
        return result
    
    try:
        if isinstance(localisation_json, str):
            loc = json.loads(localisation_json) if localisation_json != "{}" else {}
        else:
            loc = localisation_json
        
        if isinstance(loc, dict):
            if 'latitude' in loc:
                try:
                    result['latitude'] = float(loc['latitude'])
                except:
                    pass
            if 'longitude' in loc:
                try:
                    result['longitude'] = float(loc['longitude'])
                except:
                    pass
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_images_list(images_field: Any) -> List[str]:
    """Convertit le champ images en liste"""
    if not images_field:
        return []
    
    if isinstance(images_field, list):
        return images_field
    
    if isinstance(images_field, str):
        if ';' in images_field:
            return [img.strip() for img in images_field.split(';') if img.strip()]
        else:
            return [images_field.strip()]
    
    return []


# ========== FONCTION PRINCIPALE D'EXTRACTION ==========

def extract_all_from_listing(listing: Dict) -> Dict[str, Any]:
    """
    Extrait TOUS les champs possibles d'un listing de maison
    """
    desc_c = listing.get('description_courte', '') or ''
    desc_f = listing.get('description_complete', '') or ''
    all_text = f"{desc_c} {desc_f}".strip()
    
    extracted = {}
    
    # ===== 1. EXTRACTION DEPUIS LES IMAGES =====
    images_list = extract_images_list(listing.get('images', ''))
    dates = []
    for img in images_list:
        date = extract_date_from_url(img)
        if date:
            dates.append(date)
    
    if dates:
        dates.sort()
        extracted['date_publication'] = dates[0]
    
    # ===== 2. EXTRACTION DEPUIS LES TEXTES DESCRIPTIFS =====
    
    # Titre amélioré
    titre = extract_titre_ameliore(desc_c, desc_f)
    if titre:
        extracted['titre_ameliore'] = titre
    
    # Prix
    prix_info = extract_prix_from_text(all_text)
    extracted.update(prix_info)
    
    # Surfaces
    surface_hab = extract_surface_habitable_from_text(all_text)
    if surface_hab:
        extracted['surface_habitable'] = surface_hab
    
    surface_terrain = extract_surface_terrain_from_text(all_text)
    if surface_terrain:
        extracted['surface_terrain'] = surface_terrain
    
    # Nombre de niveaux
    nb_niveaux = extract_nombre_niveaux(all_text)
    if nb_niveaux:
        extracted['nombre_niveaux'] = nb_niveaux
    
    # Type de maison
    type_maison = extract_type_maison_from_text(all_text)
    if type_maison:
        extracted['type_maison_extrait'] = type_maison
    
    # Jardin
    extracted['a_jardin'] = extract_presence_jardin(all_text)
    surface_jardin = extract_surface_jardin(all_text)
    if surface_jardin:
        extracted['surface_jardin'] = surface_jardin
    
    # Piscine
    extracted['a_piscine'] = extract_presence_piscine(all_text)
    surface_piscine = extract_surface_piscine(all_text)
    if surface_piscine:
        extracted['surface_piscine'] = surface_piscine
    
    # Terrasse
    extracted['a_terrasse'] = extract_presence_terrasse(all_text)
    surface_terrasse = extract_surface_terrasse(all_text)
    if surface_terrasse:
        extracted['surface_terrasse'] = surface_terrasse
    
    # Garage
    extracted['a_garage'] = extract_presence_garage(all_text)
    nb_garage = extract_nombre_garage(all_text)
    if nb_garage:
        extracted['garage_nombre'] = nb_garage
    
    # Cave/Cellier
    extracted['a_cave'] = extract_presence_cave(all_text)
    
    # Cheminée
    extracted['a_cheminee'] = extract_presence_cheminée(all_text)
    
    # Année construction
    annee = extract_annee_construction(all_text)
    if annee:
        extracted['annee_construction'] = annee
    
    # État
    etat = extract_etat_maison(all_text)
    if etat:
        extracted['etat_maison'] = etat
    
    # Orientation
    orientation = extract_orientation(all_text)
    if orientation:
        extracted['orientation'] = orientation
    
    # Vue
    vue = extract_vue(all_text)
    if vue:
        extracted['vue_type'] = vue
    
    # Chauffage
    chauffage = extract_chauffage_type(all_text)
    if chauffage:
        extracted['chauffage_type'] = chauffage
    
    # Climatisation
    climatisation = extract_climatisation_type(all_text)
    if climatisation:
        extracted['climatisation_type'] = climatisation
    
    # Sécurité
    extracted['a_alarme'] = extract_presence_alarme(all_text)
    
    # Buanderie
    extracted['a_buanderie'] = extract_presence_buanderie(all_text)
    
    # Dressing
    extracted['a_dressing'] = extract_presence_dressing(all_text)
    
    # Placards
    extracted['a_placards'] = extract_presence_placards(all_text)
    
    # Potentiel extension
    extracted['potentiel_extension'] = extract_potentiel_extension(all_text)
    
    # Proximités
    proximites = extract_proximites(all_text)
    if proximites:
        extracted['proximites'] = proximites
    
    # Téléphone
    telephone = extract_telephone_from_text(all_text)
    if telephone:
        extracted['telephone_extrait'] = telephone
    
    # Équipements
    equip_text = extract_equipements_from_text(all_text)
    if equip_text:
        extracted['equipements_texte'] = equip_text
    
    # ===== 3. EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS =====
    
    # Caracteristiques
    caracs_info = extract_from_caracteristiques(listing.get('caracteristiques'))
    if caracs_info:
        extracted.update({f"caracs_{k}": v for k, v in caracs_info.items()})
    
    # Informations supplémentaires
    info_supp = extract_from_informations_supplementaires(listing.get('informations_supplementaires'))
    if info_supp:
        extracted['infos_supp_parse'] = info_supp
    
    # Conditions de vente
    conditions = extract_from_conditions_vente(listing.get('conditions_vente'))
    if conditions:
        extracted['conditions_vente_parse'] = conditions
    
    # Amenities maison
    amenities = extract_from_amenities_maison(listing.get('amenities_maison', []))
    if amenities:
        extracted['amenities_maison_list'] = amenities
    
    # Équipements détaillés
    equip_det_info = extract_from_equipements_detaille(listing.get('equipements_detaille'))
    if equip_det_info:
        if equip_det_info.get('equipements_detaille_list'):
            extracted['equipements_detaille_list'] = equip_det_info['equipements_detaille_list']
        if equip_det_info.get('terrasse_surface'):
            extracted['surface_terrasse_det'] = equip_det_info['terrasse_surface']
        if equip_det_info.get('jardin_surface'):
            extracted['surface_jardin_det'] = equip_det_info['jardin_surface']
        if equip_det_info.get('garage_nombre'):
            extracted['garage_nombre_det'] = equip_det_info['garage_nombre']
    
    # Contact info
    contact = extract_from_contact_info(listing.get('contact_info'))
    if contact:
        extracted['contact_info_parse'] = contact
    
    # Localisation GPS
    localisation = extract_from_localisation(listing.get('localisation'))
    if localisation:
        extracted['gps'] = localisation
    
    return extracted


def enrich_listing(listing: Dict) -> Dict:
    """
    Enrichit complètement un listing de maison
    """
    extracted = extract_all_from_listing(listing)
    
    enriched = listing.copy()
    
    # ===== FUSION DES DONNÉES EXTRAITES =====
    
    # Date publication
    if extracted.get('date_publication'):
        enriched['date_publication'] = extracted['date_publication']
    
    # Titre amélioré
    if extracted.get('titre_ameliore') and (not listing.get('titre') or len(listing.get('titre', '')) < len(extracted['titre_ameliore'])):
        enriched['titre'] = extracted['titre_ameliore']
    
    # Prix
    if extracted.get('prix') and (not listing.get('prix') or listing.get('prix') == 0):
        enriched['prix'] = extracted['prix']
        if extracted.get('prix_text'):
            enriched['prix_text'] = extracted['prix_text']
    
    # Surfaces
    if extracted.get('surface_habitable') and not listing.get('surface'):
        enriched['surface'] = extracted['surface_habitable']
        enriched['surface_text'] = f"{int(extracted['surface_habitable'])} m²"
    
    if extracted.get('surface_terrain') and not listing.get('surface_terrain'):
        enriched['surface_terrain'] = extracted['surface_terrain']
    
    # Type de maison
    if extracted.get('type_maison_extrait') and not listing.get('type_maison'):
        enriched['type_maison'] = extracted['type_maison_extrait']
    
    # Nombre de niveaux
    if extracted.get('nombre_niveaux') and not listing.get('nombre_niveaux'):
        enriched['nombre_niveaux'] = extracted['nombre_niveaux']
    
    # Jardin
    if extracted.get('a_jardin') is not None:
        enriched['a_jardin'] = extracted['a_jardin']
    if extracted.get('surface_jardin') or extracted.get('surface_jardin_det'):
        enriched['surface_jardin'] = extracted.get('surface_jardin') or extracted.get('surface_jardin_det')
    
    # Piscine
    if extracted.get('a_piscine') is not None:
        enriched['a_piscine'] = extracted['a_piscine']
    if extracted.get('surface_piscine'):
        enriched['surface_piscine'] = extracted['surface_piscine']
    
    # Terrasse
    if extracted.get('a_terrasse') is not None:
        enriched['a_terrasse'] = extracted['a_terrasse']
    if extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det'):
        enriched['surface_terrasse'] = extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det')
    
    # Garage
    if extracted.get('a_garage') is not None:
        enriched['a_garage'] = extracted['a_garage']
    if extracted.get('garage_nombre') or extracted.get('garage_nombre_det'):
        enriched['garage_nombre'] = extracted.get('garage_nombre') or extracted.get('garage_nombre_det')
    
    # Autres équipements
    bool_fields = ['a_cave', 'a_cheminee', 'a_alarme', 'a_buanderie', 'a_dressing', 'a_placards']
    for field in bool_fields:
        if extracted.get(field) is not None:
            enriched[field] = extracted[field]
    
    # Année construction
    if extracted.get('annee_construction') and not listing.get('annee_construction'):
        enriched['annee_construction'] = extracted['annee_construction']
    
    # État
    if extracted.get('etat_maison') and not listing.get('etat_maison'):
        enriched['etat_maison'] = extracted['etat_maison']
    
    # Orientation
    if extracted.get('orientation') and not listing.get('orientation'):
        enriched['orientation'] = extracted['orientation']
    
    # Vue
    if extracted.get('vue_type') and not listing.get('vue_type'):
        enriched['vue_type'] = extracted['vue_type']
    
    # Chauffage
    if extracted.get('chauffage_type') and not listing.get('chauffage_type'):
        enriched['chauffage_type'] = extracted['chauffage_type']
    
    # Climatisation
    if extracted.get('climatisation_type') and not listing.get('climatisation_type'):
        enriched['climatisation_type'] = extracted['climatisation_type']
    
    # Potentiel extension
    if extracted.get('potentiel_extension') is not None:
        enriched['potentiel_extension'] = extracted['potentiel_extension']
    
    # Proximités
    if extracted.get('proximites'):
        enriched['proximites'] = extracted['proximites']
    
    # Téléphone
    if extracted.get('telephone_extrait'):
        contact_info = enriched.get('contact_info', {})
        if isinstance(contact_info, str):
            try:
                contact_info = json.loads(contact_info)
            except:
                contact_info = {}
        if isinstance(contact_info, dict):
            contact_info['telephone'] = extracted['telephone_extrait']
            enriched['contact_info'] = json.dumps(contact_info, ensure_ascii=False)
    
    # Équipements fusionnés
    all_equipements = list(set(listing.get('equipements', []) + 
                                extracted.get('equipements_texte', []) +
                                extracted.get('amenities_maison_list', []) +
                                extracted.get('equipements_detaille_list', [])))
    if all_equipements:
        enriched['equipements'] = sorted(all_equipements)
    
    # Caractéristiques extraites
    caracs = {}
    for key, value in extracted.items():
        if key.startswith('caracs_'):
            field = key.replace('caracs_', '')
            caracs[field] = value
    if caracs:
        enriched['caracteristiques_extraites'] = caracs
    
    # Infos supplémentaires parsées
    if extracted.get('infos_supp_parse'):
        enriched['informations_supplementaires_parse'] = extracted['infos_supp_parse']
    
    # Conditions de vente parsées
    if extracted.get('conditions_vente_parse'):
        enriched['conditions_vente_parse'] = extracted['conditions_vente_parse']
    
    # Contact info parsé
    if extracted.get('contact_info_parse'):
        enriched['contact_info_parse'] = extracted['contact_info_parse']
    
    # GPS
    if extracted.get('gps'):
        enriched['gps'] = extracted['gps']
    
    return enriched


def process_json_file(input_path: str, output_path: Optional[str] = None) -> int:
    """
    Charge le JSON, enrichit chaque listing, sauvegarde
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get('listings', [])
    enriched_listings = []
    
    stats = {
        'total': len(listings),
        'dates_publication': 0,
        'prix_extraits': 0,
        'surfaces_hab_extraites': 0,
        'surfaces_terrain_extraites': 0,
        'jardins_detectes': 0,
        'piscines_detectees': 0,
        'terrasses_detectees': 0,
        'garages_detectes': 0,
        'cheminees_detectees': 0,
        'annees_constructions': 0,
        'contacts_extraits': 0
    }
    
    for listing in listings:
        try:
            enriched = enrich_listing(listing)
            enriched_listings.append(enriched)
            
            # Statistiques
            if enriched.get('date_publication'):
                stats['dates_publication'] += 1
            if enriched.get('prix') and listing.get('prix') != enriched.get('prix'):
                stats['prix_extraits'] += 1
            if enriched.get('surface') and not listing.get('surface'):
                stats['surfaces_hab_extraites'] += 1
            if enriched.get('surface_terrain'):
                stats['surfaces_terrain_extraites'] += 1
            if enriched.get('a_jardin'):
                stats['jardins_detectes'] += 1
            if enriched.get('a_piscine'):
                stats['piscines_detectees'] += 1
            if enriched.get('a_terrasse'):
                stats['terrasses_detectees'] += 1
            if enriched.get('a_garage'):
                stats['garages_detectes'] += 1
            if enriched.get('a_cheminee'):
                stats['cheminees_detectees'] += 1
            if enriched.get('annee_construction'):
                stats['annees_constructions'] += 1
            if enriched.get('telephone_extrait'):
                stats['contacts_extraits'] += 1
                
        except Exception as e:
            print(f"❌ Erreur listing {listing.get('id', '?')}: {e}")
            enriched_listings.append(listing)
    
    data['listings'] = enriched_listings
    
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['extraction_date'] = datetime.now().isoformat() + 'Z'
    data['metadata']['listings_traites'] = len(enriched_listings)
    data['metadata']['statistiques_extraction'] = stats
    
    out = output_path or str(path.parent / f"{path.stem}_extrait.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES D'EXTRACTION - VENTE DE MAISONS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Surfaces habitables extraites: {stats['surfaces_hab_extraites']}")
    print(f"✅ Surfaces terrain extraites: {stats['surfaces_terrain_extraites']}")
    print(f"✅ Jardins détectés: {stats['jardins_detectes']}")
    print(f"✅ Piscines détectées: {stats['piscines_detectees']}")
    print(f"✅ Terrasses détectées: {stats['terrasses_detectees']}")
    print(f"✅ Garages détectés: {stats['garages_detectes']}")
    print(f"✅ Cheminées détectées: {stats['cheminees_detectees']}")
    print(f"✅ Années construction extraites: {stats['annees_constructions']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Vente de Maisons")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()