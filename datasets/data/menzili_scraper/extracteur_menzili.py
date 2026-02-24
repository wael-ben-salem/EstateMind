"""
Agent d'extraction pour Menzili
Extrait TOUS les champs possibles des annonces Menzili
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import unicodedata


# ========== CONSTANTES ==========

VILLES_TUNISIE = [
    'tunis', 'la marsa', 'carthage', 'gammarth', 'sidi bou said',
    'le kram', 'salammbô', 'ariana', 'ennasr', 'manzah', 'soukra',
    'raoued', 'ain zaghouan', 'aouina', 'bhar lazreg', 'jardins de carthage',
    'ben arous', 'boumhel', 'mohammedia', 'nabeul', 'hammamet',
    'sousse', 'hammam sousse', 'monastir', 'mahdia', 'sfax', 'bizerte',
    'siliana', 'medenine', 'djerba', 'houmt souk', 'midoun', 'mezraya', 'ghizen',
    'kélibia', 'korba', 'mrezga', 'gammarth', 'raoued', 'kalaat landalous'
]

CATEGORIES = ['Maison', 'Villa', 'Appartement', 'Terrain', 'Local commercial', 'Bureau', 'Studio']

OPTIONS_MAPPING = {
    'interphone': 'Interphone',
    'terrasses': 'Terrasse',
    'garage': 'Garage',
    'jardin': 'Jardin',
    'parabole': 'Parabole/TV',
    'tv': 'Parabole/TV',
    'cuisine équipé': 'Cuisine équipée',
    'cuisine équipée': 'Cuisine équipée',
    'système alarme': 'Alarme',
    'alarme': 'Alarme',
    'place de parc': 'Parking',
    'parking': 'Parking',
    'piscine': 'Piscine',
    'climatisation': 'Climatisation',
    'chauffage': 'Chauffage',
    'double vitrage': 'Double vitrage',
    'double-vitrage': 'Double vitrage',
    'porte blindée': 'Porte blindée',
    'ascenseur': 'Ascenseur',
    'concierge': 'Concierge',
    'cheminée': 'Cheminée',
    'vue mer': 'Vue mer',
    'vue dégagée': 'Vue dégagée',
    'vue panoramique': 'Vue panoramique',
    'meublé': 'Meublé',
    'terrasse': 'Terrasse',
    'balcon': 'Balcon'
}


# ========== FONCTIONS UTILITAIRES ==========

def normalize_text(text: str) -> str:
    """Normalise le texte (enlève les espaces multiples, nettoie)"""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    # Enlever les retours à la ligne et tabs
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Enlever les espaces multiples
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
    """
    Nettoie et normalise une date
    Formats possibles: "2026-30-01" (inversé) -> "2026-01-30"
    """
    if not date_str:
        return None
    
    # Format YYYY-MM-DD
    pattern = r'(\d{4})-(\d{2})-(\d{2})'
    match = re.search(pattern, date_str)
    if match:
        annee, mois, jour = match.groups()
        # Vérifier si le mois > 12 (probablement inversé)
        if int(mois) > 12:
            # Inverser mois et jour
            return f"{annee}-{jour}-{mois}"
        return date_str
    
    return date_str


# ========== EXTRACTION DEPUIS LE TITRE ==========

def extract_ville_from_titre(titre: str) -> Optional[str]:
    """Extrait la ville depuis le titre"""
    if not titre:
        return None
    
    titre_lower = titre.lower()
    
    for ville in VILLES_TUNISIE:
        if ville in titre_lower:
            return ville.title()
    
    return None


def extract_quartier_from_titre(titre: str) -> Optional[str]:
    """Extrait le quartier depuis le titre"""
    if not titre:
        return None
    
    # Patterns de quartiers
    patterns = [
        r'cit[ée]\s+([\w\s\-]+)',
        r'quartier\s+([\w\s\-]+)',
        r'zone\s+([\w\s\-]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, titre, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
    
    return None


def extract_type_bien_from_titre(titre: str) -> Optional[str]:
    """Extrait le type de bien depuis le titre"""
    if not titre:
        return None
    
    titre_lower = titre.lower()
    
    for cat in CATEGORIES:
        if cat.lower() in titre_lower:
            return cat
    
    return None


# ========== EXTRACTION DEPUIS LA DESCRIPTION ==========

def extract_ville_from_description(description: str) -> Optional[str]:
    """Extrait la ville depuis la description"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for ville in VILLES_TUNISIE:
        if ville in desc_lower:
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
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            quartier = m.group(1).strip()
            if len(quartier) > 3 and len(quartier) < 50:
                return quartier.title()
    
    return None


