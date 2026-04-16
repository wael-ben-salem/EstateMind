"""
Agent d'extraction COMPLET pour Location Immobilier Neuf
Extrait TOUS les champs possibles depuis:
- description_courte, description_complete (comme avant)
- caracteristiques, caracteristiques_detaillees
- URLs des images, videos_completes
- equipements_complets, etc.
- ET les nouveaux champs spécifiques au neuf
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import unquote, urlparse, parse_qs


# ========== CONSTANTES (COMME AVANT) ==========

EQUIPEMENTS_VACANCES = [
    'terrasse', 'garage', 'ascenseur', 'concierge', 'climatisation',
    'chauffage', 'sécurité', 'double vitrage', 'porte blindée',
    'cuisine équipée', 'réfrigérateur', 'four', 'tv', 'machine à laver',
    'micro-ondes', 'internet', 'jardin', 'meublé', 'piscine', 'balcon',
    'parking', 'antenne parabolique', 'air conditionné', 'wifi', 'chauffage central',
    'spa', 'salle de sport', 'isolation', 'fibre optique', 'vidéosurveillance'
]

VILLES_TUNISIE = [
    'tunis', 'ariana', 'ben arous', 'manouba', 'nabeul', 'hammamet',
    'sousse', 'monastir', 'mahdia', 'sfax', 'gabes', 'medenine',
    'tataouine', 'gafsa', 'tozeur', 'kebili', 'kairouan', 'kasserine',
    'sidibouzid', 'kef', 'siliana', 'jendouba', 'beja', 'bizerte',
    'zaghouan', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'ennasr', 'manzah', 'aouina', 'la soukra', 'el mourouj', 'boumhel',
    'mohammedia', 'raoued', 'le kram', 'jardins de carthage'
]

# Mapping pour standardiser les types de prix
PRIX_TYPE_MAPPING = {
    "à partir de": "starting_from",
    "a partir de": "starting_from",
    "starting from": "starting_from",
    "à consulter": "on_request",
    "sur demande": "on_request",
    "prix sur demande": "on_request",
    "nous consulter": "on_request",
    "contactez-nous": "on_request"
}

# Mapping pour standardiser les standings
STANDING_MAPPING = {
    "haut standing": "high",
    "haut standing de luxe": "luxury",
    "de luxe": "luxury",
    "luxe": "luxury",
    "standing": "standard",
    "économique": "economic",
    "standing économique": "economic"
}

# Mapping pour standardiser les statuts de construction
STATUT_CONSTRUCTION_MAPPING = {
    "en cours de construction": "in_progress",
    "en cours": "in_progress",
    "finalisé": "completed",
    "livré": "completed",
    "achevée": "completed",
    "projet neuf": "new_project",
    "sur plan": "off_plan",
    "livraison immédiate": "immediate"
}


# ========== FONCTIONS D'EXTRACTION CLASSIQUES (COMME AVANT) ==========

def normalize_text(text: str) -> str:
    """Normalise le texte"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()


def extract_date_from_url(url: str) -> Optional[str]:
    """Extrait une date depuis une URL d'image"""
    if not url:
        return None
    
    try:
        decoded = unquote(url)
    except:
        decoded = url
    
    # Pattern pour WhatsApp Image avec date
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
    
    # Pattern pour date simple AAAA-MM-JJ
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


def extract_titre(description_courte: str, description_complete: str) -> Optional[str]:
    """Extrait ou améliore le titre"""
    text = f"{description_courte} {description_complete}"
    lines = text.split('.')
    if lines and len(lines[0]) < 100:
        return normalize_text(lines[0])
    return None


