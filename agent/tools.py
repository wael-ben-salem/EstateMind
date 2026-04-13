import json
import subprocess


def run_scraper():
    print("[TOOL] Running scraper...")
    subprocess.run(
        ["python", "/opt/project/scraper/run_scraper.py"],
        check=True,
    )


def run_raw_deduplication():
    print("[TOOL] Deduplicating raw scraped data against DB...")
    subprocess.run(
        ["python", "/opt/project/agent/deduplicate_raw_against_db.py"],
        check=True,
    )


def run_regex_enrichment():
    print("[TOOL] Running regex enrichment...")
    subprocess.run(
        ["python", "/opt/project/agent/enrich_with_regex.py"],
        check=True,
    )


def run_llm_fallback():
    print("[TOOL] Running LLM fallback enrichment...")
    subprocess.run(
        ["python", "/opt/project/agent/enrich_with_llm_fallback.py"],
        check=True,
    )


def run_location_matching():
    print("[TOOL] Running location matching...")
    subprocess.run(
        ["python", "/opt/project/agent/match_locations_from_reference.py"],
        check=True,
    )


def run_validator():
    print("[TOOL] Running validator...")
    result = subprocess.run(
        ["python", "/opt/project/agent/validator.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return json.loads(result.stdout)


def run_etl():
    print("[TOOL] Running ETL...")
    result = subprocess.run(
        ["python", "/opt/spark_app/jobs/tayara_etl.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"ETL failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def run_report():
    print("[TOOL] Running reporter...")
    result = subprocess.run(
        ["python", "/opt/project/agent/reporter.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return {"report_text": result.stdout}