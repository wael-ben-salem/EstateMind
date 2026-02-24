"""
Agent d'extraction pour Location de Bureaux
Extrait TOUS les champs spécifiques aux bureaux
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES AUX BUREAUX ==========

TYPES_BUREAUX = [
    'open space', 'openspace', 'open-space', 'plateau',
    'bureau', 'bureaux', 'cabinet', 'espace de travail',
    'immeuble de bureaux', 'tour de bureaux', 'centre d\'affaires',
    'espace professionnel', 'local professionnel'
]

EQUIPEMENTS_BUREAUX = [
    'ascenseur', 'ascenseur panoramique', 'monte-charge',
    'accueil', 'réception', 'hall d\'accueil',
    'salle de réunion', 'salle de conférence', 'espace de réunion',
    'kitchenette', 'cafétéria', 'cantine', 'espace détente',
    'sanitaires', 'wc', 'toilettes', 'bloc sanitaire',
    'parking', 'parking sous-sol', 'parking extérieur', 'garage',
    'cellier', 'dépôt', 'archives', 'espace de stockage',
    'climatisation', 'climatisation centrale', 'climatisation réversible',
    'chauffage central', 'chauffage individuel',
    'sécurité', 'gardien', 'badge', 'contrôle d\'accès', 'caméras', 'alarme',
    'fibre optique', 'data center', 'réseau', 'câblage',
    'faux plafond', 'éclairage', 'spots',
    'moquette', 'parquet', 'marbre', 'carrelage',
    'double vitrage', 'porte blindée', 'interphone',
    'vue sur lac', 'vue panoramique', 'vue dégagée',
    'terrasse', 'balcon', 'jardin',
    'accès indépendant', 'entrée privative', 'vitrine',
    'alarme incendie', 'sprinklers', 'extincteurs', 'issues de secours',
    'accessibilité pmr', 'handicapés', 'personnes à mobilité réduite'
]

PROXIMITES_BUREAUX = [
    'transports', 'métro', 'bus', 'station', 'autoroute',
    'banques', 'assurances', 'administrations', 'ambassades',
    'commerces', 'restaurants', 'hôtels', 'parking public',
    'pharmacie', 'polyclinique', 'hôpital', 'mosquée'
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
        (r'(\d+)\s*dt\s*ht', 1),  # Loyer HT
    ]
    
    for pattern, group in loyer_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                loyer_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(loyer_str)
                if 100 <= val <= 500000:
                    result['loyer'] = val
                    
                    # Détecter si c'est HT
                    if 'ht' in pattern or 'ht' in text_lower:
                        result['loyer_ht'] = True
                    break
            except:
                continue
    
    return result


def extract_type_bureau_from_text(text: str) -> Optional[str]:
    """Extrait le type de bureau"""
    text_lower = text.lower()
    
    for type_bureau in TYPES_BUREAUX:
        if type_bureau in text_lower:
            return type_bureau.title()
    
    return None


def extract_nombre_bureaux_from_text(text: str) -> Optional[int]:
    """Extrait le nombre de bureaux individuels"""
    patterns = [
        r'(\d+)\s*bureaux?',
        r'(\d+)\s*pi[èe]ces?',
        r'(\d+)\s*bureaux?\s*ind[ée]pendants?',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_est_open_space(text: str) -> bool:
    """Détecte si c'est un open space"""
    text_lower = text.lower()
    keywords = ['open space', 'openspace', 'open-space', 'plateau']
    return any(keyword in text_lower for keyword in keywords)


def extract_est_immeuble_entier(text: str) -> bool:
    """Détecte si c'est un immeuble entier"""
    text_lower = text.lower()
    keywords = ['immeuble', 'tour', 'building', 'ensemble']
    return any(keyword in text_lower for keyword in keywords)


