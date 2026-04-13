"""
Agent d'extraction pour Vente de Terrains
Extrait TOUS les champs spécifiques aux terrains
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote


# ========== CONSTANTES SPÉCIFIQUES AUX TERRAINS ==========

TYPES_TERRAINS = [
    'terrain de promotion', 'terrain agricole', 'terrain constructible',
    'terrain résidentiel', 'terrain commercial', 'terrain industriel',
    'terrain touristique', 'terrain mixte', 'lots de villa',
    'groupement d\'habitation', 'terrain à bâtir', 'terrain viabilisé',
    'terrain non constructible', 'terrain nu', 'terrain avec vue mer'
]

VOCATIONS = [
    'résidentiel', 'commercial', 'industriel', 'touristique', 'agricole', 'mixte'
]

SITUATIONS_JURIDIQUES = [
    'titre bleu', 'titre foncier', 'titré', 'promesse de vente',
    'indivision', 'cadastre', 'certificat de propriété', 'acte notarié',
    'contrat de réservation', 'loti'
]

VIABILISATION = [
    'eau', 'électricité', 'gaz', 'téléphone', 'assainissement',
    'tout-à-l\'égout', 'viabilisé', 'non viabilisé', 'réseaux'
]

CONSTRUCTIBILITE = [
    'constructible', 'non constructible', 'plain pied', 'r+1', 'r+2', 'r+3',
    'cos', 'ces', 'coefficient d\'occupation des sols'
]

TOPOLOGIE = [
    'plat', 'en pente', 'vallonné', 'irrégulier', 'régulier'
]

PROXIMITES_TERRAIN = [
    'mer', 'plage', 'commerces', 'écoles', 'collège', 'lycée',
    'hôpital', 'clinique', 'autoroute', 'route nationale',
    'transport', 'bus', 'centre ville', 'zone touristique'
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


def convert_hectares_to_m2(surface_str: str) -> Optional[float]:
    """Convertit une surface en hectares en m²"""
    if not surface_str:
        return None
    
    surface_str_lower = surface_str.lower()
    if 'hectare' in surface_str_lower or 'ha' in surface_str_lower:
        numbers = re.findall(r'(\d+[.,]?\d*)\s*(?:hectare|ha)', surface_str_lower)
        if numbers:
            try:
                hectares = float(numbers[0].replace(',', '.'))
                return hectares * 10000  # 1 hectare = 10 000 m²
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
    """Extraction du prix total et prix au m²"""
    result = {}
    text_lower = text.lower()
    
    # Prix à consulter
    if any(phrase in text_lower for phrase in ['prix à consulter', 'prix sur demande', 'nous consulter']):
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        return result
    
    # Prix total
    prix_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b(?!\s*/\s*m)', 1),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)(?!\s*/\s*m)', 1),
        (r'(\d+)\s*tnd(?!\s*/\s*m)', 1),
        (r'(\d+)\s*dt\b(?!\s*/\s*m)', 1),
    ]
    
    for pattern, group in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(group).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                if 1000 <= val <= 100000000:  # Jusqu'à 100 millions TND
                    result['prix'] = val
                    break
            except:
                continue
    
    # Prix au m²
    prix_m2_patterns = [
        r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt)\s*/\s*m[²2]',
        r'(\d[\d\s]*\.?\d*)\s*(?:dt)\s*[/-]\s*m²',
        r'(\d+)\s*(?:tnd|dt)\s*/\s*m²',
        r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt)\s*/\s*m²',
    ]
    
    for pattern in prix_m2_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_m2_str = m.group(1).replace(' ', '').replace(',', '.')
                val = float(prix_m2_str)
                if 1 <= val <= 100000:
                    result['prix_m2'] = val
                    break
            except:
                continue
    
    return result


def extract_surface_from_text(text: str) -> Dict[str, Any]:
    """Extraction de la surface en m²"""
    result = {}
    
    # Surface en m²
    surface_patterns = [
        r'(\d+)\s*m[²2]',
        r'(\d+)\s*m[e]?tres? carrés?',
        r'surface\s*[:\-]?\s*(\d+)\s*m²',
        r'superficie\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in surface_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                surface_val = float(m.group(1))
                if 10 <= surface_val <= 1000000:
                    result['surface'] = surface_val
                    result['surface_text'] = f"{int(surface_val)} m²"
                    break
            except:
                continue
    
    # Surface en hectares (conversion)
    hectares_val = convert_hectares_to_m2(text)
    if hectares_val and 'surface' not in result:
        result['surface'] = hectares_val
        result['surface_text'] = f"{int(hectares_val)} m²"
        result['surface_hectares'] = hectares_val / 10000
    
    return result


def extract_type_terrain_from_text(text: str) -> List[str]:
    """Extrait les types de terrain"""
    found_types = []
    text_lower = text.lower()
    
    for type_terrain in TYPES_TERRAINS:
        if type_terrain in text_lower:
            found_types.append(type_terrain.title())
    
    return list(set(found_types))


def extract_vocation_from_text(text: str) -> List[str]:
    """Extrait les vocations du terrain"""
    found_vocations = []
    text_lower = text.lower()
    
    for vocation in VOCATIONS:
        if vocation in text_lower:
            found_vocations.append(vocation.title())
    
    return list(set(found_vocations))


def extract_situation_juridique_from_text(text: str) -> List[str]:
    """Extrait la situation juridique"""
    found_situations = []
    text_lower = text.lower()
    
    for situation in SITUATIONS_JURIDIQUES:
        if situation in text_lower:
            found_situations.append(situation.title())
    
    return list(set(found_situations))


def extract_viabilisation_from_text(text: str) -> List[str]:
    """Extrait les informations de viabilisation"""
    found_viab = []
    text_lower = text.lower()
    
    if 'viabilisé' in text_lower:
        found_viab.append('Viabilisé')
    
    for viab in VIABILISATION:
        if viab in text_lower and viab != 'viabilisé':
            found_viab.append(viab.title())
    
    return list(set(found_viab))


def extract_constructibilite_from_text(text: str) -> List[str]:
    """Extrait les informations de constructibilité"""
    found_const = []
    text_lower = text.lower()
    
    if 'constructible' in text_lower:
        found_const.append('Constructible')
    if 'non constructible' in text_lower:
        found_const.append('Non constructible')
    
    # R+1, R+2, R+3, etc.
    r_pattern = r'r\s*\+\s*(\d+)'
    m = re.search(r_pattern, text_lower)
    if m:
        found_const.append(f"R+{m.group(1)}")
    
    # Plain pied
    if 'plain pied' in text_lower:
        found_const.append('Plain pied')
    
    # COS, CES
    cos_pattern = r'cos\s*[:\-]?\s*([\d.]+)'
    m = re.search(cos_pattern, text_lower)
    if m:
        found_const.append(f"COS {m.group(1)}")
    
    return list(set(found_const))


def extract_topographie_from_text(text: str) -> Optional[str]:
    """Extrait la topographie du terrain"""
    text_lower = text.lower()
    
    for topo in TOPOLOGIE:
        if topo in text_lower:
            return topo.title()
    
    return None


def extract_orientation_from_text(text: str) -> Optional[str]:
    """Extrait l'orientation"""
    orientations = ['nord', 'sud', 'est', 'ouest']
    text_lower = text.lower()
    
    for orientation in orientations:
        if orientation in text_lower:
            return orientation.title()
    
    return None


