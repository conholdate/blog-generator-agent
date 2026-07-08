"""
Preview the blog post layout system without calling any LLM.

Shows, for a sample of topics:
  - which layout gets selected and why
  - the resulting post skeleton (H2-level section flow)
Optionally dumps the full rendered writer prompt for one topic/layout.

Usage:
  python scripts/preview_layouts.py                 # selection + skeletons
  python scripts/preview_layouts.py --seed 7        # reproducible run
  python scripts/preview_layouts.py --full-prompt quick_answer   # dump one full prompt
"""
import argparse
import os
import random
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_GEN = os.path.join(REPO_ROOT, "agent_engine", "blog_generator")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, BLOG_GEN)

from agent_engine.blog_generator.utils.layouts import (  # noqa: E402
    ALL_LAYOUTS,
    select_layout,
    render_prompt_blocks,
)

SAMPLE_TOPICS = [
    # (topic, angle, persona, is_cloud)
    ("Generate Barcode for Healthcare Applications in Java", "compliance-focused barcode generation", "backend developer", True),
    ("Convert DWG to PDF in Python", "", "developer", False),
    ("How to Merge PDF Files in C#", "", "beginner developer new to PDF processing", False),
    ("Extract Text from Invoices for Finance Systems in .NET", "automating accounts payable", "solution architect", False),
    ("Create ZIP Archives in Java", "", "developer", False),
    ("Convert HTML to PNG via REST API", "", "developer", True),
]

SAMPLE_OUTLINE = [
    "Installation and Setup",
    "Key Features of the SDK",
    "Configuring Conversion Options",
    "Performance Optimization",
    "Best Practices",
]


def preview_selection(seed):
    rng = random.Random(seed)
    print("=" * 100)
    print("LAYOUT SELECTION PREVIEW")
    print("=" * 100)
    recent = []
    for topic, angle, persona, is_cloud in SAMPLE_TOPICS:
        choice = select_layout(
            topic, angle=angle, persona=persona, is_cloud=is_cloud,
            recent_layouts=recent[-2:], rng=rng,
        )
        recent.append(choice.name)
        print(f"\nTOPIC:  {topic}")
        print(f"  cloud={is_cloud}  persona={persona!r}")
        print(f"  LAYOUT: {choice.name}   (reason: {choice.reason})")
        print(f"  SKELETON:")
        for part in choice.skeleton():
            print(f"    - {part}")


def preview_distribution(seed, runs=1000):
    rng = random.Random(seed)
    print("\n" + "=" * 100)
    print(f"DISTRIBUTION OVER {runs} RUNS (generic how-to topic, no recent-layout exclusion)")
    print("=" * 100)
    counts = Counter(
        select_layout("Convert DOCX to PDF in Java", rng=rng).name for _ in range(runs)
    )
    for name, count in counts.most_common():
        print(f"  {name:<22} {count / runs:>6.1%}")


def preview_full_prompt(layout_name, seed):
    from agent_engine.blog_generator.utils.layouts import LAYOUTS_BY_NAME, _resolve_choice
    from agent_engine.blog_generator.utils import prompts

    rng = random.Random(seed)
    choice = _resolve_choice(LAYOUTS_BY_NAME[layout_name], is_cloud=True, rng=rng, reason="preview")
    prompt = prompts.get_blog_writer_prompt(
        title="Generate Barcode for Healthcare Applications in Java",
        keywords=["generate barcode in java", "healthcare barcode java", "barcode REST API"],
        outline=SAMPLE_OUTLINE,
        related_links=[{"title": "Related Post", "url": "https://blog.aspose.cloud/example/"}],
        context="ProductName: Aspose.BarCode Cloud\nProductURL: https://products.aspose.cloud/barcode/java/\nCategory: Barcode\nurlPrefix: barcode",
        author="Preview Author",
        target_persona="backend developer",
        angle="compliance-focused",
        long_tail_keywords=["how to generate barcode in java"],
        semantic_keywords=["barcode symbology"],
        other_important_and_relevant_things="",
        tags=["Barcode", "Java"],
        isCloud=True,
        allowed_products=[{"ProductName": "Aspose.BarCode Cloud", "ProductURL": "https://products.aspose.cloud/barcode/"}],
        layout_choice=choice,
    )
    print(prompt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--full-prompt", choices=[l.name for l in ALL_LAYOUTS], default=None)
    args = parser.parse_args()

    if args.full_prompt:
        preview_full_prompt(args.full_prompt, args.seed)
    else:
        preview_selection(args.seed)
        preview_distribution(args.seed)
