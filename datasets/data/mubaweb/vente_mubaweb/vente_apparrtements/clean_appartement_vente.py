"""
Script de nettoyage COMPLET pour Vente d'Appartements
Nettoie et normalise TOUS les champs :
- Prix, surface, localisation
- Caractéristiques, équipements
- Informations supplémentaires
- Contacts, dates, etc.
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

ETAT_MAPPING = {
    "projet neuf": "Projet neuf",
    "project neuf": "Projet neuf",
    "neuf": "Neuf",
    "bon état / habitable": "Bon état",
    "bon etat": "Bon état",
    "bon état": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "à rénover": "À rénover",
    "a renover": "À rénover",
    "rénové": "Rénové",
    "renove": "Rénové"
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

STANDING_MAPPING = {
    "haut standing": {"code": "high", "label": "Haut standing"},
    "haut standing de luxe": {"code": "luxury", "label": "Haut standing de luxe"},
    "de luxe": {"code": "luxury", "label": "De luxe"},
    "luxe": {"code": "luxury", "label": "Luxe"},
    "standing": {"code": "standard", "label": "Standard"},
    "économique": {"code": "economic", "label": "Économique"},
    "standard": {"code": "standard", "label": "Standard"}
}

STATUT_CONSTRUCTION_MAPPING = {
    "en cours de construction": {"code": "in_progress", "label": "En cours de construction"},
    "en cours": {"code": "in_progress", "label": "En cours"},
    "finalisé": {"code": "completed", "label": "Finalisé"},
    "finalise": {"code": "completed", "label": "Finalisé"},
    "projet neuf": {"code": "new_project", "label": "Projet neuf"},
    "project neuf": {"code": "new_project", "label": "Projet neuf"},
    "neuf": {"code": "new", "label": "Neuf"}
}

CHAUFFAGE_MAPPING = {
    "central": "Central",
    "au sol": "Au sol",
    "électrique": "Électrique",
    "electrique": "Électrique",
    "gaz": "Gaz"
}

CLIMATISATION_MAPPING = {
    "centrale": "Centrale",
    "central": "Centrale",
    "split": "Split"
}

VUE_MAPPING = {
    "mer": "Mer",
    "lac": "Lac",
    "montagne": "Montagne",
    "dégagée": "Dégagée",
    "degagee": "Dégagée",
    "imprenable": "Imprenable"
}


# ========== FONCTIONS DE NETTOYAGE ==========

def clean_text(text: Any) -> str:
    """Nettoie un texte (espaces multiples, retours ligne)"""
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
        # Vérifier si le prix est présent dans le texte
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


def clean_etat_bien(etat: Any) -> Optional[str]:
    """Normalise l'état du bien"""
    if not etat:
        return None
    
    etat_str = str(etat).lower().strip()
    
    for key, value in ETAT_MAPPING.items():
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


def clean_type_sol(type_sol: Any) -> Optional[str]:
    """Normalise le type de sol"""
    if not type_sol:
        return None
    
    type_sol_str = str(type_sol).lower().strip()
    
    for key, value in SOL_MAPPING.items():
        if key in type_sol_str:
            return value
    
    return str(type_sol).title()


def clean_standing(standing: Any) -> Optional[Dict[str, str]]:
    """Normalise le standing en objet {code, label}"""
    if not standing:
        return None
    
    if isinstance(standing, dict):
        return standing
    
    standing_str = str(standing).lower().strip()
    
    for key, value in STANDING_MAPPING.items():
        if key in standing_str:
            return value
    
    return {"code": "other", "label": str(standing)}


def clean_statut_construction(statut: Any) -> Optional[Dict[str, str]]:
    """Normalise le statut de construction"""
    if not statut:
        return None
    
    if isinstance(statut, dict):
        return statut
    
    statut_str = str(statut).lower().strip()
    
    for key, value in STATUT_CONSTRUCTION_MAPPING.items():
        if key in statut_str:
            return value
    
    return {"code": "other", "label": str(statut)}


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


def clean_vue_type(vue: Any) -> Optional[str]:
    """Normalise le type de vue"""
    if not vue:
        return None
    
    vue_str = str(vue).lower().strip()
    
    for key, value in VUE_MAPPING.items():
        if key in vue_str:
            return value
    
    return str(vue).title()


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
            # Enlever les numéros au début
            item = re.sub(r'^\d+[\s\.\-]*', '', item)
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
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
        
        if key_clean in ['etat', 'état']:
            result['etat'] = clean_etat_bien(value)
        elif key_clean in ['etage', 'étage', 'etage_du_bien']:
            etage_num = clean_number(value)
            if etage_num is not None:
                result['etage'] = etage_num
        elif key_clean in ['orientation']:
            result['orientation'] = clean_orientation(value)
        elif key_clean in ['type_du_sol', 'type_sol', 'sol']:
            result['type_sol'] = clean_type_sol(value)
        elif key_clean in ['standing']:
            result['standing'] = clean_standing(value)
        elif key_clean in ['statut', 'état_construction']:
            result['statut_construction'] = clean_statut_construction(value)
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
        
        # Convertir en booléen si c'est Oui/Non
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
    """Nettoie la liste des images (filtre les logos)"""
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
    
    # Filtrer les URLs
    filtered = []
    exclude_patterns = [r'logo', r'loading\.gif', r'favicon', r'banks?/', r'assets/']
    
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
    
    # Supprimer les doublons
    seen = set()
    unique = []
    for url in filtered:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    
    return unique


