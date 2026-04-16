def decide_next_action(state):
    if not state["raw_exists"]:
        return {
            "scrape": True,
            "validate": True,
            "etl": True,
            "report": True,
            "reason": "No raw data found, full pipeline required."
        }

    if state["raw_age_hours"] is not None and state["raw_age_hours"] > 12:
        return {
            "scrape": True,
            "validate": True,
            "etl": True,
            "report": True,
            "reason": "Raw data is stale, refresh required."
        }

    if state["raw_record_count"] < 500:
        return {
            "scrape": True,
            "validate": True,
            "etl": True,
            "report": True,
            "reason": "Too few records, scrape again."
        }

    return {
        "scrape": False,
        "validate": True,
        "etl": True,
        "report": True,
        "reason": "Raw data exists and is recent enough."
    }