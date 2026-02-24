import re, sys, os
from datetime import datetime
import requests
from typing import Dict, Any, Optional, List, Tuple

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


def parse_topic_details(
    topic_title: str, 
    details: str, 
    metadata: Dict[str, Optional[str]]
) -> Dict[str, Any]:
    """
    Parse individual topic details into structured format.
    
    Args:
        topic_title: Title of the topic
        details: Details string containing persona, angle, keywords, and outline
        metadata: Dictionary containing brand, product, platform info
        
    Returns:
        Dictionary with topic, product, platform, keywords, and outline
    """
    result = {
        "topic": topic_title.strip(),
        "product": metadata.get("product"),
        "platform": metadata.get("platform"),
        "keywords": {
            "primary": [],
            "secondary": []
        },
        "outline": []
    }
    
    # Extract cluster ID
    cluster_match = re.search(r'\*\*Cluster ID:\*\*\s*`([^`]+)`', details)
    if cluster_match:
        result["cluster_id"] = cluster_match.group(1).strip()
    
    # Extract target persona
    persona_match = re.search(r'\*\*Target persona:\*\*\s*(.+?)(?=\n-|\n\*\*|$)', details)
    if persona_match:
        result["target_persona"] = persona_match.group(1).strip()
    
    # Extract angle
    angle_match = re.search(r'\*\*Angle:\*\*\s*(.+?)(?=\n-|\n\*\*|$)', details)
    if angle_match:
        result["angle"] = angle_match.group(1).strip()
    
    # Extract primary keyword
    primary_match = re.search(r'\*\*Primary keyword:\*\*\s*`([^`]+)`', details)
    if primary_match:
        result["keywords"]["primary"].append(primary_match.group(1).strip())
    
    # Extract supporting keywords
    supporting_match = re.search(
        r'\*\*Supporting keywords:\*\*\s*(.+?)(?=\n\n|\n\*\*|$)',
        details,
        re.DOTALL
    )
    
    if supporting_match:
        keywords_text = supporting_match.group(1)
        # Extract all keywords within backticks
        keywords = re.findall(r'`([^`]+)`', keywords_text)
        result["keywords"]["secondary"] = [kw.strip() for kw in keywords if kw.strip()]
    
    # Extract outline items
    outline_match = re.search(
        r'\*\*Suggested outline:\*\*\s*((?:^-\s*.+$\n?)+)',
        details,
        re.MULTILINE
    )
    
    if outline_match:
        outline_text = outline_match.group(1)
        # Extract each bullet point
        outline_items = re.findall(r'^-\s*(.+)$', outline_text, re.MULTILINE)
        result["outline"] = [item.strip() for item in outline_items if item.strip()]
    
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
    """Convert text into a clean URL slug with C# → csharp normalization."""

    if not text:
        return ""

    # Normalize C# → CSharp BEFORE lowercasing
    text = text.replace("C#", "CSharp").replace("c#", "CSharp")

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
    
    # Normalize platform capitalization
    if platform_clean == "net":
        platform_clean = ".NET"
    elif platform_clean == "python-via-net":
        platform_clean = "Python via .NET"
    elif platform_clean == "java":
        platform_clean = "Java"
    elif platform_clean == "python":
        platform_clean = "Python"
    else:
        # Capitalize first letter for other platforms
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

