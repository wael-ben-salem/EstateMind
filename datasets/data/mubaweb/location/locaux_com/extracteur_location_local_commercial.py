"""
Agent d'extraction pour Location de Locaux Commerciaux
Extrait TOUS les champs spécifiques aux locaux commerciaux
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES AUX LOCAUX COMMERCIAUX ==========

TYPES_LOCAUX_COMMERCIAUX = [
    'local commercial', 'boutique', 'magasin', 'showroom',
    'restaurant', 'café', 'bar', 'brasserie', 'snack',
    'salon de coiffure', 'institut de beauté', 'esthétique',
    'pharmacie', 'parapharmacie', 'cabinet médical',
    'agence bancaire', 'bureau de change', 'assurance',
    'espace de vente', 'commerce', 'point de vente',
    'open space', 'espace bureautique', 'plateau'
]

ACTIVITES_COMMERCIALES = [
    'commerce', 'boutique', 'restauration', 'café', 'bar',
    'coiffure', 'esthétique', 'médical', 'paramédical',
    'bancaire', 'assurance', 'bureau', 'showroom',
    'artisanat', 'services', 'professions libérales'
]

EQUIPEMENTS_COMMERCIAUX = [
    'vitrine', 'devanture', 'enseigne', 'éclairage',
    'terrasse', 'mezzanine', 'réserve', 'dépôt',
    'parking', 'parking clientèle', 'livraison',
    'quai de déchargement', 'monte-charge',
    'climatisation', 'climatisation centrale',
    'chauffage', 'chauffage central',
    'alarme', 'vidéosurveillance', 'gardien',
    'sécurité', 'badge', 'contrôle d\'accès',
    'double vitrage', 'porte blindée', 'porte vitrée',
    'sanitaires', 'wc', 'toilettes', 'salle d\'eau',
    'kitchenette', 'cuisine', 'office',
    'hotte', 'extraction', 'ventilation',
    'fibre optique', 'internet', 'wifi',
    'accessibilité pmr', 'handicapés', 'personnes à mobilité réduite'
]

PROXIMITES_COMMERCIALES = [
    'artère principale', 'avenue principale', 'rue commerçante',
    'centre ville', 'centre commercial', 'galerie marchande',
    'passage piéton', 'zone piétonne', 'parking public',
    'transports', 'métro', 'bus', 'station',
    'banques', 'commerces', 'restaurants', 'hôtels'
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
                if 100 <= val <= 500000:
                    result['loyer'] = val
                    break
            except:
                continue
    
    return result


def extract_type_local_from_text(text: str) -> Optional[str]:
    """Extrait le type de local"""
    text_lower = text.lower()
    
    for type_local in TYPES_LOCAUX_COMMERCIAUX:
        if type_local in text_lower:
            return type_local.title()
    
    return None


def extract_activites_from_text(text: str) -> List[str]:
    """Extrait les activités possibles"""
    found_activites = []
    text_lower = text.lower()
    
    for activite in ACTIVITES_COMMERCIALES:
        if activite in text_lower:
            found_activites.append(activite.title())
    
    return list(set(found_activites))


def extract_est_gerance_libre(text: str) -> bool:
    """Détecte si c'est une gérance libre"""
    text_lower = text.lower()
    return 'gérance libre' in text_lower or 'gerance libre' in text_lower


def extract_presence_vitrine(text: str) -> bool:
    """Détecte la présence de vitrines"""
    return 'vitrine' in text.lower()


