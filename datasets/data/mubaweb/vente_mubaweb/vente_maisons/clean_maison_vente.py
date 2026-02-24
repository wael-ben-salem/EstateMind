"""
Script de nettoyage pour Vente de Maisons
Nettoie et normalise TOUS les champs spécifiques aux maisons/villas
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
    "nabeul": "Nabeul", "hammamet": "Nabeul",
    "sousse": "Sousse", "hammam sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte"
}

TYPES_MAISONS_NORMALISES = {
    "villa": "Villa",
    "duplex": "Duplex",
    "triplex": "Triplex",
    "maison": "Maison",
    "maison individuelle": "Maison individuelle",
    "maison de ville": "Maison de ville",
    "maison de standing": "Maison de standing",
    "villa jumelée": "Villa jumelée",
    "villa indépendante": "Villa indépendante",
    "chalet": "Chalet",
    "riad": "Riad",
    "dar": "Dar"
}

ETAT_MAISON_MAPPING = {
    "jamais habité": "Jamais habité",
    "jamais habité / rénové": "Jamais habité / Rénové",
    "neuf": "Neuf",
    "à rénover": "À rénover",
    "bon état": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
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

VUE_MAPPING = {
    "mer": "Mer",
    "lac": "Lac",
    "dégagée": "Dégagée",
    "panoramique": "Panoramique",
    "jardin": "Jardin",
    "montagne": "Montagne"
}

CHAUFFAGE_MAPPING = {
    "central": "Central",
    "au sol": "Au sol",
    "électrique": "Électrique"
}

CLIMATISATION_MAPPING = {
    "centrale": "Centrale",
    "split": "Split"
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


def clean_type_maison(type_maison: Any) -> str:
    """Normalise le type de maison"""
    if not type_maison:
        return ""
    
    type_maison_str = str(type_maison).lower().strip()
    
    for key, value in TYPES_MAISONS_NORMALISES.items():
        if key in type_maison_str:
            return value
    
    return str(type_maison).title()


def clean_etat_maison(etat: Any) -> Optional[str]:
    """Normalise l'état de la maison"""
    if not etat:
        return None
    
    etat_str = str(etat).lower().strip()
    
    for key, value in ETAT_MAISON_MAPPING.items():
        if key in etat_str:
            return value
    
    return str(etat).title()


def clean_orientation(orientation: Any) -> Optional[str]:
    """Normalise l'orientation"""
    if not orientation:
        return None
    
    orientation_str = str(orientation).lower().strip()
    
    for key, value in ORIENTATION_MAPPING.items():
        if key in orientation_str:
            return value
    
    return str(orientation).title()


def clean_vue_type(vue: Any) -> Optional[str]:
    """Normalise le type de vue"""
    if not vue:
        return None
    
    vue_str = str(vue).lower().strip()
    
    for key, value in VUE_MAPPING.items():
        if key in vue_str:
            return value
    
    return str(vue).title()


def clean_chauffage_type(chauffage: Any) -> Optional[str]:
    """Normalise le type de chauffage"""
    if not chauffage:
        return None
    
    chauffage_str = str(chauffage).lower().strip()
    
    for key, value in CHAUFFAGE_MAPPING.items():
        if key in chauffage_str:
            return value
    
    return str(chauffage).title()


def clean_climatisation_type(clim: Any) -> Optional[str]:
    """Normalise le type de climatisation"""
    if not clim:
        return None
    
    clim_str = str(clim).lower().strip()
    
    for key, value in CLIMATISATION_MAPPING.items():
        if key in clim_str:
            return value
    
    return str(clim).title()


def clean_equipements(equipements: Any) -> List[str]:
    """Nettoie une liste d'équipements"""
    if not equipements:
        return []
    
    if isinstance(equipements, str):
        if ';' in equipements:
            items = [e.strip() for e in equipements.split(';') if e.strip()]
        elif ',' in equipements:
            items = [e.strip() for e in equipements.split(',') if e.strip()]
        else:
            items = [equipements.strip()]
    elif isinstance(equipements, list):
        items = equipements
    else:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = re.sub(r'^\d+[\s\.\-]*', '', item)
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    return sorted(cleaned)


