"""
Agent d'extraction amélioré - Location Vacances
Extrait tous les champs possibles depuis description_courte, description_complete, caracteristiques et URLs des images
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import unicodedata
from urllib.parse import unquote


# Équipements connus pour extraction depuis le texte
EQUIPEMENTS_VACANCES = [
    'terrasse', 'garage', 'ascenseur', 'concierge', 'climatisation',
    'chauffage', 'sécurité', 'double vitrage', 'porte blindée',
    'cuisine équipée', 'réfrigérateur', 'four', 'tv', 'machine à laver',
    'micro-ondes', 'internet', 'jardin', 'meublé', 'piscine', 'balcon',
    'parking', 'antenne parabolique', 'air conditionné', 'wifi', 'chauffage central'
]

# Villes tunisiennes connues
VILLES_TUNISIE = [
    'tunis', 'ariana', 'ben arous', 'manouba', 'nabeul', 'hammamet',
    'sousse', 'monastir', 'mahdia', 'sfax', 'gabes', 'medenine',
    'tataouine', 'gafsa', 'tozeur', 'kebili', 'kairouan', 'kasserine',
    'sidibouzid', 'kef', 'siliana', 'jendouba', 'beja', 'bizerte',
    'zaghouan', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'ennasr', 'manzah', 'aouina', 'la soukra', 'el mourouj'
]


def normalize_text(text: str) -> str:
    """Normalise le texte (enlève les espaces multiples, nettoie)"""
    if not text:
        return ""
    # Remplacer les retours à la ligne et tabs par des espaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_date_from_url(url: str) -> Optional[str]:
    """
    Extrait une date depuis une URL d'image
    Formats recherchés :
    - WhatsApp%20Image%20AAAA-MM-JJ%20at%20HH.MM.SS
    - AAAA-MM-JJ
    - timestamp dans l'URL
    """
    if not url:
        return None
    
    # Décoder l'URL (pour gérer %20 etc.)
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
                # Valider que c'est une date valide
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
    
    # Pattern pour timestamp (nombre à 10 chiffres)
    timestamp_pattern = r'[/_](\d{10})[/_]'
    m = re.search(timestamp_pattern, url)
    if m:
        try:
            timestamp = int(m.group(1))
            # Convertir timestamp en date
            date = datetime.fromtimestamp(timestamp)
            return date.strftime('%Y-%m-%d')
        except:
            pass
    
    return None


def extract_date_publication(images_field: Any) -> Optional[str]:
    """
    Extrait la date de publication la plus ancienne depuis les URLs des images
    """
    if not images_field:
        return None
    
    # Convertir en liste d'URLs
    urls = []
    if isinstance(images_field, list):
        urls = images_field
    elif isinstance(images_field, str):
        if ';' in images_field:
            urls = [img.strip() for img in images_field.split(';') if img.strip()]
        else:
            urls = [images_field]
    
    dates = []
    for url in urls:
        date = extract_date_from_url(url)
        if date:
            dates.append(date)
    
    if dates:
        # Retourner la date la plus ancienne (première publication)
        dates.sort()
        return dates[0]
    
    return None


def extract_titre(description_courte: str, description_complete: str) -> Optional[str]:
    """Extrait ou améliore le titre"""
    text = f"{description_courte} {description_complete}"
    
    # Chercher un titre potentiel dans les premières lignes
    lines = text.split('.')
    if lines and len(lines[0]) < 100:
        return normalize_text(lines[0])
    
    return None


def extract_prix_from_text(text: str) -> Dict[str, Any]:
    """Extraction complète des prix avec normalisation"""
    result = {}
    text_lower = text.lower()
    
    # Vérifier d'abord si le prix est à consulter
    if 'prix à consulter' in text_lower or 'prix sur demande' in text_lower:
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
        return result
    
    # Patterns de prix avec différentes devises
    prix_patterns = [
        # TND / DT
        (r'(\d[\d\s]*\.?\d*)\s*(?:tnd|dt|dinars?)\b', 'TND'),
        (r'(\d[\d\s]*\.?\d*)\s*par\s*mois', 'TND'),
        (r'prix\s*[:\-]?\s*(\d[\d\s\.]+)\s*(?:tnd|dt|par)', 'TND'),
        (r'(\d+)\s*tnd', 'TND'),
        (r'(\d+)\s*dt\b', 'TND'),
        # Euro
        (r'(\d+)\s*euro[s]?\b', 'EUR'),
        (r'(\d+)\s*€\b', 'EUR'),
        # Dollar
        (r'(\d+)\s*usd\b', 'USD'),
        (r'(\d+)\s*dollar[s]?\b', 'USD'),
    ]
    
    for pattern, devise in prix_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                prix_str = m.group(1).replace(' ', '').replace(',', '.')
                val = float(prix_str)
                if 10 <= val <= 50000:
                    result['prix'] = val
                    # Générer prix_text formaté en français
                    if devise == 'TND':
                        # Format français: espace comme séparateur de milliers
                        result['prix_text'] = f"{int(val):,} TND".replace(',', ' ')
                    elif devise == 'EUR':
                        result['prix_text'] = f"{int(val)} €"
                    elif devise == 'USD':
                        result['prix_text'] = f"{int(val)} USD"
                    break
            except:
                continue
    
    # Si aucun prix trouvé mais que le texte suggère un prix à consulter
    if 'prix' not in result and ('contactez' in text_lower or 'appelez' in text_lower):
        result['prix'] = 0
        result['prix_text'] = 'Prix à consulter'
    
    # Prix par jour
    prix_jour_patterns = [
        r'(\d+)\s*(?:tnd|dt)\s*[\/\s]?\s*jour',
        r'(\d+)\s*euro[s]?\s*[\/\s]?\s*jour',
        r'(\d+)\s*€\s*[\/\s]?\s*jour',
        r'(\d+)\s*dt\s*/\s*jour',
        r'(\d+)\s*par\s*jour',
    ]
    for p in prix_jour_patterns:
        m = re.search(p, text_lower)
        if m:
            try:
                result['prix_par_jour'] = float(m.group(1))
                break
            except:
                continue
    
    return result


def extract_surface(text: str) -> Dict[str, Any]:
    """Extraction normalisée de la surface"""
    result = {}
    
    surface_patterns = [
        r'(\d+)\s*m[²2]',
        r'(\d+)\s*m[e]?tres?',
        r'surface\s*[:\-]?\s*(\d+)',
        r'superficie\s*[:\-]?\s*(\d+)',
        r'(\d+)\s*m\s*carre',
    ]
    
    for p in surface_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                surface_val = float(m.group(1))
                if 10 <= surface_val <= 1000:
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
    
    # Extraction quartier (patterns spécifiques)
    quartier_patterns = [
        (r'cit[ée]\s+([\w\s\d\-]+?)(?:\s*\.|\,|\s+derrière|$)', 1),
        (r'quartier\s+([\w\s\-]+)', 1),
        (r'à\s+([\w\s\-]+?)(?:\s*\.|\,)(?!\s*\d)', 1),
        (r'dans\s+([\w\s\-]+?)(?:\s*\.|\,)', 1),
    ]
    
    for p, grp in quartier_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            q = m.group(grp) if m.lastindex and m.lastindex >= grp else m.group(0)
            q = re.sub(r'^(?:à|dans)\s+', '', q, flags=re.I).strip()
            if 2 < len(q) < 80:
                result['quartier'] = q.title()
                break
    
    # Essayer de construire une adresse complète
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
        (r'(\d+)\s*pi[èe]ces?', lambda g: f"S{int(g)}" if int(g) > 0 else "Studio"),
        (r'studio\b', "Studio"),
        (r'villa\b', "Villa"),
        (r'maison\b', "Maison"),
        (r'dar\b', "Dar"),
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
    
    # Nombre de pièces depuis S1, S2, etc.
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
        r'(\d+)\s*bedroom',
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
        r'(\d+)\s*bathroom',
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


def extract_capacite_nuits(text: str) -> Dict[str, Any]:
    """Extraction capacité et nuits minimum"""
    result = {}
    text_lower = text.lower()
    
    # Capacité (personnes)
    cap_patterns = [
        r'(\d+)\s*personne[s]?',
        r'capacit[ée]\s*[:\-]?\s*(\d+)',
        r'(\d+)\s*place[s]?',
        r'pour\s*(\d+)\s*personne',
        r'(\d+)\s*guests?',
    ]
    
    for p in cap_patterns:
        m = re.search(p, text_lower)
        if m:
            try:
                result['capacite'] = int(m.group(1))
                break
            except:
                continue
    
    # Nuits minimum
    nuits_patterns = [
        r'(\d+)\s*nuit[s]?\s*minimum',
        r'minimum\s*(\d+)\s*nuit',
        r'(\d+)\s*nuit[s]?\s*min',
        r'location\s*(?:à partir de|min)\s*(\d+)\s*nuit',
        r'(\d+)\s*nights?\s*min',
    ]
    
    for p in nuits_patterns:
        m = re.search(p, text_lower)
        if m:
            try:
                result['nuits_minimum'] = int(m.group(1))
                break
            except:
                continue
    
    # Détection type location
    if 'toute l\'année' in text_lower or 'location annuelle' in text_lower:
        result['type_location'] = 'Location annuelle'
        if 'nuits_minimum' not in result:
            result['nuits_minimum'] = 30
    elif 'saison' in text_lower or 'vacances' in text_lower:
        result['type_location'] = 'Location saisonnière'
    elif 'par mois' in text_lower:
        if 'nuits_minimum' not in result:
            result['nuits_minimum'] = 30
    
    return result


def extract_etage_residence(text: str) -> Dict[str, Any]:
    """Extraction étage et résidence"""
    result = {}
    text_lower = text.lower()
    
    # Étage
    etage_patterns = [
        r'(\d+)[eè]me?\s*[eé]tage',
        r'au\s+(\d+)[eè]me?\s*[eé]tage',
        r'[eé]tage\s*[:\-]?\s*(\d+)',
        r'(\d+)[ea]?\s*floor',
    ]
    
    for p in etage_patterns:
        m = re.search(p, text_lower)
        if m:
            result['etage'] = m.group(1)
            break
    
    if not result.get('etage'):
        if 'rdc' in text_lower or 'rez-de-chaussée' in text_lower:
            result['etage'] = 'RDC'
    
    # Résidence
    res_m = re.search(r'r[ée]sidence\s+([\w\s\-]+)', text_lower)
    if res_m:
        result['residence'] = res_m.group(1).strip().title()
    
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
    
    # Mapping pour normalisation
    eq_map = {
        'air conditionné': 'Climatisation',
        'wifi': 'Internet',
        'chauffage central': 'Chauffage central',
        'machine à laver': 'Machine à laver',
        'micro-ondes': 'Micro-ondes',
        'double vitrage': 'Double vitrage',
        'porte blindée': 'Porte blindée',
        'cuisine équipée': 'Cuisine équipée'
    }
    
    equip_found = [eq_map.get(e.lower(), e) for e in equip_found]
    
    # Supprimer les doublons tout en préservant l'ordre
    seen = set()
    unique_equip = []
    for e in equip_found:
        if e not in seen:
            seen.add(e)
            unique_equip.append(e)
    
    return unique_equip


def extract_from_caracteristiques(caracteristiques_json: str) -> Dict[str, Any]:
    """Extraction depuis le champ caracteristiques (JSON string)"""
    result = {}
    
    if not caracteristiques_json:
        return result
    
    try:
        # Si c'est une chaîne JSON
        if isinstance(caracteristiques_json, str):
            # Nettoyer la chaîne JSON (parfois mal formatée)
            cleaned = caracteristiques_json.replace("'", '"')
            caracs = json.loads(cleaned)
        else:
            caracs = caracteristiques_json
        
        # Mapping des champs caractéristiques vers nos champs standards
        mapping = {
            'type de bien': 'type_bien',
            'etat': 'etat_bien',
            'orientation': 'orientation',
            'type du sol': 'type_sol',
            'étage du bien': 'etage',
            'nombre de chambres': 'nombre_chambres',
            'nombre de pièces': 'nombre_pieces',
            'surface': 'surface',
            'capacité': 'capacite'
        }
        
        for old_key, new_key in mapping.items():
            if old_key in caracs and caracs[old_key]:
                result[new_key] = caracs[old_key]
        
        # Extraire aussi les équipements depuis les caractéristiques
        equipements_text = ' '.join([str(v) for v in caracs.values()])
        equip_found = extract_equipements(equipements_text)
        if equip_found:
            result['equipements_extraits'] = equip_found
            
    except (json.JSONDecodeError, AttributeError):
        # Si ce n'est pas du JSON valide, chercher des patterns dans le texte
        if isinstance(caracteristiques_json, str):
            equip_found = extract_equipements(caracteristiques_json)
            if equip_found:
                result['equipements_extraits'] = equip_found
    
    return result


def extract_images(images_field: Any) -> List[str]:
    """Normalise le champ images en liste"""
    if not images_field:
        return []
    
    if isinstance(images_field, list):
        return images_field
    elif isinstance(images_field, str):
        # Séparer par ; ou espace
        if ';' in images_field:
            return [img.strip() for img in images_field.split(';') if img.strip()]
        else:
            return [images_field]
    else:
        return []


def extract_contact_info(text: str, existing_contact: Any) -> Dict[str, Any]:
    """Extraction améliorée des informations de contact"""
    contact = {}
    
    # Si contact_info existe déjà et est une chaîne JSON, la parser
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
        r'(\d{2}\s*\d{3}\s*\d{3})',
        r'(\d{8,})',  # 8 chiffres ou plus
    ]
    
    for p in tel_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            tel = re.sub(r'\s', '', m.group(1))
            if len(tel) >= 8:
                contact['telephone'] = tel
                # Nettoyer le numéro
                if not tel.startswith('+216') and len(tel) == 8:
                    contact['telephone'] = f"+216{tel}"
                break
    
    # Email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    m = re.search(email_pattern, text)
    if m:
        contact['email'] = m.group(0)
    
    return contact


def merge_values(current: Any, new: Any, field: str) -> Any:
    """
    Fusion intelligente des valeurs :
    - Garde la valeur existante si elle est non vide
    - Si nouvelle valeur différente, la conserve dans un champ dédié
    """
    # Si la valeur actuelle est vide, prendre la nouvelle
    if current is None or current == '' or current == 0 or current == [] or current == {}:
        return new
    
    # Si la nouvelle valeur est vide, garder l'actuelle
    if new is None or new == '' or new == 0 or new == [] or new == {}:
        return current
    
    # Si les deux valeurs existent et sont différentes
    if new != current:
        # Pour les nombres, garder la valeur existante mais noter la différence
        if isinstance(current, (int, float)) and isinstance(new, (int, float)):
            if abs(current - new) > 0.01:  # Différence significative
                # On garde la valeur existante
                return current
        # Pour les listes, fusionner sans doublons
        elif isinstance(current, list) and isinstance(new, list):
            merged = current.copy()
            for item in new:
                if item not in merged:
                    merged.append(item)
            return merged
        # Pour les dicts, fusionner récursivement
        elif isinstance(current, dict) and isinstance(new, dict):
            merged = current.copy()
            for k, v in new.items():
                if k not in merged:
                    merged[k] = v
            return merged
    
    return current


def extract_all_from_descriptions(listing: Dict) -> Dict[str, Any]:
    """
    Extrait tous les champs possibles depuis description_courte, 
    description_complete, caracteristiques et URLs des images
    """
    desc_c = listing.get('description_courte', '') or ''
    desc_f = listing.get('description_complete', '') or ''
    caracs = listing.get('caracteristiques', '') or ''
    images = listing.get('images', '') or ''
    
    # Concaténer toutes les sources textuelles
    all_text = f"{desc_c} {desc_f}".strip()
    
    extracted = {}
    
    # Extraire date de publication depuis les images
    date_pub = extract_date_publication(images)
    if date_pub:
        extracted['date_publication'] = date_pub
    
    # Extraire titre amélioré
    titre_extrait = extract_titre(desc_c, desc_f)
    if titre_extrait:
        extracted['titre_ameliore'] = titre_extrait
    
    # Extraire prix
    prix_info = extract_prix_from_text(all_text)
    extracted.update(prix_info)
    
    # Extraire surface
    surface_info = extract_surface(all_text)
    extracted.update(surface_info)
    
    # Extraire localisation
    loc_info = extract_localisation(all_text)
    extracted.update(loc_info)
    
    # Extraire type de bien
    type_info = extract_type_bien(all_text)
    extracted.update(type_info)
    
    # Extraire pièces, chambres, sdb
    pieces_info = extract_pieces_chambres_sdb(all_text)
    extracted.update(pieces_info)
    
    # Extraire capacité et nuits
    capacite_info = extract_capacite_nuits(all_text)
    extracted.update(capacite_info)
    
    # Extraire étage et résidence
    etage_info = extract_etage_residence(all_text)
    extracted.update(etage_info)
    
    # Extraire équipements
    equip_found = extract_equipements(all_text)
    if equip_found:
        extracted['equipements_extraits'] = equip_found
        extracted['amenities_vacances_extraits'] = equip_found
    
    # Extraire depuis caracteristiques
    caracs_info = extract_from_caracteristiques(caracs)
    extracted.update(caracs_info)
    
    # Si des équipements ont été trouvés dans caracteristiques, les fusionner
    if 'equipements_extraits' in caracs_info:
        if 'equipements_extraits' in extracted:
            # Fusionner les deux listes
            all_equip = list(set(extracted['equipements_extraits'] + caracs_info['equipements_extraits']))
            extracted['equipements_extraits'] = all_equip
            extracted['amenities_vacances_extraits'] = all_equip
    
    # Extraire contact info
    contact_info = extract_contact_info(all_text, listing.get('contact_info'))
    if contact_info:
        extracted['contact_info_extrait'] = contact_info
    
    # Déterminer type_location
    if 'type_location' not in extracted:
        if 'vacances' in all_text.lower() or 'saison' in all_text.lower():
            extracted['type_location'] = 'Location vacances'
        elif 'année' in all_text.lower() or 'annuel' in all_text.lower():
            extracted['type_location'] = 'Location annuelle'
    
    return extracted


def enrich_listing_complet(listing: Dict) -> Dict:
    """
    Enrichit complètement un listing avec fusion intelligente des données
    """
    # Extraire toutes les données disponibles
    extracted = extract_all_from_descriptions(listing)
    
    # Créer une copie du listing original
    enriched = listing.copy()
    
    # Ajouter la date de publication si trouvée
    if extracted.get('date_publication'):
        enriched['date_publication'] = extracted['date_publication']
    
    # Mapping des champs extraits vers les champs du listing
    field_mapping = {
        'prix': 'prix',
        'prix_text': 'prix_text',
        'prix_par_jour': 'prix_par_jour',
        'surface': 'surface',
        'surface_text': 'surface_text',
        'ville': 'ville',
        'quartier': 'quartier',
        'adresse': 'adresse',
        'type_bien': 'type_bien',
        'type_location': 'type_location',
        'nombre_pieces': 'nombre_pieces',
        'nombre_chambres': 'nombre_chambres',
        'nombre_sdb': 'nombre_sdb',
        'capacite': 'capacite',
        'nuits_minimum': 'nuits_minimum',
        'etage': 'etage',
        'residence': 'residence',
        'orientation': 'orientation',
        'type_sol': 'type_sol',
        'etat_bien': 'etat_bien'
    }
    
    # Fusionner les valeurs
    for ext_key, list_key in field_mapping.items():
        if ext_key in extracted:
            current_val = listing.get(list_key)
            new_val = extracted[ext_key]
            enriched[list_key] = merge_values(current_val, new_val, list_key)
    
    # Fusionner les équipements
    if extracted.get('equipements_extraits'):
        current_equip = listing.get('equipements', [])
        if isinstance(current_equip, str):
            current_equip = [e.strip() for e in current_equip.split(';') if e.strip()]
        elif not isinstance(current_equip, list):
            current_equip = []
        
        merged_equip = merge_values(current_equip, extracted['equipements_extraits'], 'equipements')
        enriched['equipements'] = merged_equip
    
    # Fusionner amenities_vacances
    if extracted.get('amenities_vacances_extraits'):
        current_amenities = listing.get('amenities_vacances', [])
        if isinstance(current_amenities, str):
            current_amenities = [e.strip() for e in current_amenities.split(';') if e.strip()]
        elif not isinstance(current_amenities, list):
            current_amenities = []
        
        merged_amenities = merge_values(current_amenities, extracted['amenities_vacances_extraits'], 'amenities_vacances')
        enriched['amenities_vacances'] = merged_amenities
    
    # Fusionner les informations de contact
    if extracted.get('contact_info_extrait'):
        current_contact = listing.get('contact_info', {})
        if isinstance(current_contact, str):
            try:
                current_contact = json.loads(current_contact)
            except:
                current_contact = {}
        
        merged_contact = merge_values(current_contact, extracted['contact_info_extrait'], 'contact_info')
        enriched['contact_info'] = json.dumps(merged_contact, ensure_ascii=False)
    
    # Améliorer le titre si nécessaire
    if extracted.get('titre_ameliore') and (not listing.get('titre') or len(listing.get('titre', '')) < len(extracted['titre_ameliore'])):
        enriched['titre'] = extracted['titre_ameliore']
    
    # Normaliser les images
    enriched['images'] = extract_images(listing.get('images', []))
    
    return enriched


def process_json_file_complet(input_path: str, output_path: Optional[str] = None) -> int:
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
        'dates_publication_trouvees': 0,
        'prix_extraits': 0,
        'equipements_ajoutes': 0
    }
    
    for listing in listings:
        try:
            enriched = enrich_listing_complet(listing)
            enriched_listings.append(enriched)
            
            # Statistiques
            if enriched.get('date_publication'):
                stats['dates_publication_trouvees'] += 1
            if enriched.get('prix') and enriched.get('prix') != listing.get('prix'):
                stats['prix_extraits'] += 1
            if len(enriched.get('equipements', [])) > len(listing.get('equipements', [])):
                stats['equipements_ajoutes'] += 1
                
        except Exception as e:
            print(f"Erreur listing {listing.get('id', '?')}: {e}")
            enriched_listings.append(listing)  # Garder l'original en cas d'erreur
    
    # Mettre à jour les données
    data['listings'] = enriched_listings
    
    # Metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['extraction_complete_date'] = datetime.now().isoformat()
    data['metadata']['listings_traites'] = len(enriched_listings)
    data['metadata']['statistiques'] = stats
    
    out = output_path or str(path.parent / f"{path.stem}_extrait_complet.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ {len(enriched_listings)} listings enrichis complètement")
    print(f"✅ Dates publication trouvées: {stats['dates_publication_trouvees']}")
    print(f"✅ Prix extraits/améliorés: {stats['prix_extraits']}")
    print(f"✅ Équipements ajoutés: {stats['equipements_ajoutes']}")
    print(f"✅ Fichier sauvegardé: {out}")
    
    return len(enriched_listings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Agent d\'extraction complète - Location Vacances')
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON des listings')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    args = parser.parse_args()
    
    process_json_file_complet(args.file, args.output)