def extract_nombre_vitrines(text: str) -> Optional[int]:
    """Extrait le nombre de vitrines"""
    patterns = [
        r'(\d+)\s*vitrine[s]?',
        r'vitrine\s+(\d+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_largeur_facade(text: str) -> Optional[float]:
    """Extrait la largeur de la façade"""
    patterns = [
        r'façade\s+de\s*(\d+)\s*m',
        r'façade\s+(\d+)\s*m',
        r'largeur\s+de\s*(\d+)\s*m',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_emplacement(text: str) -> Optional[str]:
    """Extrait le type d'emplacement"""
    text_lower = text.lower()
    
    if 'artère principale' in text_lower:
        return 'Artère principale'
    elif 'avenue principale' in text_lower:
        return 'Avenue principale'
    elif 'rue commerçante' in text_lower:
        return 'Rue commerçante'
    elif 'centre ville' in text_lower:
        return 'Centre-ville'
    elif 'centre commercial' in text_lower:
        return 'Centre commercial'
    elif 'passage' in text_lower:
        return 'Passage'
    elif 'zone piétonne' in text_lower:
        return 'Zone piétonne'
    
    return None


def extract_hauteur_sous_plafond(text: str) -> Optional[float]:
    """Extrait la hauteur sous plafond"""
    patterns = [
        r'hauteur\s+de\s*(\d+)\s*m',
        r'hauteur\s+(\d+)\s*m',
        r'(\d+)\s*m\s+de\s+hauteur',
        r'plafond\s+(\d+)\s*m',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_presence_mezzanine(text: str) -> bool:
    """Détecte la présence d'une mezzanine"""
    return 'mezzanine' in text.lower()


def extract_surface_mezzanine(text: str) -> Optional[float]:
    """Extrait la surface de la mezzanine"""
    patterns = [
        r'mezzanine\s+de\s*(\d+)\s*m[²2]',
        r'mezzanine\s+(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
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


def extract_parking_clientele(text: str) -> bool:
    """Détecte si le parking est pour la clientèle"""
    text_lower = text.lower()
    return 'parking clientèle' in text_lower


def extract_presence_livraison(text: str) -> bool:
    """Détecte la présence d'un accès livraison"""
    text_lower = text.lower()
    keywords = ['livraison', 'quai de déchargement', 'accès camion']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_enseigne(text: str) -> bool:
    """Détecte la possibilité d'enseigne"""
    return 'enseigne' in text.lower()


def extract_presence_hotte(text: str) -> bool:
    """Détecte la présence d'une hotte (restauration)"""
    return 'hotte' in text.lower()


def extract_presence_extraction(text: str) -> bool:
    """Détecte la présence d'une ventilation/extraction"""
    text_lower = text.lower()
    keywords = ['extraction', 'ventilation', 'vme']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_reserve(text: str) -> bool:
    """Détecte la présence d'une réserve"""
    text_lower = text.lower()
    keywords = ['réserve', 'reserve', 'dépôt', 'depot', 'arrière-boutique']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_acces_independant(text: str) -> bool:
    """Détecte la présence d'un accès indépendant"""
    text_lower = text.lower()
    keywords = ['accès indépendant', 'entrée indépendante', 'entrée privative']
    return any(keyword in text_lower for keyword in keywords)


def extract_acces_24h(text: str) -> bool:
    """Détecte si l'accès est 24h/24"""
    text_lower = text.lower()
    return '24h' in text_lower or '24/7' in text_lower or '24h/24' in text_lower


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
    elif 'climatisation split' in text_lower:
        return 'Split'
    
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
    keywords = ['sécurité', 'alarme', 'caméras', 'vidéosurveillance', 'gardien']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_ascenseur(text: str) -> bool:
    """Détecte la présence d'ascenseur"""
    return 'ascenseur' in text.lower()


def extract_presence_monte_charge(text: str) -> bool:
    """Détecte la présence d'un monte-charge"""
    return 'monte-charge' in text.lower() or 'monte charge' in text.lower()


def extract_presence_accessibilite_pmr(text: str) -> bool:
    """Détecte l'accessibilité PMR"""
    text_lower = text.lower()
    keywords = ['pmr', 'accessibilité', 'handicapés', 'mobilité réduite']
    return any(keyword in text_lower for keyword in keywords)


def extract_normes_erp(text: str) -> bool:
    """Détecte si le local est aux normes ERP"""
    text_lower = text.lower()
    return 'erp' in text_lower


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


def extract_depot_garantie(text: str) -> Optional[float]:
    """Extrait le montant du dépôt de garantie"""
    patterns = [
        r'dépôt de garantie\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'caution\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'garantie\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_droit_au_bail(text: str) -> Optional[float]:
    """Extrait le montant du droit au bail"""
    patterns = [
        r'droit au bail\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
        r'pas-de-porte\s*[:\-]?\s*(\d+)\s*(?:tnd|dt)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_proximites(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_COMMERCIALES:
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


def extract_vendeur(text: str) -> Optional[str]:
    """Extrait le nom du vendeur/complexe"""
    patterns = [
        r'vendeur[:\s]*([^\.]+)',
        r'complexe[:\s]*([^\.]+)',
        r'proposé par[:\s]*([^\.]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None


def extract_equipements_from_text(text: str) -> List[str]:
    """Extrait la liste des équipements depuis le texte"""
    equip_found = []
    text_lower = text.lower()
    
    for eq in EQUIPEMENTS_COMMERCIAUX:
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
                'années': 'age_bien'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    val = caracs[old_key]
                    result[new_key] = val
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extract_from_amenities_commercial(amenities: Any) -> List[str]:
    """Extrait depuis amenities_commercial"""
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


def extract_from_activites_possibles(activites: Any) -> List[str]:
    """Extrait depuis activites_possibles"""
    if not activites:
        return []
    
    if isinstance(activites, list):
        return activites
    
    if isinstance(activites, str):
        if ',' in activites:
            return [a.strip() for a in activites.split(',') if a.strip()]
        else:
            return [activites.strip()]
    
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
                elif 'vendeur' in key_clean:
                    result['vendeur'] = value
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
    Extrait TOUS les champs possibles d'un listing de local commercial
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
    
    # Type de local
    type_local = extract_type_local_from_text(all_text)
    if type_local:
        extracted['type_local_extrait'] = type_local
    
    # Activités possibles
    activites = extract_activites_from_text(all_text)
    if activites:
        extracted['activites_possibles_extrait'] = activites
    
    # Gérance libre
    extracted['est_gerance_libre'] = extract_est_gerance_libre(all_text)
    
    # Vitrines
    extracted['a_vitrine'] = extract_presence_vitrine(all_text)
    nb_vitrines = extract_nombre_vitrines(all_text)
    if nb_vitrines:
        extracted['nombre_vitrines'] = nb_vitrines
    largeur_facade = extract_largeur_facade(all_text)
    if largeur_facade:
        extracted['largeur_facade'] = largeur_facade
    
    # Emplacement
    emplacement = extract_emplacement(all_text)
    if emplacement:
        extracted['emplacement'] = emplacement
    
    # Hauteur et mezzanine
    hauteur = extract_hauteur_sous_plafond(all_text)
    if hauteur:
        extracted['hauteur_sous_plafond'] = hauteur
    extracted['a_mezzanine'] = extract_presence_mezzanine(all_text)
    surface_mezzanine = extract_surface_mezzanine(all_text)
    if surface_mezzanine:
        extracted['surface_mezzanine'] = surface_mezzanine
    
    # Terrasse
    extracted['a_terrasse'] = extract_presence_terrasse(all_text)
    surface_terrasse = extract_surface_terrasse(all_text)
    if surface_terrasse:
        extracted['surface_terrasse'] = surface_terrasse
    
    # Parking
    extracted['a_parking'] = extract_presence_parking(all_text)
    nb_parking = extract_nombre_parking(all_text)
    if nb_parking:
        extracted['parking_nombre'] = nb_parking
    extracted['parking_clientele'] = extract_parking_clientele(all_text)
    
    # Livraison
    extracted['a_livraison'] = extract_presence_livraison(all_text)
    
    # Enseigne
    extracted['a_enseigne'] = extract_presence_enseigne(all_text)
    
    # Restauration
    extracted['a_hotte'] = extract_presence_hotte(all_text)
    extracted['a_extraction'] = extract_presence_extraction(all_text)
    
    # Réserve
    extracted['a_reserve'] = extract_presence_reserve(all_text)
    
    # Accès
    extracted['acces_independant'] = extract_presence_acces_independant(all_text)
    extracted['acces_24h'] = extract_acces_24h(all_text)
    
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
    extracted['a_monte_charge'] = extract_presence_monte_charge(all_text)
    
    # Accessibilité
    extracted['accessibilite_pmr'] = extract_presence_accessibilite_pmr(all_text)
    extracted['normes_erp'] = extract_normes_erp(all_text)
    
    # Charges
    extracted['charges_incluses'] = extract_charges_incluses(all_text)
    montant_charges = extract_montant_charges(all_text)
    if montant_charges:
        extracted['montant_charges'] = montant_charges
    
    # Dépôt de garantie
    depot = extract_depot_garantie(all_text)
    if depot:
        extracted['depot_garantie'] = depot
    
    # Droit au bail
    droit_bail = extract_droit_au_bail(all_text)
    if droit_bail:
        extracted['droit_au_bail'] = droit_bail
    
    # Proximités
    proximites = extract_proximites(all_text)
    if proximites:
        extracted['proximites'] = proximites
    
    # Téléphone
    telephone = extract_telephone_from_text(all_text)
    if telephone:
        extracted['telephone_extrait'] = telephone
    
    # Vendeur
    vendeur = extract_vendeur(all_text)
    if vendeur:
        extracted['vendeur_extrait'] = vendeur
    
    # Équipements
    equip_text = extract_equipements_from_text(all_text)
    if equip_text:
        extracted['equipements_texte'] = equip_text
    
    # ===== 3. EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS =====
    
    # Caracteristiques
    caracs_info = extract_from_caracteristiques(listing.get('caracteristiques'))
    if caracs_info:
        extracted.update({f"caracs_{k}": v for k, v in caracs_info.items()})
    
    # Amenities commercial
    amenities = extract_from_amenities_commercial(listing.get('amenities_commercial', []))
    if amenities:
        extracted['amenities_commercial_list'] = amenities
    
    # Activités possibles (déjà dans le champ)
    if listing.get('activites_possibles'):
        extracted['activites_possibles_original'] = listing['activites_possibles']
    
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
    Enrichit complètement un listing de local commercial
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
    
    # Type de local
    if extracted.get('type_local_extrait') and not listing.get('type_local'):
        enriched['type_local'] = extracted['type_local_extrait']
    
    # Activités possibles
    if extracted.get('activites_possibles_extrait'):
        current_activites = listing.get('activites_possibles', [])
        all_activites = list(set(current_activites + extracted['activites_possibles_extrait']))
        if all_activites:
            enriched['activites_possibles'] = sorted(all_activites)
    
    # Gérance libre
    if extracted.get('est_gerance_libre') is not None:
        enriched['est_gerance_libre'] = extracted['est_gerance_libre']
    
    # Vitrines
    if extracted.get('a_vitrine') is not None:
        enriched['a_vitrine'] = extracted['a_vitrine']
    if extracted.get('nombre_vitrines'):
        enriched['nombre_vitrines'] = extracted['nombre_vitrines']
    if extracted.get('largeur_facade'):
        enriched['largeur_facade'] = extracted['largeur_facade']
    
    # Emplacement
    if extracted.get('emplacement') and not listing.get('emplacement'):
        enriched['emplacement'] = extracted['emplacement']
    
    # Hauteur et mezzanine
    if extracted.get('hauteur_sous_plafond'):
        enriched['hauteur_sous_plafond'] = extracted['hauteur_sous_plafond']
    if extracted.get('a_mezzanine') is not None:
        enriched['a_mezzanine'] = extracted['a_mezzanine']
    if extracted.get('surface_mezzanine'):
        enriched['surface_mezzanine'] = extracted['surface_mezzanine']
    
    # Terrasse
    if extracted.get('a_terrasse') is not None:
        enriched['a_terrasse'] = extracted['a_terrasse']
    if extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det'):
        enriched['surface_terrasse'] = extracted.get('surface_terrasse') or extracted.get('surface_terrasse_det')
    
    # Parking
    if extracted.get('a_parking') is not None:
        enriched['a_parking'] = extracted['a_parking']
    if extracted.get('parking_nombre') or extracted.get('parking_nombre_det'):
        enriched['parking_nombre'] = extracted.get('parking_nombre') or extracted.get('parking_nombre_det')
    if extracted.get('parking_clientele') is not None:
        enriched['parking_clientele'] = extracted['parking_clientele']
    
    # Livraison
    if extracted.get('a_livraison') is not None:
        enriched['a_livraison'] = extracted['a_livraison']
    
    # Enseigne
    if extracted.get('a_enseigne') is not None:
        enriched['a_enseigne'] = extracted['a_enseigne']
    
    # Restauration
    if extracted.get('a_hotte') is not None:
        enriched['a_hotte'] = extracted['a_hotte']
    if extracted.get('a_extraction') is not None:
        enriched['a_extraction'] = extracted['a_extraction']
    
    # Réserve
    if extracted.get('a_reserve') is not None:
        enriched['a_reserve'] = extracted['a_reserve']
    
    # Accès
    if extracted.get('acces_independant') is not None:
        enriched['acces_independant'] = extracted['acces_independant']
    if extracted.get('acces_24h') is not None:
        enriched['acces_24h'] = extracted['acces_24h']
    
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
    
    # Sécurité
    if extracted.get('a_securite') is not None:
        enriched['a_securite'] = extracted['a_securite']
    
    # Ascenseur
    if extracted.get('a_ascenseur') is not None:
        enriched['a_ascenseur'] = extracted['a_ascenseur']
    if extracted.get('a_monte_charge') is not None:
        enriched['a_monte_charge'] = extracted['a_monte_charge']
    
    # Accessibilité
    if extracted.get('accessibilite_pmr') is not None:
        enriched['accessibilite_pmr'] = extracted['accessibilite_pmr']
    if extracted.get('normes_erp') is not None:
        enriched['normes_erp'] = extracted['normes_erp']
    
    # Charges
    if extracted.get('charges_incluses') is not None:
        enriched['charges_incluses'] = extracted['charges_incluses']
    if extracted.get('montant_charges'):
        enriched['montant_charges'] = extracted['montant_charges']
    
    # Dépôt de garantie
    if extracted.get('depot_garantie'):
        enriched['depot_garantie'] = extracted['depot_garantie']
    
    # Droit au bail
    if extracted.get('droit_au_bail'):
        enriched['droit_au_bail'] = extracted['droit_au_bail']
    
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
    
    # Vendeur
    if extracted.get('vendeur_extrait') and not listing.get('vendeur'):
        enriched['vendeur'] = extracted['vendeur_extrait']
    
    # Équipements fusionnés
    all_equipements = list(set(listing.get('equipements', []) +
                                extracted.get('equipements_texte', []) +
                                extracted.get('amenities_commercial_list', []) +
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
        'types_local_extraits': 0,
        'activites_extraites': 0,
        'gerances_libres': 0,
        'vitrines_detectees': 0,
        'mezzanines_detectees': 0,
        'terrasses_detectees': 0,
        'parkings_detectes': 0,
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
            if enriched.get('type_local') and not listing.get('type_local'):
                stats['types_local_extraits'] += 1
            if enriched.get('activites_possibles') and len(enriched['activites_possibles']) > len(listing.get('activites_possibles', [])):
                stats['activites_extraites'] += 1
            if enriched.get('est_gerance_libre'):
                stats['gerances_libres'] += 1
            if enriched.get('a_vitrine'):
                stats['vitrines_detectees'] += 1
            if enriched.get('a_mezzanine'):
                stats['mezzanines_detectees'] += 1
            if enriched.get('a_terrasse'):
                stats['terrasses_detectees'] += 1
            if enriched.get('a_parking'):
                stats['parkings_detectes'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - LOCAUX COMMERCIAUX (LOCATION)")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Loyers extraits/améliorés: {stats['loyers_extraits']}")
    print(f"✅ Types de local extraits: {stats['types_local_extraits']}")
    print(f"✅ Activités extraites: {stats['activites_extraites']}")
    print(f"✅ Gérance libre détectée: {stats['gerances_libres']}")
    print(f"✅ Vitrines détectées: {stats['vitrines_detectees']}")
    print(f"✅ Mezzanines détectées: {stats['mezzanines_detectees']}")
    print(f"✅ Terrasses détectées: {stats['terrasses_detectees']}")
    print(f"✅ Parkings détectés: {stats['parkings_detectes']}")
    print(f"✅ Climatisations détectées: {stats['climatisations_detectees']}")
    print(f"✅ Sécurité détectée: {stats['securite_detectee']}")
    print(f"✅ Charges détectées: {stats['charges_detectees']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Location de Locaux Commerciaux")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()