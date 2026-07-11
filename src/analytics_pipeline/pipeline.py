from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import uuid

import pandas as pd

from .config import PipelineConfig
from .ingest import ingest_sources
from .logging_utils import configure_logging
from .publish import atomic_write_csv, write_json
from .transform import (
    build_carrier_scorecard,
    build_daily_service_metrics,
    build_order_service_detail,
)
from .validate import validate_outputs, validate_sources


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    status: str
    output_files: tuple[str, ...]
    metadata_path: str
    skipped_publish: bool


def _log(logger: logging.Logger, message: str, **extra: object) -> None:
    logger.info(message, extra=extra)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_pipeline(config: PipelineConfig, run_id: str | None = None) -> PipelineResult:
    logger = configure_logging()
    run_id = run_id or _utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    started = _utc_now()
    run_path = config.run_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    stage = "start"

    _log(logger, "pipeline_started", run_id=run_id, stage=stage, status="RUNNING")

    try:
        stage = "ingest"
        sources = ingest_sources(config.input_dir)
        _log(
            logger,
            "sources_ingested",
            run_id=run_id,
            stage=stage,
            row_count=sum(len(frame) for frame in sources.values()),
            status="SUCCESS",
        )

        stage = "validate_sources"
        source_checks = validate_sources(sources)
        _log(logger, "source_contracts_validated", run_id=run_id, stage=stage, status="SUCCESS")

        stage = "transform"
        detail = build_order_service_detail(sources["orders"], sources["shipments"])
        daily = build_daily_service_metrics(detail)
        carriers = build_carrier_scorecard(detail)
        _log(
            logger,
            "marts_built",
            run_id=run_id,
            stage=stage,
            row_count=len(detail) + len(daily) + len(carriers),
            status="SUCCESS",
        )

        stage = "validate_outputs"
        output_checks = validate_outputs(detail, daily, carriers)
        quality = pd.DataFrame(source_checks + output_checks)

        stage = "publish"
        artifacts = {
            "order_service_detail.csv": detail,
            "daily_service_metrics.csv": daily,
            "carrier_scorecard.csv": carriers,
            "data_quality_report.csv": quality,
        }
        published = [
            atomic_write_csv(frame, config.output_dir / filename)
            for filename, frame in artifacts.items()
        ]

        prior_latest = config.run_dir / "latest.json"
        previous_hashes: dict[str, str] = {}
        if prior_latest.exists():
            previous = json.loads(prior_latest.read_text(encoding="utf-8"))
            previous_hashes = {
                Path(item["path"]).name: item["sha256"]
                for item in previous.get("published_artifacts", [])
            }
        current_hashes = {Path(item["path"]).name: item["sha256"] for item in published}
        skipped_publish = bool(previous_hashes) and previous_hashes == current_hashes

        completed = _utc_now()
        metadata = {
            "run_id": run_id,
            "status": "SUCCESS",
            "started_at_utc": started.isoformat(),
            "completed_at_utc": completed.isoformat(),
            "duration_seconds": round((completed - started).total_seconds(), 6),
            "input_rows": {name: int(len(frame)) for name, frame in sources.items()},
            "published_artifacts": published,
            "quality_checks": source_checks + output_checks,
            "idempotent_same_as_previous": skipped_publish,
        }
        metadata_path = run_path / "run_metadata.json"
        write_json(metadata, metadata_path)
        write_json(metadata, prior_latest)

        _log(logger, "pipeline_completed", run_id=run_id, stage="complete", status="SUCCESS")
        return PipelineResult(
            run_id=run_id,
            status="SUCCESS",
            output_files=tuple(item["path"] for item in published),
            metadata_path=str(metadata_path),
            skipped_publish=skipped_publish,
        )
    except Exception as exc:
        completed = _utc_now()
        failure_metadata = {
            "run_id": run_id,
            "status": "FAILED",
            "failed_stage": stage,
            "started_at_utc": started.isoformat(),
            "completed_at_utc": completed.isoformat(),
            "duration_seconds": round((completed - started).total_seconds(), 6),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        metadata_path = run_path / "run_metadata.json"
        write_json(failure_metadata, metadata_path)
        write_json(failure_metadata, config.run_dir / "latest_failure.json")
        _log(
            logger,
            "pipeline_failed",
            run_id=run_id,
            stage=stage,
            status="FAILED",
        )
        raise
