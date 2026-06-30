"""Airflow DAG example scaffold for raw -> clean -> modeled -> report."""

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.empty import EmptyOperator
except Exception:  # Allows static reading without Airflow installed.
    DAG = None

if DAG:
    with DAG(
        dag_id="raw_to_mart_pipeline",
        start_date=datetime(2026, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["portfolio", "analytics-engineering"],
    ) as dag:
        start = EmptyOperator(task_id="start")
        ingest_raw = EmptyOperator(task_id="ingest_raw")
        validate_clean = EmptyOperator(task_id="validate_clean")
        build_marts = EmptyOperator(task_id="build_marts")
        publish_report = EmptyOperator(task_id="publish_report")
        start >> ingest_raw >> validate_clean >> build_marts >> publish_report
