from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_engine.content_gap_agent.tools.coverage.blogs_to_blogs import compute_blogs_to_blogs
from agent_engine.content_gap_agent.tools.coverage.docs_to_blogs import compute_docs_to_blogs
from agent_engine.content_gap_agent.tools.coverage.docs_to_tutorials import compute_docs_to_tutorials


def _disable_external_side_effects() -> None:
    """
    Evaluation must be offline and side-effect free. These env vars protect the
    script if it later grows an integration path that calls the full agent.
    """
    os.environ["METRICS_ENABLED"] = "false"
    os.environ["CG_SKIP_SHEETS_AUTO_POST"] = "true"


@dataclass(frozen=True)
class ScenarioMetrics:
    scenario: str
    case: str
    expected_cells: int
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    exact_matches: int
    lexical_matches: int

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else 1.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else 1.0

    @property
    def f1(self) -> float:
        denom = self.precision + self.recall
        return 2 * self.precision * self.recall / denom if denom else 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "case": self.case,
            "expected_cells": self.expected_cells,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "true_positive": self.true_positive,
            "false_positive": self.false_positive,
            "true_negative": self.true_negative,
            "false_negative": self.false_negative,
            "exact_matches": self.exact_matches,
            "lexical_matches": self.lexical_matches,
        }


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _scenario_dirs(fixtures_root: Path) -> list[Path]:
    return sorted(path.parent for path in fixtures_root.rglob("scenario.json"))


def _compute_result(scenario_dir: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    _disable_external_side_effects()
    case = str(scenario["case"])
    params = scenario.get("params") or {}
    common = {
        "brand_key": str(scenario.get("brand_key") or "fixture"),
        "product_key": str(scenario.get("product_key") or "fixture"),
        "outputs_product_root": scenario_dir,
    }

    if case == "blogs_to_blogs":
        result = compute_blogs_to_blogs(
            **common,
            baseline_platform=params.get("baseline_platform"),
            platforms_limit=params.get("platforms_limit"),
        )
    elif case == "docs_to_blogs":
        result = compute_docs_to_blogs(
            **common,
            baseline_platform=params.get("baseline_platform"),
            platforms_limit=params.get("platforms_limit"),
            threshold_strict=float(params.get("threshold_strict", 0.86)),
            threshold_loose=float(params.get("threshold_loose", 0.80)),
            top_k=int(params.get("top_k", 5)),
            no_embeddings=bool(params.get("no_embeddings", False)),
        )
    elif case == "docs_to_tutorials":
        result = compute_docs_to_tutorials(
            **common,
            baseline_platform=params.get("baseline_platform"),
            threshold_strict=float(params.get("threshold_strict", 0.86)),
            threshold_loose=float(params.get("threshold_loose", 0.80)),
            top_k=int(params.get("top_k", 5)),
            no_embeddings=bool(params.get("no_embeddings", False)),
        )
    else:
        raise ValueError(f"Unsupported scenario case: {case}")

    return result.to_json()


def _cell_lookup(coverage_json: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in coverage_json.get("rows") or []:
        if not isinstance(row, dict):
            continue
        row_key = str(row.get("key") or row.get("topic") or "")
        coverage = row.get("coverage") or {}
        if not isinstance(coverage, dict):
            continue
        for platform, cell in coverage.items():
            out[(row_key, str(platform))] = cell if isinstance(cell, dict) else {}
    return out


def evaluate_scenario(scenario_dir: Path) -> ScenarioMetrics:
    scenario = _load_json(scenario_dir / "scenario.json")
    expected = _load_json(scenario_dir / "expected.json")
    coverage_json = _compute_result(scenario_dir, scenario)
    cells = _cell_lookup(coverage_json)

    tp = fp = tn = fn = 0
    exact_matches = 0
    lexical_matches = 0

    for item in expected.get("cells") or []:
        row_key = str(item["row_key"])
        platform = str(item["platform"])
        expected_matched = bool(item["matched"])
        actual_cell = cells.get((row_key, platform), {})
        actual_matched = bool(actual_cell.get("matched"))

        if actual_matched and expected_matched:
            tp += 1
        elif actual_matched and not expected_matched:
            fp += 1
        elif not actual_matched and not expected_matched:
            tn += 1
        else:
            fn += 1

        if actual_matched:
            match_type = str(actual_cell.get("match_type") or "")
            if match_type == "lexical":
                lexical_matches += 1
            else:
                exact_matches += 1

    return ScenarioMetrics(
        scenario=str(scenario.get("name") or scenario_dir.name),
        case=str(scenario["case"]),
        expected_cells=len(expected.get("cells") or []),
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        exact_matches=exact_matches,
        lexical_matches=lexical_matches,
    )


def evaluate_fixtures(fixtures_root: Path) -> list[ScenarioMetrics]:
    scenarios = _scenario_dirs(fixtures_root)
    if not scenarios:
        raise ValueError(f"No scenario.json files found under {fixtures_root}")
    return [evaluate_scenario(path) for path in scenarios]


def _aggregate(metrics: list[ScenarioMetrics]) -> dict[str, Any]:
    tp = sum(m.true_positive for m in metrics)
    fp = sum(m.false_positive for m in metrics)
    tn = sum(m.true_negative for m in metrics)
    fn = sum(m.false_negative for m in metrics)
    exact = sum(m.exact_matches for m in metrics)
    lexical = sum(m.lexical_matches for m in metrics)
    aggregate = ScenarioMetrics(
        scenario="aggregate",
        case="all",
        expected_cells=sum(m.expected_cells for m in metrics),
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        exact_matches=exact,
        lexical_matches=lexical,
    )
    return aggregate.to_json()


def _render_text(metrics: list[ScenarioMetrics]) -> str:
    lines = ["Coverage Evaluation", ""]
    for metric in metrics:
        lines.append(
            f"- {metric.scenario} ({metric.case}): "
            f"precision={metric.precision:.2f} recall={metric.recall:.2f} f1={metric.f1:.2f} "
            f"tp={metric.true_positive} fp={metric.false_positive} tn={metric.true_negative} fn={metric.false_negative}"
        )
    aggregate = _aggregate(metrics)
    lines.append("")
    lines.append(
        "Aggregate: "
        f"precision={aggregate['precision']:.2f} recall={aggregate['recall']:.2f} f1={aggregate['f1']:.2f} "
        f"tp={aggregate['true_positive']} fp={aggregate['false_positive']} "
        f"tn={aggregate['true_negative']} fn={aggregate['false_negative']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _disable_external_side_effects()
    parser = argparse.ArgumentParser(description="Evaluate coverage matching against golden fixtures.")
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures/evaluation"))
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    metrics = evaluate_fixtures(args.fixtures)
    if args.json:
        print(json.dumps({"scenarios": [m.to_json() for m in metrics], "aggregate": _aggregate(metrics)}, indent=2))
    else:
        print(_render_text(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
