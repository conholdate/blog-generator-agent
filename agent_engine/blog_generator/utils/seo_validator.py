import re
import frontmatter
from services.LLMservice import llm_service  # Use centralized service

def validate_seo_content(markdown_string, targets):
    """
    Enhanced SEO Validator with Word Count Tolerance and Read More check.
    """
    report = {"status": "PASS", "score": 0, "details": {}}
    max_score = 100
    deductions = 0
    
    try:
        post = frontmatter.loads(markdown_string)
        content_body = post.content
        fm = post.metadata
    except Exception as e:
        return {"status": "FAIL", "error": f"Invalid Frontmatter/Markdown: {str(e)}"}

    primary_kw = targets.get("primary_keyword", "").lower()

    # --- RULE 1: seoTitle (40-60 chars + Keyword) ---
    seo_title = fm.get("seoTitle", "")
    seo_len = len(seo_title)
    has_kw_in_seo = primary_kw in seo_title.lower()
    
    title_score = 20
    if not (40 <= seo_len <= 60) or not has_kw_in_seo:
        title_score = 0
        deductions += 20
        msg = f"Length: {seo_len}, Keyword: {'Found' if has_kw_in_seo else 'Missing'}"
    else:
        msg = "Perfect"
    report["details"]["seo_title"] = {"score": title_score, "msg": msg}

    # --- RULE 2: Meta Description (140-160 chars) ---
    meta_desc = fm.get("description", "")
    meta_len = len(meta_desc)
    meta_score = 15
    if not (140 <= meta_len <= 160):
        meta_score = 0
        deductions += 15
        msg = f"Length {meta_len} (Target 140-160)"
    else:
        msg = "Perfect"
    report["details"]["meta_description"] = {"score": meta_score, "msg": msg}

    # --- RULE 3: Keyword Density (Min 5) ---
    min_kw = targets.get("target_keyword_count", 5)
    occurrences = len(re.findall(re.escape(primary_kw), markdown_string.lower()))
    kw_score = 15
    if occurrences < min_kw:
        kw_score = 0
        deductions += 15
        msg = f"Found {occurrences}. Min required: {min_kw}"
    else:
        msg = f"Passed: {occurrences} found"
    report["details"]["keyword_density"] = {"score": kw_score, "msg": msg}

    # --- RULE 4: Required Sections (FAQ & Read More) ---
    has_faq = bool(re.search(r'^#+\s*(FAQ|Frequently Asked Questions)', content_body, re.MULTILINE | re.IGNORECASE))
    has_read_more = bool(re.search(r'^#+\s*Read More', content_body, re.MULTILINE | re.IGNORECASE))
    
    sec_score = 15
    sec_msgs = []
    if not has_faq: sec_msgs.append("Missing FAQ")
    if not has_read_more: sec_msgs.append("Missing Read More")
    
    if sec_msgs:
        sec_score = 0
        deductions += 15
        msg = " | ".join(sec_msgs)
    else:
        msg = "Both sections found"
    report["details"]["required_sections"] = {"score": sec_score, "msg": msg}

    # --- RULE 5: Complete Code Snippet Wrapper ---
    has_wrapper = ("" in content_body and 
                   "" in content_body)
    code_score = 20
    if not has_wrapper:
        code_score = 0
        deductions += 20
        msg = "Tags missing"
    else:
        msg = "Tags correct"
    report["details"]["code_wrapper"] = {"score": code_score, "msg": msg}

    # --- RULE 6: Word Count with Tolerance ---
    # Logic: Accept +/- 10% of the target
    target_wc = targets.get("target_words", 1000)
    actual_wc = len(content_body.split())
    tolerance = 0.10 # 10%
    
    lower_bound = target_wc * (1 - tolerance)
    upper_bound = target_wc * (1 + tolerance)
    
    wc_score = 15
    if actual_wc < lower_bound:
        wc_score = 0
        deductions += 15
        msg = f"Too short: {actual_wc} words (Min: {int(lower_bound)})"
    elif actual_wc > upper_bound:
        # Note: Usually long is okay for SEO, but we keep the range as requested
        wc_score = 15 
        msg = f"Long but okay: {actual_wc} words"
    else:
        msg = f"Count: {actual_wc} (Within range)"
        
    report["details"]["word_count"] = {"score": wc_score, "msg": msg}

    # Final Score
    report["score"] = max(0, max_score - deductions)
    report["status"] = "PASS" if report["score"] >= 80 else "REVISION_NEEDED"
    
    return report


