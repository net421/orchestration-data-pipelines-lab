"""Execute success, idempotency, deterministic failure, and recovery scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import pandas as pd

from analytics_pipeline.config import PipelineConfig
from analytics_pipeline.errors import DataContractError
from analytics_pipeline.pipeline import run_pipeline


REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def output_hashes(output_dir: Path) -> dict[str, str]:
    return {path.name: sha256(path) for path in sorted(output_dir.glob("*.csv"))}


def execute_scenarios(report_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="orchestration-validation-") as temp:
        root = Path(temp)
        input_dir = root / "raw"
        output_dir = root / "published"
        run_dir = root / "runs"
        shutil.copytree(REPO_ROOT / "data" / "raw", input_dir)
        config = PipelineConfig(input_dir=input_dir, output_dir=output_dir, run_dir=run_dir)

        first = run_pipeline(config, run_id="scenario-success-1")
        hashes_after_first = output_hashes(output_dir)
        second = run_pipeline(config, run_id="scenario-success-2")
        hashes_after_second = output_hashes(output_dir)

        orders_path = input_dir / "erp_order_lines.csv"
        clean_orders = pd.read_csv(orders_path)
        clean_orders.drop(columns=["units_ordered"]).to_csv(orders_path, index=False)

        failure_message = ""
        try:
            run_pipeline(config, run_id="scenario-contract-failure")
        except DataContractError as exc:
            failure_message = str(exc)
        else:
            raise AssertionError("The deterministic contract failure was not detected.")

        hashes_after_failure = output_hashes(output_dir)
        failure_metadata = json.loads(
            (run_dir / "scenario-contract-failure" / "run_metadata.json").read_text(encoding="utf-8")
        )
        latest_success = json.loads((run_dir / "latest.json").read_text(encoding="utf-8"))

        clean_orders.to_csv(orders_path, index=False)
        recovery = run_pipeline(config, run_id="scenario-recovery")
        hashes_after_recovery = output_hashes(output_dir)

        assert first.status == "SUCCESS"
        assert second.status == "SUCCESS" and second.skipped_publish is True
        assert hashes_after_first == hashes_after_second
        assert hashes_after_second == hashes_after_failure
        assert hashes_after_failure == hashes_after_recovery
        assert failure_metadata["status"] == "FAILED"
        assert failure_metadata["failed_stage"] == "validate_sources"
        assert latest_success["run_id"] == "scenario-success-2"
        assert recovery.status == "SUCCESS" and recovery.skipped_publish is True

        report = {
            "status": "PASS",
            "scenarios": {
                "initial_success": first.__dict__,
                "idempotent_rerun": second.__dict__,
                "deterministic_contract_failure": {
                    "status": failure_metadata["status"],
                    "failed_stage": failure_metadata["failed_stage"],
                    "error_type": failure_metadata["error_type"],
                    "error_message": failure_message,
                    "published_outputs_unchanged": hashes_after_second == hashes_after_failure,
                    "latest_success_pointer_preserved": latest_success["run_id"] == "scenario-success-2",
                },
                "recovery": recovery.__dict__,
            },
            "published_artifact_hashes": hashes_after_recovery,
        }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-path",
        default="validation/generated/scenario_report.json",
    )
    args = parser.parse_args()
    report = execute_scenarios(Path(args.report_path))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
