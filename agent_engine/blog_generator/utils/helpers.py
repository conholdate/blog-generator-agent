
from datetime import datetime, timedelta
import re, sys, os, json, logging
from tkinter.font import names
import requests
from typing import Dict, Any, Optional, List, Tuple

import gspread
from google.oauth2.service_account import Credentials
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import settings
logger = logging.getLogger(__name__)

def parse_markdown_topics(markdown_content: str) -> Dict[str, Any]:
    """
    Parse markdown file containing blog topics and extract metadata.
    
    Args:
        markdown_content: Full markdown content string
        
    Returns:
        Dictionary with metadata (brand, product, platform) and list of topics
    """
    # Extract metadata from header
    brand_match = re.search(r'\*\*Brand:\*\*\s*(.+)', markdown_content)
    product_match = re.search(r'\*\*Product:\*\*\s*(.+)', markdown_content)
    platform_match = re.search(r'\*\*Platform:\*\*\s*(.+)', markdown_content)
    run_id_match = re.search(r'\*\*Run ID:\*\*\s*(.+)', markdown_content)
    
    metadata = {
        "brand": brand_match.group(1).strip() if brand_match else None,
        "product": product_match.group(1).strip() if product_match else None,
        "platform": platform_match.group(1).strip() if platform_match else None,
        "run_id": run_id_match.group(1).strip() if run_id_match else None,
    }
    
    # Extract all topic sections
    topic_pattern = r'##\s+\d+\.\s+(.+?)\n(.*?)(?=##\s+\d+\.|$)'
    topics = []
    
    for match in re.finditer(topic_pattern, markdown_content, re.DOTALL):
        topic_title = match.group(1).strip()
        topic_details = match.group(2).strip()
        
        parsed_topic = parse_topic_details(topic_title, topic_details, metadata)
        topics.append(parsed_topic)
    
    return {
        "metadata": metadata,
        "topics": topics
    }


# Shared helper to extract a keyword section and return a list
def _extract_keyword_list(details: str, label_pattern: str) -> list:
    match = re.search(
        rf'\*\*{label_pattern}\*\*\s*(.+?)(?=\n\*\*|\Z)',
        details,
        re.DOTALL
    )
    if not match:
        return []
    text = match.group(1)
    keywords = re.findall(r'`([^`]+)`', text)
    if not keywords:
        # Fallback: comma-separated plain text
        keywords = [kw.strip() for kw in text.split(',') if kw.strip()]
    return keywords


# Shared helper to extract a keyword section and return a list
def _extract_keyword_list(details: str, label_pattern: str) -> list:
    match = re.search(
        rf'\*\*{label_pattern}\*\*\s*(.+?)(?=\n\*\*|\Z)',
        details,
        re.DOTALL
    )
    if not match:
        return []
    text = match.group(1)
    keywords = re.findall(r'`([^`]+)`', text)
    if not keywords:
        # Fallback: comma-separated plain text
        keywords = [kw.strip() for kw in text.split(',') if kw.strip()]
    return keywords


def _extract_keyword_list(details: str, label_pattern: str) -> list:
    match = re.search(
        rf'(?:^-\s*)?\*\*{label_pattern}\*\*\s*(.+?)(?=\n-\s*\*\*|\n\*\*|\Z)',
        details,
        re.DOTALL | re.MULTILINE
    )
    if not match:
        return []
    text = match.group(1)
    keywords = re.findall(r'`([^`]+)`', text)
    if not keywords:
        keywords = [kw.strip() for kw in text.split(',') if kw.strip()]
    return keywords


def parse_topic_details(
    topic_title: str,
    details: str,
    metadata: Dict[str, Optional[str]]
) -> Dict[str, Any]:
    result = {
        "topic": topic_title.strip(),
        "product": metadata.get("product"),
        "platform": metadata.get("platform"),
        "keywords": {
            "primary": [],
            "secondary": [],
            "long_tail": [],
            "semantic": [],
        },
        "outline": []
    }

    # Shared lookahead that stops at the next label (with or without bullet prefix)
    NEXT_LABEL = r'(?=\n-\s*\*\*|\n\*\*|\Z)'

    # Cluster ID
    cluster_match = re.search(r'(?:^-\s*)?\*\*Cluster ID:\*\*\s*`([^`]+)`', details, re.MULTILINE)
    if cluster_match:
        result["cluster_id"] = cluster_match.group(1).strip()

    # Target persona
    persona_match = re.search(
        rf'(?:^-\s*)?\*\*Target persona:\*\*\s*(.+?){NEXT_LABEL}',
        details, re.DOTALL | re.MULTILINE
    )
    if persona_match:
        result["target_persona"] = persona_match.group(1).strip()

    # Angle — supports "Angle:" and "Blog post angle:"
    angle_match = re.search(
        rf'(?:^-\s*)?\*\*(?:Blog post )?[Aa]ngle:\*\*\s*(.+?){NEXT_LABEL}',
        details, re.DOTALL | re.MULTILINE
    )
    if angle_match:
        result["angle"] = angle_match.group(1).strip()

    # Primary keyword
    primary_match = re.search(
        r'(?:^-\s*)?\*\*Primary keyword:\*\*\s*`([^`]+)`',
        details, re.MULTILINE
    )
    if primary_match:
        result["keywords"]["primary"].append(primary_match.group(1).strip())

    # Secondary keywords
    result["keywords"]["secondary"] = _extract_keyword_list(
        details, r'(?:Supporting|Secondary) keywords[^:]*:'
    )

    # Long-tail keywords
    result["keywords"]["long_tail"] = _extract_keyword_list(
        details, r'Long Tails? keywords:'
    )

    # Semantic SEO keywords
    result["keywords"]["semantic"] = _extract_keyword_list(
        details, r'Semantic SEO keywords:'
    )

    # Outline — supports "Suggested outline:" and "Outline for the article:"
    outline_match = re.search(
        r'(?:^-\s*)?\*\*(?:Suggested outline|Outline for the article):\*\*\s*((?:^-\s*.+$\n?)+)',
        details, re.MULTILINE
    )
    if outline_match:
        outline_items = re.findall(r'^-\s*(.+)$', outline_match.group(1), re.MULTILINE)
        result["outline"] = [item.strip() for item in outline_items if item.strip()]

    # Other notes
    other_match = re.search(
        r'(?:^-\s*)?\*\*Other important and relevant things:\*\*\s*((?:^-\s*.+$\n?)+)',
        details, re.MULTILINE
    )
    if other_match:
        other_items = re.findall(r'^-\s*(.+)$', other_match.group(1), re.MULTILINE)
        result["other_notes"] = [item.strip() for item in other_items if item.strip()]

    return result

def get_project_root() -> str:
    """
    Resolve project root assuming this file lives under:
    project_root/agent_engine/...
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../..")
    )

def get_topic_by_index(input_file: str, ind) -> str:
    # Resolve project root
    base_dir = get_project_root()
    print(f"Project root: {base_dir}")

    # If user passed absolute path, use it directly
    if os.path.isabs(input_file):
        file_path = input_file
    else:
        file_path = os.path.join(base_dir, input_file)

    print(f"Looking for file at: {file_path}")

    # Fallback: try relative to current working directory
    if not os.path.exists(file_path):
        cwd_path = os.path.abspath(input_file)
        if os.path.exists(cwd_path):
            file_path = cwd_path
            print(f"Found file via CWD: {file_path}")
        else:
            raise FileNotFoundError(
                f"File not found.\n"
                f"Tried:\n"
                f" - {file_path}\n"
                f" - {cwd_path}"
            )

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown_topics(content)
    if 1 <= ind <= len(parsed["topics"]):
        return parsed["topics"][ind - 1]
    return None



def slugify(text: str) -> str:
    """Convert text into a clean URL slug with C# → csharp and .NET → dotnet normalization."""

    if not text:
        return ""

    # Normalize special tech terms BEFORE any stripping
    text = text.replace("C#", "CSharp").replace("c#", "CSharp")
    text = re.sub(r"\.NET", "dotnet", text, flags=re.IGNORECASE)

    # Continue with normal slugify steps
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)      # remove invalid chars
    text = re.sub(r"[\s_-]+", "-", text)      # collapse spaces/underscores
    text = re.sub(r"^-+|-+$", "", text)       # trim hyphens

    return text


def current_utc_date() -> str:
    """Return current UTC date in blog format."""
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def truncate_description(desc: str, max_len: int = 160) -> str:
    """Ensure description fits SEO meta length."""
    if len(desc) <= max_len:
        return desc
    return desc[:max_len].rsplit(" ", 1)[0] + "..."

def format_related_posts(related_links):
    # If it's a dict ({"related_posts": [...]})
    if isinstance(related_links, dict):
        related_posts = related_links.get("related_posts", [])
    else:
        related_posts = related_links

    formatted_lines = []

    for post in related_posts:
        if isinstance(post, dict):
            title = post.get("title", "")
            url = post.get("url", "")
            formatted_lines.append(f"- [{title}]({url})")

        elif isinstance(post, str):  # handle raw string URLs
            formatted_lines.append(f"- [Related Post]({post})")

    return "\n".join(formatted_lines)

def get_productInfo(product_name: str, platform: str, products, brand) -> str:
    """
    Get product info by matching product name and platform.
    
    Handles various product name formats:
    - "ProductName" + platform → "ProductName for Platform"
    - "ProductName Cloud" + platform → "ProductName Cloud SDK for Platform"
    - "ProductName Cloud SDK" + platform → "ProductName Cloud SDK for Platform"
    
    Args:
        product_name: Base product name (e.g., "GroupDocs.Editor", "GroupDocs.Editor Cloud SDK")
        platform: Platform name (e.g., "Java", ".NET", "Python via .NET")
        products: List of product dictionaries with ProductName field
        brand: Brand name (e.g., "groupdocs.cloud", "aspose")
        
    Returns:
        Product info dictionary
        
    Raises:
        ValueError: If no matching product found
    """
    base_name = product_name.strip()
    platform_clean = platform.strip().lower()
    brand_clean = brand.strip() if brand else ""
    
    print(f"DEBUG: base_name='{base_name}', platform='{platform_clean}', brand='{brand_clean}'")
    
    if brand_clean == "aspose.com" and platform_clean == "python":
        platform_clean = "Python via .NET"
    elif platform_clean == "net":
        platform_clean = ".NET"
    elif platform_clean == "python-via-net":
        platform_clean = "Python via .NET"
    elif platform_clean == "java":
        platform_clean = "Java"
    elif platform_clean == "python":
        platform_clean = "Python"
    elif platform_clean == "nodejs":
        platform_clean = "Node.js"
    else:
        platform_clean = platform_clean.capitalize()
    
    # Check if base_name already contains "Cloud SDK" or "Cloud"
    base_lower = base_name.lower()
    has_cloud_sdk = "cloud sdk" in base_lower
    has_cloud = "cloud" in base_lower
    
    # Build expected product name based on brand and platform
    if "cloud" in brand_clean.lower():
        # For Cloud brands (GroupDocs.Cloud, Aspose.Cloud)
        
        if has_cloud_sdk:
            # base_name already has "Cloud SDK" (e.g., "GroupDocs.Editor Cloud SDK")
            # Just add "for {platform}"
            expected_name = f"{base_name} for {platform_clean}"
            
        elif has_cloud:
            # base_name has "Cloud" but not "Cloud SDK" (e.g., "GroupDocs.Editor Cloud")
            if platform_clean.lower() == "cloud":
                expected_name = base_name  # Use as-is
            else:
                expected_name = f"{base_name} SDK for {platform_clean}"
                
        else:
            # base_name doesn't have "Cloud" at all
            if platform_clean.lower() == "cloud":
                expected_name = f"{base_name} Cloud"
            else:
                expected_name = f"{base_name} Cloud SDK for {platform_clean}"
    else:
        # For non-Cloud brands (regular Aspose, GroupDocs, Conholdate)
        if platform_clean.lower() == "cloud":
            expected_name = f"{base_name} Cloud"
        else:
            expected_name = f"{base_name} for {platform_clean}"
    
    print(f"DEBUG: Expected product name: '{expected_name}'")
    
    # Case-insensitive matching
    product_info = next(
        (
            p for p in products
            if p["ProductName"].lower() == expected_name.lower()
        ),
        None
    )

    if not product_info:
        # Try to find a close match for better error message
        available_products = [p["ProductName"] for p in products]
        similar = [p for p in available_products if base_name.lower() in p.lower()]
        
        error_msg = (
            f"No product found for '{product_name}' with platform '{platform}' and brand '{brand}'.\n"
            f"Expected product name: '{expected_name}'\n"
        )
        
        if similar:
            error_msg += f"Similar products found: {', '.join(similar[:5])}"
        else:
            error_msg += f"Available products: {', '.join(available_products[:5])}"
        
        raise ValueError(error_msg)

    return product_info