def clean_proximites(proximites: Any) -> List[str]:
    """Nettoie la liste des proximités"""
    if not proximites:
        return []
    
    if isinstance(proximites, list):
        return [clean_text(p) for p in proximites if p]
    elif isinstance(proximites, str):
        if ',' in proximites:
            return [clean_text(p) for p in proximites.split(',') if p.strip()]
        else:
            return [clean_text(proximites)]
    
    return []


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
        
        if key_clean in ['etat', 'état']:
            result['etat'] = clean_etat_maison(value)
        elif 'surface' in key_clean and 'terrain' in key_clean:
            num = clean_number(value)
            if num:
                result['surface_terrain'] = num
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


def clean_conditions_vente(conditions: Any) -> Dict[str, Any]:
    """Nettoie les conditions de vente"""
    result = {}
    
    if not conditions:
        return result
    
    if isinstance(conditions, dict):
        data = conditions
    elif isinstance(conditions, str):
        try:
            data = json.loads(conditions) if conditions != "{}" else {}
        except:
            data = {}
    else:
        return result
    
    for key, value in data.items():
        key_clean = key.lower().strip().replace(' ', '_')
        
        if key_clean == 'etat':
            result['etat'] = clean_etat_maison(value)
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
                # Nettoyer le numéro de téléphone
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
    exclude_patterns = [r'logo', r'loading\.gif', r'favicon', r'banks?/', r'assets/', r'app-store']
    
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


def clean_annee_construction(annee: Any) -> Optional[int]:
    """Nettoie l'année de construction"""
    if not annee:
        return None
    
    try:
        if isinstance(annee, (int, float)):
            return int(annee)
        elif isinstance(annee, str):
            numbers = re.findall(r'\d{4}', annee)
            if numbers:
                return int(numbers[0])
    except:
        pass
    
    return None


# ========== FONCTION PRINCIPALE DE NETTOYAGE ==========

