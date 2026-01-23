from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple, List
import logging

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CoverageKeyValidationResult:
    cleaned: Dict[str, Any]
    unknown_keys: List[str]


def validate_and_clean_coverage_keys(
    coverage: Dict[str, Any],
    allowed_platform_keys: Iterable[str],
) -> CoverageKeyValidationResult:
    allowed = set(allowed_platform_keys)
    cleaned: Dict[str, Any] = {}
    unknown: List[str] = []

    for k, v in (coverage or {}).items():
        if k in allowed:
            cleaned[k] = v
        else:
            unknown.append(str(k))

    return CoverageKeyValidationResult(cleaned=cleaned, unknown_keys=unknown)


def log_unknown_coverage_keys(unknown_keys: List[str], context: str, sample_n: int = 20) -> None:
    if not unknown_keys:
        return
    sample = unknown_keys[:sample_n]
    log.warning(
        "Unknown coverage keys detected (%s). count=%d sample=%s",
        context,
        len(unknown_keys),
        sample,
    )
