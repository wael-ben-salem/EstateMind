import pandas as pd


AMENITY_COLUMN_MAP = {
    "piscine": "has_piscine",
    "garage": "has_garage",
    "jardin": "has_jardin",
    "parking": "has_parking",
    "ascenseur": "has_ascenseur",
    "climatisation": "has_climatisation",
    "terrasse": "has_terrasse",
    "balcon": "has_balcon",
}


def apply_filters(df: pd.DataFrame, profile: dict) -> pd.DataFrame:
    """
    Applique les filtres du profil utilisateur.
    """
    filtered = df.copy()

    if profile.get("contrat"):
        filtered = filtered[filtered["contrat"] == profile["contrat"]]

    if profile.get("type"):
        filtered = filtered[filtered["type"] == profile["type"]]

    if profile.get("ville"):
        filtered = filtered[filtered["ville"] == profile["ville"]]

    if profile.get("budget_min") is not None:
        filtered = filtered[filtered["prix"] >= profile["budget_min"]]

    if profile.get("budget_max") is not None:
        filtered = filtered[filtered["prix"] <= profile["budget_max"]]

    if profile.get("surface_min") is not None:
        filtered = filtered[filtered["surface"] >= profile["surface_min"]]

    if profile.get("surface_max") is not None:
        filtered = filtered[filtered["surface"] <= profile["surface_max"]]

    if profile.get("pieces") is not None:
        filtered = filtered[filtered["pieces"] == profile["pieces"]]

    return filtered.copy()


def build_relaxed_profile(profile: dict, keep_fields: list[str]) -> dict:
    """
    Construit un profil relâché en ne gardant que certains champs.
    """
    relaxed = {}

    for key, value in profile.items():
        if key in keep_fields:
            relaxed[key] = value
        else:
            if key == "amenities":
                relaxed[key] = []
            else:
                relaxed[key] = None

    return relaxed


def apply_filters_with_fallback(df: pd.DataFrame, profile: dict):
    """
    Essaie plusieurs niveaux de filtres du plus strict au plus souple.
    Le type de bien est conservé le plus longtemps possible.
    """
    filter_levels = [
        (
            "strict",
            ["contrat", "type", "ville", "budget_min", "budget_max", "surface_min", "surface_max", "pieces", "amenities", "standing"]
        ),
        (
            "without_surface_pieces",
            ["contrat", "type", "ville", "budget_min", "budget_max", "amenities", "standing"]
        ),
        (
            "without_soft_preferences",
            ["contrat", "type", "ville", "budget_min", "budget_max"]
        ),
        (
            "core_location_constraints",
            ["contrat", "type", "ville"]
        ),
        (
            "contract_type_budget",
            ["contrat", "type", "budget_min", "budget_max"]
        ),
    ]

    for level_name, keep_fields in filter_levels:
        relaxed_profile = build_relaxed_profile(profile, keep_fields)
        filtered = apply_filters(df, relaxed_profile)

        if not filtered.empty:
            return filtered, level_name, relaxed_profile

    return df.iloc[0:0].copy(), "no_match", profile

def compute_match_score(row: pd.Series, profile: dict) -> float:
    """
    Calcule un score simple de pertinence.
    """
    score = 0.0

    if profile.get("contrat") and row.get("contrat") == profile["contrat"]:
        score += 2.0

    if profile.get("type") and row.get("type") == profile["type"]:
        score += 2.0

    if profile.get("ville") and row.get("ville") == profile["ville"]:
        score += 2.0

    for amenity in profile.get("amenities", []):
        col = AMENITY_COLUMN_MAP.get(amenity)
        if col and col in row.index and row[col] == 1:
            score += 1.0

    if profile.get("standing") == "haut_standing" and row.get("haut_standing", 0) == 1:
        score += 1.5

    budget_max = profile.get("budget_max")
    if budget_max is not None and pd.notna(row.get("prix")) and budget_max > 0:
        price_gap_ratio = abs(row["prix"] - budget_max) / budget_max

        if price_gap_ratio <= 0.05:
            score += 2.0
        elif price_gap_ratio <= 0.10:
            score += 1.5
        elif price_gap_ratio <= 0.20:
            score += 1.0

    budget_min = profile.get("budget_min")
    if budget_min is not None and pd.notna(row.get("prix")) and budget_min > 0:
        if row["prix"] >= budget_min:
            score += 0.5

    return score


def rerank_results(df: pd.DataFrame, profile: dict) -> pd.DataFrame:
    """
    Calcule le score de pertinence et trie les résultats.
    """
    if df.empty:
        return df.copy()

    ranked = df.copy()

    ranked["match_score"] = ranked.apply(
        lambda row: compute_match_score(row, profile),
        axis=1
    )

    ranked = ranked.sort_values(
        by=["match_score", "prix"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return ranked


def deduplicate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Déduplication intelligente basée sur similarité métier.
    """
    if df.empty:
        return df.copy()

    deduped = df.copy()

    # Déduplication exacte par URL
    if "url" in deduped.columns:
        deduped = deduped.drop_duplicates(subset=["url"])

    # Déduplication métier
    def build_key(row):
        prix = row.get("prix", 0)
        ville = str(row.get("ville", ""))
        type_bien = str(row.get("type", ""))
        surface = row.get("surface", 0)

        if pd.notna(surface):
            surface = round(surface / 10) * 10
        else:
            surface = 0

        return f"{prix}_{ville}_{type_bien}_{surface}"

    deduped["dedup_key"] = deduped.apply(build_key, axis=1)
    deduped = deduped.drop_duplicates(subset=["dedup_key"])
    deduped = deduped.drop(columns=["dedup_key"]).reset_index(drop=True)

    return deduped

def diversify_results(df: pd.DataFrame, max_per_price: int = 2) -> pd.DataFrame:
    """
    Limite le nombre de résultats trop homogènes.
    Ex: éviter 5 résultats au même prix exact.
    """
    if df.empty or "prix" not in df.columns:
        return df.copy()

    diversified_parts = []

    for _, group in df.groupby("prix", sort=False):
        diversified_parts.append(group.head(max_per_price))

    diversified = pd.concat(diversified_parts, ignore_index=True)
    return diversified.reset_index(drop=True)

def recommend_properties(df: pd.DataFrame, profile: dict, top_k: int = 10):
    """
    Pipeline complet V2 :
    1. filtres avec fallback
    2. reranking
    3. déduplication
    4. top résultats

    Retourne :
    - résultats
    - niveau de filtre utilisé
    - profil utilisé réellement
    """
    filtered, filter_level, effective_profile = apply_filters_with_fallback(df, profile)

    if filtered.empty:
        return filtered.copy(), filter_level, effective_profile

    ranked = rerank_results(filtered, effective_profile)
    ranked = deduplicate_results(ranked)
    ranked = diversify_results(ranked, max_per_price=2)

    display_columns = [
        "prix",
        "ville",
        "type",
        "contrat",
        "surface",
        "pieces",
        "titre",
        "source",
        "url",
        "match_score",
        "has_piscine",
        "has_garage",
        "has_jardin",
        "has_parking",
        "has_ascenseur",
        "has_climatisation",
        "has_terrasse",
        "has_balcon",
        "haut_standing",
    ]

    available_columns = [col for col in display_columns if col in ranked.columns]

    return ranked[available_columns].head(top_k).copy(), filter_level, effective_profile