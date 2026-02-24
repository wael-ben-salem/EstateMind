"""
Script COMPLET de nettoyage et normalisation des JSON de listings
Normalise : localisation, informations_supplementaires, contact_info, conditions_location,
caracteristiques, equipements_detaille, etat_bien, images, dates, prix, etc.
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


# Mapping pour normaliser les états de bien
ETAT_MAPPING = {
    "bon état": "Bon état",
    "bon état / habitable": "Bon état",
    "très bon état": "Très bon état",
    "excellent état": "Excellent état",
    "neuf": "Neuf",
    "à rénover": "À rénover",
    "rénové": "Rénové"
}

# Mapping pour normaliser les orientations
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

# Mapping pour normaliser les types de sol
SOL_MAPPING = {
    "carrelage": "Carrelage",
    "marbre": "Marbre",
    "parquet": "Parquet",
    "stratifié": "Stratifié",
    "moquette": "Moquette",
    "béton ciré": "Béton ciré"
}


def clean_prix_text(prix_text: Any, prix: float) -> str:
    """
    Nettoie et normalise le texte du prix
    - Si prix = 0, garde "Prix à consulter" ou équivalent
    - Sinon, formate en français avec espace comme séparateur de milliers
    """
    if not prix_text and prix == 0:
        return "Prix à consulter"
    
    if prix == 0:
        # Garder le texte original si c'est "Prix à consulter" ou similaire
        if prix_text and isinstance(prix_text, str):
            text_lower = prix_text.lower()
            if any(word in text_lower for word in ['consulter', 'contact', 'demande', 'sur demande']):
                return prix_text
        return "Prix à consulter"
    
    if not prix_text and prix > 0:
        # Générer un prix_text à partir du prix
        return f"{int(prix):,} TND".replace(',', ' ')
    
    if isinstance(prix_text, (int, float)):
        return f"{int(prix_text):,} TND".replace(',', ' ')
    
    # Nettoyer le texte existant
    cleaned = re.sub(r'\s+', ' ', str(prix_text)).strip()
    
    # Si le prix est présent, s'assurer qu'il est bien formaté
    if prix > 0 and str(int(prix)) in cleaned:
        # Remplacer par le format standard
        return f"{int(prix):,} TND".replace(',', ' ')
    
    return cleaned


def clean_surface_text(surface_text: Any, surface: float) -> str:
    """Nettoie et normalise le texte de la surface"""
    if not surface_text and surface:
        return f"{int(surface)} m²"
    
    if not surface_text:
        return ""
    
    # Nettoyer les espaces multiples et retours à la ligne
    cleaned = re.sub(r'\s+', ' ', str(surface_text)).strip()
    
    # Standardiser le format
    if 'm²' not in cleaned and 'm2' in cleaned.lower():
        cleaned = cleaned.lower().replace('m2', 'm²')
    elif 'm²' not in cleaned and surface:
        cleaned = f"{int(surface)} m²"
    
    return cleaned


def clean_equipements(equipements: Any) -> List[str]:
    """Nettoie et normalise la liste des équipements"""
    if not equipements:
        return []
    
    if isinstance(equipements, str):
        # Séparer par ; ou virgule
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
    
    # Nettoyer chaque élément
    cleaned = []
    for item in items:
        if isinstance(item, str):
            # Enlever les numéros et caractères spéciaux au début
            item = re.sub(r'^\d+[\s\.\-]*', '', item)
            item = item.strip()
            # Mettre en title case
            item = item.title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    # Trier par ordre alphabétique
    return sorted(cleaned)


def clean_json_string(json_str: str) -> Dict:
    """Convertit une string JSON en objet dict"""
    if not json_str:
        return {}
    
    try:
        if isinstance(json_str, str):
            # Nettoyer la chaîne JSON (remplacer les quotes simples si nécessaire)
            cleaned = json_str.replace("'", '"')
            return json.loads(cleaned)
        elif isinstance(json_str, dict):
            return json_str
        else:
            return {}
    except (json.JSONDecodeError, AttributeError):
        return {}


def clean_localisation(localisation: Any) -> Dict:
    """
    Normalise le champ localisation
    - Convertit les strings JSON en objet
    - Convertit les lat/long en nombres
    - Ajoute un champ coordinates au format GeoJSON [long, lat]
    """
    # Convertir en dict si c'est une string
    if isinstance(localisation, str):
        loc = clean_json_string(localisation)
    elif isinstance(localisation, dict):
        loc = localisation
    else:
        return {}
    
    cleaned = {}
    
    # Nettoyer latitude
    if 'latitude' in loc:
        try:
            lat = float(loc['latitude'])
            if -90 <= lat <= 90:
                cleaned['latitude'] = lat
        except (ValueError, TypeError):
            pass
    
    # Nettoyer longitude
    if 'longitude' in loc:
        try:
            lng = float(loc['longitude'])
            if -180 <= lng <= 180:
                cleaned['longitude'] = lng
        except (ValueError, TypeError):
            pass
    
    # Ajouter coordinates au format GeoJSON [longitude, latitude]
    if 'latitude' in cleaned and 'longitude' in cleaned:
        cleaned['coordinates'] = [cleaned['longitude'], cleaned['latitude']]
    
    return cleaned


def clean_informations_supplementaires(info: Any) -> Dict:
    """
    Normalise les informations supplémentaires
    - Convertit les strings JSON en objet
    - Convertit "Oui"/"Non" en booléens
    - Convertit les nombres en int/float
    """
    # Convertir en dict si c'est une string
    if isinstance(info, str):
        infos = clean_json_string(info)
    elif isinstance(info, dict):
        infos = info
    else:
        return {}
    
    cleaned = {}
    
    for key, value in infos.items():
        # Nettoyer la clé (enlever accents, espaces, mettre en minuscules)
        key_clean = key.lower().strip().replace(' ', '_').replace('é', 'e').replace('è', 'e')
        
        # Convertir les valeurs
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ['oui', 'yes', 'true', '1', 'vrai', 'disponible']:
                cleaned[key_clean] = True
            elif value_lower in ['non', 'no', 'false', '0', 'faux']:
                cleaned[key_clean] = False
            elif value_lower.replace('.', '').replace(',', '').isdigit():
                # Convertir en nombre si possible
                try:
                    if '.' in value_lower or ',' in value_lower:
                        cleaned[key_clean] = float(value_lower.replace(',', '.'))
                    else:
                        cleaned[key_clean] = int(value_lower)
                except:
                    cleaned[key_clean] = value
            else:
                cleaned[key_clean] = value
        else:
            cleaned[key_clean] = value
    
    return cleaned


def clean_contact_info(contact: Any) -> Dict:
    """
    Normalise les informations de contact
    - Convertit les strings JSON en objet
    - Formate les numéros de téléphone
    - Détecte WhatsApp
    """
    # Convertir en dict si c'est une string
    if isinstance(contact, str):
        contacts = clean_json_string(contact)
    elif isinstance(contact, dict):
        contacts = contact
    else:
        return {}
    
    cleaned = {}
    
    for key, value in contacts.items():
        key_clean = key.lower().strip().replace(' ', '_')
        
        if 'telephone' in key_clean or 'tel' in key_clean or 'phone' in key_clean:
            # Nettoyer le numéro de téléphone
            if isinstance(value, str):
                # Enlever tous les caractères non chiffres
                digits = re.sub(r'\D', '', value)
                if len(digits) == 8:
                    cleaned['telephone'] = f"+216{digits}"
                    cleaned['telephone_formate'] = f"+216 {digits[:2]} {digits[2:5]} {digits[5:]}"
                elif len(digits) == 12 and digits.startswith('216'):
                    cleaned['telephone'] = f"+{digits}"
                    tel = digits[3:]
                    cleaned['telephone_formate'] = f"+216 {tel[:2]} {tel[2:5]} {tel[5:]}"
                elif len(digits) > 0:
                    cleaned['telephone'] = value
                
                # Détecter WhatsApp
                if 'whatsapp' in key_clean.lower() or ('telephone' in cleaned and value):
                    cleaned['whatsapp'] = True
        elif 'formulaire' in key_clean or 'contact' in key_clean:
            if isinstance(value, str):
                cleaned['formulaire_contact'] = value.lower() in ['oui', 'yes', 'true', '1', 'disponible']
            else:
                cleaned['formulaire_contact'] = bool(value)
        else:
            cleaned[key_clean] = value
    
    return cleaned


def clean_caracteristiques(caracs: Any) -> Dict:
    """
    Normalise les caractéristiques
    - Convertit les strings JSON en objet
    - Nettoie les clés (enlève les espaces)
    - Normalise les valeurs (état, orientation, type_sol)
    """
    # Convertir en dict si c'est une string
    if isinstance(caracs, str):
        caracteristiques = clean_json_string(caracs)
    elif isinstance(caracs, dict):
        caracteristiques = caracs
    else:
        return {}
    
    cleaned = {}
    
    for key, value in caracteristiques.items():
        # Nettoyer la clé
        key_clean = key.lower().strip().replace(' ', '_').replace('é', 'e').replace('è', 'e')
        
        # Normaliser selon le type de champ
        if 'etat' in key_clean:
            if isinstance(value, str):
                value_lower = value.lower()
                for k, v in ETAT_MAPPING.items():
                    if k in value_lower:
                        cleaned['etat'] = v
                        break
                else:
                    cleaned['etat'] = value.title()
            else:
                cleaned['etat'] = value
        
        elif 'orientation' in key_clean:
            if isinstance(value, str):
                value_lower = value.lower()
                cleaned['orientation'] = ORIENTATION_MAPPING.get(value_lower, value.title())
            else:
                cleaned['orientation'] = value
        
        elif 'sol' in key_clean or 'parquet' in key_clean or 'carrelage' in key_clean:
            if isinstance(value, str):
                value_lower = value.lower()
                for k, v in SOL_MAPPING.items():
                    if k in value_lower:
                        cleaned['type_sol'] = v
                        break
                else:
                    cleaned['type_sol'] = value.title()
            else:
                cleaned['type_sol'] = value
        
        elif 'type' in key_clean and 'bien' in key_clean:
            cleaned['type_bien'] = value
        
        else:
            cleaned[key_clean] = value
    
    return cleaned


def clean_equipements_detaille(equip_det: Any) -> List[str]:
    """
    Normalise les équipements détaillés
    - Convertit la string avec ; en liste
    - Nettoie chaque équipement
    """
    if not equip_det:
        return []
    
    if isinstance(equip_det, str):
        # Séparer par ;
        if ';' in equip_det:
            items = [e.strip() for e in equip_det.split(';') if e.strip()]
        else:
            items = [equip_det.strip()]
    elif isinstance(equip_det, list):
        items = equip_det
    else:
        return []
    
    # Nettoyer chaque élément
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = re.sub(r'^\d+[\s\.\-]*', '', item)
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    return sorted(cleaned)


def clean_images(images: Any) -> List[str]:
    """
    Nettoie la liste des images
    - Garde seulement les URLs valides
    - Filtre les logos, icônes, loading.gif
    """
    if not images:
        return []
    
    # Convertir en liste
    if isinstance(images, str):
        if ';' in images:
            urls = [img.strip() for img in images.split(';') if img.strip()]
        else:
            urls = [images]
    elif isinstance(images, list):
        urls = images
    else:
        return []
    
    # Filtrer les URLs
    filtered = []
    exclude_patterns = [
        r'logo',
        r'loading\.gif',
        r'favicon',
        r'banks?/',
        r'assets/',
        r'common/'
    ]
    
    for url in urls:
        if isinstance(url, str) and url.startswith(('http://', 'https://')):
            url_lower = url.lower()
            # Vérifier si l'URL doit être exclue
            exclude = False
            for pattern in exclude_patterns:
                if re.search(pattern, url_lower):
                    exclude = True
                    break
            if not exclude:
                filtered.append(url)
    
    return filtered


def clean_date(date_str: Any) -> Optional[str]:
    """Normalise une date au format ISO"""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            # Enlever les microsecondes
            if '.' in date_str:
                date_str = date_str.split('.')[0]
            # Ajouter le Z pour indiquer UTC
            if not date_str.endswith('Z'):
                date_str += 'Z'
            return date_str
        elif isinstance(date_str, datetime):
            return date_str.isoformat() + 'Z'
    except:
        pass
    
    return None


def clean_numeric(value: Any, default: Any = None) -> Any:
    """Nettoie une valeur numérique"""
    if value is None:
        return default
    
    try:
        if isinstance(value, (int, float)):
            if value == 0 and default is None:
                return None  # Convertir 0 en null pour certains champs
            return value
        elif isinstance(value, str):
            # Enlever les espaces et convertir
            cleaned = re.sub(r'\s+', '', value)
            if ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            if cleaned.replace('.', '').isdigit():
                if '.' in cleaned:
                    return float(cleaned)
                else:
                    return int(cleaned)
    except (ValueError, TypeError):
        pass
    
    return default


def clean_listing(listing: Dict) -> Dict:
    """
    Nettoie complètement un listing avec toutes les normalisations
    """
    cleaned = {}
    
    # 1. Copier les champs simples
    simple_fields = ['id', 'titre', 'url', 'ville', 'quartier', 'adresse', 
                     'type_bien', 'type_location', 'description_courte', 
                     'description_complete', 'page_source', 'is_valid']
    
    for field in simple_fields:
        if field in listing:
            if isinstance(listing[field], str):
                cleaned[field] = re.sub(r'\s+', ' ', listing[field]).strip()
            else:
                cleaned[field] = listing[field]
        else:
            if field == 'is_valid':
                cleaned[field] = True
            else:
                cleaned[field] = ""
    
    # 2. Prix et surface
    prix = clean_numeric(listing.get('prix'), 0)
    cleaned['prix'] = prix
    cleaned['prix_text'] = clean_prix_text(listing.get('prix_text'), prix)
    
    # Prix par jour : 0 devient None
    cleaned['prix_par_jour'] = clean_numeric(listing.get('prix_par_jour'), None)
    
    surface = clean_numeric(listing.get('surface'), 0)
    cleaned['surface'] = surface
    cleaned['surface_text'] = clean_surface_text(listing.get('surface_text'), surface)
    
    # 3. Nombres (pièces, chambres, etc.)
    numeric_fields = ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 
                      'capacite', 'nuits_minimum']
    for field in numeric_fields:
        val = listing.get(field)
        if val in [None, '', 0]:
            cleaned[field] = None
        else:
            cleaned[field] = clean_numeric(val, None)
    
    # 4. Étage et résidence
    cleaned['etage'] = listing.get('etage', '') or None
    cleaned['residence'] = listing.get('residence', '') or None
    
    # 5. Équipements et amenities
    cleaned['equipements'] = clean_equipements(listing.get('equipements', []))
    cleaned['amenities_vacances'] = clean_equipements(listing.get('amenities_vacances', []))
    
    # 6. LOCALISATION (string JSON → objet)
    cleaned['localisation'] = clean_localisation(listing.get('localisation', {}))
    
    # 7. INFORMATIONS SUPPLEMENTAIRES (string JSON → objet avec booléens)
    cleaned['informations_supplementaires'] = clean_informations_supplementaires(
        listing.get('informations_supplementaires', {})
    )
    
    # 8. CONTACT INFO (string JSON → objet avec téléphone formaté)
    cleaned['contact_info'] = clean_contact_info(listing.get('contact_info', {}))
    
    # 9. CONDITIONS LOCATION (string JSON → objet)
    if listing.get('conditions_location'):
        cleaned['conditions_location'] = clean_json_string(listing['conditions_location'])
    else:
        cleaned['conditions_location'] = {}
    
    # 10. CARACTERISTIQUES (string JSON → objet normalisé)
    cleaned['caracteristiques'] = clean_caracteristiques(listing.get('caracteristiques', {}))
    
    # 11. EQUIPEMENTS DETAILLE (string avec ; → liste)
    cleaned['equipements_detaille'] = clean_equipements_detaille(
        listing.get('equipements_detaille', [])
    )
    
    # 12. IMAGES (filtrer logos et icônes)
    cleaned['images'] = clean_images(listing.get('images', []))
    
    # 13. DATES
    cleaned['date_scraping'] = clean_date(listing.get('date_scraping'))
    cleaned['date_publication'] = listing.get('date_publication')  # Déjà extrait
    
    # 14. Champs extraits (orientation, type_sol, etat_bien)
    # Utiliser les valeurs des caractéristiques si disponibles
    caracs = cleaned['caracteristiques']
    cleaned['orientation'] = caracs.get('orientation') or listing.get('orientation')
    cleaned['type_sol'] = caracs.get('type_sol') or listing.get('type_sol')
    cleaned['etat_bien'] = caracs.get('etat') or listing.get('etat_bien')
    
    # Normaliser ces champs si ce sont des strings
    if isinstance(cleaned['orientation'], str):
        cleaned['orientation'] = ORIENTATION_MAPPING.get(
            cleaned['orientation'].lower(), 
            cleaned['orientation'].title()
        )
    
    if isinstance(cleaned['etat_bien'], str):
        val_lower = cleaned['etat_bien'].lower()
        for k, v in ETAT_MAPPING.items():
            if k in val_lower:
                cleaned['etat_bien'] = v
                break
    
    if isinstance(cleaned['type_sol'], str):
        val_lower = cleaned['type_sol'].lower()
        for k, v in SOL_MAPPING.items():
            if k in val_lower:
                cleaned['type_sol'] = v
                break
    
    return cleaned


def validate_listing(listing: Dict) -> List[str]:
    """Valide un listing et retourne la liste des avertissements"""
    warnings = []
    
    # Vérifier les champs obligatoires
    if not listing.get('id'):
        warnings.append("ID manquant")
    
    if not listing.get('url'):
        warnings.append("URL manquante")
    
    # Vérifier la cohérence des prix
    prix = listing.get('prix')
    prix_text = listing.get('prix_text')
    
    if prix is not None and prix_text:
        if prix == 0:
            if 'consulter' not in prix_text.lower() and 'contact' not in prix_text.lower():
                warnings.append(f"Prix 0 mais texte '{prix_text}' ne l'indique pas")
        else:
            # Vérifier que le prix_text contient le prix
            prix_str = str(int(prix)) if isinstance(prix, (int, float)) else str(prix)
            if prix_str not in str(prix_text):
                warnings.append(f"Incohérence prix: {prix} vs {prix_text}")
    
    # Vérifier la localisation
    loc = listing.get('localisation', {})
    if loc and ('latitude' in loc or 'longitude' in loc):
        if 'latitude' not in loc or 'longitude' not in loc:
            warnings.append("Localisation incomplète (latitude ou longitude manquante)")
    
    # Vérifier les images
    images = listing.get('images', [])
    if images and len(images) == 0:
        warnings.append("Liste d'images vide après filtrage")
    
    return warnings


def clean_json_file(input_path: str, output_path: Optional[str] = None, validate: bool = False):
    """Nettoie un fichier JSON complet"""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get('listings', [])
    cleaned_listings = []
    validation_warnings = {}
    
    stats = {
        'total_initial': len(listings),
        'localisations_normalisees': 0,
        'infos_supp_normalisees': 0,
        'contacts_normalises': 0,
        'caracs_normalisees': 0,
        'equipements_detaille_normalises': 0,
        'images_filtrees': 0,
        'prix_zero_avec_texte': 0,
        'dates_publication': 0
    }
    
    for i, listing in enumerate(listings):
        try:
            cleaned = clean_listing(listing)
            cleaned_listings.append(cleaned)
            
            # Statistiques
            if cleaned.get('localisation') and len(cleaned['localisation']) > 0:
                stats['localisations_normalisees'] += 1
            if cleaned.get('informations_supplementaires') and len(cleaned['informations_supplementaires']) > 0:
                stats['infos_supp_normalisees'] += 1
            if cleaned.get('contact_info') and len(cleaned['contact_info']) > 0:
                stats['contacts_normalises'] += 1
            if cleaned.get('caracteristiques') and len(cleaned['caracteristiques']) > 0:
                stats['caracs_normalisees'] += 1
            if cleaned.get('equipements_detaille') and len(cleaned['equipements_detaille']) > 0:
                stats['equipements_detaille_normalises'] += 1
            if cleaned.get('images') and len(cleaned['images']) < len(listing.get('images', [])):
                stats['images_filtrees'] += 1
            if cleaned.get('prix') == 0 and cleaned.get('prix_text'):
                stats['prix_zero_avec_texte'] += 1
            if cleaned.get('date_publication'):
                stats['dates_publication'] += 1
            
            if validate:
                warnings = validate_listing(cleaned)
                if warnings:
                    validation_warnings[cleaned.get('id', f'ligne_{i}')] = warnings
                    
        except Exception as e:
            print(f"❌ Erreur sur listing {listing.get('id', '?')}: {e}")
            cleaned_listings.append(listing)  # Garder l'original en cas d'erreur
    
    # Mettre à jour les données
    data['listings'] = cleaned_listings
    
    # Métadonnées de nettoyage
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
    
    # Afficher les statistiques
    print("\n" + "="*50)
    print("📊 STATISTIQUES DE NETTOYAGE")
    print("="*50)
    print(f"✅ Listings traités: {stats['total_initial']}")
    print(f"✅ Localisations normalisées: {stats['localisations_normalisees']}")
    print(f"✅ Infos supplémentaires normalisées: {stats['infos_supp_normalisees']}")
    print(f"✅ Contacts normalisés: {stats['contacts_normalises']}")
    print(f"✅ Caractéristiques normalisées: {stats['caracs_normalisees']}")
    print(f"✅ Équipements détaillés normalisés: {stats['equipements_detaille_normalises']}")
    print(f"✅ Images filtrées: {stats['images_filtrees']}")
    print(f"✅ Prix à consulter: {stats['prix_zero_avec_texte']}")
    print(f"✅ Dates publication: {stats['dates_publication']}")
    print("="*50)
    print(f"💾 Fichier sauvegardé: {out}")
    
    return len(cleaned_listings)


def main():
    parser = argparse.ArgumentParser(description='Nettoyage COMPLET des JSON de listings')
    parser.add_argument('--file', '-f', required=True, help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--validate', '-v', action='store_true', help='Valider les données après nettoyage')
    args = parser.parse_args()
    
    clean_json_file(args.file, args.output, args.validate)


if __name__ == '__main__':
    main()