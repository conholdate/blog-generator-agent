import json
from datetime import datetime
import sys, os
from .helpers import slugify
from .layouts import default_choice, render_prompt_blocks, LayoutChoice
from typing import List, Dict, Optional
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import format_related_posts
from config import settings


from datetime import datetime
from typing import Dict, List


def extract_product_names(names):
    return [
        {
            "ProductName": item.get("ProductName"),
            "ProductURL": item.get("ProductURL")
        }
        for item in names
        if "ProductName" in item and "ProductURL" in item
    ]


def build_allowed_products_block(allowed_products, primary_product_name):
    products = extract_product_names(allowed_products)

    lines = []
    for p in products:
        if p["ProductName"] == primary_product_name:
            lines.append(f"  - {p['ProductName']} <- PRIMARY PRODUCT (this blog's subject)")
        else:
            lines.append(f"  - {p['ProductName']} | {p['ProductURL']}")

    allowed_list = "\n".join(lines)

    return f"""
===============================================================================
CRITICAL: CROSS-PRODUCT MENTIONS - STRICT ALLOWLIST (NON-NEGOTIABLE)
===============================================================================

The ONLY products that exist for this brand are listed below.
NEVER mention any product not on this list - not even plausibly named ones.
If a product name is not in this list, it does not exist. Do not guess,
infer, or invent product names under any circumstances.

ALLOWED PRODUCTS (name + URL for any secondary mentions):
{allowed_list}

PRIMARY PRODUCT FOR THIS BLOG: {primary_product_name}

RULES:
1. This blog is EXCLUSIVELY about the PRIMARY PRODUCT listed above.
   Every section must stay focused on it. Do not drift into unrelated
   product territory.

2. Only reference a secondary product from the allowlist above when it
   solves a DIRECT integration need that the primary product cannot
   handle alone.
   VALID example: primary product generates a barcode image ->
     mentioning Aspose.PDF for .NET to embed it in a PDF is valid.
   INVALID example: mentioning another product just to pad a features
     section or add variety to the text.

3. When mentioning a secondary product, use its EXACT name from the
   allowlist above - character for character. Do not shorten, rephrase,
   abbreviate, or infer a variant name.

4. Never link to a secondary product URL unless that URL appears in the
   allowlist above. Name-only mentions without a hyperlink are acceptable
   when the primary product context did not supply a URL for that product.

5. VIOLATION EXAMPLE - what this rule was created to prevent:
   A blog about Aspose.BarCode for .NET mentioned "Aspose.DICOM" - a
   product name that does not exist in the allowlist. This is a
   hallucination. It must never happen again. When in doubt, do not
   mention a secondary product at all.
===============================================================================
"""


