"""
Creates Gists for a given code snippet
"""
import sys, os
from fastmcp import FastMCP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../"))
if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
from agent_engine.blog_generator.config import settings
from agent_engine.blog_generator.utils.helpers import extract_all_complete_code_snippets, upload_to_gist, replace_code_snippets_with_gists

# Load your environment (optional if already set)
from dotenv import load_dotenv
load_dotenv()

# Initialize MCP
mcp = FastMCP("gist-injector")


@mcp.tool()
async def gist_injector(content: str, title: str, summary: str = "", url: str = "") -> dict:

    try:
        snippets = extract_all_complete_code_snippets(content,title)
        if len(snippets) == 0:
            print("No complete code snippets found!", flush=True, file=sys.stderr)
            return {"jistified_content": content}
        

        code_for_gist = {
            data['filename']: data['code']
            for data in snippets.values()
        }

        gist_result = await upload_to_gist(
            code_for_gist,
            description=title,
            token=settings.REPO_PAT,
            gist_name=settings.GIST_NAME,
            url=url,
            summary=summary,
        )

        print(f"gist result --- {gist_result}", flush=True, file=sys.stderr)

        if gist_result.get("success"):
            shortcodes_map = gist_result['shortcodes']
            updated_content = replace_code_snippets_with_gists(content, snippets, shortcodes_map)
            print(f"Code snippets replaced with gists.", flush=True, file=sys.stderr)
            return {"jistified_content": updated_content, "gist_url": gist_result.get("gist_url", "")}
        else:
            print(f"❌ Gist upload failed: {gist_result['error']}", flush=True, file=sys.stderr)
            return {"jistified_content": "content"}

    except Exception as e:
        print(f"Error in gist_injector: {e}", file=sys.stderr)
        return {"jistified_content": content}

if __name__ == "__main__":
    mcp.run()