# ── Configuration ─────────────────────────────────────────────────────────────
META_DESC_MIN = 140
META_DESC_MAX = 160
SEO_TITLE_MIN = 40
SEO_TITLE_MAX = 60
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


async def fix_meta_description_with_llm(
    bad_description: str,
    metrics=None                          # ← NEW: optional MetricsRecorder
) -> str | None:
    """
    Send the bad meta description to the LLM and ask it to fix the length.
    Returns the corrected description string, or None if all retries fail.
 
    NOW USES CENTRALIZED LLM SERVICE
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
 
        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Current length: {length} — asking LLM to make it {direction}...")
 
        instructions = f"""
You are a meta description optimizer.
 
Your task:
- Rewrite the meta description to be exactly {META_DESC_MIN}-{META_DESC_MAX} characters (including spaces)
- {action}
- Keep the same meaning and keywords
- Count every character including spaces before replying
- Return ONLY the rewritten description text — no quotes, no labels, no explanation
 
Current description:
{current}
"""
 
        try:
            result = await llm_service.run_agent(
                instructions=instructions,
                context="Rewrite the meta description above.",
                agent_name="meta-description-fixer",
                temperature=0.7,
                max_turns=1
            )
 
            # ── Record token usage for this attempt ──────────────────────────
            if metrics is not None:
                print("metrx is no none")
                metrics.record_llm_usage(
                    input_tokens=result.token_usage["input_tokens"],
                    output_tokens=result.token_usage["output_tokens"]
                )
            # ─────────────────────────────────────────────────────────────────
            print(f"meta---- {result.token_usage['output_tokens']}-- {result.token_usage['input_tokens']}", flush=True)
            candidate = result.final_output.strip().strip('"').strip("'")
 
            if not candidate or len(candidate.strip()) == 0:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM returned empty response")
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
 
        print(f"  [Attempt {attempt}/{MAX_RETRIES}] New length: {len(candidate)} — '{candidate[:60]}...'")
 
        if is_valid_meta_description(candidate):
            print(f"  ✅ Valid meta description on attempt {attempt}.")
            return candidate
 
        # Feed the latest attempt back for the next retry
        current = candidate
 
    print(f"  ❌ Could not fix meta description after {MAX_RETRIES} attempts.")
    return None


# ── Main public function ──────────────────────────────────────────────────────





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







# ══════════════════════════════════════════════════════════════════════════════
# SEO TITLE VALIDATION AND FIXING
# ══════════════════════════════════════════════════════════════════════════════


# ── Configuration ─────────────────────────────────────────────────────────────
META_DESC_MIN = 140
META_DESC_MAX = 160
SEO_TITLE_MIN = 40
SEO_TITLE_MAX = 60
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



# ══════════════════════════════════════════════════════════════════════════════
# SEO TITLE VALIDATION AND FIXING
# ══════════════════════════════════════════════════════════════════════════════

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




# ── Main public function ──────────────────────────────────────────────────────

async def validate_and_fix_meta_description(
    blog_content: str,
    metrics=None                          # ← NEW: optional MetricsRecorder
) -> tuple[str, bool]:
    """
    Validate the meta description in blog_content.
    If invalid, attempt to fix it via the LLM.
 
    Args:
        blog_content: Full blog post markdown content
        metrics: Optional MetricsRecorder instance to track token usage
 
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
 
    fixed_description = await fix_meta_description_with_llm(
        description,
        metrics=metrics                   # ← pass it down
    )
 
    if fixed_description is None:
        print("❌ Fix failed. Returning original content unchanged.")
        return blog_content, False
 
    updated_content = replace_meta_description(blog_content, fixed_description)
    print(f"✅ Meta description fixed: {len(fixed_description)} chars.")
    return updated_content, True


