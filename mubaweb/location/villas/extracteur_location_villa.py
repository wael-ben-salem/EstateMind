"""
Agent d'extraction pour Location de Villas
Extrait TOUS les champs spécifiques aux villas
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES AUX VILLAS ==========

TYPES_VILLAS = [
    'villa', 'villa de luxe', 'villa moderne', 'villa contemporaine',
    'villa classique', 'villa traditionnelle', 'villa vue mer',
    'villa avec piscine', 'villa de standing', 'villa haut standing',
    'villa indépendante', 'villa mitoyenne', 'villa jumelée'
]

EQUIPEMENTS_VILLA = [
    'jardin', 'piscine', 'piscine chauffée', 'piscine couverte',
    'terrasse', 'balcon', 'garage', 'parking', 'parking visiteur',
    'cave', 'cellier', 'buanderie', 'chambre de service',
    'dressing', 'cheminée', 'véranda', 'pergola', 'barbecue',
    'cuisine d\'été', 'plancha', 'spa', 'hammam', 'jacuzzi',
    'ascenseur', 'monte-charge', 'climatisation centrale',
    'climatisation split', 'chauffage central', 'chauffage au sol',
    'double vitrage', 'porte blindée', 'alarme', 'caméras',
    'vidéosurveillance', 'gardien', 'sécurité', 'interphone',
    'visiophone', 'portail automatique', 'portail électrique',
    'arrosage automatique', 'éclairage paysager', 'fontaine',
    'bassin', 'potager', 'verger', 'arbres fruitiers',
    'vue sur mer', 'vue panoramique', 'vue dégagée', 'vue sur lac',
    'proche mer', 'proche plage', 'quartier calme', 'quartier résidentiel',
    'suite parentale', 'dressing', 'placards', 'rangements'
]

PROXIMITES_VILLA = [
    'mer', 'plage', 'commerces', 'écoles', 'collège', 'lycée',
    'crèche', 'jardin d\'enfants', 'supermarché', 'marché',
    'pharmacie', 'hôpital', 'clinique', 'transports', 'bus',
    'autoroute', 'aéroport', 'restaurants', 'hôtels', 'golf',
    'tennis', 'ports de plaisance', 'marina'
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
                if 500 <= val <= 100000:
                    result['loyer'] = val
                    break
            except:
                continue
    
    return result


def extract_type_villa_from_text(text: str) -> Optional[str]:
    """Extrait le type de villa"""
    text_lower = text.lower()
    
    for type_villa in TYPES_VILLAS:
        if type_villa in text_lower:
            return type_villa.title()
    
    return None


def extract_nombre_niveaux(text: str) -> Optional[int]:
    """Extrait le nombre de niveaux"""
    patterns = [
        r'sur\s+(\d+)\s*niveaux',
        r'(\d+)\s*niveaux',
        r'r\s*\+\s*(\d+)',
        r'rez-de-chaussée\s*et\s*(\d+)\s*étages?',
        r'(\d+)\s*étages?',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return int(m.group(1)) + 1
            except:
                pass
    
    return None


def extract_surface_habitable(text: str) -> Optional[float]:
    """Extrait la surface habitable"""
    patterns = [
        r'surface\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m[²2]',
        r'(\d+)\s*m[²2]\s*(?:habitable)?',
        r'superficie\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 50 <= val <= 2000:
                    return val
            except:
                pass
    
    return None


def extract_surface_terrain(text: str) -> Optional[float]:
    """Extrait la surface du terrain"""
    patterns = [
        r'terrain\s+de\s*(\d+)\s*m[²2]',
        r'terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+du\s+terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'parcelle\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
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


def extract_type_jardin(text: str) -> Optional[str]:
    """Extrait le type de jardin"""
    text_lower = text.lower()
    
    if 'gazonné' in text_lower:
        return 'Gazonné'
    elif 'arboré' in text_lower or 'arbres' in text_lower:
        return 'Arboré'
    elif 'paysager' in text_lower:
        return 'Paysager'
    elif 'exotique' in text_lower:
        return 'Exotique'
    elif 'méditerranéen' in text_lower:
        return 'Méditerranéen'
    elif 'fruitiers' in text_lower or 'verger' in text_lower:
        return 'Verger'
    
    return 'Standard'


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
                    return float(m.group(1)) * float(m.group(2))
                else:
                    return float(m.group(1))
            except:
                pass
    
    return None


def extract_type_piscine(text: str) -> Optional[str]:
    """Extrait le type de piscine"""
    text_lower = text.lower()
    
    if 'chauffée' in text_lower:
        return 'Chauffée'
    elif 'couverte' in text_lower:
        return 'Couverte'
    elif 'intérieure' in text_lower:
        return 'Intérieure'
    elif 'extérieure' in text_lower:
        return 'Extérieure'
    elif 'à débordement' in text_lower:
        return 'À débordement'
    
    return 'Standard'


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
        r'(\d+)\s*voitures?',
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


def extract_presence_parking(text: str) -> bool:
    """Détecte la présence de parking extérieur"""
    return 'parking' in text.lower() and 'garage' not in text.lower()


def extract_nombre_parking(text: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    patterns = [
        r'(\d+)\s*places?\s*de\s*parking',
        r'(\d+)\s*parking[s]?',
        r'(\d+)\s*voitures?',
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


def extract_presence_chambre_service(text: str) -> bool:
    """Détecte la présence d'une chambre de service"""
    return 'chambre de service' in text.lower()


