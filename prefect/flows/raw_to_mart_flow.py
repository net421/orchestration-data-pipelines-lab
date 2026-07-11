"""Prefect flow using the same shared analytics pipeline."""
from pathlib import Path

from prefect import flow, get_run_logger, task

from analytics_pipeline.config import PipelineConfig
from analytics_pipeline.ingest import ingest_sources
from analytics_pipeline.pipeline import run_pipeline
from analytics_pipeline.validate import validate_sources


@task(retries=2, retry_delay_seconds=[5, 15], cache_policy=None)
def validate_inputs(input_dir: str) -> dict[str, int]:
    sources = ingest_sources(Path(input_dir))
    validate_sources(sources)
    return {name: len(frame) for name, frame in sources.items()}


@task(retries=1, retry_delay_seconds=10)
def execute_shared_pipeline(_: dict[str, int]) -> dict[str, object]:
    result = run_pipeline(
        PipelineConfig.from_strings("data/raw", "data/published", "runs")
    )
    return {
        "run_id": result.run_id,
        "status": result.status,
        "metadata_path": result.metadata_path,
        "idempotent_same_as_previous": result.skipped_publish,
    }


@flow(name="supply-chain-raw-to-mart", log_prints=True)
def raw_to_mart_flow() -> dict[str, object]:
    logger = get_run_logger()
    result = execute_shared_pipeline(validate_inputs("data/raw"))
    logger.info("Published run metadata at %s", result["metadata_path"])
    return result


if __name__ == "__main__":
    raw_to_mart_flow()
