from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import re
import unicodedata


# =========================================================
# OUTILS
# =========================================================

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"\s+", " ", text)
    return text


# =========================================================
# CONFIG
# =========================================================

SALE_KEYWORDS = {
    "vente", "vendre", "a vendre", "à vendre", "achat", "acheter", "for sale"
}

RENT_KEYWORDS = {
    "location", "louer", "a louer", "à louer", "loyer", "rent", "monthly", "/mois", "par mois"
}

VACATION_RENT_KEYWORDS = {
    "vacances", "location vacances", "estival", "estivale", "saisonnier",
    "par nuit", "/nuit", "par jour", "/jour", "weekend"
}

PROPERTY_TYPE_SYNONYMS = {
    "appartement": {"appartement", "appart", "apt", "flat"},
    "maison": {"maison", "villa", "house", "home"},
    "studio": {"studio", "s0"},
    "terrain": {"terrain", "lot", "parcelle"},
    "bureau": {"bureau", "office"},
    "local commercial": {"local commercial", "commerce", "magasin", "shop"},
}

CITY_ALIASES = {
    "tunis": {"tunis"},
    "ariana": {"ariana"},
    "nabeul": {"nabeul"},
    "hammamet": {"hammamet"},
    "sousse": {"sousse"},
    "sfax": {"sfax"},
    "la marsa": {"la marsa", "marsa"},
    "le kram": {"le kram", "kram"},
    "carthage": {"carthage"},
}

AMENITY_KEYWORDS = {
    "piscine": {"piscine", "pool"},
    "jardin": {"jardin", "garden"},
    "garage": {"garage"},
    "ascenseur": {"ascenseur", "elevator"},
    "parking": {"parking"},
    "terrasse": {"terrasse"},
    "balcon": {"balcon"},
    "meuble": {"meuble", "meublee", "meublé", "meublée", "furnished"},
}


# =========================================================
# MODELE DE SORTIE
# =========================================================

@dataclass
class QueryUnderstandingResult:
    intent: str = "search_property"
    contract: Optional[str] = None
    city: Optional[str] = None
    property_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    rooms: Optional[int] = None
    min_surface: Optional[float] = None
    amenities: List[str] = None
    preferences: List[str] = None
    confidence: float = 0.85

    def to_dict(self):
        return asdict(self)


# =========================================================
# EXTRACTION
# =========================================================

def extract_budget_range_from_query(query: str) -> Tuple[Optional[float], Optional[float]]:
    q = normalize_text(query)

    m = re.search(r"entre\s+(\d+(?:\.\d+)?)\s+et\s+(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1)), float(m.group(2))

    m = re.search(r"de\s+(\d+(?:\.\d+)?)\s+(?:a|à)\s+(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1)), float(m.group(2))

    return None, None


def extract_budget_from_query(query: str) -> Optional[float]:
    q = normalize_text(query)

    # 150 md
    m = re.search(r"(\d+(?:\.\d+)?)\s*md\b", q)
    if m:
        return float(m.group(1)) * 1000

    # 2 million / 2 millions
    m = re.search(r"(\d+(?:\.\d+)?)\s*(million|millions)\b", q)
    if m:
        return float(m.group(1)) * 1000

    # 1200 dt / 1200 tnd / 1200 dinars
    m = re.search(r"(\d+(?:\.\d+)?)\s*(dt|tnd|dinar|dinars)\b", q)
    if m:
        return float(m.group(1))

    # max 1200 / maximum 1200 / moins de 1200
    m = re.search(r"(max|maximum|jusqu a|jusqu'a|moins de|pas plus de)\s*(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(2))

    # budget 300000 / budget de 300000
    m = re.search(r"budget\s*(?:de\s*)?(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1))

    return None

def extract_city_from_query(query: str) -> Optional[str]:
    q = normalize_text(query)

    for canonical, aliases in CITY_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", q):
                return canonical
    return None


def extract_property_type_from_query(query: str) -> Optional[str]:
    q = normalize_text(query)

    for canonical, aliases in PROPERTY_TYPE_SYNONYMS.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", q):
                return canonical
    return None


def extract_rooms_from_query(query: str) -> Optional[int]:
    q = normalize_text(query)

    m = re.search(r"(\d+)\s*(chambres|chambre|pieces|piece)", q)
    if m:
        return int(m.group(1))

    m = re.search(r"s\s*\+\s*(\d+)", q)
    if m:
        return int(m.group(1)) + 1

    return None


def extract_min_surface_from_query(query: str) -> Optional[float]:
    q = normalize_text(query)

    m = re.search(r"(\d+(?:\.\d+)?)\s*(m2|m\^2|metre|metres|metres carres|metres carre)", q)
    if m:
        return float(m.group(1))

    return None


def extract_amenities(query: str) -> List[str]:
    q = normalize_text(query)
    found = []

    for canonical, keywords in AMENITY_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            found.append(canonical)

    return found


def extract_preferences(query: str) -> List[str]:
    q = normalize_text(query)
    prefs = []

    if "vacances" in q or "estival" in q or "saisonnier" in q:
        prefs.append("vacation")
    if "petit budget" in q or "pas cher" in q:
        prefs.append("small_budget")
    if "familial" in q or "famille" in q:
        prefs.append("family")
    if "proche de la mer" in q or "pres de la mer" in q or "bord de mer" in q:
        prefs.append("near_sea")

    return prefs


def infer_contract_from_query(query: str, property_type: Optional[str],
                              budget_min: Optional[float], budget_max: Optional[float]) -> Optional[str]:
    q = normalize_text(query)

    if any(kw in q for kw in VACATION_RENT_KEYWORDS):
        return "location_vacances"

    if any(kw in q for kw in SALE_KEYWORDS):
        return "vente"

    if any(kw in q for kw in RENT_KEYWORDS):
        return "location"

    price_ref = budget_max if budget_max is not None else budget_min

    if price_ref is not None:
        if price_ref <= 10000:
            return "location"
        if price_ref >= 50000:
            return "vente"

    if property_type == "terrain":
        return "vente"

    return None


def understand_query(query: str) -> QueryUnderstandingResult:
    budget_min, budget_max = extract_budget_range_from_query(query)

    if budget_max is None:
        single_budget = extract_budget_from_query(query)
        if single_budget is not None:
            budget_max = single_budget

    property_type = extract_property_type_from_query(query)

    contract = infer_contract_from_query(
        query=query,
        property_type=property_type,
        budget_min=budget_min,
        budget_max=budget_max
    )

    return QueryUnderstandingResult(
        intent="search_property",
        contract=contract,
        city=extract_city_from_query(query),
        property_type=property_type,
        budget_min=budget_min,
        budget_max=budget_max,
        rooms=extract_rooms_from_query(query),
        min_surface=extract_min_surface_from_query(query),
        amenities=extract_amenities(query),
        preferences=extract_preferences(query),
        confidence=0.88
    )