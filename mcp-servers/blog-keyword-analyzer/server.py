"""
Blog Keyword Analyzer MCP Server (blog-generator-agents)

Thin wrapper that delegates to the base blog-keyword-analyzer repo's MCP server.
This allows blog-generator-agents to use the same MCP interface as the source repo.

The actual implementation is in:
  C:\GitHub\aspose\blog-keyword-analyzer\agent_engine\blog_keyword_analyzer\mcp_server.py
"""

import sys
import os

# Setup path to import from the base blog-keyword-analyzer repo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../"))
BLOG_KWA_PATH = os.path.abspath(os.path.join(PARENT_PATH, "../../blog-keyword-analyzer"))

# Add both paths for imports
if BLOG_KWA_PATH not in sys.path:
    sys.path.insert(0, BLOG_KWA_PATH)

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)

# Import and re-export the MCP server from the base repo
from agent_engine.blog_keyword_analyzer.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
