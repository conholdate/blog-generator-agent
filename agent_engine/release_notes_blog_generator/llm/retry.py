from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY_SECONDS = 2.0


def call_with_retries(
    fn: Callable[[], T],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay_seconds: float = DEFAULT_BASE_DELAY_SECONDS,
    retryable: tuple[type[BaseException], ...] = (Exception,),
    label: str = "LLM call",
) -> T:
    """Retries `fn` with exponential backoff on transient failures.

    Each LLM client previously made its API call exactly once, so a single
    timeout or rate-limit response aborted the whole pipeline run. This wraps
    just the network call (not response parsing/validation) with bounded
    retries so transient errors self-heal instead of failing the run.
    """
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retryable as exc:  # noqa: BLE001 - callers narrow via `retryable`
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "%s failed (attempt %d/%d): %s: %s - retrying in %.1fs",
                label, attempt, max_attempts, type(exc).__name__, exc, delay,
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
