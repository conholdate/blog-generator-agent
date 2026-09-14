import argparse
import asyncio
import json
from agent_logic.orchestrator import BlogOrchestrator
import sys
sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser(description="Run BlogOrchestrator")

    parser.add_argument("--author", type=str, required=True, default=None)
    parser.add_argument("--brand", type=str, required=True, default=None)

    # Manual-entry mode: providing --topic switches from the approved-topics
    # sheet flow to a user-supplied topic/outline/keywords run. All of these
    # are optional so the existing automated invocation stays unchanged.
    parser.add_argument("--product", type=str, default="")
    parser.add_argument("--platform", type=str, default="")
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--outline", type=str, default="")
    parser.add_argument("--keywords", type=str, default="")
    parser.add_argument("--merge-serp", type=str, default="false")
    parser.add_argument("--layout", type=str, default="")
    parser.add_argument("--word-count", type=int, default=0)

    # Revise mode: edit an already-generated draft in place instead of
    # generating a new one. Mutually exclusive with the topic/sheet flows.
    parser.add_argument("--revise", action="store_true")
    parser.add_argument("--draft-path", type=str, default="")
    parser.add_argument("--instruction", type=str, default="")

    # Keyword-suggestion mode: look up real keywords for a topic, print them,
    # exit - no draft is generated. Used by the dashboard's "Generate
    # keywords" button (a separate, lightweight workflow from --topic mode).
    parser.add_argument("--suggest-keywords", action="store_true")

    args = parser.parse_args()

    orchestrator = BlogOrchestrator(brand=args.brand)

    if args.suggest_keywords:
        if not args.topic.strip() or not args.product.strip() or not args.platform.strip():
            parser.error("--topic, --product, and --platform are required with --suggest-keywords")

        result = asyncio.run(
            orchestrator.suggest_keywords(
                topic=args.topic,
                product=args.product,
                platform=args.platform,
            )
        )
        # A single, compact, clearly-marked line - the dashboard fetches
        # this job's raw log text and matches this exact prefix. Printed
        # in addition to (not instead of) the normal summary line below.
        print(f"KEYWORDS_RESULT_JSON:{json.dumps(result, separators=(',', ':'))}")
        print(f"Keyword suggestion result: {result}")
        return

    if args.revise:
        if not args.draft_path.strip() or not args.instruction.strip():
            parser.error("--draft-path and --instruction are required with --revise")

        result = asyncio.run(
            orchestrator.revise_blog_draft(
                draft_path=args.draft_path,
                instruction=args.instruction,
            )
        )
    elif args.topic.strip():
        if not args.product.strip() or not args.platform.strip():
            parser.error("--product and --platform are required when --topic is provided")

        result = asyncio.run(
            orchestrator.create_blog_from_manual_input(
                author=args.author,
                product=args.product,
                platform=args.platform,
                topic=args.topic,
                outline_text=args.outline,
                keywords_text=args.keywords,
                merge_with_serp=args.merge_serp.strip().lower() == "true",
                layout_override=args.layout,
                word_count=args.word_count,
            )
        )
    else:
        result = asyncio.run(
            orchestrator.create_blog_autonomously(
                author=args.author
            )
        )

    print(f"Generated blog post details : {result}")

    if isinstance(result, dict) and result.get("status") == "error":
        sys.exit(1)

if __name__ == "__main__":
    main()
