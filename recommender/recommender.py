import pandas as pd


CORE_COLUMNS = [
    "prix",
    "surface",
    "pieces",
    "ville",
    "type",
    "contrat"
]

AMENITY_COLUMNS = [
    "has_parking",
    "has_piscine",
    "has_jardin",
    "has_terrasse",
    "has_climatisation",
    "has_ascenseur",
    "has_garage",
    "has_balcon"
]

EXTRA_COLUMNS = [
    "latitude",
    "longitude",
    "titre",
    "description",
    "source",
    "haut_standing",
    "bon_entourage"
]

SELECTED_COLUMNS = CORE_COLUMNS + AMENITY_COLUMNS + EXTRA_COLUMNS


def load_data():
    df = pd.read_csv(
        "data_cleaned/tunisia_realestate_cleaned.csv",
        low_memory=False
    )
    print("Dataset loaded successfully.")
    print("Shape:", df.shape)
    print("Columns:")
    print(df.columns.tolist())
    return df


def prepare_dataset(df):
    # garder seulement les colonnes utiles
    df_model = df[SELECTED_COLUMNS].copy()

    # conversion des colonnes numériques principales
    df_model["prix"] = pd.to_numeric(df_model["prix"], errors="coerce")
    df_model["surface"] = pd.to_numeric(df_model["surface"], errors="coerce")
    df_model["pieces"] = pd.to_numeric(df_model["pieces"], errors="coerce")

    # nettoyage des colonnes texte principales
    df_model["ville"] = df_model["ville"].astype(str).str.strip().str.lower()
    df_model["type"] = df_model["type"].astype(str).str.strip().str.lower()
    df_model["contrat"] = df_model["contrat"].astype(str).str.strip().str.lower()

    # amenities -> binaire
    for col in AMENITY_COLUMNS:
        df_model[col] = pd.to_numeric(df_model[col], errors="coerce").fillna(0).astype(int)

    # bool métier supplémentaires
    for col in ["haut_standing", "bon_entourage"]:
        if col in df_model.columns:
            df_model[col] = pd.to_numeric(df_model[col], errors="coerce").fillna(0).astype(int)

    # suppression des lignes inutilisables
    df_model = df_model.dropna(subset=["prix", "surface", "pieces"])
    df_model = df_model[df_model["ville"] != "nan"]
    df_model = df_model[df_model["type"] != "nan"]
    df_model = df_model[df_model["contrat"] != "nan"]

    return df_model


def inspect_dataset(df_model):
    print("\nPrepared dataset shape:", df_model.shape)

    print("\nUnique values in contrat:")
    print(df_model["contrat"].value_counts(dropna=False).head(20))

    print("\nUnique values in type:")
    print(df_model["type"].value_counts(dropna=False).head(20))

    print("\nTop cities:")
    print(df_model["ville"].value_counts(dropna=False).head(20))

    print("\nMissing values:")
    print(df_model.isna().sum().sort_values(ascending=False).head(20))


if __name__ == "__main__":
    df = load_data()
    df_model = prepare_dataset(df)
    inspect_dataset(df_model)