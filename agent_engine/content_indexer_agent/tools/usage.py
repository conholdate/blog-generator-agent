from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _coerce_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _extract_total_tokens(resp: Any) -> int:
    usage = getattr(resp, "usage", None)
    if usage is None and isinstance(resp, dict):
        usage = resp.get("usage")
    if usage is None:
        return 0

    total_tokens = getattr(usage, "total_tokens", None)
    if total_tokens is None and isinstance(usage, dict):
        total_tokens = usage.get("total_tokens")
    if total_tokens is not None:
        return _coerce_int(total_tokens)

    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    if isinstance(usage, dict):
        input_tokens = usage.get("input_tokens", input_tokens)
        output_tokens = usage.get("output_tokens", output_tokens)
    return _coerce_int(input_tokens) + _coerce_int(output_tokens)


@dataclass
class UsageAccumulator:
    token_usage: int = 0
    api_call_count: int = 0

    def record_response(self, resp: Any) -> None:
        self.api_call_count += 1
        self.token_usage += _extract_total_tokens(resp)

    def snapshot(self) -> dict[str, int]:
        return {
            "token_usage": int(self.token_usage),
            "api_calls_count": int(self.api_call_count),
        }
