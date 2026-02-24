"""
Agent d'extraction pour Location d'Appartements
Extrait TOUS les champs spécifiques à la location
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES À LA LOCATION ==========

TYPES_APPARTEMENTS = [
    'studio', 's1', 's2', 's3', 's4', 's5',
    'duplex', 'triplex', 'penthouse', 'loft'
]

EQUIPEMENTS_LOCATION = [
    'ascenseur', 'parking', 'garage', 'terrasse', 'balcon',
    'jardin', 'vue sur mer', 'vue dégagée', 'climatisation',
    'chauffage central', 'chauffage individuel', 'double vitrage',
    'porte blindée', 'cuisine équipée', 'cuisine américaine',
    'réfrigérateur', 'four', 'micro-ondes', 'lave-vaisselle',
    'machine à laver', 'sèche-linge', 'tv', 'internet', 'fibre',
    'alarme', 'gardien', 'vidéosurveillance', 'interphone',
    'meublé', 'non meublé', 'chambre de service', 'buanderie',
    'cellier', 'débarras', 'dressing', 'placards'
]

PROXIMITES_APPARTEMENT = [
    'transports', 'bus', 'métro', 'tram', 'commerces',
    'supermarché', 'marché', 'écoles', 'collège', 'lycée',
    'hôpital', 'clinique', 'pharmacie', 'restaurants',
    'plage', 'mer', 'lac', 'parc', 'jardin public'
]

REGIONS_MAPPING = {
    "tunis": "Tunis", "la marsa": "Tunis", "carthage": "Tunis", "le kram": "Tunis",
    "ariana": "Ariana", "ennasr": "Ariana", "manzah": "Ariana", "soukra": "Ariana", "raoued": "Ariana",
    "ben arous": "Ben Arous", "boumhel": "Ben Arous", "mohammedia": "Ben Arous",
    "nabeul": "Nabeul", "hammamet": "Nabeul", "kélibia": "Nabeul",
    "sousse": "Sousse", "hammam sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte"
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


def extract_loyer_from_text(text: str) -> Dict[str, Any]:
    """Extraction du loyer"""
    result = {}
    text_lower = text.lower()
    
    if any(phrase in text_lower for phrase in ['prix à consulter', 'loyer à consulter', 'nous consulter']):
        result['loyer'] = 0
        result['loyer_text'] = 'Prix à consulter'
        return result
    
    # Loyer mensuel
    loyer_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 1),
        (r'loyer\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)', 1),
        (r'(\d+)\s*tnd', 1),
        (r'(\d+)\s*dt\b', 1),
        (r'(\d+)\s*tnd\s*/\s*mois', 1),
        (r'(\d+)\s*dt\s*/\s*mois', 1),
    ]
    
    for pattern, group in loyer_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                loyer_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(loyer_str)
                if 100 <= val <= 50000:
                    result['loyer'] = val
                    break
            except:
                continue
    
    return result


def extract_charges_incluses(text: str) -> bool:
    """Détecte si les charges sont incluses"""
    text_lower = text.lower()
    
    if 'charges incluses' in text_lower:
        return True
    elif 'charges comprises' in text_lower:
        return True
    elif 'syndic inclus' in text_lower:
        return True
    elif 'frais de syndic inclus' in text_lower:
        return True
    
    return False


def extract_montant_charges(text: str) -> Optional[float]:
    """Extrait le montant des charges"""
    patterns = [
        r'charges\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'(\d+)\s*(?:tnd|dt)\s*de\s*charges',
        r'syndic\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_caution(text: str) -> Optional[float]:
    """Extrait le montant de la caution"""
    patterns = [
        r'caution\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'(\d+)\s*(?:tnd|dt)\s*de\s*caution',
        r'dépôt de garantie\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_duree_location(text: str) -> Optional[str]:
    """Extrait la durée de location"""
    text_lower = text.lower()
    
    if 'long terme' in text_lower:
        return 'Long terme'
    elif 'courte durée' in text_lower:
        return 'Courte durée'
    elif 'saisonnier' in text_lower:
        return 'Saisonnier'
    elif 'vacances' in text_lower:
        return 'Vacances'
    elif 'à l\'année' in text_lower:
        return 'Long terme'
    
    return 'Long terme'  # Par défaut


def extract_duree_minimum(text: str) -> Optional[str]:
    """Extrait la durée minimum de location"""
    patterns = [
        r'minimum\s*(\d+)\s*mois',
        r'(\d+)\s*mois\s*minimum',
        r'location\s*(\d+)\s*mois',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return f"{m.group(1)} mois"
            except:
                pass
    
    return None


def extract_preavis(text: str) -> Optional[str]:
    """Extrait le préavis"""
    patterns = [
        r'préavis\s*[:\-]?\s*(\d+)\s*mois',
        r'(\d+)\s*mois\s*de\s*préavis',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return f"{m.group(1)} mois"
            except:
                pass
    
    return None


def extract_etage_from_text(text: str) -> Optional[int]:
    """Extrait le numéro d'étage"""
    text_lower = text.lower()
    
    patterns = [
        r'au\s+(\d+)[eè]me?\s*[eé]tage',
        r'(\d+)[eè]me?\s*[eé]tage',
        r'étage\s*[:\-]?\s*(\d+)',
        r'situé au (\d+)[eè]?',
        r'rdc',
        r'rez-de-chaussée',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            if 'rdc' in m.group(0) or 'rez' in m.group(0):
                return 0
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_est_dernier_etage(text: str) -> bool:
    """Détecte si c'est un dernier étage"""
    text_lower = text.lower()
    keywords = ['dernier étage', 'dernier etage', 'penthouse', 'rooftop']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_ascenseur(text: str) -> bool:
    """Détecte la présence d'un ascenseur"""
    return 'ascenseur' in text.lower()


def extract_nombre_ascenseurs(text: str) -> Optional[int]:
    """Extrait le nombre d'ascenseurs"""
    patterns = [
        r'(\d+)\s*ascenseur[s]?',
        r'ascenseur\s*(\d+)',
        r'double\s*ascenseur',
        r'deux\s*ascenseurs',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            if 'double' in pattern or 'deux' in pattern:
                return 2
            try:
                return int(m.group(1))
            except:
                pass
    
    return 1 if 'ascenseur' in text_lower else None


def extract_presence_parking(text: str) -> bool:
    """Détecte la présence d'un parking"""
    text_lower = text.lower()
    keywords = ['parking', 'garage', 'place de parking', 'sous-sol']
    return any(keyword in text_lower for keyword in keywords)


def extract_nombre_parking(text: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    patterns = [
        r'(\d+)\s*place[s]?\s*(?:de)?\s*parking',
        r'(\d+)\s*parking[s]?',
        r'parking\s+(\d+)\s*places?',
        r'(\d+)\s*garage[s]?',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return 1 if extract_presence_parking(text) else None


def extract_type_parking(text: str) -> Optional[str]:
    """Extrait le type de parking"""
    text_lower = text.lower()
    
    if 'sous-sol' in text_lower:
        return 'Sous-sol'
    elif 'couvert' in text_lower:
        return 'Couvert'
    elif 'extérieur' in text_lower:
        return 'Extérieur'
    elif 'garage' in text_lower:
        return 'Garage'
    
    return None


def extract_presence_meuble(text: str) -> bool:
    """Détecte si l'appartement est meublé"""
    text_lower = text.lower()
    
    if 'meublé' in text_lower:
        return True
    elif 'non meublé' in text_lower:
        return False
    elif 'vide' in text_lower:
        return False
    
    return False  # Par défaut, non meublé


def extract_niveau_meuble(text: str) -> Optional[str]:
    """Extrait le niveau de meublé"""
    text_lower = text.lower()
    
    if 'entièrement meublé' in text_lower:
        return 'Entièrement meublé'
    elif 'partiellement meublé' in text_lower:
        return 'Partiellement meublé'
    elif 'meublé avec goût' in text_lower:
        return 'Meublé avec goût'
    elif 'meublé' in text_lower:
        return 'Meublé'
    elif 'vide' in text_lower:
        return 'Vide'
    
    return None


def extract_vue(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower:
        return 'Mer'
    elif 'vue mer' in text_lower:
        return 'Mer'
    elif 'vue sur lac' in text_lower:
        return 'Lac'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue panoramique' in text_lower:
        return 'Panoramique'
    elif 'vue sur piscine' in text_lower:
        return 'Piscine'
    elif 'vue sur jardin' in text_lower:
        return 'Jardin'
    
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


def extract_presence_balcon(text: str) -> bool:
    """Détecte la présence d'un balcon"""
    return 'balcon' in text.lower()


def extract_presence_jardin(text: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in text.lower()


def extract_presence_cuisine_equipee(text: str) -> bool:
    """Détecte si la cuisine est équipée"""
    text_lower = text.lower()
    keywords = ['cuisine équipée', 'cuisine equipee', 'cuisine aménagée']
    return any(keyword in text_lower for keyword in keywords)


def extract_type_cuisine(text: str) -> Optional[str]:
    """Extrait le type de cuisine"""
    text_lower = text.lower()
    
    if 'cuisine américaine' in text_lower:
        return 'Américaine'
    elif 'cuisine équipée' in text_lower:
        return 'Équipée'
    elif 'cuisine aménagée' in text_lower:
        return 'Aménagée'
    elif 'cuisine séparée' in text_lower:
        return 'Séparée'
    elif 'cuisine ouverte' in text_lower:
        return 'Ouverte'
    
    return None


def extract_presence_chambre_service(text: str) -> bool:
    """Détecte la présence d'une chambre de service"""
    return 'chambre de service' in text.lower()


def extract_presence_buanderie(text: str) -> bool:
    """Détecte la présence d'une buanderie"""
    return 'buanderie' in text.lower()


def extract_presence_cellier(text: str) -> bool:
    """Détecte la présence d'un cellier"""
    return 'cellier' in text.lower() or 'débarras' in text.lower()


def extract_presence_dressing(text: str) -> bool:
    """Détecte la présence de dressing"""
    return 'dressing' in text.lower()


def extract_chauffage_type(text: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    text_lower = text.lower()
    
    if 'chauffage central' in text_lower:
        return 'Central'
    elif 'chauffage individuel' in text_lower:
        return 'Individuel'
    elif 'chauffage électrique' in text_lower:
        return 'Électrique'
    
    return None


def extract_climatisation_type(text: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    text_lower = text.lower()
    
    if 'climatisation centrale' in text_lower:
        return 'Centrale'
    elif 'climatisation réversible' in text_lower:
        return 'Réversible'
    elif 'climatisation split' in text_lower:
        return 'Split'
    
    return None


def extract_presence_securite(text: str) -> bool:
    """Détecte la présence de sécurité"""
    text_lower = text.lower()
    keywords = ['sécurité', 'gardien', 'concierge', 'caméras', 'alarme', 'code']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_internet(text: str) -> bool:
    """Détecte la présence d'internet"""
    text_lower = text.lower()
    keywords = ['internet', 'fibre', 'wifi', 'fibre optique']
    return any(keyword in text_lower for keyword in keywords)


def extract_animaux_acceptes(text: str) -> bool:
    """Détecte si les animaux sont acceptés"""
    text_lower = text.lower()
    
    if 'animaux acceptés' in text_lower:
        return True
    elif 'animaux non acceptés' in text_lower:
        return False
    elif 'animaux autorisés' in text_lower:
        return True
    
    return False


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_APPARTEMENT:
        if prox in text_lower:
            if prox == 'bus':
                found_prox.append('Bus')
            elif prox == 'métro':
                found_prox.append('Métro')
            else:
                found_prox.append(prox.title())
    
    return list(set(found_prox))


def extract_reference(text: str) -> Optional[str]:
    """Extrait la référence de l'annonce"""
    patterns = [
        r'r[eé]f[^:]*:\s*([A-Za-z0-9\-]+)',
        r'r[eé]f[eé]rence\s*[:\-]?\s*([A-Za-z0-9\-]+)',
        r'ref\s*[:\-]?\s*([A-Za-z0-9\-]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None


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
    
    for eq in EQUIPEMENTS_LOCATION:
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
                'années': 'age_bien',
                'type du sol': 'type_sol',
                'étage du bien': 'etage',
                'orientation': 'orientation'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    val = caracs[old_key]
                    if 'etage' in new_key and isinstance(val, str):
                        num = extract_number_from_text(val)
                        if num is not None:
                            result[new_key] = int(num)
                        else:
                            result[new_key] = val
                    else:
                        result[new_key] = val
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_equipements_detaille(equip_det: Any) -> Dict[str, Any]:
    """Extrait depuis equipements_detaille (string avec ;)"""
    result = {
        'equipements_list': [],
        'terrasse_surface': None,
        'jardin_surface': None,
        'parking_nombre': None
    }
    
    if not equip_det:
        return result
    
    if isinstance(equip_det, str):
        items = [item.strip() for item in equip_det.split(';') if item.strip()]
    elif isinstance(equip_det, list):
        items = equip_det
    else:
        return result
    
    for item in items:
        if not isinstance(item, str):
            continue
        
        item_lower = item.lower()
        
        if 'terrasse' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['terrasse_surface'] = surface
            result['equipements_list'].append('Terrasse')
        elif 'jardin' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['jardin_surface'] = surface
            result['equipements_list'].append('Jardin')
        elif 'parking' in item_lower or 'garage' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['parking_nombre'] = int(nombre)
            result['equipements_list'].append('Parking')
        else:
            result['equipements_list'].append(item.title())
    
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


def extract_from_conditions_location(conditions_json: Any) -> Dict[str, Any]:
    """Extrait depuis conditions_location (JSON)"""
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
    Extrait TOUS les champs possibles d'un listing de location d'appartement
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
    
    # Loyer
    loyer_info = extract_loyer_from_text(all_text)
    extracted.update(loyer_info)
    
    # Charges
    extracted['charges_incluses'] = extract_charges_incluses(all_text)
    montant_charges = extract_montant_charges(all_text)
    if montant_charges:
        extracted['montant_charges'] = montant_charges
    
    # Caution
    caution = extract_caution(all_text)
    if caution:
        extracted['caution'] = caution
    
    # Durée
    duree = extract_duree_location(all_text)
    if duree:
        extracted['duree_location_extrait'] = duree
    
    duree_min = extract_duree_minimum(all_text)
    if duree_min:
        extracted['duree_minimum'] = duree_min
    
    preavis = extract_preavis(all_text)
    if preavis:
        extracted['preavis'] = preavis
    
    # Étage
    etage = extract_etage_from_text(all_text)
    if etage is not None:
        extracted['etage_extrait'] = etage
    
    extracted['dernier_etage'] = extract_est_dernier_etage(all_text)
    
    # Ascenseur
    extracted['a_ascenseur'] = extract_presence_ascenseur(all_text)
    nb_ascenseurs = extract_nombre_ascenseurs(all_text)
    if nb_ascenseurs:
        extracted['nombre_ascenseurs'] = nb_ascenseurs
    
    # Parking
    extracted['a_parking'] = extract_presence_parking(all_text)
    nb_parking = extract_nombre_parking(all_text)
    if nb_parking:
        extracted['parking_nombre'] = nb_parking
    parking_type = extract_type_parking(all_text)
    if parking_type:
        extracted['parking_type'] = parking_type
    
    # Meublé
    extracted['meuble'] = extract_presence_meuble(all_text)
    niveau_meuble = extract_niveau_meuble(all_text)
    if niveau_meuble:
        extracted['niveau_meuble'] = niveau_meuble
    
    # Vue
    vue = extract_vue(all_text)
    if vue:
        extracted['vue'] = vue
    
    # Terrasse/Balcon/Jardin
    extracted['a_terrasse'] = extract_presence_terrasse(all_text)
    surface_terrasse = extract_surface_terrasse(all_text)
    if surface_terrasse:
        extracted['surface_terrasse'] = surface_terrasse
    
    extracted['a_balcon'] = extract_presence_balcon(all_text)
    extracted['a_jardin'] = extract_presence_jardin(all_text)
    
    # Cuisine
    extracted['cuisine_equipee'] = extract_presence_cuisine_equipee(all_text)
    type_cuisine = extract_type_cuisine(all_text)
    if type_cuisine:
        extracted['type_cuisine'] = type_cuisine
    
    # Équipements supplémentaires
    extracted['a_chambre_service'] = extract_presence_chambre_service(all_text)
    extracted['a_buanderie'] = extract_presence_buanderie(all_text)
    extracted['a_cellier'] = extract_presence_cellier(all_text)
    extracted['a_dressing'] = extract_presence_dressing(all_text)
    
    # Chauffage et climatisation
    chauffage = extract_chauffage_type(all_text)
    if chauffage:
        extracted['chauffage_type'] = chauffage
    
    clim = extract_climatisation_type(all_text)
    if clim:
        extracted['climatisation_type'] = clim
    
    # Sécurité
    extracted['a_securite'] = extract_presence_securite(all_text)
    
    # Internet
    extracted['a_internet'] = extract_presence_internet(all_text)
    
    # Animaux
    extracted['animaux_acceptes'] = extract_animaux_acceptes(all_text)
    
    # Proximités
    proximites = extract_proximites(all_text)
    if proximites:
        extracted['proximites'] = proximites
    
    # Référence
    reference = extract_reference(all_text)
    if reference:
        extracted['reference_extrait'] = reference
    
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
    
    # Équipements détaillés
    equip_det_info = extract_from_equipements_detaille(listing.get('equipements_detaille'))
    if equip_det_info:
        if equip_det_info.get('equipements_list'):
            extracted['equipements_detaille_list'] = equip_det_info['equipements_list']
        if equip_det_info.get('terrasse_surface'):
            extracted['surface_terrasse_det'] = equip_det_info['terrasse_surface']
        if equip_det_info.get('jardin_surface'):
            extracted['surface_jardin_det'] = equip_det_info['jardin_surface']
        if equip_det_info.get('parking_nombre'):
            extracted['parking_nombre_det'] = equip_det_info['parking_nombre']
    
    # Informations supplémentaires
    info_supp = extract_from_informations_supplementaires(listing.get('informations_supplementaires'))
    if info_supp:
        extracted['infos_supp_parse'] = info_supp
    
    # Conditions de location
    conditions = extract_from_conditions_location(listing.get('conditions_location'))
    if conditions:
        extracted['conditions_location_parse'] = conditions
    
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
    Enrichit complètement un listing de location d'appartement
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
    
    # Loyer
    if extracted.get('loyer') and (not listing.get('loyer') or listing.get('loyer') == 0):
        enriched['loyer'] = extracted['loyer']
        if extracted.get('loyer_text'):
            enriched['loyer_text'] = extracted['loyer_text']
    
    # Charges
    if extracted.get('charges_incluses') is not None:
        enriched['charges_incluses'] = extracted['charges_incluses']
    if extracted.get('montant_charges'):
        enriched['montant_charges'] = extracted['montant_charges']
    
    # Caution
    if extracted.get('caution'):
        enriched['caution'] = extracted['caution']
    
    # Durée
    if extracted.get('duree_location_extrait') and not listing.get('duree_location'):
        enriched['duree_location'] = extracted['duree_location_extrait']
    if extracted.get('duree_minimum'):
        enriched['duree_minimum'] = extracted['duree_minimum']
    if extracted.get('preavis'):
        enriched['preavis'] = extracted['preavis']
    
    # Étage
    if extracted.get('etage_extrait') is not None and not listing.get('etage'):
        enriched['etage'] = extracted['etage_extrait']
    if extracted.get('dernier_etage') is not None:
        enriched['dernier_etage'] = extracted['dernier_etage']
    
    # Ascenseur
    if extracted.get('a_ascenseur') is not None:
        enriched['a_ascenseur'] = extracted['a_ascenseur']
    if extracted.get('nombre_ascenseurs'):
        enriched['nombre_ascenseurs'] = extracted['nombre_ascenseurs']
    
    # Parking
    if extracted.get('a_parking') is not None:
        enriched['a_parking'] = extracted['a_parking']
    if extracted.get('parking_nombre') or extracted.get('parking_nombre_det'):
        enriched['parking_nombre'] = extracted.get('parking_nombre') or extracted.get('parking_nombre_det')
    if extracted.get('parking_type'):
        enriched['parking_type'] = extracted['parking_type']
    
    # Meublé
    if extracted.get('meuble') is not None:
        enriched['meuble'] = extracted['meuble']
    if extracted.get('niveau_meuble'):
        enriched['niveau_meuble'] = extracted['niveau_meuble']
    
    # Vue
    if extracted.get('vue') and not listing.get('vue'):
        enriched['vue'] = extracted['vue']
    
    # Terrasse/Balcon/Jardin
    if extracted.get('a_terrasse') is not None:
        enriched['a_terrasse'] = extracted['a_terrasse']
    if extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det'):
        enriched['surface_terrasse'] = extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det')
    
    if extracted.get('a_balcon') is not None:
        enriched['a_balcon'] = extracted['a_balcon']
    if extracted.get('a_jardin') is not None:
        enriched['a_jardin'] = extracted['a_jardin']
    
    # Cuisine
    if extracted.get('cuisine_equipee') is not None:
        enriched['cuisine_equipee'] = extracted['cuisine_equipee']
    if extracted.get('type_cuisine'):
        enriched['type_cuisine'] = extracted['type_cuisine']
    
    # Équipements supplémentaires
    bool_fields = ['a_chambre_service', 'a_buanderie', 'a_cellier', 'a_dressing',
                   'a_securite', 'a_internet']
    for field in bool_fields:
        if extracted.get(field) is not None:
            enriched[field] = extracted[field]
    
    # Chauffage et climatisation
    if extracted.get('chauffage_type') and not listing.get('chauffage_type'):
        enriched['chauffage_type'] = extracted['chauffage_type']
    if extracted.get('climatisation_type') and not listing.get('climatisation_type'):
        enriched['climatisation_type'] = extracted['climatisation_type']
    
    # Animaux
    if extracted.get('animaux_acceptes') is not None:
        enriched['animaux_acceptes'] = extracted['animaux_acceptes']
    
    # Proximités
    if extracted.get('proximites'):
        enriched['proximites'] = extracted['proximites']
    
    # Référence
    if extracted.get('reference_extrait') and not listing.get('reference'):
        enriched['reference'] = extracted['reference_extrait']
    
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
    
    # Conditions de location parsées
    if extracted.get('conditions_location_parse'):
        enriched['conditions_location_parse'] = extracted['conditions_location_parse']
    
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
        'loyers_extraits': 0,
        'charges_detectees': 0,
        'parkings_detectes': 0,
        'ascenseurs_detectes': 0,
        'meubles_detectes': 0,
        'vues_mer_detectees': 0,
        'etages_extraits': 0,
        'terrasses_detectees': 0,
        'references_extraites': 0,
        'contacts_extraits': 0
    }
    
    for listing in listings:
        try:
            enriched = enrich_listing(listing)
            enriched_listings.append(enriched)
            
            # Statistiques
            if enriched.get('date_publication'):
                stats['dates_publication'] += 1
            if enriched.get('loyer') and listing.get('loyer') != enriched.get('loyer'):
                stats['loyers_extraits'] += 1
            if enriched.get('charges_incluses') or enriched.get('montant_charges'):
                stats['charges_detectees'] += 1
            if enriched.get('a_parking'):
                stats['parkings_detectes'] += 1
            if enriched.get('a_ascenseur'):
                stats['ascenseurs_detectes'] += 1
            if enriched.get('meuble'):
                stats['meubles_detectes'] += 1
            if enriched.get('vue') == 'Mer':
                stats['vues_mer_detectees'] += 1
            if enriched.get('etage') and not listing.get('etage'):
                stats['etages_extraits'] += 1
            if enriched.get('a_terrasse'):
                stats['terrasses_detectees'] += 1
            if enriched.get('reference'):
                stats['references_extraites'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - LOCATION APPARTEMENTS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Loyers extraits/améliorés: {stats['loyers_extraits']}")
    print(f"✅ Charges détectées: {stats['charges_detectees']}")
    print(f"✅ Parkings détectés: {stats['parkings_detectes']}")
    print(f"✅ Ascenseurs détectés: {stats['ascenseurs_detectes']}")
    print(f"✅ Meublés détectés: {stats['meubles_detectes']}")
    print(f"✅ Vues mer détectées: {stats['vues_mer_detectees']}")
    print(f"✅ Étages extraits: {stats['etages_extraits']}")
    print(f"✅ Terrasses détectées: {stats['terrasses_detectees']}")
    print(f"✅ Références extraites: {stats['references_extraites']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Location d'Appartements")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()