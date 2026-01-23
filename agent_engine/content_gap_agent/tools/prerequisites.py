from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class PrereqSpec:
    case: str
    required_paths: List[Path]
    optional_any_of: List[Path] | None = None  # at least one must exist


class PrerequisiteError(RuntimeError):
    pass


def ensure_prerequisites(
    outputs_product_root: Path,
    case: str,
    baseline_platform: str,
) -> None:
    """
    Enforces the runtime prerequisites described in the plan.
    """
    indexes_root = outputs_product_root / "indexes"

    specs: dict[str, PrereqSpec] = {
        "blogs_to_blogs": PrereqSpec(
            case="blogs_to_blogs",
            required_paths=[indexes_root / "blog" / "all.jsonl"],
        ),
        "docs_to_blogs": PrereqSpec(
            case="docs_to_blogs",
            required_paths=[
                indexes_root / "docs" / f"{baseline_platform}.jsonl",
                indexes_root / "blog" / "all.jsonl",
            ],
        ),
        "docs_to_tutorials": PrereqSpec(
            case="docs_to_tutorials",
            required_paths=[
                indexes_root / "docs" / f"{baseline_platform}.jsonl",
                indexes_root / "tutorials" / f"{baseline_platform}.jsonl",
            ],
        ),
        "api_coverage": PrereqSpec(
            case="api_coverage",
            required_paths=[indexes_root / "api" / f"{baseline_platform}.jsonl"],
            optional_any_of=[
                indexes_root / "docs" / f"{baseline_platform}.jsonl",
                indexes_root / "tutorials" / f"{baseline_platform}.jsonl",
                indexes_root / "blog" / "all.jsonl",
            ],
        ),
    }

    if case not in specs:
        raise PrerequisiteError(
            f"Unknown case '{case}'. Valid cases: {', '.join(sorted(specs.keys()))}"
        )

    spec = specs[case]

    missing = [p for p in spec.required_paths if not p.exists()]
    if missing:
        missing_str = "\n".join(f"- {p}" for p in missing)
        raise PrerequisiteError(
            "Missing prerequisite index files:\n"
            f"{missing_str}\n\n"
            "Run the indexing pipeline for the missing step(s) first."
        )

    if spec.optional_any_of:
        if not any(p.exists() for p in spec.optional_any_of):
            any_of_str = "\n".join(f"- {p}" for p in spec.optional_any_of)
            raise PrerequisiteError(
                "Missing prerequisite indexes for api_coverage.\n"
                "Expected at least one of:\n"
                f"{any_of_str}\n\n"
                "Run indexing for docs/tutorials/blogs first."
            )
