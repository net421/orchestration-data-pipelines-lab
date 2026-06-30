"""Prefect-style flow example for analytics pipeline orchestration."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from prefect import flow, task
except Exception:
    def task(fn=None, **_kwargs):
        if fn is None:
            return lambda wrapped: wrapped
        return fn

    def flow(fn=None, **_kwargs):
        if fn is None:
            return lambda wrapped: wrapped
        return fn

from shared.local_pipeline_simulator import run_pipeline


@task(retries=2, retry_delay_seconds=30)
def ingest_raw_task():
    return "ingest_raw"


@task
def validate_clean_task(_upstream_task_id):
    return "validate_clean"


@task
def build_marts_task(_upstream_task_id):
    return "build_marts"


@task
def publish_report_task(_upstream_task_id):
    return "publish_report"


@flow(name="raw-to-mart-validation-first")
def raw_to_mart_flow():
    raw = ingest_raw_task()
    clean = validate_clean_task(raw)
    mart = build_marts_task(clean)
    publish_report_task(mart)
    return run_pipeline()


if __name__ == "__main__":
    print(raw_to_mart_flow())