def extract_etat_bien(description: str) -> Optional[str]:
    """Extrait l'état du bien depuis la description"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'neuf' in desc_lower and 'projet neuf' not in desc_lower:
        return 'Neuf'
    elif 'projet neuf' in desc_lower or 'project neuf' in desc_lower:
        return 'Projet neuf'
    elif 'rénové' in desc_lower or 'renové' in desc_lower or 'renove' in desc_lower:
        return 'Rénové'
    elif 'jamais habité' in desc_lower:
        return 'Jamais habité'
    elif 'bon état' in desc_lower:
        return 'Bon état'
    elif 'très bon état' in desc_lower:
        return 'Très bon état'
    elif 'excellent état' in desc_lower:
        return 'Excellent état'
    elif 'à rénover' in desc_lower:
        return 'À rénover'
    
    return None


def extract_titre_foncier(description: str) -> Optional[str]:
    """Extrait le type de titre foncier"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'titre bleu' in desc_lower:
        return 'Titre bleu'
    elif 'titre foncier' in desc_lower:
        return 'Titre foncier'
    elif 'acte notarié' in desc_lower or 'acte notarie' in desc_lower:
        return 'Acte notarié'
    elif 'titre' in desc_lower and 'foncier' in desc_lower:
        return 'Titre foncier'
    
    return None


def extract_zone(description: str) -> Optional[str]:
    """Extrait la zone (urbaine, agricole, etc.)"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'urbain' in desc_lower:
        return 'Urbaine'
    elif 'agricole' in desc_lower:
        return 'Agricole'
    elif 'résidentiel' in desc_lower or 'residentiel' in desc_lower:
        return 'Résidentielle'
    elif 'commercial' in desc_lower:
        return 'Commerciale'
    elif 'industriel' in desc_lower:
        return 'Industrielle'
    elif 'touristique' in desc_lower:
        return 'Touristique'
    
    return None


def extract_proximites(description: str) -> List[str]:
    """Extrait les proximités mentionnées"""
    if not description:
        return []
    
    desc_lower = description.lower()
    proximites = []
    
    keywords = {
        'école': 'École',
        'ecole': 'École',
        'collège': 'Collège',
        'college': 'Collège',
        'lycée': 'Lycée',
        'lycee': 'Lycée',
        'plage': 'Plage',
        'mer': 'Mer',
        'commerces': 'Commerces',
        'supermarché': 'Supermarché',
        'supermarché': 'Supermarché',
        'carrefour': 'Carrefour',
        'mosquée': 'Mosquée',
        'mosquee': 'Mosquée',
        'administration': 'Administration',
        'hopital': 'Hôpital',
        'hôpital': 'Hôpital',
        'clinique': 'Clinique',
        'pharmacie': 'Pharmacie',
        'transport': 'Transports',
        'bus': 'Bus',
        'autoroute': 'Autoroute'
    }
    
    for keyword, label in keywords.items():
        if keyword in desc_lower:
            if label not in proximites:
                proximites.append(label)
    
    return sorted(proximites)


def extract_nombre_etages(description: str) -> Optional[int]:
    """Extrait le nombre d'étages"""
    if not description:
        return None
    
    patterns = [
        r'(\d+)\s*étages?',
        r'(\d+)\s*niveaux?',
        r'r\s*\+\s*(\d+)',
        r'rez-de-chaussée\s*et\s*(\d+)\s*étages?',
        r'deux\s*étages',
        r'trois\s*étages',
    ]
    
    desc_lower = description.lower()
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            if 'deux' in pattern or 'deux' in m.group(0):
                return 2
            elif 'trois' in pattern or 'trois' in m.group(0):
                return 3
            try:
                return int(m.group(1)) + 1
            except:
                pass
    
    return None


