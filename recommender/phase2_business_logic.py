import re
import math
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# =========================================================
# 1) CONFIG MÉTIER
# =========================================================

SALE_KEYWORDS = {
    "vente", "vendre", "a vendre", "à vendre", "achat", "acheter",
    "for sale", "sale", "vendu", "titre bleu"
}

RENT_KEYWORDS = {
    "location", "louer", "a louer", "à louer", "locatif", "loyer",
    "par mois", "/mois", "mensuel", "monthly", "rent", "rental"
}

VACATION_RENT_KEYWORDS = {
    "vacances", "location vacances", "location estivale", "estivale",
    "saisonnier", "saisonniere", "saisonnière", "par nuit", "/nuit",
    "nuit", "par jour", "/jour", "journee", "journée", "weekend",
    "pieds dans l'eau", "bord de mer vacances"
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

# Bornes métier simples et défendables
PRICE_RULES = {
    "vente": {
        "min": 20000,
        "max": 50000000,
    },
    "location": {
        "min": 100,
        "max": 50000,
    },
    "location_vacances": {
        "min": 50,
        "max": 20000,
    },
    "unknown": {
        "min": 0,
        "max": 1e12,
    },
}


# =========================================================
# 2) OUTILS DE NORMALISATION
# =========================================================
def extract_budget_range_from_query(query: str) -> Tuple[Optional[float], Optional[float]]:
    q = normalize_text(query)

    # entre 200000 et 400000
    m = re.search(r"entre\s+(\d+(?:\.\d+)?)\s+et\s+(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1)), float(m.group(2))

    # de 200000 a 400000
    m = re.search(r"de\s+(\d+(?:\.\d+)?)\s+(?:a|à)\s+(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1)), float(m.group(2))

    return None, None 

def normalize_text(text: Any) -> str:
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()

    # enlever accents
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # nettoyer html minimal
    text = re.sub(r"<[^>]+>", " ", text)

    # espaces
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def canonicalize_city(city: Any) -> Optional[str]:
    city_norm = normalize_text(city)
    if not city_norm:
        return None

    for canonical, aliases in CITY_ALIASES.items():
        if city_norm in aliases:
            return canonical

    return city_norm


def canonicalize_property_type(value: Any) -> Optional[str]:
    value_norm = normalize_text(value)
    if not value_norm:
        return None

    for canonical, aliases in PROPERTY_TYPE_SYNONYMS.items():
        if value_norm in aliases:
            return canonical

    for canonical, aliases in PROPERTY_TYPE_SYNONYMS.items():
        if any(alias in value_norm for alias in aliases):
            return canonical

    return value_norm


def safe_float(value: Any) -> Optional[float]:
    if pd.isna(value):
        return None

    if isinstance(value, (int, float, np.integer, np.floating)):
        if np.isfinite(value):
            return float(value)
        return None

    text = normalize_text(value)
    if not text:
        return None

    text = text.replace(",", ".")
    match = re.findall(r"\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match[0])
    except Exception:
        return None


def extract_budget_from_query(query: str) -> Optional[float]:
    q = normalize_text(query)

    # exemples: 1200 dt, 350000, budget 150 md
    md_match = re.search(r"(\d+(?:\.\d+)?)\s*md\b", q)
    if md_match:
        return float(md_match.group(1)) * 1000

    million_match = re.search(r"(\d+(?:\.\d+)?)\s*(million|millions)\b", q)
    if million_match:
        return float(million_match.group(1)) * 1000

    dt_match = re.search(r"(\d+(?:\.\d+)?)\s*(dt|tnd|dinar|dinars)\b", q)
    if dt_match:
        return float(dt_match.group(1))

    generic_budget = re.search(r"(budget|max|maximum|jusqu a|jusqu'a)\s*(de)?\s*(\d+(?:\.\d+)?)", q)
    if generic_budget:
        return float(generic_budget.group(3))
    m = re.search(r"budget\s*(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1))
    

    return None


def extract_min_surface_from_query(query: str) -> Optional[float]:
    q = normalize_text(query)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(m2|m\^2|metre|metres|metres carres|metres carre)", q)
    if m:
        return float(m.group(1))
    return None


def extract_rooms_from_query(query: str) -> Optional[int]:
    q = normalize_text(query)

    # 2 chambres
    m = re.search(r"(\d+)\s*(chambres|chambre|pieces|piece)", q)
    if m:
        return int(m.group(1))

    # s+2
    m = re.search(r"s\s*\+\s*(\d+)", q)
    if m:
        return int(m.group(1)) + 1

    return None


# =========================================================
# 3) CONTRAT : DÉTECTION ET NORMALISATION
# =========================================================

def infer_contract(raw_contract: Any, title: Any, description: Any) -> str:
    contract_norm = normalize_text(raw_contract)
    title_norm = normalize_text(title)
    desc_norm = normalize_text(description)

    combined = f"{contract_norm} {title_norm} {desc_norm}".strip()

    sale_hits = sum(1 for kw in SALE_KEYWORDS if kw in combined)
    rent_hits = sum(1 for kw in RENT_KEYWORDS if kw in combined)

    if "vente" in contract_norm:
        return "vente"
    if "location" in contract_norm:
        return "location"

    if sale_hits > rent_hits and sale_hits > 0:
        return "vente"
    if rent_hits > sale_hits and rent_hits > 0:
        return "location"

    return "unknown"


def infer_contract_from_query(query: str, property_type: Optional[str] = None,
                              budget_min: Optional[float] = None,
                              budget_max: Optional[float] = None) -> Optional[str]:
    q = normalize_text(query)

    vacation_hits = sum(1 for kw in VACATION_RENT_KEYWORDS if kw in q)
    rent_hits = sum(1 for kw in RENT_KEYWORDS if kw in q)
    sale_hits = sum(1 for kw in SALE_KEYWORDS if kw in q)

    # 1. Cas explicite vacances
    if vacation_hits > 0:
        return "location_vacances"

    # 2. Cas explicite vente/location
    if sale_hits > rent_hits and sale_hits > 0:
        return "vente"
    if rent_hits > sale_hits and rent_hits > 0:
        return "location"

    # 3. Heuristique budget
    price_ref = budget_max if budget_max is not None else budget_min

    if price_ref is not None:
        # prix faibles => plutôt location
        if price_ref <= 10000:
            if "villa" in q or "maison" in q:
                # une villa à 5000 peut être location classique ou vacances
                if any(x in q for x in ["vacances", "nuit", "jour", "semaine", "weekend"]):
                    return "location_vacances"
                return "location"
            return "location"

        # prix élevés => plutôt vente
        if price_ref >= 50000:
            return "vente"

    # 4. Heuristique par type
    if property_type == "terrain":
        return "vente"

    return None


# =========================================================
# 4) PRIX : NETTOYAGE ET CONTRÔLES MÉTIER
# =========================================================

def normalize_price(value: Any) -> Optional[float]:
    """
    Nettoyage simple du prix.
    On garde volontairement une logique prudente.
    """
    price = safe_float(value)
    if price is None:
        return None

    # Cas simple : prix négatif ou nul
    if price <= 0:
        return None

    return price


def is_price_suspect(price: Optional[float], contract: str) -> bool:
    if price is None:
        return True

    rules = PRICE_RULES.get(contract, PRICE_RULES["unknown"])
    return not (rules["min"] <= price <= rules["max"])


def compute_price_per_m2(price: Optional[float], surface: Optional[float], contract: str) -> Optional[float]:
    if contract != "vente":
        return None
    if price is None or surface is None or surface <= 0:
        return None
    return price / surface


def format_price(price: Optional[float], contract: str) -> str:
    if price is None:
        return "Prix non disponible"

    if contract == "location":
        return f"{int(round(price)):,} TND / mois".replace(",", " ")

    if contract == "location_vacances":
        return f"{int(round(price)):,} TND / nuit".replace(",", " ")

    if contract == "vente":
        return f"{int(round(price)):,} TND".replace(",", " ")

    return f"{int(round(price)):,} TND".replace(",", " ")


# =========================================================
# 5) EXTRACTION DES FILTRES DEPUIS LE PROMPT
# =========================================================

@dataclass
class UserIntent:
    contract: Optional[str] = None
    city: Optional[str] = None
    property_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    rooms: Optional[int] = None
    min_surface: Optional[float] = None
    amenities: Optional[List[str]] = None
    preferences: Optional[List[str]] = None

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


def parse_user_intent(query: str) -> UserIntent:
    budget_min, budget_max = extract_budget_range_from_query(query)

    if budget_max is None:
        single_budget = extract_budget_from_query(query)
        if single_budget is not None:
            budget_max = single_budget

    property_type = extract_property_type_from_query(query)

    contract = infer_contract_from_query(
        query,
        property_type=property_type,
        budget_min=budget_min,
        budget_max=budget_max
    )

    return UserIntent(
        contract=contract,
        city=extract_city_from_query(query),
        property_type=property_type,
        budget_min=budget_min,
        budget_max=budget_max,
        rooms=extract_rooms_from_query(query),
        min_surface=extract_min_surface_from_query(query),
        amenities=[],
        preferences=[],
    )


# =========================================================
# 6) PRÉPARATION DATAFRAME
# =========================================================

def prepare_phase2_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Colonnes textuelles attendues
    for col in ["contrat", "titre", "description", "ville", "type"]:
        if col not in df.columns:
            df[col] = None

    if "surface" not in df.columns:
        df["surface"] = None

    if "prix" not in df.columns:
        df["prix"] = None

    if "pieces" not in df.columns:
        df["pieces"] = None

    df["contract_clean"] = df.apply(
        lambda row: infer_contract(
            row.get("contrat"),
            row.get("titre"),
            row.get("description")
        ),
        axis=1
    )

    df["price_clean"] = df["prix"].apply(normalize_price)
    df["surface_clean"] = df["surface"].apply(safe_float)
    df["pieces_clean"] = df["pieces"].apply(
        lambda x: int(x) if pd.notna(x) and str(x).strip() != "" else None
    )
    df["city_clean"] = df["ville"].apply(canonicalize_city)

    # 1) d'abord normaliser le type brut
    df["type_clean"] = df["type"].apply(canonicalize_property_type)

    # 2) ensuite corriger/enrichir avec le texte
    df["type_clean"] = df.apply(infer_type_from_text, axis=1)

    df["price_suspect"] = df.apply(
        lambda row: is_price_suspect(row["price_clean"], row["contract_clean"]),
        axis=1
    )

    df["price_per_m2"] = df.apply(
        lambda row: compute_price_per_m2(
            row["price_clean"],
            row["surface_clean"],
            row["contract_clean"]
        ),
        axis=1
    )

    return df


# =========================================================
# 7) FILTRES MÉTIER
# =========================================================

def apply_business_filters(df: pd.DataFrame, intent: UserIntent) -> pd.DataFrame:

    # fallback vacances -> location si aucune annonce vacances n'existe
    effective_contract = intent.contract
    if effective_contract == "location_vacances":
        temp = df[df["contract_clean"] == "location_vacances"]
        if temp.empty:
            effective_contract = "location"

        # =========================
    # NIVEAU 1 : STRICT
    # =========================
    filtered = df.copy()

    if effective_contract:
        if effective_contract == "location_vacances":
            filtered = filtered[
                filtered["contract_clean"].isin(["location_vacances", "location"])
            ]
        else:
            filtered = filtered[filtered["contract_clean"] == effective_contract]
    if intent.city:
        filtered = filtered[filtered["city_clean"] == intent.city]

    if intent.property_type:
        filtered = filtered[filtered["type_clean"] == intent.property_type]

    if intent.budget_min is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] >= intent.budget_min)
        ]

    if intent.budget_max is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] <= intent.budget_max)
        ]

    # on ne filtre plus la surface ici ; on la laisse au ranking

    if not filtered.empty:
        return filtered

    # =========================
    # NIVEAU 2 : RELAX TYPE
    # =========================
    filtered = df.copy()

    if effective_contract:
        filtered = filtered[filtered["contract_clean"] == effective_contract]

    if intent.city:
        filtered = filtered[filtered["city_clean"] == intent.city]

    if intent.budget_min is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] >= intent.budget_min)
        ]

    if intent.budget_max is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] <= intent.budget_max)
        ]

    if not filtered.empty:
        return filtered

    # =========================
    # NIVEAU 3 : RELAX CITY
    # =========================
    filtered = df.copy()

    if effective_contract:
        filtered = filtered[filtered["contract_clean"] == effective_contract]

    if intent.budget_min is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] >= intent.budget_min)
        ]

    if intent.budget_max is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] <= intent.budget_max)
        ]

    if not filtered.empty:
        return filtered

    # =========================
    # NIVEAU 4 : RELAX CONTRACT
    # =========================
    filtered = df.copy()

    if intent.budget_min is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] >= intent.budget_min)
        ]

    if intent.budget_max is not None:
        filtered = filtered[
            filtered["price_clean"].notna() &
            (filtered["price_clean"] <= intent.budget_max)
        ]

    return filtered
