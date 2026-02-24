"""
Script de nettoyage pour Menzili Location
Nettoie et normalise TOUTES les données des annonces de location
Version avec gestion complète des NoneType et du format prix spécifique
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


# ========== CONSTANTES POUR NORMALISATION ==========

CATEGORIES_NORMALISEES = {
    'maison': 'Maison',
    'villa': 'Villa',
    'appartement': 'Appartement',
    'terrain': 'Terrain',
    'local commercial': 'Local commercial',
    'bureau': 'Bureau',
    'studio': 'Studio'
}

SOUS_CATEGORIES_MAISON = {
    'villa': 'Villa',
    'duplex': 'Duplex',
    'triplex': 'Triplex',
    'plain pied': 'Maison plain-pied',
    'maison': 'Maison'
}

ETATS_NORMALISES = {
    'neuf': 'Neuf',
    'jamais habité': 'Jamais habité',
    'bon état': 'Bon état',
    'très bon état': 'Très bon état',
    'excellent état': 'Excellent état',
    'rénové': 'Rénové'
}

VUES_NORMALISEES = {
    'mer': 'Mer',
    'piscine': 'Piscine',
    'jardin': 'Jardin',
    'dégagée': 'Dégagée'
}

PROXIMITES_NORMALISEES = {
    'plage': 'Plage',
    'mer': 'Mer',
    'commerces': 'Commerces',
    'supermarché': 'Supermarché',
    'carrefour': 'Carrefour',
    'mosquée': 'Mosquée',
    'transports': 'Transports',
    'bus': 'Bus',
    'autoroute': 'Autoroute',
    'jardin': 'Jardin',
    'parc': 'Parc'
}

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte', 'medenine': 'Médenine', 'djerba': 'Médenine'
}

PERIODES_LOCATION_NORMALISEES = {
    'mensuel': 'Mensuel',
    'journalier': 'Journalier',
    'hebdomadaire': 'Hebdomadaire',
    'annuel': 'Annuel',
    'non spécifié': 'Non spécifié'
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


def clean_prix_text(prix: float, periode: str) -> str:
    """Génère un texte de prix normalisé selon la période"""
    if prix == 0:
        return "Prix à consulter"
    
    if periode == 'Mensuel':
        return f"{int(prix):,} TND/mois".replace(',', ' ')
    elif periode == 'Journalier':
        return f"{int(prix):,} TND/nuit".replace(',', ' ')
    elif periode == 'Hebdomadaire':
        return f"{int(prix):,} TND/semaine".replace(',', ' ')
    else:
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


def determine_categorie_principale(categorie: str) -> str:
    """Normalise la catégorie principale"""
    if not categorie:
        return "Inconnu"
    
    categorie_lower = categorie.lower().strip()
    
    for key, value in CATEGORIES_NORMALISEES.items():
        if key in categorie_lower:
            return value
    
    return categorie.title()


def determine_sous_categorie(categorie: str, titre: str, description: str, nombre_etages: Optional[int]) -> str:
    """Détermine la sous-catégorie"""
    if categorie not in ["Maison", "Villa"]:
        return categorie
    
    texte = f"{safe_str(titre)} {safe_str(description)}".lower()
    
    if 'villa' in texte:
        return "Villa"
    elif 'duplex' in texte:
        return "Duplex"
    elif 'triplex' in texte:
        return "Triplex"
    elif 'plain pied' in texte or 'plain-pied' in texte:
        return "Maison plain-pied"
    
    if nombre_etages and nombre_etages > 1:
        return "Maison à étages"
    
    return "Maison"


def determine_periode_location(periode: Optional[str]) -> str:
    """Normalise la période de location"""
    if not periode:
        return "Non spécifié"
    
    periode_lower = periode.lower().strip()
    
    for key, value in PERIODES_LOCATION_NORMALISEES.items():
        if key in periode_lower:
            return value
    
    return periode.title()


def clean_ville(ville_titre: Optional[str], ville_desc: Optional[str]) -> Optional[str]:
    """Nettoie et fusionne les informations de ville"""
    if ville_titre:
        return safe_str(ville_titre)
    if ville_desc:
        return safe_str(ville_desc)
    return None


def clean_quartier(quartier_titre: Optional[str], quartier_desc: Optional[str]) -> Optional[str]:
    """Nettoie et fusionne les informations de quartier"""
    if quartier_titre:
        return safe_str(quartier_titre)
    if quartier_desc:
        return safe_str(quartier_desc)
    return None


def clean_etat(etat: Optional[str]) -> Optional[str]:
    """Normalise l'état du bien"""
    if not etat:
        return None
    
    etat_lower = safe_str(etat).lower()
    
    for key, value in ETATS_NORMALISES.items():
        if key in etat_lower:
            return value
    
    return etat.title()