def extract_nombre_etages(text: str) -> Optional[int]:
    """Extrait le nombre d'étages"""
    patterns = [
        r'(\d+)\s*[ée]tages?',
        r'(\d+)\s*niveaux?',
        r'r\s*\+\s*(\d+)',
        r'sur\s*(\d+)\s*niveaux',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_etage_bureau(text: str) -> Optional[int]:
    """Extrait l'étage du bureau"""
    text_lower = text.lower()
    
    patterns = [
        r'au\s+(\d+)[eè]me?\s*[eé]tage',
        r'(\d+)[eè]me?\s*[eé]tage',
        r'étage\s*[:\-]?\s*(\d+)',
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


def extract_presence_accueil(text: str) -> bool:
    """Détecte la présence d'un espace accueil"""
    text_lower = text.lower()
    keywords = ['accueil', 'réception', 'hall', 'espace d\'accueil']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_salle_reunion(text: str) -> bool:
    """Détecte la présence de salles de réunion"""
    text_lower = text.lower()
    keywords = ['salle de réunion', 'salle de conférence', 'espace de réunion']
    return any(keyword in text_lower for keyword in keywords)


def extract_nombre_salles_reunion(text: str) -> Optional[int]:
    """Extrait le nombre de salles de réunion"""
    patterns = [
        r'(\d+)\s*salles?\s*de\s*r[ée]union',
        r'(\d+)\s*salles?\s*de\s*conf[ée]rence',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_presence_kitchenette(text: str) -> bool:
    """Détecte la présence d'une kitchenette"""
    text_lower = text.lower()
    keywords = ['kitchenette', 'cuisine', 'cafétéria', 'espace repas']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_sanitaires(text: str) -> bool:
    """Détecte la présence de sanitaires"""
    text_lower = text.lower()
    keywords = ['sanitaire', 'wc', 'toilettes', 'bloc sanitaire', 'salle d\'eau']
    return any(keyword in text_lower for keyword in keywords)


def extract_nombre_sanitaires(text: str) -> Optional[int]:
    """Extrait le nombre de blocs sanitaires"""
    patterns = [
        r'(\d+)\s*blocs?\s*sanitaires?',
        r'(\d+)\s*wc',
        r'(\d+)\s*toilettes?',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_sanitaires_separes(text: str) -> bool:
    """Détecte si les sanitaires sont séparés (hommes/femmes)"""
    text_lower = text.lower()
    return 'hommes' in text_lower and 'femmes' in text_lower


def extract_presence_parking(text: str) -> bool:
    """Détecte la présence de parking"""
    text_lower = text.lower()
    keywords = ['parking', 'garage', 'stationnement', 'place de parking']
    return any(keyword in text_lower for keyword in keywords)


def extract_nombre_parking(text: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    patterns = [
        r'(\d+)\s*places?\s*de\s*parking',
        r'(\d+)\s*parking[s]?',
        r'(\d+)\s*places?',
        r'(\d+)\s*voitures?',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_type_parking(text: str) -> Optional[str]:
    """Extrait le type de parking"""
    text_lower = text.lower()
    
    if 'sous-sol' in text_lower:
        return 'Sous-sol'
    elif 'couvert' in text_lower:
        return 'Couvert'
    elif 'extérieur' in text_lower:
        return 'Extérieur'
    
    return None


def extract_presence_stockage(text: str) -> bool:
    """Détecte la présence d'espaces de stockage"""
    text_lower = text.lower()
    keywords = ['cellier', 'dépôt', 'archives', 'stockage', 'rangement']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_fibre(text: str) -> bool:
    """Détecte la présence de fibre optique"""
    text_lower = text.lower()
    keywords = ['fibre', 'fibre optique', 'data center', 'réseau', 'câblage']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_climatisation(text: str) -> bool:
    """Détecte la présence de climatisation"""
    return 'climatisation' in text.lower()


def extract_type_climatisation(text: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    text_lower = text.lower()
    
    if 'climatisation centrale' in text_lower:
        return 'Centrale'
    elif 'climatisation réversible' in text_lower:
        return 'Réversible'
    elif 'climatisation individuelle' in text_lower:
        return 'Individuelle'
    
    return None


def extract_presence_chauffage(text: str) -> bool:
    """Détecte la présence de chauffage"""
    return 'chauffage' in text.lower()


def extract_type_chauffage(text: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    text_lower = text.lower()
    
    if 'chauffage central' in text_lower:
        return 'Central'
    elif 'chauffage individuel' in text_lower:
        return 'Individuel'
    
    return None


def extract_presence_securite(text: str) -> bool:
    """Détecte la présence de sécurité"""
    text_lower = text.lower()
    keywords = ['sécurité', 'gardien', 'badge', 'contrôle d\'accès', 'caméras', 'alarme', 'vidéosurveillance']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_ascenseur(text: str) -> bool:
    """Détecte la présence d'ascenseur"""
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


def extract_presence_ascenseur_panoramique(text: str) -> bool:
    """Détecte la présence d'un ascenseur panoramique"""
    return 'ascenseur panoramique' in text.lower()


def extract_vue(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur lac' in text_lower:
        return 'Lac'
    elif 'vue panoramique' in text_lower:
        return 'Panoramique'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue sur mer' in text_lower:
        return 'Mer'
    
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


def extract_presence_acces_independant(text: str) -> bool:
    """Détecte la présence d'un accès indépendant"""
    text_lower = text.lower()
    keywords = ['accès indépendant', 'entrée indépendante', 'entrée privative']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_moquette(text: str) -> bool:
    """Détecte la présence de moquette"""
    return 'moquette' in text.lower()


def extract_type_sol(text: str) -> Optional[str]:
    """Extrait le type de sol"""
    text_lower = text.lower()
    
    if 'marbre' in text_lower:
        return 'Marbre'
    elif 'parquet' in text_lower:
        return 'Parquet'
    elif 'moquette' in text_lower:
        return 'Moquette'
    elif 'carrelage' in text_lower:
        return 'Carrelage'
    elif 'béton ciré' in text_lower:
        return 'Béton ciré'
    
    return None


def extract_charges_incluses(text: str) -> bool:
    """Détecte si les charges sont incluses"""
    text_lower = text.lower()
    return 'charges incluses' in text_lower or 'charges comprises' in text_lower


def extract_montant_charges(text: str) -> Optional[float]:
    """Extrait le montant des charges"""
    patterns = [
        r'charges\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'(\d+)\s*(?:tnd|dt)\s*de\s*charges',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_disponibilite(text: str) -> Optional[str]:
    """Extrait la date de disponibilité"""
    patterns = [
        r'disponible\s*(?:imm[ée]diatement)?',
        r'libre\s*(?:de suite)?',
        r'disponibilit[ée]\s*[:\-]?\s*([a-zéû]+\s*\d{4})',
        r'libre\s*le\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    ]
    
    text_lower = text.lower()
    
    if 'immédiatement' in text_lower or 'de suite' in text_lower:
        return 'Immédiate'
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.lastindex:
            return m.group(1)
    
    return None


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_BUREAUX:
        if prox in text_lower:
            found_prox.append(prox.title())
    
    return list(set(found_prox))


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
    
    for eq in EQUIPEMENTS_BUREAUX:
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
                'standing': 'standing',
                'état': 'statut_construction',
                'livraison:': 'livraison',
                'années': 'age_bien',
                'étage du bien': 'etage',
                'type du sol': 'type_sol'
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


def extract_from_amenities_bureaux(amenities: Any) -> List[str]:
    """Extrait depuis amenities_bureaux"""
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
        'equipements_list': [],
        'terrasse_surface': None,
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
    Extrait TOUS les champs possibles d'un listing de location de bureaux
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
    
    # Type de bureau
    type_bureau = extract_type_bureau_from_text(all_text)
    if type_bureau:
        extracted['type_bureau_extrait'] = type_bureau
    
    # Nombre de bureaux
    nb_bureaux = extract_nombre_bureaux_from_text(all_text)
    if nb_bureaux:
        extracted['nombre_bureaux_extrait'] = nb_bureaux
    
    # Open space
    extracted['est_open_space'] = extract_est_open_space(all_text)
    
    # Immeuble entier
    extracted['est_immeuble_entier'] = extract_est_immeuble_entier(all_text)
    
    # Nombre d'étages
    nb_etages = extract_nombre_etages(all_text)
    if nb_etages:
        extracted['nombre_etages_immeuble'] = nb_etages
    
    # Étage du bureau
    etage = extract_etage_bureau(all_text)
    if etage is not None:
        extracted['etage_extrait'] = etage
    
    # Accueil
    extracted['a_accueil'] = extract_presence_accueil(all_text)
    
    # Salles de réunion
    extracted['a_salle_reunion'] = extract_presence_salle_reunion(all_text)
    nb_salles_reunion = extract_nombre_salles_reunion(all_text)
    if nb_salles_reunion:
        extracted['nombre_salles_reunion'] = nb_salles_reunion
    
    # Kitchenette
    extracted['a_kitchenette'] = extract_presence_kitchenette(all_text)
    
    # Sanitaires
    extracted['a_sanitaires'] = extract_presence_sanitaires(all_text)
    nb_sanitaires = extract_nombre_sanitaires(all_text)
    if nb_sanitaires:
        extracted['nombre_sanitaires'] = nb_sanitaires
    extracted['sanitaires_separes'] = extract_sanitaires_separes(all_text)
    
    # Parking
    extracted['a_parking'] = extract_presence_parking(all_text)
    nb_parking = extract_nombre_parking(all_text)
    if nb_parking:
        extracted['parking_nombre'] = nb_parking
    parking_type = extract_type_parking(all_text)
    if parking_type:
        extracted['parking_type'] = parking_type
    
    # Stockage
    extracted['a_stockage'] = extract_presence_stockage(all_text)
    
    # Fibre
    extracted['a_fibre'] = extract_presence_fibre(all_text)
    
    # Climatisation
    extracted['a_climatisation'] = extract_presence_climatisation(all_text)
    clim_type = extract_type_climatisation(all_text)
    if clim_type:
        extracted['climatisation_type'] = clim_type
    
    # Chauffage
    extracted['a_chauffage'] = extract_presence_chauffage(all_text)
    chauffage_type = extract_type_chauffage(all_text)
    if chauffage_type:
        extracted['chauffage_type'] = chauffage_type
    
    # Sécurité
    extracted['a_securite'] = extract_presence_securite(all_text)
    
    # Ascenseur
    extracted['a_ascenseur'] = extract_presence_ascenseur(all_text)
    nb_ascenseurs = extract_nombre_ascenseurs(all_text)
    if nb_ascenseurs:
        extracted['nombre_ascenseurs'] = nb_ascenseurs
    extracted['ascenseur_panoramique'] = extract_presence_ascenseur_panoramique(all_text)
    
    # Vue
    vue = extract_vue(all_text)
    if vue:
        extracted['vue'] = vue
    
    # Terrasse
    extracted['a_terrasse'] = extract_presence_terrasse(all_text)
    surface_terrasse = extract_surface_terrasse(all_text)
    if surface_terrasse:
        extracted['surface_terrasse'] = surface_terrasse
    
    # Accès indépendant
    extracted['acces_independant'] = extract_presence_acces_independant(all_text)
    
    # Moquette
    extracted['a_moquette'] = extract_presence_moquette(all_text)
    
    # Type de sol
    type_sol = extract_type_sol(all_text)
    if type_sol:
        extracted['type_sol_extrait'] = type_sol
    
    # Charges
    extracted['charges_incluses'] = extract_charges_incluses(all_text)
    montant_charges = extract_montant_charges(all_text)
    if montant_charges:
        extracted['montant_charges'] = montant_charges
    
    # Disponibilité
    disponibilite = extract_disponibilite(all_text)
    if disponibilite:
        extracted['disponibilite'] = disponibilite
    
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
    
    # Amenities bureaux
    amenities = extract_from_amenities_bureaux(listing.get('amenities_bureaux', []))
    if amenities:
        extracted['amenities_bureaux_list'] = amenities
    
    # Équipements détaillés
    equip_det_info = extract_from_equipements_detaille(listing.get('equipements_detaille'))
    if equip_det_info:
        if equip_det_info.get('equipements_list'):
            extracted['equipements_detaille_list'] = equip_det_info['equipements_list']
        if equip_det_info.get('terrasse_surface'):
            extracted['surface_terrasse_det'] = equip_det_info['terrasse_surface']
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
    Enrichit complètement un listing de location de bureaux
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
    if extracted.get('loyer_ht'):
        enriched['loyer_ht'] = True
    
    # Type de bureau
    if extracted.get('type_bureau_extrait') and not listing.get('type_bureau'):
        enriched['type_bureau'] = extracted['type_bureau_extrait']
    
    # Nombre de bureaux
    if extracted.get('nombre_bureaux_extrait') and not listing.get('nombre_bureaux'):
        enriched['nombre_bureaux'] = extracted['nombre_bureaux_extrait']
    
    # Caractéristiques booléennes
    bool_fields = [
        'est_open_space', 'est_immeuble_entier', 'a_accueil', 'a_salle_reunion',
        'a_kitchenette', 'a_sanitaires', 'sanitaires_separes', 'a_parking',
        'a_stockage', 'a_fibre', 'a_climatisation', 'a_chauffage', 'a_securite',
        'a_ascenseur', 'ascenseur_panoramique', 'a_terrasse', 'acces_independant',
        'a_moquette', 'charges_incluses'
    ]
    for field in bool_fields:
        if extracted.get(field) is not None:
            enriched[field] = extracted[field]
    
    # Nombres
    numeric_fields = [
        'nombre_salles_reunion', 'nombre_sanitaires', 'parking_nombre',
        'nombre_ascenseurs', 'nombre_etages_immeuble', 'surface_terrasse',
        'montant_charges'
    ]
    for field in numeric_fields:
        if extracted.get(field):
            enriched[field] = extracted[field]
    
    # Types
    type_fields = ['parking_type', 'climatisation_type', 'chauffage_type', 'type_sol_extrait', 'vue']
    for field in type_fields:
        if extracted.get(field) and not listing.get(field):
            enriched[field] = extracted[field]
    
    # Disponibilité
    if extracted.get('disponibilite'):
        enriched['disponibilite'] = extracted['disponibilite']
    
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
                                extracted.get('amenities_bureaux_list', []) +
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
        'types_bureau_extraits': 0,
        'nombres_bureaux_extraits': 0,
        'parkings_detectes': 0,
        'ascenseurs_detectes': 0,
        'salles_reunion_detectees': 0,
        'kitchenettes_detectees': 0,
        'fibres_detectees': 0,
        'climatisations_detectees': 0,
        'securite_detectee': 0,
        'charges_detectees': 0,
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
            if enriched.get('type_bureau') and not listing.get('type_bureau'):
                stats['types_bureau_extraits'] += 1
            if enriched.get('nombre_bureaux') and not listing.get('nombre_bureaux'):
                stats['nombres_bureaux_extraits'] += 1
            if enriched.get('a_parking'):
                stats['parkings_detectes'] += 1
            if enriched.get('a_ascenseur'):
                stats['ascenseurs_detectes'] += 1
            if enriched.get('a_salle_reunion'):
                stats['salles_reunion_detectees'] += 1
            if enriched.get('a_kitchenette'):
                stats['kitchenettes_detectees'] += 1
            if enriched.get('a_fibre'):
                stats['fibres_detectees'] += 1
            if enriched.get('a_climatisation'):
                stats['climatisations_detectees'] += 1
            if enriched.get('a_securite'):
                stats['securite_detectee'] += 1
            if enriched.get('charges_incluses') or enriched.get('montant_charges'):
                stats['charges_detectees'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - LOCATION DE BUREAUX")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Loyers extraits/améliorés: {stats['loyers_extraits']}")
    print(f"✅ Types de bureau extraits: {stats['types_bureau_extraits']}")
    print(f"✅ Nombres de bureaux extraits: {stats['nombres_bureaux_extraits']}")
    print(f"✅ Parkings détectés: {stats['parkings_detectes']}")
    print(f"✅ Ascenseurs détectés: {stats['ascenseurs_detectes']}")
    print(f"✅ Salles de réunion détectées: {stats['salles_reunion_detectees']}")
    print(f"✅ Kitchenettes détectées: {stats['kitchenettes_detectees']}")
    print(f"✅ Fibre optique détectée: {stats['fibres_detectees']}")
    print(f"✅ Climatisations détectées: {stats['climatisations_detectees']}")
    print(f"✅ Sécurité détectée: {stats['securite_detectee']}")
    print(f"✅ Charges détectées: {stats['charges_detectees']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Location de Bureaux")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()