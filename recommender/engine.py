import pandas as pd

from data_loader import load_clean_data
from phase2_business_logic import recommend_properties

df = load_clean_data()

queries = [
    "studio a sousse 80 m2 max 150000",
    "maison vacances a hammamet avec piscine",
    "terrain a nabeul entre 200000 et 400000",
    "appartement 1200 dt a la marsa",
]

for query in queries:
    print("=" * 100)
    print("QUERY :", query)

    response = recommend_properties(df, query, top_k=5)

    print("\nINTENT DETECTE :")
    for k, v in response["intent"].items():
        print(f"  {k}: {v}")

    print(f"\nNombre de résultats après filtres : {response['total_after_filters']}")

    if response["results"]:
        results_df = pd.DataFrame(response["results"])

        # Renommage pour affichage plus propre
        results_df = results_df.rename(
            columns={
                "title": "titre",
                "city": "ville",
                "property_type": "type",
                "contract": "contrat",
                "price": "prix_affiche",
                "surface": "surface",
                "rooms": "pieces",
                "score": "match_score",
                "url": "url",
                "price_per_m2": "prix_m2",
            }
        )

        # Ajouter les raisons sous forme lisible
        if "reasons" in results_df.columns:
            results_df["raisons"] = results_df["reasons"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else ""
            )

        cols_to_show = [
            col for col in [
                "prix_affiche",
                "ville",
                "type",
                "contrat",
                "surface",
                "pieces",
                "prix_m2",
                "match_score",
                "raisons",
                "url",
                "titre",
            ]
            if col in results_df.columns
        ]

        print("\nTOP RESULTS :")
        print(results_df[cols_to_show].to_string(index=False))
        print()
    else:
        print("\nAucun résultat trouvé.\n")