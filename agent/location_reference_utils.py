import json
import unicodedata
import re

REFERENCE_FILE = "/opt/project/agent/reference/state-municipality-areas.json"


def normalize_text(text):
    if not text:
        return ""
    text = str(text).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text)
    return text


def get_city_list(reference_file=REFERENCE_FILE):
    with open(reference_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    values = set()

    for state in data:
        # top-level governorate/state names
        for key in ["Name", "Value"]:
            val = state.get(key)
            if val:
                values.add(normalize_text(val))

        # nested delegations/localities
        for delegation in state.get("Delegations", []):
            for key in ["Name", "Value"]:
                val = delegation.get(key)
                if val:
                    values.add(normalize_text(val))

    # remove blanks and sort
    values = {v for v in values if v}
    return sorted(values)