def infer_type_from_text(row):
    text = normalize_text(str(row.get("titre", "")) + " " + str(row.get("description", "")))

    
    if "studio" in text:
        return "studio"
    if "appartement" in text or "appart" in text:
        return "appartement"
    if "villa" in text or "maison" in text:
        return "maison"
    
    if "terrain" in text and "villa" not in text and "maison" not in text:
        return "terrain"

    return row.get("type_clean")
# =========================================================
# 8) RANKING EXPLICABLE
# =========================================================

def budget_score(price: Optional[float], budget_max: Optional[float]) -> float:
    if budget_max is None:
        return 0.5
    if price is None:
        return 0.0
    if price > budget_max:
        return 0.0

    ratio = price / budget_max
    # plus c'est proche sans dépasser, mieux c'est
    return max(0.0, 1.0 - abs(0.85 - ratio))


def room_score(pieces: Optional[int], requested: Optional[int]) -> float:
    if requested is None:
        return 0.5
    if pieces is None:
        return 0.0
    if pieces < requested:
        return 0.0
    if pieces == requested:
        return 1.0
    return max(0.6, 1.0 - 0.1 * (pieces - requested))


def surface_score(surface: Optional[float], requested_min: Optional[float]) -> float:
    if requested_min is None:
        return 0.5

    if surface is None:
        return 0.0

    if surface < requested_min:
        return -1.0

    ratio = surface / requested_min
    if ratio <= 1.2:
        return 1.0
    if ratio <= 1.5:
        return 0.9
    return 0.75


