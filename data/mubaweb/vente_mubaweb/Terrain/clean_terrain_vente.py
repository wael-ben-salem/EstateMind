"""
Script de nettoyage pour Vente de Terrains
Nettoie et normalise TOUS les champs spécifiques aux terrains
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


# ========== CONSTANTES POUR NORMALISATION ==========

REGIONS_MAPPING = {
    "tunis": "Tunis", "la marsa": "Tunis", "carthage": "Tunis", "le kram": "Tunis",
    "ariana": "Ariana", "ennasr": "Ariana", "manzah": "Ariana", "soukra": "Ariana", "raoued": "Ariana",
    "ben arous": "Ben Arous", "boumhel": "Ben Arous", "mohammedia": "Ben Arous",
    "nabeul": "Nabeul", "hammamet": "Nabeul", "kélibia": "Nabeul",
    "sousse": "Sousse", "hammam sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte"
}

TYPES_TERRAINS_NORMALISES = {
    "terrain de promotion": "Terrain de promotion",
    "terrain agricole": "Terrain agricole",
    "terrain constructible": "Terrain constructible",
    "terrain résidentiel": "Terrain résidentiel",
    "terrain commercial": "Terrain commercial",
    "terrain industriel": "Terrain industriel",
    "terrain touristique": "Terrain touristique",
    "terrain mixte": "Terrain mixte",
    "lots de villa": "Lots de villa",
    "groupement d'habitation": "Groupement d'habitation"
}

VOCATIONS_NORMALISEES = {
    "résidentiel": "Résidentiel",
    "commercial": "Commercial",
    "industriel": "Industriel",
    "touristique": "Touristique",
    "agricole": "Agricole",
    "mixte": "Mixte"
}

SITUATIONS_JURIDIQUES_NORMALISEES = {
    "titre bleu": "Titre bleu",
    "titre foncier": "Titre foncier",
    "titré": "Titré",
    "promesse de vente": "Promesse de vente",
    "indivision": "Indivision",
    "cadastre": "Cadastre",
    "certificat de propriété": "Certificat de propriété",
    "acte notarié": "Acte notarié",
    "contrat de réservation": "Contrat de réservation",
    "loti": "Loti"
}

VIABILISATION_NORMALISEE = {
    "eau": "Eau",
    "électricité": "Électricité",
    "gaz": "Gaz",
    "téléphone": "Téléphone",
    "assainissement": "Assainissement",
    "tout-à-l'égout": "Tout-à-l'égout",
    "viabilisé": "Viabilisé"
}

CONSTRUCTIBILITE_NORMALISEE = {
    "constructible": "Constructible",
    "non constructible": "Non constructible",
    "plain pied": "Plain pied",
    "r+1": "R+1",
    "r+2": "R+2",
    "r+3": "R+3"
}

PROXIMITES_NORMALISEES = {
    "mer": "Mer",
    "plage": "Plage",
    "commerces": "Commerces",
    "écoles": "Écoles",
    "collège": "Collège",
    "lycée": "Lycée",
    "hôpital": "Hôpital",
    "clinique": "Clinique",
    "autoroute": "Autoroute",
    "transport": "Transport"
}


# ========== FONCTIONS DE NETTOYAGE ==========

def clean_text(text: Any) -> str:
    """Nettoie un texte"""
    if not text:
        return ""
    if isinstance(text, (int, float)):
        return str(text)
    return re.sub(r'\s+', ' ', str(text)).strip()


def clean_number(value: Any, default: Any = None) -> Any:
    """Nettoie une valeur numérique"""
    if value is None:
        return default
    
    try:
        if isinstance(value, (int, float)):
            return float(value) if isinstance(value, float) else int(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'\s+', '', value)
            if ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            if cleaned.replace('.', '').replace('-', '').isdigit():
                if '.' in cleaned:
                    return float(cleaned)
                else:
                    return int(cleaned)
    except:
        pass
    
    return default


def clean_prix_text(prix_text: Any, prix: float) -> str:
    """Nettoie le texte du prix"""
    if not prix_text and prix == 0:
        return "Prix à consulter"
    
    if prix == 0:
        if prix_text and isinstance(prix_text, str):
            text_lower = prix_text.lower()
            if any(word in text_lower for word in ['consulter', 'contact', 'demande', 'sur demande']):
                return clean_text(prix_text)
        return "Prix à consulter"
    
    if isinstance(prix_text, str):
        cleaned = clean_text(prix_text)
        if str(int(prix)) in cleaned.replace(' ', ''):
            return f"{int(prix):,} TND".replace(',', ' ')
        return cleaned
    
    return f"{int(prix):,} TND".replace(',', ' ')


def clean_surface_text(surface_text: Any, surface: float) -> str:
    """Nettoie le texte de la surface"""
    if not surface_text and surface:
        return f"{int(surface)} m²"
    
    if not surface_text:
        return ""
    
    cleaned = clean_text(surface_text)
    if 'm²' not in cleaned and 'm2' in cleaned.lower():
        cleaned = cleaned.lower().replace('m2', 'm²')
    elif 'm²' not in cleaned and surface:
        cleaned = f"{int(surface)} m²"
    
    return cleaned


def clean_region_from_ville(ville: str) -> Optional[str]:
    """Détermine la région à partir de la ville"""
    if not ville:
        return None
    
    ville_lower = ville.lower().strip()
    
    for key, region in REGIONS_MAPPING.items():
        if key in ville_lower:
            return region
    
    return None


def clean_types_terrain(types: Any) -> List[str]:
    """Nettoie la liste des types de terrain"""
    if not types:
        return []
    
    if isinstance(types, str):
        if ',' in types:
            items = [t.strip() for t in types.split(',') if t.strip()]
        else:
            items = [types.strip()]
    elif isinstance(types, list):
        items = types
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            for key, value in TYPES_TERRAINS_NORMALISES.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_vocations(vocations: Any) -> List[str]:
    """Nettoie la liste des vocations"""
    if not vocations:
        return []
    
    if isinstance(vocations, str):
        if ',' in vocations:
            items = [v.strip() for v in vocations.split(',') if v.strip()]
        else:
            items = [vocations.strip()]
    elif isinstance(vocations, list):
        items = vocations
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            for key, value in VOCATIONS_NORMALISEES.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_situations_juridiques(situations: Any) -> List[str]:
    """Nettoie la liste des situations juridiques"""
    if not situations:
        return []
    
    if isinstance(situations, str):
        if ',' in situations:
            items = [s.strip() for s in situations.split(',') if s.strip()]
        else:
            items = [situations.strip()]
    elif isinstance(situations, list):
        items = situations
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            for key, value in SITUATIONS_JURIDIQUES_NORMALISEES.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_viabilisation(viab: Any) -> List[str]:
    """Nettoie la liste des éléments de viabilisation"""
    if not viab:
        return []
    
    if isinstance(viab, str):
        if ',' in viab:
            items = [v.strip() for v in viab.split(',') if v.strip()]
        else:
            items = [viab.strip()]
    elif isinstance(viab, list):
        items = viab
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            for key, value in VIABILISATION_NORMALISEE.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_constructibilite(const: Any) -> List[str]:
    """Nettoie la liste des informations de constructibilité"""
    if not const:
        return []
    
    if isinstance(const, str):
        if ',' in const:
            items = [c.strip() for c in const.split(',') if c.strip()]
        else:
            items = [const.strip()]
    elif isinstance(const, list):
        items = const
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            # R+1, R+2, etc.
            r_match = re.search(r'r\s*\+\s*(\d+)', item_lower)
            if r_match:
                cleaned.append(f"R+{r_match.group(1)}")
                continue
            
            # COS
            cos_match = re.search(r'cos\s*[:\-]?\s*([\d.]+)', item_lower)
            if cos_match:
                cleaned.append(f"COS {cos_match.group(1)}")
                continue
            
            for key, value in CONSTRUCTIBILITE_NORMALISEE.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_proximites(prox: Any) -> List[str]:
    """Nettoie la liste des proximités"""
    if not prox:
        return []
    
    if isinstance(prox, str):
        if ',' in prox:
            items = [p.strip() for p in prox.split(',') if p.strip()]
        else:
            items = [prox.strip()]
    elif isinstance(prox, list):
        items = prox
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item_lower = item.lower()
            for key, value in PROXIMITES_NORMALISEES.items():
                if key in item_lower:
                    if value not in cleaned:
                        cleaned.append(value)
                    break
            else:
                if item.title() not in cleaned:
                    cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_acces(acces: Any) -> List[str]:
    """Nettoie la liste des accès"""
    if not acces:
        return []
    
    if isinstance(acces, str):
        if ',' in acces:
            items = [a.strip() for a in acces.split(',') if a.strip()]
        else:
            items = [acces.strip()]
    elif isinstance(acces, list):
        items = acces
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_caracteristiques(caracs: Any) -> Dict[str, Any]:
    """Nettoie les caractéristiques"""
    result = {}
    
    if not caracs:
        return result
    
    if isinstance(caracs, dict):
        data = caracs
    elif isinstance(caracs, str):
        try:
            data = json.loads(caracs) if caracs != "{}" else {}
        except:
            data = {}
    else:
        return result
    
    for key, value in data.items():
        key_clean = key.lower().strip().replace(' ', '_').replace('é', 'e').replace('è', 'e')
        
        if key_clean == 'type_de_terrain':
            result['type_terrain'] = clean_types_terrain(value)
        elif key_clean == 'constructibilite':
            result['constructibilite'] = clean_constructibilite(value)
        else:
            result[key_clean] = value
    
    return result


def clean_informations_supplementaires(info: Any) -> Dict[str, Any]:
    """Nettoie les informations supplémentaires"""
    result = {}
    
    if not info:
        return result
    
    if isinstance(info, dict):
        data = info
    elif isinstance(info, str):
        try:
            data = json.loads(info) if info != "{}" else {}
        except:
            data = {}
    else:
        return result
    
    for key, value in data.items():
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
    
    return result


def clean_contact_info(contact: Any) -> Optional[Dict[str, Any]]:
    """Nettoie les informations de contact"""
    if not contact:
        return None
    
    try:
        if isinstance(contact, str):
            data = json.loads(contact) if contact != "{}" else {}
        elif isinstance(contact, dict):
            data = contact
        else:
            return None
        
        result = {}
        
        for key, value in data.items():
            key_clean = key.lower().strip().replace(' ', '_')
            
            if 'formulaire' in key_clean:
                if isinstance(value, str):
                    result['formulaire_contact'] = value.lower() in ['disponible', 'oui', 'true']
                else:
                    result['formulaire_contact'] = bool(value)
            elif 'telephone' in key_clean:
                if isinstance(value, str):
                    digits = re.sub(r'\D', '', value)
                    if digits.startswith('216') and len(digits) == 11:
                        result['telephone'] = f"+{digits}"
                    elif len(digits) == 8:
                        result['telephone'] = f"+216{digits}"
                    else:
                        result['telephone'] = value
                else:
                    result[key_clean] = value
            else:
                result[key_clean] = value
        
        return result if result else None
    except:
        return None


def clean_localisation(loc: Any) -> Optional[Dict[str, Any]]:
    """Nettoie la localisation GPS"""
    if not loc:
        return None
    
    try:
        if isinstance(loc, str):
            data = json.loads(loc) if loc != "{}" else {}
        elif isinstance(loc, dict):
            data = loc
        else:
            return None
        
        result = {}
        
        if 'latitude' in data:
            try:
                result['latitude'] = float(data['latitude'])
            except:
                pass
        
        if 'longitude' in data:
            try:
                result['longitude'] = float(data['longitude'])
            except:
                pass
        
        if 'latitude' in result and 'longitude' in result:
            result['coordinates'] = [result['longitude'], result['latitude']]
        
        return result if result else None
    except:
        return None


def clean_images(images: Any) -> List[str]:
    """Nettoie la liste des images"""
    if not images:
        return []
    
    if isinstance(images, str):
        if ';' in images:
            urls = [img.strip() for img in images.split(';') if img.strip()]
        else:
            urls = [images.strip()]
    elif isinstance(images, list):
        urls = images
    else:
        return []
    
    filtered = []
    exclude_patterns = [r'logo', r'loading\.gif', r'favicon', r'banks?/', r'assets/', r'banner']
    
    for url in urls:
        if isinstance(url, str) and url.startswith(('http://', 'https://')):
            url_lower = url.lower()
            exclude = False
            for pattern in exclude_patterns:
                if re.search(pattern, url_lower):
                    exclude = True
                    break
            if not exclude:
                filtered.append(url)
    
    seen = set()
    unique = []
    for url in filtered:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    
    return unique


def clean_date(date_str: Any) -> Optional[str]:
    """Normalise une date"""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            if '.' in date_str:
                date_str = date_str.split('.')[0]
            if not date_str.endswith('Z'):
                date_str += 'Z'
            return date_str
        elif isinstance(date_str, datetime):
            return date_str.isoformat() + 'Z'
    except:
        pass
    
    return None


# ========== FONCTION PRINCIPALE DE NETTOYAGE ==========

def clean_listing(listing: Dict) -> Dict:
    """
    Nettoie complètement un listing de terrain
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'titre', 'url', 'description_courte', 'description_complete',
                     'page_source', 'is_valid', 'type_terrain', 'vocation', 'situation_juridique']
    
    for field in simple_fields:
        if field in listing and listing[field]:
            cleaned[field] = clean_text(listing[field])
        else:
            if field == 'is_valid':
                cleaned[field] = True
            else:
                cleaned[field] = ""
    
    # ===== 2. LOCALISATION =====
    cleaned['ville'] = clean_text(listing.get('ville', ''))
    cleaned['quartier'] = clean_text(listing.get('quartier', ''))
    cleaned['adresse'] = clean_text(listing.get('adresse', ''))
    
    region = listing.get('region') or clean_region_from_ville(cleaned['ville'])
    cleaned['region'] = clean_text(region) if region else ""
    
    # ===== 3. PRIX =====
    prix = clean_number(listing.get('prix'), 0)
    cleaned['prix'] = prix
    cleaned['prix_text'] = clean_prix_text(listing.get('prix_text'), prix)
    
    # Prix au m² (si présent)
    prix_m2 = clean_number(listing.get('prix_m2') or listing.get('prix_m2_extrait'))
    cleaned['prix_m2'] = prix_m2 if prix_m2 and prix_m2 > 0 else None
    
    # ===== 4. SURFACE =====
    surface = clean_number(listing.get('surface'))
    cleaned['surface'] = surface if surface and surface > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    if listing.get('surface_hectares'):
        cleaned['surface_hectares'] = clean_number(listing['surface_hectares'])
    
    # ===== 5. TYPES DE TERRAIN =====
    types = listing.get('types_terrain_extraits') or listing.get('types_terrain')
    cleaned['types_terrain'] = clean_types_terrain(types)
    
    # ===== 6. VOCATIONS =====
    vocations = listing.get('vocations')
    cleaned['vocations'] = clean_vocations(vocations)
    
    # ===== 7. SITUATIONS JURIDIQUES =====
    situations = listing.get('situations_juridiques')
    cleaned['situations_juridiques'] = clean_situations_juridiques(situations)
    
    # ===== 8. VIABILISATION =====
    viabilisation = listing.get('viabilisation')
    cleaned['viabilisation'] = clean_viabilisation(viabilisation)
    
    # ===== 9. CONSTRUCTIBILITÉ =====
    constructibilite = listing.get('constructibilite')
    cleaned['constructibilite'] = clean_constructibilite(constructibilite)
    
    # ===== 10. CARACTÉRISTIQUES PHYSIQUES =====
    cleaned['topographie'] = clean_text(listing.get('topographie'))
    cleaned['orientation'] = clean_text(listing.get('orientation'))
    cleaned['vue'] = clean_text(listing.get('vue'))
    cleaned['zone'] = clean_text(listing.get('zone'))
    
    # ===== 11. ACCÈS =====
    acces = listing.get('acces')
    cleaned['acces'] = clean_acces(acces)
    
    # ===== 12. PROXIMITÉS =====
    proximites = listing.get('proximites')
    cleaned['proximites'] = clean_proximites(proximites)
    
    # ===== 13. BOOLÉENS =====
    cleaned['cloture'] = bool(listing.get('cloture', False))
    cleaned['front_mer'] = bool(listing.get('front_mer', False))
    
    # ===== 14. CARACTÉRISTIQUES =====
    caracs = listing.get('caracteristiques') or listing.get('caracteristiques_extraites')
    cleaned['caracteristiques'] = clean_caracteristiques(caracs)
    
    # ===== 15. INFORMATIONS SUPPLÉMENTAIRES =====
    info_supp = listing.get('informations_supplementaires') or listing.get('informations_supplementaires_parse')
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(info_supp)
    
    # ===== 16. CONTACT INFO =====
    contact = listing.get('contact_info') or listing.get('contact_info_parse')
    cleaned['contact_info'] = clean_contact_info(contact)
    
    # ===== 17. LOCALISATION GPS =====
    gps = listing.get('localisation') or listing.get('gps')
    cleaned['localisation'] = clean_localisation(gps)
    
    # ===== 18. IMAGES =====
    cleaned['images'] = clean_images(listing.get('images', []))
    
    # ===== 19. DATES =====
    cleaned['date_scraping'] = clean_date(listing.get('date_scraping'))
    cleaned['date_publication'] = listing.get('date_publication')
    
    return cleaned