def prepare_context(product_info) -> str:
    context=''
    # Prepare context
    for k, v in product_info.items():
        context += f"\n{k}: {v}"
    return context


def sanitize_for_hugo(text):
    """Remove or replace characters that break Hugo/Markdown rendering"""
    if not text:
        return text
    
    replacements = {
        '\u2013': '-',      # en dash
        '\u2014': '-',      # em dash
        '\u2015': '-',      # horizontal bar
        '\u2212': '-',      # minus sign
        '\u201c': '"',      # left double quote
        '\u201d': '"',      # right double quote
        '\u2018': "'",      # left single quote
        '\u2019': "'",      # right single quote
        '\u2026': '...',    # ellipsis
        '\u00a0': ' ',      # non-breaking space
        '\u200b': '',       # zero-width space
        '\u200c': '',       # zero-width non-joiner
        '\u200d': '',       # zero-width joiner
        '\ufeff': '',       # zero-width no-break space (BOM)
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Remove any remaining non-ASCII characters that might cause issues
    # (optional - only if you want strict ASCII)
    # result = result.encode('ascii', 'ignore').decode('ascii')
    
    return result

def generate_snippet_filename(title: str, language: str, section_heading: str, index: int, total_snippets: int) -> str:
    """Generate a clean, meaningful filename from title + language + section keyword."""
    
    noise_words = {
        "complete", "code", "example", "step", "by", "via", "rest", "api",
        "implementation", "snippet", "sample", "the", "a", "an", "and", "or",
        "for", "to", "in", "with", "using", "how", "guide", "tutorial"
    }
    
    # Slugify title
    title_slug = re.sub(r'[^\w\s]', '', title.lower())
    title_words = [w for w in title_slug.split() if w not in noise_words][:4]
    title_part = "_".join(title_words)
    
    # Extract keyword from section heading — skip words already in title
    title_word_set = set(title_words)
    section_slug = re.sub(r'[^\w\s]', '', section_heading.lower())
    section_words = [w for w in section_slug.split() if w not in noise_words and w not in title_word_set][:3]
    section_part = "_".join(section_words)
    
    extension = get_file_extension(language)
    
    # If section adds nothing new, just use title_part alone
    if section_part:
        filename = f"{title_part}_{section_part}.{extension}"
    else:
        filename = f"{title_part}.{extension}"
    
    # Clean up double underscores
    filename = re.sub(r'_+', '_', filename).strip('_')
    
    return filename

async def extract_all_complete_code_snippets(markdown_content: str, title: str = "",metrics=None) -> dict:
    """
    Extract ALL complete code snippets marked with COMPLETE_CODE_SNIPPET tags
    """
    import re
    import sys
    
    markdown_content = markdown_content.replace('\r\n', '\n').replace('\r', '\n')
    
    snippets = {}
    snippet_index = 1
    used_filenames = {}
    
    print("\n" + "="*60, file=sys.stderr, flush=True)
    print("Searching for COMPLETE_CODE_SNIPPET tags in entire document...", file=sys.stderr, flush=True)
    print("="*60, file=sys.stderr, flush=True)
    
    code_pattern_1 = (
        r'<!--\s*\[COMPLETE_CODE_SNIPPET_START\]\s*-->'
        r'\s*'
        r'```(\w*)'
        r'\s*'
        r'(.*?)'
        r'```'
        r'\s*'
        r'<!--\s*\[COMPLETE_CODE_SNIPPET_END\]\s*-->'
    )
    
    matches = list(re.finditer(code_pattern_1, markdown_content, re.DOTALL))
    
    if matches:
        total_snippets = len(matches)
        print(f"✓ Found {total_snippets} COMPLETE_CODE_SNIPPET tag pairs", file=sys.stderr, flush=True)
        
        for match in matches:
            matched_text = match.group(0)
            language = match.group(1).strip() or 'text'
            code = match.group(2).strip()
            
            match_start = match.start()
            text_before = markdown_content[:match_start]
            section_match = re.findall(r'##\s+([^\n]+)', text_before)
            task_name = section_match[-1].strip() if section_match else f"Code Example {snippet_index}"
            
            print(f"\n🔍 Processing snippet {snippet_index}", flush=True, file=sys.stderr)
            print(f"  Section: '{task_name}'", flush=True, file=sys.stderr)
            print(f"  Language: {language}", flush=True, file=sys.stderr)
            print(f"  Code length: {len(code)} chars", flush=True, file=sys.stderr)
            
            if not code or len(code.strip()) == 0:
                print(f"  ❌ Code is empty, skipping", flush=True, file=sys.stderr)
                continue
            
            if len(code) < 50:
                print(f"  ⚠ Code is short ({len(code)} chars), but extracting anyway", flush=True, file=sys.stderr)
            
            filename = await generate_gist_filename_via_llm(title, task_name, language, metrics)

            # Fallback to slug-based if LLM fails
            if not filename:
                filename = generate_snippet_filename(title, language, task_name, snippet_index, total_snippets)            
            # Handle collisions
            if filename in used_filenames.values():
                base, ext = filename.rsplit(".", 1)
                filename = f"{base}_{snippet_index}.{ext}"
            
            used_filenames[snippet_index] = filename
            key = f"snippet_{snippet_index}_{filename.split('.')[0]}"
            
            code_lines = [line for line in code.split('\n') if line.strip()]
            
            snippets[key] = {
                "language": language,
                "extension": get_file_extension(language),
                "code": code,
                "task_name": task_name,
                "matched_text": matched_text,
                "filename": filename,
                "code_lines": len(code.split('\n')),
                "code_lines_non_empty": len(code_lines),
                "code_length": len(code),
                "has_tags": True
            }
            
            print(f"  ✅ Extracted: {filename} ({len(code)} chars, {len(code_lines)} non-empty lines)", flush=True, file=sys.stderr)
            snippet_index += 1
    
    # =========================================================================
    # Pattern 2: CODE_SNIPPET_START_COMPLETE (alternative tag format)
    # =========================================================================
    if not snippets:
        print("\nNo COMPLETE_CODE_SNIPPET tags found, trying CODE_SNIPPET_START_COMPLETE...", file=sys.stderr, flush=True)
        
        code_pattern_2 = (
            r'<!--\s*\[CODE_SNIPPET_START_COMPLETE\]\s*-->'
            r'\s*```(\w*)\s*'
            r'(.*?)'
            r'```\s*'
            r'<!--\s*\[CODE_SNIPPET_END_COMPLETE\]\s*-->'
        )
        
        matches = list(re.finditer(code_pattern_2, markdown_content, re.DOTALL))
        
        if matches:
            total_snippets = len(matches)
            print(f"✓ Found {total_snippets} CODE_SNIPPET_START_COMPLETE tag pairs", file=sys.stderr, flush=True)
            
            for match in matches:
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
                
                match_start = match.start()
                text_before = markdown_content[:match_start]
                section_match = re.findall(r'##\s+([^\n]+)', text_before)
                task_name = section_match[-1].strip() if section_match else f"Code Example {snippet_index}"
                
                if not code or len(code.strip()) == 0:
                    continue
                
                filename = generate_snippet_filename(title, language, task_name, snippet_index, total_snippets)
                
                if filename in used_filenames.values():
                    base, ext = filename.rsplit(".", 1)
                    filename = f"{base}_{snippet_index}.{ext}"
                
                used_filenames[snippet_index] = filename
                key = f"snippet_{snippet_index}_{filename.split('.')[0]}"
                code_lines = [line for line in code.split('\n') if line.strip()]
                
                snippets[key] = {
                    "language": language,
                    "extension": get_file_extension(language),
                    "code": code,
                    "task_name": task_name,
                    "matched_text": matched_text,
                    "filename": filename,
                    "code_lines": len(code.split('\n')),
                    "code_lines_non_empty": len(code_lines),
                    "code_length": len(code),
                    "has_tags": True
                }
                
                print(f"  ✅ Extracted snippet {snippet_index}: {filename}", flush=True, file=sys.stderr)
                snippet_index += 1
    
    # =========================================================================
    # Fallback: Look for "Complete Code Example" sections with any code
    # =========================================================================
    if not snippets:
        print("\nNo tagged snippets found, searching for 'Complete Code Example' sections...", file=sys.stderr, flush=True)
        
        section_pattern = r'##\s+([^#\n]+?)\s*-?\s*Complete\s+Code\s+Example[^\n]*\n(.*?)(?=\n##|\Z)'
        sections = list(re.finditer(section_pattern, markdown_content, re.DOTALL | re.IGNORECASE))
        total_snippets = len(sections)
        
        for section in sections:
            task_name = section.group(1).strip()
            section_content = section.group(2)
            
            code_pattern = r'```(\w*)\s*(.*?)```'
            code_matches = list(re.finditer(code_pattern, section_content, re.DOTALL))
            
            if code_matches:
                largest = max(code_matches, key=lambda m: len(m.group(2)))
                language = largest.group(1).strip() or 'text'
                code = largest.group(2).strip()
                
                if code and len(code) > 0:
                    filename = generate_snippet_filename(title, language, task_name, snippet_index, total_snippets)
                    
                    if filename in used_filenames.values():
                        base, ext = filename.rsplit(".", 1)
                        filename = f"{base}_{snippet_index}.{ext}"
                    
                    used_filenames[snippet_index] = filename
                    key = f"snippet_{snippet_index}_{filename.split('.')[0]}"
                    
                    snippets[key] = {
                        "language": language,
                        "extension": get_file_extension(language),
                        "code": code,
                        "task_name": task_name,
                        "matched_text": largest.group(0),
                        "filename": filename,
                        "code_lines": len(code.split('\n')),
                        "code_lines_non_empty": len([l for l in code.split('\n') if l.strip()]),
                        "code_length": len(code),
                        "has_tags": False
                    }
                    
                    print(f"  ✅ Extracted from section: {filename}", flush=True, file=sys.stderr)
                    snippet_index += 1
    
    separator = "=" * 60
    print(f"\n{separator}", file=sys.stderr, flush=True)
    if snippets:
        print(f"✅ Successfully extracted {len(snippets)} code snippet(s)", file=sys.stderr, flush=True)
        for key, data in snippets.items():
            print(f"   - {data['filename']}: {data['code_length']} chars, {data['code_lines_non_empty']} lines of code", file=sys.stderr, flush=True)
    else:
        print("⚠️ WARNING: No code snippets found", file=sys.stderr, flush=True)
    print(f"{separator}\n", file=sys.stderr, flush=True)
    
    return snippets


def get_file_extension(language: str) -> str:
    """Map language identifier to file extension"""
    extensions = {
        'python': 'py',
        'javascript': 'js',
        'typescript': 'ts',
        'java': 'java',
        'csharp': 'cs',
        'c#': 'cs',
        'cpp': 'cpp',
        'c++': 'cpp',
        'c': 'c',
        'go': 'go',
        'rust': 'rs',
        'ruby': 'rb',
        'php': 'php',
        'swift': 'swift',
        'kotlin': 'kt',
        'scala': 'scala',
        'html': 'html',
        'css': 'css',
        'sql': 'sql',
        'bash': 'sh',
        'shell': 'sh',
        'powershell': 'ps1',
        'json': 'json',
        'xml': 'xml',
        'yaml': 'yml',
        'markdown': 'md',
    }
    return extensions.get(language.lower(), 'txt')

async def upload_to_gist(
    files_dict: dict,  # {"file1.java": "code1", "file2.py": "code2"}
    description: str = "",
    token: str = "",
    gist_name: str = "",
    url: str = "" ,
    summary:str=""
) -> dict:
    """
    Upload code to GitHub Gist - handles single or multiple files intelligently
    
    Args:
        files_dict: Dictionary of {filename: code_content}
        description: Gist description
        token: GitHub token
        gist_name: Gist owner name
    
    Returns:
        dict: {
            "gist_id": "abc123",
            "shortcodes": {
                "file1.java": "{{< gist ... >}}",
                "file2.py": "{{< gist ... >}}"
            }
        }
    """
    print(f"Uploading {len(files_dict)} file(s) to gist...", flush=True, file=sys.stderr)

    # --- Token Check (fail fast) ---
    if not token:
        return {"error": "GITHUB_TOKEN environment variable not set"}
    print(f"🔑 GITHUB_TOKEN found", flush=True, file=sys.stderr)

    # --- Build readme.md (renders above code files; sorts first alphabetically) ---
    readme_lines = [f"# {description}"]
    if summary:
        readme_lines.append(f"\n{summary.strip().strip(chr(34)).strip(chr(39))}")
    if url:
        readme_lines.append(f"\nRead the full guide here: [{url}]({url})")
    readme_content = "\n".join(readme_lines)

    # --- Build files object (readme.md first, then code files) ---
    gist_files = {"readme.md": {"content": readme_content}}
    gist_files.update({
        filename: {"content": content}
        for filename, content in files_dict.items()
    })
    
    
    # --- Send Request ---
    response = requests.post(
        "https://api.github.com/gists",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        },
        json={
            "description": description,
            "public": True,
            "files": gist_files
        }
    )
    
    # --- Handle Response ---
    if response.ok:
        gist = response.json()
        gist_id = gist['id']
        
        # Generate shortcodes for each file
        shortcodes = {}
        for file_name in gist['files'].keys():
            if file_name == "readme.md":   # <-- skip the readme
                continue
            shortcodes[file_name] = f'{{{{< gist "{gist_name}" "{gist_id}" "{file_name}" >}}}}'
            print(f"✓ Created shortcode for {file_name}", flush=True, file=sys.stderr)
        
        print(f"✓ Gist created: {gist_id} with {len(shortcodes)} file(s)", flush=True, file=sys.stderr)
        
        return {
            "success": True,
            "gist_id": gist_id,
            "shortcodes": shortcodes,
            "gist_url": gist['html_url']
        }
    
    error_msg = f"Error {response.status_code}: {response.text}"
    print(f"❌ {error_msg}", flush=True, file=sys.stderr)
    return {
        "success": False,
        "error": error_msg
    }

