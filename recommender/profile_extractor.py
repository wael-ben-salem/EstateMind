import re
import unicodedata


# =========================================================
# Normalisation
# =========================================================

def normalize_text(text: str) -> str:
    text = text.lower().strip()

    # enlever accents
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    # uniformiser apostrophes et séparateurs
    text = text.replace("’", "'")
    text = text.replace(",", " ")
    text = text.replace(";", " ")
    text = text.replace("/", " ")
    text = re.sub(r"\s+", " ", text)

    return text


# =========================================================
# Dictionnaires métier
# =========================================================

CONTRAT_KEYWORDS = {
    "vente": [
        "vente", "a vendre", "acheter", "achat", "buy", "for sale"
    ],
    "location": [
        "location", "a louer", "louer", "loyer", "rent", "for rent"
    ],
    "location_vacances": [
        "vacances", "location vacances", "location saisonniere",
        "saisonnier", "summer rental", "holiday rental"
    ],
    "colocation": [
        "colocation", "roommate", "shared"
    ]
}

TYPE_KEYWORDS = {
    "appartement": ["appartement", "apartment", "flat", "apt"],
    "maison": ["maison", "house"],
    "villa": ["villa"],
    "terrain": ["terrain", "land", "lot"],
    "studio": ["studio"],
    "duplex": ["duplex"],
    "bureau": ["bureau", "office"],
    "local commercial": ["local commercial", "commerce", "shop", "commercial"],
    "immeuble": ["immeuble", "building"],
    "ferme": ["ferme", "farm"],
    "garage": ["garage"],
    "bungalow": ["bungalow"],
    "appartement meuble": ["appartement meuble", "meuble", "furnished apartment"],
}

AMENITY_KEYWORDS = {
    "piscine": ["piscine", "pool"],
    "garage": ["garage"],
    "jardin": ["jardin", "garden"],
    "parking": ["parking"],
    "ascenseur": ["ascenseur", "elevator", "lift"],
    "climatisation": ["clim", "climatisation", "climatise", "air conditioning"],
    "terrasse": ["terrasse"],
    "balcon": ["balcon", "balcony"],
}

STANDING_KEYWORDS = {
    "haut_standing": ["haut standing", "luxueux", "luxe", "high standing", "premium"]
}


# =========================================================
# Utilitaires de matching
# =========================================================

def contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def extract_contrat(text: str):
    for contrat, keywords in CONTRAT_KEYWORDS.items():
        if contains_any(text, keywords):
            return contrat
    return None


def extract_type(text: str):
    for property_type, keywords in TYPE_KEYWORDS.items():
        if contains_any(text, keywords):
            return property_type
    return None


def extract_amenities(text: str):
    found = []
    for amenity, keywords in AMENITY_KEYWORDS.items():
        if contains_any(text, keywords):
            found.append(amenity)
    return found


def extract_standing(text: str):
    for standing, keywords in STANDING_KEYWORDS.items():
        if contains_any(text, keywords):
            return standing
    return None


# =========================================================
# Villes
# =========================================================