def extract_presence_piscine(description: str) -> bool:
    """Détecte la présence d'une piscine"""
    return 'piscine' in description.lower()


def extract_presence_jardin(description: str) -> bool:
    """Détecte la présence d'un jardin"""
    return 'jardin' in description.lower()


def extract_presence_garage(description: str) -> bool:
    """Détecte la présence d'un garage"""
    return 'garage' in description.lower()


def extract_presence_climatisation(description: str) -> bool:
    """Détecte la présence de climatisation"""
    return 'climatisation' in description.lower()


def extract_presence_chauffage(description: str) -> bool:
    """Détecte la présence de chauffage"""
    return 'chauffage' in description.lower()


def extract_presence_ascenseur(description: str) -> bool:
    """Détecte la présence d'ascenseur"""
    return 'ascenseur' in description.lower()


def extract_presence_terrasse(description: str) -> bool:
    """Détecte la présence de terrasse"""
    return 'terrasse' in description.lower()


def extract_presence_balcon(description: str) -> bool:
    """Détecte la présence de balcon"""
    return 'balcon' in description.lower()


def extract_presence_cheminee(description: str) -> bool:
    """Détecte la présence de cheminée"""
    return 'cheminée' in description.lower() or 'cheminee' in description.lower()


def extract_presence_alarme(description: str) -> bool:
    """Détecte la présence d'alarme"""
    desc_lower = description.lower()
    keywords = ['alarme', 'système alarme', 'systeme alarme']
    return any(keyword in desc_lower for keyword in keywords)


def extract_vue(description: str) -> Optional[str]:
    """Extrait le type de vue"""
    if not description:
        return None
    
    desc_lower = description.lower()
    
    if 'vue sur mer' in desc_lower or 'vue mer' in desc_lower:
        return 'Mer'
    elif 'vue panoramique' in desc_lower:
        return 'Panoramique'
    elif 'vue dégagée' in desc_lower or 'vue degagee' in desc_lower:
        return 'Dégagée'
    elif 'vue sur jardin' in desc_lower:
        return 'Jardin'
    elif 'vue sur piscine' in desc_lower:
        return 'Piscine'
    
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
        r'(\d{2}\s*\d{3}\s*\d{3})',
        r'(\d{8,})',
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


