import pandas as pd

from recommender.data_loader import load_clean_data
from recommender.recommender_service import run_recommender_pipeline

def main():
    df = load_clean_data()

    queries = [
        "maison vacances a hammamet avec piscine",
        "appartement meuble a la marsa 1200 dt",
        "maison familiale a sousse budget 300000",
        "bien proche de la mer a hammamet pour vacances",
        "bonjour",
        "qui est le president",
    ]

    for query in queries:
        print("=" * 100)
        print("QUERY :", query)

        response = run_recommender_pipeline(
            user_query=query,
            df=df,
            top_k=5
        )

        print("\nSTATUS :")
        print(f"  {response['status']}")

        print("\nCLASSIFICATION :")
        for k, v in response["classification"].items():
            print(f"  {k}: {v}")

        if response.get("understanding"):
            print("\nQUERY UNDERSTANDING :")
            for k, v in response["understanding"].items():
                print(f"  {k}: {v}")

        if response.get("user_message"):
            print("\nMESSAGE UTILISATEUR :")
            print(response["user_message"])
        if response.get("summary"):
            print("\nSUMMARY :")
            print(response["summary"])
        recommendation = response.get("recommendation")
        if recommendation:
            print(f"\nNombre de résultats après filtres : {recommendation.get('total_after_filters', 0)}")

            if recommendation.get("global_explanation"):
                print("\nEXPLICATION GLOBALE :")
                print(recommendation["global_explanation"])

            if recommendation.get("used_relaxation"):
                print("\nRELAXATION INTELLIGENTE ACTIVE :")
                print(recommendation.get("message"))

            if recommendation.get("relaxed_criteria"):
                print("Critères relâchés :", ", ".join(recommendation["relaxed_criteria"]))

        results = response.get("results", [])

        if results:
            results_df = pd.DataFrame(results)

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
            for i, item in enumerate(results, start=1):
                print(f"- Résultat {i}: {item.get('explanation')}")
            print()
        else:
            print("\nAucun résultat trouvé.\n")


if __name__ == "__main__":
    main()