def clean_vue(vue: Optional[str]) -> Optional[str]:
    """Normalise la vue"""
    if not vue:
        return None
    
    vue_lower = safe_str(vue).lower()
    
    for key, value in VUES_NORMALISEES.items():
        if key in vue_lower:
            return value
    
    return vue.title()


def clean_proximites(proximites: Any) -> List[str]:
    """Nettoie la liste des proximités"""
    items = safe_list(proximites)
    
    cleaned = []
    for item in items:
        if not item:
            continue
        item_lower = item.lower().strip()
        for key, value in PROXIMITES_NORMALISEES.items():
            if key in item_lower:
                if value not in cleaned:
                    cleaned.append(value)
                break
        else:
            cleaned.append(item.title())
    
    return sorted(cleaned)


def clean_telephone(telephone: Optional[str]) -> Optional[str]:
    """Nettoie un numéro de téléphone"""
    if not telephone:
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
    exclude_patterns = [r'no_photo', r'placeholder', r'logo', r'loading']
    
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


def determine_surface_habitable(extracted: Dict) -> Optional[float]:
    """Détermine la surface habitable à partir des différentes sources"""
    for key in ['surface_habitable', 'surface_habitable_desc']:
        val = extracted.get(key)
        if val is not None:
            num = clean_number(val)
            if num and num > 0:
                return num
    return None


def determine_surface_terrain(extracted: Dict) -> Optional[float]:
    """Détermine la surface du terrain à partir des différentes sources"""
    for key in ['surface_terrain', 'surface_terrain_desc']:
        val = extracted.get(key)
        if val is not None:
            num = clean_number(val)
            if num and num > 0:
                return num
    return None


def determine_nombre_chambres(extracted: Dict) -> Optional[int]:
    """Détermine le nombre de chambres à partir des différentes sources"""
    for key in ['chambres', 'chambres_desc']:
        val = extracted.get(key)
        if val is not None:
            num = clean_number(val)
            if num and num > 0:
                return int(num)
    return None


def determine_nombre_sdb(extracted: Dict) -> Optional[int]:
    """Détermine le nombre de salles de bain à partir des différentes sources"""
    for key in ['salles_bain', 'salles_bain_desc']:
        val = extracted.get(key)
        if val is not None:
            num = clean_number(val)
            if num and num > 0:
                return int(num)
    return None