def get_blog_writer_prompt(
    title: str,
    keywords: List[str],
    outline: List[str],
    related_links: List[Dict[str, str]],
    context: str = "",
    author: str = "",
    target_persona: str = "",
    angle: str = "",
    long_tail_keywords: str = "",
    semantic_keywords: str = "",
    other_important_and_relevant_things: str = "",
    tags: List[str] = [],
    isCloud: bool = False,
    allowed_products: List[str] = [],
    layout_choice: Optional[LayoutChoice] = None,
    generated_code: Optional[Dict[str, str]] = None
) -> str:
    """
    Creates a full SEO blog-writing prompt with frontmatter, layout-driven
    structure, outline coverage rules, and a final 'Read More' section using
    the provided related_links. If layout_choice is None, the classic layout
    is used (backwards-compatible default).
    """
    url = slugify(title)

    # Parse context fields
    data = {}
    for line in context.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    category = data.get("Category", "General")

    # Properly formatted Read More links (SAFE)
    formatted_related = format_related_posts(related_links)

    # Date
    current_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    primary_keyword = keywords[0]
    secondary_keywords = keywords[1:]

    # ------------------------------------------------------------------
    # Normalise optional string parameters: callers may pass a list, None,
    # or an empty string.  Convert everything to a plain str so that
    # .strip() and f-string interpolation never raise AttributeError.
    # ------------------------------------------------------------------
    def _to_str(value) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value)

    long_tail_keywords                  = _to_str(long_tail_keywords)
    semantic_keywords                   = _to_str(semantic_keywords)
    other_important_and_relevant_things = _to_str(other_important_and_relevant_things)

    print(f"primary_keyword -- {primary_keyword}")
    print(f"secondary_keywords -- {secondary_keywords}")
    print(f"long_tail_keywords -- {long_tail_keywords}", flush=True)
    print(f"semantic_keywords -- {semantic_keywords}", flush=True)
    print(f"blog_outline -- {outline}", flush=True)
    print(f"other_important_and_relevant_things -- {other_important_and_relevant_things}", flush=True)
    print(f"target persona -- {target_persona}", flush=True)
    print(f"Blog post angle -- {angle}", flush=True)

    # ------------------------------------------------------------------
    # Build the allowed products block from the passed-in list.
    # Falls back to an empty string if no products were supplied so the
    # rest of the prompt is unaffected.
    # ------------------------------------------------------------------
    primary_product_name = data.get("ProductName", "")
    allowed_products_block = (
        build_allowed_products_block(allowed_products, primary_product_name)
        if allowed_products
        else ""
    )

    # ------------------------------------------------------------------
    # Layout system: the chosen layout drives the post structure. The
    # outline from the sheet is treated as a keyword-preserving coverage
    # checklist, not a heading list.
    # ------------------------------------------------------------------
    if layout_choice is None:
        layout_choice = default_choice(is_cloud=isCloud)
    layout_blocks = render_prompt_blocks(
        layout_choice,
        is_cloud=isCloud,
        has_read_more=bool(formatted_related),
        outline_items=outline,
    )
    print(f"layout -- {layout_choice.name} ({layout_choice.reason})", flush=True)
    print(f"skeleton -- {layout_blocks['skeleton_summary']}", flush=True)

    # ------------------------------------------------------------------
    # Optional blocks - only rendered when the values are non-empty
    # ------------------------------------------------------------------
    long_tail_block = (
        f"""
===============================================================================
LONG-TAIL KEYWORDS (INCORPORATE NATURALLY - SEO)
===============================================================================

The following long-tail keyword phrases have been identified for this topic:

{long_tail_keywords}

RULES FOR LONG-TAIL KEYWORD USAGE:
- Weave these phrases naturally into H2/H3 headings, body paragraphs, step
  descriptions, and FAQ questions/answers wherever they fit contextually.
- Do NOT force every phrase - use only those that genuinely improve the flow
  and relevance of the surrounding text.
- Long-tail phrases are especially effective in H3 subheadings, introductory
  sentences for sections, and FAQ question text.
- NEVER bold or italicise them purely for emphasis.
- They contribute to overall keyword richness but do NOT replace the mandatory
  occurrences of the primary keyword.
- Aim to use at least 2-3 of these phrases somewhere in the blog body.
"""
        if long_tail_keywords.strip()
        else ""
    )

    semantic_keywords_block = (
        f"""
===============================================================================
SEMANTIC / LSI KEYWORDS (ENRICH CONTENT NATURALLY)
===============================================================================

The following semantically related keywords and phrases should be distributed
naturally throughout the blog to improve topical depth and search relevance:

{semantic_keywords}

RULES FOR SEMANTIC KEYWORD USAGE:
- Use these words and phrases naturally in body paragraphs, section
  introductions, step descriptions, and explanatory sentences.
- Do NOT cluster them together or list them artificially anywhere in the post.
- They should appear only where they genuinely add meaning to the surrounding
  text - never forced or out of context.
- These are NOT replacements for the primary or secondary keywords.
- Aim to use most of these terms at least once across the full blog body.
- Their natural presence signals topical authority to search engines; forced
  or unnatural use undermines that goal.
"""
        if semantic_keywords.strip()
        else ""
    )

    other_notes_block = (
        f"""
===============================================================================
OTHER IMPORTANT NOTES AND CONTEXT
===============================================================================

The following additional guidance, product-specific notes, or editorial context
has been provided by the content team. Incorporate it naturally throughout the
blog where relevant:

{other_important_and_relevant_things}

RULES:
- Treat this as supplementary editorial guidance, not a section to reproduce
  verbatim in the blog output.
- Surface relevant points in the appropriate sections - Prerequisites, Steps,
  Conclusion, FAQs, etc. - rather than grouping them all in one place.
- Paraphrase and integrate naturally; do NOT copy-paste this block into the
  blog output.
- If any note here contradicts an earlier rule in this prompt, the earlier
  rule takes precedence unless the note explicitly states otherwise.
"""
        if other_important_and_relevant_things.strip()
        else ""
    )

    # ------------------------------------------------------------------
    # Provided code: the single source-of-truth snippet generated before
    # this prompt was built. Every code-bearing section derives from it
    # instead of inventing its own code (cURL is the one exception - it's
    # a separate REST approach to the same task, not a translation of it).
    # ------------------------------------------------------------------
    provided_code_block = ""
    if generated_code and generated_code.get("code"):
        code_language = generated_code.get("language", "")
        code_body = generated_code.get("code", "")
        provided_code_block = f"""
===============================================================================
PROVIDED CODE (SOURCE OF TRUTH FOR ALL CODE IN THIS POST)
===============================================================================

The following {code_language} code has already been written and verified. It
performs the exact task this blog post is about. Every code-bearing section in
this post MUST derive its code from this snippet - do not invent different
code that accomplishes the same task another way.

```{code_language}
{code_body}
```

RULES FOR USING THIS CODE:
1. COMPLETE CODE EXAMPLE section: reproduce this code EXACTLY as given above,
   wrapped in COMPLETE_CODE_SNIPPET tags, with the mandatory intro sentence
   and disclaimer. Do not modify, shorten, rename variables, or rewrite it.
2. Steps / Setup / Walkthrough / How the Code Works / Implementation /
   Configuration sections: any short snippet shown MUST be excerpted
   directly from the code above - same class/method names, same logic. Do
   not invent alternate code that does the same thing a different way.
3. cURL Commands section: this is a SEPARATE REST API approach to the SAME
   task (same source/target file formats, same operation) - it is NOT a
   translation of the code above. Write idiomatic cURL calls for the
   equivalent REST operation.
===============================================================================
"""

    # ------------------------------------------------------------------
    # FULL PROMPT
    # ------------------------------------------------------------------
    return f"""
You are an expert technical blog writer. Write a detailed, SEO-optimized blog post about "{title}" using keywords: {keywords}, target persona: {target_persona}, angle: {angle}

{context}

===============================================================================
STEP 0 - MANDATORY HEADING PLAN (DO THIS BEFORE WRITING ANYTHING ELSE)
===============================================================================

Before writing a single word of content, you MUST complete this heading plan:

1. Write down every H2 heading you intend to use across the entire blog
2. Apply Title Case to every heading - every major word must start with a capital letter
3. Apply file format and product name capitalization rules to every heading
4. Match every H2 to the MANDATORY CONTENT FLOW for this post's layout (defined in Part 2) - same sections, same order, nothing extra
5. For each heading, extract its core keyword phrase (2-4 words)
6. Scan the list - if any core keyword phrase appears more than ONCE, rewrite that heading NOW
7. Only proceed to write content after every heading in your plan is unique, Title Cased, correctly ordered, and has correct format/product casing

**TITLE CASE CHECK - APPLY TO EVERY HEADING BEFORE WRITING:**
After writing your heading plan, scan every heading and verify Title Case is applied.
Every major word MUST start with a capital letter - no exceptions.
WRONG: ## Steps to CSV editor Development in Java
CORRECT: ## Steps to CSV Editor Development in Java
WRONG: ## CSV editor Development in Java - Complete Code Example
CORRECT: ## CSV Editor Development in Java - Complete Code Example
WRONG: ## Key features of GroupDocs.Editor Cloud SDK for Java
CORRECT: ## Key Features of GroupDocs.Editor Cloud SDK for Java

Title Case Rules:
- Capitalize: First word, last word, and all major words
- Major words: Nouns, verbs, adjectives, adverbs, pronouns
- Lowercase only: Articles (a, an, the), short conjunctions (and, but, or), short prepositions (in, on, at, to, for, with, from)
- EXCEPTION: Always capitalize prepositions of 5+ letters (Between, Through, Without, Against)

**FILE FORMAT AND PRODUCT NAME CAPITALIZATION - APPLY TO ALL HEADINGS:**
After Title Case verification, scan every heading for file format names and product abbreviations.

FILE FORMATS must always be fully uppercase - no exceptions:
- WRONG: Dwt, Pdf, Png, Html, Docx, Xlsx, Csv, Json, Xml, Svg, Dxf, Dwg, Stl, Obj, Fbx, Jpg, Jpeg, Bmp, Gif, Tiff, Psd, Ai, Eps, Zip, Rar, Mp4, Mp3, Doc, Xls, Ppt, Odt, Rtf, Txt, Msg, Eml
- CORRECT: DWT, PDF, PNG, HTML, DOCX, XLSX, CSV, JSON, XML, SVG, DXF, DWG, STL, OBJ, FBX, JPG, JPEG, BMP, GIF, TIFF, PSD, AI, EPS, ZIP, RAR, MP4, MP3, DOC, XLS, PPT, ODT, RTF, TXT, MSG, EML

PRODUCT NAME ABBREVIATIONS must use correct casing:
- WRONG: Aspose.Cad, Aspose.Pdf, Aspose.Html, Aspose.Zip, Groupdocs, Conholdate
- CORRECT: Aspose.CAD, Aspose.PDF, Aspose.HTML, Aspose.ZIP, GroupDocs, Conholdate

MICROSOFT AND THIRD-PARTY BRAND NAMES must use correct casing everywhere - headings, body, FAQs, frontmatter:
- WRONG: Powerpoint, powerpoint, Power Point
- CORRECT: PowerPoint
- WRONG: Sharepoint, Share Point
- CORRECT: SharePoint
- WRONG: Github, Git Hub
- CORRECT: GitHub
- WRONG: Javascript, java script
- CORRECT: JavaScript
- WRONG: Typescript, Type Script
- CORRECT: TypeScript
- WRONG: Dotnet, dot net, .net (when used as a brand name)
- CORRECT: .NET
- WRONG: Csharp, c sharp, C#  (as "csharp" in text)
- CORRECT: C#
- WRONG: Nuget, Nu Get
- CORRECT: NuGet
- WRONG: Macos, Mac Os, MAC OS
- CORRECT: macOS
- WRONG: Ios, IOS (when referring to Apple's OS)
- CORRECT: iOS
- WRONG: Api, rest api (when used as acronym)
- CORRECT: API, REST API
- WRONG: Sdk, sdk
- CORRECT: SDK
- WRONG: Json, Xml, Html (when used as acronym in body text)
- CORRECT: JSON, XML, HTML

EXAMPLES:
- WRONG: ## Dwt to Pdf Conversion Using Rest in Java
- CORRECT: ## DWT to PDF Conversion Using REST in Java
- WRONG: ## Aspose.Cad for Java - Prerequisites and Setup
- CORRECT: ## Aspose.CAD for Java - Prerequisites and Setup
- WRONG: ## Convert Dwg to Stl in Python
- CORRECT: ## Convert DWG to STL in Python

**HEADING PLAN FORMAT (fill this out mentally before writing):**

{layout_blocks['heading_plan']}

**DEDUPLICATION CHECK - STRICTLY ENFORCED:**
- Extract the core 2-4 word phrase from each heading
- If the SAME phrase appears in 2 or more headings - REWRITE one of them
- A phrase is "the same" if it shares 3+ consecutive words with another heading
- NO exceptions - every heading must have a unique core phrase

**WRONG (CSV Editor Development in Java appears 3 times):**
  ## CSV Editor Development in Java - Prerequisites and Setup  <- phrase used
  ## CSV Editor Development in Java                            <- same phrase
  ## CSV Editor Development in Java - Complete Code Example    <- same phrase again

**CORRECT (each heading has a unique core phrase):**
  ## Steps to Build a CSV Editor in Java                       <- "Build CSV Editor"
  ## Java CSV Editing - Complete Code Example                  <- "Java CSV Editing"
  ## CSV Editor Development - Prerequisites and Setup          <- "CSV Editor Development"
  ## Key Features of the CSV Editor SDK                        <- "CSV Editor SDK"
  ## CSV File Editing via REST API using cURL                  <- "CSV File Editing"

**YOU MUST NOT PROCEED TO WRITE CONTENT UNTIL THIS CHECK IS COMPLETE.**

===============================================================================
CRITICAL REQUIREMENT - PRODUCT URL LINKING (READ THIS FIRST)
===============================================================================

**ABSOLUTE MANDATORY REQUIREMENT:**

THE FIRST PARAGRAPH OF YOUR BLOG POST **MUST** CONTAIN A LINK TO THE PRODUCT PAGE.

**Format:** [Full Product Name with Platform](ProductURL from context)

**Example:** [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)

**Where to get the URL:** context["ProductURL"] or context.get("ProductURL")

**Validation:**
- If the product link is NOT in the first paragraph - OUTPUT IS INVALID
- If the product name is not fully qualified with platform - OUTPUT IS INVALID
- If using generic text like "the SDK" or "this library" instead of product name - OUTPUT IS INVALID

**Correct First Paragraph Examples:**

[Aspose.PDF for .NET](ProductURL) is a powerful SDK that enables developers to work with PDF documents programmatically. This guide demonstrates how to convert PDF files to PNG format using C#.

Document conversion is essential in modern applications. [GroupDocs.Conversion for Java](ProductURL) provides comprehensive APIs for converting between various file formats with ease.

Working with compressed archives programmatically requires a robust solution. [Aspose.ZIP for Python via .NET](ProductURL) offers extensive features for creating and ZIP files in Python applications.

**Wrong Examples (DO NOT DO THIS):**

- "Converting PDF to PNG is a common task. Many developers need this functionality. [Aspose.PDF for .NET](ProductURL) provides..." - LINK IN SECOND PARAGRAPH, NOT FIRST
- "Aspose.PDF for .NET is a powerful SDK..." - NO LINK AT ALL
- "[This SDK](ProductURL) provides powerful features..." - NOT USING PRODUCT NAME
- "[Aspose.PDF](ProductURL) offers document processing..." - MISSING PLATFORM

**THIS IS NON-NEGOTIABLE. THE PRODUCT LINK MUST BE IN THE FIRST PARAGRAPH.**

===============================================================================
CRITICAL: MARKDOWN LINK FORMAT - ZERO TOLERANCE FOR MALFORMED LINKS
===============================================================================

**THIS IS THE MOST IMPORTANT FORMATTING RULE IN THIS ENTIRE PROMPT.**

Every single hyperlink you write MUST follow this exact format:

    [link text](URL)

That means:
1. Opening square bracket  [
2. Link text (the visible words)
3. Closing square bracket  ]
4. Opening parenthesis  (   - immediately after ], NO space allowed
5. The full URL
6. Closing parenthesis  )

**THERE MUST BE NO SPACE BETWEEN ] AND ( - EVER.**

-------------------------------------------------------------------------------
COMPLETE LIST OF MALFORMED PATTERNS - NEVER PRODUCE ANY OF THESE
-------------------------------------------------------------------------------

Every pattern below is WRONG. Study each one so you never produce it:

WRONG: [Aspose.3D for Java (https://example.com/)
  WHY: Missing closing bracket ] before the URL's opening parenthesis
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java] (https://example.com/)
  WHY: Space between ] and ( - no space is ever allowed here
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: Aspose.3D for Java](https://example.com/)
  WHY: Missing opening bracket [ before the link text
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: Aspose.3D for Java] (https://example.com/)
  WHY: Missing opening bracket [ and space before (
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java(https://example.com/)
  WHY: Missing closing bracket ] - ( must be preceded by ]
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: Aspose.3D for Java (https://example.com/)
  WHY: Missing both [ and ] around the link text
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java](https://example.com/
  WHY: Missing closing parenthesis ) at the end
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java]https://example.com/
  WHY: Missing opening parenthesis ( before the URL
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: (https://example.com/)[Aspose.3D for Java]
  WHY: URL and text are in reversed order
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java (https://example.com/
  WHY: Missing ] and missing closing )
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java(https://example.com/
  WHY: Missing ] and missing closing )
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [](https://example.com/)
  WHY: Empty link text - always provide meaningful text
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java]()
  WHY: Empty URL - always provide the full URL
  FIX: [Aspose.3D for Java](https://example.com/)

-------------------------------------------------------------------------------
THE ONLY CORRECT FORMAT
-------------------------------------------------------------------------------

CORRECT: [Aspose.3D for Java](https://products.aspose.com/3d/java/)
CORRECT: [official documentation](https://docs.aspose.com/3d/java/)
CORRECT: [support team](https://forum.aspose.com/c/3d/18)
CORRECT: [this page](https://releases.aspose.com/3d/java/)
CORRECT: [temporary license page](https://purchase.aspose.com/temporary-license/)

-------------------------------------------------------------------------------
MANDATORY MENTAL CHECKLIST - RUN THIS BEFORE WRITING EVERY SINGLE LINK
-------------------------------------------------------------------------------

Before you type any hyperlink, ask yourself these five questions:

  1. Did I write the opening bracket [ first?
  2. Is all the link text between [ and ]?
  3. Does ] come immediately before ( with NO space between them?
  4. Is the full URL between ( and )?
  5. Does the link end with a closing parenthesis )?

If the answer to ANY question is NO - do not write the link until it is fixed.

-------------------------------------------------------------------------------
SCAN BEFORE FINALIZING
-------------------------------------------------------------------------------

Before you output the complete blog post, scan the entire document for:

- Any ] at the start of a word or immediately before a URL without a preceding [
- Any product name or text followed by (https:// without a preceding [text]
- Any [text] followed by a space before (
- Any [text( without a ] between the text and the URL
- Any link missing its closing )

If you find any of these patterns - fix them before outputting.

**THIS RULE OVERRIDES ALL OTHER FORMATTING DECISIONS. A SINGLE MALFORMED LINK
INVALIDATES THE ENTIRE OUTPUT.**

===============================================================================
CRITICAL: CONTENT BOUNDARIES (NON-NEGOTIABLE)
===============================================================================
START: Blog MUST begin with frontmatter (---) - NO text before
END: Blog MUST end after {'Read More section' if formatted_related else 'FAQs section'} - NO text after
PROHIBITED: No introductory text, concluding remarks, author notes, meta-commentary outside structure

===============================================================================
CRITICAL RESTRICTIONS
===============================================================================
NEVER mention or imply:
- "free SDK" or "free library" or "free API"
- "online tool" or "online app" or "web-based application"
- "no installation required" or "browser-based"
- Any suggestion that this is a web service or online platform

ALWAYS clarify:
- This is a desktop/server SDK that requires installation
- This is a library/API for programmatic integration
- Code runs on your local machine or server
- Requires proper licensing for production use

{allowed_products_block}

===============================================================================
PART 1: FRONTMATTER REQUIREMENTS
===============================================================================

### TITLE REQUIREMENTS (CRITICAL)
**Title Field (DO NOT MODIFY):**
- Title field: MUST use title variable exactly as provided - DO NOT modify
- DO NOT change, shorten, or adjust the title
- DO NOT remove brand names or product names from title
- The title variable is pre-validated and must be used as-is

**SEO Title Field:**
- seoTitle MUST be identical to the title field
- Use the EXACT same value as title - do not modify, shorten, or rephrase
- CORRECT: title: "How to Convert PDF to PNG in C#" and seoTitle: "How to Convert PDF to PNG in C#"
- WRONG: seoTitle with any different value than title

### META DESCRIPTION - CHARACTER LIMITS (STRICTLY ENFORCED)
META DESCRIPTION LENGTH: EXACTLY 140-160 CHARACTERS

**MANDATORY VALIDATION PROCESS (FOLLOW THIS EXACTLY):**

STEP 1: Write your meta description draft
STEP 2: Count EVERY character including spaces, punctuation, and letters
STEP 3: If count is below 140 - ADD more descriptive words until 140-160
STEP 4: If count is above 160 - REMOVE words until 140-160
STEP 5: Count again to verify before finalizing
STEP 6: Only include if count is between 140-160 (inclusive)

**CHARACTER COUNTING RULES:**
- Count spaces as 1 character each
- Count punctuation (.,!?-) as 1 character each
- Count every letter and number
- Include ALL characters - nothing is excluded

**CORRECT LENGTH EXAMPLES:**
- "Learn how to convert PDF files to PNG images in C# using Aspose.PDF for .NET. This guide covers step-by-step implementation with working code." (143 chars - CORRECT)
- "Convert PDF to PNG programmatically in C# with Aspose.PDF for .NET. Follow this step-by-step guide with complete code examples for developers." (143 chars - CORRECT)

**OUTPUT IS INVALID IF:**
- Meta description is less than 140 characters
- Meta description is more than 160 characters

**THIS IS NON-NEGOTIABLE. META DESCRIPTION MUST BE 140-160 CHARACTERS.**

### SUMMARY - CHARACTER LIMITS (STRICTLY ENFORCED)
SUMMARY LENGTH: EXACTLY 200-260 CHARACTERS

**MANDATORY VALIDATION PROCESS (FOLLOW THIS EXACTLY):**

STEP 1: Write your summary draft
STEP 2: Count EVERY character including spaces, punctuation, and letters
STEP 3: If count is below 200 - ADD more descriptive words until 200-260
STEP 4: If count is above 260 - REMOVE words until 200-260
STEP 5: Count again to verify before finalizing
STEP 6: Only include if count is between 200-260 (inclusive)

**CORRECT LENGTH EXAMPLE:**
"Learn how to convert PDF files to PNG images in C# using Aspose.PDF for .NET. This guide walks you through the entire process with working code examples, prerequisites, and step-by-step instructions to help you implement PDF to PNG conversion." (244 chars - CORRECT)

**OUTPUT IS INVALID IF:**
- Summary is less than 200 characters
- Summary is more than 260 characters

**THIS IS NON-NEGOTIABLE. SUMMARY MUST BE 200-260 CHARACTERS.**

### PRODUCT/BRAND NAME REMOVAL (URL ONLY)
REMOVE from URL slug only:
- Brand names: Aspose, GroupDocs, Conholdate
- Product names: Aspose.PDF, GroupDocs.Conversion, Conholdate.Total, etc.

KEEP in title, seoTitle, and content body:
- Use the EXACT title from {{title}} variable (keep all brand/product names)
- Use full product names with platform in content: "Aspose.Slides for .NET"
- Link to product pages when mentioning products

### URL SLUG RULES (CRITICAL)
- Lowercase, hyphens for spaces
- NO product/brand names
- MUST use "in" before language/platform
- Examples:
  - "convert-pdf-to-png-in-csharp" - CORRECT
  - "excel-to-pdf-in-java" - CORRECT
  - "html-to-markdown-in-python" - CORRECT
  - "convert-pdf-png-csharp" - WRONG (missing "to" and "in")
  - "convert-pdf-aspose-java" - WRONG (contains brand)

### MARKDOWN-SAFE CONTENT (MANDATORY)
Replace automatically throughout ALL CONTENT (including frontmatter):
- Em dash (-) to single hyphen (-)
- En dash (-) to single hyphen (-)
- Non-breaking hyphen to regular hyphen (-)
- Curly double quotes to straight quotes (")
- Curly single quotes to straight quotes (')
- Ellipsis (...) to three periods (...)
- Copyright (c), Registered (R), Trademark (TM)
- Bullet to hyphen (-)
- Degree symbol to "degrees"
- NEVER use em dashes or en dashes anywhere in content
- NEVER use typographic quotes or smart quotes
- ALWAYS use simple ASCII punctuation

**CRITICAL: FRONTMATTER YAML SAFETY (STRICTLY ENFORCED)**

**YAML QUOTING RULES:**
1. ALL string values in frontmatter MUST use ONLY straight double quotes (")
2. NEVER use single quotes (') in YAML
3. ALL values containing ANY of these characters MUST be quoted:
   - Colons (:)
   - Question marks (?)
   - Hyphens at start of value (-)
   - Any quotes within the text

4. **For FAQs section specifically:**
   - Both q: and a: values MUST ALWAYS be quoted with straight double quotes
   - If the answer text contains quotes, escape them: \"
   - NEVER use curly quotes, em dashes, en dashes, or non-breaking hyphens in FAQ text
   - Replace ALL special punctuation with ASCII before writing to frontmatter

**CORRECT YAML FAQ FORMAT:**
```yaml
faqs:
  - q: "How do I handle custom fonts during conversion?"
    a: "The SDK embeds fonts into the generated HTML using @font-face rules."
  - q: "Can I convert multiple files at once?"
    a: "Yes, you can process files in a loop."
```

**WRONG YAML FAQ FORMAT (CAUSES HUGO ERRORS):**
- a: "The SDK embeds fonts using @font-face rules" with non-breaking hyphen - WRONG
- q: 'How do I process files?' with single quotes - WRONG
- a: The SDK processes files easily without quotes - WRONG

**VALIDATION BEFORE OUTPUT:**
Before finalizing frontmatter, check:
- Are ALL FAQ q: and a: values wrapped in straight double quotes?
- Are there NO curly quotes anywhere?
- Are there NO em dashes or en dashes?
- Are there NO non-breaking hyphens or special Unicode hyphens?
- Are there NO single quotes used for YAML values?
- If quotes appear INSIDE the text, are they escaped with \"?

**ABSOLUTE REQUIREMENT: All markdown links MUST use correct format [text](url)**

PROHIBITED PATTERNS (these are ERRORS that must be prevented):
- ]text](url) - Missing opening bracket
- [text(url) - Missing closing bracket before opening parenthesis
- text](url) - Missing opening bracket entirely
- [text]url) - Missing opening parenthesis
- [text] (url) - Space between ] and ( is NEVER allowed
- text (url) - Missing both brackets entirely

CORRECT FORMAT (ALWAYS use this):
- [text](url) - Square brackets around text, parentheses around URL
- [app](link) - Properly formatted with both brackets
- [documentation](https://example.com) - Complete and correct

### FRONTMATTER TEMPLATE
---
title: "{title}"
seoTitle: "{title}"
description: "[MUST BE 140-160 chars - count every character including spaces before finalizing]"
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/{url}/
author: "{author}"
summary: "[MUST BE 200-260 chars - count every character including spaces before finalizing]"
tags: {tags}
categories: ["{category}"]
showtoc: true
cover:
   image: images/{url}.jpg
   alt: "{title}"
   caption: "{title}"
steps:
  - "Step 1: [Clear actionable instruction]"
  - "Step 2: [Clear actionable instruction]"
  - "Step 3: [Clear actionable instruction]"
  - "Step 4: [Clear actionable instruction]"
  - "Step 5: [Optional]"
faqs:
  - q: "[Question - safe punctuation only]"
    a: "[Answer - include product links]"
  - q: "[Question]"
    a: "[Answer]"
  - q: "[Question]"
    a: "[Answer]"
  - q: "[Optional]"
    a: "[Optional]"
---
{provided_code_block}
===============================================================================
PART 2: CONTENT STRUCTURE (MANDATORY SECTIONS)
===============================================================================

### REQUIRED SECTIONS (IN ORDER)
This post uses the '{layout_choice.name}' layout. These are the ONLY sections allowed, in this exact order:

{layout_blocks['required_sections']}

**CRITICAL: ALL HEADINGS MUST USE TITLE CASE - H2 AND H3 WITHOUT EXCEPTION**
Every H2 (##) and every H3 (###) heading MUST follow Title Case capitalization rules.
Every major word MUST start with a capital letter - no exceptions for any heading level.
WRONG H2: ## Steps to CSV editor Development in Java
CORRECT H2: ## Steps to CSV Editor Development in Java
WRONG H3: ### optimizing HTML output performance
CORRECT H3: ### Optimizing HTML Output Performance
WRONG H3: ### configuring the conversion options for PDF
CORRECT H3: ### Configuring the Conversion Options for PDF

**H3 TITLE CASE - EXPLICITLY ENFORCED (NOT OPTIONAL):**
Every H3 subheading (### text) MUST follow the same Title Case rules as H2 headings.
Title Case is not a "recommended style" for H3 - it is mandatory and carries the same
weight as H2 enforcement. Run the exact same Title Case checklist on every H3 heading
that you run on every H2 heading during the MANDATORY HEADING SCAN.

WRONG H3 examples - output is INVALID if any of these appear:
  ### optimizing HTML output performance
  ### configuring the conversion options for PDF
  ### key differences between the two approaches
  ### handling multiple file formats in Java
  ### setting up the development environment

CORRECT H3 examples - always write H3 headings like these:
  ### Optimizing HTML Output Performance
  ### Configuring the Conversion Options for PDF
  ### Key Differences Between the Two Approaches
  ### Handling Multiple File Formats in Java
  ### Setting Up the Development Environment

{layout_blocks['content_flow']}

**GRAMMAR RULES FOR HEADINGS:**
- Product names: NEVER use articles (a/an) before product names
- CORRECT: "Prerequisites and Setup"
- WRONG: "Prerequisites and a Setup"

**HEADING CAPITALIZATION (MANDATORY - TITLE CASE FOR ALL LEVELS):**
ALL headings (H2, H3, and any other level) MUST use Title Case capitalization.

Title Case Rules:
- Capitalize: First word, last word, and all major words
- Major words: Nouns, verbs, adjectives, adverbs, pronouns
- Lowercase only: Articles (a, an, the), short conjunctions (and, but, or), short prepositions (in, on, at, to, for, with, from)
- EXCEPTION: Always capitalize prepositions of 5+ letters (Between, Through, Without, Against)

### 1. INTRODUCTION CONTENT (NO HEADING) - CRITICAL PRODUCT LINK REQUIREMENT

**MANDATORY STRUCTURE: EXACTLY ONE PARAGRAPH ONLY**

**CRITICAL RULES:**
- The introduction MUST be EXACTLY ONE paragraph
- NO second paragraph allowed
- NO third paragraph allowed
- After the single introductory paragraph, IMMEDIATELY start the FIRST H2 defined by the MANDATORY CONTENT FLOW in Part 2
- DO NOT insert any other section between the Introduction and that first H2

**SINGLE PARAGRAPH REQUIREMENTS:**
- Must be 3-5 sentences long
- FIRST sentence MUST be a punchy, engaging hook about the topic, problem, or use case
  * Hook must relate to the blog title and draw the reader in
  * DO NOT mention the product in the first sentence
  * GOOD: "Converting PDF files to PNG images is a common requirement in document processing applications, especially when you need to render pages for preview or display purposes."
  * GOOD: "Working with 3MF files programmatically can be challenging without the right tools, particularly when you need to convert them to a widely supported format like STL."
  * BAD: "Aspose.PDF for .NET is a powerful SDK that enables developers..." - starts with product, not topic
- SECOND or THIRD sentence MUST introduce and link the product: [BrandName.ProductName for Platform](ProductURL)
- MUST use FULL product name including platform
- MUST use ProductURL from context dictionary
- Remaining sentences explain what this guide will cover and what the reader will achieve
- Use correct terminology based on isCloud variable (SDK for non-cloud, library/API for cloud)

**CORRECT INTRODUCTION EXAMPLES:**

Example 1 (non-cloud):
"Converting PDF files to PNG images is a common requirement in document processing pipelines, especially for generating previews or thumbnails. [Aspose.PDF for .NET](ProductURL) is a powerful SDK that makes this conversion straightforward in C# applications. In this guide, you will learn how to implement PDF to PNG conversion step by step with complete working code examples."

Example 2 (non-cloud):
"Handling 3MF files programmatically requires a reliable solution that supports modern 3D file formats. [Aspose.3D for Java](ProductURL) provides a comprehensive SDK for working with 3D file formats, including converting 3MF to STL with just a few lines of code. This tutorial walks you through the entire process with prerequisites, implementation steps, and a complete code example."

Example 3 (cloud):
"Automating document conversion at scale is a challenge that many development teams face when building modern applications. [GroupDocs.Conversion Cloud](ProductURL) provides a powerful REST API that handles format conversion without any local installation. This guide shows you how to integrate PDF to Word conversion into your application using simple API calls."

**WRONG INTRODUCTION EXAMPLES:**
- "Aspose.PDF for .NET is a powerful SDK..." - WRONG: starts with product name, no hook
- "In today's digital landscape, PDF conversion..." - WRONG: generic AI phrase
- "[Aspose.PDF for .NET](ProductURL) enables developers to..." - WRONG: product link in first sentence
- Two separate paragraphs in introduction - WRONG: must be exactly one paragraph

### 2. OUTLINE COVERAGE (KEYWORD-PRESERVING)

{layout_blocks['outline_coverage']}

===============================================================================
HEADING UNIQUENESS RULE (APPLIES TO ALL HEADINGS ACROSS THE ENTIRE BLOG)
===============================================================================

**THIS IS NON-NEGOTIABLE. READ BEFORE WRITING ANY HEADING.**

Every H2 heading across the entire blog MUST be unique - no two headings may
share the same keyword phrase.

**THE CORE PROBLEM TO AVOID:**

The same keyword phrase must NEVER appear in more than one heading:

  WRONG: ## CSV Editor Development in Java - Prerequisites and Setup  <- phrase used
  WRONG: ## CSV Editor Development in Java                            <- same phrase
  WRONG: ## CSV Editor Development in Java - Complete Code Example    <- same phrase again

**THE SOLUTION - KEYWORD BUDGET:**

Each heading MUST draw from a DIFFERENT part of the keyword budget.
No keyword phrase may be spent twice.

{layout_blocks['heading_budget']}

===============================================================================

### 3. BODY SECTION SPECIFICATIONS (LAYOUT: {layout_choice.name})

Each body section below MUST follow its specification. Apply Title Case to every
heading. The position labels refer to the MANDATORY CONTENT FLOW in Part 2.

{layout_blocks['section_specs']}

===============================================================================

### 5. CONCLUSION (MANDATORY)
## Conclusion

- 2-3 paragraphs summarizing key points
- Include at least 1 contextual link
- MUST link product page URL with FULL product name: [Product Name](url)
- MUST mention licensing in second half or end of conclusion
- License mention must include BOTH pricing and temporary license
- Natural closing, encourage next steps
- NEVER mention "free" or "online tool"

### 6. FAQS (MANDATORY)
## FAQs

Requirements:
- 3-4 questions
- 2-4 sentences per answer
- Include contextual links in answers
- Use product page URL with full product name: [Product Name](url)
- NEVER mention "free" or "online"

{'### 7. READ MORE (MANDATORY)' if formatted_related else '### NO READ MORE SECTION'}
{'## Read More' if formatted_related else 'Do NOT include - no related links provided.'}
{formatted_related if formatted_related else 'Blog MUST end after FAQs.'}
{'Use EXACT titles and URLs provided.' if formatted_related else ''}

===============================================================================
PART 3: TERMINOLOGY RULES (CRITICAL - STRICTLY ENFORCED)
===============================================================================

isCloud variable: {isCloud}

**DECISION RULE:**
- IF isCloud = true - Use "library" or "API" EVERYWHERE
- IF isCloud = false - Use "SDK" EVERYWHERE

### PROHIBITED TERMINOLOGY (NEVER USE)
- "Framework"
- "free SDK" or "free library" or "free API"
- "online tool" or "online app" or "web-based"
- "browser-based" or "no installation required"

===============================================================================
PART 4: LINKING REQUIREMENTS (CRITICAL)
===============================================================================

### MANDATORY LINKING RULES
1. Include MINIMUM 5-7 contextual links from provided resources
2. MUST link product page URL EVERY TIME product name is mentioned
3. MUST link Documentation URL at least once
4. MUST link API Reference URL when mentioning any class, method, or property
5. MUST link Download URL in Setup/Installation section
6. MUST link License URL at least once
7. CRITICAL: Only use links explicitly provided in context
8. NEVER construct or guess URLs
9. NEVER put links inside backticks or code literals

### PRODUCT NAME AND FILE FORMAT LINKING (CRITICAL)

**1. PRODUCT NAMES (Link to Product Page):**
Format: [Aspose.ZIP for .NET](product_page_url)

**2. FILE FORMATS (Link to FileFormat.com):**
Format: [ZIP](https://docs.fileformat.com/compression/zip/)

**3. WRONG PATTERNS TO AVOID:**
- [Aspose.ZIP](fileformat_url) - Product linked to file format
- Aspose.[ZIP](fileformat_url) - Splitting product name with file format link

===============================================================================
PART 5: CODE SNIPPET REQUIREMENTS (CRITICAL)
===============================================================================

**For Regular Code Snippets (Setup, Steps, Outline, cURL Commands):**
<!--[CODE_SNIPPET_START]-->
```language
// Your code here
```
<!--[CODE_SNIPPET_END]-->

**For Complete Code Examples (MANDATORY - DIFFERENT TAGS):**
<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Your complete working code here
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

**CRITICAL DISTINCTION:**
- Regular snippets = CODE_SNIPPET_START/END (no COMPLETE_ prefix)
- Complete examples = COMPLETE_CODE_SNIPPET_START/END (WITH COMPLETE_ prefix)
- cURL commands in the cURL section = CODE_SNIPPET_START/END (regular tags, NOT COMPLETE_ prefix)
- Using wrong tags makes output INVALID

**ALL CODE MUST BE:**
- Syntactically correct
- Executable
- Complete with all imports
- No placeholder comments like "// ... rest of code"
- NO license initialization code (License class, SetLicense, ApplyLicense)
- When a PROVIDED CODE block appears earlier in this prompt, the Complete
  Code Example section MUST reproduce it exactly - not a rewritten version

===============================================================================
PART 6: KEYWORD STRATEGY (SEO - CRITICAL)
===============================================================================

### WORD COUNT TARGET
Introduction + all body sections + Conclusion = {settings.NUMBER_OF_BLOG_WORDS} words

**FILE FORMAT CAPITALIZATION IN KEYWORDS AND BODY CONTENT (STRICTLY ENFORCED):**
All file format names appearing in keywords, outline headings, steps, body content, and FAQs
MUST be fully uppercase regardless of how they appear in the input.

Common formats to always uppercase:
DWT, DWG, DXF, DWF, DGN, DWS, IFC, IGS, IGES, STL, OBJ, FBX, 3DS, GLTF, GLB,
PDF, PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP, SVG, PSD, AI, EPS, EMF, WMF,
DOCX, DOC, XLSX, XLS, PPTX, PPT, ODT, ODS, ODP, RTF, TXT, CSV,
HTML, HTM, MHTML, XML, JSON, YAML, MARKDOWN, MD,
ZIP, RAR, TAR, GZ, 7Z, MSG, EML, MBOX, ICS, VCF,
MP4, AVI, MOV, MP3, WAV, FLAC

If a file format appears in lowercase or mixed case anywhere in the input - title, keywords,
outline, or context - override it and write it in full uppercase in the output.

WRONG: "convert dwt to pdf in java", "Dwt to Pdf", "dwt file conversion"
CORRECT: "convert DWT to PDF in Java", "DWT to PDF", "DWT file conversion"

WRONG: "Aspose.Cad for Java", "Aspose.Pdf for .NET", "Groupdocs.Conversion"
CORRECT: "Aspose.CAD for Java", "Aspose.PDF for .NET", "GroupDocs.Conversion"

### PRIMARY AND SECONDARY KEYWORDS

The PRIMARY keyword is the first keyword in the list: {primary_keyword}
The SECONDARY keywords are all remaining keywords in the list: {secondary_keywords}

**MANDATORY PRIMARY KEYWORD PLACEMENT (STRICTLY ENFORCED):**

The primary keyword MUST appear AT LEAST 3-5 times across the blog body content,
EXCLUDING frontmatter fields. Occurrences must be distributed across specific sections:

| # | Location | Requirement |
|---|----------|-------------|
| 1 | Introduction paragraph | Primary keyword MUST appear in the first paragraph |
| 2 | Middle of the blog body | Primary keyword MUST appear at least once within the middle body sections |
| 3 | Conclusion section | Primary keyword MUST appear at least once in the Conclusion |
| 4 | FAQs section | Primary keyword MUST appear at least once in the FAQs |
| 5 | Optional additional occurrence | A 5th occurrence anywhere else is encouraged |

**PRIMARY KEYWORD DENSITY RULE:**
- Target density: 1% of total blog word count
- Formula: (Total Word Count / 100) = Target minimum occurrences
- NEVER pad keyword usage artificially

**PLACEMENT RULES:**
- NEVER surround the primary keyword with asterisks, bold, or italics
- NEVER force the keyword awkwardly
- NEVER place all occurrences in the same section

Secondary keywords should appear naturally 1-2 times each, distributed across the blog body.

{long_tail_block}
{semantic_keywords_block}

===============================================================================
PART 7: WRITING GUIDELINES
===============================================================================

### HUMAN-LIKE WRITING QUALITY (CRITICAL - NON-NEGOTIABLE)

**PROHIBITED PUNCTUATION (NEVER USE):**
- Em dashes (-) - Use single hyphen (-) instead
- En dashes (-) - Use single hyphen (-) instead
- Curly quotes - Use straight quotes only
- Ellipsis character - Use three periods (...) instead

**AVOID AI-TYPICAL PHRASES:**
- "In today's digital landscape"
- "It's worth noting that"
- "Delve into" / "Dive deep into"
- "Seamlessly integrate"
- "Robust solution" / "Cutting-edge technology"
- "Production-ready" / "Ready-to-run" / "Ready-to-use" / "Copy-paste ready"
- "Enterprise-ready" / "Battle-tested"
- "In conclusion, it's clear that"

===============================================================================
MANDATORY HEADING SCAN - DO THIS BEFORE OUTPUTTING ANYTHING
===============================================================================

After writing the entire blog, you MUST perform this heading scan before producing final output.
This is NON-NEGOTIABLE. Skipping this step makes the output INVALID.

STEP 1: List every single H2 (##) and H3 (###) heading you wrote, in order.
        Do this in TWO SEPARATE GROUPS:
          Group A - H2 headings (##): list every ## heading
          Group B - H3 headings (###): list every ### heading
        Apply ALL checks in Step 2 to EVERY heading in BOTH groups.
        H3 headings are NOT exempt from Title Case. They follow the exact same
        rules as H2 headings. A lowercase H3 is as invalid as a lowercase H2.

STEP 2: For each heading in BOTH groups, apply this checklist:
  - Is the first word capitalized? If NO - fix it.
  - Is the last word capitalized? If NO - fix it.
  - Are all nouns, verbs, adjectives, adverbs capitalized? If NO - fix them.
  - Are articles (a, an, the) lowercase unless first/last word? If NO - fix them.
  - Are short prepositions (in, on, at, to, for, with, from) lowercase unless first/last? If NO - fix them.
  - Are file formats fully uppercase (PDF not Pdf, PNG not Png, DOCX not Docx)? If NO - fix them.
  - Are brand names correctly cased (PowerPoint not Powerpoint, GitHub not Github)? If NO - fix them.
  - Are Aspose product names correctly cased (Aspose.CAD not Aspose.Cad)? If NO - fix them.
STEP 3: Rewrite any heading that failed any check above - this applies equally to H2 and H3.
STEP 4: Only after ALL headings in BOTH groups pass - proceed to output the blog.

WRONG HEADINGS - NEVER OUTPUT THESE (applies to BOTH H2 and H3):
  ## steps to add animation to powerpoint in java
  ## key features of aspose.slides cloud sdk
  ## installation and setup in java
  ## configuring animation settings for powerpoint
  ## best practices for powerpoint animation via rest
  ### optimizing HTML output performance
  ### configuring the conversion options
  ### handling multiple file formats
  ### key differences between cloud and on-premise

CORRECT HEADINGS - ALWAYS OUTPUT THESE:
  ## Steps to Add Animation to PowerPoint in Java
  ## Key Features of Aspose.Slides Cloud SDK
  ## Installation and Setup in Java
  ## Configuring Animation Settings for PowerPoint
  ## Best Practices for PowerPoint Animation via REST
  ### Optimizing HTML Output Performance
  ### Configuring the Conversion Options
  ### Handling Multiple File Formats
  ### Key Differences Between Cloud and On-Premise

**IF YOU OUTPUT ANY HEADING - H2 OR H3 - IN LOWERCASE OR MIXED CASE, THE ENTIRE OUTPUT IS INVALID.**

===============================================================================

**CONTENT AUTHENTICITY CHECKS:**
Before finalizing, verify:
- No em dashes or en dashes anywhere
- Only straight quotes, no curly quotes
- No overused AI phrases
- Sentence variety
- Active voice used predominantly
- All markdown links properly formatted as [text](url) with NO space between ] and (
- Meta description is EXACTLY 140-160 characters (counted manually)
- Summary is EXACTLY 200-260 characters (counted manually)
- ALL H2 headings use Title Case - every major word starts with a capital letter - VERIFIED via MANDATORY HEADING SCAN above
- ALL H3 headings use Title Case - every major word starts with a capital letter - VERIFIED via MANDATORY HEADING SCAN above. H3 headings follow the SAME Title Case rules as H2. A lowercase H3 is identical in severity to a lowercase H2 - the output is INVALID. Example of invalid H3: ### Optimizing HTML output performance. Example of valid H3: ### Optimizing HTML Output Performance
{layout_blocks['structure_checklist']}
- Introduction is EXACTLY ONE paragraph with a punchy hook as the first sentence
- First sentence of introduction does NOT mention the product name or include a product link
- Product link appears in the SECOND or THIRD sentence of the introduction
- seoTitle is IDENTICAL to title - no changes, no shortening, no rephrasing
- STEP 0 COMPLETED: Heading plan created, Title Case verified, section order verified, all core phrases unique
- GLOBAL HEADING DEDUPLICATION: No core phrase (3+ consecutive words) appears in more than one heading
- Setup heading does NOT include the platform/language name (if prompt-generated)
- OUTLINE COVERAGE: Every non-skipped outline topic covered, with its core keyword phrase preserved in the covering section's heading or first two sentences
- FILE FORMAT CAPITALIZATION: All file format names fully uppercase (DWT not Dwt, PDF not Pdf, STL not Stl)
- PRODUCT NAME CASING: Aspose.CAD not Aspose.Cad, Aspose.PDF not Aspose.Pdf, GroupDocs not Groupdocs
- THIRD-PARTY BRAND CASING: PowerPoint not Powerpoint, SharePoint not Sharepoint, GitHub not Github, JavaScript not Javascript, NuGet not Nuget, .NET not dotnet, macOS not MacOS, iOS not IOS
- PRIMARY KEYWORD - Occurrence 1: present in the Introduction paragraph?
- PRIMARY KEYWORD - Occurrence 2: present in the middle body sections?
- PRIMARY KEYWORD - Occurrence 3: present in the Conclusion section?
- PRIMARY KEYWORD - Occurrence 4: present in at least one FAQ question or answer?
- PRIMARY KEYWORD - Total body occurrences (excluding frontmatter): at least 3, ideally 4-5?
- LONG-TAIL KEYWORDS: At least 2-3 phrases from the long-tail list used naturally in the body?
- SEMANTIC KEYWORDS: Most semantic/LSI terms appear at least once naturally in the body?
- FINAL LINK SCAN: Have you checked every single link follows [text](url) with no space between ] and (?
- HEADING UNIQUENESS: Does the Complete Code Example heading contain the primary keyword? Does the cURL heading use a secondary/semantic phrase with NO repetition of the primary keyword phrase? Are all headings distinct from each other?
- ERROR HANDLING SECTIONS SKIPPED: No section with "Error", "Troubleshooting", "Debugging", or "Common Issues" in heading included?
- CROSS-PRODUCT CHECK: Does every product name mentioned in the blog appear in the allowed products list? Is any product name invented or guessed? If yes - remove it immediately.

{other_notes_block}

===============================================================================
PART 8: FLUENCY, CLARITY AND ENGAGEMENT (TARGET: HIGH QUALITY READABLE CONTENT)
===============================================================================

**FLUENCY - Write Like a Human Expert, Not a Machine**

- Vary sentence length throughout - mix short punchy sentences with longer explanatory ones
- Never write three sentences of the same length in a row
- Use natural transitions between sentences: "This means...", "As a result...", "In practice...", "For example..."
- Avoid starting consecutive sentences with the same word or phrase
- Read each paragraph aloud mentally - if it sounds robotic, rewrite it
- Use contractions naturally where appropriate: "you'll", "it's", "don't", "here's"
- WRONG: "The method initializes the object. The object is then configured. The configuration is applied."
- CORRECT: "The method initializes the object and applies your configuration in a single call, keeping the setup minimal."

**CLARITY - Make Every Sentence Earn Its Place**

- One idea per sentence - never pack two unrelated thoughts into one sentence
- Define technical terms the first time they appear, briefly and naturally
- Use concrete examples instead of vague descriptions
  * WRONG: "The API provides various options for configuration"
  * CORRECT: "The API lets you set the output resolution, color mode, and compression level before saving"
- Lead with the most important information - put the key point at the start of a sentence, not the end
- Avoid noun stacking: "document conversion output file format" - break it up into readable phrases
- Cut filler words: "basically", "essentially", "actually", "in order to", "it is important to note that"
- Replace weak verbs with strong ones:
  * WRONG: "is used to convert", "can be utilized for"
  * CORRECT: "converts", "processes", "generates", "extracts"

**ENGAGEMENT - Keep the Reader Moving Forward**

- Open every section with a sentence that tells the reader WHY this section matters to them
  * WRONG: "Aspose.PDF has many features."
  * CORRECT: "Understanding these features helps you choose the right approach for your use case."
- Use second person "you" to speak directly to the reader
  * WRONG: "Developers can use this method to..."
  * CORRECT: "You can use this method to..."
- Add brief real-world context to technical steps
  * WRONG: "Set the resolution to 300 DPI."
  * CORRECT: "Set the resolution to 300 DPI, the standard for print-quality output."
- End sections with a forward-looking sentence that connects to the next section
  * WRONG: [section just stops abruptly]
  * CORRECT: "With the conversion complete, you can now explore the configuration options to fine-tune your output."
- Use occasional rhetorical questions to keep the reader engaged
  * "Why does this matter? Because..."
  * "What happens if the file path is wrong? The SDK throws a..."
- Break up long technical paragraphs - no paragraph should exceed 4 sentences
- Use parallel structure in lists and steps for easy scanning

**PARAGRAPH QUALITY RULES:**
- Every paragraph must have a clear topic sentence
- Every paragraph must have 2-4 sentences - never 1, never more than 5
- No two consecutive paragraphs should start with the same word
- The last sentence of each paragraph should either summarize or lead into the next idea

**BEFORE FINALIZING - SELF-REVIEW CHECKLIST:**
Read the entire blog and verify:
- Does every section open with a sentence that gives context or value to the reader?
- Are sentences varied in length - not all short, not all long?
- Is "you" used throughout to speak directly to the developer?
- Are there concrete examples rather than vague descriptions?
- Does each paragraph have exactly 2-4 sentences?
- Are there natural transitions between paragraphs and sections?
- Have filler words been removed?
- Do strong verbs replace weak passive constructions?
- Does every section end with a connecting or summarizing sentence?

If any answer is NO - rewrite those sections before outputting.

===============================================================================
END OF PROMPT
===============================================================================
"""