def clean_date(date_str: Any) -> Optional[str]:
    """Normalise une date au format ISO"""
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


def clean_type_appartement(type_app: str) -> str:
    """Normalise le type d'appartement (S1, S2, S3, etc.)"""
    if not type_app:
        return ""
    
    type_app = str(type_app).upper().strip()
    
    # Patterns: S1, S2, S3, S+1, S+2, S+3, Studio/S1, etc.
    match = re.search(r'S[\+\s]*(\d+)', type_app)
    if match:
        return f"S{match.group(1)}"
    
    if 'STUDIO' in type_app.upper():
        return "Studio"
    
    return type_app.title()


# ========== FONCTION PRINCIPALE DE NETTOYAGE ==========

def clean_listing(listing: Dict) -> Dict:
    """
    Nettoie complètement un listing de vente d'appartement
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'titre', 'url', 'description_courte', 'description_complete',
                     'page_source', 'is_valid', 'reference', 'nom_agence', 'residence']
    
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
    
    # Région (déduite de la ville)
    region = listing.get('region') or clean_region_from_ville(cleaned['ville'])
    cleaned['region'] = clean_text(region) if region else ""
    
    # ===== 3. PRIX =====
    prix = clean_number(listing.get('prix'), 0)
    cleaned['prix'] = prix
    
    cleaned['prix_text'] = clean_prix_text(listing.get('prix_text'), prix)
    
    # Prix au m² (calculé si disponible)
    surface = listing.get('surface')
    if prix and surface and surface > 0:
        cleaned['prix_m2'] = round(prix / surface, 2)
    else:
        cleaned['prix_m2'] = None
    
    # Type de prix (starting_from, etc.)
    if listing.get('prix_type'):
        cleaned['prix_type'] = listing['prix_type']
    
    # ===== 4. SURFACE =====
    surface = clean_number(listing.get('surface'))
    cleaned['surface'] = surface if surface and surface > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    # ===== 5. TYPE D'APPARTEMENT ET NOMBRES =====
    cleaned['type_appartement'] = clean_type_appartement(listing.get('type_appartement', ''))
    
    numeric_fields = ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'etage']
    for field in numeric_fields:
        val = listing.get(field)
        if val is not None and val != '':
            cleaned[field] = clean_number(val)
        else:
            cleaned[field] = None
    
    # Si étage est 0, c'est RDC
    if cleaned.get('etage') == 0:
        cleaned['etage_label'] = 'RDC'
    elif cleaned.get('etage'):
        cleaned['etage_label'] = f"{cleaned['etage']}ème"
    
    # ===== 6. MEUBLÉ =====
    meuble = listing.get('meuble')
    if meuble is not None:
        if isinstance(meuble, bool):
            cleaned['meuble'] = meuble
        elif isinstance(meuble, str):
            cleaned['meuble'] = meuble.lower() in ['oui', 'true', 'yes', '1']
        else:
            cleaned['meuble'] = bool(meuble)
    else:
        cleaned['meuble'] = False
    
    # ===== 7. ÉQUIPEMENTS =====
    cleaned['equipements'] = clean_equipements(listing.get('equipements', []))
    
    # ===== 8. CARACTÉRISTIQUES =====
    caracs = listing.get('caracteristiques') or listing.get('caracs')
    cleaned['caracteristiques'] = clean_caracteristiques(caracs)
    
    # ===== 9. INFORMATIONS SUPPLÉMENTAIRES =====
    info_supp = listing.get('informations_supplementaires') or listing.get('informations_supplementaires_parse')
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(info_supp)
    
    # ===== 10. CONTACT INFO =====
    contact = listing.get('contact_info') or listing.get('contact_info_parse')
    cleaned['contact_info'] = clean_contact_info(contact)
    
    # ===== 11. LOCALISATION GPS =====
    gps = listing.get('localisation') or listing.get('gps')
    cleaned['localisation'] = clean_localisation(gps)
    
    # ===== 12. IMAGES =====
    cleaned['images'] = clean_images(listing.get('images', []))
    
    # ===== 13. DATES =====
    cleaned['date_scraping'] = clean_date(listing.get('date_scraping'))
    cleaned['date_publication'] = listing.get('date_publication')
    cleaned['date_livraison'] = listing.get('date_livraison') or listing.get('date_livraison_extrait')
    
    # ===== 14. SURFACES EXTÉRIEURES =====
    ext_surfaces = ['jardin_surface', 'terrasse_surface', 'balcon_surface']
    for field in ext_surfaces:
        val = listing.get(field) or listing.get(f"{field}_extrait")
        cleaned[field] = clean_number(val)
    
    # ===== 15. PARKING =====
    cleaned['parking_nombre'] = clean_number(listing.get('parking_nombre') or listing.get('parking_nombre_extrait'))
    cleaned['parking_type'] = clean_text(listing.get('parking_type') or listing.get('parking_type_extrait'))
    
    # ===== 16. CHAUFFAGE ET CLIMATISATION =====
    cleaned['chauffage_type'] = clean_chauffage_type(
        listing.get('chauffage_type') or listing.get('chauffage_type_extrait')
    )
    cleaned['climatisation_type'] = clean_climatisation_type(
        listing.get('climatisation_type') or listing.get('climatisation_type_extrait')
    )
    
    # ===== 17. VUE =====
    cleaned['vue_type'] = clean_vue_type(
        listing.get('vue_type') or listing.get('vue_type_extrait')
    )
    
    # ===== 18. PRÉSENCES =====
    bool_fields = ['a_dressing', 'a_cellier', 'a_chambre_service', 'a_concierge', 'a_piscine', 'a_salle_sport']
    for field in bool_fields:
        cleaned[field] = bool(listing.get(field, False))
    
    # ===== 19. ORIENTATION ET TYPE DE SOL =====
    cleaned['orientation'] = clean_orientation(
        listing.get('orientation') or listing.get('orientation_extrait')
    )
    cleaned['type_sol'] = clean_type_sol(
        listing.get('type_sol') or listing.get('type_sol_extrait')
    )
    
    # ===== 20. ÉTAT, STANDING, STATUT =====
    cleaned['etat_bien'] = clean_etat_bien(
        listing.get('etat_bien') or listing.get('caracs_etat_bien')
    )
    cleaned['standing'] = clean_standing(
        listing.get('standing') or listing.get('standing_extrait') or listing.get('caracs_standing')
    )
    cleaned['statut_construction'] = clean_statut_construction(
        listing.get('statut_construction') or listing.get('statut_construction_extrait') or listing.get('caracs_statut_construction')
    )
    
    return cleaned


def validate_listing(listing: Dict) -> List[str]:
    """
    Valide un listing et retourne les avertissements
    """
    warnings = []
    
    # Champs obligatoires
    if not listing.get('id'):
        warnings.append("ID manquant")
    
    if not listing.get('url'):
        warnings.append("URL manquante")
    
    # Cohérence des prix
    prix = listing.get('prix')
    prix_text = listing.get('prix_text')
    
    if prix and prix > 0 and prix_text:
        if str(int(prix)) not in prix_text and 'consulter' not in prix_text.lower():
            warnings.append(f"Incohérence prix: {prix} vs {prix_text}")
    
    # Surface
    surface = listing.get('surface')
    surface_text = listing.get('surface_text')
    if surface and surface > 0 and surface_text:
        if str(int(surface)) not in surface_text:
            warnings.append(f"Incohérence surface: {surface} vs {surface_text}")
    
    # Localisation
    if not listing.get('ville'):
        warnings.append("Ville manquante")
    
    return warnings


def clean_json_file(input_path: str, output_path: Optional[str] = None, validate: bool = False):
    """
    Nettoie un fichier JSON complet
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
        'contacts_normalises': 0,
        'localisations_normalisees': 0,
        'images_filtrees': 0
    }
    
    for i, listing in enumerate(listings):
        try:
            cleaned = clean_listing(listing)
            cleaned_listings.append(cleaned)
            
            # Statistiques
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
    
    # Mettre à jour les données
    data['listings'] = cleaned_listings
    
    # Métadonnées
    if 'metadata' not in data:
        data['metadata'] = {}
    
    data['metadata']['cleaning_date'] = datetime.now().isoformat() + 'Z'
    data['metadata']['listings_nettoyes'] = len(cleaned_listings)
    data['metadata']['statistiques_nettoyage'] = stats
    
    if validate and validation_warnings:
        data['metadata']['validation_warnings'] = validation_warnings
        print(f"⚠️ {len(validation_warnings)} listings avec des avertissements")
    
    # Sauvegarder
    out = output_path or str(path.parent / f"{path.stem}_clean.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES DE NETTOYAGE - VENTE APPARTEMENTS")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Prix text nettoyés: {stats['prix_text_nettoyes']}")
    print(f"✅ Surface text nettoyées: {stats['surface_text_nettoyes']}")
    print(f"✅ Prix au m² calculés: {stats['prix_m2_calcules']}")
    print(f"✅ Régions déterminées: {stats['regions_determinees']}")
    print(f"✅ Équipements nettoyés: {stats['equipements_nettoyes']}")
    print(f"✅ Caractéristiques normalisées: {stats['caracteristiques_normalisees']}")
    print(f"✅ Infos supplémentaires normalisées: {stats['infos_supp_normalisees']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ Localisations normalisées: {stats['localisations_normalisees']}")
    print(f"✅ Images filtrées: {stats['images_filtrees']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des JSON de vente d'appartements")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données après nettoyage')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()