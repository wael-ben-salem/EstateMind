"""
Script de nettoyage pour Tunisia Promo - Location
Nettoie et normalise TOUTES les données des annonces de location
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


# ========== CONSTANTES POUR NORMALISATION ==========

TYPES_BIENS_NORMALISES = {
    'appartement': 'Appartement',
    'villa': 'Villa',
    'maison': 'Maison',
    'bureau': 'Bureau',
    'studio': 'Studio',
    'local commercial': 'Local commercial'
}

TYPES_LOCATION_NORMALISES = {
    'annuelle': 'Annuelle',
    'long terme': 'Long terme',
    'temporaire': 'Temporaire',
    'saisonnier': 'Saisonnier',
    'vacances': 'Vacances'
}

VUES_NORMALISEES = {
    'mer': 'Mer',
    'lac': 'Lac',
    'dégagée': 'Dégagée',
    'jardin': 'Jardin',
    'piscine': 'Piscine'
}

CLIMATISATION_NORMALISEE = {
    'centrale': 'Centrale',
    'split': 'Split'
}

CHAUFFAGE_NORMALISE = {
    'central': 'Central',
    'individuel': 'Individuel'
}

PARKING_TYPES_NORMALISES = {
    'sous-sol': 'Sous-sol',
    'couvert': 'Couvert',
    'abrité': 'Abrité'
}

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte', 'medenine': 'Médenine', 'djerba': 'Médenine'
}


# ========== FONCTIONS DE SÉCURISATION ==========

def safe_str(value: Any) -> str:
    """Convertit n'importe quelle valeur en string de façon sécurisée"""
    if value is None:
        return ""
    try:
        return str(value).strip()
    except:
        return ""


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convertit en int de façon sécurisée"""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convertit en float de façon sécurisée"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Convertit en booléen de façon sécurisée"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['oui', 'yes', 'true', '1', 'vrai']
    return bool(value)


def safe_list(value: Any) -> List:
    """Convertit en liste de façon sécurisée"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if ',' in value:
            return [v.strip() for v in value.split(',') if v.strip()]
        return [value.strip()]
    return []


