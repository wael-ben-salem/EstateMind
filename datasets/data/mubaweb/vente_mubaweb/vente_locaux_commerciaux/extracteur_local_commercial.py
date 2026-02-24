"""
Agent d'extraction pour Vente de Locaux Commerciaux
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

TYPES_LOCAUX = [
    'local commercial', 'bureau commercial', 'bureau', 'magasin',
    'boutique', 'restaurant', 'café', 'showroom', 'entrepôt',
    'dépôt', 'atelier', 'espace de travail', 'open space'
]

EQUIPEMENTS_COMMERCIAUX = [
    'vitrine', 'devanture', 'enseigne', 'terrasse', 'mezzanine',
    'double hauteur', 'ascenseur', 'monte-charge', 'ascenseur de charge',
    'parking', 'parking clientèle', 'livraison', 'quai de déchargement',
    'alarme', 'vidéosurveillance', 'caméras', 'vigile', 'sécurité',
    'climatisation', 'climatisation centrale', 'chauffage',
    'chauffage central', 'double vitrage', 'porte blindée',
    'salle de bain', 'salle d\'eau', 'toilette', 'wc', 'kitchenette',
    'cuisine équipée', 'réfrigérateur', 'four', 'micro-ondes',
    'fibre optique', 'internet', 'wifi', 'antenne parabolique',
    'accessibilité PMR', 'normes ERP', 'issue de secours',
    'extincteur', 'sprinklers', 'détection incendie'
]

ZONES_ACTIVITE = [
    'commerciale', 'bureaux', 'mixte', 'industrielle',
    'artisanale', 'restauration', 'services'
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
                if 10000 <= val <= 50000000:
                    result['prix'] = val
                    break
            except:
                continue
    
    return result


def extract_surface_from_text(text: str) -> Dict[str, Any]:
    """Extraction de la surface"""
    result = {}
    
    surface_patterns = [
        r'(\d+)\s*m[²2]',
        r'(\d+)\s*m[e]?tres? carrés?',
        r'surface\s*[:\-]?\s*(\d+)',
        r'superficie\s*[:\-]?\s*(\d+)',
    ]
    
    for pattern in surface_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                surface_val = float(m.group(1))
                if 10 <= surface_val <= 5000:
                    result['surface'] = surface_val
                    result['surface_text'] = f"{int(surface_val)} m²"
                    break
            except:
                continue
    
    return result


def extract_type_local_from_text(text: str) -> Optional[str]:
    """Extrait le type de local"""
    text_lower = text.lower()
    
    for type_local in TYPES_LOCAUX:
        if type_local in text_lower:
            return type_local.title()
    
    return None


def extract_presence_mezzanine(text: str) -> bool:
    """Détecte la présence d'une mezzanine"""
    text_lower = text.lower()
    return 'mezzanine' in text_lower


def extract_presence_double_hauteur(text: str) -> bool:
    """Détecte la double hauteur"""
    text_lower = text.lower()
    return 'double hauteur' in text_lower or 'double-hauteur' in text_lower


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


