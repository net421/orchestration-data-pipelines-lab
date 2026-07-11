from pathlib import Path
import json
import shutil

import pandas as pd
import pytest

from analytics_pipeline.config import PipelineConfig
from analytics_pipeline.errors import DataContractError
from analytics_pipeline.pipeline import run_pipeline
from analytics_pipeline.retry import retry
from analytics_pipeline.validate import validate_sources


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_is_idempotent(tmp_path: Path) -> None:
    config = PipelineConfig(
        input_dir=REPO_ROOT / "data" / "raw",
        output_dir=tmp_path / "published",
        run_dir=tmp_path / "runs",
    )
    first = run_pipeline(config, run_id="test-run-1")
    first_bytes = {
        path.name: path.read_bytes()
        for path in sorted((tmp_path / "published").glob("*.csv"))
    }
    second = run_pipeline(config, run_id="test-run-2")
    second_bytes = {
        path.name: path.read_bytes()
        for path in sorted((tmp_path / "published").glob("*.csv"))
    }

    assert first.status == "SUCCESS"
    assert second.status == "SUCCESS"
    assert first.skipped_publish is False
    assert second.skipped_publish is True
    assert first_bytes == second_bytes
    assert first_bytes and all(first_bytes.values())


def test_contract_rejects_missing_column() -> None:
    orders = pd.read_csv(REPO_ROOT / "data" / "raw" / "erp_order_lines.csv").drop(
        columns=["units_ordered"]
    )
    shipments = pd.read_csv(REPO_ROOT / "data" / "raw" / "tms_shipments.csv")
    with pytest.raises(DataContractError, match="units_ordered"):
        validate_sources({"orders": orders, "shipments": shipments})


def test_failed_contract_preserves_outputs_and_writes_failure_metadata(tmp_path: Path) -> None:
    input_dir = tmp_path / "raw"
    shutil.copytree(REPO_ROOT / "data" / "raw", input_dir)
    config = PipelineConfig(input_dir, tmp_path / "published", tmp_path / "runs")
    run_pipeline(config, run_id="successful-run")
    before = {path.name: path.read_bytes() for path in config.output_dir.glob("*.csv")}

    orders_path = input_dir / "erp_order_lines.csv"
    orders = pd.read_csv(orders_path)
    orders.drop(columns=["units_ordered"]).to_csv(orders_path, index=False)

    with pytest.raises(DataContractError, match="units_ordered"):
        run_pipeline(config, run_id="failed-run")

    after = {path.name: path.read_bytes() for path in config.output_dir.glob("*.csv")}
    failure = json.loads((config.run_dir / "failed-run" / "run_metadata.json").read_text())
    latest = json.loads((config.run_dir / "latest.json").read_text())

    assert before == after
    assert failure["status"] == "FAILED"
    assert failure["failed_stage"] == "validate_sources"
    assert latest["run_id"] == "successful-run"

    orders.to_csv(orders_path, index=False)
    recovery = run_pipeline(config, run_id="recovery-run")
    assert recovery.status == "SUCCESS"
    assert recovery.skipped_publish is True


def test_retry_recovers_from_transient_failure() -> None:
    attempts = {"count": 0}

    @retry(attempts=3, base_delay_seconds=0, retry_on=(OSError,))
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise OSError("temporary")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 3
