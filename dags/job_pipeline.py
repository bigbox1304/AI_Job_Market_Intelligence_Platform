from datetime import datetime, timedelta
import sys
import os

sys.path.append("/opt/airflow/project")

from airflow import DAG
from airflow.operators.python import PythonOperator
from src.crawl.pipeline_monitor import record_pipeline_task


def run_stage(stage_name, stage_callable, context):
    run_id = context["run_id"]
    task_id = context["task_instance"].task_id
    record_pipeline_task(run_id, "job_recommendation_pipeline", task_id, "running")
    try:
        result = stage_callable()
        record_pipeline_task(run_id, "job_recommendation_pipeline", task_id, "success", {"result": str(result or "ok")})
        return result
    except Exception as exc:
        record_pipeline_task(run_id, "job_recommendation_pipeline", task_id, "failed", {"error": str(exc)})
        raise


def crawl_task(**context):
    from src.crawl.crawler_v2 import crawl
    return run_stage("crawl_jobs", crawl, context)


def clean_task(**context):
    from src.crawl.clean_crawl_raw import clean_data
    return run_stage("clean_jobs", clean_data, context)


def to_db_task(**context):
    from src.crawl.to_database import insert_to_db
    return run_stage("load_to_database", insert_to_db, context)


def train_task(**context):
    from src.train.train_skill_aware_model import train_embeddings
    return run_stage("train_model", train_embeddings, context)


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
