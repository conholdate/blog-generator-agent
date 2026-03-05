"""
Keywords MCP Server - Dynamic keyword research
Uses modular services via aggregator
"""

import sys
import os, json, re, ast, json
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Dict, List
from openai import OpenAI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../"))

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
    
from agent_engine.blog_generator.services.serpapi_keyword_service import SerpAPIKeywordService
from agent_engine.blog_generator.utils.prompts import keyword_filter_prompt
from agent_engine.blog_generator.config import settings
client = OpenAI(
    base_url=settings.PROFESSIONALIZE_BASE_URL,
    api_key=settings.PROFESSIONALIZE_API_KEY_2
)
# ---------------------------------------------
# Log only to stderr — keep stdout clean for JSON-RPC
# ---------------------------------------------
print(" MCP Server starting...", file=sys.stderr, flush=True)


# Add agent-engine to import path
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_engine_dir = os.path.join(current_dir, '../../agent_engine')
sys.path.insert(0, agent_engine_dir)

mcp = FastMCP("keywords-server")

# ---------------------------------------------
# Define MCP Tool
# ---------------------------------------------
@mcp.tool()
async def fetch_keywords(topic: str, product_name: str = None, platform:str=None) -> dict:
    print(f"fetch_keywords TOOL CALLED (topic={topic}, product={product_name})", file=sys.stderr, flush=True)
    
    try:
        all_results = []
        serpapi = SerpAPIKeywordService(api_key="66c1df1bd9d524fc1f5864c6070b9a73666994b392127d642839817119d7992d")
        
        try:
            result = await serpapi.fetch_keywords(topic, product_name, 10)
            all_results.append(result)
        except Exception as e:
            print(f"Error from SerpAPI: {e}", file=sys.stderr, flush=True)
        
        # Merge results
        merged = _merge_keywords(all_results)
        prompt = keyword_filter_prompt(topic, product_name, merged, platform)
        
        response = client.responses.create(
            model='gpt-oss', 
            input=prompt,
        )
        
        # Add robust parsing here
        output_text = response.output_text.strip()
        
        if not output_text:
            raise ValueError("Empty response from LLM")
        
        # Try parsing with fallbacks
        try:
            final_keywords = json.loads(output_text)
        except json.JSONDecodeError:
            print(f"LLM returned invalid JSON: {repr(output_text)}", file=sys.stderr, flush=True)
            
            # Try Python literal eval (handles single quotes)
            try:
                final_keywords = ast.literal_eval(output_text)
                print("Successfully parsed as Python dict", file=sys.stderr, flush=True)
            except (ValueError, SyntaxError):
                # Try to extract JSON from text
                match = re.search(r'\{.*\}', output_text, re.DOTALL)
                if match:
                    try:
                        final_keywords = json.loads(match.group())
                    except json.JSONDecodeError:
                        final_keywords = ast.literal_eval(match.group())
                else:
                    # Fallback to original merged keywords if LLM fails
                    print("Falling back to unfiltered keywords", file=sys.stderr, flush=True)
                    final_keywords = merged

        return {
            "topic": topic,
            "keywords": final_keywords,
            "status": "success"
        }
        
    except Exception as e:
        print(f"ERROR in fetch_keywords: {str(e)}", file=sys.stderr, flush=True)
        # Return error in proper format instead of raising
        return {
            "topic": topic,
            "keywords": {"primary": [topic], "secondary": [], "long_tail": []},
            "status": "error",
            "error": str(e)
        }

def _merge_keywords( results: List[Dict]) -> Dict:
    """
    Merge keywords from multiple sources
    Removes duplicates and combines metadata
    """

    primary = []
    secondary = []
    long_tail = []
    sources = []

    for result in results:
        primary.extend(result.get("primary", []))
        secondary.extend(result.get("secondary", []))
        long_tail.extend(result.get("long_tail", []))
        sources.append(result.get("source", "Unknown"))

    # Remove duplicates while preserving order
    primary = list(dict.fromkeys(primary))
    secondary = list(dict.fromkeys(secondary))
    long_tail = list(dict.fromkeys(long_tail))

    return {
        "primary": primary,
        "secondary": secondary,
        "long_tail": long_tail,
        "metadata": {
            "sources": sources,
            "total_services": len(results),
            "total_keywords": len(primary) + len(secondary) + len(long_tail)
        }
    }

# ---------------------------------------------
# Run MCP Server
# ---------------------------------------------
if __name__ == "__main__":
    mcp.run()