def type_score(actual_type, requested_type):
    if requested_type is None:
        return 0.5

    if actual_type is None:
        return 0.0

    if actual_type == requested_type:
        return 1.0

    # pénalité mais pas élimination
    return 0.3
def detect_piscine(row):
    text = normalize_text(str(row.get("titre", "")) + " " + str(row.get("description", "")))
    return "piscine" in text


def city_score(actual_city: Optional[str], requested_city: Optional[str]) -> float:
    if requested_city is None:
        return 0.5
    if actual_city is None:
        return 0.0
    return 1.0 if actual_city == requested_city else 0.0


def contract_score(actual_contract: str, requested_contract: Optional[str]) -> float:
    if requested_contract is None:
        return 0.5
    if requested_contract == "location_vacances":
        if actual_contract == "location_vacances":
            return 1.0
        if actual_contract == "location":
            return 0.8
        return 0.0

    return 1.0 if actual_contract == requested_contract else 0.0    


def amenity_columns(df: pd.DataFrame) -> List[str]:
    return [col for col in df.columns if col.startswith("has_")]


def amenity_score(row: pd.Series) -> float:
    amen_cols = amenity_columns(pd.DataFrame([row]))
    if not amen_cols:
        return 0.5

    vals = []
    for c in amen_cols:
        v = row.get(c)
        if pd.notna(v):
            vals.append(float(v))

    if not vals:
        return 0.5

    return min(1.0, sum(vals) / max(1, len(vals)) + 0.3)
