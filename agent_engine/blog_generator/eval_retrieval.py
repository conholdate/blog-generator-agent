"""
Evaluation harness (Phase 2, step 2 of the plan): runs a labeled ground-truth
corpus through either retrieval pipeline and reports real accuracy numbers,
instead of judging changes against a handful of hand-picked examples.

Ground-truth file format (JSON list):
    [{"topic": str, "truth": [file_path, ...] | null, "note": str (optional)}, ...]
`truth: null` means no real example exists for that topic - the correct
outcome is NO_MATCH. `truth` as a list means any one of those files counts
as correct (some topics have multiple equally-valid answers).

Usage:
    python eval_retrieval.py --ground-truth /path/to/ground_truth.json \
        --product "Aspose.Slides for .NET" --platform .NET --mode llm
    python eval_retrieval.py --ground-truth ... --mode keyword
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

from code_retrieval.retrieval import retrieve_example  # noqa: E402
from code_retrieval.retrieval_llm import retrieve_example_llm  # noqa: E402


def _selected_path(result: dict) -> str | None:
    selected = result.get("selected")
    if not selected:
        return None
    src = selected["source"]
    return f"{src['category']}/{src['file']}"


def _judge(entry: dict, result: dict) -> str:
    """Returns one of: TP (correct match), TN (correctly NO_MATCH),
    FP (wrongly matched when none exists), FN (missed a real match,
    including picking the wrong file)."""
    picked = _selected_path(result)
    truth = entry.get("truth")
    if truth is None:
        return "TN" if picked is None else "FP"
    return "TP" if picked in truth else "FN"


async def run(ground_truth_path: str, brand: str, product: str, platform: str, mode: str, token: str) -> None:
    with open(ground_truth_path) as f:
        entries = json.load(f)

    counts = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    rows = []

    for i, entry in enumerate(entries, 1):
        topic = entry["topic"]
        if mode == "llm":
            result = await retrieve_example_llm(brand=brand, product_name=product, platform=platform,
                                                  topic=topic, token=token)
        else:
            result = retrieve_example(brand=brand, product_name=product, platform=platform,
                                       topic=topic, token=token)

        verdict = _judge(entry, result)
        counts[verdict] += 1
        picked = _selected_path(result) or "NONE"
        truth_display = entry.get("truth") or "NONE"
        rows.append(f"[{verdict}] #{i} {topic!r}\n      truth={truth_display} picked={picked}")
        print(rows[-1], flush=True)

    total = sum(counts.values())
    precision = counts["TP"] / (counts["TP"] + counts["FP"]) if (counts["TP"] + counts["FP"]) else float("nan")
    recall = counts["TP"] / (counts["TP"] + counts["FN"]) if (counts["TP"] + counts["FN"]) else float("nan")
    accuracy = (counts["TP"] + counts["TN"]) / total if total else float("nan")

    print("\n" + "=" * 60)
    print(f"mode={mode} product={product!r} platform={platform!r}")
    print(f"TP={counts['TP']} TN={counts['TN']} FP={counts['FP']} FN={counts['FN']} (n={total})")
    print(f"accuracy={accuracy:.3f}  precision={precision:.3f}  recall={recall:.3f}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Evaluate a retrieval pipeline against labeled ground truth")
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--brand", default="aspose.com")
    parser.add_argument("--product", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--mode", choices=["keyword", "llm"], default="llm")
    args = parser.parse_args()

    token = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN", "")
    asyncio.run(run(args.ground_truth, args.brand, args.product, args.platform, args.mode, token))


if __name__ == "__main__":
    main()