def get_code_snippet_prompt(
    topic: str,
    primary_keyword: str,
    platform: str,
    context: str = "",
    outline: List[str] = [],
    is_cloud: bool = False,
) -> str:
    """
    Scoped prompt for generating the ONE complete, working code example that
    the rest of the post (Steps, Setup, Walkthrough, Complete Code Example)
    is built around. Asks for code only - no prose, headings, or frontmatter -
    so the response is trivial to parse and swap for a non-LLM source later.
    """
    data = {}
    for line in context.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    product_name = data.get("ProductName", "")
    outline_items = [str(item).strip() for item in (outline or []) if str(item).strip()]
    outline_block = (
        "Specific functionality to demonstrate (from the approved outline):\n"
        + "\n".join(f"- {item}" for item in outline_items)
        if outline_items
        else ""
    )
    sdk_term = "library/API" if is_cloud else "SDK"

    return f"""
You are an expert {platform} developer. Write ONE complete, working code example
in {platform} that accomplishes this task: "{topic}"

Product/{sdk_term}: {product_name}
Primary keyword/operation: {primary_keyword}
{outline_block}

REQUIREMENTS:
- Syntactically correct and executable {platform} code
- Complete with all necessary imports/using statements at the top
- Full initialization, implementation logic, and resource cleanup
- NO placeholder comments such as "// rest of code" or "// ..."
- NO license initialization code (License class, SetLicense, ApplyLicense)
- Use realistic but generic file paths (e.g. input.pdf, output.docx)
- Do NOT include markdown prose, headings, or explanation - CODE ONLY

RESPONSE FORMAT (STRICT):
Respond with a SINGLE fenced code block and nothing else - no text before or
after it:

```{platform}
// your complete code here
```
"""