def validate_listing(listing: Dict) -> List[str]:
    """
    Valide un listing et retourne les avertissements
    """
    warnings = []
    
    if not listing.get('id'):
        warnings.append("ID manquant")
    
    if not listing.get('url'):
        warnings.append("URL manquante")
    
    prix = listing.get('prix')
    prix_text = listing.get('prix_text')
    if prix and prix > 0 and prix_text:
        if str(int(prix)) not in prix_text and 'consulter' not in prix_text.lower():
            warnings.append(f"Incohérence prix: {prix} vs {prix_text}")
    
    surface = listing.get('surface')
    surface_text = listing.get('surface_text')
    if surface and surface > 0 and surface_text:
        if str(int(surface)) not in surface_text:
            warnings.append(f"Incohérence surface: {surface} vs {surface_text}")
    
    if not listing.get('ville'):
        warnings.append("Ville manquante")
    
    # Vérifier si le type de terrain est présent
    if not listing.get('types_terrain') and not listing.get('type_terrain'):
        warnings.append("Type de terrain manquant")
    
    return warnings


def clean_json_file(input_path: str, output_path: Optional[str] = None, validate: bool = False):
    """
    Nettoie un fichier JSON de terrains
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get('listings', [])
    cleaned_listings = []
    validation_warnings = {}
    
    stats = {
        'total': len(listings),
        'prix_text_nettoyes': 0,
        'surface_text_nettoyes': 0,
        'prix_m2_extraits': 0,
        'regions_determinees': 0,
        'types_terrain_nettoyes': 0,
        'vocations_nettoyees': 0,
        'situations_juridiques_nettoyees': 0,
        'viabilisation_nettoyee': 0,
        'constructibilite_nettoyee': 0,
        'proximites_nettoyees': 0,
        'contacts_normalises': 0,
        'localisations_normalisees': 0,
        'images_filtrees': 0
    }
    
    for i, listing in enumerate(listings):
        try:
            cleaned = clean_listing(listing)
            cleaned_listings.append(cleaned)
            
            if cleaned.get('prix_text') != listing.get('prix_text'):
                stats['prix_text_nettoyes'] += 1
            if cleaned.get('surface_text') != listing.get('surface_text'):
                stats['surface_text_nettoyes'] += 1
            if cleaned.get('prix_m2') and not listing.get('prix_m2'):
                stats['prix_m2_extraits'] += 1
            if cleaned.get('region') and not listing.get('region'):
                stats['regions_determinees'] += 1
            if cleaned.get('types_terrain'):
                stats['types_terrain_nettoyes'] += 1
            if cleaned.get('vocations'):
                stats['vocations_nettoyees'] += 1
            if cleaned.get('situations_juridiques'):
                stats['situations_juridiques_nettoyees'] += 1
            if cleaned.get('viabilisation'):
                stats['viabilisation_nettoyee'] += 1
            if cleaned.get('constructibilite'):
                stats['constructibilite_nettoyee'] += 1
            if cleaned.get('proximites'):
                stats['proximites_nettoyees'] += 1
            if cleaned.get('contact_info'):
                stats['contacts_normalises'] += 1
            if cleaned.get('localisation'):
                stats['localisations_normalisees'] += 1
            if len(cleaned.get('images', [])) < len(listing.get('images', [])):
                stats['images_filtrees'] += 1
            
            if validate:
                warnings = validate_listing(cleaned)
                if warnings:
                    validation_warnings[cleaned.get('id', f'ligne_{i}')] = warnings
                    
        except Exception as e:
            print(f"❌ Erreur listing {listing.get('id', '?')}: {e}")
            cleaned_listings.append(listing)
    
    data['listings'] = cleaned_listings
    
    if 'metadata' not in data:
        data['metadata'] = {}
    
    data['metadata']['cleaning_date'] = datetime.now().isoformat() + 'Z'
    data['metadata']['listings_nettoyes'] = len(cleaned_listings)
    data['metadata']['statistiques_nettoyage'] = stats
    
    if validate and validation_warnings:
        data['metadata']['validation_warnings'] = validation_warnings
        print(f"⚠️ {len(validation_warnings)} listings avec des avertissements")
    
    out = output_path or str(path.parent / f"{path.stem}_clean.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES DE NETTOYAGE - VENTE DE TERRAINS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Prix text nettoyés: {stats['prix_text_nettoyes']}")
    print(f"✅ Surface text nettoyées: {stats['surface_text_nettoyes']}")
    print(f"✅ Prix au m² extraits: {stats['prix_m2_extraits']}")
    print(f"✅ Régions déterminées: {stats['regions_determinees']}")
    print(f"✅ Types de terrain nettoyés: {stats['types_terrain_nettoyes']}")
    print(f"✅ Vocations nettoyées: {stats['vocations_nettoyees']}")
    print(f"✅ Situations juridiques nettoyées: {stats['situations_juridiques_nettoyees']}")
    print(f"✅ Viabilisation nettoyée: {stats['viabilisation_nettoyee']}")
    print(f"✅ Constructibilité nettoyée: {stats['constructibilite_nettoyee']}")
    print(f"✅ Proximités nettoyées: {stats['proximites_nettoyees']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ Localisations normalisées: {stats['localisations_normalisees']}")
    print(f"✅ Images filtrées: {stats['images_filtrees']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des JSON de vente de terrains")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()