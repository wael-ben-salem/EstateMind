"""
Agent d'extraction COMPLET pour Vente d'Appartements
Extrait TOUS les champs possibles depuis:
- description_courte, description_complete
- caracteristiques (JSON)
- equipements_detaille (string avec ;)
- URLs des images
- informations_supplementaires (JSON)
- Et tous les textes des descriptions
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES ==========

EQUIPEMENTS_RECHERCHES = [
    'terrasse', 'jardin', 'garage', 'parking', 'ascenseur', 'concierge',
    'climatisation', 'chauffage', 'chauffage central', 'chauffage au sol',
    'double vitrage', 'porte blindée', 'cuisine équipée', 'cuisine américaine',
    'réfrigérateur', 'four', 'tv', 'machine à laver', 'micro-ondes',
    'internet', 'wifi', 'meublé', 'piscine', 'balcon', 'cellier', 'débarras',
    'dressing', 'chambre de service', 'vue sur mer', 'vue sur lac',
    'vue dégagée', 'sécurité', 'alarme', 'caméras', 'interphone',
    'antenne parabolique', 'fibre optique', 'cheminée', 'spa', 'hammam',
    'salle de sport', 'jacuzzi', 'sauna', 'solarium', 'rooftop'
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

ETAT_MAPPING = {
    "projet neuf": "Projet neuf",
    "project neuf": "Projet neuf",
    "neuf": "Neuf",
    "bon état / habitable": "Bon état",
    "bon etat": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "à rénover": "À rénover",
    "rénové": "Rénové"
}

ORIENTATION_MAPPING = {
    "nord": "Nord",
    "sud": "Sud",
    "est": "Est",
    "ouest": "Ouest",
    "nord-est": "Nord-Est",
    "nord-ouest": "Nord-Ouest",
    "sud-est": "Sud-Est",
    "sud-ouest": "Sud-Ouest"
}

SOL_MAPPING = {
    "marbre": "Marbre",
    "carrelage": "Carrelage",
    "parquet": "Parquet",
    "stratifié": "Stratifié",
    "béton ciré": "Béton ciré",
    "grès": "Grès"
}


# ========== FONCTIONS UTILITAIRES ==========

def normalize_text(text: str) -> str:
    """Normalise le texte (enlève les espaces multiples, nettoie)"""
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


# ========== EXTRACTION DEPUIS LES URLs ==========

def extract_date_from_url(url: str) -> Optional[str]:
    """
    Extrait une date depuis une URL d'image
    Formats: WhatsApp%20Image%20AAAA-MM-JJ, AAAA-MM-JJ dans le chemin
    """
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
    """Extrait un titre amélioré depuis les descriptions"""
    text = f"{description_courte} {description_complete}"
    lines = text.split('.')
    if lines and len(lines[0]) < 150:
        return normalize_text(lines[0])
    return None


def extract_prix_from_text(text: str) -> Dict[str, Any]:
    """Extraction complète des prix depuis le texte"""
    result = {}
    text_lower = text.lower()
    
    # Vérifier si prix à consulter
    if any(phrase in text_lower for phrase in ['prix à consulter', 'prix sur demande', 'nous consulter']):
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        return result
    
    # Patterns de prix TND
    prix_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 1),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)', 1),
        (r'(\d+)\s*tnd', 1),
        (r'(\d+)\s*dt\b', 1),
        (r'(\d[\d\s]+)\s*tnd', 1),
    ]
    
    for pattern, group in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                if 1000 <= val <= 50000000:
                    result['prix'] = val
                    # Vérifier si c'est un prix "à partir de"
                    if 'à partir de' in text_lower or 'a partir de' in text_lower:
                        result['prix_type'] = 'starting_from'
                    break
            except:
                continue
    
    return result


def extract_surface_from_text(text: str) -> Dict[str, Any]:
    """Extraction de la surface depuis le texte"""
    result = {}
    
    surface_patterns = [
        r'(\d+)\s*m[²2]',
        r'(\d+)\s*m[e]?tres? carrés?',
        r'surface\s*[:\-]?\s*(\d+)',
        r'superficie\s*[:\-]?\s*(\d+)',
        r'(\d+)\s*m²',
    ]
    
    for pattern in surface_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                surface_val = float(m.group(1))
                if 20 <= surface_val <= 1000:
                    result['surface'] = surface_val
                    result['surface_text'] = f"{int(surface_val)} m²"
                    break
            except:
                continue
    
    return result


def extract_etage_from_text(text: str) -> Optional[int]:
    """Extrait le numéro d'étage depuis le texte"""
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


