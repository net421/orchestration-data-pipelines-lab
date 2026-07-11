"""Airflow TaskFlow example wrapping the shared analytics pipeline.

Install Apache Airflow separately before importing this DAG.
"""
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

from analytics_pipeline.config import PipelineConfig
from analytics_pipeline.ingest import ingest_sources
from analytics_pipeline.pipeline import run_pipeline
from analytics_pipeline.validate import validate_sources


DEFAULT_ARGS = {
    "owner": "analytics-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
}


@dag(
    dag_id="supply_chain_raw_to_mart",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["portfolio", "supply-chain", "data-quality"],
)
def supply_chain_raw_to_mart():
    @task
    def preflight(input_dir: str) -> dict[str, int]:
        sources = ingest_sources(Path(input_dir))
        validate_sources(sources)
        return {name: len(frame) for name, frame in sources.items()}

    @task
    def execute_pipeline(_: dict[str, int]) -> dict[str, object]:
        result = run_pipeline(
            PipelineConfig.from_strings("data/raw", "data/published", "runs")
        )
        if result.status != "SUCCESS":
            raise AirflowFailException("Shared pipeline did not complete successfully.")
        return {
            "run_id": result.run_id,
            "metadata_path": result.metadata_path,
            "idempotent_same_as_previous": result.skipped_publish,
        }

    execute_pipeline(preflight("data/raw"))


supply_chain_raw_to_mart()
