"""
Script de nettoyage pour Tunisia Promo - Vente
Nettoie et normalise TOUTES les données des annonces de vente
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
    'terrain': 'Terrain',
    'studio': 'Studio',
    'local commercial': 'Local commercial',
    'bureau': 'Bureau'
}

ETATS_BIEN_NORMALISES = {
    'neuf': 'Neuf',
    'jamais habité': 'Jamais habité',
    'bon état': 'Bon état',
    'très bon état': 'Très bon état',
    'excellent état': 'Excellent état',
    'rénové': 'Rénové',
    'en cours de finition': 'En cours de finition'
}

VUES_NORMALISEES = {
    'mer': 'Mer',
    'piscine': 'Piscine',
    'jardin': 'Jardin',
    'dégagée': 'Dégagée'
}

CHAUFFAGE_NORMALISE = {
    'central': 'Central'
}

TITRES_FONCIERS_NORMALISES = {
    'titre bleu': 'Titre bleu',
    'titre foncier': 'Titre foncier'
}

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'tazarka': 'Nabeul', 'korba': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte'
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
    return f"{int(prix):,} TND".replace(',', ' ')


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


def clean_etat_bien(etat: Optional[str]) -> Optional[str]:
    """Normalise l'état du bien"""
    if not etat:
        return None
    
    etat_lower = etat.lower().strip()
    
    for key, value in ETATS_BIEN_NORMALISES.items():
        if key in etat_lower:
            return value
    
    return etat.title()


def clean_vue(vue: Optional[str]) -> Optional[str]:
    """Normalise le type de vue"""
    if not vue:
        return None
    
    vue_lower = vue.lower().strip()
    
    for key, value in VUES_NORMALISEES.items():
        if key in vue_lower:
            return value
    
    return vue.title()


def clean_chauffage_type(chauffage_type: Optional[str]) -> Optional[str]:
    """Normalise le type de chauffage"""
    if not chauffage_type:
        return None
    
    chauffage_lower = chauffage_type.lower().strip()
    
    for key, value in CHAUFFAGE_NORMALISE.items():
        if key in chauffage_lower:
            return value
    
    return chauffage_type


def clean_titre_foncier(titre_foncier: Optional[str]) -> Optional[str]:
    """Normalise le titre foncier"""
    if not titre_foncier:
        return None
    
    titre_lower = titre_foncier.lower().strip()
    
    for key, value in TITRES_FONCIERS_NORMALISES.items():
        if key in titre_lower:
            return value
    
    return titre_foncier.title()


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


def calculer_prix_m2(prix: float, surface: float) -> Optional[float]:
    """Calcule le prix au m²"""
    if prix and surface and surface > 0:
        return round(prix / surface, 2)
    return None


def determiner_surface_principale(annonce: Dict) -> Optional[float]:
    """Détermine la surface principale à utiliser"""
    if annonce.get('surface_habitable'):
        return clean_number(annonce['surface_habitable'])
    if annonce.get('surface_terrain'):
        return clean_number(annonce['surface_terrain'])
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
    
    prix = annonce.get('prix')
    if prix and prix < 1000:
        problems.append("Prix anormalement bas")
    
    is_valid = len(problems) == 0
    return is_valid, problems


# ========== FONCTION PRINCIPALE DE NETTOYAGE ==========

