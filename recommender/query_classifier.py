from dataclasses import dataclass
from typing import List, Optional
import re
import unicodedata


# =========================================================
# OUTILS
# =========================================================

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"\s+", " ", text)
    return text


# =========================================================
# MODELE DE SORTIE
# =========================================================

@dataclass
class QueryClassificationResult:
    label: str                 # "real_estate", "greeting", "out_of_scope", "unknown"
    confidence: float
    reason: str


# =========================================================
# LISTES DE MOTS-CLES
# =========================================================

GREETING_KEYWORDS = {
    "bonjour", "salut", "hello", "cc", "coucou", "bonsoir",
    "merci", "thank you", "svp", "stp"
}

REAL_ESTATE_KEYWORDS = {
    "appartement", "appart", "studio", "villa", "maison", "terrain",
    "location", "louer", "a louer", "à louer", "vente", "a vendre", "à vendre",
    "immobilier", "bien", "prix", "budget", "surface", "m2", "piece", "pieces",
    "chambre", "s+1", "s+2", "s+3", "contrat", "piscine", "garage", "jardin",
    "marsa", "tunis", "sousse", "hammamet", "nabeul", "ariana", "sfax"
}

OUT_OF_SCOPE_HINTS = {
    "president", "météo", "meteo", "football", "match", "blague",
    "python", "java", "recette", "medecin", "maladie", "film"
}


# =========================================================
# CLASSIFICATION
# =========================================================

def classify_query(query: str) -> QueryClassificationResult:
    q = normalize_text(query)

    if not q:
        return QueryClassificationResult(
            label="unknown",
            confidence=0.0,
            reason="empty_query"
        )

    # 1. Greeting simple
    if q in GREETING_KEYWORDS or len(q.split()) <= 2 and any(k == q for k in GREETING_KEYWORDS):
        return QueryClassificationResult(
            label="greeting",
            confidence=0.95,
            reason="simple_greeting_detected"
        )

    # 2. Score immobilier
    real_estate_hits = sum(1 for kw in REAL_ESTATE_KEYWORDS if kw in q)
    out_scope_hits = sum(1 for kw in OUT_OF_SCOPE_HINTS if kw in q)

    # présence de chiffres + termes immobiliers = fort signal
    has_number = bool(re.search(r"\d+", q))

    if real_estate_hits >= 2:
        confidence = 0.95 if has_number else 0.85
        return QueryClassificationResult(
            label="real_estate",
            confidence=confidence,
            reason="multiple_real_estate_signals"
        )

    if real_estate_hits == 1 and has_number:
        return QueryClassificationResult(
            label="real_estate",
            confidence=0.80,
            reason="single_real_estate_signal_with_numeric_constraint"
        )

    # 3. Hors sujet
    if out_scope_hits > 0 and real_estate_hits == 0:
        return QueryClassificationResult(
            label="out_of_scope",
            confidence=0.90,
            reason="non_real_estate_topic_detected"
        )

    # 4. Si ambigu
    if real_estate_hits == 1:
        return QueryClassificationResult(
            label="real_estate",
            confidence=0.60,
            reason="weak_real_estate_signal"
        )

    return QueryClassificationResult(
        label="unknown",
        confidence=0.40,
        reason="insufficient_signal"
    )