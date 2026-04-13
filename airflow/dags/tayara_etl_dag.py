from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="tayara_etl_pipeline",
    start_date=datetime(2026, 3, 15),
    schedule=None,
    catchup=False,
    tags=["spark", "etl", "tayara"]
) as dag:

    run_tayara_etl = BashOperator(
        task_id="run_tayara_etl",
        bash_command="python /opt/spark_app/jobs/tayara_etl.py"
    )