def extract_nombre_suites(text: str) -> Optional[int]:
    """Extrait le nombre de suites parentales"""
    patterns = [
        r'(\d+)\s*suite[s]?\s*parentale[s]?',
        r'(\d+)\s*suite[s]?',
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


def extract_presence_dressing(text: str) -> bool:
    """Détecte la présence de dressing"""
    return 'dressing' in text.lower()


def extract_presence_cheminee(text: str) -> bool:
    """Détecte la présence d'une cheminée"""
    return 'cheminée' in text.lower() or 'cheminee' in text.lower()


def extract_presence_ascenseur(text: str) -> bool:
    """Détecte la présence d'un ascenseur"""
    return 'ascenseur' in text.lower()


def extract_vue(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower:
        return 'Mer'
    elif 'vue mer' in text_lower:
        return 'Mer'
    elif 'vue panoramique' in text_lower:
        return 'Panoramique'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue sur lac' in text_lower:
        return 'Lac'
    elif 'vue sur jardin' in text_lower:
        return 'Jardin'
    elif 'vue sur piscine' in text_lower:
        return 'Piscine'
    
    return None


def extract_proximite_mer(text: str) -> Optional[str]:
    """Extrait la distance à la mer"""
    patterns = [
        r'(\d+)\s*minutes?\s*(?:à pied)?\s*de\s*la\s*mer',
        r'(\d+)\s*m\s*de\s*la\s*mer',
        r'proche\s*de\s*la\s*mer',
        r'front\s*de\s*mer',
    ]
    
    text_lower = text.lower()
    
    if 'front de mer' in text_lower:
        return 'Front de mer'
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                if m.lastindex:
                    return f"{m.group(1)} min"
                else:
                    return 'Proche'
            except:
                return 'Proche'
    
    return None


def extract_presence_climatisation(text: str) -> bool:
    """Détecte la présence de climatisation"""
    return 'climatisation' in text.lower()


def extract_type_climatisation(text: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    text_lower = text.lower()
    
    if 'climatisation centrale' in text_lower:
        return 'Centrale'
    elif 'climatisation split' in text_lower:
        return 'Split'
    elif 'climatisation réversible' in text_lower:
        return 'Réversible'
    
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
    elif 'chauffage au sol' in text_lower:
        return 'Au sol'
    
    return None


def extract_presence_securite(text: str) -> bool:
    """Détecte la présence de sécurité"""
    text_lower = text.lower()
    keywords = ['sécurité', 'alarme', 'caméras', 'vidéosurveillance', 'gardien', 'surveillance']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_spa(text: str) -> bool:
    """Détecte la présence d'un spa"""
    return 'spa' in text.lower()


def extract_presence_hammam(text: str) -> bool:
    """Détecte la présence d'un hammam"""
    return 'hammam' in text.lower()


def extract_presence_jacuzzi(text: str) -> bool:
    """Détecte la présence d'un jacuzzi"""
    return 'jacuzzi' in text.lower()


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


def extract_meuble(text: str) -> bool:
    """Détecte si la villa est meublée"""
    text_lower = text.lower()
    
    if 'meublé' in text_lower and 'non meublé' not in text_lower:
        return True
    elif 'vide' in text_lower:
        return False
    
    return False


def extract_duree_location(text: str) -> Optional[str]:
    """Extrait la durée de location"""
    text_lower = text.lower()
    
    patterns = [
        r'location\s*(\d+)\s*an',
        r'bail\s*(\d+)\s*an',
        r'minimum\s*(\d+)\s*mois',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return f"{m.group(1)} ans" if 'an' in pattern else f"{m.group(1)} mois"
            except:
                pass
    
    if 'long terme' in text_lower:
        return 'Long terme'
    elif 'courte durée' in text_lower:
        return 'Courte durée'
    
    return None


def extract_disponibilite(text: str) -> Optional[str]:
    """Extrait la date de disponibilité"""
    patterns = [
        r'disponible\s*(?:à partir du)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'libre\s*(?:à partir du)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'disponible\s*(?:imm[ée]diatement)?',
        r'libre\s*(?:de suite)?',
    ]
    
    text_lower = text.lower()
    
    if 'immédiatement' in text_lower or 'de suite' in text_lower:
        return 'Immédiate'
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m and m.lastindex:
            return m.group(1)
    
    return None


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


def extract_materiaux(text: str) -> List[str]:
    """Extrait les matériaux mentionnés"""
    found = []
    text_lower = text.lower()
    
    materiaux = ['marbre', 'parquet', 'carrelage', 'granit', 'pierre', 'bois']
    
    for mat in materiaux:
        if mat in text_lower:
            found.append(mat.title())
    
    return list(set(found))


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_VILLA:
        if prox in text_lower:
            if prox == 'mer':
                found_prox.append('Mer')
            elif prox == 'plage':
                found_prox.append('Plage')
            else:
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
    
    for eq in EQUIPEMENTS_VILLA:
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
                'orientation': 'orientation',
                'type du sol': 'type_sol'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    val = caracs[old_key]
                    result[new_key] = val
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_amenities_villa(amenities: Any) -> List[str]:
    """Extrait depuis amenities_villa"""
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
        'jardin_surface': None,
        'terrasse_surface': None,
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
    
    for item in items:
        if not isinstance(item, str):
            continue
        
        item_lower = item.lower()
        
        if 'jardin' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['jardin_surface'] = surface
            result['equipements_list'].append('Jardin')
        elif 'terrasse' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['terrasse_surface'] = surface
            result['equipements_list'].append('Terrasse')
        elif 'garage' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['garage_nombre'] = int(nombre)
            result['equipements_list'].append('Garage')
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
    Extrait TOUS les champs possibles d'un listing de location de villa
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
    
    # Type de villa
    type_villa = extract_type_villa_from_text(all_text)
    if type_villa:
        extracted['type_villa_extrait'] = type_villa
    
    # Nombre de niveaux
    nb_niveaux = extract_nombre_niveaux(all_text)
    if nb_niveaux:
        extracted['nombre_niveaux'] = nb_niveaux
    
    # Surfaces
    surface_hab = extract_surface_habitable(all_text)
    if surface_hab:
        extracted['surface_habitable'] = surface_hab
    
    surface_terrain = extract_surface_terrain(all_text)
    if surface_terrain:
        extracted['surface_terrain'] = surface_terrain
    
    # Jardin
    extracted['a_jardin'] = extract_presence_jardin(all_text)
    surface_jardin = extract_surface_jardin(all_text)
    if surface_jardin:
        extracted['surface_jardin'] = surface_jardin
    type_jardin = extract_type_jardin(all_text)
    if type_jardin:
        extracted['type_jardin'] = type_jardin
    
    # Piscine
    extracted['a_piscine'] = extract_presence_piscine(all_text)
    surface_piscine = extract_surface_piscine(all_text)
    if surface_piscine:
        extracted['surface_piscine'] = surface_piscine
    type_piscine = extract_type_piscine(all_text)
    if type_piscine:
        extracted['type_piscine'] = type_piscine
    
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
    
    # Parking
    extracted['a_parking'] = extract_presence_parking(all_text)
    nb_parking = extract_nombre_parking(all_text)
    if nb_parking:
        extracted['parking_nombre'] = nb_parking
    
    # Chambre de service
    extracted['a_chambre_service'] = extract_presence_chambre_service(all_text)
    
    # Suites
    nb_suites = extract_nombre_suites(all_text)
    if nb_suites:
        extracted['nombre_suites'] = nb_suites
    
    # Dressing
    extracted['a_dressing'] = extract_presence_dressing(all_text)
    
    # Cheminée
    extracted['a_cheminee'] = extract_presence_cheminee(all_text)
    
    # Ascenseur
    extracted['a_ascenseur'] = extract_presence_ascenseur(all_text)
    
    # Vue
    vue = extract_vue(all_text)
    if vue:
        extracted['vue'] = vue
    
    # Proximité mer
    prox_mer = extract_proximite_mer(all_text)
    if prox_mer:
        extracted['proximite_mer'] = prox_mer
    
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
    
    # Spa, Hammam, Jacuzzi
    extracted['a_spa'] = extract_presence_spa(all_text)
    extracted['a_hammam'] = extract_presence_hammam(all_text)
    extracted['a_jacuzzi'] = extract_presence_jacuzzi(all_text)
    
    # Animaux
    extracted['animaux_acceptes'] = extract_animaux_acceptes(all_text)
    
    # Meublé
    extracted['meuble'] = extract_meuble(all_text)
    
    # Durée location
    duree = extract_duree_location(all_text)
    if duree:
        extracted['duree_location_extrait'] = duree
    
    # Disponibilité
    dispo = extract_disponibilite(all_text)
    if dispo:
        extracted['disponibilite'] = dispo
    
    # Référence
    ref = extract_reference(all_text)
    if ref:
        extracted['reference_extrait'] = ref
    
    # Matériaux
    materiaux = extract_materiaux(all_text)
    if materiaux:
        extracted['materiaux'] = materiaux
    
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
    
    # Amenities villa
    amenities = extract_from_amenities_villa(listing.get('amenities_villa', []))
    if amenities:
        extracted['amenities_villa_list'] = amenities
    
    # Équipements détaillés
    equip_det_info = extract_from_equipements_detaille(listing.get('equipements_detaille'))
    if equip_det_info:
        if equip_det_info.get('equipements_list'):
            extracted['equipements_detaille_list'] = equip_det_info['equipements_list']
        if equip_det_info.get('jardin_surface'):
            extracted['surface_jardin_det'] = equip_det_info['jardin_surface']
        if equip_det_info.get('terrasse_surface'):
            extracted['surface_terrasse_det'] = equip_det_info['terrasse_surface']
        if equip_det_info.get('garage_nombre'):
            extracted['garage_nombre_det'] = equip_det_info['garage_nombre']
    
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
    Enrichit complètement un listing de location de villa
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
    
    # Type de villa
    if extracted.get('type_villa_extrait') and not listing.get('type_villa'):
        enriched['type_villa'] = extracted['type_villa_extrait']
    
    # Nombre de niveaux
    if extracted.get('nombre_niveaux') and not listing.get('niveaux'):
        enriched['niveaux'] = extracted['nombre_niveaux']
    
    # Surfaces
    if extracted.get('surface_habitable') and not listing.get('surface'):
        enriched['surface'] = extracted['surface_habitable']
        enriched['surface_text'] = f"{int(extracted['surface_habitable'])} m²"
    
    if extracted.get('surface_terrain') and not listing.get('surface_terrain'):
        enriched['surface_terrain'] = extracted['surface_terrain']
    
    # Jardin
    if extracted.get('a_jardin') is not None:
        enriched['jardin'] = extracted['a_jardin']
    if extracted.get('surface_jardin') or extracted.get('surface_jardin_det'):
        enriched['surface_jardin'] = extracted.get('surface_jardin') or extracted.get('surface_jardin_det')
    if extracted.get('type_jardin'):
        enriched['type_jardin'] = extracted['type_jardin']
    
    # Piscine
    if extracted.get('a_piscine') is not None:
        enriched['piscine'] = extracted['a_piscine']
    if extracted.get('surface_piscine'):
        enriched['surface_piscine'] = extracted['surface_piscine']
    if extracted.get('type_piscine'):
        enriched['type_piscine'] = extracted['type_piscine']
    
    # Terrasse
    if extracted.get('a_terrasse') is not None:
        enriched['a_terrasse'] = extracted['a_terrasse']
    if extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det'):
        enriched['surface_terrasse'] = extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det')
    
    # Garage
    if extracted.get('a_garage') is not None:
        enriched['garage'] = extracted['a_garage']
    if extracted.get('garage_nombre') or extracted.get('garage_nombre_det'):
        enriched['garage_nombre'] = extracted.get('garage_nombre') or extracted.get('garage_nombre_det')
    
    # Parking
    if extracted.get('a_parking') is not None:
        enriched['parking'] = extracted['a_parking']
    if extracted.get('parking_nombre'):
        enriched['parking_nombre'] = extracted['parking_nombre']
    
    # Chambre de service
    if extracted.get('a_chambre_service') is not None:
        enriched['a_chambre_service'] = extracted['a_chambre_service']
    
    # Suites
    if extracted.get('nombre_suites') and not listing.get('nombre_suites'):
        enriched['nombre_suites'] = extracted['nombre_suites']
    
    # Autres équipements
    bool_fields = ['a_dressing', 'a_cheminee', 'a_ascenseur', 'a_securite',
                   'a_spa', 'a_hammam', 'a_jacuzzi']
    for field in bool_fields:
        if extracted.get(field) is not None:
            enriched[field] = extracted[field]
    
    # Vue
    if extracted.get('vue') and not listing.get('vue'):
        enriched['vue'] = extracted['vue']
    
    # Proximité mer
    if extracted.get('proximite_mer') and not listing.get('proximite_mer'):
        enriched['proximite_mer'] = extracted['proximite_mer']
    
    # Climatisation
    if extracted.get('a_climatisation') is not None:
        enriched['a_climatisation'] = extracted['a_climatisation']
    if extracted.get('climatisation_type') and not listing.get('climatisation_type'):
        enriched['climatisation_type'] = extracted['climatisation_type']
    
    # Chauffage
    if extracted.get('a_chauffage') is not None:
        enriched['a_chauffage'] = extracted['a_chauffage']
    if extracted.get('chauffage_type') and not listing.get('chauffage_type'):
        enriched['chauffage_type'] = extracted['chauffage_type']
    
    # Animaux
    if extracted.get('animaux_acceptes') is not None:
        enriched['animaux_acceptes'] = extracted['animaux_acceptes']
    
    # Meublé
    if extracted.get('meuble') is not None:
        enriched['meuble'] = extracted['meuble']
    
    # Durée location
    if extracted.get('duree_location_extrait') and not listing.get('duree_location'):
        enriched['duree_location'] = extracted['duree_location_extrait']
    
    # Disponibilité
    if extracted.get('disponibilite') and not listing.get('disponibilite'):
        enriched['disponibilite'] = extracted['disponibilite']
    
    # Référence
    if extracted.get('reference_extrait') and not listing.get('reference'):
        enriched['reference'] = extracted['reference_extrait']
    
    # Matériaux
    if extracted.get('materiaux'):
        enriched['materiaux'] = extracted['materiaux']
    
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
                                extracted.get('amenities_villa_list', []) +
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
        'types_villa_extraits': 0,
        'jardins_detectes': 0,
        'piscines_detectees': 0,
        'terrasses_detectees': 0,
        'garages_detectes': 0,
        'vues_mer_detectees': 0,
        'suites_detectees': 0,
        'ascenseurs_detectes': 0,
        'chauffages_detectes': 0,
        'climatisations_detectees': 0,
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
            if enriched.get('type_villa') and not listing.get('type_villa'):
                stats['types_villa_extraits'] += 1
            if enriched.get('jardin'):
                stats['jardins_detectes'] += 1
            if enriched.get('piscine'):
                stats['piscines_detectees'] += 1
            if enriched.get('a_terrasse'):
                stats['terrasses_detectees'] += 1
            if enriched.get('garage'):
                stats['garages_detectes'] += 1
            if enriched.get('vue') == 'Mer':
                stats['vues_mer_detectees'] += 1
            if enriched.get('nombre_suites'):
                stats['suites_detectees'] += 1
            if enriched.get('a_ascenseur'):
                stats['ascenseurs_detectes'] += 1
            if enriched.get('a_chauffage'):
                stats['chauffages_detectes'] += 1
            if enriched.get('a_climatisation'):
                stats['climatisations_detectees'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - LOCATION DE VILLAS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Loyers extraits/améliorés: {stats['loyers_extraits']}")
    print(f"✅ Types de villa extraits: {stats['types_villa_extraits']}")
    print(f"✅ Jardins détectés: {stats['jardins_detectes']}")
    print(f"✅ Piscines détectées: {stats['piscines_detectees']}")
    print(f"✅ Terrasses détectées: {stats['terrasses_detectees']}")
    print(f"✅ Garages détectés: {stats['garages_detectes']}")
    print(f"✅ Vues mer détectées: {stats['vues_mer_detectees']}")
    print(f"✅ Suites détectées: {stats['suites_detectees']}")
    print(f"✅ Ascenseurs détectés: {stats['ascenseurs_detectes']}")
    print(f"✅ Chauffages détectés: {stats['chauffages_detectes']}")
    print(f"✅ Climatisations détectées: {stats['climatisations_detectees']}")
    print(f"✅ Références extraites: {stats['references_extraites']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Location de Villas")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()