def replace_code_snippets_with_gists(markdown_content: str, snippets: dict, shortcodes_map: dict) -> str:
    """
    Replace all code snippets with their corresponding gist shortcodes
    """
    updated_content = markdown_content
    
    for key, data in snippets.items():
        filename = data['filename']
        matched_text = data['matched_text']
        
        # Get the corresponding gist shortcode
        if filename in shortcodes_map:
            gist_shortcode = shortcodes_map[filename]
            
            # Verify the matched_text exists before replacing
            if matched_text in updated_content:
                # Replace ONLY the matched text with gist shortcode
                updated_content = updated_content.replace(matched_text, gist_shortcode, 1)
                print(f"✓ Replaced {filename} with gist (removed {len(matched_text)} chars)", flush=True, file=sys.stderr)
            else:
                print(f"⚠ Matched text not found in content for {filename}", flush=True, file=sys.stderr)
                print(f"  Looking for: {matched_text[:100]}...", flush=True, file=sys.stderr)
        else:
            print(f"⚠ No gist found for {filename}", flush=True, file=sys.stderr)
    
    return updated_content


def inject_file_format_links(full_markdown, FILE_FORMAT_MAPPINGS, BASE_URL):
    # --- 1. Separate Frontmatter ---
    parts = re.split(r'^---$', full_markdown, maxsplit=2, flags=re.MULTILINE)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = parts[2]
    else:
        frontmatter = None
        body = full_markdown
    
    # --- 2. Protect ALL contexts where we should NOT add links ---
    placeholders = []
    
    def hide_content(match):
        placeholders.append(match.group(0))
        return f"%%CONTENT_HOLDER_{len(placeholders)-1}%%"
    
    # Protect in order of specificity:
    
    # 2a. Hide fenced code blocks (```)
    body_protected = re.sub(r'```.*?```', hide_content, body, flags=re.DOTALL)
    
    # 2b. Hide inline code (`)
    body_protected = re.sub(r'`[^`]+`', hide_content, body_protected)
    
    # 2c. Hide existing Markdown links COMPLETELY: [any text](any url)
    body_protected = re.sub(r'\[[^\]]+\]\([^)]+\)', hide_content, body_protected)
    
    # 2d. Hide HTML tags and their contents
    body_protected = re.sub(r'<[^>]+>', hide_content, body_protected)
    
    # 2e. Hide URLs that aren't in markdown link format (bare URLs)
    body_protected = re.sub(r'https?://[^\s\)]+', hide_content, body_protected)
    
    # 2f. Hide image references ![alt](url)
    body_protected = re.sub(r'!\[[^\]]*\]\([^)]+\)', hide_content, body_protected)
    
    # 2g. Hide any text within parentheses that contains forward slashes (likely paths/URLs)
    body_protected = re.sub(r'\([^)]*\/[^)]*\)', hide_content, body_protected)
    
    # --- 3. Inject Links into Body (ONLY standalone terms) ---
    sorted_keys = sorted(FILE_FORMAT_MAPPINGS.keys(), key=len, reverse=True)
    
    # STRICT pattern: Must be completely standalone
    # - Not preceded by: letters, numbers, underscore, dot, hyphen, forward slash, colon
    # - Not followed by: letters, numbers, underscore, dot, hyphen, forward slash, colon
    # This ensures -png and .png are ignored
    pattern = r'(?<![A-Za-z0-9_.\/:-])\b(' + '|'.join(re.escape(k) for k in sorted_keys) + r')\b(?![A-Za-z0-9_.\/:-])'
    
    linked_terms = set()
    
    def replace_logic(match):
        found_text = match.group(1)
        lookup_key = next((k for k in sorted_keys if k.lower() == found_text.lower()), None)
        
        # Only link the first occurrence of each term
        if lookup_key and lookup_key.lower() not in linked_terms:
            linked_terms.add(lookup_key.lower())
            return f"[{found_text}]({BASE_URL}{FILE_FORMAT_MAPPINGS[lookup_key]})"
        return found_text
    
    body_linked = re.sub(pattern, replace_logic, body_protected, flags=re.IGNORECASE)
    
    # --- 4. Restore Protected Content ---
    for i in range(len(placeholders) - 1, -1, -1):
        body_linked = body_linked.replace(f"%%CONTENT_HOLDER_{i}%%", placeholders[i])
    
    # --- 5. Reassemble ---
    if frontmatter:
        return f"---{frontmatter}---\n{body_linked}"
    return body_linked



import re

