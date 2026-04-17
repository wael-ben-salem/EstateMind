import pandas as pd

from data_loader import load_clean_data
from phase2_business_logic import recommend_properties_from_understanding
from query_classifier import classify_query
from query_understanding import understand_query

df = load_clean_data()

queries = [
    "maison vacances a hammamet avec piscine",
    "appartement meuble a la marsa 1200 dt",
    "maison familiale a sousse budget 300000",
    "bien proche de la mer a hammamet pour vacances",
]

for query in queries:
    print("=" * 100)
    print("QUERY :", query)

    # 1. CLASSIFICATION
    classification = classify_query(query)

    print("\nCLASSIFICATION :")
    print(f"  label      : {classification.label}")
    print(f"  confidence : {classification.confidence}")
    print(f"  reason     : {classification.reason}")

    # 2. GESTION SELON TYPE
    if classification.label == "greeting":
        print("\nRéponse : Bonjour 👋 Je peux vous aider à trouver un bien immobilier.")
        continue

    if classification.label == "out_of_scope":
        print("\nRéponse : Je suis spécialisé dans l'immobilier. Posez-moi une question sur un bien.")
        continue

    # 3. QUERY UNDERSTANDING
    understanding = understand_query(query)

    print("\nQUERY UNDERSTANDING :")
    for k, v in understanding.to_dict().items():
        print(f"  {k}: {v}")

    # 4. RECOMMANDATION
    response = recommend_properties_from_understanding(
        df,
        understanding.to_dict(),
        top_k=5
    )

    print("\nINTENT DETECTE (ENGINE ACTUEL) :")
    for k, v in response["intent"].items():
        print(f"  {k}: {v}")

    print(f"\nNombre de résultats après filtres : {response['total_after_filters']}")

    if response.get("global_explanation"):
        print("\nEXPLICATION GLOBALE :")
        print(response["global_explanation"])

    if response.get("used_relaxation"):
        print("\nRELAXATION INTELLIGENTE ACTIVE :")
        print(response.get("message"))

    if response.get("relaxed_criteria"):
        print("Critères relâchés :", ", ".join(response["relaxed_criteria"]))

    if response["results"]:
        results_df = pd.DataFrame(response["results"])

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
                "explanation": "explication",
            }
        )

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

        print("\nEXPLICATIONS DES RESULTATS :")
        for i, item in enumerate(response["results"], start=1):
            print(f"- Résultat {i}: {item.get('explanation')}")
        print()

    else:
        print("\nAucun résultat trouvé.\n")