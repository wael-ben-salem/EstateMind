"""
Agent d'extraction pour Vente de Villas de Luxe
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
    'villa', 'villa moderne', 'villa classique', 'villa contemporaine',
    'villa traditionnelle', 'villa vue mer', 'villa de luxe',
    'villa de standing', 'villa avec piscine', 'villa indépendante',
    'villa jumelée', 'villa mitoyenne', 'maison de maître'
]

STYLES_ARCHITECTURAUX = [
    'moderne', 'classique', 'contemporain', 'traditionnel',
    'méditerranéen', 'andin', 'mauresque', 'arabo-andalou'
]

EQUIPEMENTS_LUXE = [
    'piscine', 'piscine chauffée', 'piscine couverte', 'spa', 'hammam',
    'jacuzzi', 'sauna', 'salle de sport', 'home cinéma', 'cinéma maison',
    'cave à vin', 'bibliothèque', 'bureau', 'atelier', 'véranda',
    'pergola', 'barbecue', 'plancha', 'cuisine d\'été', 'terrasse couverte',
    'jardin paysager', 'jardin exotique', 'potager', 'verger',
    'fontaine', 'bassin', 'éclairage paysager', 'arrosage automatique',
    'alarme', 'caméras', 'vidéosurveillance', 'gardien', 'clôture électrique',
    'portail automatique', 'visiophone', 'interphone', 'détecteur de mouvement',
    'panneaux solaires', 'panneaux photovoltaïques', 'chauffe-eau solaire',
    'puits', 'citerne', 'récupération eau de pluie', 'adoucisseur d\'eau',
    'chauffage central', 'chauffage au sol', 'plancher chauffant',
    'climatisation centrale', 'climatisation réversible', 'VMC',
    'double vitrage', 'porte blindée', 'volet roulant électrique',
    'store automatique', 'domotique', 'maison intelligente',
    'ascenseur privatif', 'monte-charge', 'garage', 'parking couvert',
    'carport', 'abri de voiture', 'borne de recharge électrique'
]

MATERIAUX_NOBLES = [
    'marbre', 'parquet', 'parquet massif', 'pierre naturelle',
    'granit', 'travertin', 'zellige', 'carreau ciment',
    'bois exotique', 'teck', 'ipé', 'mosaïque'
]

PROXIMITES_VILLA = [
    'mer', 'plage', 'commerces', 'écoles', 'collège', 'lycée',
    'hôpital', 'clinique', 'pharmacie', 'supermarché', 'centre commercial',
    'restaurants', 'cafés', 'golf', 'tennis', 'ports de plaisance',
    'marina', 'aéroport', 'autoroute', 'transports en commun'
]

REGIONS_MAPPING = {
    "tunis": "Tunis", "la marsa": "Tunis", "carthage": "Tunis", "le kram": "Tunis",
    "ariana": "Ariana", "ennasr": "Ariana", "manzah": "Ariana", "soukra": "Ariana", "raoued": "Ariana",
    "ben arous": "Ben Arous", "boumhel": "Ben Arous", "mohammedia": "Ben Arous",
    "nabeul": "Nabeul", "hammamet": "Nabeul", "kélibia": "Nabeul",
    "sousse": "Sousse", "hammam sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte", "djerba": "Médenine"
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


def extract_prix_from_text(text: str) -> Dict[str, Any]:
    """Extraction du prix"""
    result = {}
    text_lower = text.lower()
    
    if any(phrase in text_lower for phrase in ['prix à consulter', 'prix sur demande', 'nous consulter']):
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        return result
    
    # Prix total (MDT = millions dinars)
    prix_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 1),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)', 1),
        (r'(\d+)\s*tnd', 1),
        (r'(\d+)\s*dt\b', 1),
        (r'(\d+\.?\d*)\s*mdt', 1),  # millions de dinars
    ]
    
    for pattern, group in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                # Conversion de MDT à TND si nécessaire
                if 'mdt' in pattern or ('m' in text_lower and 'dt' in text_lower and val < 1000):
                    val = val * 1000000
                if 50000 <= val <= 50000000:
                    result['prix'] = val
                    break
            except:
                continue
    
    return result


def extract_surface_habitable(text: str) -> Optional[float]:
    """Extrait la surface habitable"""
    patterns = [
        r'surface\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m[²2]',
        r'(\d+)\s*m[²2]\s*(?:habitable)?',
        r'superficie\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+couverte\s*[:\-]?\s*(\d+)\s*m²',
        r'(\d+)\s*m²\s+habitables?',
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


def extract_type_villa(text: str) -> Optional[str]:
    """Extrait le type de villa"""
    text_lower = text.lower()
    
    for type_villa in TYPES_VILLAS:
        if type_villa in text_lower:
            return type_villa.title()
    
    return None


def extract_style_architectural(text: str) -> Optional[str]:
    """Extrait le style architectural"""
    text_lower = text.lower()
    
    for style in STYLES_ARCHITECTURAUX:
        if style in text_lower:
            return style.title()
    
    return None


def extract_nombre_etages(text: str) -> Optional[int]:
    """Extrait le nombre d'étages"""
    patterns = [
        r'(\d+)\s*étages?',
        r'(\d+)\s*niveaux?',
        r'r\s*\+\s*(\d+)',
        r'rez-de-chaussée\s*et\s*(\d+)\s*étages?',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            try:
                return int(m.group(1)) + 1  # R+1 = 2 niveaux
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


def extract_type_piscine(text: str) -> Optional[str]:
    """Extrait le type de piscine"""
    text_lower = text.lower()
    
    if 'piscine chauffée' in text_lower:
        return 'Chauffée'
    elif 'piscine couverte' in text_lower:
        return 'Couverte'
    elif 'piscine intérieure' in text_lower:
        return 'Intérieure'
    elif 'piscine extérieure' in text_lower:
        return 'Extérieure'
    elif 'piscine à débordement' in text_lower:
        return 'À débordement'
    
    return 'Standard'


def extract_presence_spa(text: str) -> bool:
    """Détecte la présence d'un spa"""
    return 'spa' in text.lower()


def extract_presence_hammam(text: str) -> bool:
    """Détecte la présence d'un hammam"""
    return 'hammam' in text.lower()


def extract_presence_jardin(text: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in text.lower()


def extract_surface_jardin(text: str) -> Optional[float]:
    """Extrait la surface du jardin"""
    patterns = [
        r'jardin\s+de\s*(\d+)\s*m[²2]',
        r'jardin\s+(\d+)\s*m²',
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
    
    if 'arbres fruitiers' in text_lower:
        return 'Avec arbres fruitiers'
    elif 'jardin paysager' in text_lower:
        return 'Paysager'
    elif 'jardin exotique' in text_lower:
        return 'Exotique'
    elif 'jardin méditerranéen' in text_lower:
        return 'Méditerranéen'
    elif 'potager' in text_lower:
        return 'Potager'
    
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
        r'abri\s+(\d+)\s*voitures?',
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


def extract_nombre_suites(text: str) -> Optional[int]:
    """Extrait le nombre de suites"""
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


def extract_vue(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower:
        return 'Mer'
    elif 'vue mer' in text_lower:
        return 'Mer'
    elif 'vue sur la mer' in text_lower:
        return 'Mer'
    elif 'vue panoramique' in text_lower:
        return 'Panoramique'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue sur montagne' in text_lower:
        return 'Montagne'
    elif 'vue sur jardin' in text_lower:
        return 'Jardin'
    elif 'vue sur piscine' in text_lower:
        return 'Piscine'
    
    return None


def extract_proximite_plage(text: str) -> Optional[str]:
    """Extrait la distance à la plage"""
    patterns = [
        r'(\d+)\s*minutes?\s*(?:à pied)?\s*de\s*la\s*plage',
        r'(\d+)\s*m\s*de\s*la\s*plage',
        r'proche\s*de\s*la\s*plage',
    ]
    
    text_lower = text.lower()
    
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


def extract_presence_cheminée(text: str) -> bool:
    """Détecte la présence d'une cheminée"""
    return 'cheminée' in text.lower() or 'cheminee' in text.lower()


def extract_presence_home_cinema(text: str) -> bool:
    """Détecte la présence d'un home cinéma"""
    text_lower = text.lower()
    return 'home cinéma' in text_lower or 'cinéma' in text_lower


def extract_presence_cave_vin(text: str) -> bool:
    """Détecte la présence d'une cave à vin"""
    text_lower = text.lower()
    return 'cave à vin' in text_lower or 'cave a vin' in text_lower


def extract_presence_bureau(text: str) -> bool:
    """Détecte la présence d'un bureau"""
    return 'bureau' in text.lower()


def extract_presence_dressing(text: str) -> bool:
    """Détecte la présence de dressing"""
    return 'dressing' in text.lower()


def extract_presence_buanderie(text: str) -> bool:
    """Détecte la présence d'une buanderie"""
    text_lower = text.lower()
    return 'buanderie' in text_lower or 'lingerie' in text_lower


def extract_presence_cellier(text: str) -> bool:
    """Détecte la présence d'un cellier"""
    return 'cellier' in text.lower() or 'débarras' in text.lower()


def extract_chauffage_type(text: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    text_lower = text.lower()
    
    if 'chauffage central' in text_lower:
        return 'Central'
    elif 'chauffage au sol' in text_lower:
        return 'Au sol'
    elif 'plancher chauffant' in text_lower:
        return 'Plancher chauffant'
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


def extract_presence_alarme(text: str) -> bool:
    """Détecte la présence d'une alarme/sécurité"""
    text_lower = text.lower()
    keywords = ['alarme', 'sécurité', 'caméras', 'vidéosurveillance', 'gardien']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_panneaux_solaires(text: str) -> bool:
    """Détecte la présence de panneaux solaires"""
    text_lower = text.lower()
    keywords = ['panneaux solaires', 'photovoltaïque', 'chauffe-eau solaire']
    return any(keyword in text_lower for keyword in keywords)


def extract_annee_construction(text: str) -> Optional[int]:
    """Extrait l'année de construction"""
    patterns = [
        r'construit[e]?\s+en\s+(\d{4})',
        r'construction\s+(\d{4})',
        r'(\d{4})\s*construction',
        r'construite\s+en\s+(\d{4})',
        r'neuve\s+(\d{4})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_etat_villa(text: str) -> Optional[str]:
    """Extrait l'état de la villa"""
    text_lower = text.lower()
    
    if 'project neuf' in text_lower:
        return 'Projet neuf'
    elif 'neuf' in text_lower:
        return 'Neuf'
    elif 'jamais habité' in text_lower:
        return 'Jamais habité'
    elif 'bon état' in text_lower:
        return 'Bon état'
    elif 'très bon état' in text_lower:
        return 'Très bon état'
    elif 'excellent état' in text_lower:
        return 'Excellent état'
    elif 'à rénover' in text_lower:
        return 'À rénover'
    elif 'rénové' in text_lower:
        return 'Rénové'
    
    return None


def extract_materiaux(text: str) -> List[str]:
    """Extrait les matériaux nobles mentionnés"""
    found_materiaux = []
    text_lower = text.lower()
    
    for materiau in MATERIAUX_NOBLES:
        if materiau in text_lower:
            found_materiaux.append(materiau.title())
    
    return list(set(found_materiaux))


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_VILLA:
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
                'nombre d\'étages': 'nombre_etages',
                'surface de la parcelle': 'surface_terrain_carac',
                'orientation': 'orientation'
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


def extract_from_amenities_detaille(amenities_det: Any) -> Dict[str, Any]:
    """Extrait depuis amenities_detaille (string avec ;)"""
    result = {
        'amenities_list': [],
        'jardin_surface': None,
        'terrasse_surface': None,
        'garage_nombre': None,
        'piscine': False,
        'hammam': False
    }
    
    if not amenities_det:
        return result
    
    if isinstance(amenities_det, str):
        items = [item.strip() for item in amenities_det.split(';') if item.strip()]
    elif isinstance(amenities_det, list):
        items = amenities_det
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
            result['amenities_list'].append('Jardin')
        elif 'terrasse' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['terrasse_surface'] = surface
            result['amenities_list'].append('Terrasse')
        elif 'garage' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['garage_nombre'] = int(nombre)
            result['amenities_list'].append('Garage')
        elif 'piscine' in item_lower:
            result['piscine'] = True
            result['amenities_list'].append('Piscine')
        elif 'hammam' in item_lower:
            result['hammam'] = True
            result['amenities_list'].append('Hammam')
        else:
            result['amenities_list'].append(item.title())
    
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
                    if 'nombre_photos' in key_clean:
                        num = extract_number_from_text(value)
                        if num:
                            result['nombre_photos'] = int(num)
                    elif value.lower() in ['oui', 'yes', 'true', 'disponible']:
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
    Extrait TOUS les champs possibles d'un listing de villa
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
    surface_hab = extract_surface_habitable(all_text)
    if surface_hab:
        extracted['surface_habitable'] = surface_hab
    
    surface_terrain = extract_surface_terrain(all_text)
    if surface_terrain:
        extracted['surface_terrain_extrait'] = surface_terrain
    
    # Type et style
    type_villa = extract_type_villa(all_text)
    if type_villa:
        extracted['type_villa_extrait'] = type_villa
    
    style = extract_style_architectural(all_text)
    if style:
        extracted['style_architectural_extrait'] = style
    
    # Nombre d'étages
    nb_etages = extract_nombre_etages(all_text)
    if nb_etages:
        extracted['nombre_etages'] = nb_etages
    
    # Piscine
    extracted['a_piscine'] = extract_presence_piscine(all_text)
    surface_piscine = extract_surface_piscine(all_text)
    if surface_piscine:
        extracted['surface_piscine'] = surface_piscine
    type_piscine = extract_type_piscine(all_text)
    if type_piscine:
        extracted['type_piscine'] = type_piscine
    
    # Spa et Hammam
    extracted['a_spa'] = extract_presence_spa(all_text)
    extracted['a_hammam'] = extract_presence_hammam(all_text)
    
    # Jardin
    extracted['a_jardin'] = extract_presence_jardin(all_text)
    surface_jardin = extract_surface_jardin(all_text)
    if surface_jardin:
        extracted['surface_jardin'] = surface_jardin
    type_jardin = extract_type_jardin(all_text)
    if type_jardin:
        extracted['type_jardin'] = type_jardin
    
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
    
    # Suites
    nb_suites = extract_nombre_suites(all_text)
    if nb_suites:
        extracted['nombre_suites'] = nb_suites
    
    # Vue
    vue = extract_vue(all_text)
    if vue:
        extracted['vue'] = vue
    
    # Proximité plage
    prox_plage = extract_proximite_plage(all_text)
    if prox_plage:
        extracted['proximite_plage'] = prox_plage
    
    # Équipements luxe
    extracted['a_cheminee'] = extract_presence_cheminée(all_text)
    extracted['a_home_cinema'] = extract_presence_home_cinema(all_text)
    extracted['a_cave_vin'] = extract_presence_cave_vin(all_text)
    extracted['a_bureau'] = extract_presence_bureau(all_text)
    extracted['a_dressing'] = extract_presence_dressing(all_text)
    extracted['a_buanderie'] = extract_presence_buanderie(all_text)
    extracted['a_cellier'] = extract_presence_cellier(all_text)
    
    # Chauffage et climatisation
    chauffage = extract_chauffage_type(all_text)
    if chauffage:
        extracted['chauffage_type'] = chauffage
    
    clim = extract_climatisation_type(all_text)
    if clim:
        extracted['climatisation_type'] = clim
    
    # Sécurité
    extracted['a_alarme'] = extract_presence_alarme(all_text)
    
    # Panneaux solaires
    extracted['a_panneaux_solaires'] = extract_presence_panneaux_solaires(all_text)
    
    # Année construction
    annee = extract_annee_construction(all_text)
    if annee:
        extracted['annee_construction'] = annee
    
    # État
    etat = extract_etat_villa(all_text)
    if etat:
        extracted['etat_villa'] = etat
    
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
    
    # ===== 3. EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS =====
    
    # Caracteristiques
    caracs_info = extract_from_caracteristiques(listing.get('caracteristiques'))
    if caracs_info:
        extracted.update({f"caracs_{k}": v for k, v in caracs_info.items()})
    
    # Amenities détaillées
    amenities_info = extract_from_amenities_detaille(listing.get('amenities_detaille'))
    if amenities_info:
        if amenities_info.get('amenities_list'):
            extracted['amenities_detaille_list'] = amenities_info['amenities_list']
        if amenities_info.get('jardin_surface'):
            extracted['surface_jardin_det'] = amenities_info['jardin_surface']
        if amenities_info.get('terrasse_surface'):
            extracted['surface_terrasse_det'] = amenities_info['terrasse_surface']
        if amenities_info.get('garage_nombre'):
            extracted['garage_nombre_det'] = amenities_info['garage_nombre']
        if amenities_info.get('piscine'):
            extracted['a_piscine_det'] = amenities_info['piscine']
        if amenities_info.get('hammam'):
            extracted['a_hammam_det'] = amenities_info['hammam']
    
    # Informations supplémentaires
    info_supp = extract_from_informations_supplementaires(listing.get('informations_supplementaires'))
    if info_supp:
        extracted['infos_supp_parse'] = info_supp
    
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
    Enrichit complètement un listing de villa
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
    
    if extracted.get('surface_terrain_extrait') and not listing.get('surface_terrain'):
        enriched['surface_terrain'] = extracted['surface_terrain_extrait']
    
    # Type et style
    if extracted.get('type_villa_extrait') and not listing.get('type_villa'):
        enriched['type_villa'] = extracted['type_villa_extrait']
    
    if extracted.get('style_architectural_extrait') and not listing.get('style_architectural'):
        enriched['style_architectural'] = extracted['style_architectural_extrait']
    
    # Nombre d'étages
    if extracted.get('nombre_etages') and not listing.get('nombre_etages'):
        enriched['nombre_etages'] = extracted['nombre_etages']
    
    # Piscine
    if extracted.get('a_piscine') is not None:
        enriched['a_piscine'] = extracted['a_piscine']
    if extracted.get('surface_piscine'):
        enriched['surface_piscine'] = extracted['surface_piscine']
    if extracted.get('type_piscine'):
        enriched['type_piscine'] = extracted['type_piscine']
    
    # Spa et Hammam
    if extracted.get('a_spa') is not None:
        enriched['a_spa'] = extracted['a_spa']
    if extracted.get('a_hammam') is not None or extracted.get('a_hammam_det') is not None:
        enriched['a_hammam'] = extracted.get('a_hammam') or extracted.get('a_hammam_det')
    
    # Jardin
    if extracted.get('a_jardin') is not None:
        enriched['a_jardin'] = extracted['a_jardin']
    if extracted.get('surface_jardin') or extracted.get('surface_jardin_det'):
        enriched['surface_jardin'] = extracted.get('surface_jardin') or extracted.get('surface_jardin_det')
    if extracted.get('type_jardin'):
        enriched['type_jardin'] = extracted['type_jardin']
    
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
    
    # Suites
    if extracted.get('nombre_suites') and not listing.get('nombre_suites'):
        enriched['nombre_suites'] = extracted['nombre_suites']
    
    # Vue
    if extracted.get('vue') and not listing.get('vue'):
        enriched['vue'] = extracted['vue']
    
    # Proximité plage
    if extracted.get('proximite_plage'):
        enriched['proximite_plage'] = extracted['proximite_plage']
    
    # Équipements luxe
    bool_fields = ['a_cheminee', 'a_home_cinema', 'a_cave_vin', 'a_bureau',
                   'a_dressing', 'a_buanderie', 'a_cellier', 'a_alarme',
                   'a_panneaux_solaires']
    for field in bool_fields:
        if extracted.get(field) is not None:
            enriched[field] = extracted[field]
    
    # Chauffage et climatisation
    if extracted.get('chauffage_type') and not listing.get('chauffage_type'):
        enriched['chauffage_type'] = extracted['chauffage_type']
    if extracted.get('climatisation_type') and not listing.get('climatisation_type'):
        enriched['climatisation_type'] = extracted['climatisation_type']
    
    # Année construction
    if extracted.get('annee_construction') and not listing.get('annee_construction'):
        enriched['annee_construction'] = extracted['annee_construction']
    
    # État
    if extracted.get('etat_villa') and not listing.get('etat_bien'):
        enriched['etat_bien'] = extracted['etat_villa']
    
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
                                extracted.get('amenities_detaille_list', [])))
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
        'piscines_detectees': 0,
        'spas_detectes': 0,
        'hammams_detectes': 0,
        'jardins_detectes': 0,
        'terrasses_detectees': 0,
        'garages_detectes': 0,
        'vues_mer_detectees': 0,
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
            if enriched.get('a_piscine'):
                stats['piscines_detectees'] += 1
            if enriched.get('a_spa'):
                stats['spas_detectes'] += 1
            if enriched.get('a_hammam'):
                stats['hammams_detectes'] += 1
            if enriched.get('a_jardin'):
                stats['jardins_detectes'] += 1
            if enriched.get('a_terrasse'):
                stats['terrasses_detectees'] += 1
            if enriched.get('a_garage'):
                stats['garages_detectes'] += 1
            if enriched.get('vue') == 'Mer':
                stats['vues_mer_detectees'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - VENTE DE VILLAS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Surfaces habitables extraites: {stats['surfaces_hab_extraites']}")
    print(f"✅ Surfaces terrain extraites: {stats['surfaces_terrain_extraites']}")
    print(f"✅ Piscines détectées: {stats['piscines_detectees']}")
    print(f"✅ Spas détectés: {stats['spas_detectes']}")
    print(f"✅ Hammams détectés: {stats['hammams_detectes']}")
    print(f"✅ Jardins détectés: {stats['jardins_detectes']}")
    print(f"✅ Terrasses détectées: {stats['terrasses_detectees']}")
    print(f"✅ Garages détectés: {stats['garages_detectes']}")
    print(f"✅ Vues mer détectées: {stats['vues_mer_detectees']}")
    print(f"✅ Cheminées détectées: {stats['cheminees_detectees']}")
    print(f"✅ Années construction extraites: {stats['annees_constructions']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Vente de Villas")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()