# ══════════════════════════════════════════════════════════════════════════════
# SEO TITLE VALIDATION AND FIXING
# ══════════════════════════════════════════════════════════════════════════════
def fix_title_case(title: str) -> str:
    """
    Auto-correct title to use proper Title Case.
    
    Rules:
    - Capitalize first and last words
    - Capitalize major words (nouns, verbs, adjectives, adverbs)
    - Lowercase small words (a, an, the, and, but, or, for, in, on, at, to, by, of, with, from)
    - Keep acronyms uppercase (PDF, HTML, PSD, etc.)
    - Preserve known product/brand names (PowerPoint, Excel, SharePoint, etc.)
    - Capitalize prepositions of 5+ letters
    
    Returns:
        Title with corrected capitalization
    """
    if not title:
        return title
    
    # Small words that should be lowercase (unless first/last)
    small_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'in', 'of', 'with', 'from', 'into', 'via'}
    
    # Known product/brand names that should preserve their exact capitalization
    # Key: lowercase version, Value: correct capitalization
    proper_nouns = {
        'powerpoint': 'PowerPoint',
        'sharepoint': 'SharePoint',
        'excel': 'Excel',
        'word': 'Word',
        'outlook': 'Outlook',
        'onenote': 'OneNote',
        'visio': 'Visio',
        'photoshop': 'Photoshop',
        'illustrator': 'Illustrator',
        'indesign': 'InDesign',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'nodejs': 'Node.js',
        'mongodb': 'MongoDB',
        'mysql': 'MySQL',
        'postgresql': 'PostgreSQL',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'linkedin': 'LinkedIn',
        'youtube': 'YouTube',
        'iphone': 'iPhone',
        'ipad': 'iPad',
        'macos': 'macOS',
        'ios': 'iOS',
        'android': 'Android',
        'windows': 'Windows',
        'linux': 'Linux',
        'ubuntu': 'Ubuntu',
    }
    
    words = title.split()
    corrected_words = []
    
    for i, word in enumerate(words):
        is_first = i == 0
        is_last = i == len(words) - 1
        
        # Check if word is a known proper noun (case-insensitive match)
        word_lower = word.lower()
        if word_lower in proper_nouns:
            # Use the correct capitalization from our dictionary
            corrected_words.append(proper_nouns[word_lower])
            continue
        
        # Check if word is likely an acronym (all uppercase and 2+ chars)
        if word.isupper() and len(word) > 1:
            # Keep acronyms as-is (PDF, HTML, PSD, etc.)
            corrected_words.append(word)
            continue
        
        # Check if word contains hyphens or special chars
        if '-' in word:
            # Handle hyphenated words (e.g., "Step-by-Step")
            parts = word.split('-')
            corrected_parts = []
            for j, part in enumerate(parts):
                part_lower = part.lower()
                # Check if part is a proper noun
                if part_lower in proper_nouns:
                    corrected_parts.append(proper_nouns[part_lower])
                elif part_lower in small_words and not (j == 0 or j == len(parts) - 1):
                    corrected_parts.append(part_lower)
                else:
                    corrected_parts.append(part.capitalize())
            corrected_words.append('-'.join(corrected_parts))
            continue
        
        # First and last words always capitalized
        if is_first or is_last:
            corrected_words.append(word.capitalize())
        # Small words lowercase (unless first/last)
        elif word_lower in small_words:
            corrected_words.append(word_lower)
        # All other words capitalized
        else:
            corrected_words.append(word.capitalize())
    
    return ' '.join(corrected_words)


def is_valid_seo_title(title: str, primary_keyword: str) -> tuple[bool, str]:
    """
    Validate if SEO title meets requirements.
    
    Requirements:
    - Length between 40-60 characters
    - Contains the primary keyword (case-insensitive)
    - Uses Title Case (major words capitalized)
    
    Returns:
        (is_valid, reason) - reason is empty string if valid, otherwise explains why invalid
    """
    length = len(title)
    
    # Check length
    if length < SEO_TITLE_MIN:
        return False, f"Too short ({length} chars, need {SEO_TITLE_MIN}-{SEO_TITLE_MAX})"
    if length > SEO_TITLE_MAX:
        return False, f"Too long ({length} chars, need {SEO_TITLE_MIN}-{SEO_TITLE_MAX})"
    
    # Check if primary keyword is present (case-insensitive)
    if primary_keyword.lower() not in title.lower():
        return False, f"Missing primary keyword '{primary_keyword}'"
    
    # Check Title Case (words that should be capitalized)
    # Small words that should be lowercase (unless first/last word)
    small_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'in', 'of', 'with', 'from', 'into', 'via'}
    
    words = title.split()
    title_case_errors = []
    
    for i, word in enumerate(words):
        # Skip words with special characters or all caps (like PSD, HTML)
        if not word.replace('-', '').replace("'", '').isalpha():
            continue
        if word.isupper() and len(word) > 1:  # Acronyms like PDF, HTML
            continue
            
        is_first = i == 0
        is_last = i == len(words) - 1
        word_lower = word.lower()
        
        # First and last words should always be capitalized
        if is_first or is_last:
            if not word[0].isupper():
                title_case_errors.append(f"'{word}' should be '{word.capitalize()}'")
        # Small words should be lowercase (unless first/last)
        elif word_lower in small_words:
            if word[0].isupper():
                title_case_errors.append(f"'{word}' should be '{word_lower}'")
        # Major words should be capitalized
        else:
            if not word[0].isupper():
                title_case_errors.append(f"'{word}' should be '{word.capitalize()}'")
    
    if title_case_errors:
        return False, f"Title Case errors: {', '.join(title_case_errors[:3])}"
    
    return True, ""