def build_outline_prompt(title: str, keywords: list[str]) -> str:
    keyword_list = ", ".join(keywords)

    return f"""
        You are an expert technical SEO content writer.

        TASK:
        Create a **comprehensive, SEO-optimized blog post outline** for the topic:

        Title: **{title}**

        Popular Keywords: {keyword_list}

        STRICT REQUIREMENTS:
        - Generate EXACTLY 4-6 main headings (H2 level)
        - Each main heading MUST be a complete, actionable section title
        - Include 2-3 subheadings (H3 level) under each main heading
        - Headings MUST include the popular keywords naturally
        - Outline must be detailed, hierarchical, and structured
        - Follow proper markdown heading structure
        - Be concise but comprehensive
        - NO introductory text, NO explanations, NO meta-commentary
        - NO content outside the outline structure

        OUTPUT FORMAT:
        Return ONLY a well-formatted markdown outline with exactly 6 H2 sections.

        ENFORCEMENT:
        - STRICTLY 5-7 main H2 headings - no more, no less
        - Each H2 must be a substantial section that can contain multiple paragraphs
        - NO additional text before or after the outline
        - Start immediately with H1 title
        - End after the last H3 subheading

        EXAMPLE STRUCTURE:
        # Main Title

        ## First Main Heading
        ### First Subheading
        ### Second Subheading

        ## Second Main Heading
        ### First Subheading
        ### Second Subheading

        [Continue with 3-5 more main headings...]

        Now create the outline for: **{title}**
        """

