"""
Agent d'extraction pour Tunisia Promo - Colocation
Extrait TOUS les champs possibles des annonces de colocation
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import unicodedata


# ========== CONSTANTES ==========

TYPES_BIENS = [
    'appartement', 'villa', 'maison', 'bureau', 'studio', 'foyer', 'chambre'
]

TYPES_LOGEMENTS = {
    'chambre privée': 'Chambre privée',
    'chambre individuelle': 'Chambre privée',
    'chambre double': 'Chambre double',
    'bureau partagé': 'Bureau partagé',
    'appartement partagé': 'Appartement partagé',
    'foyer': 'Foyer'
}

GENRES = {
    'f': 'Femme',
    'femme': 'Femme',
    'fille': 'Femme',
    'féminin': 'Femme',
    'm': 'Homme',
    'homme': 'Homme',
    'garçon': 'Homme',
    'masculin': 'Homme',
    'mixte': 'Mixte'
}

PROFILS = {
    'étudiant': 'Étudiant',
    'etudiant': 'Étudiant',
    'élève': 'Étudiant',
    'fonctionnaire': 'Fonctionnaire',
    'cadre': 'Cadre',
    'professionnel': 'Professionnel',
    'ingénieur': 'Ingénieur'
}

OPTIONS_MAPPING = {
    'balcon': 'Balcon',
    'bureau': 'Bureau',
    'chauffage': 'Chauffage',
    'climatisation': 'Climatisation',
    'connexion internet': 'Internet',
    'internet': 'Internet',
    'wifi': 'Internet',
    'cuisine équipée': 'Cuisine équipée',
    'meublé': 'Meublé',
    'terrasse': 'Terrasse',
    'jardin': 'Jardin',
    'parking': 'Parking',
    'garage': 'Garage',
    'place de parc': 'Parking',
    'interphone': 'Interphone',
    'système d\'alarme': 'Alarme',
    'alarme': 'Alarme',
    'haut standing': 'Haut standing',
    'dépendances': 'Dépendances'
}

EQUIPEMENTS_MAPPING = {
    'four': 'Four',
    'lave-linge': 'Lave-linge',
    'micro-onde': 'Micro-ondes',
    'micro-ondes': 'Micro-ondes',
    'récepteur satellite': 'Parabole/TV',
    'réfrigérateur': 'Réfrigérateur',
    'tv': 'TV',
    'tv lcd': 'TV LCD',
    'télévision': 'TV'
}

VILLES_TUNISIE = [
    'tunis', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'le kram', 'salammbô', 'ariana', 'ennasr', 'manzah', 'soukra',
    'raoued', 'ain zaghouan', 'aouina', 'bhar lazreg', 'jardins de carthage',
    'ben arous', 'boumhel', 'mohammedia', 'nabeul', 'hammamet',
    'sousse', 'hammam sousse', 'monastir', 'mahdia', 'sfax', 'bizerte',
    'siliana', 'medenine', 'djerba', 'houmt souk', 'midoun', 'mezraya', 'ghizen',
    'kélibia', 'korba', 'mrezga', 'raoued', 'el hafsia', 'thrayette', 'sousse riadh',
    'bab bhar', 'la médina', 'la soukra'
]

REGIONS_MAPPING = {
    'tunis': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis', 'le kram': 'Tunis',
    'ariana': 'Ariana', 'ennasr': 'Ariana', 'manzah': 'Ariana', 'soukra': 'Ariana', 'raoued': 'Ariana',
    'ben arous': 'Ben Arous', 'boumhel': 'Ben Arous', 'mohammedia': 'Ben Arous',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'kélibia': 'Nabeul',
    'sousse': 'Sousse', 'hammam sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'sfax': 'Sfax', 'bizerte': 'Bizerte', 'medenine': 'Médenine', 'djerba': 'Médenine'
}


# ========== FONCTIONS UTILITAIRES ==========

def normalize_text(text: str) -> str:
    """Normalise le texte"""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_number_from_text(text: str) -> Optional[float]:
    """Extrait le premier nombre d'un texte"""
    if not text:
        return None
    numbers = re.findall(r'\d+[.,]?\d*', text.replace(' ', ''))
    if numbers:
        try:
            return float(numbers[0].replace(',', '.'))
        except:
            return None
    return None


def clean_number(value: Any) -> Optional[float]:
    """Nettoie une valeur numérique"""
    if value is None:
        return None
    
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
    
    return None


