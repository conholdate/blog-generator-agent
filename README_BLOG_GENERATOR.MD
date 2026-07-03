# Blog Post Generator Agent Backend

An automated blog post creation engine powered by **OpenAI Agents SDK** and a network of **MCP servers**.  
This backend system generates SEO-optimized technical blog posts for supported brands using SERP-based keyword research, content orchestration, and multi-step LLM workflows.

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd blog-generator-agent
cd scripts
chmod +x blog-post-generation-setup.sh
./blog-post-generation-setup.sh
```

## Configure Environment Variables

Update the .env file inside agent_engine/.env:

## Run the Agent

python main.py  --author "Muhammad Mustafa"  --brand "aspose.cloud"
## Project Structure

```
blog-generator-agent/
├── agent_engine/
│   └── blog_generator/
│       ├── main.py                     # Main runner script
│       ├── config.py                   # Configuration loader
│       ├── agent_logic/
│       │   └── orchestrator.py         # Core orchestration workflow
│       ├── tools/
│       │   └── mcp_tools.py            # MCP tool wrapper functions
│       ├── utils/
│       │   ├── helpers.py              # Helper utilities
│       │   └── prompts.py              # Prompt builders for LLM
│       └── requirements.txt
│
├── mcp-servers/
│   ├── file-generator/
│   │   └── server.py                  # Markdown file generator
│   ├── related-topics/
│   │   └── server.py                  # Related content fetcher
│   ├── gist-injector/
│   │   └── server.py                  # Gist Creator & Injector
│   ├── keywords_auto/
│   │   └── server.py                  # SEO keyword fetcher
│   ├── blog-banner-generator/
│   │   └── tools/public-release-post-cover/banner_mcp_server.py  # Blog cover image generator
│   ├── blog-orchestrator/
│   │   └── server.py                  # HTTP MCP wrapper around BlogOrchestrator (remote/agent-to-agent access)
│   └── requirements.txt
│
├── content/
│   ├── productsData/                  # Contains products data
│   │   ├── aspose.json
│   │   ├── groupdocs.json
│   │   └── conholdate.json
│   └── blogPosts/                     # Generated Markdown blog posts
│
└── scripts/
    └── blog-post-generation-setup.sh  # Initial installation script

```

---

## Remote Access via HTTP MCP (blog-orchestrator)

By default, the agent only runs as a one-shot CLI command (`python main.py ...`). `mcp-servers/blog-orchestrator/server.py` wraps the same `BlogOrchestrator` in an HTTP MCP server, so other MCP clients/agents can trigger blog generation remotely instead of only via the CLI.

This is an additional entrypoint only. It does not change `main.py`, `orchestrator.py`, `mcp_tools.py`, or any of the internal stdio MCP servers (`file-generator`, `related-topics`, `gist-injector`, `keywords_auto`, `blog-banner-generator`) - those still work exactly as before, and are still spawned over stdio internally, not HTTP.

### Running it

```bash
venv/bin/python mcp-servers/blog-orchestrator/server.py
```

> **Shell alias gotcha:** if your shell aliases `python`/`python3` to a system interpreter, plain `python mcp-servers/blog-orchestrator/server.py` may fail with `ModuleNotFoundError: No module named 'fastmcp'` because it bypasses the venv. Always invoke via the explicit `venv/bin/python` path (or run `which python3` to confirm it resolves inside `venv/bin` first).

The server listens on `http://127.0.0.1:8800/mcp` - localhost only, no authentication. It is not reachable from other machines unless you deploy it somewhere reachable (VM, container, tunnel) and add auth in front of it; neither is set up yet.

### Tools exposed

Since blog generation can take several minutes (LLM calls, keyword research, image generation), the tool call returns immediately with a job id instead of blocking - poll for the result.

- `generate_blog_post(brand: str, author: str) -> {job_id, status: "running"}`
  Starts a background job. Pulls the next approved topic from that brand's Google Sheet queue and runs the same flow as `python main.py --brand <brand> --author <author>` - it does **not** accept a topic; the topic still comes from the sheet queue.
- `get_job_status(job_id: str) -> {status, message, result}`
  `status` is one of `running | success | error | not_found`. Once finished, `message` is a human-readable confirmation (e.g. `✅ Blog post generation completed!\n📄 File: ...`) and `result` is the raw dict `create_blog_autonomously()` returned.

### Testing it

Use any MCP client that supports Streamable HTTP, e.g. the official inspector:

```bash
npx @modelcontextprotocol/inspector
```

Connect via transport "Streamable HTTP" to `http://127.0.0.1:8800/mcp`, then call `generate_blog_post` followed by `get_job_status` with the returned `job_id`.

Or use the official `mcp` Python SDK directly:

```python
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://127.0.0.1:8800/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "generate_blog_post", {"brand": "aspose.cloud", "author": "Your Name"}
            )
            job_id = json.loads(result.content[0].text)["job_id"]
            # poll get_job_status with job_id until status != "running"

asyncio.run(main())
```