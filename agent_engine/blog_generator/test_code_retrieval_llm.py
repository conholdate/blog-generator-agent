"""
Manual tester for the LLM-judgment retrieval pipeline (see
code_retrieval/retrieval_llm.py). Same shape as test_code_retrieval.py, but
calls the LLM-judgment version instead of the keyword-scoring one - lets the
two be run side by side against the same topics for comparison.

Usage:
    python test_code_retrieval_llm.py \
        --product "Aspose.Slides for .NET" --platform .NET \
        --topic "Convert ODP to PPTX in C# using Aspose.Slides" \
        [--brand aspose.com] [--json-out result.json]
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env"))

from code_retrieval.retrieval_llm import retrieve_example_llm  # noqa: E402


def _print_report(result: dict) -> None:
    inp = result["input"]
    print(f"\nINPUT\nProduct: {inp['product']}\nPlatform: {inp['platform']}\nTopic: {inp['topic']}")

    if result.get("reason") and not result.get("selected"):
        print(f"\nNO MATCH — {result['reason']}")
        if result.get("pick"):
            print(f"(LLM stage 1 pick: {result['pick'].get('raw_file')})")
        print(f"\nTime taken: {result.get('elapsed_seconds', '?')}s")
        return

    print(f"\nRepo: {result['repo']}")
    print(f"\nSTAGE 1 PICK: {result['pick']['file']}")
    print(f"Reason: {result['pick']['reason']}")
    print(f"\nSTAGE 2 VERIFICATION: {'PASS' if result['verification']['verified'] else 'FAIL'}")
    print(f"Reason: {result['verification']['reason']}")

    selected = result["selected"]
    print(f"\nSELECTED\n{selected['source']['category']}/{selected['source']['file']}")
    print(f"\nCONFIDENCE: {result['confidence']}")
    print(f"\nTime taken: {result.get('elapsed_seconds', '?')}s")
    print(f"\nLanguage: {selected['language']}")
    print(f"\nCODE:\n{selected['code']}")


async def main_async():
    parser = argparse.ArgumentParser(description="LLM-judgment code-retrieval tester")
    parser.add_argument("--brand", default="aspose.com")
    parser.add_argument("--product", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--primary-keyword", default="")
    parser.add_argument("--outline", action="append", default=[])
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args()

    token = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN", "")

    result = await retrieve_example_llm(
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


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