async def generate_seo_title_with_llm(
    primary_keyword: str,
    product_name: str = None,
    isCloud: bool = False,
    platform: str = None,
    metrics=None                          # ← NEW: optional MetricsRecorder
) -> str | None:
    """
    Generate a new SEO title from scratch using LLM.
    
    Args:
        primary_keyword: The primary keyword that must be included
        product_name: Optional exact product name to include (e.g., "Aspose.HTML for Python via .NET")
        isCloud: If True, use "library/API" terminology; if False, use "SDK" terminology
        platform: Optional platform name (e.g., "Python via .NET", "Java", ".NET")
        metrics: Optional MetricsRecorder instance to track token usage per attempt
        
    Returns:
        Generated title or None if all retries fail
    """
    # Determine correct terminology based on isCloud
    if isCloud:
        terminology = "library or API"
        terminology_examples = "library, API, cloud API"
        avoid_terms = "SDK"
    else:
        terminology = "SDK"
        terminology_examples = "SDK"
        avoid_terms = "library, API"
    
    # Extract platform name (trim "via X" part if present)
    platform_for_title = None
    if platform:
        if ' via ' in platform:
            platform_for_title = platform.split(' via ')[0].strip()
        else:
            platform_for_title = platform.strip()
    
    # Build product name instructions
    product_instruction = ""
    if product_name:
        product_instruction = f"""
🚨 PRODUCT NAME HANDLING 🚨

Product name: "{product_name}"

YOU HAVE TWO OPTIONS:
1. Include the COMPLETE product name EXACTLY as shown: "{product_name}"
   - Use it word-for-word, no changes, no abbreviations
2. Do NOT include it at all (focus on keywords and benefits only)

CHOOSE based on what fits better in 40-60 characters.

FORBIDDEN:
❌ DO NOT use partial product name
❌ DO NOT rephrase or abbreviate
❌ DO NOT mention just the platform (e.g., "Python" or ".NET")

EITHER use "{product_name}" completely OR don't mention it.
"""
    
    # Build platform instructions
    platform_instruction = ""
    if platform_for_title:
        platform_instruction = f"""
🎯 PLATFORM REQUIREMENT 🎯

Platform: {platform_for_title}

MANDATORY: The title MUST include "in {platform_for_title}" to specify the programming language/platform.

Examples:
- "Convert PSD to HTML in Python Programmatically"
- "Excel to PDF Conversion in Java: Complete Guide"
- "PDF Processing in .NET: Developer Tutorial"

Format: "[action/task] in {platform_for_title} [additional context]"

This is REQUIRED for proper SEO and clarity.
"""
    
    # Build file format capitalization rules
    format_instruction = """
📝 FILE FORMAT CAPITALIZATION RULES 📝

ALL file format names MUST be in UPPERCASE:
✅ PSD (not Psd or psd)
✅ HTML (not Html or html)
✅ PDF (not Pdf or pdf)
✅ PNG (not Png or png)
✅ JPEG (not Jpeg or jpeg)
✅ DOCX (not Docx or docx)
✅ XLSX (not Xlsx or xlsx)
✅ ZIP (not Zip or zip)
✅ XML (not Xml or xml)
✅ JSON (not Json or json)

Examples of CORRECT titles:
✅ "Convert PSD to HTML in Python Programmatically"
✅ "PDF to PNG Conversion in Java: Complete Guide"
✅ "XLSX to PDF in .NET: Step-by-Step Tutorial"

Examples of WRONG titles (DO NOT USE):
❌ "Convert Psd to Html in Python"
❌ "Pdf to Png Conversion in Java"
❌ "Excel to Pdf in .NET"
"""
    
    # Build terminology instructions
    terminology_instruction = f"""
📚 TERMINOLOGY RULES 📚

When referring to the software/tool (if applicable):
✅ USE: {terminology_examples}
❌ AVOID: {avoid_terms}

🚫 STRICTLY FORBIDDEN TERMS:
❌ NEVER use: "online tool", "online app", "web-based tool", "web app"
❌ NEVER use: "browser-based", "no installation required"
❌ NEVER use: "free", "free library", "free API", "free SDK", "no cost"
❌ NEVER use: "open source" (unless explicitly true)

REASON: 
1. We are NOT writing about online/web-based applications
2. This is a COMMERCIAL {terminology} that requires licensing
3. This is NOT free software - it requires purchase for production use

Examples:
- Cloud-based: "Convert PDF Using Python Library"
- Non-cloud: "Convert PDF with .NET SDK"

Only use these terms if they fit naturally in the title.
"""
    
    for attempt in range(1, MAX_RETRIES + 1):
        instructions = f"""
You are an SEO title generator.

Your task: Create an SEO-optimized title from scratch.

Requirements:
- Length: EXACTLY {SEO_TITLE_MIN}-{SEO_TITLE_MAX} characters (count every character including spaces)
- MUST include the primary keyword: "{primary_keyword}"
- Make it compelling and click-worthy
- Focus on action/benefit/solution
- Use Title Case (capitalize major words)

{format_instruction}

{platform_instruction}

{terminology_instruction}

{product_instruction}

Primary keyword (MUST include): {primary_keyword}

Generate a new SEO title that meets all requirements.
Return ONLY the title text — no quotes, no labels, no explanation.
"""
        
        context = f"Generate SEO title for: {primary_keyword}"
        
        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Generating SEO title from scratch...")
        
        try:
            result = await llm_service.run_agent(
                instructions=instructions,
                context=context,
                agent_name="seo-title-generator",
                temperature=0.7,
                max_turns=1
            )

            # ── Record token usage for this attempt ──────────────────────────
            if metrics is not None:
                metrics.record_llm_usage(
                    input_tokens=result.token_usage["input_tokens"],
                    output_tokens=result.token_usage["output_tokens"]
                )
            print(f"seo llm---- {result.token_usage['output_tokens']}-- {result.token_usage['input_tokens']}", flush=True)

            # ─────────────────────────────────────────────────────────────────
            
            candidate = result.final_output.strip().strip('"').strip("'")
            
            # Validate response
            if not candidate or len(candidate.strip()) == 0:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM returned empty response")
                if attempt == MAX_RETRIES:
                    return None
                continue
            
            # Validate product name handling (if provided)
            product_name_violated = False
            if product_name:
                product_in_candidate = product_name.lower() in candidate.lower()
                
                if product_in_candidate:
                    if product_name not in candidate:
                        print(f"  [Attempt {attempt}/{MAX_RETRIES}] Product name present but modified")
                        print(f"      Expected: '{product_name}'")
                        print(f"      Retry...")
                        product_name_violated = True
                        continue
                else:
                    keywords_to_check = []
                    
                    if 'python' in product_name.lower():
                        keywords_to_check.append('python')
                    if '.net' in product_name.lower():
                        keywords_to_check.append('.net')
                    if 'java' in product_name.lower() and 'javascript' not in product_name.lower():
                        keywords_to_check.append('java')
                    if 'c#' in product_name.lower():
                        keywords_to_check.append('c#')
                    
                    match = re.match(r'^(.+?)\s+(?:for|via)\s+', product_name)
                    if match:
                        product_brand = match.group(1)
                        if product_brand.lower() in candidate.lower():
                            print(f"  [Attempt {attempt}/{MAX_RETRIES}] Incomplete product name detected")
                            print(f"      Found: '{product_brand}' without platform")
                            print(f"      Expected full: '{product_name}' or remove entirely")
                            product_name_violated = True
                            continue
                    
                    platform_keywords_from_param = []
                    if platform_for_title:
                        platform_keywords_from_param.append(platform_for_title.lower())
                    
                    for keyword in keywords_to_check:
                        keyword_pattern = rf'\b{re.escape(keyword)}\b'
                        if re.search(keyword_pattern, candidate, re.IGNORECASE):
                            if keyword.lower() not in platform_keywords_from_param:
                                print(f"  [Attempt {attempt}/{MAX_RETRIES}] Platform keyword '{keyword}' found without product name")
                                print(f"      Full product is: '{product_name}'")
                                print(f"      Either use complete product name or remove platform mention")
                                product_name_violated = True
                                break
            
            if product_name_violated:
                continue
            
            # Check for banned terms
            banned_terms = [
                'online tool', 'online app', 'web-based tool', 'web app',
                'browser-based', 'web-based', 'no installation',
                'free library', 'free api', 'free sdk', 'free tool',
                'free software', 'free download'
            ]
            
            if re.search(r'\bfree\b', candidate, re.IGNORECASE):
                banned_found = 'free'
            else:
                banned_found = None
                for banned_term in banned_terms:
                    if banned_term.lower() in candidate.lower():
                        banned_found = banned_term
                        break
            
            if banned_found:
                print(f"  [Attempt {attempt}/{MAX_RETRIES}] Banned term detected: '{banned_found}'")
                print(f"      We are NOT writing about online/web-based applications")
                print(f"      Retrying...")
                continue
            
            is_valid, reason = is_valid_seo_title(candidate, primary_keyword)
            
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] Generated: '{candidate}' ({len(candidate)} chars)")
            
            if is_valid:
                print(f"  ✅ Valid SEO title on attempt {attempt}.")
                return candidate
            else:
                print(f"  ❌ Invalid: {reason}")
                
        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] LLM call failed: {e}")
            if attempt == MAX_RETRIES:
                return None
            continue
    
    print(f"  ❌ Could not generate valid SEO title after {MAX_RETRIES} attempts.")
    return None


