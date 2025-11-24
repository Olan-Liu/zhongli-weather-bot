from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator  # type: ignore
from datetime import datetime

with DAG(
    dag_id="my_first_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["grok"]
) as dag:
    task = BashOperator(
        task_id="hello",
        bash_command='echo "恭喜！你的 Airflow 終於完全正常了！by Grok"'
    )
