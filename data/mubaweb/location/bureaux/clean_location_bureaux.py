"""
Script de nettoyage pour Location de Bureaux
Nettoie et normalise TOUS les champs spécifiques aux bureaux
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

TYPES_BUREAUX_NORMALISES = {
    "open space": "Open Space",
    "openspace": "Open Space",
    "open-space": "Open Space",
    "plateau": "Plateau",
    "bureau": "Bureau",
    "bureaux": "Bureaux",
    "cabinet": "Cabinet",
    "immeuble de bureaux": "Immeuble de bureaux",
    "centre d'affaires": "Centre d'affaires"
}

VUES_NORMALISEES = {
    "lac": "Lac",
    "mer": "Mer",
    "panoramique": "Panoramique",
    "dégagée": "Dégagée"
}

CLIMATISATION_NORMALISEE = {
    "centrale": "Centrale",
    "réversible": "Réversible",
    "individuelle": "Individuelle"
}

CHAUFFAGE_NORMALISE = {
    "central": "Central",
    "individuel": "Individuel"
}

PARKING_TYPES_NORMALISES = {
    "sous-sol": "Sous-sol",
    "couvert": "Couvert",
    "extérieur": "Extérieur"
}

ETAT_BUREAU_NORMALISE = {
    "neuf": "Neuf",
    "project neuf": "Projet neuf",
    "bon état": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "rénové": "Rénové"
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


def clean_loyer_text(loyer_text: Any, loyer: float) -> str:
    """Nettoie le texte du loyer"""
    if not loyer_text and loyer == 0:
        return "Prix à consulter"
    
    if loyer == 0:
        if loyer_text and isinstance(loyer_text, str):
            text_lower = loyer_text.lower()
            if any(word in text_lower for word in ['consulter', 'contact', 'demande', 'sur demande']):
                return clean_text(loyer_text)
        return "Prix à consulter"
    
    if isinstance(loyer_text, str):
        cleaned = clean_text(loyer_text)
        if str(int(loyer)) in cleaned.replace(' ', ''):
            return f"{int(loyer):,} TND".replace(',', ' ')
        return cleaned
    
    return f"{int(loyer):,} TND".replace(',', ' ')


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


def clean_type_bureau(type_bureau: Any) -> str:
    """Normalise le type de bureau"""
    if not type_bureau:
        return ""
    
    type_str = str(type_bureau).lower().strip()
    
    for key, value in TYPES_BUREAUX_NORMALISES.items():
        if key in type_str:
            return value
    
    return str(type_bureau).title()


def clean_vue(vue: Any) -> Optional[str]:
    """Normalise le type de vue"""
    if not vue:
        return None
    
    vue_str = str(vue).lower().strip()
    
    for key, value in VUES_NORMALISEES.items():
        if key in vue_str:
            return value
    
    return str(vue).title()


def clean_climatisation_type(clim: Any) -> Optional[str]:
    """Normalise le type de climatisation"""
    if not clim:
        return None
    
    clim_str = str(clim).lower().strip()
    
    for key, value in CLIMATISATION_NORMALISEE.items():
        if key in clim_str:
            return value
    
    return str(clim).title()


def clean_chauffage_type(chauffage: Any) -> Optional[str]:
    """Normalise le type de chauffage"""
    if not chauffage:
        return None
    
    chauffage_str = str(chauffage).lower().strip()
    
    for key, value in CHAUFFAGE_NORMALISE.items():
        if key in chauffage_str:
            return value
    
    return str(chauffage).title()


def clean_parking_type(parking_type: Any) -> Optional[str]:
    """Normalise le type de parking"""
    if not parking_type:
        return None
    
    parking_str = str(parking_type).lower().strip()
    
    for key, value in PARKING_TYPES_NORMALISES.items():
        if key in parking_str:
            return value
    
    return str(parking_type).title()


def clean_etat_bureau(etat: Any) -> Optional[str]:
    """Normalise l'état du bureau"""
    if not etat:
        return None
    
    etat_str = str(etat).lower().strip()
    
    for key, value in ETAT_BUREAU_NORMALISE.items():
        if key in etat_str:
            return value
    
    return str(etat).title()


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


