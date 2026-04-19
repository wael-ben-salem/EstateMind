from typing import Any, Dict, Optional

from recommender.data_loader import load_clean_data
from recommender.query_classifier import classify_query
from recommender.query_understanding import understand_query
from recommender.response_generator import build_user_message, build_summary
from recommender.phase2_business_logic import recommend_properties_from_understanding

def run_recommender_pipeline(
    user_query: str,
    df: Optional[Any] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Point d'entrée principal du module recommender.
    Cette fonction est pensée pour être appelée par un chatbot,
    un agent ou une API.
    """

    if df is None:
        df = load_clean_data()

    classification = classify_query(user_query)

    classification_payload = {
        "label": classification.label,
        "confidence": classification.confidence,
        "reason": classification.reason,
    }

    # 1. Salutation
    if classification.label == "greeting":
        user_message = build_user_message(
            classification_label=classification.label,
            understanding=None,
            recommendation=None,
            results=[],
        )

        return {
            "status": "handled",
            "query": user_query,
            "classification": classification_payload,
            "understanding": None,
            "user_message": user_message,
            "summary": None,
            "recommendation": None,
            "results": [],
        }

    # 2. Hors sujet
    if classification.label == "out_of_scope":
        user_message = build_user_message(
            classification_label=classification.label,
            understanding=None,
            recommendation=None,
            results=[],
        )

        return {
            "status": "handled",
            "query": user_query,
            "classification": classification_payload,
            "understanding": None,
            "user_message": user_message,
            "summary": None,
            "recommendation": None,
            "results": [],
        }

    # 3. Requête ambiguë
    if classification.label == "unknown":
        user_message = build_user_message(
            classification_label=classification.label,
            understanding=None,
            recommendation=None,
            results=[],
        )

        return {
            "status": "handled",
            "query": user_query,
            "classification": classification_payload,
            "understanding": None,
            "user_message": user_message,
            "summary": None,
            "recommendation": None,
            "results": [],
        }

    # 4. Requête immobilière
    understanding = understand_query(user_query)

    recommendation = recommend_properties_from_understanding(
        df=df,
        understanding=understanding.to_dict(),
        top_k=top_k,
    )

    results = recommendation.get("results", [])

    user_message = build_user_message(
        classification_label=classification.label,
        understanding=understanding.to_dict(),
        recommendation=recommendation,
        results=results,
    )

    summary = build_summary(
        understanding=understanding.to_dict(),
        recommendation=recommendation,
        results=results,
    )

    return {
        "status": "success",
        "query": user_query,
        "classification": classification_payload,
        "understanding": understanding.to_dict(),
        "user_message": user_message,
        "summary": summary,
        "recommendation": recommendation,
        "results": results,
    }