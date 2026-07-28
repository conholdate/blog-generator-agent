from __future__ import annotations

import logging
import time
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from .base import LLMClient
from .retry import call_with_retries

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str, max_tokens: int = 16384) -> None:
        super().__init__()
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def complete_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        logger.debug("Calling OpenAI (model=%s) for %s...", self._model, schema.__name__)
        started = time.perf_counter()

        def _call():
            return self._client.beta.chat.completions.parse(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=schema,
            )

        completion = call_with_retries(_call, label=f"OpenAI {schema.__name__}")
        logger.debug("OpenAI call for %s finished in %.1fs", schema.__name__, time.perf_counter() - started)
        usage = getattr(completion, "usage", None)
        self._record_usage(getattr(usage, "total_tokens", 0) if usage else 0)
        choice = completion.choices[0]
        if choice.finish_reason == "length":
            raise ValueError(
                f"OpenAI response was truncated before completing (max_tokens={self._max_tokens}); "
                "increase max_tokens or shorten the input."
            )
        if choice.message.parsed is None:
            raise ValueError("OpenAI response could not be parsed against the schema")
        return choice.message.parsed
