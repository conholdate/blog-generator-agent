# scripts/run_kra_from_config.py
from __future__ import annotations

import sys
import argparse
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

import yaml  # make sure pyyaml is in requirements.txt


def build_command(engine: Dict[str, Any]) -> list[str]:
    """
    Build the CLI command to run the KRA runner.

    - If engine.missing_topics_file is set:
        - process a missing-topics markdown row via --missing-topics-file and --missing-topic-row
    - Else if engine.use_llm_keywords / use-llm-keywords is truthy:
        - skip SerpAPI and use the built-in LLM keyword generator
    - Else if engine.use_serp_api / use-serp-api is truthy:
        - use SerpAPI ingestion: pass --use-serp-api and optional --serp-topic
    - Otherwise:
        - require engine.input_file and pass --file <path>
    """
    cmd: list[str] = [
        sys.executable,
        "-m",
        "agent_engine.blog_keyword_analyzer.runner",
    ]

    missing_topics_file = engine.get("missing_topics_file") or engine.get("missing-topics-file")
    missing_topic_row = engine.get("missing_topic_row") or engine.get("missing-topic-row")
    use_llm_keywords = bool(engine.get("use_llm_keywords") or engine.get("use-llm-keywords"))
    use_serp_api = bool(engine.get("use_serp_api") or engine.get("use-serp-api"))

    if use_llm_keywords and use_serp_api:
        raise SystemExit(
            "Use only one of engine.use_llm_keywords or engine.use_serp_api in kra_run.yaml."
        )

    if missing_topics_file:
        cmd.extend(["--missing-topics-file", str(missing_topics_file)])
        if not missing_topic_row:
            raise SystemExit(
                "engine.missing_topic_row is required in kra_run.yaml when missing_topics_file is set."
            )
        cmd.extend(["--missing-topic-row", str(missing_topic_row)])
        if use_llm_keywords:
            cmd.append("--use-llm-keywords")
        elif use_serp_api:
            cmd.append("--use-serp-api")
    elif use_serp_api:
        # Flag only, no value
        cmd.append("--use-serp-api")

        serp_topic = (
            engine.get("serp_topic")
            or engine.get("serp-topic")
            or ""
        )
        if serp_topic:
            cmd.extend(["--serp-topic", serp_topic])
    elif use_llm_keywords:
        cmd.append("--use-llm-keywords")

        serp_topic = (
            engine.get("serp_topic")
            or engine.get("serp-topic")
            or ""
        )
        if serp_topic:
            cmd.extend(["--serp-topic", serp_topic])
    else:
        input_file = engine.get("input_file")
        if not input_file:
            raise SystemExit(
                "engine.input_file is required in kra_run.yaml when both use_serp_api and use_llm_keywords are false."
            )
        cmd.extend(["--file", input_file])

    # Required / common arguments
    cmd.extend(
        [
            "--brand",
            engine["brand"],
            "--product",
            engine["product"],
            "--locale",
            engine.get("locale", "en-US"),
            "--top",
            str(engine.get("top_clusters", 10)),
            "--max-rows",
            str(engine.get("max_rows", 50000)),
        ]
    )

    platform = engine.get("platform")
    if platform:
        cmd.extend(["--platform", platform])

    include_product_in_title = engine.get("include_product_in_title")
    if include_product_in_title is None:
        include_product_in_title = engine.get("include-product-in-title")
    if include_product_in_title is not None:
        if bool(include_product_in_title):
            cmd.append("--include-product-in-title")
        else:
            cmd.append("--no-product-in-title")

    # Optional: if your CLI supports --no-content-index
    use_content_index = bool(engine.get("use_content_index", True))
    if not use_content_index:
        cmd.append("--no-content-index")

    return cmd


def resolve_blog_content_root(ci_cfg: Dict[str, Any]) -> str | None:
    """
    Decide BLOG_CONTENT_ROOT based on environment:

    - If BLOG_CONTENT_ROOT is already set in env (e.g. by CI workflow), use that.
    - Otherwise, use local_root from kra_run.yaml (for local dev).
    """
    existing = os.getenv("BLOG_CONTENT_ROOT")
    if existing:
        print(f"[KRA] BLOG_CONTENT_ROOT already set in environment: {existing}")
        return existing

    local_root = ci_cfg.get("local_root")
    if local_root:
        print(f"[KRA] Local BLOG_CONTENT_ROOT resolved to: {local_root}")
        return local_root

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Blog Keyword Analyzer from a kra_run.yaml file."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to kra_run.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        raise SystemExit(f"Config file not found: {config_path}")

    cfg: Dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    engine: Dict[str, Any] = cfg["engine"]
    ci_cfg: Dict[str, Any] = cfg.get("content_index") or {}

    cmd = build_command(engine)

    # Build env and wire BLOG_CONTENT_ROOT from kra_run
    env = os.environ.copy()

    blog_root = resolve_blog_content_root(ci_cfg)
    if blog_root:
        env["BLOG_CONTENT_ROOT"] = blog_root

    # Optional: pass debug flag
    if engine.get("debug"):
        env["KRA_DEBUG"] = "1"

    print("[KRA] Using BLOG_CONTENT_ROOT:", env.get("BLOG_CONTENT_ROOT"))
    print("[KRA] Running command:\n  " + " ".join(cmd))

    subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