def extract_ville(text: str, df):
    if "ville" not in df.columns:
        return None

    villes = (
        df["ville"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
        .tolist()
    )

    # plus longues d'abord pour éviter "marsa" avant "la marsa"
    villes = sorted(villes, key=len, reverse=True)

    for ville in villes:
        if ville and ville in text:
            return ville
    return None


# =========================================================
# Budget
# =========================================================

def parse_number_token(token: str):
    """
    Convertit:
    - 500000
    - 500 000
    - 500k
    - 500 k
    - 500 mille
    - 1.2 million
    - 2m
    en nombre float
    """
    token = token.strip().lower()
    token = token.replace(" ", "")

    multiplier = 1

    if token.endswith("k"):
        multiplier = 1_000
        token = token[:-1]
    elif token.endswith("m"):
        multiplier = 1_000_000
        token = token[:-1]

    token = token.replace(",", ".")
    token = re.sub(r"[^\d.]", "", token)

    if token == "":
        return None

    try:
        return float(token) * multiplier
    except ValueError:
        return None


def parse_budget_phrase(value: str, unit: str | None):
    """
    value: ex "500", "1.2"
    unit: ex "k", "mille", "million", "dt"
    """
    raw = value.strip().lower().replace(",", ".")
    base = None

    try:
        base = float(raw)
    except ValueError:
        return None

    if unit is None:
        return base

    unit = unit.lower().strip()

    if unit in ["k", "mille", "mil"]:
        return base * 1_000
    if unit in ["m", "million", "millions"]:
        return base * 1_000_000

    # dt / tnd / dinars = pas de multiplication
    return base


def extract_budget(text: str):
    """
    Retourne (budget_min, budget_max)

    Gère:
    - moins de 500k
    - max 500000
    - budget max 1.2 million
    - entre 800 et 1200 dt
    - de 200000 a 400000
    - plus de 300000
    - a partir de 500 mille
    """
    text = normalize_text(text)

    number_pattern = r"(\d+(?:[.,]\d+)?)"
    unit_pattern = r"(millions|million|mille|mil|tnd|dinars|dinar|dt|k|m)?"
    # 1) Intervalle : entre X et Y
    interval_patterns = [
        rf"entre\s+{number_pattern}\s*{unit_pattern}\s+et\s+{number_pattern}\s*{unit_pattern}",
        rf"de\s+{number_pattern}\s*{unit_pattern}\s+a\s+{number_pattern}\s*{unit_pattern}",
        rf"de\s+{number_pattern}\s*{unit_pattern}\s+jusqu[ae]\s+{number_pattern}\s*{unit_pattern}",
    ]

    for pattern in interval_patterns:
        match = re.search(pattern, text)
        if match:
            n1, u1, n2, u2 = match.groups()
            b1 = parse_budget_phrase(n1, u1)
            b2 = parse_budget_phrase(n2, u2)
            if b1 is not None and b2 is not None:
                return min(b1, b2), max(b1, b2)

    # 2) Maximum
    max_patterns = [
        rf"moins de\s+{number_pattern}\s*{unit_pattern}",
        rf"max(?:imum)?\s+{number_pattern}\s*{unit_pattern}",
        rf"budget max\s+{number_pattern}\s*{unit_pattern}",
        rf"jusqu[ae]\s+{number_pattern}\s*{unit_pattern}",
        rf"pas plus de\s+{number_pattern}\s*{unit_pattern}",
    ]

    for pattern in max_patterns:
        match = re.search(pattern, text)
        if match:
            n, u = match.groups()
            budget = parse_budget_phrase(n, u)
            return None, budget

    # 3) Minimum
    min_patterns = [
        rf"plus de\s+{number_pattern}\s*{unit_pattern}",
        rf"min(?:imum)?\s+{number_pattern}\s*{unit_pattern}",
        rf"budget min\s+{number_pattern}\s*{unit_pattern}",
        rf"a partir de\s+{number_pattern}\s*{unit_pattern}",
        rf"au moins\s+{number_pattern}\s*{unit_pattern}",
    ]

    for pattern in min_patterns:
        match = re.search(pattern, text)
        if match:
            n, u = match.groups()
            budget = parse_budget_phrase(n, u)
            return budget, None

    # 4) Valeur seule explicite
    standalone_pattern = rf"{number_pattern}\s*{unit_pattern}"
    matches = re.findall(standalone_pattern, text)

    if matches:
        # on prend le plus grand nombre détecté comme budget max probable
        budgets = []
        for n, u in matches:
            budget = parse_budget_phrase(n, u)
            if budget is not None:
                budgets.append(budget)

        if budgets:
            return None, max(budgets)

    return None, None


# =========================================================
# Pièces
# =========================================================

def extract_pieces(text: str):
    text = normalize_text(text)

    patterns = [
        r"(\d+)\s*pieces?",
        r"(\d+)\s*chambres?",
        r"s\+?\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


# =========================================================
# Surface
# =========================================================

def extract_surface(text: str):
    text = normalize_text(text)

    number_pattern = r"(\d+(?:[.,]\d+)?)"

    # intervalle
    interval_patterns = [
        rf"entre\s+{number_pattern}\s*(?:m2|m²)\s+et\s+{number_pattern}\s*(?:m2|m²)?",
        rf"de\s+{number_pattern}\s*(?:m2|m²)\s+a\s+{number_pattern}\s*(?:m2|m²)?",
    ]

    for pattern in interval_patterns:
        match = re.search(pattern, text)
        if match:
            s1 = float(match.group(1).replace(",", "."))
            s2 = float(match.group(2).replace(",", "."))
            return min(s1, s2), max(s1, s2)

    # minimum
    min_patterns = [
        rf"plus de\s+{number_pattern}\s*(?:m2|m²)",
        rf"au moins\s+{number_pattern}\s*(?:m2|m²)",
        rf"surface min\s+{number_pattern}\s*(?:m2|m²)?",
    ]

    for pattern in min_patterns:
        match = re.search(pattern, text)
        if match:
            s = float(match.group(1).replace(",", "."))
            return s, None

    # maximum
    max_patterns = [
        rf"moins de\s+{number_pattern}\s*(?:m2|m²)",
        rf"surface max\s+{number_pattern}\s*(?:m2|m²)?",
    ]

    for pattern in max_patterns:
        match = re.search(pattern, text)
        if match:
            s = float(match.group(1).replace(",", "."))
            return None, s

    # valeur simple
    simple_match = re.search(rf"{number_pattern}\s*(?:m2|m²)", text)
    if simple_match:
        s = float(simple_match.group(1).replace(",", "."))
        return s, None

    return None, None


# =========================================================
# Fonction principale
# =========================================================
def infer_contrat(profile: dict, text: str):
    """
    Déduit le contrat si l'utilisateur ne l'a pas précisé explicitement.
    """
    # Si contrat déjà détecté explicitement, on le garde
    if profile.get("contrat") is not None:
        return profile["contrat"]

    budget_max = profile.get("budget_max")
    budget_min = profile.get("budget_min")
    property_type = profile.get("type")

    # -------------------------
    # Indices textuels directs
    # -------------------------
    if any(term in text for term in ["par mois", "mensuel", "loyer"]):
        return "location"

    if any(term in text for term in ["par nuit", "par semaine", "vacances", "saisonnier", "location saisonniere"]):
        return "location_vacances"

    # -------------------------
    # Heuristiques budget
    # -------------------------
    # Budget faible -> location probable
    if budget_max is not None and budget_max <= 10000:
        return "location"

    # Budget élevé -> vente probable
    if budget_max is not None and budget_max >= 50000:
        return "vente"

    if budget_min is not None and budget_min >= 50000:
        return "vente"

    # -------------------------
    # Heuristiques type + budget
    # -------------------------
    if property_type == "terrain":
        # un terrain avec budget significatif est presque toujours une vente
        if budget_max is not None and budget_max >= 20000:
            return "vente"
        if budget_min is not None and budget_min >= 20000:
            return "vente"

    # Si on ne sait pas, on laisse None
    return None

def extract_user_profile(query: str, df):
    text = normalize_text(query)

    budget_min, budget_max = extract_budget(text)
    surface_min, surface_max = extract_surface(text)

    profile = {
        "contrat": extract_contrat(text),
        "type": extract_type(text),
        "ville": extract_ville(text, df),
        "budget_min": budget_min,
        "budget_max": budget_max,
        "pieces": extract_pieces(text),
        "surface_min": surface_min,
        "surface_max": surface_max,
        "amenities": extract_amenities(text),
        "standing": extract_standing(text),
    }

    # Déduction intelligente du contrat si absent
    profile["contrat"] = infer_contrat(profile, text)

    return profile

    return profile