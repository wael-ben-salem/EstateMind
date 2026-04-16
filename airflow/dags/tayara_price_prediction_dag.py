from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="tayara_price_prediction_pipeline",
    start_date=datetime(2026, 4, 11),
    schedule=None,
    catchup=False,
    tags=["price-prediction", "xgboost", "tayara"]
) as dag:

    prepare_training_data = BashOperator(
        task_id="prepare_training_data",
        bash_command="python /opt/project/agent_price/prepare_training_data.py"
    )

    train_price_model = BashOperator(
        task_id="train_price_model",
        bash_command="python /opt/project/agent_price/train_price_model.py"
    )

    test_prediction = BashOperator(
        task_id="test_prediction",
        bash_command="python /opt/project/agent_price/predict_price.py"
    )

    prepare_training_data >> train_price_model >> test_prediction