def violates_critical_constraints(row: pd.Series, intent: UserIntent) -> bool:
    """
    Retourne True si le bien viole un critère critique demandé par l'utilisateur.
    Pour l’instant, on considère critiques :
    - surface minimale
    - type demandé
    """

    # 1. Surface minimale
    if intent.min_surface is not None:
        surface = row.get("surface_clean")
        if surface is None or pd.isna(surface) or surface < intent.min_surface:
            return True

    # 2. Type demandé
    if intent.property_type is not None:
        actual_type = row.get("type_clean")
        if actual_type != intent.property_type:
            return True

    return False
def relax_intent_for_alternatives(intent: UserIntent) -> UserIntent:
    """
    Construit une version plus souple de l'intent.
    On garde les contraintes les plus structurantes :
    - contrat
    - ville
    - budget
    On relâche les contraintes secondaires :
    - type
    - surface
    """

    return UserIntent(
        contract=intent.contract,
        city=intent.city,
        property_type=None,
        budget_min=intent.budget_min,
        budget_max=intent.budget_max,
        rooms=intent.rooms,
        min_surface=None,
        amenities=intent.amenities or [],
        preferences=intent.preferences or [],
    )
def build_global_explanation(intent: UserIntent, used_relaxation: bool) -> str:
    parts = []

    if intent.contract:
        parts.append(f"contrat = {intent.contract}")
    if intent.city:
        parts.append(f"ville = {intent.city}")
    if intent.property_type:
        parts.append(f"type = {intent.property_type}")
    if intent.budget_max is not None:
        parts.append(f"budget max = {int(intent.budget_max)} TND")
    if intent.min_surface is not None:
        parts.append(f"surface min = {int(intent.min_surface)} m²")

    criteria_text = ", ".join(parts) if parts else "critères généraux"

    if used_relaxation:
        return (
            f"Aucun bien ne correspond strictement à tous les critères demandés ({criteria_text}). "
            f"Le système a donc proposé les alternatives les plus proches en conservant les contraintes majeures."
        )

    return f"Les résultats ont été sélectionnés selon les critères demandés ({criteria_text})."
