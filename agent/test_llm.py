from llm_reasoner import call_llm_for_decision

state = {
    "raw_exists": True,
    "raw_record_count": 9980,
    "raw_age_hours": 2.1,
    "last_run": None
}

print(call_llm_for_decision(state))