def normalize_case_preserve_formats_in_keywords(text_array, file_formats):
    """
    Lowercase the first letter and all other words (except file formats, product names, 
    and common suffix words) while preserving file formats in uppercase.
    
    Args:
        text_array: List of strings to process
        file_formats: List of file format names to keep uppercase
    
    Returns:
        List of processed strings with normalized casing
    """
    # Comprehensive list of words to lowercase
    lowercase_words = [
        # Articles
        'a', 'an', 'the',
        
        # Prepositions
        'to', 'from', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 
        'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 
        'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'until', 'without', 'within', 'upon', 'via',
        'per', 'plus', 'minus', 'across', 'among', 'around', 'behind', 'beside',
        'beyond', 'inside', 'outside', 'throughout', 'toward', 'towards', 'underneath',
        'unlike', 'onto', 'past', 'since', 'near', 'next', 'opposite', 'regarding',
        
        # Conjunctions
        'and', 'or', 'but', 'nor', 'so', 'yet', 'as', 'if', 'because', 'although',
        'though', 'unless', 'while', 'whereas', 'whether',
        
        # Common verbs (infinitive and conjugated forms)
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'make', 'makes', 'made', 'making', 'get', 'gets', 'got',
        'create', 'creates', 'created', 'creating', 'build', 'builds', 'built', 'building',
        'develop', 'develops', 'developed', 'developing', 'design', 'designs', 'designed', 'designing',
        'convert', 'converts', 'converted', 'converting', 'change', 'changes', 'changed', 'changing',
        'transform', 'transforms', 'transformed', 'transforming', 'edit', 'edits', 'edited', 'editing',
        'view', 'views', 'viewed', 'viewing', 'open', 'opens', 'opened', 'opening',
        'save', 'saves', 'saved', 'saving', 'export', 'exports', 'exported', 'exporting',
        'import', 'imports', 'imported', 'importing', 'download', 'downloads', 'downloaded', 'downloading',
        'upload', 'uploads', 'uploaded', 'uploading', 'generate', 'generates', 'generated', 'generating',
        'process', 'processes', 'processed', 'processing', 'render', 'renders', 'rendered', 'rendering',
        'parse', 'parses', 'parsed', 'parsing', 'compile', 'compiles', 'compiled', 'compiling',
        'extract', 'extracts', 'extracted', 'extracting', 'compress', 'compresses', 'compressed', 'compressing',
        'decompress', 'decompresses', 'decompressed', 'decompressing', 'merge', 'merges', 'merged', 'merging',
        'split', 'splits', 'splitting', 'join', 'joins', 'joined', 'joining',
        'combine', 'combines', 'combined', 'combining', 'separate', 'separates', 'separated', 'separating',
        'compare', 'compares', 'compared', 'comparing', 'validate', 'validates', 'validated', 'validating',
        'verify', 'verifies', 'verified', 'verifying', 'check', 'checks', 'checked', 'checking',
        'test', 'tests', 'tested', 'testing', 'analyze', 'analyzes', 'analyzed', 'analyzing',
        'scan', 'scans', 'scanned', 'scanning', 'search', 'searches', 'searched', 'searching',
        'find', 'finds', 'found', 'finding', 'replace', 'replaces', 'replaced', 'replacing',
        'insert', 'inserts', 'inserted', 'inserting', 'delete', 'deletes', 'deleted', 'deleting',
        'remove', 'removes', 'removed', 'removing', 'add', 'adds', 'added', 'adding',
        'update', 'updates', 'updated', 'updating', 'modify', 'modifies', 'modified', 'modifying',
        'read', 'reads', 'reading', 'write', 'writes', 'wrote', 'written', 'writing',
        'print', 'prints', 'printed', 'printing', 'display', 'displays', 'displayed', 'displaying',
        'show', 'shows', 'showed', 'shown', 'showing', 'hide', 'hides', 'hid', 'hidden', 'hiding',
        'enable', 'enables', 'enabled', 'enabling', 'disable', 'disables', 'disabled', 'disabling',
        'support', 'supports', 'supported', 'supporting', 'allow', 'allows', 'allowed', 'allowing',
        'provide', 'provides', 'provided', 'providing', 'offer', 'offers', 'offered', 'offering',
        'use', 'uses', 'used', 'using', 'apply', 'applies', 'applied', 'applying',
        'set', 'sets', 'setting', 'configure', 'configures', 'configured', 'configuring',
        'install', 'installs', 'installed', 'installing', 'uninstall', 'uninstalls', 'uninstalled', 'uninstalling',
        'load', 'loads', 'loaded', 'loading', 'unload', 'unloads', 'unloaded', 'unloading',
        'start', 'starts', 'started', 'starting', 'stop', 'stops', 'stopped', 'stopping',
        'run', 'runs', 'ran', 'running', 'execute', 'executes', 'executed', 'executing',
        'launch', 'launches', 'launched', 'launching', 'close', 'closes', 'closed', 'closing',
        'copy', 'copies', 'copied', 'copying', 'paste', 'pastes', 'pasted', 'pasting',
        'cut', 'cuts', 'cutting', 'undo', 'undoes', 'undid', 'undone', 'undoing',
        'redo', 'redoes', 'redid', 'redone', 'redoing', 'rotate', 'rotates', 'rotated', 'rotating',
        'resize', 'resizes', 'resized', 'resizing', 'crop', 'crops', 'cropped', 'cropping',
        'scale', 'scales', 'scaled', 'scaling', 'flip', 'flips', 'flipped', 'flipping',
        'mirror', 'mirrors', 'mirrored', 'mirroring', 'invert', 'inverts', 'inverted', 'inverting',
        'filter', 'filters', 'filtered', 'filtering', 'sort', 'sorts', 'sorted', 'sorting',
        'group', 'groups', 'grouped', 'grouping', 'ungroup', 'ungroups', 'ungrouped', 'ungrouping',
        'align', 'aligns', 'aligned', 'aligning', 'arrange', 'arranges', 'arranged', 'arranging',
        'optimize', 'optimizes', 'optimized', 'optimizing', 'enhance', 'enhances', 'enhanced', 'enhancing',
        'improve', 'improves', 'improved', 'improving', 'fix', 'fixes', 'fixed', 'fixing',
        'repair', 'repairs', 'repaired', 'repairing', 'recover', 'recovers', 'recovered', 'recovering',
        'restore', 'restores', 'restored', 'restoring', 'backup', 'backups', 'backed', 'backing',
        'preview', 'previews', 'previewed', 'previewing', 'review', 'reviews', 'reviewed', 'reviewing',
        'share', 'shares', 'shared', 'sharing', 'publish', 'publishes', 'published', 'publishing',
        'send', 'sends', 'sent', 'sending', 'receive', 'receives', 'received', 'receiving',
        'transfer', 'transfers', 'transferred', 'transferring', 'sync', 'syncs', 'synced', 'syncing',
        'synchronize', 'synchronizes', 'synchronized', 'synchronizing',
        
        # Common adjectives
        'online', 'offline', 'free', 'premium', 'pro', 'basic', 'advanced', 'simple', 'easy',
        'fast', 'quick', 'slow', 'high', 'low', 'best', 'better', 'good', 'bad', 'new', 'old',
        'modern', 'classic', 'professional', 'personal', 'public', 'private', 'secure', 'safe',
        'reliable', 'efficient', 'effective', 'powerful', 'lightweight', 'portable', 'compatible',
        'compatible', 'universal', 'standard', 'custom', 'automatic', 'manual', 'smart', 'intelligent',
        'interactive', 'responsive', 'adaptive', 'flexible', 'scalable', 'robust', 'stable',
        'latest', 'newest', 'updated', 'improved', 'enhanced', 'optimized', 'complete', 'full',
        'partial', 'total', 'entire', 'whole', 'main', 'primary', 'secondary', 'multiple', 'single',
        'unique', 'common', 'rare', 'popular', 'favorite', 'premium', 'deluxe', 'ultimate',
        'essential', 'necessary', 'optional', 'required', 'recommended', 'suggested', 'preferred',
        'available', 'unavailable', 'accessible', 'inaccessible', 'visible', 'invisible', 'hidden',
        'open', 'closed', 'active', 'inactive', 'enabled', 'disabled', 'supported', 'unsupported',
        
        # Common nouns (tools, features, etc.)
        'tool', 'tools', 'converter', 'converters', 'editor', 'editors', 'viewer', 'viewers',
        'generator', 'generators', 'creator', 'creators', 'maker', 'makers', 'builder', 'builders',
        'designer', 'designers', 'manager', 'managers', 'organizer', 'organizers', 'optimizer', 'optimizers',
        'analyzer', 'analyzers', 'scanner', 'scanners', 'reader', 'readers', 'writer', 'writers',
        'parser', 'parsers', 'compiler', 'compilers', 'interpreter', 'interpreters', 'processor', 'processors',
        'renderer', 'renderers', 'exporter', 'exporters', 'importer', 'importers', 'downloader', 'downloaders',
        'uploader', 'uploaders', 'compressor', 'compressors', 'decompressor', 'decompressors',
        'extractor', 'extractors', 'merger', 'mergers', 'splitter', 'splitters', 'joiner', 'joiners',
        'validator', 'validators', 'checker', 'checkers', 'tester', 'testers', 'debugger', 'debuggers',
        'application', 'applications', 'app', 'apps', 'program', 'programs', 'software', 'utility', 'utilities',
        'service', 'services', 'platform', 'platforms', 'system', 'systems', 'solution', 'solutions',
        'library', 'libraries', 'framework', 'frameworks', 'api', 'apis', 'sdk', 'sdks',
        'plugin', 'plugins', 'extension', 'extensions', 'addon', 'addons', 'module', 'modules',
        'component', 'components', 'widget', 'widgets', 'control', 'controls', 'element', 'elements',
        'feature', 'features', 'function', 'functions', 'functionality', 'option', 'options',
        'setting', 'settings', 'preference', 'preferences', 'configuration', 'configurations',
        'parameter', 'parameters', 'property', 'properties', 'attribute', 'attributes', 'value', 'values',
        'file', 'files', 'document', 'documents', 'page', 'pages', 'sheet', 'sheets',
        'slide', 'slides', 'image', 'images', 'picture', 'pictures', 'photo', 'photos',
        'graphic', 'graphics', 'icon', 'icons', 'logo', 'logos', 'banner', 'banners',
        'template', 'templates', 'theme', 'themes', 'style', 'styles', 'layout', 'layouts',
        'format', 'formats', 'type', 'types', 'kind', 'kinds', 'version', 'versions',
        'edition', 'editions', 'release', 'releases', 'update', 'updates', 'patch', 'patches',
        'mode', 'modes', 'view', 'views', 'display', 'displays', 'screen', 'screens',
        'window', 'windows', 'panel', 'panels', 'tab', 'tabs', 'menu', 'menus',
        'toolbar', 'toolbars', 'sidebar', 'sidebars', 'statusbar', 'statusbars', 'header', 'headers',
        'footer', 'footers', 'navigation', 'navigations', 'content', 'contents', 'section', 'sections',
        'chapter', 'chapters', 'part', 'parts', 'item', 'items', 'entry', 'entries',
        'record', 'records', 'data', 'information', 'details', 'text', 'code', 'script', 'scripts',
        'size', 'sizes', 'dimension', 'dimensions', 'resolution', 'resolutions', 'quality', 'qualities',
        'color', 'colors', 'colour', 'colours', 'background', 'backgrounds', 'foreground', 'foregrounds',
        'border', 'borders', 'margin', 'margins', 'padding', 'spacing', 'alignment', 'alignments',
        'position', 'positions', 'location', 'locations', 'path', 'paths', 'directory', 'directories',
        'folder', 'folders', 'drive', 'drives', 'disk', 'disks', 'storage', 'memory',
        'cache', 'buffer', 'queue', 'stack', 'list', 'lists', 'array', 'arrays',
        'table', 'tables', 'row', 'rows', 'column', 'columns', 'cell', 'cells',
        'field', 'fields', 'form', 'forms', 'input', 'inputs', 'output', 'outputs',
        'result', 'results', 'response', 'responses', 'request', 'requests', 'query', 'queries',
        'command', 'commands', 'action', 'actions', 'operation', 'operations', 'task', 'tasks',
        'process', 'job', 'jobs', 'workflow', 'workflows', 'pipeline', 'pipelines',
        'step', 'steps', 'stage', 'stages', 'phase', 'phases', 'level', 'levels',
        'layer', 'layers', 'object', 'objects', 'instance', 'instances', 'class', 'classes',
        'method', 'methods', 'event', 'events', 'handler', 'handlers', 'callback', 'callbacks',
        'error', 'errors', 'warning', 'warnings', 'message', 'messages', 'notification', 'notifications',
        'alert', 'alerts', 'dialog', 'dialogs', 'prompt', 'prompts', 'confirmation', 'confirmations',
        'user', 'users', 'account', 'accounts', 'profile', 'profiles', 'session', 'sessions',
        'login', 'logout', 'signin', 'signout', 'signup', 'register', 'registration',
        'password', 'passwords', 'username', 'usernames', 'email', 'emails', 'address', 'addresses',
        'link', 'links', 'url', 'urls', 'path', 'paths', 'route', 'routes',
        'connection', 'connections', 'network', 'networks', 'server', 'servers', 'client', 'clients',
        'database', 'databases', 'schema', 'schemas', 'index', 'indexes', 'indices',
        'key', 'keys', 'token', 'tokens', 'certificate', 'certificates', 'license', 'licenses',
        'permission', 'permissions', 'role', 'roles', 'group', 'groups', 'team', 'teams',
        'project', 'projects', 'workspace', 'workspaces', 'environment', 'environments',
        'package', 'packages', 'bundle', 'bundles', 'archive', 'archives', 'backup', 'backups',
        'copy', 'copies', 'duplicate', 'duplicates', 'clone', 'clones', 'snapshot', 'snapshots',
        'checkpoint', 'checkpoints', 'milestone', 'milestones', 'branch', 'branches', 'tag', 'tags',
        'commit', 'commits', 'change', 'changes', 'diff', 'diffs', 'patch', 'patches',
        'issue', 'issues', 'bug', 'bugs', 'fix', 'fixes', 'enhancement', 'enhancements',
        'feature', 'improvement', 'improvements', 'optimization', 'optimizations',
        'performance', 'speed', 'efficiency', 'accuracy', 'precision', 'reliability',
        'security', 'privacy', 'safety', 'protection', 'encryption', 'decryption',
        'compression', 'decompression', 'encoding', 'decoding', 'conversion', 'transformation',
        'translation', 'localization', 'internationalization', 'customization', 'personalization',
        'automation', 'integration', 'synchronization', 'migration', 'import', 'export',
        'batch', 'bulk', 'mass', 'multi', 'single', 'individual', 'specific', 'general',
        'default', 'custom', 'standard', 'advanced', 'expert', 'professional', 'enterprise',
        'business', 'commercial', 'corporate', 'industrial', 'educational', 'academic',
        'personal', 'home', 'office', 'desktop', 'mobile', 'web', 'cloud', 'local', 'remote',
        'source', 'target', 'destination', 'origin', 'input', 'output', 'start', 'end',
        'beginning', 'finish', 'first', 'last', 'initial', 'final', 'original', 'modified',
        'current', 'previous', 'next', 'recent', 'old', 'new', 'existing', 'available',
        
        # Temporal words
        'today', 'yesterday', 'tomorrow', 'now', 'later', 'soon', 'recently', 'currently',
        'always', 'never', 'sometimes', 'often', 'rarely', 'seldom', 'frequently',
        
        # Quantifiers
        'all', 'any', 'some', 'none', 'every', 'each', 'many', 'much', 'few', 'little',
        'several', 'various', 'numerous', 'countless', 'multiple', 'single', 'double', 'triple',
        'half', 'quarter', 'third', 'full', 'empty', 'partial', 'complete', 'incomplete',
        
        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
        'this', 'that', 'these', 'those', 'who', 'whom', 'whose', 'which', 'what',
        'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'yourselves', 'themselves',
        
        # Other common words
        'yes', 'no', 'maybe', 'ok', 'okay', 'please', 'thanks', 'thank', 'welcome',
        'hello', 'hi', 'bye', 'goodbye', 'help', 'support', 'guide', 'tutorial', 'demo',
        'example', 'sample', 'test', 'trial', 'beta', 'alpha', 'stable', 'experimental',
        'deprecated', 'legacy', 'obsolete', 'outdated', 'current', 'modern', 'classic',
    ]
    
    result = []
    
    for text in text_array:
        if not text:
            result.append(text)
            continue
        
        words = text.split()
        if not words:
            result.append(text)
            continue
        
        processed_words = []
        
        for i, word in enumerate(words):
            # Check if this word is a product name (contains dot)
            is_product_name = '.' in word
            
            # Check if this word is a file format (case-insensitive)
            is_file_format = word.upper() in [fmt.upper() for fmt in file_formats]
            
            # For the first word
            if i == 0:
                if is_product_name or is_file_format:
                    # Keep as-is
                    processed_words.append(word)
                else:
                    # Lowercase the first character only
                    processed_words.append(word[0].lower() + word[1:] if len(word) > 1 else word.lower())
            else:
                # For subsequent words
                if is_product_name or is_file_format:
                    # Keep as-is (will be uppercased later if it's a format)
                    processed_words.append(word)
                else:
                    # Check if it's a common word that should be lowercase
                    if word.lower() in lowercase_words:
                        processed_words.append(word.lower())
                    else:
                        # Keep original casing for other words (like "Chrome", brand names, etc.)
                        processed_words.append(word)
        
        # Join the words back
        processed = ' '.join(processed_words)
        
        # Ensure all file formats are uppercase everywhere in the text
        for fmt in file_formats:
            pattern = r'\b' + re.escape(fmt) + r'\b'
            processed = re.sub(pattern, fmt.upper(), processed, flags=re.IGNORECASE)
        
        result.append(processed)
    
    return result


