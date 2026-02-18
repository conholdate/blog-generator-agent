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

═══════════════════════════════════════════════════════════════════════════════
🚨 CRITICAL REQUIREMENT - PRODUCT URL LINKING (READ THIS FIRST) 🚨
═══════════════════════════════════════════════════════════════════════════════

**ABSOLUTE MANDATORY REQUIREMENT:**

THE FIRST PARAGRAPH OF YOUR BLOG POST **MUST** CONTAIN A LINK TO THE PRODUCT PAGE.

**Format:** [Full Product Name with Platform](ProductURL from context)

**Example:** [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)

**Where to get the URL:** context["ProductURL"] or context.get("ProductURL")

**Validation:**
❌ If the product link is NOT in the first paragraph → OUTPUT IS INVALID
❌ If the product name is not fully qualified with platform → OUTPUT IS INVALID  
❌ If using generic text like "the SDK" or "this library" instead of product name → OUTPUT IS INVALID

**Correct First Paragraph Examples:**

✅ "[Aspose.PDF for .NET](ProductURL) is a powerful SDK that enables developers to work with PDF documents programmatically. This guide demonstrates how to convert PDF files to PNG format using C#."

✅ "Document conversion is essential in modern applications. [GroupDocs.Conversion for Java](ProductURL) provides comprehensive APIs for converting between various file formats with ease."

✅ "Working with compressed archives programmatically requires a robust solution. [Aspose.ZIP for Python via .NET](ProductURL) offers extensive features for creating and extracting ZIP files in Python applications."

**Wrong Examples (DO NOT DO THIS):**

❌ "Converting PDF to PNG is a common task. Many developers need this functionality. [Aspose.PDF for .NET](ProductURL) provides..." ← LINK IN SECOND PARAGRAPH, NOT FIRST

❌ "Aspose.PDF for .NET is a powerful SDK..." ← NO LINK AT ALL

❌ "[This SDK](ProductURL) provides powerful features..." ← NOT USING PRODUCT NAME

❌ "[Aspose.PDF](ProductURL) offers document processing..." ← MISSING PLATFORM

**THIS IS NON-NEGOTIABLE. THE PRODUCT LINK MUST BE IN THE FIRST PARAGRAPH.**

