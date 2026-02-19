"""
Module d'extraction de données structurées depuis le champ description.
Exemple: "Appartement S3 Très Haut Standing au 10ème étage à jardin de Carthage..."
→ type_appartement: S3, etage: 10, quartier: jardin de Carthage
"""
import re
from typing import Dict, Optional, Any


def extract_from_description(description: str, property_category: str = "appartement") -> Dict[str, Any]:
    """
    Extrait les données structurées depuis une description textuelle.
    
    Args:
        description: Texte de la description
        property_category: appartement | villa | maison | bureau | locaux_com
    
    Returns:
        Dict avec les champs extraits (seulement ceux trouvés)
    """
    if not description or not isinstance(description, str):
        return {}
    
    text = description
    text_lower = text.lower()
    extracted = {}
    
    # === TYPE APPARTEMENT / PIÈCES (S+1, S+2, S+3, S3, S4...) ===
    type_patterns = [
        (r'Appartement\s+S(\d+)[^\w]', 'S{}', 'type_appartement'),
        (r'appartement\s+s(\d+)[^\w]', 'S{}', 'type_appartement'),
        (r'\bS(\d+)\s+Tr[eé]s?\s*Haut', 'S{}', 'type_appartement'),
        (r'\bS(\d+)\s+[Hh]aut\s+[Ss]tanding', 'S{}', 'type_appartement'),
        (r'\bS\+(\d+)\b', 'S+{}', 'type_appartement'),
        (r'\bS(\d+)\b(?!\s*m[²2])', 'S{}', 'type_appartement'),  # S3, S4 (pas suivi de m²)
        (r'(\d+)\s*pi[èe]ces?\b', lambda m: "Studio/S1" if m.group(1) == "1" else f"S{m.group(1)}", 'type_appartement'),
        (r'studio\b', 'Studio/S1', 'type_appartement'),
        (r'Un\s+Appartement\s+S(\d+)', 'S{}', 'type_appartement'),
    ]
    
    for pattern, format_val, key in type_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and key not in extracted:
            if callable(format_val):
                extracted[key] = format_val(match)
            else:
                extracted[key] = format_val.format(match.group(1))
            break
    
    # === ÉTAGE ===
    etage_patterns = [
        r'(\d+)[eè]me?\s*[eé]tage',
        r'au\s+(\d+)[eè]me?\s*[eé]tage',
        r'(\d+)[eè]me?\s*étage',
        r'au\s+(\d+)\s*ème\s*étage',
        r'étage\s*[:\-]?\s*(\d+)',
    ]
    for p in etage_patterns:
        m = re.search(p, text_lower)
        if m:
            extracted['etage'] = m.group(1)
            break
    
    if 'rdc' in text_lower or 'rez-de-chaussée' in text_lower or 'rez de chaussée' in text_lower:
        extracted['etage'] = 'RDC'
    
    # === QUARTIER / LIEU (jardin de Carthage, La Marsa, etc.) ===
    lieu_patterns = [
        r'[àa]\s+([\w\s\-]+?)(?:\s+se\s+compose|\.|$)',
        r'à\s+(jardin\s+de\s+\w+)',
        r'dans?\s+(?:le\s+)?([\w\s\-]+?)(?:\s+(?:quartier|zone)|\.|$)',
        r'([\w\s\-]+),\s*(?:Tunis|Tunisie)',
    ]
    for p in lieu_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            quartier = m.group(1).strip()
            if len(quartier) > 2 and quartier.lower() not in ('la', 'le', 'les', 'un', 'une'):
                extracted['quartier_extrait'] = quartier
                break
    
    # Villes connues
    villes = ['carthage', 'la marsa', 'gammarth', 'la soukra', 'ariana', 'hammamet', 'nabeul', 'tunis']
    for v in villes:
        if v in text_lower:
            extracted['ville_extrait'] = v.title()
            break
    
    # === NOMBRE CHAMBRES ===
    chambre_patterns = [
        r'(\d+)\s*chambre[s]?\s*à\s*coucher',
        r'(\d+)\s*chambre',
        r'Deux\s+Chambres',
        r'Trois\s+Chambres',
        r'Une\s+Suite\s+Parentale',
    ]
    for p in chambre_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            if 'deux' in m.group(0).lower():
                extracted['nombre_chambres'] = 2
            elif 'trois' in m.group(0).lower():
                extracted['nombre_chambres'] = 3
            elif 'suite parentale' in m.group(0).lower():
                extracted['nombre_chambres'] = (extracted.get('nombre_chambres', 0) or 0) + 1
            elif m.group(1).isdigit():
                extracted['nombre_chambres'] = int(m.group(1))
            break
    
    # === SALLES DE BAIN ===
    sdb_patterns = [
        r'(\d+)\s*salle[s]?\s*(?:de\s*)?bain',
        r'(\d+)\s*salle[s]?\s*d\'eau',
        r'Une\s+salle\s+de\s+bain',
        r'Une\s+salle\s+d\'eau',
    ]
    for p in sdb_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            if 'une' in m.group(0).lower():
                extracted['nombre_sdb'] = 1
            elif m.lastindex and m.group(1).isdigit():
                extracted['nombre_sdb'] = int(m.group(1))
            break
    
    # === PARKING ===
    if re.search(r'(?:place?|parking|garage).*?(?:au?\s+)?sous[\s-]?sol', text_lower):
        extracted['parking'] = True
        extracted['parking_sous_sol'] = True
    elif re.search(r'parking|garage|place\s+de\s+parking', text_lower):
        extracted['parking'] = True
    
    # === STANDING ===
    if 'haut standing' in text_lower or 'très haut standing' in text_lower:
        extracted['standing'] = 'Haut standing'
    elif 'standing' in text_lower:
        extracted['standing'] = 'Standing'
    
    # === CUISINE ===
    if 'cuisine bien équipée' in text_lower or 'cuisine équipée' in text_lower:
        extracted['cuisine_equipee'] = True
    
    # === CHAUFFAGE / CLIMATISATION ===
    if 'chauffé' in text_lower or 'chauffage' in text_lower:
        extracted['chauffage'] = True
    if 'climatis' in text_lower:
        extracted['climatisation'] = True
    
    # === BALCON / TERRASSE ===
    if 'balcon' in text_lower:
        extracted['balcon'] = True
    if 'terrasse' in text_lower:
        extracted['terrasse'] = True
    
    # === SALON ===
    if 'salon' in text_lower:
        extracted['salon'] = True
    
    # === RÉFÉRENCE ===
    ref_match = re.search(r'[Rr]éférence\s*(?:du\s+bien)?\s*[:\-]?\s*(\w+)', text)
    if ref_match:
        extracted['reference'] = ref_match.group(1)
    
    return extracted