def get_relaxed_criteria(original_intent: UserIntent, relaxed_intent: UserIntent) -> List[str]:
    relaxed = []

    if original_intent.property_type is not None and relaxed_intent.property_type is None:
        relaxed.append("type")

    if original_intent.min_surface is not None and relaxed_intent.min_surface is None:
        relaxed.append("surface")

    return relaxed

def recommend_properties_from_understanding(
    df: pd.DataFrame,
    understanding: Dict[str, Any],
    top_k: int = 5
) -> Dict[str, Any]:

    prepared = prepare_phase2_dataframe(df)

    intent = UserIntent(
        contract=understanding.get("contract"),
        city=understanding.get("city"),
        property_type=understanding.get("property_type"),
        budget_min=understanding.get("budget_min"),
        budget_max=understanding.get("budget_max"),
        rooms=understanding.get("rooms"),
        min_surface=understanding.get("min_surface"),
        amenities=understanding.get("amenities", []),
        preferences=understanding.get("preferences", []),
    )

    # =========================
    # 1. Recherche stricte
    # =========================
    filtered = apply_business_filters(prepared, intent)
    ranked = rank_listings(filtered, intent, top_k=top_k)

    used_relaxation = False
    message = None

    # =========================
    # 2. Déclencher relaxation intelligente si besoin
    # =========================
    should_relax = False
    
    if ranked.empty:
        should_relax = True
    elif len(ranked) < 3:
        top_row = ranked.iloc[0]
        if violates_critical_constraints(top_row, intent):
            should_relax = True

    if should_relax:
        relaxed_intent = relax_intent_for_alternatives(intent)
        filtered_relaxed = apply_business_filters(prepared, relaxed_intent)
        ranked_relaxed = rank_listings(filtered_relaxed, relaxed_intent, top_k=top_k)

        if not ranked_relaxed.empty:
            ranked = ranked_relaxed
            filtered = filtered_relaxed
            used_relaxation = True
            message = (
                "Aucun bien ne correspond strictement à tous les critères. "
                "Voici les alternatives les plus proches selon la ville, le budget et le contrat."
            )

    relaxed_criteria = []
    if used_relaxation:
        relaxed_criteria = get_relaxed_criteria(intent, relaxed_intent)

    global_explanation = build_global_explanation(intent, used_relaxation)

    results = [build_result_card(row, intent) for _, row in ranked.iterrows()]

    return {
        "intent": understanding,
        "total_after_filters": int(len(filtered)),
        "used_relaxation": used_relaxation,
        "message": message,
        "global_explanation": global_explanation,
        "relaxed_criteria": relaxed_criteria,
        "results": results,
    }
