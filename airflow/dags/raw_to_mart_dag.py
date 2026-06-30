"""Airflow DAG example scaffold for raw -> clean -> modeled -> report."""

import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from airflow import DAG
    from airflow.operators.empty import EmptyOperator
    from airflow.operators.python import PythonOperator
except Exception:  # Allows static reading without Airflow installed.
    DAG = None

from shared.local_pipeline_simulator import run_pipeline

if DAG:
    with DAG(
        dag_id="raw_to_mart_pipeline",
        start_date=datetime(2026, 1, 1),
        schedule="@daily",
        catchup=False,
        default_args={"retries": 2},
        tags=["portfolio", "analytics-engineering"],
    ) as dag:
        start = EmptyOperator(task_id="start")
        ingest_raw = EmptyOperator(task_id="ingest_raw")
        validate_clean = EmptyOperator(task_id="validate_clean")
        build_marts = EmptyOperator(task_id="build_marts")
        publish_report = PythonOperator(
            task_id="publish_report",
            python_callable=run_pipeline,
        )
        start >> ingest_raw >> validate_clean >> build_marts >> publish_report