def keyword_filter_prompt(TOPIC, PRODUCT_NAME, KEYWORDS, platform) -> str:
  
    return f"""
    You are an expert in keyword filtering and refinement.
    
    **HARD RULE — READ THIS FIRST:**
    Your final output MUST contain EXACTLY 3 or 4 keywords total (primary + secondary + long_tail combined).
    Before returning, count your keywords. If the count is less than 3, generate more. If more than 4, trim.
    This rule overrides everything else. There are NO exceptions.

    I have a product called {PRODUCT_NAME}, topic: {TOPIC}, platform: {platform}
    and a list of candidate keywords: {KEYWORDS}

    **STEP-BY-STEP INSTRUCTIONS — FOLLOW IN ORDER:**

    STEP 1 — FILTER:
       - A keyword is relevant ONLY if it relates to both the TOPIC "{TOPIC}" and the product "{PRODUCT_NAME}"
       - If a keyword mentions a completely different product, file format, or technology
         that has nothing to do with "{TOPIC}", DISCARD it entirely
       - A keyword is relevant if it relates to the TOPIC or FILE FORMAT the product handles,
         even if it does not explicitly mention the product name or platform
       - GOOD: relates to "{TOPIC}" even without mentioning product name or platform
       - BAD: mentions unrelated formats, products, or technologies not related to "{TOPIC}"
       - If platform is NOT 'cloud': EXCLUDE keywords where the PRIMARY intent is a cloud/REST service
         (e.g. "Edit PPTX using .NET REST API" where REST API IS the product being advertised)
         Do NOT discard a keyword merely because it contains the word "API" or "library" in passing
         Still EXCLUDE keywords containing: "cURL", "online", "web-based", "cloud", "SaaS", "endpoint"
       - If platform IS 'cloud': INCLUDE keywords related to REST APIs, cloud services, online tools
       - DISCARD any keyword that is a generic FAQ or consumer question with no developer implementation intent
         Examples to DISCARD: "What is the 5 5 5 rule in PowerPoint?", "Why can't I edit my PPTX?",
         "How many slides should a presentation have?", "What makes a good presentation?"
         Examples to KEEP: "How do I edit an existing PPT file programmatically?",
         "Can a PPTX file be edited with code?", "How to update PPTX slides in .NET?"

    STEP 2 — CLEAN:
       - Strip trailing suffixes like "- Blog", "- Tutorial", "- Easy Guide", "- Step by Step", "- Free"
       - Strip URL fragments (e.g. "https://kb. ..." or any partial/full URL at end of keyword)
       - Max ~60 characters per keyword; trim to core intent if longer
       - Remove duplicate or near-duplicate keywords
       - **REMOVE PRODUCT NAME: Do NOT include "{PRODUCT_NAME}" or any part of it in any keyword**
         * Strip product name if it appears anywhere in the keyword
         * BAD:  "Convert AI to PDF using Aspose.PDF in Python"
         * GOOD: "Convert AI to PDF in Python"
         * BAD:  "Aspose.3D Java 3MF to STL conversion"
         * GOOD: "3MF to STL conversion in Java"
       - **REMOVE VERSION NUMBERS:**
         * Strip any version numbers, release numbers, or version strings from keywords
         * Patterns to remove: "25.2", "v1.0", "2024.1", "23.11", or any "digits.digits" pattern
         * BAD: "Email .NET 25.2: Filter & Paginate MBOX Messages"
         * GOOD: "Filter and Paginate MBOX Messages in .NET"
         * After stripping version, also clean up any leftover colons, dashes, or double spaces
       - **PLATFORM TERM ENFORCEMENT:**
         * Only the platform term "{platform}" is allowed in keywords
         * If platform is ".NET": treat "C#" as an alias for .NET — a keyword containing "C#" alongside
           valid topic content may be kept, but normalize by removing "C#" and retaining ".NET"
           (e.g. "Edit PPTX in C# .NET" → "Edit PPTX in .NET")
         * REMOVE or DISCARD any keyword containing other unrelated platform/language terms
         * Forbidden terms (when not the current platform): Java, Node.js, Ruby, PHP, Go, Swift, Kotlin, VB.NET
         * If platform=".NET": also treat standalone "C#" without ".NET" as forbidden — strip or normalize
         * BAD (platform=python): "LaTeX to JPEG conversion .NET"
         * BAD (platform=python): "LaTeX to JPEG Java library"
         * GOOD (platform=python): "LaTeX to JPEG conversion in Python"
         * GOOD (platform=python): "LaTeX to JPEG Python library"
         * GOOD (platform=.NET): "Edit PPTX in C# .NET" → normalize to "Edit PPTX in .NET"
       - **TOPIC STRICT ENFORCEMENT:**
         * Every keyword must strictly reflect the exact file formats and intent mentioned in TOPIC="{TOPIC}"
         * Extract the exact format names from "{TOPIC}" — only those formats are allowed in keywords
         * If a keyword introduces file formats, extensions, or terms NOT present in "{TOPIC}", remove them
         * BAD (topic="Export LaTeX to JPG"): "Convert LaTeX to PNG JPG image" — PNG is not in topic, strip it
         * GOOD (topic="Export LaTeX to JPG"): "Convert LaTeX to JPG in Python"
         * BAD (topic="PDF to Word Conversion"): "PDF to Word or DOCX conversion" — DOCX not in topic, strip it
         * GOOD (topic="PDF to Word Conversion"): "PDF to Word conversion in Python"
         * Strip any extra format names, synonyms, or alternatives not explicitly in "{TOPIC}"

    STEP 3 — COUNT AND TOP UP:
       - Count how many keywords you have after STEP 1 and STEP 2
       - TARGET is exactly 4 keywords — always try to reach 4 before settling for 3
       - If count is 0, 1, 2, or 3: generate additional keywords until you have exactly 4
       - If count is 0 (all keywords were irrelevant or list was empty):
         * Ignore candidate list entirely
         * Generate 4 fresh keywords using TOPIC="{TOPIC}", PLATFORM="{platform}"
         * Use the topic as the primary source of intent
         * DO NOT include "{PRODUCT_NAME}" in any generated keyword
       - Generated keywords must be realistic search queries a developer would type
       - No cloud/API terms for on-premises platforms; include them for cloud
       - Place generated keywords in secondary or long_tail categories
       - If count exceeds 4: keep only the 4 most relevant, discard the rest
       - **GENERATION PLATFORM RULES:**
         * ONLY use "{platform}" as the technology term in generated keywords
         * NEVER generate keywords containing: Java, C#, Node.js, Ruby, PHP, Go, Swift, Kotlin
         * If platform is ".NET", you may use ".NET" only — do not generate "C#" standalone
         * BAD (platform=python): "convert LaTeX to JPEG in .NET"
         * GOOD (platform=python): "convert LaTeX to JPEG in Python"
       - **GENERATION TOPIC RULES:**
         * ONLY use file formats and terms present in "{TOPIC}" in generated keywords
         * NEVER introduce new formats, synonyms, or alternatives not in "{TOPIC}"
         * BAD (topic="Export LaTeX to JPG"): generate "convert LaTeX to PNG in Python"
         * GOOD (topic="Export LaTeX to JPG"): generate "export LaTeX to JPG in Python"

    STEP 4 — FIX CHARACTERS:
       - \u2013, \u2014 (en/em dash) → - (hyphen)
       - \u201c, \u201d, \u2018, \u2019 (curly quotes) → straight quotes
       - \u2026 (ellipsis) → ...
       - Replace & with "and"
       - Remove any other Unicode that could break Hugo YAML frontmatter

    STEP 5 — VERIFY AND RETURN:
       - Count total keywords one final time — must be between 3 and 4, fix if not
       - Confirm no keyword contains "{PRODUCT_NAME}" — if any does, strip it out
       - Confirm no keyword contains any platform term other than "{platform}"
         * Scan every keyword for: Java, .NET (if platform != .NET), C#, Node.js, Ruby, PHP, Go, Swift, Kotlin
         * If found, remove the term or discard and replace the keyword
       - Confirm no keyword contains file formats or terms not present in "{TOPIC}"
         * Re-read "{TOPIC}" and extract the exact format names
         * Scan every keyword — if it contains a format outside of "{TOPIC}", strip it or fix the keyword
       - Confirm no keyword contains version numbers
         * Scan every keyword for patterns like "25.2", "v1.0", "2024.1", any "digits.digits" pattern
         * If found, strip the version number and clean up leftover punctuation
       - Confirm no keyword is a generic FAQ/consumer question — if found, discard and replace with
         a developer-intent keyword generated from TOPIC and PLATFORM
       - Return ONLY valid JSON with double quotes, no extra text

    **CRITICAL OUTPUT FORMAT:**
    - Return ONLY a JSON object — no markdown, no explanation, no preamble
    - Use DOUBLE QUOTES for all strings
    - Must be parseable by json.loads()
    - CORRECT:   {{"primary": ["keyword1", "keyword2"], "secondary": ["keyword3"], "long_tail": ["keyword4"]}}
    - INCORRECT: {{'primary': ['keyword1']}}

    **EXAMPLES:**

    Example 1 — Strip version number from keyword:
    Input: topic="Filter and Paginate MBOX Emails", platform=".NET",
           keywords={{"primary": ["Filter and Paginate MBOX Emails", "Email .NET 25.2: Filter & Paginate MBOX Messages"],
                      "secondary": ["Filter MBOX messages with .NET library"],
                      "long_tail": ["MBOX email pagination in .NET"]}}
    Step 2: strip version "25.2" and clean up → "Filter and Paginate MBOX Messages in .NET"
    Step 2: replace "&" with "and" → "Filter and Paginate MBOX Messages in .NET"
    Step 3: count is 4 — no top up needed
    Output: {{"primary": ["Filter and Paginate MBOX Emails", "Filter and Paginate MBOX Messages in .NET"],
              "secondary": ["Filter MBOX messages with .NET library"],
              "long_tail": ["MBOX email pagination in .NET"]}}

    Example 2 — Keyword introduces format not in topic, strip it:
    Input: topic="Export LaTeX to JPG", platform="python",
           keywords={{"primary": ["Convert LaTeX to PNG JPG image"], "secondary": [], "long_tail": []}}
    Step 2: "PNG" is not in topic "Export LaTeX to JPG" — strip PNG, keep JPG only
    Step 3: only 1 keyword remains — generate 3 more using topic and platform
    Output: {{"primary": ["Export LaTeX to JPG in Python", "convert LaTeX to JPG in Python"],
              "secondary": ["LaTeX to JPG conversion Python"],
              "long_tail": ["how to export LaTeX to JPG programmatically in Python"]}}

    Example 3 — All keywords irrelevant to topic, generate from scratch:
    Input: topic="AI to PDF Conversion", product="Aspose.PDF", platform="python",
           keywords={{"primary": [], "secondary": ["Convert PSD to PNG with Aspose.PSD in Python",
                      "Load and edit PSD file using Aspose.PSD Python"],
                      "long_tail": ["Extract PSD layers using Aspose.PSD in Python"]}}
    Step 1: ALL keywords discarded — PSD/PNG has nothing to do with "AI to PDF Conversion"
    Step 3: 0 keywords remain — generate 4 fresh ones from topic, no product name
    Output: {{"primary": ["AI to PDF conversion in Python", "convert AI file to PDF in Python"],
              "secondary": ["AI to PDF Python library"],
              "long_tail": ["how to convert AI file to PDF using Python"]}}

    Example 4 — Strip product name and wrong platform terms:
    Input: topic="LaTeX to JPEG Conversion", product="Aspose", platform="python",
           keywords={{"primary": ["LaTeX to JPEG conversion API .NET", "LaTeX to JPEG Java library"],
                      "secondary": ["convert LaTeX to JPEG in Python"],
                      "long_tail": ["how to convert LaTeX to JPEG file"]}}
    Step 2: discard ".NET" and "Java" keywords — wrong platform
    Step 3: 2 keywords remain — generate 2 more using platform=python
    Output: {{"primary": ["convert LaTeX to JPEG in Python", "LaTeX to JPEG conversion in Python"],
              "secondary": ["LaTeX to JPEG Python library"],
              "long_tail": ["how to convert LaTeX to JPEG using Python"]}}

    Example 5 — Strip product name from existing keywords:
    Input: topic="3MF to STL Conversion", product="Aspose.3D", platform="java",
           keywords={{"primary": ["Convert 3MF to STL using Aspose.3D in Java", "Aspose.3D 3MF to STL Java"],
                      "secondary": ["How to convert 3MF files to STL"],
                      "long_tail": ["How do I convert a 3MF file to STL?"]}}
    Step 2: strip product name → ["Convert 3MF to STL in Java", "3MF to STL in Java"]
    Step 3: count is 4 — no top up needed
    Output: {{"primary": ["Convert 3MF to STL in Java", "3MF to STL in Java"],
              "secondary": ["How to convert 3MF files to STL"],
              "long_tail": ["How do I convert a 3MF file to STL?"]}}

    Example 6 — 2 keywords survive filtering, top up with correct platform:
    Input: topic="PDF to Word Conversion", product="Aspose.Words", platform="java",
           keywords={{"primary": ["Convert PDF to Word in Java", "PDF to Word Java"],
                      "secondary": [], "long_tail": []}}
    Step 3: only 2 keywords — generate 2 more using platform=java, no product name
    Output: {{"primary": ["Convert PDF to Word in Java", "PDF to Word Java"],
              "secondary": ["PDF to Word Java library"],
              "long_tail": ["how to convert PDF to Word document in Java"]}}

    Example 7 — Cloud platform, keep REST/online keywords:
    Input: topic="PDF to Word Conversion", product="Aspose.PDF Cloud", platform="cloud",
           keywords={{"primary": ["Convert PDF REST API", "PDF to Word online"],
                      "secondary": ["Aspose.PDF Cloud Java library"], "long_tail": []}}
    Step 1: exclude "Aspose.PDF Cloud Java library" (contains product name and wrong platform)
    Step 3: 2 keywords remain — generate 2 more
    Output: {{"primary": ["Convert PDF REST API", "PDF to Word online"],
              "secondary": ["PDF conversion REST API"],
              "long_tail": ["how to convert PDF to Word using REST API"]}}

    Example 8 — Too many keywords, trim to 4:
    Input: 6 keywords survive filtering
    Step 3: trim to 4 most relevant
    Output: {{"primary": ["keyword1", "keyword2"], "secondary": ["keyword3"], "long_tail": ["keyword4"]}}

    Example 9 — Dirty keywords, clean then top up:
    Input: topic="3MF to STL Conversion", platform="java",
           keywords={{"primary": ["Convert 3MF to STL in Java - Easy Conversion Guide - Blog",
                                  "3MF to STL Java"], "secondary": [], "long_tail": []}}
    Step 2: strip suffixes → ["Convert 3MF to STL in Java", "3MF to STL Java"]
    Step 3: only 2 — generate 2 more using platform=java, no product name
    Output: {{"primary": ["Convert 3MF to STL in Java", "3MF to STL Java"],
              "secondary": ["3MF to STL Java library"],
              "long_tail": ["how to export 3MF as STL file in Java"]}}

    Example 10 — Mixed valid, REST API, FAQ, and C# keywords for .NET platform:
    Input: topic="Update PPTX File", product="Aspose.Slides", platform=".NET",
           keywords={{"primary": ["Update PPTX File in .NET",
                                  "Edit PowerPoint Presentations in C# using .NET REST API",
                                  "Edit PPTX Metadata in C# using .NET REST API https://kb. ...",
                                  "Groupdocs Editor with PPTX - Free Support Forum"],
                      "secondary": [],
                      "long_tail": ["How do I edit an already existing PPT?",
                                    "What is the 5 5 5 rule in PowerPoint?",
                                    "Can a PPTX file be edited?",
                                    "Why can't I edit my PPTX?"]}}
    Step 1: discard "Groupdocs Editor..." (wrong product), discard "What is the 5 5 5 rule..." (generic FAQ),
            discard "Why can't I edit my PPTX?" (consumer FAQ, no developer intent),
            discard "Edit PowerPoint in C# using .NET REST API" (primary intent is REST API service),
            keep "Update PPTX File in .NET", keep "How do I edit an already existing PPT?" (borderline developer),
            keep "Can a PPTX file be edited?" (borderline)
    Step 2: strip URL from "Edit PPTX Metadata in C# using .NET REST API https://kb. ..." → discard (REST API product)
            normalize "C#" → ".NET" where applicable
    Step 3: 3 keywords remain — generate 1 more using platform=.NET
    Output: {{"primary": ["Update PPTX File in .NET", "Edit PPTX in .NET"],
              "secondary": ["How to update an existing PPTX file in .NET"],
              "long_tail": ["how to edit PowerPoint slides programmatically in .NET"]}}

    Return ONLY the JSON object. No text before or after it.
"""
