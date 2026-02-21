"""
Script de nettoyage COMPLET pour Location Immobilier Neuf
Nettoie TOUS les champs :
- Champs classiques (prix, surface, localisation, etc.)
- Nouveaux champs spécifiques au neuf
- Normalise les formats, les booléens, les listes, les objets JSON
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


# ========== CONSTANTES POUR NORMALISATION ==========

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

STANDING_MAPPING = {
    "haut standing": {"code": "high", "label": "Haut standing"},
    "haut standing de luxe": {"code": "luxury", "label": "Haut standing de luxe"},
    "de luxe": {"code": "luxury", "label": "De luxe"},
    "luxe": {"code": "luxury", "label": "Luxe"},
    "standing": {"code": "standard", "label": "Standard"},
    "économique": {"code": "economic", "label": "Économique"},
    "standing économique": {"code": "economic", "label": "Économique"}
}

STATUT_CONSTRUCTION_MAPPING = {
    "en cours de construction": {"code": "in_progress", "label": "En cours de construction"},
    "en cours": {"code": "in_progress", "label": "En cours"},
    "finalisé": {"code": "completed", "label": "Finalisé"},
    "livré": {"code": "completed", "label": "Livré"},
    "achevée": {"code": "completed", "label": "Achevée"},
    "projet neuf": {"code": "new_project", "label": "Projet neuf"},
    "sur plan": {"code": "off_plan", "label": "Sur plan"},
    "livraison immédiate": {"code": "immediate", "label": "Livraison immédiate"}
}

REGIONS_MAPPING = {
    "tunis": "Tunis", "la marsa": "Tunis", "carthage": "Tunis", "le kram": "Tunis",
    "ariana": "Ariana", "ennasr": "Ariana", "manzah": "Ariana", "soukra": "Ariana", "raoued": "Ariana",
    "ben arous": "Ben Arous", "boumhel": "Ben Arous", "mohammedia": "Ben Arous",
    "nabeul": "Nabeul", "hammamet": "Nabeul",
    "sousse": "Sousse", "monastir": "Monastir", "mahdia": "Mahdia",
    "sfax": "Sfax", "bizerte": "Bizerte", "zaghouan": "Zaghouan"
}

ETAT_MAPPING = {
    "bon état": "Bon état",
    "bon état / habitable": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "neuf": "Neuf",
    "à rénover": "À rénover",
    "rénové": "Rénové"
}

ORIENTATION_MAPPING = {
    "nord": "Nord", "sud": "Sud", "est": "Est", "ouest": "Ouest",
    "nord-est": "Nord-Est", "nord-ouest": "Nord-Ouest",
    "sud-est": "Sud-Est", "sud-ouest": "Sud-Ouest"
}

SOL_MAPPING = {
    "carrelage": "Carrelage", "marbre": "Marbre", "parquet": "Parquet",
    "stratifié": "Stratifié", "moquette": "Moquette", "béton ciré": "Béton ciré"
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
            return float(value) if isinstance(value, float) else value
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


def clean_prix_text(prix_text: Any, prix: float, prix_type: str = None) -> str:
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
        if prix_type and 'starting_from' in str(prix_type):
            if not cleaned.lower().startswith('à partir de'):
                cleaned = f"À partir de {cleaned}"
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


def clean_prix_type(prix_type: Any) -> Dict[str, str]:
    """Normalise le type de prix"""
    if not prix_type:
        return {"code": "unknown", "label": ""}
    
    if isinstance(prix_type, dict):
        return prix_type
    
    prix_type_str = str(prix_type).lower().strip()
    
    for key, code in PRIX_TYPE_MAPPING.items():
        if key in prix_type_str:
            return {"code": code, "label": str(prix_type)}
    
    return {"code": "other", "label": str(prix_type)}


def clean_standing(standing: Any) -> Dict[str, str]:
    """Normalise le standing"""
    if not standing:
        return {"code": "unknown", "label": ""}
    
    if isinstance(standing, dict):
        return standing
    
    standing_str = str(standing).lower().strip()
    
    for key, value in STANDING_MAPPING.items():
        if key in standing_str:
            return value
    
    return {"code": "other", "label": str(standing)}


def clean_statut_construction(statut: Any) -> Dict[str, str]:
    """Normalise le statut de construction"""
    if not statut:
        return {"code": "unknown", "label": ""}
    
    if isinstance(statut, dict):
        return statut
    
    statut_str = str(statut).lower().strip()
    
    for key, value in STATUT_CONSTRUCTION_MAPPING.items():
        if key in statut_str:
            return value
    
    return {"code": "other", "label": str(statut)}


def clean_region_from_ville(ville: str) -> Optional[str]:
    """Détermine la région à partir de la ville"""
    if not ville:
        return None
    
    ville_lower = ville.lower().strip()
    
    for key, region in REGIONS_MAPPING.items():
        if key in ville_lower:
            return region
    
    return None


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


def clean_caracteristiques_detaillees(caracs: Any) -> Dict[str, Any]:
    """Nettoie les caractéristiques détaillées"""
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
        key_clean = key.lower().strip().replace(' ', '_').replace('-', '_')
        
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers and key_clean in ['nombre_appartements', 'nombre_niveaux', 'surface_terrain', 'nb_appartements']:
                result[key_clean] = int(numbers[0])
            else:
                result[key_clean] = value
        else:
            result[key_clean] = value
    
    return result


def clean_images_neuf(images_field: Any, images_completes: Any, logo_agence: Any) -> Dict[str, Any]:
    """Nettoie et fusionne les images"""
    result = {'images': [], 'logo_agence': None}
    
    # Images principales
    if isinstance(images_field, str):
        if ';' in images_field:
            result['images'].extend([img.strip() for img in images_field.split(';') if img.strip()])
        else:
            result['images'].append(images_field.strip())
    elif isinstance(images_field, list):
        result['images'].extend(images_field)
    
    # Images complètes
    if images_completes:
        if isinstance(images_completes, str):
            if ';' in images_completes:
                result['images'].extend([img.strip() for img in images_completes.split(';') if img.strip()])
            else:
                result['images'].append(images_completes.strip())
        elif isinstance(images_completes, list):
            result['images'].extend(images_completes)
    
    # Logo
    if logo_agence and isinstance(logo_agence, str):
        if 'nologo' not in logo_agence.lower():
            result['logo_agence'] = logo_agence.strip()
    
    # Filtrer les URLs invalides
    valid_images = []
    for img in result['images']:
        if isinstance(img, str) and img.startswith(('http://', 'https://')):
            img_lower = img.lower()
            if not any(x in img_lower for x in ['logo', 'favicon', 'loading', 'spacer', 'nologo']):
                valid_images.append(img)
    
    # Supprimer doublons
    seen = set()
    unique_images = []
    for img in valid_images:
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
    
    result['images'] = unique_images
    
    return result


def clean_videos(videos_field: Any, videos_parse: Any = None) -> List[Dict[str, Any]]:
    """Nettoie les vidéos"""
    if videos_parse and isinstance(videos_parse, list):
        return videos_parse
    
    if not videos_field:
        return []
    
    videos = []
    
    if isinstance(videos_field, str):
        if ';' in videos_field:
            urls = [url.strip() for url in videos_field.split(';') if url.strip()]
        else:
            urls = [videos_field.strip()]
        
        for url in urls:
            if 'youtube' in url or 'youtu.be' in url:
                video_id = None
                if 'embed/' in url:
                    video_id = url.split('embed/')[-1].split('?')[0]
                elif 'watch?v=' in url:
                    video_id = url.split('watch?v=')[-1].split('&')[0]
                elif 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[-1].split('?')[0]
                
                if video_id:
                    videos.append({
                        'id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'embed': f"https://www.youtube.com/embed/{video_id}",
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/0.jpg",
                        'type': 'youtube'
                    })
    
    return videos


def clean_plans(plans_field: Any) -> List[str]:
    """Nettoie les plans"""
    if not plans_field:
        return []
    
    if isinstance(plans_field, list):
        return [p for p in plans_field if isinstance(p, str) and p.startswith(('http://', 'https://'))]
    
    if isinstance(plans_field, str):
        if ';' in plans_field:
            return [p.strip() for p in plans_field.split(';') if p.strip() and p.startswith(('http://', 'https://'))]
        else:
            return [plans_field.strip()] if plans_field.startswith(('http://', 'https://')) else []
    
    return []


def clean_json_object(json_str: str) -> Optional[Dict]:
    """Nettoie un objet JSON"""
    if not json_str or json_str == "{}":
        return None
    
    try:
        if isinstance(json_str, str):
            obj = json.loads(json_str)
            return obj if obj else None
        elif isinstance(json_str, dict):
            return json_str if json_str else None
    except:
        pass
    
    return None


def clean_contact_info(contact: Any) -> Optional[Dict]:
    """Nettoie les informations de contact"""
    if not contact:
        return None
    
    try:
        if isinstance(contact, str):
            obj = json.loads(contact)
        elif isinstance(contact, dict):
            obj = contact
        else:
            return None
        
        if not obj:
            return None
        
        # Normaliser les booléens
        if 'formulaire_contact' in obj:
            val = str(obj['formulaire_contact']).lower()
            obj['formulaire_contact'] = val in ['disponible', 'oui', 'yes', 'true', '1']
        
        return obj
    except:
        return None


def clean_caracteristiques(caracs: Any) -> List[str]:
    """Nettoie les caractéristiques (liste)"""
    if not caracs:
        return []
    
    if isinstance(caracs, list):
        return [str(c).strip() for c in caracs if c]
    elif isinstance(caracs, str):
        try:
            parsed = json.loads(caracs)
            if isinstance(parsed, list):
                return [str(c).strip() for c in parsed if c]
        except:
            return [caracs.strip()] if caracs.strip() else []
    
    return []


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

def clean_listing_neuf_complet(listing: Dict) -> Dict:
    """
    Nettoie complètement un listing d'immobilier neuf
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'promotion_id', 'titre', 'url', 'description_courte', 
                     'description_complete', 'page_source', 'has_video']
    
    for field in simple_fields:
        if field in listing and listing[field]:
            cleaned[field] = clean_text(listing[field])
        else:
            if field == 'has_video':
                cleaned[field] = False
            else:
                cleaned[field] = ""
    
    # ===== 2. LOCALISATION =====
    cleaned['ville'] = clean_text(listing.get('ville', ''))
    cleaned['quartier'] = clean_text(listing.get('quartier', ''))
    cleaned['adresse'] = clean_text(listing.get('adresse', ''))
    cleaned['region'] = clean_text(listing.get('region', '')) or clean_region_from_ville(cleaned['ville'])
    
    # ===== 3. PRIX =====
    prix = clean_number(listing.get('prix'), 0)
    cleaned['prix'] = prix
    
    prix_type_obj = clean_prix_type(listing.get('prix_type'))
    cleaned['prix_type'] = prix_type_obj
    
    cleaned['prix_text'] = clean_prix_text(
        listing.get('prix_text'), 
        prix,
        prix_type_obj.get('code')
    )
    
    # Prix au m²
    prix_m2 = clean_number(listing.get('prix_m2'))
    cleaned['prix_m2'] = prix_m2 if prix_m2 and prix_m2 > 0 else None
    
    # ===== 4. SURFACE =====
    surface = clean_number(listing.get('surface'))
    cleaned['surface'] = surface if surface and surface > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    # ===== 5. TYPE DE BIEN ET STANDING =====
    cleaned['type_bien'] = clean_text(listing.get('type_bien', ''))
    cleaned['standing'] = clean_standing(listing.get('standing'))
    cleaned['statut_construction'] = clean_statut_construction(listing.get('statut_construction'))
    cleaned['date_livraison'] = listing.get('date_livraison') or listing.get('date_livraison_extrait')
    
    # ===== 6. NOMBRES =====
    numeric_fields = ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'nombre_appartements']
    for field in numeric_fields:
        val = listing.get(field)
        if val and isinstance(val, (int, float)) and val > 0:
            cleaned[field] = int(val) if isinstance(val, (int, float)) else val
        else:
            cleaned[field] = None
    
    # ===== 7. CARACTÉRISTIQUES ET ÉQUIPEMENTS =====
    cleaned['caracteristiques'] = clean_caracteristiques(listing.get('caracteristiques', []))
    cleaned['equipements'] = clean_equipements(listing.get('equipements', []))
    
    # ===== 8. CARACTÉRISTIQUES DÉTAILLÉES =====
    caracs_det = listing.get('caracteristiques_detaillees') or listing.get('caracteristiques_detaillees_parse')
    cleaned['caracteristiques_detaillees'] = clean_caracteristiques_detaillees(caracs_det)
    
    # ===== 9. ÉQUIPEMENTS COMPLETS =====
    cleaned['equipements_complets'] = clean_equipements(listing.get('equipements_complets', ''))
    
    # ===== 10. IMAGES ET LOGO =====
    images_data = clean_images_neuf(
        listing.get('images', []),
        listing.get('images_completes', ''),
        listing.get('logo_agence', '')
    )
    cleaned['images'] = images_data['images']
    cleaned['logo_agence'] = images_data['logo_agence']
    cleaned['nom_agence'] = clean_text(listing.get('nom_agence', ''))
    
    # ===== 11. VIDÉOS =====
    videos = listing.get('videos_parse') or listing.get('videos_completes')
    cleaned['videos'] = clean_videos(videos)
    cleaned['has_video'] = len(cleaned['videos']) > 0
    
    # ===== 12. PLANS =====
    cleaned['plans'] = clean_plans(listing.get('plans', ''))
    
    # ===== 13. OBJETS JSON =====
    json_fields = ['localisation_exacte', 'informations_promotion', 'conditions_vente']
    for field in json_fields:
        cleaned[field] = clean_json_object(listing.get(field, '{}'))
    
    # ===== 14. PROMOTEUR INFO =====
    promoteur = listing.get('promoteur_info') or listing.get('promoteur_info_extrait')
    cleaned['promoteur_info'] = clean_json_object(promoteur) if promoteur else None
    
    # ===== 15. CONTACT INFO =====
    cleaned['contact_info'] = clean_contact_info(listing.get('contact_info'))
    
    # ===== 16. DATES =====
    cleaned['date_scraping'] = clean_date(listing.get('date_scraping'))
    cleaned['date_publication'] = listing.get('date_publication')
    
    # ===== 17. CHAMPS EXTRAITS DES CARACTÉRISTIQUES =====
    cleaned['etat_bien'] = clean_etat_bien(listing.get('etat_bien'))
    cleaned['orientation'] = clean_orientation(listing.get('orientation'))
    cleaned['type_sol'] = clean_type_sol(listing.get('type_sol'))
    
    # ===== 18. IS VALID =====
    cleaned['is_valid'] = listing.get('is_valid', True)
    
    return cleaned