def listing_text(row: pd.Series) -> str:
    return normalize_text(
        str(row.get("titre", "")) + " " + str(row.get("description", ""))
    )


def amenity_match_score(row: pd.Series, intent: UserIntent) -> float:
    requested = intent.amenities or []
    if not requested:
        return 0.5

    text = listing_text(row)
    matches = 0

    for amenity in requested:
        if amenity in text:
            matches += 1

    return matches / len(requested)


def preference_score(row: pd.Series, intent: UserIntent) -> float:
    prefs = intent.preferences or []
    if not prefs:
        return 0.5

    text = listing_text(row)
    score = 0.0
    count = 0

    for pref in prefs:
        count += 1

        if pref == "vacation":
            if any(k in text for k in ["vacances", "estival", "saisonnier", "bord de mer", "plage"]):
                score += 1.0
        elif pref == "small_budget":
            price = row.get("price_clean")
            if price is not None and pd.notna(price):
                if intent.budget_max is not None and price <= intent.budget_max * 0.9:
                    score += 1.0
                elif intent.budget_max is None:
                    score += 0.5
        elif pref == "family":
            pieces = row.get("pieces_clean")
            surface = row.get("surface_clean")
            if (pieces is not None and pieces >= 3) or (surface is not None and surface >= 120):
                score += 1.0
        elif pref == "near_sea":
            if any(k in text for k in ["mer", "plage", "bord de mer", "pieds dans l'eau"]):
                score += 1.0
        else:
            score += 0.5

    return score / count if count > 0 else 0.5

def compute_listing_score(row: pd.Series, intent: UserIntent) -> Tuple[float, Dict[str, float]]:
    scores = {
        "contract": contract_score(row["contract_clean"], intent.contract),
        "city": city_score(row["city_clean"], intent.city),
        "type": type_score(row["type_clean"], intent.property_type),
        "budget": budget_score(row["price_clean"], intent.budget_max),
        "rooms": room_score(row["pieces_clean"], intent.rooms),
        "surface": surface_score(row["surface_clean"], intent.min_surface),
        "amenities": amenity_match_score(row, intent),
        "preferences": preference_score(row, intent),
        "piscine": piscine_score(row, intent),
        "data_quality": 0.0 if row["price_suspect"] else 1.0,
    }

    weights = {
        "contract": 0.22,
        "city": 0.18,
        "type": 0.20,
        "budget": 0.18,
        "rooms": 0.06,
        "surface": 0.12,
        "amenities": 0.08,
        "preferences": 0.08,
        "piscine": 0.05,
        "data_quality": 0.03,
    }

    total = sum(scores[k] * weights[k] for k in scores)
    return total, scores

def rank_listings(df: pd.DataFrame, intent: UserIntent, top_k: int = 10) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    ranked = df.copy()

    global_scores = []
    explanations = []

    for _, row in ranked.iterrows():
        total, parts = compute_listing_score(row, intent)
        global_scores.append(total)
        explanations.append(parts)

    ranked["ranking_score"] = global_scores
    ranked["score_breakdown"] = explanations

    ranked = ranked.sort_values(by="ranking_score", ascending=False).head(top_k).copy()
    return ranked

def piscine_score(row, intent):
    if not intent.amenities or "piscine" not in intent.amenities:
        return 0.5

    text = normalize_text(str(row.get("titre", "")) + " " + str(row.get("description", "")))

    if "piscine" in text:
        return 1.0

    return 0.0
