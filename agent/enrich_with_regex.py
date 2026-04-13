import json
import re
from location_reference_utils import get_city_list

INPUT_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"
OUTPUT_FILE = "/opt/spark_app/data/TayaraDataRegex.json"

CITY_LIST = get_city_list()

def extract_surface(text: str):
    if not text:
        return None
    patterns = [
        r'(\d+(?:[.,]\d+)?)\s*m²',
        r'(\d+(?:[.,]\d+)?)\s*m2',
        r'superficie\s*(\d+(?:[.,]\d+)?)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
    return None

def extract_rooms(text: str):
    if not text:
        return None
    patterns = [
        r'(\d+)\s*chambres?',
        r'(\d+)\s*pi[eè]ces?',
        r'salon\s*\+\s*(\d+)\s*chambres?'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None

def extract_bathrooms(text: str):
    if not text:
        return None
    patterns = [
        r'(\d+)\s*salles?\s*de\s*bain',
        r'(\d+)\s*sdb'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None

def extract_floor(text: str):
    if not text:
        return None

    text_lower = text.lower()

    if "rdc" in text_lower or "rez de chaussée" in text_lower:
        return "RDC"

    patterns = [
        r'(\d+)[ée]me\s*[ée]tage',
        r'(\d+)\s*e\s*[ée]tage',
        r'(\d+)\s*er\s*[ée]tage',
        r'au\s*(\d+)[ée]me',
        r'situ[ée]\s*au\s*(\d+)'
    ]

    for p in patterns:
        m = re.search(p, text_lower, re.IGNORECASE)
        if m:
            return m.group(1)

    return None

def extract_transaction_type(text: str):
    if not text:
        return None
    text_lower = text.lower()
    if "à louer" in text_lower or "a louer" in text_lower or "location" in text_lower:
        return "A louer"
    if "à vendre" in text_lower or "a vendre" in text_lower or "vente" in text_lower:
        return "A vendre"
    return None

def extract_titre_foncier(text: str):
    if not text:
        return None
    if "titre foncier" in text.lower():
        return "Oui"
    return None

def extract_usage(text: str):
    if not text:
        return None
    t = text.lower()
    if "bureau" in t or "open space" in t:
        return "bureau"
    if "local commercial" in t or "commerce" in t:
        return "commerce"
    if "terrain" in t or "lot" in t:
        return "terrain"
    if "villa" in t or "maison" in t or "studio" in t or "appartement" in t:
        return "habitation"
    return None

def extract_type_bien(text: str):
    if not text:
        return None
    t = text.lower()
    mapping = {
        "villa": "villa",
        "maison": "maison",
        "studio": "studio",
        "appartement": "appartement",
        "terrain": "terrain",
        "bureau": "bureau",
        "local": "local",
        "immeuble": "immeuble",
        "ferme": "ferme"
    }
    for key, value in mapping.items():
        if key in t:
            return value
    return None

def extract_city(text: str):
    if not text:
        return None

    text_lower = text.lower()
    sorted_cities = sorted(CITY_LIST, key=len, reverse=True)

    for city in sorted_cities:
        if city.lower() in text_lower:
            return city

    return None

def build_full_text(item):
    title = item.get("title", "") or ""
    description = item.get("description", "") or ""
    location = item.get("location", "") or ""
    return f"{title} {description} {location}"

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = []

    for item in data:
        full_text = build_full_text(item)

        extracted = {
            "num_etage": extract_floor(full_text),
            "adresse_raw": None,
            "ville": extract_city(full_text),
            "quartier": None,
            "delegation": None,
            "gouvernorat": None,
            "surface_extraite": extract_surface(full_text),
            "nb_chambres_extrait": extract_rooms(full_text),
            "nb_sdb_extrait": extract_bathrooms(full_text),
            "type_bien_extrait": extract_type_bien(full_text),
            "usage_extrait": extract_usage(full_text),
            "transaction_type_extrait": extract_transaction_type(full_text),
            "titre_foncier_extrait": extract_titre_foncier(full_text),
            "source_extraction": "regex",
            "extraction_confidence": 0.5,
        }

        missing_critical = (
            extracted["ville"] is None or
            extracted["type_bien_extrait"] is None or
            extracted["usage_extrait"] is None
        )

        merged = {**item, **extracted}
        merged["needs_llm_enrichment"] = missing_critical
        enriched.append(merged)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"Regex enrichment saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()