def extract_prix_from_text(text: str) -> Dict[str, Any]:
    """Extraction complète des prix"""
    result = {}
    text_lower = text.lower()
    
    # Vérifier si prix à consulter
    if 'prix à consulter' in text_lower or 'prix sur demande' in text_lower:
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        result['prix_type'] = 'on_request'
        return result
    
    # Patterns de prix
    prix_patterns = [
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 'TND'),
        (r'(\d[\d\s]*\.?\d*)\s*par\s*mois', 'TND'),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt|par)', 'TND'),
        (r'(\d+)\s*tnd', 'TND'),
        (r'(\d+)\s*dt\b', 'TND'),
    ]
    
    for pattern, devise in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(1).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                if 10 <= val <= 50000000:
                    result['prix'] = val
                    result['prix_text'] = f"{int(val):,} TND".replace(',', ' ')
                    
                    # Détecter si c'est un prix "à partir de"
                    if 'à partir de' in text_lower or 'a partir de' in text_lower:
                        result['prix_type'] = 'starting_from'
                    break
            except:
                continue
    
    return result


def extract_surface(text: str) -> Dict[str, Any]:
    """Extraction de la surface"""
    result = {}
    
    surface_patterns = [
        r'(\d+)\s*m[²2]',
        r'(\d+)\s*m[e]?tres?',
        r'surface\s*[:\-]?\s*(\d+)',
        r'superficie\s*[:\-]?\s*(\d+)',
    ]
    
    for p in surface_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                surface_val = float(m.group(1))
                if 10 <= surface_val <= 10000:
                    result['surface'] = surface_val
                    result['surface_text'] = f"{int(surface_val)} m²"
                    break
            except:
                continue
    
    return result


def extract_localisation(text: str) -> Dict[str, Any]:
    """Extraction ville, quartier, adresse"""
    result = {}
    text_lower = text.lower()
    
    # Extraction ville
    for ville in VILLES_TUNISIE:
        if ville in text_lower:
            result['ville'] = ville.title()
            break
    
    # Extraction quartier
    quartier_patterns = [
        (r'cit[ée]\s+([\w\s\d\-]+?)(?:\s*\.|\,|\s+derrière|$)', 1),
        (r'quartier\s+([\w\s\-]+)', 1),
        (r'à\s+([\w\s\-]+?)(?:\s*\.|\,)(?!\s*\d)', 1),
    ]
    
    for p, grp in quartier_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            q = m.group(grp) if m.lastindex and m.lastindex >= grp else m.group(0)
            q = re.sub(r'^(?:à|dans)\s+', '', q, flags=re.I).strip()
            if 2 < len(q) < 80:
                result['quartier'] = q.title()
                break
    
    # Adresse complète
    if result.get('ville') and result.get('quartier'):
        result['adresse'] = f"{result['quartier']}, {result['ville']}"
    elif result.get('quartier'):
        result['adresse'] = result['quartier']
    elif result.get('ville'):
        result['adresse'] = result['ville']
    
    return result


def extract_type_bien(text: str) -> Dict[str, Any]:
    """Extraction du type de bien"""
    result = {}
    text_lower = text.lower()
    
    type_patterns = [
        (r'appart(?:ement)?\s+s(\d+)', lambda g: f"S{g}"),
        (r'\bS(\d+)\b', lambda g: f"S{g}"),
        (r'(\d+)\s*pi[èe]ces?', lambda g: f"S{int(g)}"),
        (r'studio\b', "Studio"),
        (r'villa\b', "Villa"),
        (r'maison\b', "Maison"),
        (r'résidence\b', "Résidence"),
        (r'bureau[x]?\b', "Bureau"),
        (r'terrain\b', "Terrain"),
        (r'local commercial\b', "Local commercial"),
        (r'appart(?:ement)?\b', "Appartement"),
    ]
    
    for pattern, value in type_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if callable(value):
                try:
                    result['type_bien'] = value(m.group(1))
                except:
                    result['type_bien'] = "Appartement"
            else:
                result['type_bien'] = value
            break
    
    return result