async def validate_and_fix_seo_title(
    title: str,
    primary_keyword: str,
    product_name: str = None,
    isCloud: bool = False,
    platform: str = None,
    verbose: bool = True,
    metrics=None                          # ← NEW: optional MetricsRecorder
) -> str:
    """
    Validate existing title or generate new SEO-optimized title.
    
    Args:
        title: The existing title to validate
        primary_keyword: The primary keyword that must be included
        product_name: Optional exact product name (e.g., "Aspose.HTML for Python via .NET")
        isCloud: If True, use "library/API" terminology; if False, use "SDK" terminology
        platform: Optional platform name (e.g., "Python via .NET", "Java", ".NET")
        verbose: If True, print detailed generation info
        metrics: Optional MetricsRecorder instance to track token usage
        
    Returns:
        Validated existing title or newly generated SEO title
    """
    # Extract platform name for display (trim "via X" if present)
    platform_display = None
    if platform:
        platform_display = platform.split(' via ')[0].strip() if ' via ' in platform else platform.strip()
    
    # AUTO-CORRECT: Fix Title Case before validation
    title_corrected = fix_title_case(title)
    
    # OPTIMIZATION: If title is valid, return it as-is (no LLM call needed)
    is_valid, reason = is_valid_seo_title(title_corrected, primary_keyword)
    
    if is_valid:
        if verbose:
            if title_corrected != title:
                print(f"✅ Title fixed (Title Case corrected):")
                print(f"   Original: '{title}'")
                print(f"   Corrected: '{title_corrected}'")
            else:
                print(f"✅ Title is already valid:")
                print(f"   Title: '{title_corrected}'")
            print(f"   Length: {len(title_corrected)} chars")
            print(f"   Contains keyword: '{primary_keyword}' ✓")
            print(f"   No generation needed - returning as-is")
        return title_corrected
    
    # Title is invalid - generate new one
    if verbose:
        print(f"⚠️  Title is invalid: {reason}")
        print(f"   Current title: '{title}'")
        print(f"   Generating new title...")
        print(f"📏 Generation parameters:")
        print(f"   Primary keyword: '{primary_keyword}'")
        if product_name:
            print(f"   Product name: '{product_name}'")
        if platform_display:
            print(f"   Platform: '{platform_display}'")
        print(f"   Product type: {'Cloud (Library/API)' if isCloud else 'Non-Cloud (SDK)'}")
    
    # Generate new title from scratch — pass metrics through
    generated_title = await generate_seo_title_with_llm(
        primary_keyword,
        product_name,
        isCloud,
        platform,
        metrics=metrics                   # ← pass it down
    )
    
    if generated_title is None:
        if verbose:
            print("❌ Generation failed. Creating fallback title...")
        
        if product_name:
            fallback = f"{primary_keyword.title()}: {product_name} Guide"
        else:
            fallback = f"{primary_keyword.title()}: Complete Guide"
        
        if len(fallback) > SEO_TITLE_MAX:
            fallback = f"{primary_keyword.title()}: Tutorial"
        
        if verbose:
            print(f"   Fallback title: '{fallback}' ({len(fallback)} chars)")
        
        return fallback
    
    if verbose:
        print(f"✅ SEO title generated: '{generated_title}' ({len(generated_title)} chars)")
    
    return generated_title