def extract_protected_blocks(content: str) -> tuple[str, dict]:
    """
    Extract and protect markdown blocks that should not be modified.
    Returns content with placeholders and a dict of protected blocks.
    
    Protected elements:
    - Code blocks (```...```)
    - Inline code (`...`)
    - Images (![alt](url))
    - URLs/Links ([text](url))
    - HTML comments (<!-- ... -->)
    - Gist embeds or script tags
    
    Note: Frontmatter is NOT protected - we want to process titles there
    """
    protected = {}
    placeholder_content = content
    counter = 0
    
    # 1. Protect code blocks (```...```) - non-greedy, handles nested backticks
    def protect_code_block(match):
        nonlocal counter
        placeholder = f"___PROTECTED_CODE_BLOCK_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'```[\s\S]*?```',
        protect_code_block,
        placeholder_content,
        flags=re.MULTILINE
    )
    
    # 2. Protect inline code (`...`) - handles edge cases with multiple backticks
    def protect_inline_code(match):
        nonlocal counter
        placeholder = f"___PROTECTED_INLINE_CODE_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    # Match both single and double backticks, non-greedy
    placeholder_content = re.sub(
        r'``[^`]+``|`[^`\n]+`',
        protect_inline_code,
        placeholder_content
    )
    
    # 3. Protect images (![alt](url)) - handles optional title, spaces in URLs
    def protect_image(match):
        nonlocal counter
        placeholder = f"___PROTECTED_IMAGE_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'!\[([^\]]*)\]\(([^\)]+)\)',
        protect_image,
        placeholder_content
    )
    
    # 4. Protect links ([text](url)) - only the URL part, handles nested brackets
    def protect_link(match):
        nonlocal counter
        text = match.group(1)
        url = match.group(2)
        url_placeholder = f"___PROTECTED_URL_{counter}___"
        protected[url_placeholder] = url
        counter += 1
        return f"[{text}]({url_placeholder})"
    
    # More robust link pattern - handles spaces and special chars in URLs
    placeholder_content = re.sub(
        r'\[([^\]]+)\]\(([^\)]+)\)',
        protect_link,
        placeholder_content
    )
    
    # 5. Protect HTML comments (<!-- ... -->) - handles multiline
    def protect_comment(match):
        nonlocal counter
        placeholder = f"___PROTECTED_COMMENT_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'<!--[\s\S]*?-->',
        protect_comment,
        placeholder_content,
        flags=re.MULTILINE
    )
    
    # 6. Protect script tags (for gists) - handles attributes and multiline
    def protect_script(match):
        nonlocal counter
        placeholder = f"___PROTECTED_SCRIPT_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'<script[\s\S]*?</script>',
        protect_script,
        placeholder_content,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # 7. Protect HTML/XML tags that might contain dashes (e.g., <div class="my-class">)
    def protect_html_tag(match):
        nonlocal counter
        placeholder = f"___PROTECTED_HTML_TAG_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'<[^>]+>',
        protect_html_tag,
        placeholder_content
    )
    
    return placeholder_content, protected


def restore_protected_blocks(content: str, protected: dict) -> str:
    """Restore protected blocks back into the content."""
    for placeholder, original in protected.items():
        content = content.replace(placeholder, original)
    return content


def get_line_number(content: str, position: int) -> int:
    """Get line number for a given character position in content."""
    return content[:position].count('\n') + 1


def find_replacements_with_lines(content: str, pattern: str, replacement: str, pattern_name: str) -> list[dict]:
    """
    Find all occurrences of a pattern and return details including line numbers.
    
    Returns:
        List of dicts with: line_number, original_text, context, replacement
    """
    replacements = []
    
    for match in re.finditer(re.escape(pattern), content):
        start_pos = match.start()
        end_pos = match.end()
        line_num = get_line_number(content, start_pos)
        
        # Extract context (50 chars before and after)
        context_start = max(0, start_pos - 50)
        context_end = min(len(content), end_pos + 50)
        context = content[context_start:context_end]
        
        # Clean up context for display
        context = context.replace('\n', ' ').strip()
        
        replacements.append({
            'line_number': line_num,
            'pattern_name': pattern_name,
            'original': pattern,
            'replacement': replacement,
            'context': f"...{context}..."
        })
    
    return replacements


def remove_all_fancy_punctuation_with_tracking(content: str) -> tuple[str, dict, list[dict]]:
    """
    Remove all fancy/typographic punctuation with detailed tracking.
    Preserves code blocks, gists, images, and URLs.
    
    CONTEXT-AWARE EM DASH HANDLING:
    - In frontmatter title/seoTitle: Replace em dash with hyphen (-)
    - In headings (##, ###): Replace em dash with hyphen (-)
    - In regular text: Remove em dash completely
    
    Returns:
        tuple of (cleaned_content, stats, all_replacements)
        - cleaned_content: Content with fancy punctuation replaced
        - stats: Dict with counts of each type replaced
        - all_replacements: List of dicts with line numbers and contexts
    """
    # First, protect code blocks, images, URLs, etc.
    protected_content, protected_blocks = extract_protected_blocks(content)
    
    stats = {
        "em_dashes_in_frontmatter": 0,
        "em_dashes_in_headings": 0,
        "em_dashes_in_body": 0,
        "en_dashes": 0,
        "curly_double_quotes": 0,
        "curly_single_quotes": 0,
        "ellipsis": 0,
        "bullets": 0,
        "other": 0
    }
    
    all_replacements = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # SPECIAL HANDLING FOR EM DASHES (context-aware)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Split content into lines for context-aware processing
    lines = protected_content.split('\n')
    processed_lines = []
    
    # Detect frontmatter boundaries
    in_frontmatter = False
    frontmatter_delimiter_count = 0
    
    for line_idx, line in enumerate(lines, start=1):
        # Track frontmatter boundaries (between --- delimiters)
        if line.strip() == '---':
            frontmatter_delimiter_count += 1
            if frontmatter_delimiter_count <= 2:
                in_frontmatter = not in_frontmatter
        
        # Check if this line is a heading
        is_heading = line.strip().startswith('#') and not in_frontmatter
        
        # Check if this line is a frontmatter title field
        is_frontmatter_title = (
            in_frontmatter and 
            (line.strip().startswith('title:') or line.strip().startswith('seoTitle:'))
        )
        
        if '\u2014' in line:  # Em dash present
            if is_frontmatter_title or is_heading:
                # In frontmatter titles or headings: Replace with hyphen
                count = line.count('\u2014')
                for match in re.finditer(re.escape('\u2014'), line):
                    start_pos = match.start()
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(line), start_pos + 51)
                    context = line[context_start:context_end].strip()
                    
                    if is_frontmatter_title:
                        label = 'Em dash in frontmatter title (\u2014)'
                        stats["em_dashes_in_frontmatter"] += 1
                    else:
                        label = 'Em dash in heading (\u2014)'
                        stats["em_dashes_in_headings"] += 1
                    
                    all_replacements.append({
                        'line_number': line_idx,
                        'pattern_name': label,
                        'original': '\u2014',
                        'replacement': '-',
                        'context': f"...{context}..."
                    })
                
                line = line.replace('\u2014', '-')
                
            elif not in_frontmatter:
                # In body text: Remove completely (with smart spacing)
                count = line.count('\u2014')
                for match in re.finditer(re.escape('\u2014'), line):
                    start_pos = match.start()
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(line), start_pos + 51)
                    context = line[context_start:context_end].strip()
                    
                    all_replacements.append({
                        'line_number': line_idx,
                        'pattern_name': 'Em dash in body (\u2014)',
                        'original': '\u2014',
                        'replacement': '[removed]',
                        'context': f"...{context}..."
                    })
                
                # Smart removal: handle spacing around em dash
                # "word — word" → "word word"
                # "word—word" → "word word"
                line = re.sub(r'\s*\u2014\s*', ' ', line)
                stats["em_dashes_in_body"] += count
        
        processed_lines.append(line)
    
    protected_content = '\n'.join(processed_lines)
    
    # ═══════════════════════════════════════════════════════════════════════
    # HANDLE ALL OTHER PUNCTUATION (same throughout)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Define other replacements (excluding em dash which we already handled)
    replacements_map = [
        ("\u2013", "-", "En dash (\u2013)"),           # – (U+2013)
        ("\u201C", '"', "Left curly double quote (\u201C)"),   # " (U+201C)
        ("\u201D", '"', "Right curly double quote (\u201D)"),  # " (U+201D)
        ("\u2018", "'", "Left curly single quote (\u2018)"),   # ' (U+2018)
        ("\u2019", "'", "Right curly single quote (\u2019)"),  # ' (U+2019)
        ("\u2026", "...", "Ellipsis (\u2026)"),        # … (U+2026)
        ("\u2022", "-", "Bullet (\u2022)"),            # • (U+2022)
        ("\u00A9", "(c)", "Copyright (\u00A9)"),       # © (U+00A9)
        ("\u00AE", "(R)", "Registered (\u00AE)"),      # ® (U+00AE)
        ("\u2122", "(TM)", "Trademark (\u2122)"),      # ™ (U+2122)
        ("\u00B0", " degrees", "Degree (\u00B0)"),     # ° (U+00B0)
        ("\u00D7", "x", "Multiplication (\u00D7)"),    # × (U+00D7)
        ("\u00F7", "/", "Division (\u00F7)"),          # ÷ (U+00F7)
    ]
    
    # Process each replacement and track changes
    for original, replacement, name in replacements_map:
        if original in protected_content:
            # Find all occurrences with line numbers
            found = find_replacements_with_lines(protected_content, original, replacement, name)
            all_replacements.extend(found)
            
            # Perform replacement
            protected_content = protected_content.replace(original, replacement)
            
            # Update stats
            count = len(found)
            if "dash" in name.lower():
                stats["en_dashes"] += count
            elif "quote" in name.lower():
                if "double" in name.lower():
                    stats["curly_double_quotes"] += count
                else:
                    stats["curly_single_quotes"] += count
            elif "Ellipsis" in name:
                stats["ellipsis"] += count
            elif "Bullet" in name:
                stats["bullets"] += count
            else:
                stats["other"] += count
    
    # Restore protected blocks
    cleaned_content = restore_protected_blocks(protected_content, protected_blocks)
    
    return cleaned_content, stats, all_replacements


