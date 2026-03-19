import json
from datetime import datetime
import sys, os
from .helpers import slugify
from typing import List, Dict
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import format_related_posts
from config import settings

def get_blog_writer_prompt(
    title: str,
    seo_topic: str,
    keywords: List[str],
    outline: List[str],
    related_links: List[Dict[str, str]],
    context: str = "",
    author: str = "",
    platform: str = "",
    target_persona: str = "",
    angle: str = "",
    isCloud: bool =False
    
) -> str:
    """
    Creates a full SEO blog-writing prompt with frontmatter, outline, and
    a final 'Read More' section using the provided related_links.
    """
    url = slugify(title)
    # Parse context fields
    data = {}
    for line in context.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    category = data.get("Category", "General")
    # Outline formatting
    formatted_outline = "\n".join([f"   {item}" for item in outline])

    # Properly formatted Read More links (SAFE)
    formatted_related = format_related_posts(related_links)

    # Date
    current_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    primary_keyword = keywords[0]
    secondary_keywords = keywords[0]
 
    # FULL PROMPT.  /{data.get("urlPrefix")}/{url}/
    return f"""
You are an expert technical blog writer. Write a detailed, SEO-optimized blog post about "{title}" using keywords: {keywords}, target persona: {target_persona}, angle: {angle}

{context}

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

**THERE MUST BE NO SPACE BETWEEN ] AND ( — EVER.**

-------------------------------------------------------------------------------
COMPLETE LIST OF MALFORMED PATTERNS — NEVER PRODUCE ANY OF THESE
-------------------------------------------------------------------------------

Every pattern below is WRONG. Study each one so you never produce it:

WRONG: [Aspose.3D for Java (https://example.com/)
  WHY: Missing closing bracket ] before the URL's opening parenthesis
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java] (https://example.com/)
  WHY: Space between ] and ( — no space is ever allowed here
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: Aspose.3D for Java](https://example.com/)
  WHY: Missing opening bracket [ before the link text
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: Aspose.3D for Java] (https://example.com/)
  WHY: Missing opening bracket [ and space before (
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java(https://example.com/)
  WHY: Missing closing bracket ] — ( must be preceded by ]
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
  WHY: Empty link text — always provide meaningful text
  FIX: [Aspose.3D for Java](https://example.com/)

WRONG: [Aspose.3D for Java]()
  WHY: Empty URL — always provide the full URL
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
MANDATORY MENTAL CHECKLIST — RUN THIS BEFORE WRITING EVERY SINGLE LINK
-------------------------------------------------------------------------------

Before you type any hyperlink, ask yourself these five questions:

  1. Did I write the opening bracket [ first?
  2. Is all the link text between [ and ]?
  3. Does ] come immediately before ( with NO space between them?
  4. Is the full URL between ( and )?
  5. Does the link end with a closing parenthesis )?

If the answer to ANY question is NO — do not write the link until it is fixed.

-------------------------------------------------------------------------------
SCAN BEFORE FINALIZING
-------------------------------------------------------------------------------

Before you output the complete blog post, scan the entire document for:

- Any ] at the start of a word or immediately before a URL without a preceding [
- Any product name or text followed by (https:// without a preceding [text]
- Any [text] followed by a space before (
- Any [text( without a ] between the text and the URL
- Any link missing its closing )

If you find any of these patterns — fix them before outputting.

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

===============================================================================
PART 1: FRONTMATTER REQUIREMENTS
===============================================================================

### TITLE REQUIREMENTS (CRITICAL)
**Title Field (DO NOT MODIFY):**
- Title field: MUST use title variable exactly as provided - DO NOT modify
- DO NOT change, shorten, or adjust the title
- DO NOT remove brand names or product names from title
- The title variable is pre-validated and must be used as-is

**SEO Title Field (MUST CREATE):**
- SEO Title: MUST be created using the primary keyword
- SEO Title MUST be 50-60 characters (including spaces) - STRICTLY ENFORCED
- SEO Title format should be compelling and click-worthy
- MUST include the primary keyword naturally
- Should focus on the action/benefit/solution
- NO brand/product names in SEO Title
- Count characters carefully before finalizing

**SEO Title Examples:**
Primary Keyword: "convert pdf to png"
- "Convert PDF to PNG: Complete Step-by-Step Guide" (51 chars) - CORRECT
- "How to Convert PDF to PNG Files Easily in Minutes" (51 chars) - CORRECT
- "Convert PDF to PNG Images: Complete Developer Guide" (54 chars) - CORRECT

Primary Keyword: "excel to pdf conversion"
- "Excel to PDF Conversion: Developer's Complete Guide" (53 chars) - CORRECT
- "Excel to PDF Conversion Tutorial for Developers" (50 chars) - CORRECT

**Character Count Validation for SEO Title:**
- Count EVERY character including spaces
- Minimum: 50 characters (reject if less)
- Maximum: 60 characters (reject if more)
- Must include primary keyword naturally
- Must be grammatically correct and compelling

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
seoTitle: "{seo_topic}"
description: "[MUST BE 140-160 chars - count every character including spaces before finalizing]"
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/{url}/
author: "{author}"
summary: "[MUST BE 200-260 chars - count every character including spaces before finalizing]"
tags: {json.dumps(keywords[:3])}
categories: ["{category}"]
showtoc: true
cover:
   image: images/{url}.png
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

===============================================================================
PART 2: CONTENT STRUCTURE (MANDATORY SECTIONS)
===============================================================================

### REQUIRED SECTIONS (IN ORDER)
1. Introduction Content (NO H2 heading - direct paragraphs)
2. Prerequisites and Setup (H2 heading - ALWAYS include - combines installation and environment setup)
3. Outline Sections (Follow provided outline exactly - SKIP any "Setting Up", "Installation", or "Steps/Step-by-Step" sections as they are already covered by dedicated sections)
4. **Steps (H2 heading - ALWAYS include - MUST appear immediately before Complete Code Example with NO other heading between them)**
5. **Complete Code Example(s) (H2 heading - MANDATORY - NEVER SKIP - MUST appear immediately after Steps with NO other heading between them)**
6. **[CLOUD ONLY] [Core Action] via REST API using cURL (H2 heading - MANDATORY when isCloud = true - NEVER SKIP - heading must NOT copy the blog title keyword)**
7. Conclusion (H2 heading - ALWAYS include)
8. FAQs (H2 heading - ALWAYS include)
{'9. Read More (H2 heading - ALWAYS include last)' if formatted_related else ''}

**CRITICAL: ALL HEADINGS MUST USE TITLE CASE**
Every H2 and H3 heading MUST follow Title Case capitalization rules.
Examples:
- "Prerequisites and Setup" - CORRECT
- "Steps to Convert PDF to PNG" - CORRECT
- "Understanding File Compression" - CORRECT

**CRITICAL SECTION ORDERING RULES:**
- [Topic] - Prerequisites and Setup MUST come immediately after Introduction
- Outline sections MUST come immediately after Prerequisites and Setup
- IMPORTANT: Skip any "Setting Up [Product]", "Installation", "Configuration", or "Steps/Step-by-Step" sections from the outline
- Steps MUST come immediately after ALL Outline sections
- Complete Code Example(s) MUST come immediately after Steps
- [CLOUD ONLY] cURL Commands section MUST come immediately after Complete Code Example(s) when isCloud = true
- Conclusion MUST come after Complete Code Example(s)
- FAQs MUST come after Conclusion
- Order (non-cloud): Intro -> [Topic] - Prerequisites and Setup -> Outline -> Steps -> Complete Code -> Conclusion -> FAQs -> Read More
- Order (cloud): Intro -> [Topic] - Prerequisites and Setup -> Outline -> Steps -> Complete Code -> cURL Commands -> Conclusion -> FAQs -> Read More

**LOGICAL FLOW ENFORCEMENT FOR OUTLINE SECTIONS:**
- SKIP any sections about "Setting Up", "Installation", "Configuration", "Prerequisites"
- SKIP any sections containing "Steps" or "Step-by-Step" in the heading
- Include Understanding/Conceptual sections FIRST
- Include Implementation/Usage/Advanced sections SECOND

**GRAMMAR RULES FOR HEADINGS:**
- Product names: NEVER use articles (a/an) before product names
- CORRECT: "Prerequisites and Setup"
- WRONG: "Prerequisites and a Setup"

**HEADING CAPITALIZATION (MANDATORY - TITLE CASE):**
ALL headings (H2, H3, etc.) MUST use Title Case capitalization.

Title Case Rules:
- Capitalize: First word, last word, and all major words
- Major words: Nouns, verbs, adjectives, adverbs, pronouns
- Lowercase: Articles (a, an, the), conjunctions (and, but, or), prepositions (in, on, at, to, for, with, from)
- EXCEPTION: Always capitalize prepositions of 5+ letters (Between, Through, Without)

### 1. INTRODUCTION CONTENT (NO HEADING) - CRITICAL PRODUCT LINK REQUIREMENT

**MANDATORY STRUCTURE: EXACTLY ONE PARAGRAPH ONLY**

**CRITICAL RULES:**
- The introduction MUST be EXACTLY ONE paragraph
- NO second paragraph allowed
- NO third paragraph allowed
- After the single introductory paragraph, IMMEDIATELY start the next H2 heading ([Topic] - Prerequisites and Setup)

**SINGLE PARAGRAPH REQUIREMENTS:**
- Must be 3-5 sentences long
- First or second sentence MUST include the product page link: [BrandName.ProductName for Platform](ProductURL)
- MUST use FULL product name including platform
- MUST use ProductURL from context dictionary
- Explain what the product does and what this guide will cover
- Use correct terminology based on isCloud variable (SDK for non-cloud, library/API for cloud)

### 2. PREREQUISITES AND SETUP (MANDATORY)

**HEADING FORMAT (CRITICAL - SEO ENFORCED):**

The Prerequisites and Setup heading MUST include the primary keyword or a close semantic
variant of it. NEVER use the plain generic heading "## Prerequisites and Setup" on its own.

**HEADING FORMULA:**
## [Primary Keyword Topic] - Prerequisites and Setup

**HOW TO DERIVE THE HEADING:**
1. Take the primary keyword: {primary_keyword}
2. Extract the core action or topic (strip platform/language if the result is too long)
3. Append " - Prerequisites and Setup"

**HEADING DERIVATION EXAMPLES:**

Primary keyword: "convert HTML to Powerpoint in Java"
- Core topic: "HTML to Powerpoint Conversion"
- CORRECT: "## HTML to Powerpoint Conversion - Prerequisites and Setup"
- WRONG:   "## Prerequisites and Setup"

Primary keyword: "convert PDF to PNG in C#"
- Core topic: "PDF to PNG Conversion"
- CORRECT: "## PDF to PNG Conversion - Prerequisites and Setup"
- WRONG:   "## Prerequisites and Setup"

Primary keyword: "merge Excel files in Python"
- Core topic: "Merging Excel Files"
- CORRECT: "## Merging Excel Files - Prerequisites and Setup"
- WRONG:   "## Prerequisites and Setup"

Primary keyword: "convert 3DS file to STL in Java"
- Core topic: "3DS to STL Conversion"
- CORRECT: "## 3DS to STL Conversion - Prerequisites and Setup"
- WRONG:   "## Prerequisites and Setup"

Primary keyword: "uncompress Z file in Python"
- Core topic: "Z File Decompression"
- CORRECT: "## Z File Decompression - Prerequisites and Setup"
- WRONG:   "## Prerequisites and Setup"

**RULES:**
- The core topic part MUST use Title Case
- Keep the core topic concise - 3 to 6 words maximum
- DO NOT include the full platform/language name if the heading becomes too long
- The separator between core topic and "Prerequisites and Setup" is " - " (space hyphen space)
- This heading counts as a natural keyword occurrence for SEO

**VALIDATION:**
- Does the heading contain a keyword-rich topic before "Prerequisites and Setup"? - REQUIRED
- Is it "## [Topic] - Prerequisites and Setup" format? - REQUIRED
- Is it just "## Prerequisites and Setup" with no topic prefix? - INVALID - rewrite it

Content MUST include:
- System requirements (if applicable)
- Product installation instructions
- Environment/project setup if needed
- MUST link Download URL: "Download the latest version from [this page](download_url)"
- Package manager command (NuGet, Maven, pip, npm, etc.)
- Installation code wrapped in tags:

<!--[CODE_SNIPPET_START]-->
```language
// Installation command
```
<!--[CODE_SNIPPET_END]-->

**IMPORTANT: LICENSE HANDLING**
- DO NOT mention license setup in Prerequisites section
- DO NOT include license code in any code examples
- DO mention licensing AFTER Complete Code Example or in Conclusion

### 3. OUTLINE SECTIONS
Follow the provided outline but SKIP any setup/installation/steps sections:

{formatted_outline}

**CRITICAL: SKIP THESE TOPICS FROM OUTLINE (already covered by dedicated prompt sections):**
- Skip: "Setting Up [Product]"
- Skip: "Installing [Product]"
- Skip: "Configuring [Product]"
- Skip: "Environment Setup"
- Skip: "Prerequisites"
- Skip: ANY heading containing the word "Steps" or "Step-by-Step"

### 4. STEPS SECTION (MANDATORY)
## Steps to [Task Name Based on Title]

**PLACEMENT RULE (NON-NEGOTIABLE):**
- This section MUST appear immediately after the last Outline section
- This section MUST be immediately followed by the Complete Code Example section
- NO other heading is allowed between Steps and Complete Code Example

Format:
1. **[Step summary with class/method]**: Brief explanation
   - Mention classes/methods naturally
   - Link API references if URLs in context: "Initialize the [ClassName](api_url) class"
   - NEVER put links inside backticks
   - Optional code snippet if helpful

3-6 steps total, each actionable and technical
MUST include at least 1 Documentation or API Reference link in this section

### 5. COMPLETE CODE EXAMPLE(S) - MANDATORY (NON-NEGOTIABLE)
CRITICAL: This section is MANDATORY and MUST ALWAYS be included. NO EXCEPTIONS.

**ABSOLUTE REQUIREMENT:**
- EVERY blog post MUST have at least ONE Complete Code Example section
- This section MUST appear immediately after the Steps section
- NEVER insert any heading between Steps and Complete Code Example

**FORMAT (ALWAYS INCLUDE):**
## [Specific Task from Title] - Complete Code Example

**INTRO SENTENCE (1-2 sentences before code block):**
- NEVER use: "ready-to-run", "ready-to-use", "production-ready", "copy-paste ready"
- DO use phrases like:
  - "This example demonstrates how to..."
  - "The following code shows the implementation of..."

**YOU MUST USE THESE EXACT TAGS:**

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code
// All necessary imports at the top
// Complete initialization
// Full implementation logic
// Error handling where applicable
// Resource cleanup
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

**IMPORTANT READER DISCLAIMER (MANDATORY - INCLUDE AFTER EVERY COMPLETE CODE EXAMPLE):**

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.png`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](documentation_url) or reach out to the [support team](forums_url) for assistance.

===============================================================================
### 5a. [CLOUD ONLY] CURL COMMANDS SECTION - MANDATORY WHEN isCloud = true
===============================================================================

**CONDITION: Include this section ONLY when isCloud = {isCloud}**

**IF isCloud = true - THIS SECTION IS MANDATORY. NEVER SKIP IT.**
**IF isCloud = false - DO NOT include this section at all.**

**HEADING CONSTRUCTION RULES (CRITICAL - READ CAREFULLY):**

The cURL section heading MUST be meaningfully different from the Complete Code Example heading.

**RULE: The cURL heading MUST use ONLY the core file formats or action - NEVER the product name, library name, platform, or language.**

**Heading formula:**
## [Core Action or Source Format to Target Format] via REST API using cURL

**HEADING DERIVATION EXAMPLES:**

Blog title: "Edit PowerPoint Files Using Java Library"
- Core action: "Edit PowerPoint Files"
- Correct cURL heading: "Edit PowerPoint Files via REST API using cURL"
- Wrong: "Edit PowerPoint Files Using Java Library using cURL Commands"

Blog title: "Convert PDF to PNG in C# Using Aspose.PDF for .NET"
- Core action: "PDF to PNG Conversion"
- Correct cURL heading: "PDF to PNG Conversion via REST API using cURL"
- Wrong: "Convert PDF to PNG in C# using cURL Commands"

**FORMAT:**
## [Core Action] via REST API using cURL

**REQUIREMENTS:**
- Place this section IMMEDIATELY after the Complete Code Example section
- Provide a brief 2-3 sentence introduction
- Include all required cURL steps in logical order:
  1. Authenticate and Get Access Token
  2. Upload the Source File
  3. Execute the Conversion or Operation
  4. Download the Output File

**CODE FORMAT FOR EACH cURL STEP:**

<!--[CODE_SNIPPET_START]-->
```bash
curl -X POST "https://api.example.com/v1/endpoint" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{{"inputFile": "input.ext", "outputFormat": "target"}}'
```
<!--[CODE_SNIPPET_END]-->

**cURL SECTION CONTENT RULES:**
- Use placeholder values for credentials: YOUR_CLIENT_ID, YOUR_CLIENT_SECRET, YOUR_ACCESS_TOKEN
- Use realistic but generic API endpoint URLs
- Use the actual source and target file formats from the blog title
- Add a brief explanatory sentence before each cURL command
- NEVER use COMPLETE_CODE_SNIPPET tags in this section - use regular CODE_SNIPPET tags only
- Include a closing note pointing readers to the [official API documentation](documentation_url)

===============================================================================

### 6. CONCLUSION (MANDATORY)
## Conclusion

- 2-3 paragraphs summarizing key points
- Include at least 1 contextual link
- MUST link product page URL with FULL product name: [Product Name](url)
- MUST mention licensing in second half or end of conclusion
- License mention must include BOTH pricing and temporary license
- Natural closing, encourage next steps
- NEVER mention "free" or "online tool"

### 7. FAQS (MANDATORY)
## FAQs

Requirements:
- 3-4 questions
- 2-4 sentences per answer
- Include contextual links in answers
- Use product page URL with full product name: [Product Name](url)
- NEVER mention "free" or "online"

{'### 8. READ MORE (MANDATORY)' if formatted_related else '### NO READ MORE SECTION'}
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
5. MUST link Download URL in Prerequisites/Installation section
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

**For Regular Code Snippets (Prerequisites, Steps, Outline, cURL Commands):**
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
- Include error handling
- No placeholder comments like "// ... rest of code"
- NO license initialization code (License class, SetLicense, ApplyLicense)

===============================================================================
PART 6: WRITING GUIDELINES
===============================================================================

### WORD COUNT TARGET
Introduction + Prerequisites + Outline sections + Conclusion = {settings.NUMBER_OF_BLOG_WORDS} words

### PRIMARY KEYWORD USAGE (CRITICAL - SEO REQUIREMENT)
The PRIMARY keyword is the first keyword in the list: {primary_keyword}
The SECONDARY keywords are all remaining keywords in the list: {secondary_keywords}

**MANDATORY PRIMARY KEYWORD PLACEMENT (STRICTLY ENFORCED):**

The primary keyword MUST appear AT LEAST 3-5 times across the blog body content, EXCLUDING frontmatter fields. Occurrences must be distributed across specific sections:

| # | Location | Requirement |
|---|----------|-------------|
| 1 | Introduction paragraph | Primary keyword MUST appear in the first paragraph |
| 2 | Middle of the blog body | Primary keyword MUST appear at least once within Outline or Steps sections |
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
- "Production-ready" / "Ready-to-run" / "Copy-paste ready"
- "Enterprise-ready" / "Battle-tested"
- "In conclusion, it's clear that"

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
- ALL headings (H2, H3) use Title Case capitalization
- No duplicate Steps/Step-by-Step headings from outline
- Steps section appears immediately after the last Outline section
- Complete Code Example appears immediately after Steps with NO heading between them
- [CLOUD ONLY] cURL Commands section is present when isCloud = true
- PRIMARY KEYWORD - Occurrence 1: present in the Introduction paragraph?
- PRIMARY KEYWORD - Occurrence 2: present in the Outline or Steps sections?
- PRIMARY KEYWORD - Occurrence 3: present in the Conclusion section?
- PRIMARY KEYWORD - Occurrence 4: present in at least one FAQ question or answer?
- PRIMARY KEYWORD - Total body occurrences (excluding frontmatter): at least 3, ideally 4-5?
- FINAL LINK SCAN: Have you checked every single link follows [text](url) with no space between ] and (?
- PREREQUISITES HEADING: Does the heading follow "## [Topic] - Prerequisites and Setup" format with a keyword-rich topic prefix?

===============================================================================
END OF PROMPT
===============================================================================
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
