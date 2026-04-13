import json
import unicodedata
import re

INPUT_FILE = "/opt/spark_app/data/TayaraDataEnriched.json"
REFERENCE_FILE = "/opt/project/agent/reference/state-municipality-areas.json"
OUTPUT_FILE = "/opt/spark_app/data/TayaraDataEnrichedLocated.json"

def normalize_text(text):
    if not text:
        return ""
    text = str(text).upper().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_reference():
    with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
        ref = json.load(f)

    state_index = {}
    delegation_index = {}

    for state in ref:
        state_name = normalize_text(state.get("Name"))
        state_value = normalize_text(state.get("Value"))

        state_payload = {
            "matched_state": state.get("Name"),
            "state_latitude": state.get("Latitude"),
            "state_longitude": state.get("Longitude"),
        }

        if state_name:
            state_index[state_name] = state_payload
        if state_value:
            state_index[state_value] = state_payload

        for d in state.get("Delegations", []):
            keys = {
                normalize_text(d.get("Name")),
                normalize_text(d.get("Value")),
            }

            payload = {
                "matched_state": state.get("Name"),
                "matched_delegation": d.get("Value"),
                "matched_locality_name": d.get("Name"),
                "matched_postal_code": d.get("PostalCode"),
                "latitude": d.get("Latitude"),
                "longitude": d.get("Longitude"),
                "geo_match_level": "delegation",
                "geo_source": "state_municipality_areas"
            }

            for key in keys:
                if key:
                    delegation_index[key] = payload

    return state_index, delegation_index

def try_match_location(item, state_index, delegation_index):
    candidates = [
        item.get("adresse_raw"),
        item.get("quartier"),
        item.get("delegation"),
        item.get("ville"),
        item.get("gouvernorat"),
        item.get("location"),
    ]

    normalized_candidates = [normalize_text(c) for c in candidates if c]

    for cand in normalized_candidates:
        if cand in delegation_index:
            return delegation_index[cand]

    for cand in normalized_candidates:
        if cand in state_index:
            s = state_index[cand]
            return {
                "matched_state": s.get("matched_state"),
                "matched_delegation": None,
                "matched_locality_name": None,
                "matched_postal_code": None,
                "latitude": s.get("state_latitude"),
                "longitude": s.get("state_longitude"),
                "geo_match_level": "state",
                "geo_source": "state_municipality_areas"
            }

    return {
        "matched_state": None,
        "matched_delegation": None,
        "matched_locality_name": None,
        "matched_postal_code": None,
        "latitude": None,
        "longitude": None,
        "geo_match_level": "none",
        "geo_source": "none"
    }

def main():
    state_index, delegation_index = load_reference()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for item in data:
        match = try_match_location(item, state_index, delegation_index)
        item = {**item, **match}
        result.append(item)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Location matching saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()