def clean_ai_generated_markdown(content: str, verbose: bool = True) -> str:
    """
    Main function to clean AI-generated markdown content.
    Removes all fancy punctuation that indicates AI generation.
    PRESERVES: Code blocks, gists, images, URLs, and other markdown elements.
    
    Args:
        content: Raw markdown content from LLM
        verbose: If True, print detailed cleanup report with line numbers
        
    Returns:
        Cleaned markdown content with all fancy punctuation replaced
    """
    # Perform cleanup with tracking
    cleaned_content, stats, replacements = remove_all_fancy_punctuation_with_tracking(content)
    
    total_replaced = sum(stats.values())
    
    if verbose:
        print("\n" + "=" * 70, file=sys.stderr)
        print("AI CONTENT CLEANUP - Markdown-Aware Processing", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        
        if total_replaced == 0:
            print(" No AI indicators found - content looks clean!", file=sys.stderr)
            print("=" * 70 + "\n", file=sys.stderr)
            return cleaned_content
        
        print(f"⚠️  Found {total_replaced} AI generation indicators\n", file=sys.stderr)
        
        # Group replacements by type
        by_type = {}
        for rep in replacements:
            pattern_name = rep['pattern_name']
            if pattern_name not in by_type:
                by_type[pattern_name] = []
            by_type[pattern_name].append(rep)
        
        # Display grouped results
        for pattern_name, items in by_type.items():
            print(f"📍 {pattern_name}: {len(items)} occurrence(s)", file=sys.stderr)
            
            # Show first 5 occurrences with line numbers
            for i, item in enumerate(items[:5], 1):
                print(f"   Line {item['line_number']}: '{item['original']}' → '{item['replacement']}'", file=sys.stderr)
                print(f"   Context: {item['context']}", file=sys.stderr)
            
            if len(items) > 5:
                print(f"   ... and {len(items) - 5} more occurrence(s)", file=sys.stderr)
        
        print(f"🔧 Cleanup completed: Replaced {total_replaced} fancy punctuation marks", file=sys.stderr)
        print("✅ Protected: Code blocks, inline code, images, URLs, gists", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
    
    return cleaned_content


def find_malformed_links(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    inline_code_re = re.compile(r'`[^`]+`')
    in_code_block = False

    patterns = [
        # ── 0. [text] (url)  →  [text](url)   (space between ] and open-paren)
        (
            re.compile(r'(?<!!)\[([^\[\]]{1,300})\]\s+\((https?://[^\s)]{1,500})\)'),
            r'[\1](\2)',
            'space_before_paren',
        ),

        # ── 1. [text (url)  →  [text](url)   (missing ] and space before open-paren)
        (
            re.compile(r'(?<!!)\[([^\[\]()]{1,300})\s+\((https?://[^\s)]{1,500})\)'),
            r'[\1](\2)',
            'missing_closing_bracket_space',
        ),

        # ── 2b. [text(url/  →  [text](url/)  (missing ] AND missing closing paren)
        (
            re.compile(
                r'(?<!!)\[([^\[\]()]{1,300})\((https?://[^\s)\]]{1,500})(?=\s|$)'
            ),
            r'[\1](\2)',
            'missing_closing_bracket_and_paren',
        ),

        # ── 3. [text(url)  →  [text](url)   (missing ] before open-paren, no space)
        (
            re.compile(r'(?<!!)\[([^\[\]()]{1,300})\((https?://[^\s)]{1,500})\)'),
            r'[\1](\2)',
            'missing_closing_bracket',
        ),

        # ── 4. [text](url  →  [text](url)   (missing closing paren)
        (
            re.compile(
                r'(?<!!)\[([^\[\]]{1,300})\]\((https?://[^\s)\]]{1,500})(?<![/)])$',
                re.MULTILINE
            ),
            r'[\1](\2)',
            'missing_closing_paren',
        ),

        # ── 5. [text]url  →  [text](url)   (missing open-paren entirely)
        (
            re.compile(r'(?<!!)\[([^\[\]]{1,300})\](https?://[^\s)]{1,500})(?!\))'),
            r'[\1](\2)',
            'missing_opening_paren',
        ),

        # ── 6. text](url)  →  [text](url)   (missing open-bracket)
        (
            re.compile(r'(?<!\[)(?<!\])([A-Za-z0-9][A-Za-z0-9 \t\.\-\/]{1,80})\]\((https?://[^\s)]{1,500})\)'),
            r'[\1](\2)',
            'missing_opening_bracket',
        ),

        # ── 7. text] (url)  →  [text](url)   (missing open-bracket, space before paren)
        (
            re.compile(r'(?<!\[)(?<!\])([A-Za-z0-9][A-Za-z0-9 \t\.\-\/]{1,80})\]\s+\((https?://[^\s)]{1,500})\)'),
            r'[\1](\2)',
            'missing_opening_bracket_space',
        ),

        # ── 8. (url)[text]  →  [text](url)   (reversed structure)
        (
            re.compile(r'(?<!!)\((https?://[^\s)]{1,500})\)\[([^\[\]]{1,300})\]'),
            r'[\2](\1)',
            'reversed_structure',
        ),

        # ── 9. text (url)  →  [text](url)   (missing both brackets)
        (
            re.compile(
                r'(?<!\])(?<!!)(?<!\[)'
                r'(?:(?<=\s)|(?<=\n)|(?<=\>)|(?:^))'
                r'([A-Za-z0-9][A-Za-z0-9 \t\.\-\/]{0,80}?)'
                r'\s*\((https?://[^\s)]{1,500})\)',
                re.MULTILINE
            ),
            r'[\1](\2)',
            'missing_both_brackets',
        ),

        # ── 10. [](url)  →  flagged, no auto-fix
        (
            re.compile(r'(?<!!)\[\]\((https?://[^\s)]{1,500})\)'),
            None,
            'empty_link_text',
        ),

        # ── 11. [text]()  →  flagged, no auto-fix
        (
            re.compile(r'(?<!!)\[([^\[\]]{1,300})\]\(\s*\)'),
            None,
            'empty_url',
        ),
        
    ]

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if len(line) > 2000:
            continue

        searchable = inline_code_re.sub(lambda m: ' ' * len(m.group()), line)

        for pattern_idx, (compiled_pattern, replacement, issue_type) in enumerate(patterns):
            for match in compiled_pattern.finditer(searchable):
                original = match.group(0)

                if re.fullmatch(r'!?\[[^\]]*\]\([^)]*\)', original):
                    continue

                suggested = compiled_pattern.sub(replacement, original) \
                    if replacement is not None else original

                issues.append({
                    'original':            original,
                    'suggested':           suggested,
                    'line_number':         line_num,
                    'context':             line.strip()[:80],
                    'issue_type':          issue_type,
                    'pattern':             compiled_pattern.pattern,
                    'replacement_pattern': replacement,
                    'pattern_index':       pattern_idx,
                })

    return issues

def extract_protected_regions(content: str) -> Tuple[str, Dict[str, str]]:
    protected = {}
    result = content
    counter = 0

    def make_placeholder(kind: str) -> str:
        nonlocal counter
        key = f"___PROTECTED_{kind}_{counter}___"
        counter += 1
        return key

    # 1. YAML frontmatter — must be first
    def protect_frontmatter(match):
        key = make_placeholder("FRONTMATTER")
        protected[key] = match.group(0)
        return key + "\n\n"

    result = re.sub(
        r'^---\s*\n.*?\n---\s*\n*',
        protect_frontmatter,
        result,
        count=1,
        flags=re.DOTALL | re.MULTILINE
    )

    # 2. Fenced code blocks — before HTML so XML inside code is safe
    def protect_code_block(match):
        key = make_placeholder("CODE_BLOCK")
        protected[key] = match.group(0)
        return key

    result = re.sub(
        r'```[\s\S]*?```|~~~[\s\S]*?~~~',
        protect_code_block,
        result
    )

    # 3. Inline code — before HTML tags
    def protect_inline_code(match):
        key = make_placeholder("INLINE_CODE")
        protected[key] = match.group(0)
        return key

    result = re.sub(
        r'``[^`]+``|`[^`\n]+`',
        protect_inline_code,
        result
    )

    # 4. HTML comments
    def protect_html_block(match):
        key = make_placeholder("HTML_BLOCK")
        protected[key] = match.group(0)
        return key

    result = re.sub(r'<!--[\s\S]*?-->', protect_html_block, result)

    # 5. Block-level HTML elements
    result = re.sub(
        r'<(?:script|style|pre|div|section|article|header|footer|nav)[\s\S]*?'
        r'</(?:script|style|pre|div|section|article|header|footer|nav)>',
        protect_html_block,
        result,
        flags=re.IGNORECASE
    )

    # 6. Single HTML tags
    def protect_html_tag(match):
        key = make_placeholder("HTML_TAG")
        protected[key] = match.group(0)
        return key

    result = re.sub(r'<[^>]{1,500}>', protect_html_tag, result)

    # 7. Autolinks <https://...>
    def protect_autolink(match):
        key = make_placeholder("AUTOLINK")
        protected[key] = match.group(0)
        return key

    result = re.sub(r'<(?:https?://|mailto:)[^>]{1,500}>', protect_autolink, result)

    # 8. Reference-style link definitions [ref]: url
    def protect_reference_def(match):
        key = make_placeholder("REFERENCE_DEF")
        protected[key] = match.group(0)
        return key

    result = re.sub(
        r'^\s*\[[^\]]{1,200}\]:\s+\S+(?:\s+"[^"]*")?$',
        protect_reference_def,
        result,
        flags=re.MULTILINE
    )

    # 9. Images ![alt](url)
    def protect_image(match):
        key = make_placeholder("IMAGE")
        protected[key] = match.group(0)
        return key

    result = re.sub(r'!\[[^\]]{0,500}\]\([^)]{1,500}\)', protect_image, result)
 
    # 10. Valid markdown links
    #     (?<![.\w]) — never match [ preceded by a dot or word char
    #     This prevents [3D Cloud SDK](url) from being matched inside
    #     the malformed [Aspose.3D Cloud SDK(url)
    valid_link_re = re.compile(
        r'(?<![.\w])(?<!!)\[([^\[\]]{1,500})\]\(([^)]{1,500})\)'
    )

    def protect_valid_link(match):
        key = make_placeholder("VALID_LINK")
        protected[key] = match.group(0)
        return key

    result = valid_link_re.sub(protect_valid_link, result)

    # 11. Reference-style link usage [text][ref]
    def protect_reference_link(match):
        key = make_placeholder("REFERENCE_LINK")
        protected[key] = match.group(0)
        return key

    result = re.sub(r'\[[^\]]{1,200}\]\[[^\]]{1,200}\]', protect_reference_link, result)

    return result, protected


def restore_protected_regions(content: str, protected: Dict[str, str]) -> str:
    for placeholder, original in protected.items():
        content = content.replace(placeholder, original)
    return content



def fix_malformed_links(content: str, verbose: bool = True) -> Tuple[str, int, List[Dict]]:
    protected_content, protected_blocks = extract_protected_regions(content)
    issues = find_malformed_links(protected_content)

    if not issues:
        if verbose:
            print("\n" + "=" * 70, file=sys.stderr)
            print("MARKDOWN LINK VALIDATION", file=sys.stderr)
            print("=" * 70, file=sys.stderr)
            print("✅ No malformed links found - all links are properly formatted!", file=sys.stderr)
            print("=" * 70 + "\n", file=sys.stderr)
        return content, 0, []

    lines = protected_content.split('\n')
    fixes_applied = 0
    in_code_block = False

    # Per line, keep only the highest-priority (lowest pattern_index) fixable issue
    line_fixes: Dict[int, Dict] = {}
    for issue in issues:
        if issue['replacement_pattern'] is None:
            continue
        ln = issue['line_number']
        if ln not in line_fixes:
            line_fixes[ln] = issue
        elif issue['pattern_index'] < line_fixes[ln]['pattern_index']:
            line_fixes[ln] = issue

    fixed_lines = []
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_code_block = not in_code_block
            fixed_lines.append(line)
            continue

        if in_code_block:
            fixed_lines.append(line)
            continue

        if line_num in line_fixes:
            issue = line_fixes[line_num]
            new_line = line.replace(issue['original'], issue['suggested'], 1)
            if new_line != line:
                fixes_applied += 1
                line = new_line

        fixed_lines.append(line)

    fixed_content = '\n'.join(fixed_lines)
    fixed_content = restore_protected_regions(fixed_content, protected_blocks)

    if verbose:
        issue_labels = {
            'space_before_paren':                'Space between ] and (',
            'missing_closing_bracket_space':     'Missing ] with space before (',
            'missing_closing_bracket':           'Missing closing bracket ]',
            'missing_closing_bracket_and_paren': 'Missing ] and closing )',
            'missing_closing_paren':             'Missing closing parenthesis )',
            'missing_opening_paren':             'Missing opening parenthesis (',
            'missing_opening_bracket':           'Missing opening bracket [',
            'missing_opening_bracket_space':     'Missing [ with space before (',
            'reversed_structure':                'Reversed structure (url)[text]',
            'missing_both_brackets':             'Missing both brackets — text + bare (url)',
            'empty_link_text':                   'Empty link text []',
            'empty_url':                         'Empty URL ()',
        }

        print("\n" + "=" * 70, file=sys.stderr)
        print("MARKDOWN LINK VALIDATION & REPAIR", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"⚠️  Found {len(issues)} malformed link(s)\n", file=sys.stderr)

        by_type: Dict[str, List[Dict]] = {}
        for issue in issues:
            by_type.setdefault(issue['issue_type'], []).append(issue)

        for issue_type, type_issues in by_type.items():
            label = issue_labels.get(issue_type, issue_type)
            print(f"📍 {label}: {len(type_issues)} occurrence(s)", file=sys.stderr)
            for issue in type_issues[:3]:
                print(f"   Line {issue['line_number']}: "
                      f"'{issue['original']}' → '{issue['suggested']}'", file=sys.stderr)
                print(f"   Context: {issue['context']}", file=sys.stderr)
            if len(type_issues) > 3:
                print(f"   ... and {len(type_issues) - 3} more occurrence(s)", file=sys.stderr)

        fixable   = sum(1 for i in issues if i['replacement_pattern'] is not None)
        unfixable = len(issues) - fixable
        print(f"🔧 Repair completed: Fixed {fixes_applied} of {fixable} fixable link(s)", file=sys.stderr)
        if unfixable:
            print(f"⚠️  {unfixable} issue(s) require manual review", file=sys.stderr)
        print("✅ Protected: Frontmatter, code blocks, inline code, HTML, autolinks,", file=sys.stderr)
        print("              images, valid links, reference-style links", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)

    return fixed_content, fixes_applied, issues



def validate_markdown_links(content: str, fix_automatically: bool = True, verbose: bool = True) -> str:
    if fix_automatically:
        fixed_content, count, issues = fix_malformed_links(content, verbose=verbose)
        return fixed_content
    else:
        protected_content, _ = extract_protected_regions(content)
        issues = find_malformed_links(protected_content)
        if verbose and issues:
            print(f"\n⚠️  Found {len(issues)} malformed links (not fixed)", file=sys.stderr)
            for issue in issues[:5]:
                print(f"   Line {issue['line_number']}: {issue['original']}", file=sys.stderr)
        return content



def capitalize_file_formats_for_title(
    title: str, 
    file_format_mappings: Dict[str, str]
) -> str:
    """
    Capitalize file format names in a title based on FILE_FORMAT_MAPPINGS dict.
    
    This function works with your FILE_FORMAT_MAPPINGS dictionary structure where
    keys are file format names (e.g., "3D2", "3DS", "PDF") and values are paths.
    
    Args:
        title: The title string to process
        file_format_mappings: Dictionary with format names as keys
                              Example: {"PDF": "document/pdf/", "PNG": "image/png/"}
                     
    Returns:
        Title with matching file formats capitalized
        
    Examples:
        >>> mappings = {"3DS": "3d/3ds/", "STL": "3d/stl/", "PDF": "document/pdf/"}
        >>> capitalize_file_formats_from_mappings("Convert 3ds to stl", mappings)
        'Convert 3DS to STL'
    """
    # Extract format names from dictionary keys and convert to lowercase for matching
    format_set = {fmt.lower() for fmt in file_format_mappings.keys()}
    
    # Split title into words while preserving spaces and punctuation
    words = re.split(r'(\s+|[^\w\s])', title)
    
    result = []
    for word in words:
        if not word:  # Skip empty strings
            continue
            
        # Check if it's a whitespace or punctuation (preserve as-is)
        if re.match(r'^\s+$', word) or re.match(r'^[^\w\s]+$', word):
            result.append(word)
            continue
        
        word_lower = word.lower()
        
        # Check if the word matches any format in our mappings
        if word_lower in format_set:
            result.append(word.upper())
        else:
            # Preserve original capitalization
            result.append(word)
    
    return ''.join(result)



def sanitize_keywords(keywords_dict):
    """Recursively sanitize all keyword strings in the structure"""
    if isinstance(keywords_dict, dict):
        return {k: sanitize_keywords(v) for k, v in keywords_dict.items()}
    elif isinstance(keywords_dict, list):
        return [sanitize_keywords(item) for item in keywords_dict]
    elif isinstance(keywords_dict, str):
        return sanitize_for_hugo(keywords_dict)
    else:
        return keywords_dict
    
def parse_keywords_response(content):
    """Safely parse keywords from MCP response with multiple fallback strategies"""
    
    # Strategy 1: Direct dict access
    if hasattr(content, "data") and isinstance(content.data, dict):
        return content.data
    
    # Strategy 2: Parse text content
    if hasattr(content, "text") and content.text:
        text = content.text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                # Remove language identifier (json, python, etc.)
                if text.startswith(("json", "python", "py")):
                    text = text.split("\n", 1)[1] if "\n" in text else text[4:]
        
        text = text.strip()
        
        # Try multiple parsing strategies
        strategies = [
            # Standard JSON
            lambda: json.loads(text),
            # Python literal (handles single quotes)
            lambda: ast.literal_eval(text),
            # JSON with relaxed parsing (allows trailing commas, comments)
            lambda: json.loads(re.sub(r',(\s*[}\]])', r'\1', text)),
            # Remove any leading/trailing non-JSON text
            lambda: json.loads(re.search(r'\{.*\}', text, re.DOTALL).group())
        ]
        
        for strategy in strategies:
            try:
                return strategy()
            except (json.JSONDecodeError, ValueError, SyntaxError, AttributeError):
                continue
        
        # If all strategies fail, log the raw text for debugging
        print(f"PARSE ERROR - Raw text: {repr(text)}")
        raise ValueError(f"Unable to parse keywords response: {text[:200]}...")
    
    raise ValueError("No valid content found in response")


def setup_logger():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    LOG_FILE = os.path.join(BASE_DIR, "content", "logs", "logs.txt")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    print(f"Log file path: {LOG_FILE}")
    def log(message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        print(line, end="")  # console
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)

    return log



async def generate_tags_with_llm(
    post_topic: str,
    keywords: list[str],
    blog_outline: str,
    metrics=None
) -> list[str] | None:
    """
    Generate 3 relevant Hugo tags for a blog post using LLM.
    Returns a list of 3 tag strings, or None if all retries fail.
    """
    from services.LLMservice import llm_service
    MAX_RETRIES = 3

    keywords_str = ", ".join(keywords) if keywords else "none provided"

    instructions = f"""
You are a Hugo blog tag generator.

Your task:
- Generate exactly 3 relevant tags for the blog post described below
- Tags must be lowercase, hyphen-separated if multi-word (e.g. "leather-jackets")
- Tags must be specific, searchable, and relevant to the topic
- Do NOT use generic tags like "blog", "post", "article"
- Return ONLY the 3 tags as a comma-separated list — no explanations, no numbering, no extra text

Blog Topic: {post_topic}
Keywords: {keywords_str}
Outline:
{blog_outline}

Example output format:
gymwear, sweatsuit-design, streetwear-trends
"""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Generating Hugo tags for topic: '{post_topic}'...")

        try:
            result = await llm_service.run_agent(
                instructions=instructions,
                context="Generate 3 Hugo tags for the blog post above.",
                agent_name="hugo-tag-generator",
                temperature=0.5,
                max_turns=1
            )

            if metrics is not None:
                metrics.record_llm_usage(
                    input_tokens=result.token_usage["input_tokens"],
                    output_tokens=result.token_usage["output_tokens"]
                )

            print(f"  tags---- {result.token_usage['output_tokens']}-- {result.token_usage['input_tokens']}", flush=True)

            raw = result.final_output.strip().strip('"').strip("'")

            if not raw or len(raw.strip()) == 0:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM returned empty response")
                if attempt == MAX_RETRIES:
                    return None
                continue

            tags = [tag.strip().lower().replace("-", " ").replace("_", " ") for tag in raw.split(",")]
            tags = [tag for tag in tags if tag]  # remove empty strings

            if len(tags) == 3:
                print(f"  ✅ Valid tags generated on attempt {attempt}: {tags}")
                return tags
            else:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] Expected 3 tags, got {len(tags)}: {tags}")
                if attempt == MAX_RETRIES:
                    return None
                continue

        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            if attempt == MAX_RETRIES:
                return None
            continue

    print(f"  ❌ Could not generate tags after {MAX_RETRIES} attempts.")
    return None




def get_weekly_sheet_name() -> str:
    now = datetime.utcnow()
    # Get the Monday of the current week
    monday = now - timedelta(days=now.weekday())
    return monday.strftime("%Y-%m-%d")

def get_or_create_weekly_sheet(spreadsheet, sheet_name: str, headers: list):
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
    
    if sheet_name in existing_sheets:
        return spreadsheet.worksheet(sheet_name)
    else:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
        # Move weekly sheet to index 1 (right after consolidated at index 0)
        spreadsheet.reorder_worksheets([
            spreadsheet.worksheet(settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA),
            worksheet,
            *[spreadsheet.worksheet(ws) for ws in existing_sheets if ws != settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA]
        ])
        worksheet.append_row(headers)
        print(f"Created new weekly sheet: {sheet_name}")
        return worksheet
     

def convert_sheet_row_to_file_format(row: dict) -> dict:
    return {
        "topic": row.get("generated_title", ""),
        "product": row.get("product", ""),
        "platform": row.get("selected_platform", ""),
        "keywords": {
            "primary": [row.get("primary_keyword", "")],
            "secondary": [kw.strip() for kw in row.get("secondary_keywords", "").split("|")],
            "long_tail": [kw.strip() for kw in row.get("long_tail_keywords", "").split("|")],
            "semantic": [kw.strip() for kw in row.get("semantic_keywords", "").split("|")]
        },
        "outline": [item.strip() for item in row.get("outline", "").split("|")],
        "cluster_id": row.get("run_id", ""),
        "target_persona": row.get("target_persona", ""),
        "angle": row.get("angle", ""),
        "other_notes": [note.strip() for note in row.get("editorial_notes", "").split("|")],
        "layout": str(row.get("layout", "")).strip()
    }

def extract_blog_metadata(markdown_content: str) -> dict:
    def get_field(pattern, text):
        match = re.search(pattern, text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    frontmatter = re.search(r"^---\n(.*?)\n---", markdown_content, re.DOTALL)
    if not frontmatter:
        return {}

    fm = frontmatter.group(1)

    return {
        "title": get_field(r'^title:\s*"(.+?)"', fm),
        "url": get_field(r'^url:\s*(.+)', fm),
        "date": get_field(r'^date:\s*(.+)', fm),
        "author": get_field(r'^author:\s*"(.+?)"', fm),
        "summary": get_field(r'^summary:\s*(.+)', fm)
    }




# sheet automation functions

ROTATION_STATE_TAB = "RotationState"


def get_last_processed_product() -> str:
    """Round-robin pointer for fallback topic selection.

    Prefers the dedicated RotationState tab (written only by round-robin picks,
    so GSC-driven picks never move the pointer). Falls back to the legacy
    behavior — last row of the consolidated metadata tab — until the state tab
    exists.
    """
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA)

    try:
        state_value = spreadsheet.worksheet(ROTATION_STATE_TAB).acell("B1").value
        if state_value and state_value.strip():
            print(f"Rotation pointer from {ROTATION_STATE_TAB}: {state_value.strip()}")
            return state_value.strip()
    except gspread.WorksheetNotFound:
        pass

    worksheet = spreadsheet.worksheet(settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA)

    all_rows = worksheet.get_all_records()
    print(f"Headers detected: {all_rows[0].keys() if all_rows else 'empty'}")
    print(f"Last row: {all_rows[-1] if all_rows else 'empty'}")
    if not all_rows:
        print("Metadata sheet is empty, no last product found.")
        return None

    last_row = all_rows[-1]
    return last_row.get("Product", None)


def update_last_processed_product(product: str) -> None:
    """Advance the round-robin pointer (RotationState tab, cell B1).

    Called only after round-robin picks — GSC-driven picks leave the pointer
    untouched so the fallback rotation stays fair.
    """
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA)
    try:
        worksheet = spreadsheet.worksheet(ROTATION_STATE_TAB)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=ROTATION_STATE_TAB, rows=2, cols=2)
    worksheet.update([["Last Round-Robin Product", product]], "A1:B1")
    print(f"Rotation pointer updated to: {product}")