def extract_pieces_chambres_sdb(text: str) -> Dict[str, Any]:
    """Extraction nombre de pièces, chambres, sdb"""
    result = {}
    text_lower = text.lower()
    
    # Nombre de pièces
    pieces_m = re.search(r'S(\d+)', text, re.IGNORECASE)
    if pieces_m:
        try:
            result['nombre_pieces'] = int(pieces_m.group(1))
        except:
            pass
    
    # Nombre de chambres
    chambre_patterns = [
        r'(\d+)\s*chambre[s]?',
        r'deux\s+chambres',
        r'trois\s+chambres',
        r'une\s+chambre',
    ]
    
    for p in chambre_patterns:
        m = re.search(p, text_lower)
        if m:
            if 'deux' in m.group(0):
                result['nombre_chambres'] = 2
            elif 'trois' in m.group(0):
                result['nombre_chambres'] = 3
            elif 'une' in m.group(0):
                result['nombre_chambres'] = 1
            elif m.lastindex and m.group(1).isdigit():
                result['nombre_chambres'] = int(m.group(1))
            break
    
    # Nombre de salles de bain
    sdb_patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'une\s+salle\s+de\s+bain',
        r'une\s+salle\s+d\'eau',
    ]
    
    for p in sdb_patterns:
        m = re.search(p, text_lower)
        if m:
            if 'une' in m.group(0):
                result['nombre_sdb'] = 1
            elif m.lastindex and m.group(1).isdigit():
                result['nombre_sdb'] = int(m.group(1))
            break
    
    return result


def extract_equipements(text: str) -> List[str]:
    """Extraction des équipements depuis le texte"""
    equip_found = []
    text_lower = text.lower()
    
    for eq in EQUIPEMENTS_VACANCES:
        if eq in text_lower:
            eq_title = eq.title()
            if eq_title not in equip_found:
                equip_found.append(eq_title)
    
    # Supprimer doublons
    seen = set()
    unique_equip = []
    for e in equip_found:
        if e not in seen:
            seen.add(e)
            unique_equip.append(e)
    
    return sorted(unique_equip)


def extract_from_caracteristiques(caracteristiques_json: str) -> Dict[str, Any]:
    """Extraction depuis le champ caracteristiques (JSON string)"""
    result = {}
    
    if not caracteristiques_json:
        return result
    
    try:
        if isinstance(caracteristiques_json, str):
            cleaned = caracteristiques_json.replace("'", '"')
            caracs = json.loads(cleaned)
        else:
            caracs = caracteristiques_json
        
        if isinstance(caracs, list):
            # Si c'est une liste, chaque élément est une caractéristique
            for item in caracs:
                if isinstance(item, str):
                    # Chercher des équipements dans la liste
                    equip_found = extract_equipements(item)
                    if equip_found:
                        if 'equipements_extraits' not in result:
                            result['equipements_extraits'] = []
                        result['equipements_extraits'].extend(equip_found)
        
        elif isinstance(caracs, dict):
            # Mapping des champs
            mapping = {
                'type de bien': 'type_bien',
                'etat': 'etat_bien',
                'orientation': 'orientation',
                'type du sol': 'type_sol',
                'standing': 'standing',
                'statut': 'statut_construction'
            }
            
            for old_key, new_key in mapping.items():
                if old_key in caracs and caracs[old_key]:
                    result[new_key] = caracs[old_key]
            
            # Extraire équipements
            equip_text = ' '.join([str(v) for v in caracs.values()])
            equip_found = extract_equipements(equip_text)
            if equip_found:
                result['equipements_extraits'] = equip_found
                
    except (json.JSONDecodeError, AttributeError):
        if isinstance(caracteristiques_json, str):
            equip_found = extract_equipements(caracteristiques_json)
            if equip_found:
                result['equipements_extraits'] = equip_found
    
    return result