def safe_dict(value: Any) -> Dict:
    """Convertit en dictionnaire de façon sécurisée"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}


# ========== FONCTIONS DE NETTOYAGE ==========

def clean_text(text: Any) -> str:
    """Nettoie un texte"""
    return safe_str(text)


def clean_number(value: Any, default: Any = None) -> Any:
    """Nettoie une valeur numérique"""
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return value
    
    if isinstance(value, str):
        try:
            cleaned = re.sub(r'\s+', '', value)
            if not cleaned:
                return default
            cleaned = cleaned.replace(',', '.')
            if cleaned.replace('.', '').replace('-', '').isdigit():
                if '.' in cleaned:
                    return float(cleaned)
                else:
                    return int(cleaned)
        except:
            pass
    
    return default


def clean_prix_text(prix: float) -> str:
    """Génère un texte de prix normalisé"""
    if prix == 0:
        return "Prix à consulter"
    return f"{int(prix):,} TND/mois".replace(',', ' ')


def determine_region_from_ville(ville: str) -> Optional[str]:
    """Détermine la région à partir de la ville"""
    if not ville:
        return None
    
    ville_lower = ville.lower().strip()
    
    for key, region in REGIONS_MAPPING.items():
        if key in ville_lower:
            return region
    
    return None


def clean_type_bien(type_bien: Optional[str]) -> str:
    """Normalise le type de bien"""
    if not type_bien:
        return "Non spécifié"
    
    type_lower = type_bien.lower().strip()
    
    for key, value in TYPES_BIENS_NORMALISES.items():
        if key in type_lower:
            return value
    
    return type_bien.title()


def clean_type_location(type_location: Optional[str]) -> str:
    """Normalise le type de location"""
    if not type_location or type_location == "Non spécifié":
        return "Non spécifié"
    
    type_lower = type_location.lower().strip()
    
    for key, value in TYPES_LOCATION_NORMALISES.items():
        if key in type_lower:
            return value
    
    return type_location


def clean_vue(vue: Optional[str]) -> Optional[str]:
    """Normalise le type de vue"""
    if not vue:
        return None
    
    vue_lower = vue.lower().strip()
    
    for key, value in VUES_NORMALISEES.items():
        if key in vue_lower:
            return value
    
    return vue.title()


def clean_climatisation_type(clim_type: Optional[str]) -> Optional[str]:
    """Normalise le type de climatisation"""
    if not clim_type:
        return None
    
    clim_lower = clim_type.lower().strip()
    
    for key, value in CLIMATISATION_NORMALISEE.items():
        if key in clim_lower:
            return value
    
    return clim_type


def clean_chauffage_type(chauffage_type: Optional[str]) -> Optional[str]:
    """Normalise le type de chauffage"""
    if not chauffage_type:
        return None
    
    chauffage_lower = chauffage_type.lower().strip()
    
    for key, value in CHAUFFAGE_NORMALISE.items():
        if key in chauffage_lower:
            return value
    
    return chauffage_type


def clean_parking_type(parking_type: Optional[str]) -> Optional[str]:
    """Normalise le type de parking"""
    if not parking_type:
        return None
    
    parking_lower = parking_type.lower().strip()
    
    for key, value in PARKING_TYPES_NORMALISES.items():
        if key in parking_lower:
            return value
    
    return parking_type


def clean_proximites(proximites: Any) -> List[str]:
    """Nettoie la liste des proximités"""
    items = safe_list(proximites)
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    return sorted(cleaned)


def clean_options(options: Any) -> List[str]:
    """Nettoie la liste des options"""
    items = safe_list(options)
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    return sorted(cleaned)


def clean_equipements(equipements: Any) -> List[str]:
    """Nettoie la liste des équipements"""
    items = safe_list(equipements)
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = item.strip().title()
            if item and item not in cleaned:
                cleaned.append(item)
    
    return sorted(cleaned)


def clean_telephone(telephone: Optional[str]) -> Optional[str]:
    """Nettoie un numéro de téléphone"""
    if not telephone or telephone == '#':
        return None
    
    digits = re.sub(r'\D', '', safe_str(telephone))
    
    if digits.startswith('216') and len(digits) == 11:
        return f"+{digits}"
    elif len(digits) == 8:
        return f"+216{digits}"
    elif len(digits) == 12 and digits.startswith('00216'):
        return f"+216{digits[5:]}"
    
    return telephone


def clean_images(images: Any) -> List[str]:
    """Nettoie la liste des images"""
    urls = safe_list(images)
    
    filtered = []
    exclude_patterns = [r'no_photo', r'placeholder', r'logo']
    
    for url in urls:
        if not isinstance(url, str):
            continue
        if not url.startswith(('http://', 'https://')):
            continue
        
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


def clean_charges(charges: Any) -> Dict[str, Any]:
    """Nettoie les informations de charges"""
    if not charges:
        return {}
    
    charges_dict = safe_dict(charges)
    cleaned = {}
    
    if charges_dict.get('syndic_annuel'):
        cleaned['syndic_annuel'] = safe_float(charges_dict['syndic_annuel'])
    
    if charges_dict.get('charges_incluses'):
        cleaned['charges_incluses'] = True
        details = charges_dict.get('charges_details', [])
        if details:
            cleaned['charges_details'] = sorted(list(set(details)))
    
    return cleaned


def clean_date(date_str: Any) -> Optional[str]:
    """Normalise une date"""
    if not date_str:
        return None
    
    date_str = safe_str(date_str)
    
    try:
        if '.' in date_str:
            date_str = date_str.split('.')[0]
        if not date_str.endswith('Z'):
            date_str += 'Z'
        return date_str
    except:
        return None


def determiner_etage(annonce: Dict) -> Optional[int]:
    """Détermine l'étage à partir des différentes sources"""
    if annonce.get('etage') is not None:
        return safe_int(annonce['etage'])
    if annonce.get('etage_desc') is not None:
        return safe_int(annonce['etage_desc'])
    return None


def valider_annonce(annonce: Dict) -> Tuple[bool, List[str]]:
    """Valide une annonce et retourne (est_valide, liste des problèmes)"""
    problems = []
    
    if not annonce.get('annonce_id'):
        problems.append("ID manquant")
    
    if not annonce.get('url'):
        problems.append("URL manquante")
    
    if not annonce.get('ville'):
        problems.append("Ville non déterminée")
    
    is_valid = len(problems) == 0
    return is_valid, problems


# ========== FONCTION PRINCIPALE DE NETTOYAGE ==========

