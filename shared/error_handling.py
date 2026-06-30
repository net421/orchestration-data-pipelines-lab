"""Reusable validation helpers for pipeline orchestration examples."""


class PipelineValidationError(Exception):
    """Raised when a deterministic pipeline validation check fails."""


def require_positive_row_count(row_count: int, dataset_name: str = "dataset") -> None:
    if row_count <= 0:
        raise PipelineValidationError(f"{dataset_name} expected positive row count")


def require_columns(row: dict, required_columns: set[str], dataset_name: str) -> None:
    missing_columns = sorted(required_columns - set(row))
    if missing_columns:
        raise PipelineValidationError(
            f"{dataset_name} missing required columns: {', '.join(missing_columns)}"
        )


def require_no_nulls(rows: list[dict], required_columns: set[str], dataset_name: str) -> None:
    failing = []
    for index, row in enumerate(rows, start=1):
        for column in required_columns:
            if row.get(column) in {None, ""}:
                failing.append(f"row {index} column {column}")
    if failing:
        raise PipelineValidationError(
            f"{dataset_name} null check failed: {'; '.join(failing[:5])}"
        )


def require_unique_key(rows: list[dict], key: str, dataset_name: str) -> None:
    seen = set()
    duplicates = set()
    for row in rows:
        value = row.get(key)
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise PipelineValidationError(
            f"{dataset_name} duplicate {key} values: {', '.join(sorted(map(str, duplicates)))}"
        )
