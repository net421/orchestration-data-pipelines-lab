class PipelineError(Exception):
    """Base pipeline exception."""


class DataContractError(PipelineError):
    """Raised when an input violates its declared contract."""


class PublishError(PipelineError):
    """Raised when atomic publication cannot be completed."""
