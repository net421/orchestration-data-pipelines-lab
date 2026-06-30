"""Validation-first local orchestration simulator.

This module is intentionally framework-light so portfolio reviewers can run it
without installing Airflow, Prefect, or Dagster. It models the orchestration
contract those tools would enforce: task dependency order, retry policy,
deterministic validation gates, lineage metadata, and publish-ready output.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

try:
    from shared.error_handling import (
        PipelineValidationError,
        require_columns,
        require_no_nulls,
        require_positive_row_count,
        require_unique_key,
    )
    from shared.pipeline_logging import get_logger, log_event
except ModuleNotFoundError:
    from error_handling import (
        PipelineValidationError,
        require_columns,
        require_no_nulls,
        require_positive_row_count,
        require_unique_key,
    )
    from pipeline_logging import get_logger, log_event


LOGGER = get_logger("local_orchestration_simulator")


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    depends_on: tuple[str, ...]
    callable_name: str
    retries: int = 0
    retryable: bool = False


@dataclass
class TaskRun:
    task_id: str
    status: str
    attempts: int
    row_count: int = 0
    message: str = ""


@dataclass
class PipelineContext:
    run_id: str
    raw_orders: list[dict] = field(default_factory=list)
    clean_orders: list[dict] = field(default_factory=list)
    mart_orders: list[dict] = field(default_factory=list)
    quality_results: list[dict] = field(default_factory=list)
    task_runs: list[TaskRun] = field(default_factory=list)


RAW_ORDERS = [
    {
        "order_id": "1001",
        "customer_id": "C001",
        "order_date": "2026-01-01",
        "promised_date": "2026-01-05",
        "units_ordered": "10",
        "units_shipped": "10",
        "revenue": "500",
    },
    {
        "order_id": "1002",
        "customer_id": "C002",
        "order_date": "2026-01-02",
        "promised_date": "2026-01-06",
        "units_ordered": "20",
        "units_shipped": "18",
        "revenue": "800",
    },
    {
        "order_id": "1003",
        "customer_id": "C001",
        "order_date": "2026-01-03",
        "promised_date": "2026-01-07",
        "units_ordered": "15",
        "units_shipped": "15",
        "revenue": "600",
    },
]


TASK_GRAPH = [
    TaskSpec("extract_raw_orders", (), "extract_raw_orders", retries=2, retryable=True),
    TaskSpec("validate_raw_orders", ("extract_raw_orders",), "validate_raw_orders"),
    TaskSpec("clean_orders", ("validate_raw_orders",), "clean_orders"),
    TaskSpec("validate_clean_orders", ("clean_orders",), "validate_clean_orders"),
    TaskSpec("build_order_mart", ("validate_clean_orders",), "build_order_mart"),
    TaskSpec("publish_quality_summary", ("build_order_mart",), "publish_quality_summary"),
]


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def extract_raw_orders(context: PipelineContext) -> int:
    context.raw_orders = [dict(row) for row in RAW_ORDERS]
    return len(context.raw_orders)


def validate_raw_orders(context: PipelineContext) -> int:
    require_positive_row_count(len(context.raw_orders), "raw_orders")
    required_columns = {
        "order_id",
        "customer_id",
        "order_date",
        "promised_date",
        "units_ordered",
        "units_shipped",
        "revenue",
    }
    for row in context.raw_orders:
        require_columns(row, required_columns, "raw_orders")
    require_no_nulls(context.raw_orders, required_columns, "raw_orders")
    require_unique_key(context.raw_orders, "order_id", "raw_orders")
    context.quality_results.append({"check": "raw_orders_contract", "failing_rows": 0})
    return len(context.raw_orders)


def clean_orders(context: PipelineContext) -> int:
    cleaned = []
    for row in context.raw_orders:
        order_date = parse_iso_date(row["order_date"])
        promised_date = parse_iso_date(row["promised_date"])
        units_ordered = int(row["units_ordered"])
        units_shipped = int(row["units_shipped"])
        revenue = float(row["revenue"])
        cleaned.append(
            {
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "order_date": order_date.isoformat(),
                "promised_date": promised_date.isoformat(),
                "units_ordered": units_ordered,
                "units_shipped": units_shipped,
                "revenue": revenue,
                "fill_rate": round(units_shipped / units_ordered, 4) if units_ordered else 0,
            }
        )
    context.clean_orders = cleaned
    return len(context.clean_orders)


def validate_clean_orders(context: PipelineContext) -> int:
    failures = []
    for row in context.clean_orders:
        if row["units_ordered"] < 0 or row["units_shipped"] < 0:
            failures.append(row["order_id"])
        if row["units_shipped"] > row["units_ordered"]:
            failures.append(row["order_id"])
        if parse_iso_date(row["promised_date"]) < parse_iso_date(row["order_date"]):
            failures.append(row["order_id"])
    if failures:
        raise PipelineValidationError(f"clean_orders failed deterministic checks: {failures}")
    context.quality_results.append({"check": "clean_orders_values", "failing_rows": 0})
    return len(context.clean_orders)


def build_order_mart(context: PipelineContext) -> int:
    context.mart_orders = [
        {
            **row,
            "in_full": row["units_shipped"] >= row["units_ordered"],
            "backorder_units": max(row["units_ordered"] - row["units_shipped"], 0),
            "service_exception": row["units_shipped"] < row["units_ordered"],
        }
        for row in context.clean_orders
    ]
    require_positive_row_count(len(context.mart_orders), "mart_orders")
    context.quality_results.append({"check": "mart_orders_row_count", "failing_rows": 0})
    return len(context.mart_orders)


def publish_quality_summary(context: PipelineContext) -> int:
    summary = {
        "orders": len(context.mart_orders),
        "fill_rate": round(
            sum(row["units_shipped"] for row in context.mart_orders)
            / sum(row["units_ordered"] for row in context.mart_orders),
            4,
        ),
        "service_exceptions": sum(1 for row in context.mart_orders if row["service_exception"]),
        "quality_checks": len(context.quality_results) + 1,
    }
    context.quality_results.append({"check": "publish_summary", "failing_rows": 0, "summary": summary})
    return len(context.quality_results)


TASK_FUNCTIONS: dict[str, Callable[[PipelineContext], int]] = {
    "extract_raw_orders": extract_raw_orders,
    "validate_raw_orders": validate_raw_orders,
    "clean_orders": clean_orders,
    "validate_clean_orders": validate_clean_orders,
    "build_order_mart": build_order_mart,
    "publish_quality_summary": publish_quality_summary,
}


def run_task(task: TaskSpec, context: PipelineContext, completed_tasks: set[str]) -> None:
    missing_dependencies = [dependency for dependency in task.depends_on if dependency not in completed_tasks]
    if missing_dependencies:
        raise PipelineValidationError(
            f"{task.task_id} missing dependencies: {', '.join(missing_dependencies)}"
        )

    attempts = 0
    max_attempts = task.retries + 1
    while attempts < max_attempts:
        attempts += 1
        try:
            log_event(LOGGER, "task_start", task_id=task.task_id, attempt=attempts)
            row_count = TASK_FUNCTIONS[task.callable_name](context)
            context.task_runs.append(TaskRun(task.task_id, "success", attempts, row_count))
            completed_tasks.add(task.task_id)
            log_event(LOGGER, "task_success", task_id=task.task_id, rows=row_count, attempts=attempts)
            return
        except PipelineValidationError as exc:
            context.task_runs.append(TaskRun(task.task_id, "failed", attempts, message=str(exc)))
            log_event(LOGGER, "task_validation_failed", task_id=task.task_id, attempt=attempts, error=str(exc))
            raise
        except Exception as exc:
            context.task_runs.append(TaskRun(task.task_id, "retryable_failed", attempts, message=str(exc)))
            log_event(LOGGER, "task_retryable_failed", task_id=task.task_id, attempt=attempts, error=str(exc))
            if not task.retryable or attempts >= max_attempts:
                raise
            time.sleep(0.01)


def summarize_context(context: PipelineContext) -> dict:
    last_quality = context.quality_results[-1] if context.quality_results else {}
    return {
        "run_id": context.run_id,
        "task_count": len(TASK_GRAPH),
        "successful_tasks": sum(1 for task_run in context.task_runs if task_run.status == "success"),
        "quality_checks": len(context.quality_results),
        "mart_rows": len(context.mart_orders),
        "summary": last_quality.get("summary", {}),
        "lineage": {
            "raw": "RAW_ORDERS",
            "clean": "clean_orders",
            "mart": "mart_orders",
            "quality": "quality_results",
        },
    }


def run_pipeline(run_id: str = "local-validation-run") -> dict:
    context = PipelineContext(run_id=run_id)
    completed_tasks: set[str] = set()
    for task in TASK_GRAPH:
        run_task(task, context, completed_tasks)
    return summarize_context(context)


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2, sort_keys=True))
