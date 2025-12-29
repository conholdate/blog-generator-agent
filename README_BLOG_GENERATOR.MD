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

python3 main.py --keywords_file "content/GroupDocs/output/e5afbdf4_groupdocs-conversion_c_topics.md" --author "Muhammad Mustafa" --brand "groupdocs.com"

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