from typing import Any, Dict

from data_loader import load_clean_data
from query_classifier import classify_query
from query_understanding import understand_query
from phase2_business_logic import recommend_properties_from_understanding


def run_recommender_pipeline(user_query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Point d'entrée principal du module recommender.
    Cette fonction est pensée pour être appelée plus tard
    par un chatbot, un agent ou une API.
    """

    df = load_clean_data()

    classification = classify_query(user_query)

    # 1. Salutation
    if classification.label == "greeting":
        return {
            "status": "handled",
            "query": user_query,
            "classification": {
                "label": classification.label,
                "confidence": classification.confidence,
                "reason": classification.reason,
            },
            "message": "Bonjour 👋 Je peux vous aider à trouver un bien immobilier.",
            "results": [],
        }

    # 2. Hors sujet
    if classification.label == "out_of_scope":
        return {
            "status": "handled",
            "query": user_query,
            "classification": {
                "label": classification.label,
                "confidence": classification.confidence,
                "reason": classification.reason,
            },
            "message": "Je suis spécialisé dans l'immobilier. Posez-moi une question sur un bien.",
            "results": [],
        }

    # 3. Requête immobilière
    understanding = understand_query(user_query)

    recommendation = recommend_properties_from_understanding(
        df=df,
        understanding=understanding.to_dict(),
        top_k=top_k,
    )

    return {
        "status": "success",
        "query": user_query,
        "classification": {
            "label": classification.label,
            "confidence": classification.confidence,
            "reason": classification.reason,
        },
        "understanding": understanding.to_dict(),
        "recommendation": recommendation,
    }