def extract_orientation_from_text(text: str) -> Optional[str]:
    """Extrait l'orientation depuis le texte"""
    text_lower = text.lower()
    
    for orientation in ['nord', 'sud', 'est', 'ouest', 'nord-est', 'nord-ouest', 'sud-est', 'sud-ouest']:
        if orientation in text_lower:
            return ORIENTATION_MAPPING.get(orientation, orientation.title())
    
    return None


def extract_type_sol_from_text(text: str) -> Optional[str]:
    """Extrait le type de sol depuis le texte"""
    text_lower = text.lower()
    
    for sol in ['marbre', 'carrelage', 'parquet', 'stratifié', 'béton ciré', 'grès']:
        if sol in text_lower:
            return SOL_MAPPING.get(sol, sol.title())
    
    return None


def extract_nom_residence_from_text(text: str) -> Optional[str]:
    """Extrait le nom de la résidence depuis le texte"""
    patterns = [
        r'r[eé]sidence\s+([A-Z][A-Za-z0-9\s\-]+)',
        r'rés\s+([A-Z][A-Za-z0-9\s\-]+)',
        r'projet\s+([A-Z][A-Za-z0-9\s\-]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()
    
    return None


def extract_nom_agence_from_text(text: str) -> Optional[str]:
    """Extrait le nom de l'agence depuis le texte"""
    patterns = [
        r'agence\s+([A-Z][A-Za-z0-9\s\-&]+)',
        r'proposé par\s+([A-Z][A-Za-z0-9\s\-&]+)',
        r'([A-Z][A-Za-z0-9\s\-&]+)\s+(?:vous propose|met en vente)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None


def extract_telephone_from_text(text: str) -> Optional[str]:
    """Extrait le numéro de téléphone depuis le texte"""
    patterns = [
        r'(?:\+216|00216|216)?\s*(\d[\d\s]{7,})',
        r't[eé]l[eé]phone\s*[:\-]?\s*(\d[\d\s]{7,})',
        r'contact\s*(?:\s*:)?\s*(\d[\d\s]{7,})',
        r'whatsapp[:\s]*(\d[\d\s]{7,})',
        r'(\d{2}\s*\d{3}\s*\d{3})',
        r'(\d{8,})',
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


def extract_email_from_text(text: str) -> Optional[str]:
    """Extrait l'email depuis le texte"""
    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    m = re.search(pattern, text)
    if m:
        return m.group(0)
    return None


def extract_site_web_from_text(text: str) -> Optional[str]:
    """Extrait le site web depuis le texte"""
    patterns = [
        r'www\.[a-zA-Z0-9\.\-]+\.(?:com|tn|fr|net|org)',
        r'https?://[^\s]+',
        r'site web\s*[:\-]?\s*([^\s]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            url = m.group(0) if m.lastindex is None else m.group(1)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    
    return None


def extract_reference_from_text(text: str) -> Optional[str]:
    """Extrait la référence de l'annonce depuis le texte"""
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


def extract_surface_terrasse(text: str) -> Optional[float]:
    """Extrait la surface de la terrasse"""
    patterns = [
        r'terrasse\s+de\s*(\d+)\s*m[²2]',
        r'terrasse\s+(\d+)\s*m²',
        r'terrasse\s+(\d+)\s*m',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_surface_balcon(text: str) -> Optional[float]:
    """Extrait la surface du balcon"""
    patterns = [
        r'balcon\s+de\s*(\d+)\s*m[²2]',
        r'balcon\s+(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_nombre_parking(text: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    patterns = [
        r'(\d+)\s*place[s]?\s*(?:de)?\s*parking',
        r'(\d+)\s*parking[s]?',
        r'deux\s+places\s+de\s+parking',
        r'une\s+place\s+de\s+parking',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            if 'deux' in m.group(0):
                return 2
            elif 'une' in m.group(0):
                return 1
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_chauffage_type(text: str) -> Optional[str]:
    """Extrait le type de chauffage"""
    text_lower = text.lower()
    
    if 'chauffage central' in text_lower:
        return 'Central'
    elif 'chauffage au sol' in text_lower:
        return 'Au sol'
    elif 'chauffage électrique' in text_lower:
        return 'Électrique'
    elif 'chauffage gaz' in text_lower:
        return 'Gaz'
    
    return None


def extract_climatisation_type(text: str) -> Optional[str]:
    """Extrait le type de climatisation"""
    text_lower = text.lower()
    
    if 'climatisation centrale' in text_lower or 'climatisation central' in text_lower:
        return 'Centrale'
    elif 'climatisation split' in text_lower or 'split' in text_lower:
        return 'Split'
    
    return None


def extract_vue_type(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower:
        return 'Mer'
    elif 'vue sur lac' in text_lower:
        return 'Lac'
    elif 'vue sur montagne' in text_lower or 'vue sur les montagnes' in text_lower:
        return 'Montagne'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue imprenable' in text_lower:
        return 'Imprenable'
    
    return None


def extract_presence_dressing(text: str) -> bool:
    """Détecte la présence de dressing"""
    return 'dressing' in text.lower()


def extract_presence_cellier(text: str) -> bool:
    """Détecte la présence de cellier / débarras"""
    text_lower = text.lower()
    return 'cellier' in text_lower or 'débarras' in text_lower


def extract_presence_chambre_service(text: str) -> bool:
    """Détecte la présence de chambre de service"""
    return 'chambre de service' in text.lower()


def extract_presence_concierge(text: str) -> bool:
    """Détecte la présence de concierge / gardien"""
    text_lower = text.lower()
    return 'concierge' in text_lower or 'gardien' in text_lower


def extract_presence_piscine(text: str) -> bool:
    """Détecte la présence de piscine"""
    return 'piscine' in text.lower()


def extract_presence_salle_sport(text: str) -> bool:
    """Détecte la présence de salle de sport"""
    text_lower = text.lower()
    return 'salle de sport' in text_lower or 'gym' in text_lower


def extract_date_livraison(text: str) -> Optional[str]:
    """Extrait la date de livraison prévue"""
    patterns = [
        r'livraison\s*[:\-]?\s*([a-zéû]+)\s*(\d{4})',
        r'livrable\s*en\s*(\d{4})',
        r'prévue\s*pour\s*([a-zéû]+)\s*(\d{4})',
        r'remise des clés\s*[:\-]?\s*([a-zéû]+)\s*(\d{4})',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            if m.lastindex == 2:
                mois = m.group(1)
                annee = m.group(2)
                return f"{mois} {annee}"
            elif m.lastindex == 1:
                return m.group(1)
    
    return None


def extract_statut_construction(text: str) -> Optional[str]:
    """Extrait le statut de construction"""
    text_lower = text.lower()
    
    if 'projet neuf' in text_lower or 'project neuf' in text_lower:
        return 'Projet neuf'
    elif 'en cours de construction' in text_lower:
        return 'En cours de construction'
    elif 'finalisé' in text_lower:
        return 'Finalisé'
    elif 'neuf' in text_lower:
        return 'Neuf'
    
    return None


def extract_standing(text: str) -> Optional[str]:
    """Extrait le standing du bien"""
    text_lower = text.lower()
    
    if 'haut standing' in text_lower:
        return 'Haut standing'
    elif 'standing' in text_lower:
        return 'Standard'
    
    return None


def extract_equipements_from_text(text: str) -> List[str]:
    """Extrait la liste des équipements depuis le texte"""
    equip_found = []
    text_lower = text.lower()
    
    for eq in EQUIPEMENTS_RECHERCHES:
        if eq in text_lower:
            equip_found.append(eq.title())
    
    # Supprimer les doublons
    seen = set()
    unique_equip = []
    for e in equip_found:
        if e not in seen:
            seen.add(e)
            unique_equip.append(e)
    
    return sorted(unique_equip)


# ========== EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS ==========

def extract_from_caracteristiques(caracteristiques_json: Any) -> Dict[str, Any]:
    """
    Extrait les données depuis le champ caracteristiques (JSON string)
    """
    result = {}
    
    if not caracteristiques_json:
        return result
    
    try:
        # Si c'est une chaîne JSON
        if isinstance(caracteristiques_json, str):
            # Nettoyer la chaîne JSON
            cleaned = caracteristiques_json.replace("'", '"')
            caracs = json.loads(cleaned)
        else:
            caracs = caracteristiques_json
        
        if isinstance(caracs, dict):
            # Mapping des champs
            mapping = {
                'type de bien': 'type_bien',
                'etat': 'etat_bien',
                'étage du bien': 'etage',
                'type du sol': 'type_sol',
                'orientation': 'orientation',
                'standing': 'standing',
                'années': 'age_bien',
                'état': 'statut_construction',
                'livraison:': 'date_livraison',
                'livraison': 'date_livraison'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    result[new_key] = caracs[old_key]
            
            # Extraire les nombres de l'étage
            if 'etage' in result and isinstance(result['etage'], str):
                etage_num = extract_number_from_text(result['etage'])
                if etage_num is not None:
                    result['etage'] = int(etage_num)
            
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_equipements_detaille(equip_det: Any) -> Dict[str, Any]:
    """
    Extrait les données depuis equipements_detaille (string avec ;)
    """
    result = {
        'equipements_detaille_list': [],
        'terrasse_surface': None,
        'jardin_surface': None,
        'balcon_surface': None,
        'parking_nombre': None,
        'parking_type': None
    }
    
    if not equip_det:
        return result
    
    # Convertir en liste
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
        
        # Extraire les surfaces
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
        
        elif 'balcon' in item_lower:
            surface = extract_number_from_text(item)
            if surface:
                result['balcon_surface'] = surface
            equip_list.append('Balcon')
        
        elif 'garage' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['parking_nombre'] = int(nombre)
                result['parking_type'] = 'Garage'
            equip_list.append('Garage')
        
        elif 'parking' in item_lower:
            nombre = extract_number_from_text(item)
            if nombre:
                result['parking_nombre'] = int(nombre)
                result['parking_type'] = 'Parking'
            equip_list.append('Parking')
        
        else:
            equip_list.append(item.title())
    
    result['equipements_detaille_list'] = sorted(list(set(equip_list)))
    
    return result


def extract_from_informations_supplementaires(info_json: Any) -> Dict[str, Any]:
    """
    Extrait les données depuis informations_supplementaires (JSON string)
    """
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
                
                # Convertir les valeurs "Oui"/"Non" en booléens
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


def extract_contact_info(contact_json: Any) -> Dict[str, Any]:
    """
    Extrait les données depuis contact_info (JSON string)
    """
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
                    result[key_clean] = str(value).lower() in ['disponible', 'oui', 'true']
                else:
                    result[key_clean] = value
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_localisation(localisation_json: Any) -> Dict[str, Any]:
    """
    Extrait les données depuis localisation (JSON string)
    """
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
    Extrait TOUS les champs possibles d'un listing de vente d'appartement
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
    
    # Surface
    surface_info = extract_surface_from_text(all_text)
    extracted.update(surface_info)
    
    # Étage
    etage = extract_etage_from_text(all_text)
    if etage is not None:
        extracted['etage_extrait'] = etage
    
    # Orientation
    orientation = extract_orientation_from_text(all_text)
    if orientation:
        extracted['orientation_extrait'] = orientation
    
    # Type de sol
    type_sol = extract_type_sol_from_text(all_text)
    if type_sol:
        extracted['type_sol_extrait'] = type_sol
    
    # Nom de la résidence
    residence = extract_nom_residence_from_text(all_text)
    if residence:
        extracted['residence_extrait'] = residence
    
    # Nom de l'agence
    agence = extract_nom_agence_from_text(all_text)
    if agence:
        extracted['nom_agence_extrait'] = agence
    
    # Téléphone
    telephone = extract_telephone_from_text(all_text)
    if telephone:
        extracted['telephone_extrait'] = telephone
    
    # Email
    email = extract_email_from_text(all_text)
    if email:
        extracted['email_extrait'] = email
    
    # Site web
    site_web = extract_site_web_from_text(all_text)
    if site_web:
        extracted['site_web_extrait'] = site_web
    
    # Référence
    reference = extract_reference_from_text(all_text)
    if reference:
        extracted['reference_extrait'] = reference
    
    # Surfaces extérieures
    jardin_surface = extract_surface_jardin(all_text)
    if jardin_surface:
        extracted['jardin_surface_extrait'] = jardin_surface
    
    terrasse_surface = extract_surface_terrasse(all_text)
    if terrasse_surface:
        extracted['terrasse_surface_extrait'] = terrasse_surface
    
    balcon_surface = extract_surface_balcon(all_text)
    if balcon_surface:
        extracted['balcon_surface_extrait'] = balcon_surface
    
    # Parking
    parking_nombre = extract_nombre_parking(all_text)
    if parking_nombre:
        extracted['parking_nombre_extrait'] = parking_nombre
    
    # Chauffage
    chauffage = extract_chauffage_type(all_text)
    if chauffage:
        extracted['chauffage_type_extrait'] = chauffage
    
    # Climatisation
    climatisation = extract_climatisation_type(all_text)
    if climatisation:
        extracted['climatisation_type_extrait'] = climatisation
    
    # Vue
    vue = extract_vue_type(all_text)
    if vue:
        extracted['vue_type_extrait'] = vue
    
    # Présences
    extracted['a_dressing'] = extract_presence_dressing(all_text)
    extracted['a_cellier'] = extract_presence_cellier(all_text)
    extracted['a_chambre_service'] = extract_presence_chambre_service(all_text)
    extracted['a_concierge'] = extract_presence_concierge(all_text)
    extracted['a_piscine'] = extract_presence_piscine(all_text)
    extracted['a_salle_sport'] = extract_presence_salle_sport(all_text)
    
    # Date livraison et statut
    date_livraison = extract_date_livraison(all_text)
    if date_livraison:
        extracted['date_livraison_extrait'] = date_livraison
    
    statut = extract_statut_construction(all_text)
    if statut:
        extracted['statut_construction_extrait'] = statut
    
    standing = extract_standing(all_text)
    if standing:
        extracted['standing_extrait'] = standing
    
    # Équipements depuis texte
    equip_text = extract_equipements_from_text(all_text)
    if equip_text:
        extracted['equipements_texte'] = equip_text
    
    # ===== 3. EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS =====
    
    # Caracteristiques
    caracs_info = extract_from_caracteristiques(listing.get('caracteristiques'))
    if caracs_info:
        extracted.update({f"caracs_{k}": v for k, v in caracs_info.items()})
    
    # Equipements détaillés
    equip_det_info = extract_from_equipements_detaille(listing.get('equipements_detaille'))
    if equip_det_info:
        if equip_det_info.get('equipements_detaille_list'):
            extracted['equipements_detaille_list'] = equip_det_info['equipements_detaille_list']
        if equip_det_info.get('terrasse_surface'):
            extracted['terrasse_surface_extrait'] = equip_det_info['terrasse_surface']
        if equip_det_info.get('jardin_surface'):
            extracted['jardin_surface_extrait'] = equip_det_info['jardin_surface']
        if equip_det_info.get('balcon_surface'):
            extracted['balcon_surface_extrait'] = equip_det_info['balcon_surface']
        if equip_det_info.get('parking_nombre'):
            extracted['parking_nombre_extrait'] = equip_det_info['parking_nombre']
        if equip_det_info.get('parking_type'):
            extracted['parking_type_extrait'] = equip_det_info['parking_type']
    
    # Informations supplémentaires
    info_supp = extract_from_informations_supplementaires(listing.get('informations_supplementaires'))
    if info_supp:
        extracted['informations_supplementaires_parse'] = info_supp
    
    # Contact info
    contact = extract_contact_info(listing.get('contact_info'))
    if contact:
        extracted['contact_info_parse'] = contact
    
    # Localisation GPS
    localisation = extract_from_localisation(listing.get('localisation'))
    if localisation:
        extracted['gps'] = localisation
    
    return extracted


def enrich_listing(listing: Dict) -> Dict:
    """
    Enrichit complètement un listing avec toutes les données extraites
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
    
    if extracted.get('prix_type'):
        enriched['prix_type'] = extracted['prix_type']
    
    # Surface
    if extracted.get('surface') and not listing.get('surface'):
        enriched['surface'] = extracted['surface']
        if extracted.get('surface_text'):
            enriched['surface_text'] = extracted['surface_text']
    
    # Étage
    if extracted.get('etage_extrait') is not None and not listing.get('etage'):
        enriched['etage'] = extracted['etage_extrait']
    
    # Orientation
    if extracted.get('orientation_extrait') and not listing.get('orientation'):
        enriched['orientation'] = extracted['orientation_extrait']
    
    # Type de sol
    if extracted.get('type_sol_extrait') and not listing.get('type_sol'):
        enriched['type_sol'] = extracted['type_sol_extrait']
    
    # Résidence
    if extracted.get('residence_extrait') and not listing.get('residence'):
        enriched['residence'] = extracted['residence_extrait']
    
    # Nom agence
    if extracted.get('nom_agence_extrait') and not listing.get('nom_agence'):
        enriched['nom_agence'] = extracted['nom_agence_extrait']
    
    # Contact info enrichi
    if extracted.get('telephone_extrait') or extracted.get('email_extrait') or extracted.get('site_web_extrait'):
        contact_info = enriched.get('contact_info', {})
        if isinstance(contact_info, str):
            try:
                contact_info = json.loads(contact_info)
            except:
                contact_info = {}
        
        if extracted.get('telephone_extrait'):
            contact_info['telephone'] = extracted['telephone_extrait']
        if extracted.get('email_extrait'):
            contact_info['email'] = extracted['email_extrait']
        if extracted.get('site_web_extrait'):
            contact_info['site_web'] = extracted['site_web_extrait']
        
        enriched['contact_info'] = json.dumps(contact_info, ensure_ascii=False)
    
    # Référence
    if extracted.get('reference_extrait') and not listing.get('reference'):
        enriched['reference'] = extracted['reference_extrait']
    
    # Surfaces extérieures
    if extracted.get('jardin_surface_extrait') and not listing.get('jardin_surface'):
        enriched['jardin_surface'] = extracted['jardin_surface_extrait']
    if extracted.get('terrasse_surface_extrait') and not listing.get('terrasse_surface'):
        enriched['terrasse_surface'] = extracted['terrasse_surface_extrait']
    if extracted.get('balcon_surface_extrait') and not listing.get('balcon_surface'):
        enriched['balcon_surface'] = extracted['balcon_surface_extrait']
    
    # Parking
    if extracted.get('parking_nombre_extrait') and not listing.get('parking_nombre'):
        enriched['parking_nombre'] = extracted['parking_nombre_extrait']
    if extracted.get('parking_type_extrait') and not listing.get('parking_type'):
        enriched['parking_type'] = extracted['parking_type_extrait']
    
    # Chauffage et climatisation
    if extracted.get('chauffage_type_extrait') and not listing.get('chauffage_type'):
        enriched['chauffage_type'] = extracted['chauffage_type_extrait']
    if extracted.get('climatisation_type_extrait') and not listing.get('climatisation_type'):
        enriched['climatisation_type'] = extracted['climatisation_type_extrait']
    
    # Vue
    if extracted.get('vue_type_extrait') and not listing.get('vue_type'):
        enriched['vue_type'] = extracted['vue_type_extrait']
    
    # Présences
    for bool_field in ['a_dressing', 'a_cellier', 'a_chambre_service', 'a_concierge', 'a_piscine', 'a_salle_sport']:
        if bool_field in extracted:
            enriched[bool_field] = extracted[bool_field]
    
    # Date livraison et statut
    if extracted.get('date_livraison_extrait') and not listing.get('date_livraison'):
        enriched['date_livraison'] = extracted['date_livraison_extrait']
    if extracted.get('statut_construction_extrait') and not listing.get('statut_construction'):
        enriched['statut_construction'] = extracted['statut_construction_extrait']
    if extracted.get('standing_extrait') and not listing.get('standing'):
        enriched['standing'] = extracted['standing_extrait']
    
    # Équipements fusionnés
    all_equipements = list(set(listing.get('equipements', []) + extracted.get('equipements_texte', [])))
    if extracted.get('equipements_detaille_list'):
        all_equipements = list(set(all_equipements + extracted['equipements_detaille_list']))
    if all_equipements:
        enriched['equipements'] = sorted(all_equipements)
    
    # Informations supplémentaires parsées
    if extracted.get('informations_supplementaires_parse'):
        enriched['informations_supplementaires_parse'] = extracted['informations_supplementaires_parse']
    
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
        'surfaces_extraites': 0,
        'etages_extraits': 0,
        'orientations_extraites': 0,
        'residences_extraites': 0,
        'agences_extraites': 0,
        'contacts_extraits': 0,
        'references_extraites': 0,
        'parkings_extraits': 0,
        'dates_livraison': 0
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
            if enriched.get('surface') and listing.get('surface') != enriched.get('surface'):
                stats['surfaces_extraites'] += 1
            if enriched.get('etage') and not listing.get('etage'):
                stats['etages_extraits'] += 1
            if enriched.get('orientation') and not listing.get('orientation'):
                stats['orientations_extraites'] += 1
            if enriched.get('residence') and not listing.get('residence'):
                stats['residences_extraites'] += 1
            if enriched.get('nom_agence') and not listing.get('nom_agence'):
                stats['agences_extraites'] += 1
            if enriched.get('contact_info') and enriched['contact_info'] != listing.get('contact_info'):
                stats['contacts_extraits'] += 1
            if enriched.get('reference') and not listing.get('reference'):
                stats['references_extraites'] += 1
            if enriched.get('parking_nombre') and not listing.get('parking_nombre'):
                stats['parkings_extraits'] += 1
            if enriched.get('date_livraison') and not listing.get('date_livraison'):
                stats['dates_livraison'] += 1
                
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
    print("📊 STATISTIQUES D'EXTRACTION - VENTE APPARTEMENTS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Surfaces extraites: {stats['surfaces_extraites']}")
    print(f"✅ Étages extraits: {stats['etages_extraits']}")
    print(f"✅ Orientations extraites: {stats['orientations_extraites']}")
    print(f"✅ Résidences extraites: {stats['residences_extraites']}")
    print(f"✅ Agences extraites: {stats['agences_extraites']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print(f"✅ Références extraites: {stats['references_extraites']}")
    print(f"✅ Parkings extraits: {stats['parkings_extraits']}")
    print(f"✅ Dates livraison extraites: {stats['dates_livraison']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Vente d'Appartements")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()