def extract_vue_from_text(text: str) -> Optional[str]:
    """Extrait le type de vue"""
    text_lower = text.lower()
    
    if 'vue sur mer' in text_lower or 'vue mer' in text_lower:
        return 'Mer'
    elif 'vue sur montagne' in text_lower:
        return 'Montagne'
    elif 'vue dégagée' in text_lower:
        return 'Dégagée'
    elif 'vue panoramique' in text_lower:
        return 'Panoramique'
    
    return None


def extract_acces_from_text(text: str) -> List[str]:
    """Extrait les informations d'accès"""
    found_acces = []
    text_lower = text.lower()
    
    acces_keywords = {
        'route goudronnée': 'Route goudronnée',
        'route goudronne': 'Route goudronnée',
        'piste': 'Piste',
        'impasse': 'Impasse',
        'voie d\'accès': 'Voie d\'accès'
    }
    
    for keyword, label in acces_keywords.items():
        if keyword in text_lower:
            found_acces.append(label)
    
    return list(set(found_acces))


def extract_proximites_from_text(text: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    found_prox = []
    text_lower = text.lower()
    
    for prox in PROXIMITES_TERRAIN:
        if prox in text_lower:
            if prox == 'mer':
                found_prox.append('Mer')
            elif prox == 'plage':
                found_prox.append('Plage')
            else:
                found_prox.append(prox.title())
    
    return list(set(found_prox))


def extract_presence_cloture(text: str) -> bool:
    """Détecte si le terrain est clôturé"""
    text_lower = text.lower()
    return 'clôturé' in text_lower or 'cloture' in text_lower


def extract_presence_front_mer(text: str) -> bool:
    """Détecte si le terrain a un front de mer"""
    text_lower = text.lower()
    return 'front de mer' in text_lower or 'bord de mer' in text_lower


def extract_zone(text: str) -> Optional[str]:
    """Extrait la zone (urbaine, rurale, etc.)"""
    text_lower = text.lower()
    
    if 'urbain' in text_lower:
        return 'Urbaine'
    elif 'péri-urbain' in text_lower or 'peri-urbain' in text_lower:
        return 'Péri-urbaine'
    elif 'rural' in text_lower:
        return 'Rurale'
    elif 'touristique' in text_lower:
        return 'Touristique'
    
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
                'type de terrain': 'type_terrain_carac',
                'constructibilité': 'constructibilite_carac',
                'livraison': 'livraison_carac',
                'statut du terrain': 'statut_terrain_carac'
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
    Extrait TOUS les champs possibles d'un listing de terrain
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
    
    # Type de terrain
    types_terrain = extract_type_terrain_from_text(all_text)
    if types_terrain:
        extracted['types_terrain'] = types_terrain
    
    # Vocation
    vocations = extract_vocation_from_text(all_text)
    if vocations:
        extracted['vocations'] = vocations
    
    # Situation juridique
    situations = extract_situation_juridique_from_text(all_text)
    if situations:
        extracted['situations_juridiques'] = situations
    
    # Viabilisation
    viabilisation = extract_viabilisation_from_text(all_text)
    if viabilisation:
        extracted['viabilisation'] = viabilisation
    
    # Constructibilité
    constructibilite = extract_constructibilite_from_text(all_text)
    if constructibilite:
        extracted['constructibilite'] = constructibilite
    
    # Topographie
    topographie = extract_topographie_from_text(all_text)
    if topographie:
        extracted['topographie'] = topographie
    
    # Orientation
    orientation = extract_orientation_from_text(all_text)
    if orientation:
        extracted['orientation'] = orientation
    
    # Vue
    vue = extract_vue_from_text(all_text)
    if vue:
        extracted['vue'] = vue
    
    # Accès
    acces = extract_acces_from_text(all_text)
    if acces:
        extracted['acces'] = acces
    
    # Proximités
    proximites = extract_proximites_from_text(all_text)
    if proximites:
        extracted['proximites'] = proximites
    
    # Clôture
    extracted['cloture'] = extract_presence_cloture(all_text)
    
    # Front de mer
    extracted['front_mer'] = extract_presence_front_mer(all_text)
    
    # Zone
    zone = extract_zone(all_text)
    if zone:
        extracted['zone'] = zone
    
    # Téléphone
    telephone = extract_telephone_from_text(all_text)
    if telephone:
        extracted['telephone_extrait'] = telephone
    
    # ===== 3. EXTRACTION DEPUIS LES CHAMPS STRUCTURÉS =====
    
    # Caracteristiques
    caracs_info = extract_from_caracteristiques(listing.get('caracteristiques'))
    if caracs_info:
        extracted.update({f"caracs_{k}": v for k, v in caracs_info.items()})
    
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
    Enrichit complètement un listing de terrain
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
    
    if extracted.get('prix_m2') and not listing.get('prix_m2'):
        enriched['prix_m2_extrait'] = extracted['prix_m2']
    
    # Surface
    if extracted.get('surface') and (not listing.get('surface') or listing.get('surface') == 0):
        enriched['surface'] = extracted['surface']
        if extracted.get('surface_text'):
            enriched['surface_text'] = extracted['surface_text']
    
    if extracted.get('surface_hectares'):
        enriched['surface_hectares'] = extracted['surface_hectares']
    
    # Types de terrain
    if extracted.get('types_terrain'):
        enriched['types_terrain_extraits'] = extracted['types_terrain']
    
    # Vocations
    if extracted.get('vocations'):
        enriched['vocations'] = extracted['vocations']
    
    # Situations juridiques
    if extracted.get('situations_juridiques'):
        enriched['situations_juridiques'] = extracted['situations_juridiques']
    
    # Viabilisation
    if extracted.get('viabilisation'):
        enriched['viabilisation'] = extracted['viabilisation']
    
    # Constructibilité
    if extracted.get('constructibilite'):
        enriched['constructibilite'] = extracted['constructibilite']
    
    # Topographie
    if extracted.get('topographie'):
        enriched['topographie'] = extracted['topographie']
    
    # Orientation
    if extracted.get('orientation'):
        enriched['orientation'] = extracted['orientation']
    
    # Vue
    if extracted.get('vue'):
        enriched['vue'] = extracted['vue']
    
    # Accès
    if extracted.get('acces'):
        enriched['acces'] = extracted['acces']
    
    # Proximités
    if extracted.get('proximites'):
        enriched['proximites'] = extracted['proximites']
    
    # Clôture
    if extracted.get('cloture') is not None:
        enriched['cloture'] = extracted['cloture']
    
    # Front de mer
    if extracted.get('front_mer') is not None:
        enriched['front_mer'] = extracted['front_mer']
    
    # Zone
    if extracted.get('zone'):
        enriched['zone'] = extracted['zone']
    
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
        'prix_m2_extraits': 0,
        'surfaces_extraites': 0,
        'types_terrain_extraits': 0,
        'vocations_extraites': 0,
        'situations_juridiques_extraites': 0,
        'viabilisation_extraite': 0,
        'constructibilite_extraite': 0,
        'proximites_extraites': 0,
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
            if enriched.get('prix_m2_extrait'):
                stats['prix_m2_extraits'] += 1
            if enriched.get('surface') and listing.get('surface') != enriched.get('surface'):
                stats['surfaces_extraites'] += 1
            if enriched.get('types_terrain_extraits'):
                stats['types_terrain_extraits'] += 1
            if enriched.get('vocations'):
                stats['vocations_extraites'] += 1
            if enriched.get('situations_juridiques'):
                stats['situations_juridiques_extraites'] += 1
            if enriched.get('viabilisation'):
                stats['viabilisation_extraite'] += 1
            if enriched.get('constructibilite'):
                stats['constructibilite_extraite'] += 1
            if enriched.get('proximites'):
                stats['proximites_extraites'] += 1
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
    print("📊 STATISTIQUES D'EXTRACTION - VENTE DE TERRAINS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Prix au m² extraits: {stats['prix_m2_extraits']}")
    print(f"✅ Surfaces extraites: {stats['surfaces_extraites']}")
    print(f"✅ Types de terrain extraits: {stats['types_terrain_extraits']}")
    print(f"✅ Vocations extraites: {stats['vocations_extraites']}")
    print(f"✅ Situations juridiques extraites: {stats['situations_juridiques_extraites']}")
    print(f"✅ Viabilisation extraite: {stats['viabilisation_extraite']}")
    print(f"✅ Constructibilité extraite: {stats['constructibilite_extraite']}")
    print(f"✅ Proximités extraites: {stats['proximites_extraites']}")
    print(f"✅ Contacts extraits: {stats['contacts_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Vente de Terrains")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file(args.file, args.output)


if __name__ == '__main__':
    main()