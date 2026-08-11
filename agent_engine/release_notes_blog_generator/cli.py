from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Settings
from .llm.factory import get_llm_client
from .logging_config import configure_logging
from .output.markdown_exporter import export
from .pipeline.orchestrator import SOURCE_TYPE_DOCS, SOURCE_TYPE_RELEASE_NOTES, SOURCE_TYPES, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="release-notes-blog-generator",
        description="Generate blog post drafts from product release notes or a documentation article.",
    )
    parser.add_argument("url", help="Release notes URL (default) or documentation article URL to process")
    parser.add_argument(
        "--source-type",
        default=SOURCE_TYPE_RELEASE_NOTES,
        choices=list(SOURCE_TYPES),
        help=(
            "What kind of page the URL points at: 'release-notes' (default) generates one draft "
            "per code-backed feature section; 'docs' generates a single detailed draft covering "
            "every topic on the documentation article"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write generated drafts to (default: settings.output_dir)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Progress log verbosity (default: settings.log_level / INFO)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Shortcut for --log-level DEBUG",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    configure_logging("DEBUG" if args.verbose else (args.log_level or settings.log_level))
    llm = get_llm_client(settings)

    result = run(args.url, llm, settings, source_type=args.source_type)

    if result.publication_readiness == "blocked":
        print(f"BLOCKED: {result.blocker_reason}", file=sys.stderr)
        if result.remediation_report:
            print(result.remediation_report, file=sys.stderr)
        return 1

    if not result.topics:
        if args.source_type == SOURCE_TYPE_DOCS:
            print("The documentation article contained no usable code samples; nothing to generate.")
        else:
            print("No code-backed topics were found; nothing to generate.")
        return 0

    output_dir = Path(args.output_dir or settings.output_dir)
    written = export(result, output_dir)
    print(f"Generated {len(result.topics)} draft(s):")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