def extract_contact_info(text: str, existing_contact: Any) -> Dict[str, Any]:
    """Extraction des informations de contact"""
    contact = {}
    
    if existing_contact:
        try:
            if isinstance(existing_contact, str):
                contact = json.loads(existing_contact)
            else:
                contact = existing_contact
        except:
            contact = {}
    
    # Patterns de téléphone
    tel_patterns = [
        r'(?:\+216|00216|216)?\s*(\d[\d\s]{7,})',
        r't[eé]l[eé]phone\s*[:\-]?\s*(\d[\d\s]{7,})',
        r'contact\s*(?:\s*:)?\s*(\d[\d\s]{7,})',
        r'whatsapp[:\s]*(\d[\d\s]{7,})',
    ]
    
    for p in tel_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            tel = re.sub(r'\s', '', m.group(1))
            if len(tel) >= 8:
                contact['telephone'] = tel
                if not tel.startswith('+216') and len(tel) == 8:
                    contact['telephone'] = f"+216{tel}"
                break
    
    # Email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    m = re.search(email_pattern, text)
    if m:
        contact['email'] = m.group(0)
    
    return contact


# ========== NOUVELLES FONCTIONS SPÉCIFIQUES AU NEUF ==========

def extract_from_caracteristiques_detaillees(caracs_json: str) -> Dict[str, Any]:
    """Extrait les données depuis caracteristiques_detaillees"""
    result = {}
    
    if not caracs_json or caracs_json == "{}":
        return result
    
    try:
        cleaned = caracs_json.replace("'", '"')
        caracs = json.loads(cleaned)
        
        if isinstance(caracs, dict):
            for key, value in caracs.items():
                key_clean = key.lower().strip().replace(' ', '_')
                
                if isinstance(value, str):
                    numbers = re.findall(r'\d+', value)
                    if numbers and key_clean in ['nombre_appartements', 'nombre_niveaux', 'surface_terrain', 'nb_appartements']:
                        result[key_clean] = int(numbers[0])
                    else:
                        result[key_clean] = value
                else:
                    result[key_clean] = value
    except:
        pass
    
    return result


def extract_videos(videos_str: str) -> List[Dict[str, Any]]:
    """Extrait les vidéos YouTube depuis videos_completes"""
    if not videos_str:
        return []
    
    videos = []
    
    if ';' in videos_str:
        urls = [url.strip() for url in videos_str.split(';') if url.strip()]
    else:
        urls = [videos_str.strip()]
    
    for url in urls:
        video_info = extract_youtube_info(url)
        if video_info:
            videos.append(video_info)
    
    return videos


def extract_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Extrait les informations d'une vidéo YouTube"""
    parsed = urlparse(url)
    video_id = None
    
    if 'youtube.com' in parsed.netloc:
        if '/embed/' in parsed.path:
            video_id = parsed.path.split('/embed/')[-1].split('?')[0]
        elif '/watch' in parsed.path:
            query = parse_qs(parsed.query)
            video_id = query.get('v', [None])[0]
    elif 'youtu.be' in parsed.netloc:
        video_id = parsed.path.lstrip('/')
    
    if video_id:
        return {
            'id': video_id,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'embed': f"https://www.youtube.com/embed/{video_id}",
            'thumbnail': f"https://img.youtube.com/vi/{video_id}/0.jpg",
            'type': 'youtube'
        }
    
    return None


def extract_promoteur_info(texte: str) -> Dict[str, Any]:
    """Extrait les informations du promoteur"""
    result = {}
    texte_lower = texte.lower()
    
    promoteur_patterns = [
        r'promoteur\s*[:\-]?\s*([^\.]+)',
        r'réalisé par\s*([^\.]+)',
        r'construit par\s*([^\.]+)',
        r'développé par\s*([^\.]+)'
    ]
    
    for pattern in promoteur_patterns:
        m = re.search(pattern, texte, re.IGNORECASE)
        if m:
            result['nom'] = m.group(1).strip()
            break
    
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, texte)
    if urls:
        result['site_web'] = urls[0]
    
    return result


def extract_prix_m2(prix: float, surface: float) -> Optional[float]:
    """Calcule le prix au m²"""
    if prix and surface and surface > 0:
        return round(prix / surface, 2)
    return None