def get_next_tab() -> str:
    try:
        base_dir = get_project_root()
        key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(key_path, scopes=scopes)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_KEYWORDS)

        excluded_tabs = {"tracker", "sheet1", "template", "all missing topics"}
        all_tabs = [ws.title for ws in spreadsheet.worksheets() if ws.title.lower() not in excluded_tabs]

        print(f"Available tabs: {all_tabs}")

        last_product = get_last_processed_product()
        print(f"last_product returned: '{last_product}'")

        if not last_product or last_product not in all_tabs:
            start_index = 0
        else:
            start_index = (all_tabs.index(last_product) + 1) % len(all_tabs)

        for i in range(len(all_tabs)):
            index = (start_index + i) % len(all_tabs)
            tab_name = all_tabs[index]
            print(f"Checking tab: {tab_name}")

            result = get_topic_from_sheet(tab_name)
            if result:
                print(f"✅ Found approved topic in tab: {tab_name}")
                return tab_name

        print("❌ No approved topics found in any tab")
        return None

    except Exception as e:
        import traceback
        print(f"❌ Failed to get next tab: {e}")
        traceback.print_exc()
        return None


def get_topic_from_sheet(sheet_name: str) -> tuple[dict, int] | None:
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    worksheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_KEYWORDS).worksheet(sheet_name)

    all_rows = worksheet.get_all_records()

    if not all_rows:
        print(f"No rows found in tab: {sheet_name}")
        return None

    for i, row in enumerate(all_rows):
        if row.get("status", "").strip().lower() == "approved":
            row_number = i + 2  # +1 for 0-index, +1 for header row
            print(f"Found approved row at index {row_number}: {row}")
            formatted_data = convert_sheet_row_to_file_format(row)
            return formatted_data, row_number

    print(f"No approved rows found in tab: {sheet_name}")
    return None