# =========================================================
# 9) SORTIE CHATBOT
# =========================================================
def build_result_explanation(row: pd.Series, breakdown: Dict[str, float], intent: UserIntent) -> str:
    matched = []
    missing = []

    if breakdown.get("contract", 0) >= 1:
        matched.append("le contrat")
    else:
        missing.append("le contrat")

    if breakdown.get("city", 0) >= 1:
        matched.append("la ville")
    else:
        missing.append("la ville")

    if breakdown.get("type", 0) >= 1:
        matched.append("le type de bien")
    elif intent.property_type is not None:
        missing.append("le type de bien")

    if breakdown.get("budget", 0) >= 0.7:
        matched.append("le budget")
    elif intent.budget_max is not None:
        missing.append("le budget")

    if breakdown.get("surface", 0) >= 0.9:
        matched.append("la surface")
    elif intent.min_surface is not None:
        missing.append("la surface")

    if breakdown.get("piscine", 0) >= 1:
        matched.append("la piscine")
    elif intent.amenities and "piscine" in intent.amenities:
        missing.append("la piscine")

    if matched:
        explanation = "Ce bien respecte bien " + ", ".join(matched)
    else:
        explanation = "Ce bien constitue un compromis global acceptable"

    if missing:
        explanation += ". En revanche, il ne respecte pas totalement " + ", ".join(missing)

    # Ajouter les amenities réellement détectées
    requested_amenities = intent.amenities or []
    if requested_amenities:
        text = listing_text(row)
        found = [a for a in requested_amenities if a in text]
        if found:
            explanation += ". Il inclut également : " + ", ".join(found)

    # Ajouter les préférences implicites
    if intent.preferences:
        matched_prefs = []
        if breakdown.get("preferences", 0) >= 0.8:
            matched_prefs.append("préférences implicites")
        if matched_prefs:
            explanation += ". Il est aussi cohérent avec vos préférences implicites"
        if "family" in intent.preferences:
            pieces = row.get("pieces_clean")
            surface = row.get("surface_clean")

            if (pieces is not None and pieces >= 3) or (surface is not None and surface >= 120):
                explanation += ". Ce bien est adapté à un usage familial"    
        if "near_sea" in intent.preferences:
            text = listing_text(row)
            if any(k in text for k in ["mer", "plage", "bord de mer"]):
                explanation += ". Il est situé à proximité de la mer"        

    return explanation + "."

def build_result_card(row: pd.Series, intent: Optional[UserIntent] = None) -> Dict[str, Any]:
    breakdown = row.get("score_breakdown", {})

    reasons = []

    if breakdown.get("contract", 0) >= 1:
        reasons.append("contrat conforme")
    if breakdown.get("city", 0) >= 1:
        reasons.append("ville conforme")
    if breakdown.get("type", 0) >= 1:
        reasons.append("type conforme")
    if breakdown.get("budget", 0) >= 0.7:
        reasons.append("dans le budget")
    if breakdown.get("rooms", 0) >= 0.9:
        reasons.append("nombre de pièces adapté")
    if breakdown.get("surface", 0) >= 0.9:
        reasons.append("surface adaptée")

    if not reasons:
        reasons.append("bon compromis global")

    explanation = None
    if intent is not None:
        explanation = build_result_explanation(row, breakdown, intent)

    return {
        "title": row.get("titre"),
        "city": row.get("city_clean"),
        "property_type": row.get("type_clean"),
        "contract": row.get("contract_clean"),
        "price": format_price(row.get("price_clean"), row.get("contract_clean")),
        "surface": row.get("surface_clean"),
        "rooms": row.get("pieces_clean"),
        "score": round(float(row.get("ranking_score", 0.0)), 4),
        "reasons": reasons,
        "explanation": explanation,
        "url": row.get("url"),
        "price_per_m2": row.get("price_per_m2"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
    }

def recommend_properties(df: pd.DataFrame, user_query: str, top_k: int = 5) -> Dict[str, Any]:
    prepared = prepare_phase2_dataframe(df)
    intent = parse_user_intent(user_query)
    filtered = apply_business_filters(prepared, intent)
    ranked = rank_listings(filtered, intent, top_k=top_k)

    results = [build_result_card(row) for _, row in ranked.iterrows()]

    return {
        "query": user_query,
        "intent": asdict(intent),
        "total_after_filters": int(len(filtered)),
        "results": results,
    }


# =========================================================
# 10) EXEMPLE D’UTILISATION
# =========================================================

if __name__ == "__main__":
    # Exemple:
    # df = pd.read_csv("listings_clean.csv")
    # response = recommend_properties(
    #     df,
    #     "Je cherche un appartement à louer à Ariana, budget 1200 dt, 2 chambres",
    #     top_k=5
    # )
    # print(response)
    pass