def extract_nombre_appartements(texte: str) -> Optional[int]:
    """Extrait le nombre d'appartements depuis le texte"""
    texte_lower = texte.lower()
    
    patterns = [
        r'(\d+)\s*appartement[s]?',
        r'(\d+)\s*logement[s]?',
        r'programme de\s*(\d+)\s*appart',
        r'(\d+)\s*unités?'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, texte_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_date_livraison(texte: str) -> Optional[str]:
    """Extrait la date de livraison depuis le texte"""
    patterns = [
        r'livraison\s*[:\-]?\s*(\d{4})',
        r'livrable en\s*(\d{4})',
        r'prévue pour\s*(\d{4})',
        r'remise des clés\s*[:\-]?\s*(\d{4})'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, texte, re.IGNORECASE)
        if m:
            return m.group(1)
    
    return None


def extract_standing_from_text(texte: str) -> Optional[str]:
    """Extrait le standing depuis le texte"""
    texte_lower = texte.lower()
    
    if 'haut standing' in texte_lower or 'haut standing de luxe' in texte_lower:
        return 'Haut standing'
    elif 'de luxe' in texte_lower or 'luxe' in texte_lower:
        return 'De luxe'
    elif 'standing' in texte_lower:
        return 'Standard'
    elif 'économique' in texte_lower:
        return 'Économique'
    
    return None


def extract_statut_construction_from_text(texte: str) -> Optional[str]:
    """Extrait le statut de construction depuis le texte"""
    texte_lower = texte.lower()
    
    if 'en cours de construction' in texte_lower or 'en cours' in texte_lower:
        return 'En cours de construction'
    elif 'finalisé' in texte_lower or 'livré' in texte_lower or 'achevée' in texte_lower:
        return 'Finalisé'
    elif 'sur plan' in texte_lower:
        return 'Sur plan'
    elif 'livraison immédiate' in texte_lower:
        return 'Livraison immédiate'
    
    return None


def extract_nom_agence_from_logo(logo_url: str) -> Optional[str]:
    """Extrait le nom de l'agence depuis l'URL du logo"""
    if not logo_url or 'logo' not in logo_url.lower():
        return None
    
    try:
        decoded = unquote(logo_url)
        # Chercher un nom entre / et Logo
        pattern = r'/([^/]+?)[-_][lL]ogo'
        match = re.search(pattern, decoded)
        if match:
            nom = match.group(1).replace('-', ' ').replace('_', ' ').title()
            return nom
    except:
        pass
    
    return None


# ========== FONCTION PRINCIPALE D'EXTRACTION ==========

def extract_all_from_listing_neuf(listing: Dict) -> Dict[str, Any]:
    """
    Extrait TOUS les champs possibles d'un listing immobilier neuf
    - Extraction classique (descriptions)
    - Extraction spécifique au neuf
    """
    desc_c = listing.get('description_courte', '') or ''
    desc_f = listing.get('description_complete', '') or ''
    caracs = listing.get('caracteristiques', '') or ''
    caracs_det = listing.get('caracteristiques_detaillees', '') or ''
    
    all_text = f"{desc_c} {desc_f}".strip()
    
    extracted = {}
    
    # ===== 1. EXTRACTION CLASSIQUE (comme avant) =====
    
    # Date depuis images
    images_field = listing.get('images', '')
    images_completes = listing.get('images_completes', '')
    
    all_images = []
    if isinstance(images_field, str):
        all_images.extend([img.strip() for img in images_field.split(';') if img.strip()])
    elif isinstance(images_field, list):
        all_images.extend(images_field)
    
    if isinstance(images_completes, str):
        all_images.extend([img.strip() for img in images_completes.split(';') if img.strip()])
    elif isinstance(images_completes, list):
        all_images.extend(images_completes)
    
    dates = []
    for img in all_images:
        date = extract_date_from_url(img)
        if date:
            dates.append(date)
    
    if dates:
        dates.sort()
        extracted['date_publication'] = dates[0]
    
    # Titre amélioré
    titre_extrait = extract_titre(desc_c, desc_f)
    if titre_extrait:
        extracted['titre_ameliore'] = titre_extrait
    
    # Prix
    prix_info = extract_prix_from_text(all_text)
    extracted.update(prix_info)
    
    # Surface
    surface_info = extract_surface(all_text)
    extracted.update(surface_info)
    
    # Localisation
    loc_info = extract_localisation(all_text)
    extracted.update(loc_info)
    
    # Type de bien
    type_info = extract_type_bien(all_text)
    extracted.update(type_info)
    
    # Pièces, chambres, sdb
    pieces_info = extract_pieces_chambres_sdb(all_text)
    extracted.update(pieces_info)
    
    # Équipements depuis texte
    equip_found = extract_equipements(all_text)
    if equip_found:
        extracted['equipements_extraits'] = equip_found
    
    # Depuis caracteristiques
    caracs_info = extract_from_caracteristiques(caracs)
    extracted.update(caracs_info)
    
    if 'equipements_extraits' in caracs_info:
        if 'equipements_extraits' in extracted:
            all_equip = list(set(extracted['equipements_extraits'] + caracs_info['equipements_extraits']))
            extracted['equipements_extraits'] = sorted(all_equip)
    
    # Contact info
    contact_info = extract_contact_info(all_text, listing.get('contact_info'))
    if contact_info:
        extracted['contact_info_extrait'] = contact_info
    
    # ===== 2. EXTRACTION SPÉCIFIQUE AU NEUF =====
    
    # Depuis caracteristiques_detaillees
    caracs_det_info = extract_from_caracteristiques_detaillees(caracs_det)
    if caracs_det_info:
        extracted['caracteristiques_detaillees_parse'] = caracs_det_info
    
    # Vidéos
    if listing.get('videos_completes'):
        videos = extract_videos(listing['videos_completes'])
        if videos:
            extracted['videos_parse'] = videos
    
    # Promoteur info
    promoteur_info = extract_promoteur_info(all_text)
    if promoteur_info:
        extracted['promoteur_info_extrait'] = promoteur_info
    
    # Nombre d'appartements
    nb_appart = extract_nombre_appartements(all_text)
    if nb_appart:
        extracted['nombre_appartements_extrait'] = nb_appart
    
    # Date livraison
    date_livraison = extract_date_livraison(all_text)
    if date_livraison:
        extracted['date_livraison_extrait'] = date_livraison
    
    # Standing depuis texte (si pas déjà présent)
    if not listing.get('standing'):
        standing = extract_standing_from_text(all_text)
        if standing:
            extracted['standing_extrait'] = standing
    
    # Statut construction depuis texte (si pas déjà présent)
    if not listing.get('statut_construction'):
        statut = extract_statut_construction_from_text(all_text)
        if statut:
            extracted['statut_construction_extrait'] = statut
    
    # Nom agence depuis logo
    if listing.get('logo_agence') and not listing.get('nom_agence'):
        nom_agence = extract_nom_agence_from_logo(listing['logo_agence'])
        if nom_agence:
            extracted['nom_agence_extrait'] = nom_agence
    
    # Prix au m² calculé
    prix = extracted.get('prix') or listing.get('prix')
    surface = extracted.get('surface') or listing.get('surface')
    if prix and surface:
        prix_m2 = extract_prix_m2(prix, surface)
        if prix_m2:
            extracted['prix_m2_calcule'] = prix_m2
    
    return extracted


def enrich_listing_neuf_complet(listing: Dict) -> Dict:
    """
    Enrichit complètement un listing immobilier neuf
    """
    extracted = extract_all_from_listing_neuf(listing)
    
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
        enriched['prix_text'] = extracted.get('prix_text', listing.get('prix_text'))
    
    if extracted.get('prix_type'):
        enriched['prix_type'] = extracted['prix_type']
    
    # Prix au m²
    if extracted.get('prix_m2_calcule'):
        if not listing.get('prix_m2') or listing.get('prix_m2') == 0:
            enriched['prix_m2'] = extracted['prix_m2_calcule']
    
    # Surface
    if extracted.get('surface') and not listing.get('surface'):
        enriched['surface'] = extracted['surface']
        enriched['surface_text'] = extracted.get('surface_text', listing.get('surface_text'))
    
    # Localisation
    if extracted.get('ville') and not listing.get('ville'):
        enriched['ville'] = extracted['ville']
    if extracted.get('quartier') and not listing.get('quartier'):
        enriched['quartier'] = extracted['quartier']
    if extracted.get('adresse') and not listing.get('adresse'):
        enriched['adresse'] = extracted['adresse']
    
    # Type de bien
    if extracted.get('type_bien') and not listing.get('type_bien'):
        enriched['type_bien'] = extracted['type_bien']
    
    # Pièces, chambres, sdb
    for field in ['nombre_pieces', 'nombre_chambres', 'nombre_sdb']:
        if extracted.get(field) and not listing.get(field):
            enriched[field] = extracted[field]
    
    # Équipements
    if extracted.get('equipements_extraits'):
        current_equip = listing.get('equipements', [])
        if isinstance(current_equip, str):
            current_equip = [e.strip() for e in current_equip.split(';') if e.strip()]
        elif not isinstance(current_equip, list):
            current_equip = []
        
        all_equip = list(set(current_equip + extracted['equipements_extraits']))
        enriched['equipements'] = sorted(all_equip)
    
    # Contact info
    if extracted.get('contact_info_extrait'):
        current_contact = listing.get('contact_info', {})
        if isinstance(current_contact, str):
            try:
                current_contact = json.loads(current_contact)
            except:
                current_contact = {}
        
        current_contact.update(extracted['contact_info_extrait'])
        enriched['contact_info'] = json.dumps(current_contact, ensure_ascii=False)
    
    # Caracteristiques detaillées
    if extracted.get('caracteristiques_detaillees_parse'):
        enriched['caracteristiques_detaillees'] = json.dumps(extracted['caracteristiques_detaillees_parse'], ensure_ascii=False)
    
    # Vidéos
    if extracted.get('videos_parse'):
        enriched['videos_parse'] = extracted['videos_parse']
    
    # Promoteur info
    if extracted.get('promoteur_info_extrait'):
        try:
            promoteur_info = json.loads(listing.get('promoteur_info', '{}')) if isinstance(listing.get('promoteur_info'), str) else listing.get('promoteur_info', {})
            if not promoteur_info:
                promoteur_info = {}
            promoteur_info.update(extracted['promoteur_info_extrait'])
            enriched['promoteur_info'] = json.dumps(promoteur_info, ensure_ascii=False)
        except:
            pass
    
    # Nombre d'appartements
    if extracted.get('nombre_appartements_extrait') and not listing.get('nombre_appartements'):
        enriched['nombre_appartements'] = extracted['nombre_appartements_extrait']
    
    # Date livraison
    if extracted.get('date_livraison_extrait') and not listing.get('date_livraison'):
        enriched['date_livraison'] = extracted['date_livraison_extrait']
    
    # Standing extrait
    if extracted.get('standing_extrait') and not listing.get('standing'):
        enriched['standing'] = extracted['standing_extrait']
    
    # Statut construction extrait
    if extracted.get('statut_construction_extrait') and not listing.get('statut_construction'):
        enriched['statut_construction'] = extracted['statut_construction_extrait']
    
    # Nom agence extrait
    if extracted.get('nom_agence_extrait') and not listing.get('nom_agence'):
        enriched['nom_agence'] = extracted['nom_agence_extrait']
    
    return enriched


def process_json_file_neuf_complet(input_path: str, output_path: Optional[str] = None) -> int:
    """
    Charge le JSON, enrichit complètement chaque listing, sauvegarde
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
        'localisations_extraites': 0,
        'equipements_ajoutes': 0,
        'caracs_detaillees': 0,
        'videos_parsees': 0,
        'promoteurs_extraits': 0,
        'nombres_appartements': 0,
        'dates_livraison': 0,
        'prix_m2_calcules': 0,
        'standings_extraits': 0,
        'statuts_extraits': 0,
        'noms_agence_extraits': 0
    }
    
    for listing in listings:
        try:
            enriched = enrich_listing_neuf_complet(listing)
            enriched_listings.append(enriched)
            
            # Statistiques
            if enriched.get('date_publication'):
                stats['dates_publication'] += 1
            if enriched.get('prix') and listing.get('prix') != enriched.get('prix'):
                stats['prix_extraits'] += 1
            if enriched.get('surface') and listing.get('surface') != enriched.get('surface'):
                stats['surfaces_extraites'] += 1
            if enriched.get('ville') and not listing.get('ville'):
                stats['localisations_extraites'] += 1
            if len(enriched.get('equipements', [])) > len(listing.get('equipements', [])):
                stats['equipements_ajoutes'] += 1
            if enriched.get('caracteristiques_detaillees') and enriched['caracteristiques_detaillees'] != "{}":
                stats['caracs_detaillees'] += 1
            if enriched.get('videos_parse'):
                stats['videos_parsees'] += 1
            if enriched.get('promoteur_info') and enriched['promoteur_info'] != "{}":
                stats['promoteurs_extraits'] += 1
            if enriched.get('nombre_appartements'):
                stats['nombres_appartements'] += 1
            if enriched.get('date_livraison'):
                stats['dates_livraison'] += 1
            if enriched.get('prix_m2') and listing.get('prix_m2') == 0:
                stats['prix_m2_calcules'] += 1
            if enriched.get('standing') and not listing.get('standing'):
                stats['standings_extraits'] += 1
            if enriched.get('statut_construction') and not listing.get('statut_construction'):
                stats['statuts_extraits'] += 1
            if enriched.get('nom_agence') and not listing.get('nom_agence'):
                stats['noms_agence_extraits'] += 1
                
        except Exception as e:
            print(f"❌ Erreur listing {listing.get('id', '?')}: {e}")
            enriched_listings.append(listing)
    
    data['listings'] = enriched_listings
    
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['extraction_complete_date'] = datetime.now().isoformat() + 'Z'
    data['metadata']['listings_traites'] = len(enriched_listings)
    data['metadata']['statistiques_extraction'] = stats
    
    out = output_path or str(path.parent / f"{path.stem}_extrait_complet.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES D'EXTRACTION COMPLÈTE - IMMOBILIER NEUF")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Dates publication extraites: {stats['dates_publication']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Surfaces extraites: {stats['surfaces_extraites']}")
    print(f"✅ Localisations extraites: {stats['localisations_extraites']}")
    print(f"✅ Équipements ajoutés: {stats['equipements_ajoutes']}")
    print(f"✅ Caractéristiques détaillées parsées: {stats['caracs_detaillees']}")
    print(f"✅ Vidéos parsées: {stats['videos_parsees']}")
    print(f"✅ Promoteurs extraits: {stats['promoteurs_extraits']}")
    print(f"✅ Nombres d'appartements extraits: {stats['nombres_appartements']}")
    print(f"✅ Dates livraison extraites: {stats['dates_livraison']}")
    print(f"✅ Prix au m² calculés: {stats['prix_m2_calcules']}")
    print(f"✅ Standings extraits: {stats['standings_extraits']}")
    print(f"✅ Statuts construction extraits: {stats['statuts_extraits']}")
    print(f"✅ Noms agence extraits: {stats['noms_agence_extraits']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction COMPLET pour Location Immobilier Neuf")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file_neuf_complet(args.file, args.output)


if __name__ == '__main__':
    main()