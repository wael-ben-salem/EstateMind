"""
Script de nettoyage pour Vente de Locaux Commerciaux
Nettoie et normalise TOUS les champs spécifiques aux locaux commerciaux
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
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "à rénover": "À rénover"
}

TYPES_LOCAUX_NORMALISES = {
    "local commercial": "Local commercial",
    "bureau commercial": "Bureau commercial",
    "bureau": "Bureau",
    "magasin": "Magasin",
    "boutique": "Boutique",
    "restaurant": "Restaurant",
    "café": "Café",
    "showroom": "Showroom",
    "entrepôt": "Entrepôt",
    "dépôt": "Dépôt",
    "atelier": "Atelier"
}

ZONES_ACTIVITE_MAPPING = {
    "commerciale": "Commerciale",
    "bureaux": "Bureaux",
    "mixte": "Mixte",
    "industrielle": "Industrielle",
    "artisanale": "Artisanale",
    "restauration": "Restauration",
    "services": "Services"
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


def clean_type_local(type_local: Any) -> str:
    """Normalise le type de local"""
    if not type_local:
        return ""
    
    type_local_str = str(type_local).lower().strip()
    
    for key, value in TYPES_LOCAUX_NORMALISES.items():
        if key in type_local_str:
            return value
    
    return str(type_local).title()


def clean_zone_activite(zone: Any) -> Optional[str]:
    """Normalise la zone d'activité"""
    if not zone:
        return None
    
    zone_str = str(zone).lower().strip()
    
    for key, value in ZONES_ACTIVITE_MAPPING.items():
        if key in zone_str:
            return value
    
    return str(zone).title()


def clean_etat_bien(etat: Any) -> Optional[str]:
    """Normalise l'état du bien"""
    if not etat:
        return None
    
    etat_str = str(etat).lower().strip()
    
    for key, value in ETAT_MAPPING.items():
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


def clean_amenities_commercial(amenities: Any) -> List[str]:
    """Nettoie les amenities commerciales"""
    return clean_equipements(amenities)


def clean_catalogue_urls(urls: Any) -> List[str]:
    """Nettoie la liste des URLs de catalogues"""
    if not urls:
        return []
    
    if isinstance(urls, list):
        return [url.strip() for url in urls if url and url.startswith(('http://', 'https://'))]
    elif isinstance(urls, str):
        if ';' in urls:
            return [url.strip() for url in urls.split(';') if url.strip() and url.startswith(('http://', 'https://'))]
        else:
            return [urls.strip()] if urls.startswith(('http://', 'https://')) else []
    
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
            result['etat'] = clean_etat_bien(value)
        elif key_clean == 'type_du_sol':
            result['type_sol'] = str(value).title()
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
            result['etat'] = clean_etat_bien(value)
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
            elif 'catalogue_pdf' in key_clean and 'urls' not in key_clean:
                if isinstance(value, str):
                    result['catalogue_disponible'] = value.lower() in ['disponible', 'oui', 'true']
            elif 'catalogue_pdf_urls' in key_clean:
                result['catalogue_urls'] = clean_catalogue_urls(value)
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
    Nettoie complètement un listing de local commercial
    """
    cleaned = {}
    
    # ===== 1. CHAMPS SIMPLES =====
    simple_fields = ['id', 'titre', 'url', 'description_courte', 'description_complete',
                     'page_source', 'is_valid', 'type_transaction']
    
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
    
    # ===== 4. SURFACE =====
    surface = clean_number(listing.get('surface'))
    cleaned['surface'] = surface if surface and surface > 0 else None
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), cleaned['surface'] or 0)
    
    # Surfaces additionnelles
    surface_fields = ['surface_mezzanine', 'surface_terrasse']
    for field in surface_fields:
        val = listing.get(field)
        cleaned[field] = clean_number(val)
    
    # ===== 5. TYPE DE LOCAL =====
    cleaned['type_local'] = clean_type_local(listing.get('type_local', ''))
    
    # ===== 6. NOMBRES =====
    numeric_fields = ['nombre_sdb', 'etage', 'nombre_vitrines', 'parking_nombre']
    for field in numeric_fields:
        val = listing.get(field)
        cleaned[field] = clean_number(val)
    
    # ===== 7. CARACTÉRISTIQUES SPÉCIFIQUES =====
    bool_fields = [
        'a_mezzanine', 'double_hauteur', 'a_terrasse', 'acces_livraison',
        'possibilite_enseigne', 'a_alarme', 'a_monte_charge', 'accessibilite_pmr'
    ]
    for field in bool_fields:
        cleaned[field] = bool(listing.get(field, False))
    
    # ===== 8. ZONE D'ACTIVITÉ =====
    cleaned['zone_activite'] = clean_zone_activite(listing.get('zone_activite'))
    
    # ===== 9. LARGEUR FAÇADE =====
    cleaned['largeur_facade'] = clean_number(listing.get('largeur_facade'))
    
    # ===== 10. ÉQUIPEMENTS =====
    equipements = listing.get('equipements', [])
    amenities = listing.get('amenities_commercial', [])
    all_equipements = list(set(
        clean_equipements(equipements) + 
        clean_amenities_commercial(amenities)
    ))
    cleaned['equipements'] = sorted(all_equipements) if all_equipements else []
    
    # ===== 11. AMENITIES COMMERCIALES =====
    cleaned['amenities_commercial'] = clean_amenities_commercial(listing.get('amenities_commercial', []))
    
    # ===== 12. CARACTÉRISTIQUES =====
    caracs = listing.get('caracteristiques') or listing.get('caracteristiques_extraites')
    cleaned['caracteristiques'] = clean_caracteristiques(caracs)
    
    # ===== 13. INFORMATIONS SUPPLÉMENTAIRES =====
    info_supp = listing.get('informations_supplementaires') or listing.get('informations_supplementaires_parse')
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(info_supp)
    
    # ===== 14. CONDITIONS DE VENTE =====
    conditions = listing.get('conditions_vente') or listing.get('conditions_vente_parse')
    cleaned['conditions_vente'] = clean_conditions_vente(conditions)
    
    # ===== 15. CONTACT INFO =====
    contact = listing.get('contact_info') or listing.get('contact_info_parse')
    cleaned['contact_info'] = clean_contact_info(contact)
    
    # ===== 16. LOCALISATION GPS =====
    gps = listing.get('localisation') or listing.get('gps')
    cleaned['localisation'] = clean_localisation(gps)
    
    # ===== 17. IMAGES =====
    cleaned['images'] = clean_images(listing.get('images', []))
    
    # ===== 18. DATES =====
    cleaned['date_scraping'] = clean_date(listing.get('date_scraping'))
    cleaned['date_publication'] = listing.get('date_publication')
    cleaned['annee_construction'] = listing.get('annee_construction', '')
    
    # ===== 19. ÉTAT DU BIEN =====
    etat = (
        listing.get('etat_bien') or 
        cleaned['caracteristiques'].get('etat') or
        cleaned['conditions_vente'].get('etat')
    )
    cleaned['etat_bien'] = clean_etat_bien(etat)
    
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
    Nettoie un fichier JSON de locaux commerciaux
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
        'catalogues_trouves': 0
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
            if cleaned.get('contact_info', {}).get('catalogue_urls'):
                stats['catalogues_trouves'] += 1
            
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
    print("📊 STATISTIQUES DE NETTOYAGE - LOCAUX COMMERCIAUX")
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
    print(f"✅ Catalogues PDF trouvés: {stats['catalogues_trouves']}")
    print("="*70)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des JSON de locaux commerciaux")
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()