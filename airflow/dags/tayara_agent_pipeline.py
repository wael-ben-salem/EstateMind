from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import json
import os

MEMORY_FILE = "/opt/project/agent/memory.json"

def load_and_save_memory(**context):
    """Load memory at the start of the pipeline"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    memory = {}
                else:
                    memory = json.loads(content)
        except Exception as e:
            print(f"[MEMORY WARNING] Could not read memory file: {e}")
            memory = {}
    else:
        memory = {}
    
    context['task_instance'].xcom_push(key='memory', value=memory)
    print(f"[AGENT] Pipeline started. Memory loaded: {bool(memory)}")

def save_final_memory(**context):
    """Save memory at the end of the pipeline"""
    memory = context['task_instance'].xcom_pull(task_ids='load_memory', key='memory')
    if memory is None:
        memory = {}
    
    memory["last_run"] = {
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
    
    print("[AGENT] Pipeline finished successfully.")
    print(json.dumps(memory["last_run"], indent=2, ensure_ascii=False))

with DAG(
    dag_id="tayara_ai_agent_pipeline",
    start_date=datetime(2026, 4, 8),
    schedule=None,
    catchup=False,
    tags=["ai-agent", "tayara", "etl"],
    description="Step-by-step Tayara AI Agent Pipeline"
) as dag:

    # Step 0: Load Memory
    load_memory = PythonOperator(
        task_id="load_memory",
        python_callable=load_and_save_memory,
        doc="Initialize pipeline and load memory state"
    )

    # Step 1: Run Scraper
    step_scraper = BashOperator(
        task_id="step_1_scraper",
        bash_command="python /opt/project/scraper/run_scraper.py",
        doc="Scrape data from Tayara website"
    )

    # Step 2: Raw Deduplication
    step_deduplicate = BashOperator(
        task_id="step_2_deduplicate_raw",
        bash_command="python /opt/project/agent/deduplicate_raw_against_db.py",
        doc="Remove duplicates from raw scraped data"
    )

    # Step 3: Regex Enrichment
    step_regex = BashOperator(
        task_id="step_3_regex_enrichment",
        bash_command="python /opt/project/agent/enrich_with_regex.py",
        doc="Enrich data using regex patterns"
    )

    # Step 4: LLM Fallback Enrichment
    step_llm = BashOperator(
        task_id="step_4_llm_enrichment",
        bash_command="python /opt/project/agent/enrich_with_llm_fallback.py",
        doc="Use LLM for fallback enrichment"
    )

    # Step 5: Location Matching
    step_location = BashOperator(
        task_id="step_5_location_matching",
        bash_command="python /opt/project/agent/match_locations_from_reference.py",
        doc="Match locations from reference database"
    )

    # Step 6: Validation
    step_validator = BashOperator(
        task_id="step_6_validator",
        bash_command="python /opt/project/agent/validator.py",
        doc="Validate processed data"
    )

    # Step 7: ETL
    step_etl = BashOperator(
        task_id="step_7_etl_transform",
        bash_command="python /opt/spark_app/jobs/tayara_etl.py",
        doc="Transform and load data to warehouse"
    )

    # Step 8: Generate Report
    step_reporter = BashOperator(
        task_id="step_8_generate_report",
        bash_command="python /opt/project/agent/reporter.py",
        doc="Generate final report"
    )

    # Step 9: Save Memory
    save_memory = PythonOperator(
        task_id="save_memory",
        python_callable=save_final_memory,
        trigger_rule="all_done",
        doc="Save memory state after pipeline completion"
    )

    # Define dependencies
    load_memory >> step_scraper >> step_deduplicate >> step_regex >> step_llm >> \
    step_location >> step_validator >> step_etl >> step_reporter >> save_memory