def clean_proximites(prox: Any) -> List[str]:
    """Nettoie la liste des proximités"""
    if not prox:
        return []
    
    if isinstance(prox, list):
        return [clean_text(p) for p in prox if p]
    elif isinstance(prox, str):
        if ',' in prox:
            return [clean_text(p) for p in prox.split(',') if p.strip()]
        else:
            return [clean_text(prox)]
    
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
            result['etat'] = clean_etat_bureau(value)
        elif key_clean == 'standing':
            result['standing'] = str(value).title()
        elif key_clean == 'type_du_sol':
            result['type_sol'] = str(value).title()
        elif key_clean in ['etage', 'étage', 'etage_du_bien']:
            num = clean_number(value)
            if num is not None:
                result['etage'] = num
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


def clean_conditions_location(conditions: Any) -> Dict[str, Any]:
    """Nettoie les conditions de location"""
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
    Nettoie complètement un listing de location de bureaux
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'titre', 'url', 'description_courte', 'description_complete',
                     'page_source', 'is_valid', 'type_contrat', 'type_location',
                     'batiment', 'residence', 'disponibilite']
    
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
    
    # ===== 3. LOYER =====
    loyer = clean_number(listing.get('loyer'), 0)
    cleaned['loyer'] = loyer
    cleaned['loyer_text'] = clean_loyer_text(listing.get('loyer_text'), loyer)
    
    # Loyer au m²
    surface = listing.get('surface')
    if loyer and surface and surface > 0:
        cleaned['loyer_m2'] = round(loyer / surface, 2)
    else:
        cleaned['loyer_m2'] = None
    
    # Loyer HT
    if listing.get('loyer_ht'):
        cleaned['loyer_ht'] = True
    
    # ===== 4. SURFACE =====
    surface = clean_number(listing.get('surface'))
    cleaned['surface'] = surface if surface and surface > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    # Surfaces additionnelles
    if listing.get('surface_terrasse'):
        cleaned['surface_terrasse'] = clean_number(listing['surface_terrasse'])
    
    # ===== 5. TYPE DE BUREAU =====
    cleaned['type_bureau'] = clean_type_bureau(listing.get('type_bureau', ''))
    
    # ===== 6. NOMBRES =====
    numeric_fields = ['nombre_pieces', 'nombre_bureaux', 'nombre_sdb', 'etage',
                      'nombre_ascenseurs', 'parking_nombre', 'nombre_salles_reunion',
                      'nombre_sanitaires', 'nombre_etages_immeuble', 'montant_charges']
    for field in numeric_fields:
        val = listing.get(field)
        cleaned[field] = clean_number(val)
    
    # ===== 7. CARACTÉRISTIQUES SPÉCIFIQUES =====
    bool_fields = [
        'est_open_space', 'est_immeuble_entier', 'a_accueil', 'a_salle_reunion',
        'a_kitchenette', 'a_sanitaires', 'sanitaires_separes', 'a_parking',
        'a_stockage', 'a_fibre', 'a_climatisation', 'a_chauffage', 'a_securite',
        'a_ascenseur', 'ascenseur_panoramique', 'a_terrasse', 'acces_independant',
        'a_moquette', 'charges_incluses'
    ]
    for field in bool_fields:
        cleaned[field] = bool(listing.get(field, False))
    
    # ===== 8. TYPES SPÉCIFIQUES =====
    cleaned['vue'] = clean_vue(listing.get('vue'))
    cleaned['climatisation_type'] = clean_climatisation_type(listing.get('climatisation_type'))
    cleaned['chauffage_type'] = clean_chauffage_type(listing.get('chauffage_type'))
    cleaned['parking_type'] = clean_parking_type(listing.get('parking_type'))
    
    # ===== 9. TYPE DE SOL =====
    type_sol = listing.get('type_sol') or listing.get('type_sol_extrait')
    cleaned['type_sol'] = clean_text(type_sol) if type_sol else None
    
    # ===== 10. PROXIMITÉS =====
    cleaned['proximites'] = clean_proximites(listing.get('proximites', []))
    
    # ===== 11. ÉQUIPEMENTS =====
    equipements = listing.get('equipements', [])
    amenities = listing.get('amenities_bureaux', [])
    equip_det = listing.get('equipements_detaille_list', [])
    
    all_equipements = list(set(
        clean_equipements(equipements) +
        clean_equipements(amenities) +
        clean_equipements(equip_det)
    ))
    cleaned['equipements'] = sorted(all_equipements) if all_equipements else []
    
    # ===== 12. AMENITIES BUREAUX =====
    cleaned['amenities_bureaux'] = clean_equipements(listing.get('amenities_bureaux', []))
    
    # ===== 13. CARACTÉRISTIQUES =====
    caracs = listing.get('caracteristiques') or listing.get('caracteristiques_extraites')
    cleaned['caracteristiques'] = clean_caracteristiques(caracs)
    
    # ===== 14. INFORMATIONS SUPPLÉMENTAIRES =====
    info_supp = listing.get('informations_supplementaires') or listing.get('informations_supplementaires_parse')
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(info_supp)
    
    # ===== 15. CONDITIONS DE LOCATION =====
    conditions = listing.get('conditions_location') or listing.get('conditions_location_parse')
    cleaned['conditions_location'] = clean_conditions_location(conditions)
    
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
    
    # ===== 20. ÉTAT =====
    etat = listing.get('etat_bien') or listing.get('caracs_etat_bien') or listing.get('etat_bureau')
    cleaned['etat_bien'] = clean_etat_bureau(etat)
    
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
    
    loyer = listing.get('loyer')
    loyer_text = listing.get('loyer_text')
    if loyer and loyer > 0 and loyer_text:
        if str(int(loyer)) not in loyer_text and 'consulter' not in loyer_text.lower():
            warnings.append(f"Incohérence loyer: {loyer} vs {loyer_text}")
    
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
    Nettoie un fichier JSON de location de bureaux
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
        'loyer_text_nettoyes': 0,
        'surface_text_nettoyes': 0,
        'loyer_m2_calcules': 0,
        'regions_determinees': 0,
        'equipements_nettoyes': 0,
        'caracteristiques_normalisees': 0,
        'infos_supp_normalisees': 0,
        'conditions_normalisees': 0,
        'contacts_normalises': 0,
        'localisations_normalisees': 0,
        'images_filtrees': 0,
        'types_bureau_normalises': 0
    }
    
    for i, listing in enumerate(listings):
        try:
            cleaned = clean_listing(listing)
            cleaned_listings.append(cleaned)
            
            if cleaned.get('loyer_text') != listing.get('loyer_text'):
                stats['loyer_text_nettoyes'] += 1
            if cleaned.get('surface_text') != listing.get('surface_text'):
                stats['surface_text_nettoyes'] += 1
            if cleaned.get('loyer_m2') and not listing.get('loyer_m2'):
                stats['loyer_m2_calcules'] += 1
            if cleaned.get('region') and not listing.get('region'):
                stats['regions_determinees'] += 1
            if len(cleaned.get('equipements', [])) != len(listing.get('equipements', [])):
                stats['equipements_nettoyes'] += 1
            if cleaned.get('caracteristiques'):
                stats['caracteristiques_normalisees'] += 1
            if cleaned.get('informations_supplementaires'):
                stats['infos_supp_normalisees'] += 1
            if cleaned.get('conditions_location'):
                stats['conditions_normalisees'] += 1
            if cleaned.get('contact_info'):
                stats['contacts_normalises'] += 1
            if cleaned.get('localisation'):
                stats['localisations_normalisees'] += 1
            if len(cleaned.get('images', [])) < len(listing.get('images', [])):
                stats['images_filtrees'] += 1
            if cleaned.get('type_bureau') and cleaned['type_bureau'] != listing.get('type_bureau'):
                stats['types_bureau_normalises'] += 1
            
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
    print("📊 STATISTIQUES DE NETTOYAGE - LOCATION DE BUREAUX")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Loyer text nettoyés: {stats['loyer_text_nettoyes']}")
    print(f"✅ Surface text nettoyées: {stats['surface_text_nettoyes']}")
    print(f"✅ Loyer au m² calculés: {stats['loyer_m2_calcules']}")
    print(f"✅ Régions déterminées: {stats['regions_determinees']}")
    print(f"✅ Équipements nettoyés: {stats['equipements_nettoyes']}")
    print(f"✅ Caractéristiques normalisées: {stats['caracteristiques_normalisees']}")
    print(f"✅ Infos supplémentaires normalisées: {stats['infos_supp_normalisees']}")
    print(f"✅ Conditions de location normalisées: {stats['conditions_normalisees']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ Localisations normalisées: {stats['localisations_normalisees']}")
    print(f"✅ Images filtrées: {stats['images_filtrees']}")
    print(f"✅ Types de bureau normalisés: {stats['types_bureau_normalises']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des JSON de location de bureaux")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()