def validate_listing_neuf_complet(listing: Dict) -> List[str]:
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
        if str(int(prix)) not in str(prix_text) and 'consulter' not in prix_text.lower():
            warnings.append(f"Incohérence prix: {prix} vs {prix_text}")
    
    # Standing
    standing = listing.get('standing', {})
    if standing and isinstance(standing, dict):
        if 'code' not in standing or 'label' not in standing:
            warnings.append("Standing mal formaté")
    
    # Statut construction
    statut = listing.get('statut_construction', {})
    if statut and isinstance(statut, dict):
        if 'code' not in statut or 'label' not in statut:
            warnings.append("Statut construction mal formaté")
    
    # Images
    if not listing.get('images') and not listing.get('logo_agence'):
        warnings.append("Aucune image ni logo")
    
    return warnings


def clean_json_file_neuf_complet(input_path: str, output_path: Optional[str] = None, validate: bool = False):
    """
    Nettoie un fichier JSON d'immobilier neuf
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
        'prix_types_normalises': 0,
        'standings_normalises': 0,
        'statuts_normalises': 0,
        'regions_determinees': 0,
        'equipements_nettoyes': 0,
        'caracs_detaillees_normalisees': 0,
        'equipements_complets_nettoyes': 0,
        'images_fusionnees': 0,
        'videos_parsees': 0,
        'plans_nettoyes': 0,
        'json_objects_nettoyes': 0,
        'contacts_normalises': 0,
        'etats_normalises': 0,
        'orientations_normalisees': 0,
        'sols_normalises': 0
    }
    
    for i, listing in enumerate(listings):
        try:
            cleaned = clean_listing_neuf_complet(listing)
            cleaned_listings.append(cleaned)
            
            # Statistiques
            if cleaned.get('prix_text') != listing.get('prix_text'):
                stats['prix_text_nettoyes'] += 1
            if cleaned.get('surface_text') != listing.get('surface_text'):
                stats['surface_text_nettoyes'] += 1
            if cleaned.get('prix_type') and isinstance(cleaned['prix_type'], dict):
                stats['prix_types_normalises'] += 1
            if cleaned.get('standing') and isinstance(cleaned['standing'], dict):
                stats['standings_normalises'] += 1
            if cleaned.get('statut_construction') and isinstance(cleaned['statut_construction'], dict):
                stats['statuts_normalises'] += 1
            if cleaned.get('region') and not listing.get('region'):
                stats['regions_determinees'] += 1
            if len(cleaned.get('equipements', [])) != len(listing.get('equipements', [])):
                stats['equipements_nettoyes'] += 1
            if cleaned.get('caracteristiques_detaillees'):
                stats['caracs_detaillees_normalisees'] += 1
            if cleaned.get('equipements_complets'):
                stats['equipements_complets_nettoyes'] += 1
            if len(cleaned.get('images', [])) > 0 and (listing.get('images_completes') or listing.get('logo_agence')):
                stats['images_fusionnees'] += 1
            if cleaned.get('videos'):
                stats['videos_parsees'] += 1
            if cleaned.get('plans'):
                stats['plans_nettoyes'] += 1
            if any(cleaned.get(field) is None for field in ['localisation_exacte', 'informations_promotion', 'conditions_vente']):
                stats['json_objects_nettoyes'] += 1
            if cleaned.get('contact_info') and not listing.get('contact_info'):
                stats['contacts_normalises'] += 1
            if cleaned.get('etat_bien') and cleaned['etat_bien'] != listing.get('etat_bien'):
                stats['etats_normalises'] += 1
            if cleaned.get('orientation') and cleaned['orientation'] != listing.get('orientation'):
                stats['orientations_normalisees'] += 1
            if cleaned.get('type_sol') and cleaned['type_sol'] != listing.get('type_sol'):
                stats['sols_normalises'] += 1
            
            if validate:
                warnings = validate_listing_neuf_complet(cleaned)
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
    data['metadata']['type'] = 'immobilier_neuf_clean'
    
    if validate and validation_warnings:
        data['metadata']['validation_warnings'] = validation_warnings
        print(f"⚠️ {len(validation_warnings)} listings avec des avertissements")
    
    # Sauvegarder
    out = output_path or str(path.parent / f"{path.stem}_clean.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES DE NETTOYAGE COMPLET - IMMOBILIER NEUF")
    print("="*70)
    print(f"✅ Listings traités: {stats['total']}")
    print(f"✅ Prix text nettoyés: {stats['prix_text_nettoyes']}")
    print(f"✅ Surface text nettoyées: {stats['surface_text_nettoyes']}")
    print(f"✅ Prix types normalisés: {stats['prix_types_normalises']}")
    print(f"✅ Standings normalisés: {stats['standings_normalises']}")
    print(f"✅ Statuts construction normalisés: {stats['statuts_normalises']}")
    print(f"✅ Régions déterminées: {stats['regions_determinees']}")
    print(f"✅ Équipements nettoyés: {stats['equipements_nettoyes']}")
    print(f"✅ Caractéristiques détaillées normalisées: {stats['caracs_detaillees_normalisees']}")
    print(f"✅ Équipements complets nettoyés: {stats['equipements_complets_nettoyes']}")
    print(f"✅ Images fusionnées: {stats['images_fusionnees']}")
    print(f"✅ Vidéos parsées: {stats['videos_parsees']}")
    print(f"✅ Plans nettoyés: {stats['plans_nettoyes']}")
    print(f"✅ Objets JSON nettoyés: {stats['json_objects_nettoyes']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ États bien normalisés: {stats['etats_normalises']}")
    print(f"✅ Orientations normalisées: {stats['orientations_normalisees']}")
    print(f"✅ Types sol normalisés: {stats['sols_normalises']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage COMPLET des JSON d'immobilier neuf")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données après nettoyage')
    args = parser.parse_args()
    
    clean_json_file_neuf_complet(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()