def enrich_listing_with_description(listing: Dict) -> Dict:
    """
    Enrichit un listing avec les données extraites de description_complete ou description_courte.
    Ne remplace pas les valeurs existantes, complète seulement les champs vides.
    """
    desc = listing.get('description_complete') or listing.get('description_courte') or ''
    if not desc:
        return listing
    
    category = 'appartement'
    if listing.get('type_villa') or 'villa' in (listing.get('titre') or '').lower():
        category = 'villa'
    elif listing.get('type_maison') or 'maison' in (listing.get('titre') or '').lower():
        category = 'maison'
    elif listing.get('type_bureau') or 'bureau' in (listing.get('titre') or '').lower():
        category = 'bureau'
    elif listing.get('type_local') or 'local' in (listing.get('titre') or '').lower():
        category = 'locaux_com'
    
    extracted = extract_from_description(desc, category)
    
    # Mapping vers les champs du listing unifié
    mapping = {
        'type_appartement': ['type_appartement', 'type_villa', 'type_maison'],
        'etage': ['etage'],
        'quartier_extrait': ['quartier'],
        'ville_extrait': ['ville'],
        'nombre_chambres': ['nombre_chambres'],
        'nombre_sdb': ['nombre_sdb'],
    }
    
    for ext_key, target_keys in mapping.items():
        if ext_key not in extracted:
            continue
        val = extracted[ext_key]
        for tk in target_keys:
            if tk in listing and (listing[tk] is None or listing[tk] == '' or listing[tk] == 0):
                listing[tk] = val
                break
    
    # Stocker les extraits enrichis pour référence
    listing['description_extracted'] = extracted
    
    return listing


# Exemple d'utilisation
if __name__ == "__main__":
    example = """L'agence immobilière Premier Déclic vous propose à la location Un Appartement S3 Très Haut Standing au 10ème étage à jardin de Carthage se compose:
- Un salon Avec Balcon
- Deux Chambres à coucher
- Une Suite Parentale
- Une cuisine bien équipée
- Une salle de bain
- Une salle d'eau
- Une place de parking au sous sol
L'appartement est entièrement Chauffé et climatisé
Référence du bien: Ref202a"""
    
    result = extract_from_description(example, "appartement")
    print("Extraction:", result)
