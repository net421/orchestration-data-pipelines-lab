from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int = 3,
    base_delay_seconds: float = 0.1,
    retry_on: tuple[type[BaseException], ...] = (OSError,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Bounded exponential retry for transient I/O operations."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_error = exc
                    if attempt == attempts:
                        raise
                    time.sleep(base_delay_seconds * (2 ** (attempt - 1)))
            assert last_error is not None
            raise last_error

        return wrapped

    return decorator
