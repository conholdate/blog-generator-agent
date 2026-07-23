from __future__ import annotations

import json
import logging
import re
import time
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from .base import LLMClient
from .retry import call_with_retries

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ProfessionalizeClient(LLMClient):
    """Client for the in-house 'professionalize' gateway: an OpenAI-compatible
    Chat Completions API at a custom base_url, fronting an open-weight model
    (e.g. gpt-oss).

    Unlike OpenAIClient, this does not use `beta.chat.completions.parse()`.
    That convenience wrapper assumes the backend honors OpenAI's strict
    structured-outputs contract (`additionalProperties: false`, every field
    forced required); a self-hosted gateway may not enforce that. Instead
    this sends a plain `response_format: json_schema` request plus an
    explicit instruction, and parses the returned text itself — tolerating
    a model that wraps its JSON in markdown fences.
    """

    def __init__(self, base_url: str, api_key: str, model: str, max_tokens: int = 16384) -> None:
        super().__init__()
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def complete_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        schema_instructions = (
            "Respond with a single JSON object only - no markdown fences, no "
            "commentary before or after it - that matches this JSON schema:\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        logger.debug("Calling professionalize (model=%s) for %s...", self._model, schema.__name__)
        started = time.perf_counter()

        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": f"{system}\n\n{schema_instructions}"},
                    {"role": "user", "content": user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
                },
            )

        completion = call_with_retries(_call, label=f"professionalize {schema.__name__}")
        logger.debug("professionalize call for %s finished in %.1fs", schema.__name__, time.perf_counter() - started)
        usage = getattr(completion, "usage", None)
        self._record_usage(getattr(usage, "total_tokens", 0) if usage else 0)
        choice = completion.choices[0]
        if choice.finish_reason == "length":
            raise ValueError(
                f"Professionalize response was truncated before completing (max_tokens={self._max_tokens}); "
                "increase max_tokens or shorten the input."
            )
        content = choice.message.content
        if not content:
            raise ValueError("Professionalize response had no content")
        return schema.model_validate_json(_extract_json(content))


def _extract_json(content: str) -> str:
    match = _JSON_FENCE_PATTERN.search(content)
    return match.group(1) if match else content
