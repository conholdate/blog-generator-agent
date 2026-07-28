from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Provider-agnostic interface: every pipeline stage that calls an LLM
    asks for a schema-validated response, never free-form text, so the
    provider behind it (Anthropic, OpenAI, ...) is an implementation detail.
    """

    def __init__(self) -> None:
        # Cumulative usage across every complete_structured() call made on this
        # client instance, read by the orchestrator to report per-topic metrics.
        self.api_calls: int = 0
        self.total_tokens: int = 0

    def _record_usage(self, tokens: int) -> None:
        self.api_calls += 1
        self.total_tokens += max(0, tokens)

    @abstractmethod
    def complete_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        """Send a system/user prompt pair and return a response validated against `schema`."""
        raise NotImplementedError
