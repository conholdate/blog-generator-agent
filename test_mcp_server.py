#!/usr/bin/env python3
"""
Quick test of the blog-keyword-analyzer MCP server.
Run this to verify the MCP server works without network access.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_keyword_analyzer():
    """Test the blog-keyword-analyzer MCP server."""

    server_script = repo_root / "mcp-servers" / "blog-keyword-analyzer" / "server.py"

    if not server_script.exists():
        print(f"[!] Server script not found: {server_script}")
        return False

    print(f"[*] Testing MCP server: {server_script}")
    print()

    try:
        # Start the MCP server
        params = StdioServerParameters(command=sys.executable, args=[str(server_script)])

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test call
                print("[*] Calling fetch_keywords...")
                result = await asyncio.wait_for(
                    session.call_tool("fetch_keywords", {
                        "topic": "How to read Excel files in Python",
                        "product_name": "Aspose.Cells",
                        "platform": "general",
                        "brand": "Aspose",
                    }),
                    timeout=180.0,
                )

        # Parse response
        if not result.content:
            print("[!] MCP server returned no content")
            return False

        content = result.content[0]
        text = getattr(content, "text", None)

        if text is None:
            print(f"[!] MCP server returned non-text content: {content!r}")
            return False

        response = json.loads(text)

        # Verify response structure
        print("[+] MCP server response received")
        print()
        print("Response structure:")
        print(json.dumps({
            "status": response.get("status"),
            "topic": response.get("topic"),
            "keywords": {
                "primary_count": len(response.get("keywords", {}).get("primary", [])),
                "secondary_count": len(response.get("keywords", {}).get("secondary", [])),
                "long_tail_count": len(response.get("keywords", {}).get("long_tail", [])),
                "has_metadata": bool(response.get("keywords", {}).get("metadata")),
            },
            "has_topic_idea": bool(response.get("topic_idea")),
        }, indent=2))

        if response.get("status") == "success":
            keywords = response.get("keywords", {})
            print()
            print("[+] Keyword analysis successful!")
            print(f"    Primary keyword: {keywords.get('primary', [None])[0]}")
            print(f"    Secondary keywords ({len(keywords.get('secondary', []))}): {keywords.get('secondary', [])[:3]}")
            print(f"    Long-tail keywords ({len(keywords.get('long_tail', []))}): {keywords.get('long_tail', [])[:3]}")
            return True
        else:
            print()
            print(f"[!] Error: {response.get('error')}")
            return False

    except asyncio.TimeoutError:
        print("[!] MCP server timeout (>180s)")
        return False
    except Exception as e:
        print(f"[!] Error: {e!r}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_keyword_analyzer())
    sys.exit(0 if success else 1)
