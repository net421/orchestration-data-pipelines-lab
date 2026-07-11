"""Dagster software-defined assets for the shared analytics pipeline."""
from pathlib import Path

from dagster import AssetCheckResult, asset, asset_check

from analytics_pipeline.config import PipelineConfig
from analytics_pipeline.ingest import ingest_sources
from analytics_pipeline.pipeline import run_pipeline
from analytics_pipeline.validate import validate_sources


@asset(group_name="supply_chain")
def validated_sources() -> dict[str, int]:
    sources = ingest_sources(Path("data/raw"))
    validate_sources(sources)
    return {name: len(frame) for name, frame in sources.items()}


@asset(group_name="supply_chain", deps=[validated_sources])
def published_supply_chain_marts() -> dict[str, object]:
    result = run_pipeline(
        PipelineConfig.from_strings("data/raw", "data/published", "runs")
    )
    return {
        "run_id": result.run_id,
        "status": result.status,
        "metadata_path": result.metadata_path,
    }


@asset_check(asset=published_supply_chain_marts)
def published_marts_succeeded(
    published_supply_chain_marts: dict[str, object],
) -> AssetCheckResult:
    return AssetCheckResult(
        passed=published_supply_chain_marts["status"] == "SUCCESS",
        metadata=published_supply_chain_marts,
    )