def extract_surface_terrain_from_description(description: str) -> Optional[float]:
    """Extrait la surface du terrain depuis la description"""
    if not description:
        return None
    
    patterns = [
        r'terrain\s+de\s*(\d+)\s*m[²2]',
        r'terrain\s*[:\-]?\s*(\d+)\s*m²',
        r'surface\s+du\s+terrain\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_surface_habitable_from_description(description: str) -> Optional[float]:
    """Extrait la surface habitable depuis la description"""
    if not description:
        return None
    
    patterns = [
        r'surface\s*(?:habitable)?\s*[:\-]?\s*(\d+)\s*m[²2]',
        r'(\d+)\s*m[²2]\s*(?:habitable)?',
        r'superficie\s*(?:couverte)?\s*[:\-]?\s*(\d+)\s*m²',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    
    return None


def extract_nombre_chambres_from_description(description: str) -> Optional[int]:
    """Extrait le nombre de chambres depuis la description"""
    if not description:
        return None
    
    patterns = [
        r'(\d+)\s*chambres?',
        r'(\d+)\s*pi[èe]ces?',
    ]
    
    desc_lower = description.lower()
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


def extract_nombre_sdb_from_description(description: str) -> Optional[int]:
    """Extrait le nombre de salles de bain depuis la description"""
    if not description:
        return None
    
    patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'(\d+)\s*sdb',
    ]
    
    desc_lower = description.lower()
    
    for pattern in patterns:
        m = re.search(pattern, desc_lower)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    
    return None


# ========== EXTRACTION DEPUIS LES OPTIONS ==========

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
            # Garder l'original si non mappé
            normalized.append(option.strip().title())
    
    return sorted(normalized)


# ========== EXTRACTION DEPUIS L'URL DU VENDEUR ==========

def extract_vendeur_url_propre(vendeur_url: Any) -> Optional[str]:
    """Nettoie l'URL du vendeur (enlève le HTML)"""
    if not vendeur_url:
        return None
    
    if not isinstance(vendeur_url, str):
        return None
    
    # Extraire l'URL du lien HTML
    match = re.search(r'href="([^"]+)"', vendeur_url)
    if match:
        return match.group(1)
    
    return vendeur_url.strip()


# ========== FONCTION PRINCIPALE D'EXTRACTION ==========

def extract_all_from_annonce(annonce: Dict) -> Dict[str, Any]:
    """
    Extrait TOUS les champs possibles d'une annonce Menzili
    """
    extracted = {}
    
    # ===== 1. DONNÉES DE BASE =====
    extracted['annonce_id'] = str(annonce.get('annonce_id', ''))
    extracted['url'] = annonce.get('url', '')
    extracted['titre'] = normalize_text(annonce.get('titre', ''))
    extracted['date_scraping'] = annonce.get('date_scraping', '')
    extracted['page_trouvee'] = annonce.get('page_trouvee', 0)
    extracted['est_premium'] = bool(annonce.get('est_premium', False))
    extracted['statut'] = annonce.get('statut', 'inchangé')
    extracted['ref_annonce'] = normalize_text(annonce.get('ref_annonce', ''))
    
    # ===== 2. PRIX =====
    prix = clean_number(annonce.get('prix'))
    if prix == 1.0:  # Prix à consulter
        extracted['prix'] = 0
        extracted['prix_text'] = 'Prix à consulter'
        extracted['prix_a_consulter'] = True
    else:
        extracted['prix'] = prix
        if prix:
            extracted['prix_text'] = f"{int(prix):,} TND".replace(',', ' ')
        extracted['prix_a_consulter'] = False
    
    extracted['prix_euro'] = clean_number(annonce.get('prix_euro'))
    
    # ===== 3. SURFACES =====
    extracted['surface_habitable'] = clean_number(annonce.get('surface_habitable'))
    extracted['surface_terrain'] = clean_number(annonce.get('surface_terrain'))
    
    # Si surfaces manquantes, essayer de les extraire de la description
    if not extracted['surface_habitable'] and annonce.get('description'):
        surface_desc = extract_surface_habitable_from_description(annonce['description'])
        if surface_desc:
            extracted['surface_habitable_desc'] = surface_desc
    
    if not extracted['surface_terrain'] and annonce.get('description'):
        terrain_desc = extract_surface_terrain_from_description(annonce['description'])
        if terrain_desc:
            extracted['surface_terrain_desc'] = terrain_desc
    
    # ===== 4. NOMBRES =====
    extracted['chambres'] = clean_number(annonce.get('chambres'))
    extracted['salles_bain'] = clean_number(annonce.get('salles_bain'))
    extracted['pieces'] = clean_number(annonce.get('pieces'))
    
    # Si nombres manquants, essayer de les extraire de la description
    if not extracted['chambres'] and annonce.get('description'):
        chambres_desc = extract_nombre_chambres_from_description(annonce['description'])
        if chambres_desc:
            extracted['chambres_desc'] = chambres_desc
    
    if not extracted['salles_bain'] and annonce.get('description'):
        sdb_desc = extract_nombre_sdb_from_description(annonce['description'])
        if sdb_desc:
            extracted['salles_bain_desc'] = sdb_desc
    
    # ===== 5. CATÉGORIES =====
    extracted['categorie'] = annonce.get('categorie', '')
    
    # ===== 6. DESCRIPTION =====
    description = annonce.get('description', '')
    extracted['description'] = normalize_text(description)
    
    # ===== 7. EXTRACTIONS DEPUIS LE TITRE =====
    titre = extracted['titre']
    
    ville_titre = extract_ville_from_titre(titre)
    if ville_titre:
        extracted['ville_titre'] = ville_titre
    
    quartier_titre = extract_quartier_from_titre(titre)
    if quartier_titre:
        extracted['quartier_titre'] = quartier_titre
    
    type_bien_titre = extract_type_bien_from_titre(titre)
    if type_bien_titre:
        extracted['type_bien_titre'] = type_bien_titre
    
    # ===== 8. EXTRACTIONS DEPUIS LA DESCRIPTION =====
    if description:
        # Ville et quartier
        ville_desc = extract_ville_from_description(description)
        if ville_desc:
            extracted['ville_desc'] = ville_desc
        
        quartier_desc = extract_quartier_from_description(description)
        if quartier_desc:
            extracted['quartier_desc'] = quartier_desc
        
        # État
        etat = extract_etat_bien(description)
        if etat:
            extracted['etat'] = etat
        
        # Titre foncier
        titre_foncier = extract_titre_foncier(description)
        if titre_foncier:
            extracted['titre_foncier'] = titre_foncier
        
        # Zone
        zone = extract_zone(description)
        if zone:
            extracted['zone'] = zone
        
        # Proximités
        proximites = extract_proximites(description)
        if proximites:
            extracted['proximites'] = proximites
        
        # Nombre d'étages
        nb_etages = extract_nombre_etages(description)
        if nb_etages:
            extracted['nombre_etages'] = nb_etages
        
        # Équipements et caractéristiques
        extracted['a_piscine'] = extract_presence_piscine(description)
        extracted['a_jardin'] = extract_presence_jardin(description)
        extracted['a_garage'] = extract_presence_garage(description)
        extracted['a_climatisation'] = extract_presence_climatisation(description)
        extracted['a_chauffage'] = extract_presence_chauffage(description)
        extracted['a_ascenseur'] = extract_presence_ascenseur(description)
        extracted['a_terrasse'] = extract_presence_terrasse(description)
        extracted['a_balcon'] = extract_presence_balcon(description)
        extracted['a_cheminee'] = extract_presence_cheminee(description)
        extracted['a_alarme'] = extract_presence_alarme(description)
        
        # Vue
        vue = extract_vue(description)
        if vue:
            extracted['vue'] = vue
        
        # Téléphone
        telephone = extract_telephone(description)
        if telephone:
            extracted['telephone'] = telephone
    
    # ===== 9. OPTIONS =====
    options = annonce.get('options', [])
    if options:
        extracted['options_brutes'] = options
        extracted['options_normalisees'] = normalize_options(options)
    
    # ===== 10. IMAGES =====
    images = annonce.get('images_urls', [])
    if isinstance(images, list):
        # Filtrer les images placeholder
        extracted['images'] = [
            img for img in images 
            if img and 'no_photo' not in img and 'placeholder' not in img
        ]
        extracted['nombre_images'] = len(extracted['images'])
    else:
        extracted['images'] = []
        extracted['nombre_images'] = 0
    
    # ===== 11. VENDEUR =====
    extracted['vendeur_nom'] = normalize_text(annonce.get('vendeur_nom', ''))
    extracted['vendeur_type'] = annonce.get('vendeur_type', '')
    
    vendeur_url = annonce.get('vendeur_url')
    if vendeur_url:
        extracted['vendeur_url'] = extract_vendeur_url_propre(vendeur_url)
    
    # ===== 12. DATE DE PUBLICATION =====
    date_pub = annonce.get('date_publication', '')
    if date_pub:
        extracted['date_publication'] = clean_date(date_pub)
    
    return extracted


def extraire_menzili(annonce: Dict) -> Dict:
    """
    Fonction principale d'extraction pour une annonce Menzili
    """
    return extract_all_from_annonce(annonce)


def load_existing_annonces(filepath: Path) -> Dict[str, Dict]:
    """
    Charge les annonces existantes depuis un fichier JSON
    """
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Différents formats possibles
        if isinstance(data, list):
            return {str(a.get('annonce_id')): a for a in data if a.get('annonce_id')}
        elif isinstance(data, dict) and 'annonces' in data:
            return {str(a.get('annonce_id')): a for a in data['annonces'] if a.get('annonce_id')}
        elif isinstance(data, dict):
            annonces_dict = {}
            for key, value in data.items():
                if isinstance(value, dict) and 'annonce_id' in value:
                    annonces_dict[str(value['annonce_id'])] = value
            return annonces_dict
    except json.JSONDecodeError:
        print(f"⚠️ Fichier {filepath} corrompu")
    
    return {}


def process_menzili_file_extract(input_path: str, output_path: Optional[str] = None):
    """
    Traite le fichier JSON de Menzili (extraction uniquement)
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {input_path}")
    
    output_file = Path(output_path) if output_path else input_file.parent / f"{input_file.stem}_extrait.json"
    
    # Charger les données existantes (pour mise à jour)
    existing_dict = load_existing_annonces(output_file)
    
    # Charger les nouvelles données
    with open(input_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    # Normaliser en liste
    if isinstance(new_data, list):
        nouvelles_annonces = new_data
    elif isinstance(new_data, dict) and 'annonces' in new_data:
        nouvelles_annonces = new_data['annonces']
    else:
        nouvelles_annonces = list(new_data.values()) if isinstance(new_data, dict) else []
    
    # Statistiques
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
            print(f"⚠️ Annonce sans ID ignorée")
            stats['ignorees'] += 1
            continue
        
        # Vérifier si l'annonce existait déjà
        existing = existing_dict.get(annonce_id)
        
        # Déterminer si on doit traiter
        doit_traiter = (
            statut in ['nouveau', 'modifié'] or  # Nouvelle ou modifiée
            not existing  # N'existait pas
        )
        
        if doit_traiter:
            # Extraire les données
            extracted = extraire_menzili(annonce)
            annonces_traitees.append(extracted)
            
            if statut == 'nouveau':
                stats['nouvelles'] += 1
            elif statut == 'modifié':
                stats['modifiees'] += 1
            else:
                stats['nouvelles'] += 1
        else:
            # Garder l'ancienne version inchangée
            if existing:
                annonces_traitees.append(existing)
                stats['inchangées'] += 1
            else:
                # Cas improbable, mais on traite quand même
                extracted = extraire_menzili(annonce)
                annonces_traitees.append(extracted)
                stats['nouvelles'] += 1
    
    # Trier par ID (optionnel)
    annonces_traitees.sort(key=lambda x: x.get('annonce_id', ''))
    
    # Métadonnées
    metadata = {
        'date_extraction': datetime.now().isoformat(),
        'total_annonces': len(annonces_traitees),
        'statistiques': stats,
        'version': '1.0'
    }
    
    # Sauvegarder
    output_data = {
        'metadata': metadata,
        'annonces': annonces_traitees
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES D'EXTRACTION - MENZILI")
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
    parser = argparse.ArgumentParser(description="Agent d'extraction pour Menzili")
    parser.add_argument('--file', '-f', default='menzili_annonces.json', help='Fichier JSON des annonces')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: *_extrait.json)')
    args = parser.parse_args()
    
    process_menzili_file_extract(args.file, args.output)


if __name__ == '__main__':
    main()