═══════════════════════════════════════════════════════════════════════════════
CRITICAL: CONTENT BOUNDARIES (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════════════════════════
START: Blog MUST begin with frontmatter (---) - NO text before
END: Blog MUST end after {'Read More section' if formatted_related else 'FAQs section'} - NO text after
PROHIBITED: No introductory text, concluding remarks, author notes, meta-commentary outside structure

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RESTRICTIONS
═══════════════════════════════════════════════════════════════════════════════
NEVER mention or imply:
❌ "free SDK" or "free library" or "free API"
❌ "online tool" or "online app" or "web-based application"
❌ "no installation required" or "browser-based"
❌ Any suggestion that this is a web service or online platform

ALWAYS clarify:
✅ This is a desktop/server SDK that requires installation
✅ This is a library/API for programmatic integration
✅ Code runs on your local machine or server
✅ Requires proper licensing for production use

═══════════════════════════════════════════════════════════════════════════════
PART 1: FRONTMATTER REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

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
✅ "Convert PDF to PNG: Complete Step-by-Step Guide" (51 chars)
✅ "How to Convert PDF to PNG Files Easily in Minutes" (51 chars)
✅ "PDF to PNG Conversion Made Simple and Fast" (43 chars) - TOO SHORT
✅ "Master PDF to PNG Conversion: Quick Tutorial" (47 chars) - TOO SHORT
✅ "Convert PDF to PNG Images: Complete Developer Guide" (54 chars)

Primary Keyword: "excel to pdf conversion"
✅ "Excel to PDF Conversion: Developer's Complete Guide" (53 chars)
✅ "How to Convert Excel to PDF Programmatically" (47 chars) - TOO SHORT
✅ "Excel to PDF Conversion Tutorial for Developers" (50 chars)

**Character Count Validation for SEO Title:**
- Count EVERY character including spaces
- Minimum: 50 characters (reject if less)
- Maximum: 60 characters (reject if more)
- Must include primary keyword naturally
- Must be grammatically correct and compelling

### META DESCRIPTION - CHARACTER LIMITS (STRICTLY ENFORCED)
════════════════════════════════════════════════════════════════
🚨 META DESCRIPTION LENGTH: EXACTLY 140-160 CHARACTERS 🚨
════════════════════════════════════════════════════════════════

**MANDATORY VALIDATION PROCESS (FOLLOW THIS EXACTLY):**

STEP 1: Write your meta description draft
STEP 2: Count EVERY character including spaces, punctuation, and letters
STEP 3: If count is below 140 → ADD more descriptive words until 140-160
STEP 4: If count is above 160 → REMOVE words until 140-160
STEP 5: Count again to verify before finalizing
STEP 6: Only include if count is between 140-160 (inclusive)

**CHARACTER COUNTING RULES:**
- Count spaces as 1 character each
- Count punctuation (.,!?-) as 1 character each
- Count every letter and number
- Include ALL characters - nothing is excluded

**VALIDATION EXAMPLES:**

TOO SHORT (❌ INVALID - must rewrite):
"Learn how to convert PDF to PNG using Aspose.PDF for .NET." (59 chars - WAY too short)
"Convert PDF files to PNG images programmatically using C#." (58 chars - WAY too short)

TOO LONG (❌ INVALID - must trim):
"Learn how to convert PDF to PNG images programmatically using Aspose.PDF for .NET Cloud SDK with detailed code examples and step-by-step instructions for C# developers." (170 chars - too long)

CORRECT LENGTH (✅ VALID):
"Learn how to convert PDF files to PNG images in C# using Aspose.PDF for .NET. This guide covers step-by-step implementation with working code." (143 chars ✅)
"Convert PDF to PNG programmatically in C# with Aspose.PDF for .NET. Follow this step-by-step guide with complete code examples for developers." (143 chars ✅)

**SELF-CHECK BEFORE FINALIZING:**
Ask yourself:
1. Have I counted every single character including spaces?
2. Is my count between 140 and 160?
3. If not, have I rewritten until it is?

**OUTPUT IS INVALID IF:**
❌ Meta description is less than 140 characters
❌ Meta description is more than 160 characters

**THIS IS NON-NEGOTIABLE. META DESCRIPTION MUST BE 140-160 CHARACTERS.**

### SUMMARY - CHARACTER LIMITS (STRICTLY ENFORCED)
════════════════════════════════════════════════════════════════
🚨 SUMMARY LENGTH: EXACTLY 200-260 CHARACTERS 🚨
════════════════════════════════════════════════════════════════

**MANDATORY VALIDATION PROCESS (FOLLOW THIS EXACTLY):**

STEP 1: Write your summary draft
STEP 2: Count EVERY character including spaces, punctuation, and letters
STEP 3: If count is below 200 → ADD more descriptive words until 200-260
STEP 4: If count is above 260 → REMOVE words until 200-260
STEP 5: Count again to verify before finalizing
STEP 6: Only include if count is between 200-260 (inclusive)

**VALIDATION EXAMPLES:**

TOO SHORT (❌ INVALID - must rewrite):
"Learn how to convert PDF to PNG using Aspose.PDF for .NET with C#." (66 chars - WAY too short)

TOO LONG (❌ INVALID - must trim):
"Learn how to convert PDF to PNG images programmatically using Aspose.PDF for .NET SDK with detailed step-by-step code examples, complete implementation guide, error handling, and best practices for C# developers working with document conversion." (246 chars - check carefully)

CORRECT LENGTH (✅ VALID):
"Learn how to convert PDF files to PNG images in C# using Aspose.PDF for .NET. This guide walks you through the entire process with working code examples, prerequisites, and step-by-step instructions to help you implement PDF to PNG conversion." (244 chars ✅)

**OUTPUT IS INVALID IF:**
❌ Summary is less than 200 characters
❌ Summary is more than 260 characters

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
  ✅ "convert-pdf-to-png-in-csharp"
  ✅ "excel-to-pdf-in-java"
  ✅ "html-to-markdown-in-python"
  ❌ "convert-pdf-png-csharp" (missing "to" and "in")
  ❌ "convert-pdf-aspose-java" (contains brand)

### MARKDOWN-SAFE CONTENT (MANDATORY)
Replace automatically throughout:
- Em dash (—) to single hyphen (-)
- En dash (–) to single hyphen (-)
- Curly double quotes (" ") to straight quotes (" ")
- Curly single quotes (' ') to straight quotes (' ')
- Ellipsis (…) to three periods (...)
- Copyright (©) to (c), Registered (®) to (R), Trademark (™) to (TM)
- Bullet (•) to hyphen (-)
- Degree symbol (°) to "degrees"
- NEVER use em dashes or en dashes anywhere in content
- NEVER use typographic quotes or smart quotes
- ALWAYS use simple ASCII punctuation

### MARKDOWN LINK VALIDATION (MANDATORY - CRITICAL)
**ABSOLUTE REQUIREMENT: All markdown links MUST use correct format [text](url)**

PROHIBITED PATTERNS (these are ERRORS that must be prevented):
❌ ]text](url) - Missing opening bracket
❌ [text(url) - Missing closing bracket before opening parenthesis  
❌ text](url) - Missing opening bracket entirely
❌ [text]url) - Missing opening parenthesis
❌ ]app](link) - Missing opening bracket (common LLM error)