def clean_listing(listing: Dict) -> Dict:
    """
    Nettoie complètement un listing de maison
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'titre', 'url', 'description_courte', 'description_complete',
                     'page_source', 'is_valid', 'type_transaction', 'residence', 'batiment']
    
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
    
    # Prix au m²
    surface = listing.get('surface')
    if prix and surface and surface > 0:
        cleaned['prix_m2'] = round(prix / surface, 2)
    else:
        cleaned['prix_m2'] = None
    
    # ===== 4. SURFACES =====
    surface_hab = clean_number(listing.get('surface'))
    cleaned['surface'] = surface_hab if surface_hab and surface_hab > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    surface_terrain = clean_number(listing.get('surface_terrain'))
    cleaned['surface_terrain'] = surface_terrain if surface_terrain and surface_terrain > 0 else None
    
    # Surfaces additionnelles
    surface_fields = ['surface_jardin', 'surface_terrasse', 'surface_piscine']
    for field in surface_fields:
        val = listing.get(field)
        cleaned[field] = clean_number(val)
    
    # ===== 5. TYPE DE MAISON =====
    cleaned['type_maison'] = clean_type_maison(listing.get('type_maison', ''))
    
    # ===== 6. NOMBRES =====
    numeric_fields = ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'nombre_niveaux', 'garage_nombre', 'etage']
    for field in numeric_fields:
        val = listing.get(field)
        cleaned[field] = clean_number(val)
    
    # ===== 7. ANNÉE CONSTRUCTION =====
    cleaned['annee_construction'] = clean_annee_construction(
        listing.get('annee_construction')
    )
    
    # ===== 8. ÉTAT =====
    etat = listing.get('etat_maison') or listing.get('caracs_etat_bien') or listing.get('etat_bien')
    cleaned['etat_maison'] = clean_etat_maison(etat)
    
    # ===== 9. CARACTÉRISTIQUES SPÉCIFIQUES =====
    bool_fields = [
        'a_jardin', 'a_piscine', 'a_terrasse', 'a_garage',
        'a_cave', 'a_cheminee', 'a_alarme', 'a_buanderie',
        'a_dressing', 'a_placards', 'potentiel_extension'
    ]
    for field in bool_fields:
        cleaned[field] = bool(listing.get(field, False))
    
    # ===== 10. ORIENTATION, VUE, CHAUFFAGE, CLIMATISATION =====
    cleaned['orientation'] = clean_orientation(listing.get('orientation'))
    cleaned['vue_type'] = clean_vue_type(listing.get('vue_type'))
    cleaned['chauffage_type'] = clean_chauffage_type(listing.get('chauffage_type'))
    cleaned['climatisation_type'] = clean_climatisation_type(listing.get('climatisation_type'))
    
    # ===== 11. PROXIMITÉS =====
    cleaned['proximites'] = clean_proximites(listing.get('proximites', []))
    
    # ===== 12. ÉQUIPEMENTS =====
    equipements = listing.get('equipements', [])
    amenities = listing.get('amenities_maison', [])
    equip_det = listing.get('equipements_detaille_list', [])
    
    all_equipements = list(set(
        clean_equipements(equipements) +
        clean_equipements(amenities) +
        clean_equipements(equip_det)
    ))
    cleaned['equipements'] = sorted(all_equipements) if all_equipements else []
    
    # ===== 13. AMENITIES MAISON =====
    cleaned['amenities_maison'] = clean_equipements(listing.get('amenities_maison', []))
    
    # ===== 14. CARACTÉRISTIQUES =====
    caracs = listing.get('caracteristiques') or listing.get('caracteristiques_extraites')
    cleaned['caracteristiques'] = clean_caracteristiques(caracs)
    
    # ===== 15. INFORMATIONS SUPPLÉMENTAIRES =====
    info_supp = listing.get('informations_supplementaires') or listing.get('informations_supplementaires_parse')
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(info_supp)
    
    # ===== 16. CONDITIONS DE VENTE =====
    conditions = listing.get('conditions_vente') or listing.get('conditions_vente_parse')
    cleaned['conditions_vente'] = clean_conditions_vente(conditions)
    
    # ===== 17. CONTACT INFO =====
    contact = listing.get('contact_info') or listing.get('contact_info_parse')
    cleaned['contact_info'] = clean_contact_info(contact)
    
    # ===== 18. LOCALISATION GPS =====
    gps = listing.get('localisation') or listing.get('gps')
    cleaned['localisation'] = clean_localisation(gps)
    
    # ===== 19. IMAGES =====
    cleaned['images'] = clean_images(listing.get('images', []))
    
    # ===== 20. DATES =====
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
    
    return warnings


def clean_json_file(input_path: str, output_path: Optional[str] = None, validate: bool = False):
    """
    Nettoie un fichier JSON de maisons
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
        'prix_m2_calcules': 0,
        'regions_determinees': 0,
        'equipements_nettoyes': 0,
        'caracteristiques_normalisees': 0,
        'infos_supp_normalisees': 0,
        'conditions_normalisees': 0,
        'contacts_normalises': 0,
        'localisations_normalisees': 0,
        'images_filtrees': 0,
        'surfaces_terrain_extraites': 0
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
                stats['prix_m2_calcules'] += 1
            if cleaned.get('region') and not listing.get('region'):
                stats['regions_determinees'] += 1
            if len(cleaned.get('equipements', [])) != len(listing.get('equipements', [])):
                stats['equipements_nettoyes'] += 1
            if cleaned.get('caracteristiques'):
                stats['caracteristiques_normalisees'] += 1
            if cleaned.get('informations_supplementaires'):
                stats['infos_supp_normalisees'] += 1
            if cleaned.get('conditions_vente'):
                stats['conditions_normalisees'] += 1
            if cleaned.get('contact_info'):
                stats['contacts_normalises'] += 1
            if cleaned.get('localisation'):
                stats['localisations_normalisees'] += 1
            if len(cleaned.get('images', [])) < len(listing.get('images', [])):
                stats['images_filtrees'] += 1
            if cleaned.get('surface_terrain'):
                stats['surfaces_terrain_extraites'] += 1
            
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
    print("📊 STATISTIQUES DE NETTOYAGE - VENTE DE MAISONS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Prix text nettoyés: {stats['prix_text_nettoyes']}")
    print(f"✅ Surface text nettoyées: {stats['surface_text_nettoyes']}")
    print(f"✅ Prix au m² calculés: {stats['prix_m2_calcules']}")
    print(f"✅ Régions déterminées: {stats['regions_determinees']}")
    print(f"✅ Équipements nettoyés: {stats['equipements_nettoyes']}")
    print(f"✅ Caractéristiques normalisées: {stats['caracteristiques_normalisees']}")
    print(f"✅ Infos supplémentaires normalisées: {stats['infos_supp_normalisees']}")
    print(f"✅ Conditions de vente normalisées: {stats['conditions_normalisees']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ Localisations normalisées: {stats['localisations_normalisees']}")
    print(f"✅ Images filtrées: {stats['images_filtrees']}")
    print(f"✅ Surfaces terrain extraites: {stats['surfaces_terrain_extraites']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des JSON de vente de maisons")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()