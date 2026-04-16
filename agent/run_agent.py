import json
import os
from datetime import datetime
from tools import (
    run_scraper,
    run_raw_deduplication,
    run_regex_enrichment,
    run_llm_fallback,
    run_location_matching,
    run_validator,
    run_etl,
    run_report,
)

MEMORY_FILE = "/opt/project/agent/memory.json"


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception as e:
            print(f"[MEMORY WARNING] Could not read memory file: {e}")
            return {}
    return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def main():
    memory = load_memory()

    run_scraper()
    run_raw_deduplication()
    run_regex_enrichment()
    run_llm_fallback()
    run_location_matching()
    validation_result = run_validator()
    run_etl()
    report_result = run_report()

    memory["last_run"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "validation_result": validation_result,
        "report_result": report_result,
    }

    save_memory(memory)

    print("[AGENT] Finished.")
    print(json.dumps(memory["last_run"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()