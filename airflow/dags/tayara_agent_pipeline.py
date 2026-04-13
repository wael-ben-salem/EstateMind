from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="tayara_ai_agent_pipeline",
    start_date=datetime(2026, 4, 8),
    schedule=None,
    catchup=False,
    tags=["ai-agent", "tayara", "etl"]
) as dag:

    run_agent = BashOperator(
        task_id="run_agent",
        bash_command="python /opt/project/agent/run_agent.py"
    )