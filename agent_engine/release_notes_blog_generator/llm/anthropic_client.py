from __future__ import annotations

import logging
import time
from typing import TypeVar

from anthropic import Anthropic
from pydantic import BaseModel

from .base import LLMClient
from .retry import call_with_retries

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__()
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        # Force the schema via a single tool call rather than parsing free text,
        # since Claude has no native "response_format" JSON-schema mode.
        tool_name = f"emit_{schema.__name__.lower()}"
        logger.debug("Calling Anthropic (model=%s) for %s...", self._model, schema.__name__)
        started = time.perf_counter()

        def _call():
            return self._client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[
                    {
                        "name": tool_name,
                        "description": f"Return the extracted data as {schema.__name__}.",
                        "input_schema": schema.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
            )

        response = call_with_retries(_call, label=f"Anthropic {schema.__name__}")
        logger.debug("Anthropic call for %s finished in %.1fs", schema.__name__, time.perf_counter() - started)
        usage = getattr(response, "usage", None)
        self._record_usage(getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0) if usage else 0)
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return schema.model_validate(block.input)
        raise ValueError("Anthropic response did not include the expected tool call")