def extract_all_complete_code_snippets(markdown_content: str) -> dict:
    """
    Extract ALL complete code snippets marked with COMPLETE_CODE_SNIPPET tags
    
    Searches for tags anywhere in the document, not just in specific section headers
    """
    import re
    import sys
    
    # Normalize line endings
    markdown_content = markdown_content.replace('\r\n', '\n').replace('\r', '\n')
    
    snippets = {}
    snippet_index = 1
    
    print("\n" + "="*60, file=sys.stderr, flush=True)
    print("Searching for COMPLETE_CODE_SNIPPET tags in entire document...", file=sys.stderr, flush=True)
    print("="*60, file=sys.stderr, flush=True)
    
    # =========================================================================
    # Strategy: Find ALL occurrences of COMPLETE_CODE_SNIPPET tags
    # anywhere in the document, regardless of section headers
    # =========================================================================
    
    # Pattern 1: COMPLETE_CODE_SNIPPET_START/END
    code_pattern_1 = (
        r'<!--\s*\[COMPLETE_CODE_SNIPPET_START\]\s*-->'  # Opening tag
        r'\s*'                                              # Optional whitespace
        r'```(\w*)'                                         # Opening code fence with language
        r'\s*'                                              # Optional whitespace
        r'(.*?)'                                            # Code content (non-greedy)
        r'```'                                              # Closing code fence
        r'\s*'                                              # Optional whitespace
        r'<!--\s*\[COMPLETE_CODE_SNIPPET_END\]\s*-->'     # Closing tag
    )
    
    matches = list(re.finditer(code_pattern_1, markdown_content, re.DOTALL))
    
    if matches:
        print(f"✓ Found {len(matches)} COMPLETE_CODE_SNIPPET tag pairs", file=sys.stderr, flush=True)
        
        for match in matches:
            matched_text = match.group(0)
            language = match.group(1).strip() or 'text'
            code = match.group(2).strip()
            
            # Find the section this code belongs to (look backwards for nearest H2)
            match_start = match.start()
            text_before = markdown_content[:match_start]
            
            # Find the most recent ## heading
            section_match = re.findall(r'##\s+([^\n]+)', text_before)
            task_name = section_match[-1].strip() if section_match else f"Code Example {snippet_index}"
            
            print(f"\n🔍 Processing snippet {snippet_index}", flush=True, file=sys.stderr)
            print(f"  Section: '{task_name}'", flush=True, file=sys.stderr)
            print(f"  Language: {language}", flush=True, file=sys.stderr)
            print(f"  Code length: {len(code)} chars", flush=True, file=sys.stderr)
            
            # Validate code
            if not code or len(code.strip()) == 0:
                print(f"  ❌ Code is empty, skipping", flush=True, file=sys.stderr)
                continue
            
            if len(code) < 50:
                print(f"  ⚠ Code is short ({len(code)} chars), but extracting anyway", 
                      flush=True, file=sys.stderr)
            
            # Create safe filename
            safe_task_name = re.sub(r'[^\w\s-]', '', task_name)
            safe_task_name = re.sub(r'[-\s]+', '_', safe_task_name)
            safe_task_name = safe_task_name.lower().strip('_')[:50]
            
            if not safe_task_name:
                safe_task_name = f"code_example_{snippet_index}"
            
            extension = get_file_extension(language)
            key = f"snippet_{snippet_index}_{safe_task_name}"
            filename = f"{safe_task_name}.{extension}"
            
            # Count lines
            code_lines = [line for line in code.split('\n') if line.strip()]
            total_lines = len(code.split('\n'))
            
            snippets[key] = {
                "language": language,
                "extension": extension,
                "code": code,
                "task_name": task_name,
                "matched_text": matched_text,
                "filename": filename,
                "code_lines": total_lines,
                "code_lines_non_empty": len(code_lines),
                "code_length": len(code),
                "has_tags": True
            }
            
            print(f"  ✅ Extracted: {filename} ({len(code)} chars, {len(code_lines)} non-empty lines)", 
                  flush=True, file=sys.stderr)
            
            snippet_index += 1
    
    # =========================================================================
    # Pattern 2: CODE_SNIPPET_START_COMPLETE (alternative tag format)
    # =========================================================================
    if not snippets:
        print("\nNo COMPLETE_CODE_SNIPPET tags found, trying CODE_SNIPPET_START_COMPLETE...", 
              file=sys.stderr, flush=True)
        
        code_pattern_2 = (
            r'<!--\s*\[CODE_SNIPPET_START_COMPLETE\]\s*-->'
            r'\s*```(\w*)\s*'
            r'(.*?)'
            r'```\s*'
            r'<!--\s*\[CODE_SNIPPET_END_COMPLETE\]\s*-->'
        )
        
        matches = list(re.finditer(code_pattern_2, markdown_content, re.DOTALL))
        
        if matches:
            print(f"✓ Found {len(matches)} CODE_SNIPPET_START_COMPLETE tag pairs", 
                  file=sys.stderr, flush=True)
            
            for match in matches:
                matched_text = match.group(0)
                language = match.group(1).strip() or 'text'
                code = match.group(2).strip()
                
                # Find section
                match_start = match.start()
                text_before = markdown_content[:match_start]
                section_match = re.findall(r'##\s+([^\n]+)', text_before)
                task_name = section_match[-1].strip() if section_match else f"Code Example {snippet_index}"
                
                if not code or len(code.strip()) == 0:
                    continue
                
                safe_task_name = re.sub(r'[^\w\s-]', '', task_name)
                safe_task_name = re.sub(r'[-\s]+', '_', safe_task_name).lower().strip('_')[:50]
                
                if not safe_task_name:
                    safe_task_name = f"code_example_{snippet_index}"
                
                extension = get_file_extension(language)
                key = f"snippet_{snippet_index}_{safe_task_name}"
                filename = f"{safe_task_name}.{extension}"
                
                code_lines = [line for line in code.split('\n') if line.strip()]
                
                snippets[key] = {
                    "language": language,
                    "extension": extension,
                    "code": code,
                    "task_name": task_name,
                    "matched_text": matched_text,
                    "filename": filename,
                    "code_lines": len(code.split('\n')),
                    "code_lines_non_empty": len(code_lines),
                    "code_length": len(code),
                    "has_tags": True
                }
                
                print(f"  ✅ Extracted snippet {snippet_index}: {filename}", 
                      flush=True, file=sys.stderr)
                
                snippet_index += 1
    
    # =========================================================================
    # Fallback: Look for "Complete Code Example" sections with any code
    # =========================================================================
    if not snippets:
        print("\nNo tagged snippets found, searching for 'Complete Code Example' sections...", 
              file=sys.stderr, flush=True)
        
        section_pattern = r'##\s+([^#\n]+?)\s*-?\s*Complete\s+Code\s+Example[^\n]*\n(.*?)(?=\n##|\Z)'
        sections = re.finditer(section_pattern, markdown_content, re.DOTALL | re.IGNORECASE)
        
        for section in sections:
            task_name = section.group(1).strip()
            section_content = section.group(2)
            
            # Find any code block
            code_pattern = r'```(\w*)\s*(.*?)```'
            matches = list(re.finditer(code_pattern, section_content, re.DOTALL))
            
            if matches:
                # Use largest code block
                largest = max(matches, key=lambda m: len(m.group(2)))
                language = largest.group(1).strip() or 'text'
                code = largest.group(2).strip()
                
                if code and len(code) > 0:
                    safe_task_name = re.sub(r'[^\w\s-]', '', task_name)
                    safe_task_name = re.sub(r'[-\s]+', '_', safe_task_name).lower().strip('_')[:50]
                    
                    if not safe_task_name:
                        safe_task_name = f"code_example_{snippet_index}"
                    
                    extension = get_file_extension(language)
                    key = f"snippet_{snippet_index}_{safe_task_name}"
                    filename = f"{safe_task_name}.{extension}"
                    
                    snippets[key] = {
                        "language": language,
                        "extension": extension,
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
    
    # Final summary
    separator = "=" * 60
    print(f"\n{separator}", file=sys.stderr, flush=True)
    if snippets:
        print(f"✅ Successfully extracted {len(snippets)} code snippet(s)", file=sys.stderr, flush=True)
        for key, data in snippets.items():
            print(f"   - {data['filename']}: {data['code_length']} chars, "
                  f"{data['code_lines_non_empty']} lines of code", 
                  file=sys.stderr, flush=True)
    else:
        print("⚠️ WARNING: No code snippets found with COMPLETE_CODE_SNIPPET tags or in Complete Code Example sections", 
              file=sys.stderr, flush=True)
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
    gist_name: str = ""
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
    
    # --- Token Check ---
    if not token:
        return {"error": "GITHUB_TOKEN environment variable not set"}
    
    print(f"🔑 GITHUB_TOKEN found", flush=True, file=sys.stderr)
    
    # --- Build files object for gist ---
    gist_files = {
        filename: {"content": content} 
        for filename, content in files_dict.items()
    }
    
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


# ── Configuration ─────────────────────────────────────────────────────────────
META_DESC_MIN = 140
META_DESC_MAX = 160
MAX_RETRIES = 3
# ── Core helpers ──────────────────────────────────────────────────────────────

def extract_meta_description(content: str) -> str | None:
    """
    Extract the meta description value from Hugo frontmatter.
    Handles both single-line and quoted multi-word values.

    Returns the raw description string, or None if not found.
    """
    # Match:  description: "some text"  OR  description: some text
    match = re.search(
        r'^description:\s*["\']?(.+?)["\']?\s*$',
        content,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def replace_meta_description(content: str, new_description: str) -> str:
    """
    Replace the existing description line in the frontmatter with new_description.
    Always wraps the value in double quotes for YAML safety.
    """
    replacement = f'description: "{new_description}"'
    updated = re.sub(
        r'^description:\s*["\']?.+?["\']?\s*$',
        replacement,
        content,
        flags=re.MULTILINE,
    )
    return updated


def is_valid_meta_description(description: str) -> bool:
    """Return True if description length is within 140-160 characters."""
    length = len(description)
    return META_DESC_MIN <= length <= META_DESC_MAX


def fix_meta_description_with_llm(bad_description: str) -> str | None:
    """
    Send the bad meta description to the LLM and ask it to fix the length.
    Returns the corrected description string, or None if all retries fail.
    """
    current = bad_description

    for attempt in range(1, MAX_RETRIES + 1):
        length = len(current)
        direction = "shorter" if length > META_DESC_MAX else "longer"
        action = (
            f"It is {length} characters, which exceeds the {META_DESC_MAX} character limit. "
            f"Shorten it."
            if length > META_DESC_MAX
            else
            f"It is {length} characters, which is below the {META_DESC_MIN} character limit. "
            f"Expand it."
        )

        prompt = (
            f"The following meta description needs to be rewritten to be exactly "
            f"{META_DESC_MIN}-{META_DESC_MAX} characters (including spaces).\n\n"
            f"{action}\n\n"
            f"Rules:\n"
            f"- Keep the same meaning and keywords\n"
            f"- Count every character including spaces before replying\n"
            f"- Return ONLY the rewritten description text — no quotes, no labels, "
            f"no explanation\n\n"
            f"Current description:\n{current}"
        )

        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Current length: {length} — asking LLM to make it {direction}...")

        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        candidate = response.content[0].text.strip().strip('"').strip("'")

        print(f"  [Attempt {attempt}/{MAX_RETRIES}] New length: {len(candidate)} — '{candidate[:60]}...'")

        if is_valid_meta_description(candidate):
            print(f"  ✅ Valid meta description on attempt {attempt}.")
            return candidate

        # Feed the latest attempt back for the next retry
        current = candidate

    print(f"  ❌ Could not fix meta description after {MAX_RETRIES} attempts.")
    return None


# ── Main public function ──────────────────────────────────────────────────────

def validate_and_fix_meta_description(blog_content: str) -> tuple[str, bool]:
    """
    Validate the meta description in blog_content.
    If invalid, attempt to fix it via the LLM.

    Returns:
        (updated_content, was_fixed)
        - updated_content : the blog content with the (possibly corrected) description
        - was_fixed       : True if a correction was applied, False if already valid
                            or if correction failed (content returned as-is in that case)
    """
    description = extract_meta_description(blog_content)

    if description is None:
        print("⚠️  No meta description found in content. Skipping validation.")
        return blog_content, False

    length = len(description)
    print(f"📏 Meta description length: {length} characters")
    print(f"   '{description[:80]}{'...' if length > 80 else ''}'")

    if is_valid_meta_description(description):
        print(f"✅ Meta description is valid ({length} chars — within {META_DESC_MIN}-{META_DESC_MAX}).")
        return blog_content, False

    print(f"⚠️  Meta description is OUT OF RANGE ({length} chars). Attempting fix...")

    fixed_description = fix_meta_description_with_llm(description)

    if fixed_description is None:
        print("❌ Fix failed. Returning original content unchanged.")
        return blog_content, False

    updated_content = replace_meta_description(blog_content, fixed_description)
    print(f"✅ Meta description fixed: {len(fixed_description)} chars.")
    return updated_content, True

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
        print("\n" + "=" * 70)
        print("AI CONTENT CLEANUP - Markdown-Aware Processing")
        print("=" * 70)
        
        if total_replaced == 0:
            print("✅ No AI indicators found - content looks clean!")
            print("=" * 70 + "\n")
            return cleaned_content
        
        print(f"⚠️  Found {total_replaced} AI generation indicators\n")
        
        # Group replacements by type
        by_type = {}
        for rep in replacements:
            pattern_name = rep['pattern_name']
            if pattern_name not in by_type:
                by_type[pattern_name] = []
            by_type[pattern_name].append(rep)
        
        # Display grouped results
        for pattern_name, items in by_type.items():
            print(f"📍 {pattern_name}: {len(items)} occurrence(s)")
            
            # Show first 5 occurrences with line numbers
            for i, item in enumerate(items[:5], 1):
                print(f"   Line {item['line_number']}: '{item['original']}' → '{item['replacement']}'")
                print(f"   Context: {item['context']}")
            
            if len(items) > 5:
                print(f"   ... and {len(items) - 5} more occurrence(s)")
            print()
        
        print(f"🔧 Cleanup completed: Replaced {total_replaced} fancy punctuation marks")
        print("✅ Protected: Code blocks, inline code, images, URLs, gists")
        print("=" * 70 + "\n")
    
    return cleaned_content


def find_malformed_links(content: str) -> List[Dict]:
    """
    Scan content for malformed markdown links and return detailed information.
    
    Returns:
        List of dicts with: line_number, issue_type, original, suggestion, context
    """
    issues = []
    lines = content.split('\n')
    
    # Patterns for different types of malformed links
    patterns = [
        # Missing opening bracket: ]text](url)
        (r'\]([^\]]+)\]\(([^\)]+)\)', 'missing_opening_bracket', r'[\1](\2)'),
        
        # Missing closing bracket before parenthesis: [text(url)
        (r'\[([^\]]+)\(([^\)]+)\)', 'missing_closing_bracket', r'[\1](\2)'),
        
        # Missing opening parenthesis: [text]url)
        (r'\[([^\]]+)\]([^(\s][^\)]*)\)', 'missing_opening_paren', r'[\1](\2)'),
        
        # Missing closing parenthesis: [text](url
        (r'\[([^\]]+)\]\(([^\)\s]+)(?!\))', 'missing_closing_paren', r'[\1](\2)'),
        
        # Reversed structure: (text[url] or (text)[url]
        (r'\(([^\)]+)\)\[([^\]]+)\]', 'reversed_structure', r'[\1](\2)'),
        (r'\(([^\)]+)\[([^\]]+)\]', 'reversed_structure_partial', r'[\1](\2)'),
        
        # Empty link text: [](url)
        (r'\[\]\(([^\)]+)\)', 'empty_link_text', r'[link](\1)'),
        
        # Empty URL: [text]()
        (r'\[([^\]]+)\]\(\)', 'empty_url', r'[\1](#)'),
        
        # Missing brackets entirely: text](url) or text(url)
        (r'(?<!\[)(\w+)\]\(([^\)]+)\)', 'missing_both_brackets', r'[\1](\2)'),
    ]
    
    for line_idx, line in enumerate(lines, start=1):
        for pattern, issue_type, replacement_pattern in patterns:
            for match in re.finditer(pattern, line):
                # Extract context (50 chars before and after)
                start_pos = match.start()
                end_pos = match.end()
                context_start = max(0, start_pos - 30)
                context_end = min(len(line), end_pos + 30)
                context = line[context_start:context_end].strip()
                
                # Generate suggested fix
                try:
                    suggested = re.sub(pattern, replacement_pattern, match.group(0))
                except:
                    suggested = "[MANUAL_FIX_NEEDED]"
                
                issues.append({
                    'line_number': line_idx,
                    'issue_type': issue_type,
                    'original': match.group(0),
                    'suggested': suggested,
                    'context': f"...{context}...",
                    'position': start_pos
                })
    
    return issues
def extract_protected_regions(content: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract and protect regions that should not be modified.
    Returns content with placeholders and dict of protected regions.
    
    Protected:
    - YAML frontmatter (between --- delimiters)
    - Code blocks (```...```)
    - Inline code (`...`)
    - HTML blocks and tags
    - Autolinks <https://example.com>
    - Reference-style link definitions [ref]: url
    - Images ![alt](url)
    - Existing valid markdown links (to avoid breaking them)
    """
    protected = {}
    placeholder_content = content
    counter = 0
    
    # 1. Protect YAML frontmatter (FIRST - highest priority)
    def protect_frontmatter(match):
        nonlocal counter
        placeholder = f"___PROTECTED_FRONTMATTER_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    # Match frontmatter between --- delimiters at start of document
    placeholder_content = re.sub(
        r'^---\s*\n.*?\n---\s*\n',
        protect_frontmatter,
        placeholder_content,
        flags=re.DOTALL | re.MULTILINE,
        count=1  # Only first occurrence
    )
    
    # 2. Protect HTML blocks (before code blocks to handle <script>, <style>)
    def protect_html_block(match):
        nonlocal counter
        placeholder = f"___PROTECTED_HTML_BLOCK_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    # Multi-line HTML blocks
    placeholder_content = re.sub(
        r'<(?:script|style|pre|div|section|article|header|footer|nav)[\s\S]*?</(?:script|style|pre|div|section|article|header|footer|nav)>',
        protect_html_block,
        placeholder_content,
        flags=re.IGNORECASE | re.MULTILINE
    )
    
    # HTML comments
    placeholder_content = re.sub(
        r'<!--[\s\S]*?-->',
        protect_html_block,
        placeholder_content,
        flags=re.MULTILINE
    )
    
    # Single HTML tags
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
    
    # 3. Protect code blocks
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
    
    # 4. Protect inline code
    def protect_inline_code(match):
        nonlocal counter
        placeholder = f"___PROTECTED_INLINE_CODE_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'``[^`]+``|`[^`\n]+`',
        protect_inline_code,
        placeholder_content
    )
    
    # 5. Protect autolinks <url>
    def protect_autolink(match):
        nonlocal counter
        placeholder = f"___PROTECTED_AUTOLINK_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'<(?:https?://|mailto:)[^>]+>',
        protect_autolink,
        placeholder_content
    )
    
    # 6. Protect reference-style link definitions [ref]: url "title"
    def protect_reference_def(match):
        nonlocal counter
        placeholder = f"___PROTECTED_REFERENCE_DEF_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    # Match: [ref]: url or [ref]: url "title"
    placeholder_content = re.sub(
        r'^\s*\[[^\]]+\]:\s+\S+(?:\s+"[^"]*")?$',
        protect_reference_def,
        placeholder_content,
        flags=re.MULTILINE
    )
    
    # 7. Protect images ![alt](url) - BEFORE protecting links
    def protect_image(match):
        nonlocal counter
        placeholder = f"___PROTECTED_IMAGE_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'!\[[^\]]*\]\([^\)]+\)',
        protect_image,
        placeholder_content
    )
    
    # 8. Protect valid markdown links with nested brackets [text [nested] text](url)
    def protect_valid_link(match):
        nonlocal counter
        placeholder = f"___PROTECTED_VALID_LINK_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    # Match properly formatted links (handles nested brackets)
    # This regex handles: [text], [text [nested] more], etc.
    placeholder_content = re.sub(
        r'\[(?:[^\[\]]+|\[[^\]]*\])*\]\([^\)]+\)',
        protect_valid_link,
        placeholder_content
    )
    
    # 9. Protect reference-style link usage [text][ref]
    def protect_reference_link(match):
        nonlocal counter
        placeholder = f"___PROTECTED_REFERENCE_LINK_{counter}___"
        protected[placeholder] = match.group(0)
        counter += 1
        return placeholder
    
    placeholder_content = re.sub(
        r'\[[^\]]+\]\[[^\]]+\]',
        protect_reference_link,
        placeholder_content
    )
    
    return placeholder_content, protected


def restore_protected_regions(content: str, protected: Dict[str, str]) -> str:
    """Restore protected regions back into content."""
    for placeholder, original in protected.items():
        content = content.replace(placeholder, original)
    return content


def find_malformed_links(content: str) -> List[Dict]:
    """
    Scan content for malformed markdown links and return detailed information.
    Only scans unprotected regions.
    
    Returns:
        List of dicts with: line_number, issue_type, original, suggestion, context
    """
    # Protect valid regions first
    protected_content, protected_blocks = extract_protected_regions(content)
    
    issues = []
    lines = protected_content.split('\n')
    
    # Patterns for different types of malformed links
    patterns = [
        # Missing opening bracket: ]text](url)
        (r'\]([^\]]+)\]\(([^\)]+)\)', 'missing_opening_bracket', r'[\1](\2)'),
        
        # Missing closing bracket before parenthesis: [text(url)
        (r'\[([^\]]+)\(([^\)]+)\)', 'missing_closing_bracket', r'[\1](\2)'),
        
        # Missing opening parenthesis: [text]url) - but not valid links already protected
        (r'\[([^\]]+)\]([^(\s\[])[^\)]*\)', 'missing_opening_paren', r'[\1](\2)'),
        
        # Reversed structure: (text)[url] or (text[url]
        (r'\(([^\)]+)\)\[([^\]]+)\]', 'reversed_structure', r'[\1](\2)'),
        (r'\(([^\)]+)\[([^\)]+)\]', 'reversed_structure_partial', r'[\1](\2)'),
        
        # Missing both brackets: text (url) - COMMON PATTERN
        # Match product names or text followed by (url)
        # Examples: "Aspose.HTML for Python via .NET (https://...)"
        (r'(?<!\])([A-Z][A-Za-z0-9]+(?:\.[A-Z][A-Za-z0-9]+)?(?:\s+for\s+|\s+via\s+|\s+by\s+)[A-Za-z0-9\s\.\-]+)\s+\((https?://[^\)]+)\)',
         'missing_both_brackets_product', r'[\1](\2)'),
        
        # Simpler version: Any capitalized text (5+ chars) followed by (url)
        (r'(?<!\])([A-Z][A-Za-z0-9\s\.\-]{5,?})\s+\((https?://[^\)]+)\)',
         'missing_both_brackets', r'[\1](\2)'),
        
        # Empty link text: [](url)
        (r'\[\]\(([^\)]+)\)', 'empty_link_text', r'[link](\1)'),
        
        # Empty URL: [text]()
        (r'\[([^\]]+)\]\(\)', 'empty_url', r'[\1](#)'),
    ]
    
    for line_idx, line in enumerate(lines, start=1):
        for pattern, issue_type, replacement_pattern in patterns:
            for match in re.finditer(pattern, line):
                # Extract context (50 chars before and after)
                start_pos = match.start()
                end_pos = match.end()
                context_start = max(0, start_pos - 30)
                context_end = min(len(line), end_pos + 30)
                context = line[context_start:context_end].strip()
                
                # Generate suggested fix
                try:
                    suggested = re.sub(pattern, replacement_pattern, match.group(0))
                except:
                    suggested = "[MANUAL_FIX_NEEDED]"
                
                issues.append({
                    'line_number': line_idx,
                    'issue_type': issue_type,
                    'original': match.group(0),
                    'suggested': suggested,
                    'context': f"...{context}...",
                    'pattern': pattern,
                    'replacement_pattern': replacement_pattern
                })
    
    return issues


def fix_malformed_links(content: str, verbose: bool = True) -> Tuple[str, int, List[Dict]]:
    """
    Automatically fix malformed markdown links in content.
    Uses regex substitution to avoid string replace issues.
    Protects code blocks and valid links.
    
    Args:
        content: Markdown content to fix
        verbose: If True, print detailed report
        
    Returns:
        Tuple of (fixed_content, count_fixed, issues_found)
    """
    # Protect code blocks and valid links
    protected_content, protected_blocks = extract_protected_regions(content)
    
    # Find all issues in protected content
    issues = find_malformed_links(content)
    
    if len(issues) == 0:
        if verbose:
            print("\n" + "=" * 70)
            print("MARKDOWN LINK VALIDATION")
            print("=" * 70)
            print("✅ No malformed links found - all links are properly formatted!")
            print("=" * 70 + "\n")
        return content, 0, []
    
    # Apply fixes using regex substitution (safer than .replace())
    fixed_content = protected_content
    fixes_applied = 0
    
    # Group issues by pattern to apply fixes efficiently
    pattern_groups = {}
    for issue in issues:
        pattern_key = issue['pattern']
        if pattern_key not in pattern_groups:
            pattern_groups[pattern_key] = {
                'pattern': issue['pattern'],
                'replacement': issue['replacement_pattern'],
                'count': 0
            }
        pattern_groups[pattern_key]['count'] += 1
    
    # Apply each pattern fix
    for pattern_key, group in pattern_groups.items():
        pattern = group['pattern']
        replacement = group['replacement']
        
        # Use re.sub which handles overlapping issues better than .replace()
        fixed_content, count = re.subn(pattern, replacement, fixed_content)
        fixes_applied += count
    
    # Restore protected blocks
    fixed_content = restore_protected_regions(fixed_content, protected_blocks)
    
    if verbose:
        print("\n" + "=" * 70)
        print("MARKDOWN LINK VALIDATION & REPAIR")
        print("=" * 70)
        print(f"⚠️  Found {len(issues)} malformed link(s)\n")
        
        # Group by issue type for reporting
        by_type = {}
        for issue in issues:
            issue_type = issue['issue_type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        # Display grouped results
        issue_labels = {
            'missing_opening_bracket': 'Missing opening bracket [',
            'missing_closing_bracket': 'Missing closing bracket ]',
            'missing_opening_paren': 'Missing opening parenthesis (',
            'missing_closing_paren': 'Missing closing parenthesis )',
            'reversed_structure': 'Reversed structure (text)[url]',
            'reversed_structure_partial': 'Partial reversed structure',
            'missing_both_brackets_product': 'Missing brackets around product name',
            'missing_both_brackets': 'Missing both brackets around text',
            'empty_link_text': 'Empty link text []',
            'empty_url': 'Empty URL ()',
        }
        
        for issue_type, type_issues in by_type.items():
            label = issue_labels.get(issue_type, issue_type)
            print(f"📍 {label}: {len(type_issues)} occurrence(s)")
            
            # Show first 3 examples
            for i, issue in enumerate(type_issues[:3], 1):
                print(f"   Line {issue['line_number']}: '{issue['original']}' → '{issue['suggested']}'")
                print(f"   Context: {issue['context']}")
            
            if len(type_issues) > 3:
                print(f"   ... and {len(type_issues) - 3} more occurrence(s)")
            print()
        
        print(f"🔧 Repair completed: Fixed {fixes_applied} malformed link(s)")
        print("✅ Protected: Frontmatter, code blocks, inline code, HTML, autolinks,")
        print("              images, valid links, reference-style links")
        print("=" * 70 + "\n")
    
    return fixed_content, fixes_applied, issues


def validate_markdown_links(content: str, fix_automatically: bool = True, verbose: bool = True) -> str:
    """
    Main function to validate and optionally fix markdown links.
    
    Args:
        content: Markdown content to validate
        fix_automatically: If True, automatically fix issues; if False, just report
        verbose: If True, print detailed report
        
    Returns:
        Fixed content (or original if fix_automatically=False)
    """
    if fix_automatically:
        fixed_content, count, issues = fix_malformed_links(content, verbose=verbose)
        return fixed_content
    else:
        issues = find_malformed_links(content)
        if verbose and len(issues) > 0:
            print(f"\n⚠️  Found {len(issues)} malformed links (not fixed)")
            for issue in issues[:5]:
                print(f"   Line {issue['line_number']}: {issue['original']}")
        return content