def clean_annonce(annonce: Dict) -> Dict:
    """
    Nettoie complètement une annonce de vente Tunisia Promo
    """
    cleaned = {}
    
    try:
        # ===== 1. IDENTIFIANTS =====
        cleaned['annonce_id'] = safe_str(annonce.get('annonce_id'))
        cleaned['url'] = safe_str(annonce.get('url'))
        cleaned['reference'] = safe_str(annonce.get('reference'))
        cleaned['type_offre'] = safe_str(annonce.get('type_offre', 'Vente'))
        
        # ===== 2. TITRE =====
        cleaned['titre'] = clean_text(annonce.get('titre'))
        
        # ===== 3. TYPE DE BIEN =====
        cleaned['type_bien'] = clean_type_bien(annonce.get('type_bien'))
        
        # ===== 4. PRIX =====
        prix = clean_number(annonce.get('prix'), 0)
        cleaned['prix'] = prix
        cleaned['prix_text'] = clean_prix_text(prix)
        
        # ===== 5. LOCALISATION =====
        cleaned['region'] = safe_str(annonce.get('region'))
        cleaned['ville'] = safe_str(annonce.get('ville'))
        cleaned['adresse'] = clean_text(annonce.get('adresse'))
        cleaned['code_postal'] = safe_str(annonce.get('code_postal'))
        
        # Déterminer la région si manquante
        if not cleaned['region'] and cleaned['ville']:
            cleaned['region'] = determine_region_from_ville(cleaned['ville']) or ""
        
        # ===== 6. DESCRIPTION =====
        cleaned['description'] = clean_text(annonce.get('description'))
        
        # ===== 7. CARACTÉRISTIQUES DU BIEN =====
        cleaned['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
        cleaned['surface_terrain'] = clean_number(annonce.get('surface_terrain'))
        
        # Surface principale pour calcul prix m²
        surface_principale = determiner_surface_principale(annonce)
        if surface_principale and prix > 0:
            cleaned['prix_m2'] = calculer_prix_m2(prix, surface_principale)
        else:
            cleaned['prix_m2'] = None
        
        # Nombres
        cleaned['pieces'] = clean_number(annonce.get('pieces'))
        cleaned['chambres'] = clean_number(annonce.get('chambres'))
        cleaned['salles_bain'] = clean_number(annonce.get('salles_bain'))
        cleaned['places_voiture'] = clean_number(annonce.get('places_voiture'))
        cleaned['annee_construction'] = clean_number(annonce.get('annee_construction'))
        cleaned['etage'] = clean_number(annonce.get('etage'))
        
        # ===== 8. ÉTAT DU BIEN =====
        cleaned['etat_bien'] = clean_etat_bien(annonce.get('etat_bien'))
        
        # ===== 9. TITRE FONCIER =====
        cleaned['titre_foncier'] = clean_titre_foncier(annonce.get('titre_foncier'))
        
        # ===== 10. VUE =====
        cleaned['vue'] = clean_vue(annonce.get('vue'))
        
        # ===== 11. DISTANCE MER =====
        cleaned['distance_mer'] = safe_str(annonce.get('distance_mer'))
        
        # ===== 12. ÉQUIPEMENTS (booléens) =====
        bool_fields = [
            'a_ascenseur', 'a_piscine', 'a_jardin', 'a_terrasse',
            'a_balcon', 'a_climatisation', 'a_chauffage', 'a_securite',
            'a_parking', 'cloture', 'a_puit', 'promoteur_direct'
        ]
        for field in bool_fields:
            cleaned[field] = safe_bool(annonce.get(field))
        
        # ===== 13. TYPES SPÉCIFIQUES =====
        cleaned['chauffage_type'] = clean_chauffage_type(annonce.get('chauffage_type'))
        cleaned['parking_nombre'] = clean_number(annonce.get('parking_nombre'))
        cleaned['parking_type'] = safe_str(annonce.get('parking_type'))
        
        # ===== 14. CARACTÉRISTIQUES TERRAIN =====
        terrain_fields = ['forme_terrain', 'façade_m', 'acces_route',
                          'reseau_eau', 'reseau_electricite', 'reseau_assainissement']
        for field in terrain_fields:
            if field in annonce:
                cleaned[field] = annonce[field]
        
        # ===== 15. PROXIMITÉS =====
        proximites = annonce.get('proximites')
        if proximites:
            cleaned['proximites'] = clean_proximites(proximites)
        
        # ===== 16. FRAIS ENREGISTREMENT =====
        if annonce.get('frais_enregistrement'):
            cleaned['frais_enregistrement'] = safe_str(annonce['frais_enregistrement'])
        
        # ===== 17. OPTIONS =====
        options = annonce.get('options_normalisees') or annonce.get('options_brutes')
        if options:
            cleaned['options'] = clean_options(options)
        
        # ===== 18. IMAGES =====
        cleaned['images'] = clean_images(annonce.get('images', []))
        cleaned['nombre_images'] = len(cleaned['images'])
        
        # ===== 19. ANNONCEUR =====
        cleaned['annonceur_nom'] = clean_text(annonce.get('annonceur_nom'))
        cleaned['annonceur_type'] = safe_str(annonce.get('annonceur_type'))
        
        telephone = annonce.get('telephone') or annonce.get('annonceur_telephone')
        if telephone and telephone != '#':
            cleaned['telephone'] = clean_telephone(telephone)
        
        cleaned['email'] = safe_str(annonce.get('email'))
        cleaned['site_web'] = safe_str(annonce.get('site_web'))
        
        # ===== 20. DATES =====
        cleaned['date_publication'] = annonce.get('date_publication')
        cleaned['date_scraping'] = clean_date(annonce.get('date_scraping'))
        
        # ===== 21. MÉTADONNÉES =====
        cleaned['page_trouvee'] = safe_int(annonce.get('page_trouvee'), 0)
        cleaned['statut'] = safe_str(annonce.get('statut', 'inchangé'))
        
        if annonce.get('nombre_photos_annonce'):
            cleaned['nombre_photos_annonce'] = safe_int(annonce['nombre_photos_annonce'])
        
        # ===== 22. VALIDATION =====
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
    """Nettoie un fichier JSON d'annonces de vente"""
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
        'villas': 0,
        'maisons': 0,
        'terrains': 0,
        'neufs': 0,
        'avec_piscine': 0,
        'avec_parking': 0
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
            
            type_bien = cleaned.get('type_bien')
            if type_bien == 'Appartement':
                stats['appartements'] += 1
            elif type_bien == 'Villa':
                stats['villas'] += 1
            elif type_bien == 'Maison':
                stats['maisons'] += 1
            elif type_bien == 'Terrain':
                stats['terrains'] += 1
            
            if cleaned.get('etat_bien') == 'Neuf':
                stats['neufs'] += 1
            
            if cleaned.get('a_piscine'):
                stats['avec_piscine'] += 1
            
            if cleaned.get('a_parking'):
                stats['avec_parking'] += 1
                
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
        'type': 'vente'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_nettoyees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE NETTOYAGE - TUNISIA PROMO VENTE")
    print("="*60)
    print(f"📥 Annonces lues: {stats['total']}")
    print(f"🧹 Annonces nettoyées: {stats['nettoyees']}")
    print(f"⏸️ Annonces inchangées: {stats['inchangees']}")
    print(f"✅ Annonces valides: {stats['valides']}")
    print(f"⚠️ Annonces invalides: {stats['invalides']}")
    print(f"📞 Annonces avec téléphone: {stats['avec_telephone']}")
    print(f"🖼️ Annonces avec images: {stats['avec_images']}")
    print(f"🏢 Appartements: {stats['appartements']}")
    print(f"🏠 Villas: {stats['villas']}")
    print(f"🏡 Maisons: {stats['maisons']}")
    print(f"🗺️ Terrains: {stats['terrains']}")
    print(f"🆕 Biens neufs: {stats['neufs']}")
    print(f"🏊 Avec piscine: {stats['avec_piscine']}")
    print(f"🅿️ Avec parking: {stats['avec_parking']}")
    print("="*60)
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    return len(annonces_nettoyees)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des données Tunisia Promo Vente")
    parser.add_argument('--file', '-f', default='tunisiapromo_vente_extrait.json', help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_clean.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_clean(args.file, args.output)


if __name__ == '__main__':
    main()