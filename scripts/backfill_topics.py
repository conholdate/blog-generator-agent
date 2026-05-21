from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_engine.content_indexer_agent.tools.key_maker import build_content_topic


def _default_output_path(input_path: Path) -> Path:
    if input_path.suffix:
        return input_path.with_name(f"{input_path.stem}-updated{input_path.suffix}")
    return input_path.with_name(f"{input_path.name}-updated")


def _updated_row(row: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(row)
    title = str(updated.get("title") or "").strip()
    url = str(updated.get("url") or "").strip() or None
    topic = str(updated.get("topic") or "").strip() or None

    updated["topic"] = build_content_topic(
        title=title,
        url=url,
        llm_topic=topic,
    )
    return updated


def backfill_topics(input_path: Path, output_path: Path) -> tuple[int, int]:
    rows = 0
    changed = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line_no, line in enumerate(src, start=1):
            raw = line.strip()
            if not raw:
                continue

            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no} in {input_path}: {exc}") from exc

            updated = _updated_row(row)
            if updated.get("topic") != row.get("topic"):
                changed += 1

            dst.write(json.dumps(updated, ensure_ascii=False) + "\n")
            rows += 1

    return rows, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill normalized topic values in an existing JSONL index and write a sibling *-updated.jsonl file."
    )
    parser.add_argument("input_jsonl", help="Path to the existing JSONL file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional explicit output path. Defaults to a sibling *-updated.jsonl file.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_jsonl).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {input_path}")

    output_path = Path(args.output).expanduser().resolve() if args.output else _default_output_path(input_path)
    rows, changed = backfill_topics(input_path, output_path)
    print(f"Wrote {rows} rows to {output_path} ({changed} topic updates)")


if __name__ == "__main__":
    main()