def extract_nombre_vitrines(text: str) -> Optional[int]:
    """Extrait le nombre de vitrines"""
    patterns = [
        r'(\d+)\s*vitrine[s]?',
        r'vitrine\s+(\d+)',
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


def extract_largeur_facade(text: str) -> Optional[float]:
    """Extrait la largeur de la façade"""
    patterns = [
        r'façade\s+de\s*(\d+)\s*m',
        r'façade\s+(\d+)\s*m',
        r'vitrine\s+(\d+)\s*m',
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


def extract_nombre_parking(text: str) -> Optional[int]:
    """Extrait le nombre de places de parking"""
    patterns = [
        r'(\d+)\s*place[s]?\s*(?:de)?\s*parking',
        r'(\d+)\s*parking[s]?',
        r'parking\s+(\d+)\s*places?',
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


def extract_presence_livraison(text: str) -> bool:
    """Détecte la présence d'un accès livraison"""
    text_lower = text.lower()
    keywords = ['livraison', 'quai de déchargement', 'accès camion', 'déchargement']
    return any(keyword in text_lower for keyword in keywords)


def extract_zone_activite(text: str) -> Optional[str]:
    """Extrait la zone d'activité"""
    text_lower = text.lower()
    
    for zone in ZONES_ACTIVITE:
        if zone in text_lower:
            return zone.title()
    
    return None


def extract_presence_enseigne(text: str) -> bool:
    """Détecte la possibilité d'enseigne"""
    return 'enseigne' in text.lower()


def extract_presence_alarme(text: str) -> bool:
    """Détecte la présence d'alarme"""
    text_lower = text.lower()
    keywords = ['alarme', 'sécurité', 'vidéosurveillance', 'caméras', 'vigile']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_monte_charge(text: str) -> bool:
    """Détecte la présence d'un monte-charge"""
    text_lower = text.lower()
    keywords = ['monte-charge', 'monte charge', 'ascenseur de charge']
    return any(keyword in text_lower for keyword in keywords)


def extract_presence_accessibilite_pmr(text: str) -> bool:
    """Détecte l'accessibilité PMR"""
    text_lower = text.lower()
    keywords = ['pmr', 'accessibilité', 'personnes à mobilité réduite', 'handicapé']
    return any(keyword in text_lower for keyword in keywords)


def extract_etage_from_text(text: str) -> Optional[int]:
    """Extrait le numéro d'étage"""
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


def extract_nombre_sdb_from_text(text: str) -> Optional[int]:
    """Extrait le nombre de salles de bain/d'eau"""
    patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'(\d+)\s*wc',
        r'(\d+)\s*toilette[s]?',
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
                'années': 'age_bien',
                'type du sol': 'type_sol',
                'état': 'statut_construction'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    result[new_key] = caracs[old_key]
    
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
                
                if 'catalogue_pdf_urls' in key_clean:
                    if isinstance(value, list):
                        result['catalogue_urls'] = value
                elif 'catalogue_pdf' in key_clean:
                    if isinstance(value, str):
                        result['catalogue_disponible'] = value.lower() in ['disponible', 'oui', 'true']
                elif 'formulaire' in key_clean:
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


def extract_amenities_commercial(amenities: Any) -> List[str]:
    """Extrait la liste des amenities commerciales"""
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
    
    # Prix
    prix_info = extract_prix_from_text(all_text)
    extracted.update(prix_info)
    
    # Surface
    surface_info = extract_surface_from_text(all_text)
    extracted.update(surface_info)
    
    # Type de local
    type_local = extract_type_local_from_text(all_text)
    if type_local:
        extracted['type_local_extrait'] = type_local
    
    # Mezzanine
    extracted['a_mezzanine'] = extract_presence_mezzanine(all_text)
    surface_mezzanine = extract_surface_mezzanine(all_text)
    if surface_mezzanine:
        extracted['surface_mezzanine'] = surface_mezzanine
    
    # Double hauteur
    extracted['double_hauteur'] = extract_presence_double_hauteur(all_text)
    
    # Vitrines
    nb_vitrines = extract_nombre_vitrines(all_text)
    if nb_vitrines:
        extracted['nombre_vitrines'] = nb_vitrines
    
    largeur_facade = extract_largeur_facade(all_text)
    if largeur_facade:
        extracted['largeur_facade'] = largeur_facade
    
    # Terrasse
    extracted['a_terrasse'] = extract_presence_terrasse(all_text)
    surface_terrasse = extract_surface_terrasse(all_text)
    if surface_terrasse:
        extracted['surface_terrasse'] = surface_terrasse
    
    # Parking
    nb_parking = extract_nombre_parking(all_text)
    if nb_parking:
        extracted['parking_nombre'] = nb_parking
    
    # Livraison
    extracted['acces_livraison'] = extract_presence_livraison(all_text)
    
    # Zone d'activité
    zone = extract_zone_activite(all_text)
    if zone:
        extracted['zone_activite'] = zone
    
    # Enseigne
    extracted['possibilite_enseigne'] = extract_presence_enseigne(all_text)
    
    # Sécurité
    extracted['a_alarme'] = extract_presence_alarme(all_text)
    
    # Monte-charge
    extracted['a_monte_charge'] = extract_presence_monte_charge(all_text)
    
    # Accessibilité PMR
    extracted['accessibilite_pmr'] = extract_presence_accessibilite_pmr(all_text)
    
    # Étage
    etage = extract_etage_from_text(all_text)
    if etage is not None:
        extracted['etage_extrait'] = etage
    
    # Salles de bain
    nb_sdb = extract_nombre_sdb_from_text(all_text)
    if nb_sdb:
        extracted['nombre_sdb_extrait'] = nb_sdb
    
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
    
    # Contact info
    contact = extract_from_contact_info(listing.get('contact_info'))
    if contact:
        extracted['contact_info_parse'] = contact
    
    # Localisation GPS
    localisation = extract_from_localisation(listing.get('localisation'))
    if localisation:
        extracted['gps'] = localisation
    
    # Amenities commerciales
    amenities = extract_amenities_commercial(listing.get('amenities_commercial', []))
    if amenities:
        extracted['amenities_commercial_list'] = amenities
    
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
    
    # Prix
    if extracted.get('prix') and (not listing.get('prix') or listing.get('prix') == 0):
        enriched['prix'] = extracted['prix']
        if extracted.get('prix_text'):
            enriched['prix_text'] = extracted['prix_text']
    
    # Surface
    if extracted.get('surface') and not listing.get('surface'):
        enriched['surface'] = extracted['surface']
        if extracted.get('surface_text'):
            enriched['surface_text'] = extracted['surface_text']
    
    # Type de local
    if extracted.get('type_local_extrait') and not listing.get('type_local'):
        enriched['type_local'] = extracted['type_local_extrait']
    
    # Mezzanine
    if extracted.get('a_mezzanine') is not None:
        enriched['a_mezzanine'] = extracted['a_mezzanine']
    if extracted.get('surface_mezzanine'):
        enriched['surface_mezzanine'] = extracted['surface_mezzanine']
    
    # Double hauteur
    if extracted.get('double_hauteur') is not None:
        enriched['double_hauteur'] = extracted['double_hauteur']
    
    # Vitrines
    if extracted.get('nombre_vitrines'):
        enriched['nombre_vitrines'] = extracted['nombre_vitrines']
    if extracted.get('largeur_facade'):
        enriched['largeur_facade'] = extracted['largeur_facade']
    
    # Terrasse
    if extracted.get('a_terrasse') is not None:
        enriched['a_terrasse'] = extracted['a_terrasse']
    if extracted.get('surface_terrasse'):
        enriched['surface_terrasse'] = extracted['surface_terrasse']
    
    # Parking
    if extracted.get('parking_nombre'):
        enriched['parking_nombre'] = extracted['parking_nombre']
    
    # Livraison
    if extracted.get('acces_livraison') is not None:
        enriched['acces_livraison'] = extracted['acces_livraison']
    
    # Zone d'activité
    if extracted.get('zone_activite'):
        enriched['zone_activite'] = extracted['zone_activite']
    
    # Enseigne
    if extracted.get('possibilite_enseigne') is not None:
        enriched['possibilite_enseigne'] = extracted['possibilite_enseigne']
    
    # Sécurité
    if extracted.get('a_alarme') is not None:
        enriched['a_alarme'] = extracted['a_alarme']
    
    # Monte-charge
    if extracted.get('a_monte_charge') is not None:
        enriched['a_monte_charge'] = extracted['a_monte_charge']
    
    # Accessibilité PMR
    if extracted.get('accessibilite_pmr') is not None:
        enriched['accessibilite_pmr'] = extracted['accessibilite_pmr']
    
    # Étage
    if extracted.get('etage_extrait') is not None and not listing.get('etage'):
        enriched['etage'] = extracted['etage_extrait']
    
    # Salles de bain
    if extracted.get('nombre_sdb_extrait') and not listing.get('nombre_sdb'):
        enriched['nombre_sdb'] = extracted['nombre_sdb_extrait']
    
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
    all_equipements = list(set(listing.get('equipements', []) + extracted.get('equipements_texte', [])))
    if extracted.get('amenities_commercial_list'):
        all_equipements = list(set(all_equipements + extracted['amenities_commercial_list']))
    if all_equipements:
        enriched['equipements'] = sorted(all_equipements)
    
    # Caractéristiques enrichies
    caracs = {}
    for key in ['caracs_etat_bien', 'caracs_age_bien', 'caracs_type_sol', 'caracs_statut_construction']:
        if extracted.get(key):
            field = key.replace('caracs_', '')
            caracs[field] = extracted[key]
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
        'surfaces_extraites': 0,
        'mezzanines_detectees': 0,
        'double_hauteur_detectees': 0,
        'vitrines_extraites': 0,
        'parkings_extraits': 0,
        'etages_extraits': 0,
        'sdb_extraites': 0,
        'contacts_extraits': 0,
        'catalogues_trouves': 0
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
            if enriched.get('a_mezzanine'):
                stats['mezzanines_detectees'] += 1
            if enriched.get('double_hauteur'):
                stats['double_hauteur_detectees'] += 1
            if enriched.get('nombre_vitrines'):
                stats['vitrines_extraites'] += 1
            if enriched.get('parking_nombre'):
                stats['parkings_extraits'] += 1
            if enriched.get('etage') and not listing.get('etage'):
                stats['etages_extraits'] += 1
            if enriched.get('nombre_sdb') and not listing.get('nombre_sdb'):
                stats['sdb_extraites'] += 1
            if enriched.get('telephone_extrait'):
                stats['contacts_extraits'] += 1
            if enriched.get('contact_info_parse', {}).get('catalogue_urls'):
                stats['catalogues_trouves'] += 1
                
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
    print("📊 STATISTIQUES D'EXTRACTION - LOCAUX COMMERCIAUX")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Surfaces extraites: {stats['surfaces_extraites']}")
    print(f"✅ Mezzanines détectées: {stats['mezzanines_detectees']}")
    print(f"✅ Double hauteur détectées: {stats['double_hauteur_detectees']}")
    print(f"✅ Vitrines extraites: {stats['vitrines_extraites']}")
    print(f"✅ Parkings extraits: {stats['parkings_extraits']}")
    print(f"✅ Étages extraits: {stats['etages_extraits']}")
    print(f"✅ Salles d'eau extraites: {stats['sdb_extraites']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print(f"✅ Catalogues PDF trouvés: {stats['catalogues_trouves']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Locaux Commerciaux")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()