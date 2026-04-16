import json
import os
from datetime import datetime, timezone


RAW_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"


def read_state(memory):
    state = {
        "raw_exists": os.path.exists(RAW_FILE),
        "raw_record_count": 0,
        "raw_age_hours": None,
        "last_run": memory.get("last_run"),
    }

    if os.path.exists(RAW_FILE):
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            state["raw_record_count"] = len(data)

        mtime = os.path.getmtime(RAW_FILE)
        file_time = datetime.fromtimestamp(mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - file_time).total_seconds() / 3600
        state["raw_age_hours"] = round(age_hours, 2)

    return state