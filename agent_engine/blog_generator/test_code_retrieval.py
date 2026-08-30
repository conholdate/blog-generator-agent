"""
Phase 1 manual tester for the code-retrieval pipeline. Run by hand against
real blog topics to judge whether the matching logic actually works, before
any of this touches code_snippet.py or the orchestrator.

Usage:
    python test_code_retrieval.py \
        --product "Aspose.Cells for .NET" --platform .NET \
        --topic "How to calculate Excel formulas with a custom function in C#" \
        [--primary-keyword "custom function calculate formula"] \
        [--outline "step one" --outline "step two"] \
        [--brand aspose.com] [--json-out result.json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env"))

from code_retrieval.retrieval import retrieve_example  # noqa: E402


def _print_report(result: dict) -> None:
    inp = result["input"]
    print(f"\nINPUT\nProduct: {inp['product']}\nPlatform: {inp['platform']}\nTopic: {inp['topic']}")
    if inp.get("primary_keyword"):
        print(f"Primary keyword: {inp['primary_keyword']}")
    print(f"\nNormalized terms: {', '.join(result['normalized_terms'])}")

    if result.get("reason"):
        print(f"\nNO MATCH — {result['reason']}")
        return

    print(f"\nRepo: {result['repo']}")

    print("\nCATEGORY CANDIDATES")
    for i, c in enumerate(result["category_candidates"], 1):
        print(f"{i}. {c['id']}: {c['score']}")

    print("\nFILE CANDIDATES")
    for i, c in enumerate(result["file_candidates"], 1):
        flag = " [REJECTED]" if c.get("rejected") else ""
        print(f"{i}. {c['category']}/{c['file']}: filename={c['score']} combined={c['combined_score']}{flag}")

    selected = result.get("selected")
    if not selected:
        print(f"\nSELECTED: none — {result.get('reason', 'no candidate cleared verification')}")
        print(f"\nFINAL CONFIDENCE: {result['confidence']}")
        return

    print(f"\nSELECTED\n{selected['source']['category']}/{selected['source']['file']}")

    print("\nVERIFICATION")
    winner = next(
        c for c in result["file_candidates"]
        if c["category"] == selected["source"]["category"] and c["file"] == selected["source"]["file"]
    )
    for check, passed in winner["verification"]["checks"].items():
        print(f"{check}: {'PASS' if passed else 'FAIL'}")

    print(f"\nFINAL CONFIDENCE: {result['confidence']} ({selected['matching']['combined_score']})")
    print(f"\nLanguage: {selected['language']}")
    print(f"\nCODE:\n{selected['code']}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 code-retrieval tester")
    parser.add_argument("--brand", default="aspose.com")
    parser.add_argument("--product", required=True, help='e.g. "Aspose.Cells for .NET"')
    parser.add_argument("--platform", required=True, help='e.g. ".NET"')
    parser.add_argument("--topic", required=True)
    parser.add_argument("--primary-keyword", default="")
    parser.add_argument("--outline", action="append", default=[])
    parser.add_argument("--json-out", default=None, help="also write the full result to this path")
    args = parser.parse_args()

    token = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN", "")

    result = retrieve_example(
        brand=args.brand,
        product_name=args.product,
        platform=args.platform,
        topic=args.topic,
        primary_keyword=args.primary_keyword,
        outline=args.outline,
        token=token,
    )

    _print_report(result)

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result written to {args.json_out}")


if __name__ == "__main__":
    main()
