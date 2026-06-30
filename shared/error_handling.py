class PipelineValidationError(Exception):
    """Raised when a pipeline validation check fails."""


def require_positive_row_count(row_count: int) -> None:
    if row_count <= 0:
        raise PipelineValidationError("Expected positive row count")