def clean_date(date_str: str) -> Optional[str]:
    """Nettoie et normalise une date"""
    if not date_str or 'Annonce' in date_str:
        return None
    
    # Essayer de trouver une date dans le format YYYY-MM-DD
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, date_str)
    if match:
        return match.group(1)
    
    return None


# ========== EXTRACTION DU GENRE ==========

def extract_genre(genre_str: str) -> str:
    """Normalise le genre recherché"""
    if not genre_str or genre_str == "Non spécifié":
        return "Non spécifié"
    
    genre_lower = genre_str.lower().strip()
    
    for key, value in GENRES.items():
        if key in genre_lower:
            return value
    
    return genre_str


def extract_genre_from_description(description: str) -> Optional[str]:
    """Extrait le genre recherché depuis la description"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    # Chercher des indices
    if 'fille' in desc_lower or 'femme' in desc_lower or 'étudiante' in desc_lower:
        return 'Femme'
    elif 'garçon' in desc_lower or 'homme' in desc_lower or 'étudiant' in desc_lower:
        return 'Homme'
    
    return None


# ========== EXTRACTION DU PROFIL ==========

def extract_profil(description: str) -> Optional[str]:
    """Extrait le profil du colocataire recherché"""
    if not description:
        return None
    
    desc_lower = description.lower()
    profils_trouves = []
    
    for key, value in PROFILS.items():
        if key in desc_lower:
            if value not in profils_trouves:
                profils_trouves.append(value)
    
    return profils_trouves if profils_trouves else None


# ========== EXTRACTION DU TYPE DE LOGEMENT ==========

def extract_type_logement(type_logement: str, type_bien: str, description: str) -> str:
    """Détermine le type de logement en colocation"""
    if type_logement and type_logement != "Non spécifié":
        type_lower = type_logement.lower()
        for key, value in TYPES_LOGEMENTS.items():
            if key in type_lower:
                return value
        return type_logement
    
    # Déduire du type de bien et de la description
    type_bien_lower = type_bien.lower() if type_bien else ""
    desc_lower = description.lower() if description else ""
    
    if 'bureau' in type_bien_lower or 'bureau' in desc_lower:
        return "Bureau partagé"
    elif 'foyer' in type_bien_lower or 'foyer' in desc_lower:
        return "Foyer"
    elif 'chambre' in type_bien_lower or 'chambre' in desc_lower:
        if 'double' in desc_lower:
            return "Chambre double"
        else:
            return "Chambre privée"
    else:
        return "Appartement partagé"


# ========== EXTRACTION DES CHARGES ==========

def extract_charges_incluses(description: str) -> Dict[str, bool]:
    """Extrait les charges incluses depuis la description"""
    if not description:
        return {}
    
    desc_lower = description.lower()
    charges = {}
    
    if 'charges comprises' in desc_lower:
        charges['charges_incluses'] = True
        charges['details'] = []
        
        if 'électricité' in desc_lower or 'electricite' in desc_lower:
            charges['details'].append('Électricité')
        if 'eau' in desc_lower:
            charges['details'].append('Eau')
        if 'gaz' in desc_lower:
            charges['details'].append('Gaz')
        if 'internet' in desc_lower or 'wifi' in desc_lower:
            charges['details'].append('Internet')
    
    return charges


# ========== EXTRACTION DES OPTIONS ET ÉQUIPEMENTS ==========

def normalize_options(options: List[str]) -> List[str]:
    """Normalise la liste des options"""
    if not options:
        return []
    
    normalized = []
    
    for option in options:
        if not isinstance(option, str):
            continue
        
        option_lower = option.lower().strip()
        
        for key, value in OPTIONS_MAPPING.items():
            if key in option_lower:
                if value not in normalized:
                    normalized.append(value)
                break
        else:
            normalized.append(option.strip().title())
    
    return sorted(normalized)


def normalize_equipements(equipements: List[str]) -> List[str]:
    """Normalise la liste des équipements"""
    if not equipements:
        return []
    
    normalized = []
    
    for equip in equipements:
        if not isinstance(equip, str):
            continue
        
        equip_lower = equip.lower().strip()
        
        for key, value in EQUIPEMENTS_MAPPING.items():
            if key in equip_lower:
                if value not in normalized:
                    normalized.append(value)
                break
        else:
            normalized.append(equip.strip().title())
    
    return sorted(normalized)


# ========== EXTRACTION DEPUIS LA DESCRIPTION ==========

def extract_ville_from_description(description: str, titre: str) -> Optional[str]:
    """Extrait la ville depuis la description ou le titre"""
    texte = f"{titre} {description}".lower()
    
    for ville in VILLES_TUNISIE:
        if ville in texte:
            return ville.title()
    
    return None


def extract_quartier_from_description(description: str) -> Optional[str]:
    """Extrait le quartier depuis la description"""
    if not description:
        return None
    
    patterns = [
        r'quartier\s+([\w\s\-]+)',
        r'cit[ée]\s+([\w\s\-]+)',
        r'à\s+([\w\s\-]+?)(?:\s*\.|\,|\s+à|\s+dans)',
        r'dans\s+([\w\s\-]+?)(?:\s*\.|\,)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            quartier = m.group(1).strip()
            if len(quartier) > 3 and len(quartier) < 50:
                # Vérifier que ce n'est pas une ville
                if quartier.lower() not in VILLES_TUNISIE:
                    return quartier.title()
    
    return None


def extract_proximites(description: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    if not description:
        return []
    
    desc_lower = description.lower()
    proximites = []
    
    keywords = {
        'métro': 'Métro',
        'metro': 'Métro',
        'train': 'Train',
        'bus': 'Bus',
        'station': 'Station',
        'commerces': 'Commerces',
        'magasins': 'Commerces',
        'monoprix': 'Monoprix',
        'aziza': 'Aziza',
        'université': 'Université',
        'universite': 'Université',
        'fac': 'Université',
        'école': 'École',
        'ecole': 'École',
        'lycée': 'Lycée',
        'lycee': 'Lycée'
    }
    
    for keyword, label in keywords.items():
        if keyword in desc_lower:
            if label not in proximites:
                proximites.append(label)
    
    return sorted(proximites)


def extract_nombre_colocataires(description: str) -> Optional[int]:
    """Extrait le nombre de colocataires"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    patterns = [
        r'avec\s+une\s+autre',
        r'partager\s+avec\s+une',
        r'(\d+)\s*personnes?',
        r'(\d+)\s*colocataires?'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            if 'une autre' in pattern or 'une' in m.group(0):
                return 1
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_telephone(description: str) -> Optional[str]:
    """Extrait le numéro de téléphone de la description"""
    if not description:
        return None
    
    patterns = [
        r'(?:\+216|00216|216)?\s*(\d[\d\s]{7,})',
        r't[eé]l[eé]phone\s*[:\-]?\s*(\d[\d\s]{7,})',
        r'contact\s*(?:\s*:)?\s*(\d[\d\s]{7,})',
        r'whatsapp[:\s]*(\d[\d\s]{7,})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description)
        if m:
            tel = re.sub(r'\s', '', m.group(1))
            if len(tel) >= 8:
                if not tel.startswith('+216') and len(tel) == 8:
                    return f"+216{tel}"
                return tel
    
    return None


def extract_email(description: str) -> Optional[str]:
    """Extrait l'email de la description"""
    if not description:
        return None
    
    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    m = re.search(pattern, description)
    if m:
        return m.group(0)
    
    return None


def extract_site_web(description: str) -> Optional[str]:
    """Extrait le site web de la description"""
    if not description:
        return None
    
    patterns = [
        r'www\.[a-zA-Z0-9\.\-]+\.(?:com|tn|fr|net|org)',
        r'https?://[^\s]+'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description)
        if m:
            url = m.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    
    return None


# ========== EXTRACTION DEPUIS L'URL ==========

def extract_reference_from_url(url: str) -> Optional[str]:
    """Extrait la référence depuis l'URL"""
    if not url:
        return None
    
    # Format: ...-z140709.html
    match = re.search(r'-z(\d+)\.html', url)
    if match:
        return match.group(1)
    
    return None


# ========== EXTRACTION DES IMAGES ==========

def extract_images_list(images_urls: Any, nombre_photos: Any) -> List[str]:
    """Extrait la liste des images"""
    if images_urls and isinstance(images_urls, list):
        return images_urls
    
    return []


# ========== FONCTION PRINCIPALE D'EXTRACTION ==========

def extract_all_from_annonce(annonce: Dict) -> Dict[str, Any]:
    """
    Extrait TOUS les champs possibles d'une annonce de colocation Tunisia Promo
    """
    extracted = {}
    
    # ===== 1. DONNÉES DE BASE =====
    extracted['annonce_id'] = str(annonce.get('annonce_id', ''))
    extracted['url'] = annonce.get('url', '')
    extracted['titre'] = normalize_text(annonce.get('titre', ''))
    extracted['date_scraping'] = annonce.get('date_scraping', '')
    extracted['page_trouvee'] = annonce.get('page_trouvee', 0)
    extracted['statut'] = annonce.get('statut', 'inchangé')
    extracted['reference'] = annonce.get('reference', '') or extract_reference_from_url(extracted['url'])
    
    # ===== 2. TYPE D'ANNONCE =====
    extracted['type_annonce'] = annonce.get('type_annonce', 'Offre')
    
    # ===== 3. PRIX =====
    prix = clean_number(annonce.get('prix'))
    extracted['prix'] = prix if prix and prix > 0 else 0
    if prix and prix > 0:
        extracted['prix_text'] = f"{int(prix):,} TND/mois".replace(',', ' ')
    else:
        extracted['prix_text'] = "Prix à consulter"
    
    # ===== 4. LOCALISATION =====
    extracted['region'] = annonce.get('region', '')
    extracted['ville'] = annonce.get('ville', '')
    extracted['quartier'] = annonce.get('quartier', '')
    extracted['adresse'] = normalize_text(annonce.get('adresse', ''))
    extracted['code_postal'] = annonce.get('code_postal', '')
    
    # Si ville manquante, essayer de l'extraire
    if not extracted['ville'] and annonce.get('description'):
        ville_desc = extract_ville_from_description(
            annonce.get('description', ''),
            extracted['titre']
        )
        if ville_desc:
            extracted['ville'] = ville_desc
    
    # Si quartier manquant, essayer de l'extraire
    if not extracted['quartier'] and annonce.get('description'):
        quartier_desc = extract_quartier_from_description(annonce.get('description', ''))
        if quartier_desc:
            extracted['quartier'] = quartier_desc
    
    # ===== 5. TYPE DE BIEN =====
    extracted['type_bien'] = annonce.get('type_bien', '')
    
    # ===== 6. TYPE DE LOGEMENT (colocation) =====
    type_logement = annonce.get('type_logement', '')
    extracted['type_logement'] = extract_type_logement(
        type_logement,
        extracted['type_bien'],
        annonce.get('description', '')
    )
    
    # ===== 7. GENRE RECHERCHÉ =====
    genre = annonce.get('genre_recherche', 'Non spécifié')
    extracted['genre_recherche'] = extract_genre(genre)
    
    # Si genre non spécifié, essayer de l'extraire de la description
    if extracted['genre_recherche'] == 'Non spécifié' and annonce.get('description'):
        genre_desc = extract_genre_from_description(annonce.get('description', ''))
        if genre_desc:
            extracted['genre_recherche'] = genre_desc
    
    # ===== 8. DESCRIPTION =====
    description = annonce.get('description', '')
    extracted['description'] = normalize_text(description)
    
    # ===== 9. EXTRACTIONS DEPUIS LA DESCRIPTION =====
    if description:
        # Profil recherché
        profil = extract_profil(description)
        if profil:
            extracted['profil_recherche'] = profil
        
        # Charges incluses
        charges = extract_charges_incluses(description)
        if charges:
            extracted['charges'] = charges
        
        # Proximités
        proximites = extract_proximites(description)
        if proximites:
            extracted['proximites'] = proximites
        
        # Nombre de colocataires
        nb_coloc = extract_nombre_colocataires(description)
        if nb_coloc:
            extracted['nombre_colocataires'] = nb_coloc
        
        # Téléphone
        telephone = extract_telephone(description)
        if telephone:
            extracted['telephone'] = telephone
        
        # Email
        email = extract_email(description)
        if email:
            extracted['email'] = email
        
        # Site web
        site_web = extract_site_web(description)
        if site_web:
            extracted['site_web'] = site_web
    
    # ===== 10. CARACTÉRISTIQUES DU BIEN =====
    extracted['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
    extracted['pieces'] = clean_number(annonce.get('pieces'))
    extracted['etage'] = clean_number(annonce.get('etage'))
    extracted['annee_construction'] = clean_number(annonce.get('annee_construction'))
    extracted['places_voiture'] = clean_number(annonce.get('places_voiture'))
    
    # ===== 11. OPTIONS ET ÉQUIPEMENTS =====
    options = annonce.get('options', [])
    if options:
        extracted['options_brutes'] = options
        extracted['options_normalisees'] = normalize_options(options)
    
    equipements = annonce.get('equipements', [])
    if equipements:
        extracted['equipements_bruts'] = equipements
        extracted['equipements_normalises'] = normalize_equipements(equipements)
    
    # Fusionner options et équipements
    all_equip = []
    if extracted.get('options_normalisees'):
        all_equip.extend(extracted['options_normalisees'])
    if extracted.get('equipements_normalises'):
        all_equip.extend(extracted['equipements_normalises'])
    if all_equip:
        extracted['tous_equipements'] = sorted(list(set(all_equip)))
    
    # ===== 12. IMAGES =====
    images = extract_images_list(
        annonce.get('images_urls', []),
        annonce.get('nombre_photos')
    )
    extracted['images'] = images
    extracted['nombre_images'] = len(images)
    
    # ===== 13. ANNONCEUR =====
    extracted['annonceur_type'] = annonce.get('annonceur_type')
    extracted['annonceur_telephone'] = annonce.get('annonceur_telephone', '#')
    
    # ===== 14. DATE DE PUBLICATION =====
    date_pub = annonce.get('date_publication', '')
    if date_pub and 'Annonce' not in date_pub:
        extracted['date_publication'] = clean_date(date_pub)
    else:
        extracted['date_publication'] = None
    
    # ===== 15. MÉTADONNÉES =====
    if annonce.get('nombre_photos'):
        extracted['nombre_photos_annonce'] = annonce.get('nombre_photos')
    
    return extracted


def extraire_tunisiapromo_colocation(annonce: Dict) -> Dict:
    """
    Fonction principale d'extraction pour une annonce de colocation Tunisia Promo
    """
    return extract_all_from_annonce(annonce)


def load_existing_annonces(filepath: Path) -> Dict[str, Dict]:
    """Charge les annonces existantes depuis un fichier JSON"""
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {str(a.get('annonce_id')): a for a in data if a.get('annonce_id')}
        elif isinstance(data, dict) and 'annonces' in data:
            return {str(a.get('annonce_id')): a for a in data['annonces'] if a.get('annonce_id')}
    except json.JSONDecodeError:
        print(f"⚠️ Fichier {filepath} corrompu")
    
    return {}


def process_tunisiapromo_file_extract(input_path: str, output_path: Optional[str] = None):
    """
    Traite le fichier JSON de Tunisia Promo (extraction uniquement)
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    output_file = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_extrait.json"
    
    existing_dict = load_existing_annonces(output_file)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    if isinstance(new_data, list):
        nouvelles_annonces = new_data
    else:
        nouvelles_annonces = []
    
    stats = {
        'total_original': len(nouvelles_annonces),
        'nouvelles': 0,
        'modifiees': 0,
        'inchangées': 0,
        'ignorees': 0
    }
    
    annonces_traitees = []
    
    for annonce in nouvelles_annonces:
        annonce_id = str(annonce.get('annonce_id', ''))
        statut = annonce.get('statut', 'inchangé')
        
        if not annonce_id:
            stats['ignorees'] += 1
            continue
        
        existing = existing_dict.get(annonce_id)
        
        doit_traiter = (
            statut in ['nouveau', 'modifié'] or
            not existing
        )
        
        if doit_traiter:
            extracted = extraire_tunisiapromo_colocation(annonce)
            annonces_traitees.append(extracted)
            
            if statut == 'nouveau':
                stats['nouvelles'] += 1
            elif statut == 'modifié':
                stats['modifiees'] += 1
            else:
                stats['nouvelles'] += 1
        else:
            if existing:
                annonces_traitees.append(existing)
                stats['inchangées'] += 1
            else:
                extracted = extraire_tunisiapromo_colocation(annonce)
                annonces_traitees.append(extracted)
                stats['nouvelles'] += 1
    
    annonces_traitees.sort(key=lambda x: x.get('annonce_id', ''))
    
    metadata = {
        'date_extraction': datetime.now().isoformat(),
        'total_annonces': len(annonces_traitees),
        'statistiques': stats,
        'version': '1.0',
        'type': 'colocation'
    }
    
    output_data = {
        'metadata': metadata,
        'annonces': annonces_traitees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES D'EXTRACTION - TUNISIA PROMO COLOCATION")
    print("="*60)
    print(f"📥 Annonces lues: {stats['total_original']}")
    print(f"🆕 Nouvelles annonces extraites: {stats['nouvelles']}")
    print(f"✏️ Annonces modifiées extraites: {stats['modifiees']}")
    print(f"⏸️ Annonces inchangées conservées: {stats['inchangées']}")
    print(f"⚠️ Annonces ignorées: {stats['ignorees']}")
    print(f"📊 Total après extraction: {len(annonces_traitees)}")
    print("="*60)
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    return len(annonces_traitees)


def main():
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Tunisia Promo Colocation")
    parser.add_argument('--file', '-f', default='tunisiapromo_colocation.json', help='Fichier JSON des annonces')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_extrait.json)')
    args = parser.parse_args()
    
    process_tunisiapromo_file_extract(args.file, args.output)


if __name__ == '__main__':
    main()