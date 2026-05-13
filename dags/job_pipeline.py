from datetime import datetime, timedelta
import sys
import os

sys.path.append("/opt/airflow/project")

from airflow import DAG
from airflow.operators.python import PythonOperator


def crawl_task():
    from src.crawl.crawler_v2 import crawl
    crawl()

def clean_task():
    from src.crawl.clean_crawl_raw import clean_data
    clean_data()

def to_db_task():
    from src.crawl.to_database import insert_to_db
    insert_to_db()

def train_task():
    from src.train.train_skill_aware_model import train_embeddings
    train_embeddings()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="job_recommendation_pipeline",
    default_args=default_args,
    description="Job recommendation pipeline",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["job", "ml", "pipeline"],
) as dag:

    crawl = PythonOperator(
        task_id="crawl_jobs",
        python_callable=crawl_task,
    )

    clean = PythonOperator(
        task_id="clean_jobs",
        python_callable=clean_task,
    )

    to_db = PythonOperator(
        task_id="load_to_database",
        python_callable=to_db_task,
    )

    train = PythonOperator(
        task_id="train_model",
        python_callable=train_task,
    )

    crawl >> clean >> to_db >> train