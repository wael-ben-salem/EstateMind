import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CANDIDATE_PATHS = [
    #os.path.join(BASE_DIR, "EstateMind-master", "data_cleaned", "tunisia_realestate_cleaned.csv"),
    os.path.join(BASE_DIR, "data_cleaned", "tunisia_realestate_cleaned.csv"),
]

DATA_PATH = None
for path in CANDIDATE_PATHS:
    if os.path.exists(path):
        DATA_PATH = path
        break

if DATA_PATH is None:
    raise FileNotFoundError(
        "Impossible de trouver tunisia_realestate_cleaned.csv dans les emplacements attendus."
    )
CORE_COLUMNS = [
    "prix",
    "ville",
    "type",
    "contrat",
    "surface",
    "pieces",
    "titre",
    "description",
    "source",
    "url",
    "has_parking",
    "has_piscine",
    "has_jardin",
    "has_garage",
    "has_ascenseur",
    "has_climatisation",
    "has_terrasse",
    "has_balcon",
    "haut_standing",
]

TEXT_COLUMNS = [
    "ville",
    "type",
    "contrat",
    "titre",
    "description",
    "source",
    "url",
]

NUMERIC_COLUMNS = [
    "prix",
    "surface",
    "pieces",
]

BOOL_COLUMNS = [
    "has_parking",
    "has_piscine",
    "has_jardin",
    "has_garage",
    "has_ascenseur",
    "has_climatisation",
    "has_terrasse",
    "has_balcon",
    "haut_standing",
]


def load_raw_data():
    """
    Charge le dataset brut complet.
    Sert au diagnostic et à l'analyse.
    """
    print(f"[INFO] Chargement dataset : {DATA_PATH}")
    return pd.read_csv(DATA_PATH, low_memory=False)


def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    S'assure que toutes les colonnes cœur existent.
    Si une colonne manque, elle est créée vide.
    """
    for col in CORE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df


def load_clean_data() -> pd.DataFrame:
    """
    Charge et nettoie le dataset pour le moteur de recommandation.
    Retourne uniquement les colonnes cœur utiles au module.
    """
    df = load_raw_data().copy()
    df = _ensure_required_columns(df)

    # On ne garde que les colonnes utiles au moteur
    df = df[CORE_COLUMNS].copy()

    # Normalisation des colonnes texte
    for col in TEXT_COLUMNS:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # Conversion numérique
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Conversion booléenne/binaire
    for col in BOOL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Filtrage minimal pour rendre le moteur exploitable
    df = df[df["prix"] > 0].copy()
    df = df[df["ville"] != ""].copy()
    df = df[df["type"] != ""].copy()
    df = df[df["contrat"] != ""].copy()

    # Reset index pour garder quelque chose de propre
    df = df.reset_index(drop=True)

    return df