def clean_annonce(annonce: Dict) -> Dict:
    """
    Nettoie complètement une annonce de location Tunisia Promo
    """
    cleaned = {}
    
    try:
        # ===== 1. IDENTIFIANTS =====
        cleaned['annonce_id'] = safe_str(annonce.get('annonce_id'))
        cleaned['url'] = safe_str(annonce.get('url'))
        cleaned['reference'] = safe_str(annonce.get('reference'))
        cleaned['type_offre'] = safe_str(annonce.get('type_offre', 'Location'))
        
        # ===== 2. TITRE =====
        cleaned['titre'] = clean_text(annonce.get('titre'))
        
        # ===== 3. PRIX =====
        prix = clean_number(annonce.get('prix'), 0)
        cleaned['prix'] = prix
        cleaned['prix_text'] = clean_prix_text(prix)
        
        # ===== 4. LOCALISATION =====
        cleaned['region'] = safe_str(annonce.get('region'))
        cleaned['ville'] = safe_str(annonce.get('ville'))
        cleaned['adresse'] = clean_text(annonce.get('adresse'))
        cleaned['code_postal'] = safe_str(annonce.get('code_postal'))
        
        # Déterminer la région si manquante
        if not cleaned['region'] and cleaned['ville']:
            cleaned['region'] = determine_region_from_ville(cleaned['ville']) or ""
        
        # ===== 5. TYPE DE BIEN =====
        cleaned['type_bien'] = clean_type_bien(annonce.get('type_bien'))
        
        # ===== 6. TYPE DE LOCATION =====
        cleaned['type_location'] = clean_type_location(annonce.get('type_location'))
        
        # ===== 7. DESCRIPTION =====
        cleaned['description'] = clean_text(annonce.get('description'))
        
        # ===== 8. CARACTÉRISTIQUES DU BIEN =====
        cleaned['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
        cleaned['pieces'] = clean_number(annonce.get('pieces'))
        cleaned['places_voiture'] = clean_number(annonce.get('places_voiture'))
        
        # Étage
        cleaned['etage'] = determiner_etage(annonce)
        cleaned['dernier_etage'] = safe_bool(annonce.get('dernier_etage'))
        
        # ===== 9. VUE =====
        cleaned['vue'] = clean_vue(annonce.get('vue'))
        
        # ===== 10. ÉQUIPEMENTS (booléens) =====
        bool_fields = [
            'a_piscine', 'a_jardin', 'a_ascenseur', 'a_gardien',
            'a_terrasse', 'a_balcon', 'a_climatisation', 'a_chauffage',
            'a_meuble', 'a_cuisine_equipee', 'a_parking'
        ]
        for field in bool_fields:
            cleaned[field] = safe_bool(annonce.get(field))
        
        # ===== 11. TYPES SPÉCIFIQUES =====
        cleaned['climatisation_type'] = clean_climatisation_type(annonce.get('climatisation_type'))
        cleaned['chauffage_type'] = clean_chauffage_type(annonce.get('chauffage_type'))
        cleaned['parking_type'] = clean_parking_type(annonce.get('parking_type'))
        cleaned['parking_nombre'] = clean_number(annonce.get('parking_nombre'))
        cleaned['surface_terrasse'] = clean_number(annonce.get('surface_terrasse'))
        
        # ===== 12. PROXIMITÉS =====
        proximites = annonce.get('proximites')
        if proximites:
            cleaned['proximites'] = clean_proximites(proximites)
        
        # ===== 13. DISPONIBILITÉ =====
        if annonce.get('disponibilite'):
            cleaned['disponibilite'] = safe_str(annonce['disponibilite'])
        
        # ===== 14. CHARGES =====
        charges = annonce.get('charges')
        if charges:
            cleaned['charges'] = clean_charges(charges)
        
        # ===== 15. OPTIONS ET ÉQUIPEMENTS =====
        options = annonce.get('options_normalisees') or annonce.get('options_brutes')
        if options:
            cleaned['options'] = clean_options(options)
        
        equipements = annonce.get('equipements_normalises') or annonce.get('equipements_bruts')
        if equipements:
            cleaned['equipements'] = clean_equipements(equipements)
        
        # Fusionner tous les équipements
        tous_equip = []
        if cleaned.get('options'):
            tous_equip.extend(cleaned['options'])
        if cleaned.get('equipements'):
            tous_equip.extend(cleaned['equipements'])
        if tous_equip:
            cleaned['tous_equipements'] = sorted(list(set(tous_equip)))
        
        # ===== 16. IMAGES =====
        cleaned['images'] = clean_images(annonce.get('images', []))
        cleaned['nombre_images'] = len(cleaned['images'])
        
        # ===== 17. ANNONCEUR =====
        cleaned['annonceur_nom'] = clean_text(annonce.get('annonceur_nom'))
        cleaned['annonceur_type'] = safe_str(annonce.get('annonceur_type'))
        
        telephone = annonce.get('telephone') or annonce.get('annonceur_telephone')
        if telephone and telephone != '#':
            cleaned['telephone'] = clean_telephone(telephone)
        
        cleaned['email'] = safe_str(annonce.get('email'))
        cleaned['site_web'] = safe_str(annonce.get('site_web'))
        
        # ===== 18. DATES =====
        cleaned['date_publication'] = annonce.get('date_publication')
        cleaned['date_scraping'] = clean_date(annonce.get('date_scraping'))
        
        # ===== 19. MÉTADONNÉES =====
        cleaned['page_trouvee'] = safe_int(annonce.get('page_trouvee'), 0)
        cleaned['statut'] = safe_str(annonce.get('statut', 'inchangé'))
        
        if annonce.get('nombre_photos_annonce'):
            cleaned['nombre_photos_annonce'] = safe_int(annonce['nombre_photos_annonce'])
        
        # ===== 20. VALIDATION =====
        is_valid, problems = valider_annonce(cleaned)
        cleaned['est_valide'] = is_valid
        if problems:
            cleaned['problemes_validation'] = problems
        
        return cleaned
        
    except Exception as e:
        print(f"Erreur détaillée sur annonce {annonce.get('annonce_id')}: {e}")
        return annonce


def load_annonces_from_file(filepath: Path) -> List[Dict]:
    """Charge les annonces depuis un fichier JSON"""
    if not filepath.exists():
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'annonces' in data:
            return data['annonces']
    except json.JSONDecodeError:
        print(f"⚠️ Fichier {filepath} corrompu")
    
    return []


def process_tunisiapromo_file_clean(input_path: str, output_path: Optional[str] = None):
    """Nettoie un fichier JSON d'annonces de location"""
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    output_file = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_clean.json"
    
    annonces = load_annonces_from_file(input_file)
    
    if not annonces:
        print(f"⚠️ Aucune annonce trouvée dans {input_file}")
        return 0
    
    stats = {
        'total': len(annonces),
        'nettoyees': 0,
        'inchangees': 0,
        'valides': 0,
        'invalides': 0,
        'avec_telephone': 0,
        'avec_images': 0,
        'appartements': 0,
        'maisons': 0,
        'location_annuelle': 0
    }
    
    annonces_nettoyees = []
    
    for i, annonce in enumerate(annonces):
        try:
            cleaned = clean_annonce(annonce)
            annonces_nettoyees.append(cleaned)
            stats['nettoyees'] += 1
            
            if cleaned.get('est_valide'):
                stats['valides'] += 1
            else:
                stats['invalides'] += 1
            
            if cleaned.get('telephone'):
                stats['avec_telephone'] += 1
            
            if cleaned.get('images'):
                stats['avec_images'] += 1
            
            if cleaned.get('type_bien') == 'Appartement':
                stats['appartements'] += 1
            elif cleaned.get('type_bien') == 'Maison' or cleaned.get('type_bien') == 'Villa':
                stats['maisons'] += 1
            
            if cleaned.get('type_location') == 'Annuelle':
                stats['location_annuelle'] += 1
                
        except Exception as e:
            print(f"❌ Erreur annonce {annonce.get('annonce_id', '?')}: {e}")
            annonces_nettoyees.append(annonce)
            stats['inchangees'] += 1
        
        if (i + 1) % 1000 == 0:
            print(f"⏳ Progression: {i + 1}/{len(annonces)} annonces traitées")
    
    annonces_nettoyees.sort(key=lambda x: safe_str(x.get('annonce_id')))
    
    metadata = {
        'date_nettoyage': datetime.now().isoformat(),
        'total_annonces': len(annonces_nettoyees),
        'statistiques': stats,
        'version': '1.0',
        'type': 'location'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_nettoyees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE NETTOYAGE - TUNISIA PROMO LOCATION")
    print("="*60)
    print(f"📥 Annonces lues: {stats['total']}")
    print(f"🧹 Annonces nettoyées: {stats['nettoyees']}")
    print(f"⏸️ Annonces inchangées: {stats['inchangees']}")
    print(f"✅ Annonces valides: {stats['valides']}")
    print(f"⚠️ Annonces invalides: {stats['invalides']}")
    print(f"📞 Annonces avec téléphone: {stats['avec_telephone']}")
    print(f"🖼️ Annonces avec images: {stats['avec_images']}")
    print(f"🏢 Appartements: {stats['appartements']}")
    print(f"🏠 Maisons/Villas: {stats['maisons']}")
    print(f"📅 Location annuelle: {stats['location_annuelle']}")
    print("="*60)
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    return len(annonces_nettoyees)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des données Tunisia Promo Location")
    parser.add_argument('--file', '-f', default='tunisiapromo_location_extrait.json', help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_clean.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_clean(args.file, args.output)


if __name__ == '__main__':
    main()