def calculer_prix_m2(prix: float, surface: float) -> Optional[float]:
    """Calcule le prix au m² (pour location mensuelle)"""
    if prix and surface and surface > 0:
        return round(prix / surface, 2)
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
    Nettoie complètement une annonce de location Menzili
    """
    cleaned = {}
    
    try:
        # ===== 1. IDENTIFIANTS =====
        cleaned['annonce_id'] = safe_str(annonce.get('annonce_id'))
        cleaned['url'] = safe_str(annonce.get('url'))
        cleaned['ref_annonce'] = clean_text(annonce.get('ref_annonce'))
        
        # ===== 2. TITRE =====
        cleaned['titre'] = clean_text(annonce.get('titre'))
        
        # ===== 3. PRIX (spécifique location) =====
        prix_mensuel = clean_number(annonce.get('prix_mensuel'))
        prix_journalier = clean_number(annonce.get('prix_journalier'))
        periode = determine_periode_location(annonce.get('periode_location'))
        
        cleaned['periode_location'] = periode
        cleaned['prix_mensuel'] = prix_mensuel
        cleaned['prix_journalier'] = prix_journalier
        
        # Déterminer le prix principal et le texte
        if prix_mensuel and prix_mensuel > 0:
            cleaned['prix_principal'] = prix_mensuel
            cleaned['prix_text'] = clean_prix_text(prix_mensuel, 'Mensuel')
        elif prix_journalier and prix_journalier > 0:
            cleaned['prix_principal'] = prix_journalier
            cleaned['prix_text'] = clean_prix_text(prix_journalier, 'Journalier')
        else:
            cleaned['prix_principal'] = 0
            cleaned['prix_text'] = "Prix à consulter"
        
        # ===== 4. SURFACES =====
        cleaned['surface_habitable'] = determine_surface_habitable(annonce)
        cleaned['surface_terrain'] = determine_surface_terrain(annonce)
        
        # Prix au m² (pour location mensuelle)
        if cleaned['prix_principal'] and cleaned['surface_habitable'] and periode == 'Mensuel':
            cleaned['prix_m2'] = calculer_prix_m2(cleaned['prix_principal'], cleaned['surface_habitable'])
        else:
            cleaned['prix_m2'] = None
        
        # ===== 5. NOMBRES =====
        cleaned['chambres'] = determine_nombre_chambres(annonce)
        cleaned['salles_bain'] = determine_nombre_sdb(annonce)
        cleaned['pieces'] = clean_number(annonce.get('pieces'))
        cleaned['nombre_etages'] = clean_number(annonce.get('nombre_etages'))
        
        # ===== 6. LOCALISATION =====
        ville = clean_ville(annonce.get('ville_titre'), annonce.get('ville_desc'))
        cleaned['ville'] = ville if ville else ""
        
        quartier = clean_quartier(annonce.get('quartier_titre'), annonce.get('quartier_desc'))
        cleaned['quartier'] = quartier if quartier else ""
        
        cleaned['region'] = determine_region_from_ville(cleaned['ville'])
        
        # ===== 7. CATÉGORIES =====
        categorie_originale = safe_str(annonce.get('categorie'))
        cleaned['categorie'] = determine_categorie_principale(categorie_originale)
        
        cleaned['sous_categorie'] = determine_sous_categorie(
            cleaned['categorie'],
            cleaned['titre'],
            safe_str(annonce.get('description')),
            cleaned['nombre_etages']
        )
        
        # ===== 8. DESCRIPTION =====
        cleaned['description'] = clean_text(annonce.get('description'))
        
        # ===== 9. CARACTÉRISTIQUES =====
        cleaned['etat'] = clean_etat(annonce.get('etat'))
        cleaned['vue'] = clean_vue(annonce.get('vue'))
        
        # ===== 10. PROXIMITÉS =====
        cleaned['proximites'] = clean_proximites(annonce.get('proximites', []))
        
        # ===== 11. ÉQUIPEMENTS (booléens) =====
        bool_fields = [
            'a_piscine', 'a_jardin', 'a_garage', 'a_climatisation',
            'a_chauffage', 'a_ascenseur', 'a_terrasse', 'a_balcon',
            'a_meuble', 'a_internet'
        ]
        for field in bool_fields:
            cleaned[field] = safe_bool(annonce.get(field))
        
        # ===== 12. CONDITIONS DE LOCATION =====
        conditions = safe_dict(annonce.get('conditions_location'))
        if conditions:
            cleaned['caution_mois'] = safe_int(conditions.get('caution_mois'))
            cleaned['frais_agence_mois'] = safe_int(conditions.get('frais_agence_mois'))
        
        # ===== 13. OPTIONS =====
        if annonce.get('options_normalisees'):
            cleaned['options'] = safe_list(annonce['options_normalisees'])
        
        # ===== 14. IMAGES =====
        cleaned['images'] = clean_images(annonce.get('images', []))
        cleaned['nombre_images'] = len(cleaned['images'])
        
        # ===== 15. VENDEUR =====
        cleaned['vendeur_nom'] = clean_text(annonce.get('vendeur_nom'))
        cleaned['vendeur_type'] = safe_str(annonce.get('vendeur_type'))
        cleaned['vendeur_url'] = safe_str(annonce.get('vendeur_url'))
        
        # ===== 16. TÉLÉPHONE =====
        telephone = annonce.get('telephone')
        if telephone:
            cleaned['telephone'] = clean_telephone(telephone)
        
        # ===== 17. DATES =====
        cleaned['date_publication'] = annonce.get('date_publication')
        cleaned['date_scraping'] = clean_date(annonce.get('date_scraping'))
        
        # ===== 18. MÉTADONNÉES =====
        cleaned['page_trouvee'] = safe_int(annonce.get('page_trouvee'), 0)
        cleaned['est_premium'] = safe_bool(annonce.get('est_premium'))
        cleaned['statut'] = safe_str(annonce.get('statut', 'inchangé'))
        
        # ===== 19. VALIDATION =====
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


def process_menzili_file_clean(input_path: str, output_path: Optional[str] = None):
    """Nettoie un fichier JSON d'annonces de location Menzili"""
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
        'location_mensuelle': 0,
        'location_journaliere': 0
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
            
            if cleaned.get('periode_location') == 'Mensuel':
                stats['location_mensuelle'] += 1
            elif cleaned.get('periode_location') == 'Journalier':
                stats['location_journaliere'] += 1
                
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
    print("📊 STATISTIQUES DE NETTOYAGE - MENZILI LOCATION")
    print("="*60)
    print(f"📥 Annonces lues: {stats['total']}")
    print(f"🧹 Annonces nettoyées: {stats['nettoyees']}")
    print(f"⏸️ Annonces inchangées: {stats['inchangees']}")
    print(f"✅ Annonces valides: {stats['valides']}")
    print(f"⚠️ Annonces invalides: {stats['invalides']}")
    print(f"📞 Annonces avec téléphone: {stats['avec_telephone']}")
    print(f"🖼️ Annonces avec images: {stats['avec_images']}")
    print(f"📅 Location mensuelle: {stats['location_mensuelle']}")
    print(f"🌙 Location journalière: {stats['location_journaliere']}")
    print("="*60)
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    return len(annonces_nettoyees)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage des données Menzili Location")
    parser.add_argument('--file', '-f', default='menzili_location_extrait.json', help='Fichier JSON à nettoyer')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_clean.json)')
    args = parser.parse_args()
    
    process_menzili_file_clean(args.file, args.output)


if __name__ == '__main__':
    main()