def mark_topic_as_generated(sheet_name: str, row_number: int) -> None:
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    worksheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_KEYWORDS).worksheet(sheet_name)

    # Find the status column index
    headers = worksheet.row_values(1)
    if "status" not in [h.lower() for h in headers]:
        print("❌ Status column not found in sheet")
        return

    status_col = [h.lower() for h in headers].index("status") + 1  # 1-based

    worksheet.update_cell(row_number, status_col, "Generated")
    print(f"✅ Row {row_number} in '{sheet_name}' marked as Generated")


def save_blog_metadata_to_sheet(brand: str, url: str, title: str, author: str, gist_url: str, published_date: str, product: str = "", layout: str = "") -> None:
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    spreadsheet_id = settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA
    if not spreadsheet_id:
        print(f"❌ No spreadsheet configured for brand: {brand}")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(spreadsheet_id)
    headers = ["Published Date", "Product", "Blog Title", "Author", "Gist URL", "Blog URL", "Layout"]
    row = [published_date, product, title, author, gist_url, url, layout]

    # Save to consolidated sheet
    consolidated = spreadsheet.worksheet(settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA)
    if consolidated.row_count == 0 or not consolidated.row_values(1):
        consolidated.append_row(headers)
    consolidated.append_row(row)
    print(f"Saved to consolidated sheet: {row}")

    # Save to weekly sheet
    weekly_sheet_name = get_weekly_sheet_name()
    weekly = get_or_create_weekly_sheet(spreadsheet, weekly_sheet_name, headers)
    weekly.append_row(row)
    print(f"Saved to weekly sheet '{weekly_sheet_name}': {row}")


def get_recent_layouts(product: str, limit: int = 2) -> list[str]:
    """Return the layouts of the most recent posts for a product (newest last),
    read from the consolidated blog metadata sheet. Used by the layout selector
    to avoid repeating the same skeleton back-to-back within a product.

    Columns are read positionally (Product = col 2, Layout = col 7) because
    older rows predate the Layout column and get_all_records would choke on
    the header mismatch.
    """
    base_dir = get_project_root()
    key_path = os.path.join(base_dir, "keys", settings.GOOGLE_KEY)

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA)
    worksheet = spreadsheet.worksheet(settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA)

    layouts = []
    for row in worksheet.get_all_values()[1:]:
        if len(row) >= 7 and row[1].strip().lower() == product.strip().lower() and row[6].strip():
            layouts.append(row[6].strip())
    return layouts[-limit:]


def extract_product_names(names):
    return [
        {
            "ProductName": item.get("ProductName"),
            "ProductURL": item.get("ProductURL")
        }
        for item in names
        if "ProductName" in item and "ProductURL" in item
    ]

async def generate_gist_filename_via_llm(
    title: str,
    section_heading: str,
    language: str,
    metrics=None
) -> str | None:
    """
    Generate a clean, meaningful gist filename using LLM.
    Returns a filename string, or None if all retries fail.
    """
    from services.LLMservice import llm_service
    MAX_RETRIES = 3

    extension = get_file_extension(language)

    instructions = f"""
You are a code file naming assistant.

Your task:
- Generate a clean, concise filename for a code snippet
- Use snake_case
- Max 4 words
- Do NOT include the language name (extension already conveys it)
- Do NOT use noise words like: without, external, tools, simple, using, with, complete, example, code, guide, tutorial, step, basic, advanced
- Must reflect what the code actually does
- Return ONLY the filename with .{extension} extension — no explanations, no extra text

Topic: {title}
Section: {section_heading}
Language: {language}

Example output format:
svg_to_jpg.php
"""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Generating gist filename for: '{section_heading}'...",flush=True, file=sys.stderr)

        try:
            result = await llm_service.run_agent(
                instructions=instructions,
                context="Generate a clean filename for the code snippet above.",
                agent_name="gist-filename-generator",
                temperature=0.3,
                max_turns=1
            )

            if metrics is not None:
                metrics.record_llm_usage(
                    input_tokens=result.token_usage["input_tokens"],
                    output_tokens=result.token_usage["output_tokens"],
                    caller="gist-filename-generator"
                )

            raw = result.final_output.strip().strip('"').strip("'")

            if not raw or len(raw.strip()) == 0:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM returned empty response",flush=True, file=sys.stderr)
                if attempt == MAX_RETRIES:
                    return None
                continue

            # Sanitize
            filename = re.sub(r'[^\w.]', '_', raw)
            filename = re.sub(r'_+', '_', filename).strip('_')

            # Ensure correct extension
            if not filename.endswith(f".{extension}"):
                base = filename.rsplit(".", 1)[0] if "." in filename else filename
                filename = f"{base}.{extension}"

            print(f"  ✅ Filename generated on attempt {attempt}: {filename}",flush=True, file=sys.stderr)
            return filename

        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM call failed: {e}",flush=True, file=sys.stderr)
            import traceback
            traceback.print_exc()
            if attempt == MAX_RETRIES:
                return None
            continue

    print(f"  ❌ Could not generate filename after {MAX_RETRIES} attempts.",flush=True, file=sys.stderr)
    return None