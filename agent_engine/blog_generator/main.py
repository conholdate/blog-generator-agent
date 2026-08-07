import argparse
import asyncio
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

    args = parser.parse_args()

    orchestrator = BlogOrchestrator(brand=args.brand)

    if args.topic.strip():
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
