from typing import Any, Dict, List, Optional


def format_location_label(city: Optional[str]) -> str:
    if not city:
        return "la zone demandée"
    return city


def format_property_label(property_type: Optional[str]) -> str:
    if not property_type:
        return "bien"
    return property_type

def pluralize(word: str, count: int) -> str:
    if count <= 1:
        return word
    return word + "s"


def build_user_message(
    classification_label: str,
    understanding: Optional[Dict[str, Any]],
    recommendation: Optional[Dict[str, Any]],
    results: List[Dict[str, Any]]
) -> str:
    if classification_label == "greeting":
        return "Bonjour 👋 Je peux vous aider à trouver un bien immobilier."

    if classification_label == "out_of_scope":
        return "Je suis spécialisé dans l'immobilier. Posez-moi une question sur un appartement, une maison, un terrain ou une location."

    if classification_label == "unknown":
        return "Je n’ai pas bien compris votre demande. Je peux vous aider à chercher un appartement, une maison, un terrain ou une location selon votre budget et votre ville."

    if not recommendation:
        return "Aucune recommandation n’a pu être générée."

    if recommendation.get("used_relaxation"):
        return recommendation.get(
            "message",
            "Aucun bien ne correspond strictement à vos critères. Voici les alternatives les plus proches."
        )

    if not results:
        return "Aucun bien n’a été trouvé pour cette recherche."

    city = format_location_label(understanding.get("city") if understanding else None)
    property_type = format_property_label(understanding.get("property_type") if understanding else None)
    property_type_label = pluralize(property_type, len(results))

    return f"J’ai trouvé {len(results)} {property_type_label} à {city} correspondant à votre recherche."

def build_summary(
    understanding: Optional[Dict[str, Any]],
    recommendation: Optional[Dict[str, Any]],
    results: List[Dict[str, Any]]
) -> Optional[str]:
    if not understanding or not recommendation:
        return None

    parts = []

    if understanding.get("contract"):
        parts.append(f"contrat={understanding['contract']}")
    if understanding.get("city"):
        parts.append(f"ville={understanding['city']}")
    if understanding.get("property_type"):
        parts.append(f"type={understanding['property_type']}")
    if understanding.get("budget_max") is not None:
        parts.append(f"budget_max={int(understanding['budget_max'])} TND")
    if understanding.get("min_surface") is not None:
        parts.append(f"surface_min={int(understanding['min_surface'])} m²")

    criteria = ", ".join(parts) if parts else "critères généraux"

    if results:
        return f"{len(results)} résultat(s) retenu(s) selon : {criteria}."
    return f"Aucun résultat trouvé selon : {criteria}."