CORRECT FORMAT (ALWAYS use this):
✅ [text](url) - Square brackets around text, parentheses around URL
✅ [app](link) - Properly formatted with both brackets
✅ [documentation](https://example.com) - Complete and correct

**PREVENTION RULES:**
1. ALWAYS write opening square bracket [ BEFORE link text
2. ALWAYS write closing square bracket ] AFTER link text
3. ALWAYS write opening parenthesis ( BEFORE URL
4. ALWAYS write closing parenthesis ) AFTER URL
5. NEVER start a link with ] - this is ALWAYS wrong
6. NEVER omit the opening bracket [

**VALIDATION BEFORE OUTPUT:**
Before finalizing the blog post, mentally scan for these patterns:
- Look for any ] at the start of a word followed by ](
- Look for patterns like ]word]( or ]text](
- If found, ADD the missing opening bracket [

**EXAMPLES OF AUTO-CORRECTION:**

WRONG → CORRECT:
]API Reference](https://example.com) → [API Reference](https://example.com)
]documentation](url) → [documentation](url)  
product page](link) → [product page](link)
]app](link) → [app](link)
]Aspose.PDF](url) → [Aspose.PDF](url)

**SELF-CHECK QUESTIONS:**
Before writing any link, ask:
1. Did I write the opening bracket [ first?
2. Is the link text between [ and ]?
3. Is the URL between ( and )?
4. Does it follow the exact pattern [text](url)?

If answer to ANY question is "No" - FIX IT IMMEDIATELY

YAML SAFETY:
- Quote strings containing colons
- No line breaks in values
- Escape internal quotes
- ASCII characters only

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
tags: {json.dumps(keywords)}
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

═══════════════════════════════════════════════════════════════════════════════
PART 2: CONTENT STRUCTURE (MANDATORY SECTIONS)
═══════════════════════════════════════════════════════════════════════════════

### REQUIRED SECTIONS (IN ORDER)
1. Introduction Content (NO H2 heading - direct paragraphs)
2. Prerequisites and Setup (H2 heading - ALWAYS include - combines installation and environment setup)
3. Steps (H2 heading - ALWAYS include)
4. Outline Sections (Follow provided outline exactly - SKIP any "Setting Up" or "Installation" sections as they're covered in Prerequisites)
5. **Complete Code Example(s) (H2 heading - MANDATORY - NEVER SKIP)**
6. Conclusion (H2 heading - ALWAYS include)
7. FAQs (H2 heading - ALWAYS include)
{'8. Read More (H2 heading - ALWAYS include last)' if formatted_related else ''}

**CRITICAL SECTION ORDERING RULES:**
- Prerequisites and Setup MUST come immediately after Introduction
- Steps MUST come immediately after Prerequisites and Setup
- Outline sections MUST come after Steps
- **IMPORTANT: Skip any "Setting Up [Product]" or "Installation" or "Configuration" sections from the outline - these are already covered in Prerequisites and Setup**
- **Steps section MUST appear in the document BEFORE Complete Code Example(s)**
- Complete Code Example(s) MUST come after ALL Outline sections
- Conclusion MUST come after Complete Code Example(s)
- FAQs MUST come after Conclusion
- Order: Intro → Prerequisites and Setup → Steps → Outline (excluding setup topics) → Complete Code → Conclusion → FAQs → Read More
- **INVALID: If Complete Code Example appears before Steps section**
- **INVALID: If Steps section is missing from the document**

**LOGICAL FLOW ENFORCEMENT FOR OUTLINE SECTIONS:**
The outline sections come AFTER the Steps section. Within the outline sections:

- **SKIP** any sections about "Setting Up", "Installation", "Configuration", "Prerequisites" - these are already covered
- Include Understanding/Conceptual sections FIRST
- Include Implementation/Usage/Advanced sections SECOND

**Example of CORRECT order:**
1. Introduction
2. Prerequisites and Setup (covers installation, environment setup, configuration)
3. **Steps to Uncompress Z File (MUST appear here, BEFORE Complete Code Example)**
4. Understanding Z File Compression (Outline section - conceptual)
5. Advanced Compression Options (Outline section - advanced usage)
6. **Complete Code Example (MUST appear AFTER Steps section)**
7. Conclusion
8. FAQs

**Example of WRONG order (don't do this):**
1. Introduction
2. Prerequisites and Setup
3. Steps to Uncompress Z File
4. Setting Up Aspose.ZIP (WRONG - redundant, already covered in Prerequisites and Setup)
5. Understanding Z File Compression
6. Complete Code Example
7. Conclusion

**GRAMMAR RULES FOR HEADINGS:**
- Product names: NEVER use articles (a/an) before product names
- ✅ CORRECT: "Prerequisites and Setup"
- ❌ WRONG: "Prerequisites and a Setup"

### 1. INTRODUCTION CONTENT (NO HEADING) - CRITICAL PRODUCT LINK REQUIREMENT

**MANDATORY FIRST PARAGRAPH FORMAT:**
The very first paragraph MUST include the product page link using this EXACT format:

[BrandName.ProductName for Platform](ProductURL)

**CRITICAL RULES:**
✅ Product link MUST appear in the FIRST paragraph (not second, not third - FIRST)
✅ MUST use FULL product name including platform
✅ MUST use ProductURL from context dictionary: context["ProductURL"] or context.get("ProductURL")
✅ Link must be in the FIRST or SECOND sentence of the first paragraph
✅ Use format: [Aspose.PDF for .NET](ProductURL) or [GroupDocs.Conversion for Java](ProductURL)

**ENFORCEMENT:**
- If ProductURL is not linked in the first paragraph, the output is INVALID
- If product name is not linked with full name and platform, the output is INVALID
- The product link is NON-NEGOTIABLE and MUST be in the first paragraph

**INTRODUCTION STRUCTURE (AFTER FIRST PARAGRAPH WITH PRODUCT LINK):**
- First paragraph: 2-4 sentences including the product link (MANDATORY)
- Second paragraph: 2-3 sentences explaining the topic and its value
- Optional third paragraph: 1-2 sentences with additional context or use cases
- Include at least 1 additional contextual link in subsequent paragraphs
- Total: 2-3 paragraphs with product link in FIRST paragraph
- Use correct terminology based on isCloud variable (see Part 3)
- Natural flow, explain the topic and its value
- NEVER mention "free SDK" or "online tool"
- Clarify this is a programmatic SDK/library for local/server use

### 2. PREREQUISITES AND SETUP (MANDATORY)
## Prerequisites and Setup

Content MUST include:
- System requirements (if applicable)
- **Product installation instructions**
- **Environment/project setup if needed**
- **MUST link Download URL**: "Download the latest version from [this page](download_url)"
- Package manager command (NuGet, Maven, pip, npm, etc.)
- Installation code wrapped in tags:

<!--[CODE_SNIPPET_START]-->
```language
// Installation command
```
<!--[CODE_SNIPPET_END]-->

**IMPORTANT: LICENSE HANDLING**
- **DO NOT mention license setup in Prerequisites section**
- **DO NOT include license code in any code examples**
- **DO mention licensing AFTER Complete Code Example or in Conclusion**

Keep comprehensive but well-organized (2-5 paragraphs covering installation and setup)
NEVER mention "free" or "online"

### 3. STEPS SECTION (MANDATORY)
## Steps to [Task Name Based on Title]

Format:
1. **[Step summary with class/method]**: Brief explanation
   - Mention classes/methods naturally
   - **Link API references if URLs in context**: "Initialize the [ClassName](api_url) class"
   - NEVER put links inside backticks
   - Optional code snippet if helpful

3-6 steps total, each actionable and technical
**MUST include at least 1 Documentation or API Reference link in this section**

### 4. OUTLINE SECTIONS
Follow the provided outline but SKIP any setup/installation sections:

{formatted_outline}

**CRITICAL: SKIP THESE TOPICS FROM OUTLINE (already covered in Prerequisites and Setup):**
❌ Skip: "Setting Up [Product]"
❌ Skip: "Installing [Product]"
❌ Skip: "Configuring [Product]"
❌ Skip: "Environment Setup"
❌ Skip: "Prerequisites"

**ONLY INCLUDE THESE TYPES OF OUTLINE SECTIONS:**
✅ Include: Understanding/Conceptual sections
✅ Include: Feature explanations
✅ Include: Usage/Implementation topics
✅ Include: Best practices, tips, or optimization sections

### 5. COMPLETE CODE EXAMPLE(S) - MANDATORY (NON-NEGOTIABLE)
CRITICAL: This section is MANDATORY and MUST ALWAYS be included. NO EXCEPTIONS.

**ABSOLUTE REQUIREMENT:**
- EVERY blog post MUST have at least ONE Complete Code Example section
- This is a HARD REQUIREMENT that cannot be skipped
- **This section MUST appear AFTER the Steps section in the document**
- **This section MUST appear AFTER all Outline sections**
- **NEVER place Complete Code Example before the Steps section**

**FORMAT (ALWAYS INCLUDE):**
## [Specific Task from Title] - Complete Code Example

**INTRO SENTENCE (1-2 sentences before code block):**
- NEVER use: "ready-to-run", "ready-to-use", "production-ready", "copy-paste ready"
- DO use phrases like:
  * "This example demonstrates how to..."
  * "The following code shows the implementation of..."

**⚠️ CRITICAL: YOU MUST USE THESE EXACT TAGS ⚠️**

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

### 6. CONCLUSION (MANDATORY)
## Conclusion

- 2-3 paragraphs summarizing key points
- Include at least 1 contextual link
- MUST link product page URL with FULL product name: [Product Name](url)
- **MUST mention licensing in second half or end of conclusion**
- **License mention must include BOTH pricing and temporary license**
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

═══════════════════════════════════════════════════════════════════════════════
PART 3: TERMINOLOGY RULES (CRITICAL - STRICTLY ENFORCED)
═══════════════════════════════════════════════════════════════════════════════

isCloud variable: {isCloud}

**DECISION RULE:**
- IF isCloud = true → Use "library" or "API" EVERYWHERE
- IF isCloud = false → Use "SDK" EVERYWHERE

### PROHIBITED TERMINOLOGY (NEVER USE)
❌ "Framework"
❌ "free SDK" or "free library" or "free API"
❌ "online tool" or "online app" or "web-based"
❌ "browser-based" or "no installation required"

═══════════════════════════════════════════════════════════════════════════════
PART 4: LINKING REQUIREMENTS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

### MANDATORY LINKING RULES
1. Include **MINIMUM 5-7 contextual links** from provided resources
2. MUST link product page URL EVERY TIME product name is mentioned
3. MUST link **Documentation URL** at least once
4. MUST link **API Reference URL** when mentioning any class, method, or property
5. MUST link **Download URL** in Prerequisites/Installation section
6. MUST link **License URL** at least once
7. CRITICAL: Only use links explicitly provided in context
8. NEVER construct or guess URLs
9. NEVER put links inside backticks or code literals

### PRODUCT NAME AND FILE FORMAT LINKING (CRITICAL)

**1. PRODUCT NAMES (Link to Product Page):**
Format: [Aspose.ZIP for .NET](product_page_url)

**2. FILE FORMATS (Link to FileFormat.com):**
Format: [ZIP](https://docs.fileformat.com/compression/zip/)

**3. WRONG PATTERNS TO AVOID:**
❌ [Aspose.ZIP](fileformat_url) - Product linked to file format
❌ Aspose.[ZIP](fileformat_url) - Splitting product name with file format link

═══════════════════════════════════════════════════════════════════════════════
PART 5: CODE SNIPPET REQUIREMENTS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

**For Regular Code Snippets (Prerequisites, Steps, Outline):**
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
- Using wrong tags makes output INVALID

**ALL CODE MUST BE:**
✅ Syntactically correct
✅ Executable
✅ Complete with all imports
✅ Include error handling
✅ No placeholder comments like "// ... rest of code"
❌ NO license initialization code (License class, SetLicense, ApplyLicense)

═══════════════════════════════════════════════════════════════════════════════
PART 6: WRITING GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

### WORD COUNT TARGET
Introduction + Prerequisites + Outline sections + Conclusion = {settings.NUMBER_OF_BLOG_WORDS} words

### PRIMARY KEYWORD USAGE (CRITICAL - SEO REQUIREMENT)
The PRIMARY keyword is the first keyword in the list: {primary_keyword}
The SECONDARY keywords are all remaining keywords in the list: {secondary_keywords}

**MANDATORY PRIMARY KEYWORD DENSITY:**
- PRIMARY keyword MUST appear at 1% density of total blog word count
- Formula: (Word Count / 100) = Minimum keyword occurrences
- NEVER surround primary keyword with asterisks or make it italic/bold

**SECONDARY KEYWORDS USAGE (MANDATORY):**
- MUST use ALL secondary keywords throughout the blog post
- Each secondary keyword should appear 2-4 times naturally

### HUMAN-LIKE WRITING QUALITY (CRITICAL - NON-NEGOTIABLE)

**PROHIBITED PUNCTUATION (NEVER USE):**
❌ Em dashes (—) - Use single hyphen (-) instead
❌ En dashes (–) - Use single hyphen (-) instead
❌ Curly quotes (" " ' ') - Use straight quotes (" ') only
❌ Ellipsis character (…) - Use three periods (...) instead

**AVOID AI-TYPICAL PHRASES:**
❌ "In today's digital landscape"
❌ "It's worth noting that"
❌ "Delve into" / "Dive deep into"
❌ "Seamlessly integrate"
❌ "Robust solution" / "Cutting-edge technology"
❌ "Production-ready" / "Ready-to-run" / "Copy-paste ready"
❌ "Enterprise-ready" / "Battle-tested"
❌ "In conclusion, it's clear that"

**CONTENT AUTHENTICITY CHECKS:**
Before finalizing, verify:
□ No em dashes or en dashes anywhere
□ Only straight quotes, no curly quotes
□ No overused AI phrases
□ Sentence variety
□ Active voice used predominantly
□ All markdown links properly formatted as [text](url)
□ Meta description is EXACTLY 140-160 characters (counted manually)
□ Summary is EXACTLY 200-260 characters (counted manually)

═══════════════════════════════════════════════════════════════════════════════
END OF PROMPT
═══════════════════════════════════════════════════════════════════════════════
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

def keyword_filter_prompt(PRODUCT_NAME, KEYWORDS, platform) -> str:
  
    return f"""
    You are an expert in keyword filtering and refinement.
    I have a product called {PRODUCT_NAME} and a list of candidate keywords: {KEYWORDS} and platform: {platform}.
    
    1. Only return keywords that are relevant to the exact product.
    2. Exclude any keyword that refers to other products or cloud offerings if the product is on-premises.
    3. **PLATFORM-SPECIFIC FILTERING:**
       - If platform is NOT 'cloud' (i.e., on-premises/desktop):
         * EXCLUDE all keywords mentioning: REST API, REST APIs, Web API, Cloud API, cURL, HTTP requests, API endpoints, web services, cloud storage, cloud conversion
         * EXCLUDE keywords with terms: "online", "web-based", "cloud", "SaaS", "API call", "REST", "endpoint"
         * KEEP only keywords related to: desktop applications, local libraries, SDK, on-premise tools, offline conversion
       - If platform IS 'cloud':
         * INCLUDE keywords related to REST APIs, cloud services, web APIs, online tools
    4. If any keyword is incomplete, truncated, or has trailing ellipses (e.g., "..."), complete it sensibly while keeping it relevant.
    5. Remove or replace any characters that break Hugo/Markdown rendering:
       - Replace Unicode dashes (\\u2013, \\u2014, em dash, en dash) with standard hyphens (-)
       - Replace smart quotes (\\u201c, \\u201d, \\u2018, \\u2019) with straight quotes (' or ")
       - Replace ellipsis character (\\u2026) with three periods (...)
       - Remove any other Unicode characters that could break YAML frontmatter
       - Ensure all characters are safe for Hugo YAML frontmatter rendering
    6. **MINIMUM KEYWORD REQUIREMENT:**
       - If after filtering, the total number of keywords (primary + secondary + long_tail) is less than 2:
         * Generate 2-5 additional relevant keywords based on the product name and topic
         * Add them to the appropriate category (primary for broad terms, long_tail for specific queries)
         * Ensure generated keywords match the platform type (cloud vs on-premises)
         * Generated keywords must be realistic search queries users would actually type
    7. Return the filtered and refined keywords in the **exact structure as you received** (e.g., primary, secondary, long_tail).
    
    **Character Replacement Rules:**
    - \\u2013 (en dash) → - (hyphen)
    - \\u2014 (em dash) → - (hyphen)
    - \\u201c, \\u201d (curly double quotes) → " (straight double quote)
    - \\u2018, \\u2019 (curly single quotes) → ' (straight single quote)
    - \\u2026 (ellipsis) → ... (three periods)
    - Any other problematic Unicode → Remove or replace with ASCII equivalent
    
    **CRITICAL OUTPUT FORMAT REQUIREMENT:**
    - You MUST return ONLY valid JSON format
    - Use DOUBLE QUOTES for all strings (not single quotes)
    - Do NOT return Python dict format with single quotes
    - Your response must be parseable by json.loads() without any modifications
    - Example of CORRECT format: {{"primary": ["keyword1", "keyword2"], "secondary": [], "long_tail": ["how to keyword3"]}}
    - Example of INCORRECT format: {{'primary': ['keyword1', 'keyword2']}}
    
    **EXAMPLES OF PLATFORM-SPECIFIC FILTERING:**
    
    Example 1 - On-premises platform:
    Input: platform="java", keywords=["Convert PDF using REST API", "PDF to Word Java", "Cloud PDF conversion"]
    Output: {{"primary": ["PDF to Word Java"], "secondary": [], "long_tail": []}}
    (Excluded: REST API and Cloud keywords)
    
    Example 2 - Cloud platform:
    Input: platform="cloud", keywords=["Convert PDF REST API", "PDF to Word online", "Java PDF library"]
    Output: {{"primary": ["Convert PDF REST API", "PDF to Word online"], "secondary": [], "long_tail": []}}
    (Kept: REST API and online keywords, excluded Java library as it's not cloud-related)
    
    Example 3 - Minimum keywords requirement:
    Input: After filtering, only 1 keyword remains
    Output: {{"primary": ["original keyword", "generated relevant keyword 1"], "secondary": [], "long_tail": ["generated long-tail keyword"]}}
    (Added keywords to meet minimum of 2)
    
    Return ONLY the JSON object with no additional text, explanation, or markdown formatting.
    Ensure all output keywords are Hugo/YAML-safe and will render correctly in frontmatter.
"""