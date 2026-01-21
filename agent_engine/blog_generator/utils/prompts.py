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
    angle: str = ""
    
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

### CHARACTER LIMITS (FOR OTHER FIELDS ONLY)
- Meta Description: 140-160 characters (including spaces)
- Summary: 140-160 characters (including spaces)
- Count manually before finalizing

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

YAML SAFETY:
- Quote strings containing colons
- No line breaks in values
- Escape internal quotes
- ASCII characters only

### FRONTMATTER TEMPLATE
---
title: "{title}"
seoTitle: "{title}"
description: "[140-160 chars, NO colons/special chars/line breaks]"
date: {current_date}
lastmod: {current_date}
draft: false
url: /{data.get("urlPrefix")}/{url}/
author: "{author}"
summary: "[140-160 chars, wrap in quotes if needed]"
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
3. **Steps to Uncompress Z File ← (MUST appear here, BEFORE Complete Code Example)**
4. Understanding Z File Compression ← (Outline section - conceptual)
5. Advanced Compression Options ← (Outline section - advanced usage)
6. **Complete Code Example ← (MUST appear AFTER Steps section)**
7. Conclusion
8. FAQs

**Example of WRONG order (don't do this):**
1. Introduction
2. Prerequisites and Setup
3. Steps to Uncompress Z File
4. Setting Up Aspose.ZIP ← (WRONG - redundant, already covered in Prerequisites and Setup)
5. Understanding Z File Compression
6. Complete Code Example
7. Conclusion

**Another WRONG example (missing Steps or wrong position):**
1. Introduction
2. Prerequisites and Setup
3. Understanding Z File Compression
4. Complete Code Example ← (WRONG - appears before Steps section)
5. Steps to Uncompress Z File ← (WRONG - should be before Complete Code Example)
6. Conclusion

**GRAMMAR RULES FOR HEADINGS:**
- Product names: NEVER use articles (a/an) before product names
- ✅ CORRECT: "Prerequisites and Setup"
- ❌ WRONG: "Prerequisites and a Setup"

### 1. INTRODUCTION CONTENT (NO HEADING)
- Start directly with 2-3 paragraphs after frontmatter
- NO H2 heading
- **CRITICAL: The FIRST paragraph MUST contain the product page URL**
- **MANDATORY: Link format in first paragraph**: [Full Product Name with Platform](ProductURL)
- **EXACT FORMAT REQUIRED**: [BrandName.ProductName for Platform](ProductPageURL)
- **Examples of CORRECT format**:
  * [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)
  * [GroupDocs.Conversion for Java](https://products.groupdocs.com/conversion/java/)
  * [Aspose.Slides for Python via .NET](https://products.aspose.com/slides/python-net/)
  * [Conholdate.Total for .NET](https://products.conholdate.com/total/net/)
- **Examples of WRONG format**:
  * ❌ Aspose.PDF for .NET (no link)
  * ❌ [Aspose.PDF](URL) (missing platform)
  * ❌ [the SDK](URL) (not using product name)
  * ❌ Using [Aspose.PDF for .NET](URL) in second or third paragraph (must be in FIRST paragraph)
- **The product name link MUST appear in the FIRST sentence or FIRST paragraph**
- **Use the FULL product name including platform (e.g., "for .NET", "for Java")**
- Include at least 1 additional contextual link in subsequent paragraphs
- Use correct terminology based on platform (see Part 3)
- Natural flow, explain the topic and its value
- NEVER mention "free SDK" or "online tool"
- Clarify this is a programmatic SDK/library for local/server use
- Total: 2-3 paragraphs with product link in FIRST paragraph

### 2. PREREQUISITES AND SETUP (MANDATORY)
## Prerequisites and Setup

**This section combines all installation, configuration, and environment setup requirements.**

Content MUST include:
- System requirements (if applicable)
- **Product installation instructions**
- **Environment/project setup if needed**
- **MUST link Download URL**: "Download the latest version from [this page](download_url)" or "Get it from the [releases page](download_url)"
- Package manager command (NuGet, Maven, pip, npm, etc.)
- Installation code wrapped in tags:

<!--[CODE_SNIPPET_START]-->
```language
// Installation command
```
<!--[CODE_SNIPPET_END]-->

- **Optional: Link Documentation**: "See the [installation guide](documentation_url) for more details"

**IMPORTANT: LICENSE HANDLING**
- **DO NOT mention license setup in Prerequisites section**
- **DO NOT include license code in any code examples**
- **DO mention licensing AFTER Complete Code Example or in Conclusion**
- **Format for license mention**: "For production use, you can purchase a license by visiting the [pricing page](pricing_url)" or "Get your [license](license_url) for commercial use"

Keep comprehensive but well-organized (2-5 paragraphs covering installation and setup)
NEVER mention "free" or "online"

**What to include in this section:**
✅ Installing the library/SDK
✅ Setting up the development environment
✅ Configuring project dependencies
✅ Initial configuration steps
✅ Any prerequisites needed before using the product

**What NOT to include:**
❌ License setup or license code
❌ License acquisition steps (save for later sections)

### 3. STEPS SECTION (MANDATORY)
## Steps to [Task Name Based on Title]

Format:
1. **[Step summary with class/method]**: Brief explanation
   - Mention classes/methods naturally
   - **Link API references if URLs in context**: "Initialize the [ClassName](api_url) class"
   - NEVER put links inside backticks
   - Optional code snippet if helpful
   - **Can reference documentation**: "For more details, see [documentation](doc_url)"
   
2. **[Next step]**: [Explanation]

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
❌ Skip: Any section about installation or initial configuration

**ONLY INCLUDE THESE TYPES OF OUTLINE SECTIONS:**
✅ Include: Understanding/Conceptual sections (e.g., "Understanding Z File Compression")
✅ Include: Feature explanations (e.g., "Key Features of the API")
✅ Include: Usage/Implementation topics (e.g., "Advanced Compression Options")
✅ Include: Best practices, tips, or optimization sections

**ORDERING RULES FOR REMAINING OUTLINE SECTIONS:**
The outline sections appear AFTER the Steps section. Arrange remaining sections logically:

1. **Overall document order**:
   - Introduction (no heading)
   - Prerequisites and Setup (covers ALL installation and configuration)
   - Steps to [Task Name]
   - **Then include relevant outline sections:**
     - Understanding/Conceptual sections FIRST (e.g., "Understanding Z Compression")
     - Advanced/Usage sections SECOND (e.g., "Advanced Options", "Best Practices")
   - Complete Code Example(s)
   - Conclusion
   - FAQs

2. **Correct sequence for outline sections (after skipping setup topics)**:
   ✅ After Steps: "Understanding [Concept]" → "Advanced [Feature]" → "Best Practices"
   ✅ After Steps: "Key Features Overview" → "Usage Examples" → "Optimization Tips"
   
3. **Grammar check for headings**:
   - NEVER use "a" or "an" before product names
   - ✅ "Understanding Z File Compression"
   - ✅ "Advanced Compression Options"

**Section Content Requirements:**
- Use H2/H3 headers as specified
- Include contextual links naturally
- May include code snippets with explanations
- Link classes/methods ONLY if URLs in context
- Link product name to product page URL: [Full Product Name](url)

### 5. COMPLETE CODE EXAMPLE(S) - MANDATORY (NON-NEGOTIABLE)
CRITICAL: This section is MANDATORY and MUST ALWAYS be included. NO EXCEPTIONS.

**ABSOLUTE REQUIREMENT:**
- EVERY blog post MUST have at least ONE Complete Code Example section
- This is a HARD REQUIREMENT that cannot be skipped
- Even if the outline doesn't explicitly mention it, you MUST create it
- If multiple tasks in title, create a section for EACH task that can be demonstrated with code
- **This section MUST appear AFTER the Steps section in the document**
- **This section MUST appear AFTER all Outline sections**
- **NEVER place Complete Code Example before the Steps section**

**MANDATORY IMPLEMENTATION:**
✅ MUST include full, working code that demonstrates the concept
✅ MUST be syntactically correct and compilable
✅ MUST demonstrate the main task from the title
✅ Code MUST be executable with appropriate setup
✅ MUST include all imports, initialization, and implementation
✅ MUST have error handling where applicable

**NEVER SKIP THIS SECTION:**
❌ Do NOT skip even if you think the task is "conceptual"
❌ Do NOT skip because the outline doesn't mention it
❌ Do NOT skip for any reason whatsoever
❌ Skipping this section makes the output INVALID

**MULTIPLE TASKS HANDLING:**
- Title: "Convert PDF to PNG and JPG"
  → Create BOTH sections (MANDATORY):
  ## Convert PDF to PNG - Complete Code Example
  ## Convert PDF to JPG - Complete Code Example

- Title: "Convert PDF to PNG"
  → Create 1 section (MANDATORY):
  ## Convert PDF to PNG - Complete Code Example

- Title: "Extract Text from PDF and Save to Word"
  → Create BOTH sections (MANDATORY):
  ## Extract Text from PDF - Complete Code Example
  ## Save Text to Word - Complete Code Example

**FORMAT (ALWAYS INCLUDE):**
## [Specific Task from Title] - Complete Code Example

**INTRO SENTENCE (1-2 sentences before code block):**
- Explain what the code demonstrates or shows
- NEVER use: "ready-to-run", "ready-to-use", "production-ready", "copy-paste ready"
- DO use phrases like:
  * "This example demonstrates how to..."
  * "The following code shows the implementation of..."
  * "This code illustrates the process of..."
  * "Here's an example that demonstrates..."

**CORRECT intro examples:**
✅ "This example demonstrates how to convert PDF to PNG using Aspose.PDF for .NET."
✅ "The following code shows how to implement the conversion process."
✅ "This code illustrates the basic steps for PDF to PNG conversion."

**INCORRECT intro examples:**
❌ "This ready-to-run example converts PDF to PNG."
❌ "Here's a production-ready console application that converts PDF."
❌ "This copy-paste ready code handles PDF conversion."

[Write your 1-2 sentence intro here following the CORRECT examples above]

**⚠️ CRITICAL: YOU MUST USE THESE EXACT TAGS BELOW ⚠️**
**⚠️ TAG NAME: COMPLETE_CODE_SNIPPET_START (NOT CODE_SNIPPET_START) ⚠️**
**⚠️ DO NOT FORGET THE WORD "COMPLETE" IN THE TAG ⚠️**

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code
// All necessary imports at the top
// Complete initialization
// Full implementation logic
// Error handling where applicable
// Resource cleanup
// Demonstrates the concept, no placeholders, no "// ... rest of code" comments
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

**⚠️ CRITICAL: YOU MUST USE THESE EXACT TAGS ABOVE ⚠️**
**⚠️ TAG NAME: COMPLETE_CODE_SNIPPET_END (NOT CODE_SNIPPET_END) ⚠️**
**⚠️ THE TAGS MUST INCLUDE THE WORD "COMPLETE" ⚠️**

**IMPORTANT READER DISCLAIMER (MANDATORY - INCLUDE AFTER EVERY COMPLETE CODE EXAMPLE):**

After each complete code example, you MUST include this exact disclaimer text (adapt the file paths to match the actual code):

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.png`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](documentation_url) or reach out to the [support team](forums_url) for assistance.

**Disclaimer Requirements:**
- Place this note IMMEDIATELY after the code block (after the closing tag)
- Use the blockquote format (>) for visibility
- Replace `documentation_url` and `forums_url` with actual URLs from context
- Adapt file path examples to match what's actually used in the code
- Keep the tone helpful and professional, not apologetic
- This disclaimer is MANDATORY for EVERY complete code example section

**CRITICAL TAG USAGE REMINDER (READ THIS CAREFULLY):**
- Complete Code Examples MUST use: <!--[COMPLETE_CODE_SNIPPET_START]--> and <!--[COMPLETE_CODE_SNIPPET_END]-->
- These tags are DIFFERENT from regular code snippet tags
- Regular code snippets use: <!--[CODE_SNIPPET_START]--> and <!--[CODE_SNIPPET_END]-->
- DO NOT confuse these tags - Complete Code Examples require the word "COMPLETE" in the tag name
- Using <!--[CODE_SNIPPET_START]--> for Complete Code Examples is WRONG and makes output INVALID
- YOU MUST TYPE: COMPLETE_CODE_SNIPPET_START (with the word COMPLETE)
- YOU MUST TYPE: COMPLETE_CODE_SNIPPET_END (with the word COMPLETE)

**VISUAL EXAMPLE OF THE DIFFERENCE:**

❌ WRONG - DO NOT USE THIS FOR COMPLETE CODE EXAMPLES:
<!--[CODE_SNIPPET_START]-->
```java
// This is WRONG for Complete Code Examples
```
<!--[CODE_SNIPPET_END]-->

✅ CORRECT - USE THIS FOR COMPLETE CODE EXAMPLES:
<!--[COMPLETE_CODE_SNIPPET_START]-->
```java
// This is CORRECT for Complete Code Examples
// Notice the word "COMPLETE" in the tag
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

**MEMORIZE THIS:**
- Section 5 (Complete Code Examples) = MUST use COMPLETE_CODE_SNIPPET_START
- All other sections = use CODE_SNIPPET_START (without COMPLETE)

**ENFORCEMENT:**
- Output is INVALID if this section is missing
- Output is INVALID if the disclaimer is missing after code examples
- Blog generation FAILS if Complete Code Example is not present
- This section MUST appear after outline sections and before Conclusion
- Order: Outline Sections → Complete Code Example(s) → Conclusion → FAQs → Read More

### 6. CONCLUSION (MANDATORY)
## Conclusion

- 2-3 paragraphs summarizing key points
- Include at least 1 contextual link
- MUST link product page URL with FULL product name: [Product Name](url)
- **MUST mention licensing in second half or end of conclusion**
- **License mention must include BOTH pricing and temporary license**
- **Format for license mention (use one of these patterns)**:
  * "For production use, you can purchase a license by visiting the [pricing page](pricing_url). Alternatively, you can request a [temporary license](license_url) for evaluation purposes."
  * "To use this SDK in commercial projects, obtain a [license](pricing_url). You can also get a [temporary license](license_url) for testing."
  * "Explore the [pricing options](pricing_url) for commercial use, or request a [temporary license](license_url) to evaluate the SDK."
- **Optional: Link Forums or Blogs**: "Explore more [tutorials](blogs_url)" or "Join our [community](forums_url)"
- Use correct terminology based on platform
- Natural closing, encourage next steps
- NEVER mention "free" or "online tool"

**License Mention Requirements:**
- Mention license availability AFTER discussing the main content
- Include link to pricing page using pricing_url from context
- Include link to temporary license using license_url from context
- Keep it brief and natural (1-2 sentences total)
- Don't make it overly promotional
- Examples:
  * ✅ "For production use, visit the [pricing page](pricing_url) to purchase a license. You can also request a [temporary license](license_url) for evaluation."
  * ✅ "Get a [license](pricing_url) for commercial deployment, or try it with a [temporary license](license_url) first."
  * ❌ "Get your free trial license" (don't mention free)
  * ❌ Only mentioning pricing without temporary license option

### 7. FAQs (MANDATORY)
## FAQs

**Q: [Question]**  
A: [Detailed answer with contextual link and product page URL]

**Q: [Question]**  
A: [Answer]

**Q: [Question]**  
A: [Answer]

**Q: [Optional fourth question]**  
A: [Optional answer]

Requirements:
- 3-4 questions
- 2-4 sentences per answer
- Include contextual links in answers
- Use product page URL with full product name: [Product Name](url)
- **LICENSE QUESTION PLACEMENT**: 
  * If including a license question, place it as the 2nd, 3rd, or 4th question (NOT first)
  * License answer should include BOTH pricing page and temporary license links
  * Format: "You can purchase a license by visiting the [pricing page](pricing_url) for commercial use. For evaluation, you can request a [temporary license](license_url)."
- **Suggested FAQ topics** (in order of preference):
  1. Technical question related to main topic → Link API Reference or Documentation
  2. "How do I get a license?" or "What are the licensing options?" → Link BOTH Pricing URL and License URL
  3. "Where can I find more examples?" → Link Documentation or Blogs URL
  4. "Where can I get support?" → Link Forums URL
- Practical questions related to topic
- NEVER mention "free" or "online"

**LICENSE FAQ EXAMPLES:**
✅ **Q: How can I use this SDK in production?**  
   A: For commercial use, you can purchase a license from the [pricing page](pricing_url). If you want to evaluate the SDK first, request a [temporary license](license_url) for testing purposes.

✅ **Q: What licensing options are available?**  
   A: Visit the [pricing page](pricing_url) to explore different licensing tiers for production use. You can also obtain a [temporary license](license_url) to evaluate the SDK before purchasing.

✅ **Q: Do I need a license to use this SDK?**  
   A: Yes, for production deployment you need a license from the [pricing page](pricing_url). For evaluation and testing, you can get a [temporary license](license_url).

❌ **Q: How do I get a license?** (as first question - WRONG placement)

❌ A: Purchase from the [pricing page](pricing_url). (WRONG - missing temporary license option)

{'### 8. READ MORE (MANDATORY)' if formatted_related else '### NO READ MORE SECTION'}
{'## Read More' if formatted_related else 'Do NOT include - no related links provided.'}
{formatted_related if formatted_related else 'Blog MUST end after FAQs.'}
{'Use EXACT titles and URLs provided.' if formatted_related else ''}

═══════════════════════════════════════════════════════════════════════════════
PART 3: TERMINOLOGY RULES (CRITICAL - STRICTLY ENFORCED)
═══════════════════════════════════════════════════════════════════════════════

### SDK vs LIBRARY/API TERMINOLOGY - MANDATORY ENFORCEMENT
**CRITICAL: Platform determines which term to use throughout the ENTIRE blog post.**

Platform variable: {platform}

**DECISION RULE:**
- IF platform = "cloud" → Use "library" or "API" EVERYWHERE
- IF platform ≠ "cloud" (on-premises) → Use "SDK" EVERYWHERE

**Platform Examples:**
- Cloud platforms: "cloud"
- On-premises platforms: ".NET", "Java", "Python", "C++", "Node.js", "PHP", etc.

**TERMINOLOGY APPLICATION:**
IF platform = "cloud":
  ✅ "the library provides"
  ✅ "install the library"
  ✅ "using this API"
  ✅ "the library handles"
  ❌ "the SDK provides" (WRONG)
  ❌ "install the SDK" (WRONG)

IF platform ≠ "cloud" (on-premises like .NET, Java, Python, etc.):
  ✅ "the SDK provides"
  ✅ "install the SDK"
  ✅ "using this SDK"
  ✅ "the SDK handles"
  ❌ "the library provides" (WRONG)
  ❌ "install the library" (WRONG)

**APPLY EVERYWHERE IN BLOG:**
- Introduction paragraphs
- Prerequisites and Setup section
- Steps section
- Outline sections
- Complete Code Example descriptions
- Conclusion section
- FAQ answers

**EXAMPLES BY PLATFORM:**

Platform = ".NET" (on-premises):
  ✅ "Aspose.PDF for .NET is a powerful SDK for document processing"
  ✅ "Install the SDK via NuGet"
  ✅ "This SDK provides comprehensive features"
  ❌ "Aspose.PDF for .NET is a powerful library" (WRONG)

Platform = "Java" (on-premises):
  ✅ "GroupDocs.Conversion for Java SDK enables developers"
  ✅ "Download the SDK from the releases page"
  ❌ "GroupDocs.Conversion for Java library enables" (WRONG)

Platform = "cloud":
  ✅ "The Aspose.PDF Cloud library offers REST API access"
  ✅ "Install the library using pip"
  ❌ "The Aspose.PDF Cloud SDK offers" (WRONG)

### PROHIBITED TERMINOLOGY (NEVER USE)
**NEVER use anywhere in content:**
❌ "Framework" - use "SDK", "library", "platform", "toolkit" instead
❌ "free SDK" or "free library" or "free API"
❌ "online tool" or "online app" or "web-based"
❌ "browser-based" or "no installation required"

**ALWAYS use:**
✅ "SDK" (if platform ≠ cloud)
✅ "library" or "API" (if platform = cloud)
✅ "programmatic solution"
✅ "install and integrate"

═══════════════════════════════════════════════════════════════════════════════
PART 4: LINKING REQUIREMENTS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

### CONTEXT RESOURCES (MUST USE - COMPREHENSIVE LINKING)
Context contains ALL these resource types - YOU MUST USE THEM:
- **Product Page URL** (MANDATORY - link every time product mentioned)
- **Documentation URL** (MANDATORY - link in Prerequisites, Steps, or Outline)
- **API Reference URL** (MANDATORY - link when mentioning classes/methods)
- **Download URL** (MANDATORY - link in Prerequisites/Installation section)
- **License URL** (MANDATORY - link in Prerequisites or Conclusion)
- Blog Category URL (optional - can link in Introduction or Conclusion)
- Forums URL (optional - can mention for support in Conclusion or FAQs)
- Free Apps URL (optional - avoid mentioning as per restrictions)

### MANDATORY LINKING RULES - EXPANDED
1. Include **MINIMUM 5-7 contextual links** from provided resources (not just 2-3)
2. MUST link product page URL EVERY TIME product name is mentioned
3. MUST link **Documentation URL** at least once (Prerequisites, Steps, or Outline)
4. MUST link **API Reference URL** when mentioning any class, method, or property
5. MUST link **Download URL** in Prerequisites/Installation section
6. MUST link **License URL** at least once (Prerequisites or Conclusion)
7. CRITICAL: Only use links explicitly provided in context
8. NEVER construct or guess URLs
9. If class/method URL NOT in context → mention as plain text, no link
10. Link naturally within paragraphs (not just FAQs)
11. Use descriptive anchor text (not "click here")
12. NEVER put links inside backticks or code literals

### WHERE TO USE EACH RESOURCE LINK

**Product Page URL** - Use in:
- Introduction (when first mentioning product)
- Prerequisites/Installation (when explaining what product does)
- Outline sections (when referencing product capabilities)
- Conclusion (final mention of product)
- FAQs (when answering product-related questions)

**Documentation URL** - Use in:
- Prerequisites (link to getting started docs)
- Steps section ("For more details, see the [documentation](URL)")
- Outline sections (when explaining complex features)
- Example: "Learn more about configuration in the [official documentation](URL)"

**API Reference URL** - Use in:
- Steps section (when mentioning classes/methods)
- Outline sections (when explaining APIs)
- Example: "Initialize the [Presentation](API_URL) class"
- Example: "Use the [save](API_URL) method"

**Download URL** - Use in:
- Prerequisites/Installation section (MANDATORY)
- Example: "Download the latest version from the [release page](URL)"
- Can also link External Download URL if provided

**License URL** - Use in:
- Prerequisites section ("Get a [temporary license](URL) for testing")
- Conclusion section ("For production use, obtain a [license](URL)")
- FAQs ("How do I get a license? Visit [this page](URL)")

**Blog Category URL** - Use in:
- Introduction or Conclusion (optional)
- Example: "Check out more [tutorials](URL) on our blog"

**Forums URL** - Use in:
- Conclusion or FAQs (optional)
- Example: "Need help? Visit our [support forums](URL)"
- Example FAQ: "Where can I get support? Check the [community forums](URL)"

### PRODUCT NAME AND FILE FORMAT LINKING (CRITICAL - NEW RULES)

**CRITICAL DISTINCTION: Product Names vs File Formats**

**1. PRODUCT NAMES (Link to Product Page):**
When mentioning the product (e.g., Aspose.ZIP, Aspose.PDF, GroupDocs.Conversion):
- Link the FULL product name to the product page
- Format: [Aspose.ZIP for .NET](product_page_url)
- Examples:
  * [Aspose.ZIP for .NET](https://products.aspose.com/zip/net/)
  * [Aspose.PDF for Java](https://products.aspose.com/pdf/java/)
  * [GroupDocs.Conversion for Python](https://products.groupdocs.com/conversion/python-net/)

**2. FILE FORMATS (Link to FileFormat.com):**
When discussing file formats separately (e.g., ZIP, PDF, DOCX, PNG):
- Link ONLY the file format to docs.fileformat.com
- Format: [ZIP](https://docs.fileformat.com/compression/zip/)
- Examples:
  * [ZIP](https://docs.fileformat.com/compression/zip/)
  * [PDF](https://docs.fileformat.com/pdf/)
  * [PNG](https://docs.fileformat.com/image/png/)
  * [DOCX](https://docs.fileformat.com/word-processing/docx/)

**3. WRONG PATTERNS TO AVOID:**
❌ [Aspose.ZIP](fileformat_url) - Product linked to file format
❌ [ZIP for .NET](product_url) - File format with platform linked to product
❌ Aspose.[ZIP](fileformat_url) - Splitting product name with file format link

**4. CORRECT USAGE EXAMPLES:**

**Example 1: Introduction paragraph**
"[Aspose.ZIP for .NET](https://products.aspose.com/zip/net/) is a powerful SDK for working with [ZIP](https://docs.fileformat.com/compression/zip/) archives in C# applications."

**Example 2: Discussing formats**
"The [PDF](https://docs.fileformat.com/pdf/) format is widely used for documents, and [Aspose.PDF for Java](https://products.aspose.com/pdf/java/) provides comprehensive features for PDF manipulation."

**Example 3: Format comparison**
"Converting between [DOCX](https://docs.fileformat.com/word-processing/docx/) and [PDF](https://docs.fileformat.com/pdf/) formats is straightforward with [GroupDocs.Conversion for .NET](https://products.groupdocs.com/conversion/net/)."

**5. APPLICATION THROUGHOUT BLOG:**
- First mention of product: Link product name to product page
- First mention of file format: Link format to docs.fileformat.com
- Subsequent mentions: Can be plain text or link again as appropriate
- Never split product names with file format links
EVERY TIME you mention the product name, you MUST link it to the product page:

FORMAT: [Full Product Name with Platform](product_page_url)

EXAMPLES:
✅ [Aspose.Slides for .NET](https://products.aspose.com/slides/net/)
✅ [GroupDocs.Conversion for Java](https://products.groupdocs.com/conversion/java/)
✅ [Conholdate.Total for Python](https://products.conholdate.com/total/python-net/)

REQUIREMENTS:
- MUST include full product name with platform
- MUST use product page URL from context
- Apply EVERY time product is mentioned in:
  * Introduction paragraphs
  * Prerequisites/Installation section
  * Steps section
  * Outline sections
  * Conclusion section
  * FAQ answers

### LINKING FORMAT - DO'S AND DON'TS

PRODUCT PAGE LINKS (MANDATORY):
✅ [Aspose.Slides for .NET](URL) - Full product name with platform
✅ [GroupDocs.Viewer for Java](URL) - Full product name with platform
❌ [product page](URL) - Generic text
❌ [Aspose.Slides](URL) - Missing platform
❌ [the SDK](URL) - Not using product name

API REFERENCE LINKS (ONLY IF URL IN CONTEXT):
✅ Initialize the [Presentation](URL) class - Link outside backticks
✅ Use the [Save](URL) method - Link outside backticks
❌ Initialize the `[Presentation](URL)` class - Link inside backticks
❌ Use `[Save](URL).PNG` - Link inside code literal
❌ [ImageFormat](URL).PNG - Appending to URL breaks link

If URL NOT in context:
✅ Initialize the Presentation class - Plain text, no link
✅ Use the Save method - Plain text, no link

DOCUMENTATION LINKS:
- "Learn more in the [documentation](URL)"
- "See the [API reference](URL) for details"

DOWNLOAD LINKS:
- "[Download the SDK](URL)" (if platform ≠ cloud)
- "[Download the library](URL)" (if platform = cloud)

### LINK PLACEMENT BEST PRACTICES
- Integrate naturally within sentences
- Place where readers logically want more info
- Don't cluster multiple links unless necessary
- Ensure links add value, not just SEO
- Verify all URLs from context before using
- MUST link product name EVERY time it appears

═══════════════════════════════════════════════════════════════════════════════
PART 5: CODE SNIPPET REQUIREMENTS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

### MANDATORY CODE WRAPPER FORMAT
ALL code snippets MUST use appropriate wrapper tags:

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
- Complete Code Examples MUST use COMPLETE_CODE_SNIPPET tags

### CODE SNIPPET TYPES AND THEIR WRAPPERS
1. **Prerequisites/Installation**: Installation commands (must be valid and working)
   - Use: <!--[CODE_SNIPPET_START]--> ... <!--[CODE_SNIPPET_END]-->

2. **Steps Section**: Partial code illustrating specific actions (must be syntactically correct)
   - Use: <!--[CODE_SNIPPET_START]--> ... <!--[CODE_SNIPPET_END]-->

3. **Outline Sections**: Code chunks broken down for explanation (must be valid code)
   - Use: <!--[CODE_SNIPPET_START]--> ... <!--[CODE_SNIPPET_END]-->

4. **Complete Code Examples**: FULL working code (demonstrates entire concept)
   - Use: <!--[COMPLETE_CODE_SNIPPET_START]--> ... <!--[COMPLETE_CODE_SNIPPET_END]-->
   - **CRITICAL: Must use COMPLETE_ prefix in tags**
   - **This is the ONLY section that uses COMPLETE_CODE_SNIPPET tags**

### CODE QUALITY REQUIREMENTS (CRITICAL - NON-NEGOTIABLE)

**ALL CODE MUST BE:**
✅ **Syntactically correct** - No syntax errors, proper language conventions
✅ **Executable** - Code runs without errors when executed with proper setup
✅ **Complete** - All necessary imports, dependencies, and initialization included
✅ **Functional** - Demonstrates the concept with appropriate error handling
✅ **Sound logic** - Code logic achieves the stated purpose
✅ **Bug-free compilation** - No compilation errors, null pointer exceptions, or obvious bugs
✅ **Platform-appropriate** - Uses correct APIs and methods for the specified platform/language
✅ **Version-compatible** - Works with the library/SDK version being discussed

**PROHIBITED IN CODE:**
❌ Placeholder comments like "// ... rest of code" or "// your code here"
❌ Undefined variables or missing imports
❌ Syntax errors (missing semicolons, brackets, quotes, etc.)
❌ Incorrect method names or class names
❌ Wrong API usage or deprecated methods
❌ Missing file paths or hardcoded invalid paths
❌ Unhandled exceptions in critical sections
❌ Memory leaks or resource leaks (unclosed streams, connections)
❌ Logic errors that would cause runtime failures
❌ Pseudo-code or conceptual code that won't compile/run
❌ **License initialization code (License class, SetLicense, ApplyLicense)**
❌ **License file paths or license-related variables**
❌ **Any code related to license setup**

### CODE VERIFICATION CHECKLIST

Before including ANY code snippet, verify:
□ All imports/includes are present and correct
□ All variables are declared before use
□ All method/function names are spelled correctly
□ All class names match the actual API
□ Proper syntax for the language (semicolons, brackets, indentation)
□ File paths use proper format (forward slashes, backslashes as needed)
□ Resources are properly initialized and disposed
□ Error handling is present (try-catch, if-checks)
□ Code follows the documented API for the product version
□ No hardcoded values that would cause failures
□ Comments are helpful, not placeholders

### INSTALLATION CODE REQUIREMENTS

**Package Manager Commands:**
- Must use correct package manager for platform (NuGet, Maven, pip, npm)
- Must include correct package name and syntax
- Version numbers should be current or use latest tag
- Must be valid commands that can be executed in terminal/command prompt

**Examples:**
✅ CORRECT (NuGet):
```bash
Install-Package Aspose.Slides.NET
```

✅ CORRECT (Maven):
```xml
<dependency>
    <groupId>com.aspose</groupId>
    <artifactId>aspose-slides</artifactId>
    <version>25.1</version>
    <classifier>jdk16</classifier>
</dependency>
```

❌ WRONG:
```bash
Install-Package [PackageName]  # Placeholder not allowed
```

### COMPLETE CODE EXAMPLE REQUIREMENTS (ENHANCED)

**MUST INCLUDE:**
1. **All Imports/Includes** at the top
   - Every class, method, or type used must be imported
   - Use correct import syntax for the language
   - Include platform-specific imports (System, java.io, etc.)

2. **Proper Initialization**
   - Objects created with correct constructors
   - Variables initialized before use
   - Configuration set up properly
   - **DO NOT include license initialization code**
   - **DO NOT include License class or SetLicense calls**

3. **Working Logic**
   - Code achieves the stated goal (e.g., actually converts PDF to PNG)
   - All steps are present and in correct order
   - No logical errors or missing steps

4. **Error Handling**
   - Try-catch blocks for operations that can fail
   - Appropriate exception handling
   - Graceful error messages where needed

5. **Resource Cleanup**
   - Close file streams after use
   - Dispose of objects properly
   - Release memory/resources

6. **Correct File Paths**
   - Use realistic example paths (e.g., "input.pdf", "output.png")
   - Use proper path separators for platform
   - No invalid or system-specific paths

7. **Comments for Clarity**
   - Explain what the code does
   - Not placeholders or TODOs
   - Help users understand the logic

**WHAT NOT TO INCLUDE IN CODE:**
❌ License initialization (License class)
❌ SetLicense() or ApplyLicense() calls
❌ License file paths
❌ Any licensing-related code

**QUALITY STANDARDS:**
- Code should compile without modifications (except file paths)
- Users should be able to adapt and use it (after updating file paths and obtaining license separately)
- Code demonstrates best practices for the SDK/library
- Code is efficient and doesn't include unnecessary operations
- Code matches the examples in official documentation style

### PARTIAL CODE SNIPPETS (Steps/Outline Sections)

Even partial code must be:
✅ Syntactically valid (can be compiled if isolated)
✅ Logically sound
✅ Use correct API methods
✅ Include necessary imports in context

### CODE TESTING MANDATE

**Before including code, mentally verify:**
1. Would this code compile without errors?
2. Would this code run without exceptions (with proper setup)?
3. Would this code produce the expected output?
4. Are all API calls correct for this product/platform?
5. Is appropriate error handling included?
6. Are resources cleaned up properly?

**If answer to ANY question is "No" or "Unsure" - DO NOT INCLUDE THE CODE**
Rewrite until all answers are "Yes"

**Note:** Code examples are meant to demonstrate concepts and functionality. Users should test and adapt them for their specific needs.

### CRITICAL: CORRECT WRAPPER TAG USAGE

**Complete Code Examples (Section 5) - MUST USE THESE TAGS:**
<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code here
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

**Regular Code Snippets (Prerequisites, Steps, Outline) - MUST USE THESE TAGS:**
<!--[CODE_SNIPPET_START]-->
```language
// Code snippet here
```
<!--[CODE_SNIPPET_END]-->

**CRITICAL RULES:**
- Complete Code Examples = COMPLETE_CODE_SNIPPET_START/END (with COMPLETE_ prefix)
- Regular snippets = CODE_SNIPPET_START/END (without COMPLETE_ prefix)
- Using wrong tags makes output INVALID
- This distinction is MANDATORY and NON-NEGOTIABLE

═══════════════════════════════════════════════════════════════════════════════
PART 6: WRITING GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

### WORD COUNT TARGET
Introduction + Prerequisites + Outline sections + Conclusion = {settings.NUMBER_OF_BLOG_WORDS} words

EXCLUDED from word count:
- Frontmatter
- Steps section
- Code examples
- FAQs
{'- Read More' if formatted_related else ''}

### PRIMARY KEYWORD USAGE (CRITICAL - SEO REQUIREMENT)
The PRIMARY keyword is the first keyword in the list: {primary_keyword}
The SECONDARY keywords are all remaining keywords in the list: {secondary_keywords}

**MANDATORY PRIMARY KEYWORD DENSITY:**
- PRIMARY keyword MUST appear at 1% density of total blog word count
- Formula: (Word Count / 100) = Minimum keyword occurrences
- Examples:
  * 600 words = 6 occurrences minimum
  * 800 words = 8 occurrences minimum
  * 1000 words = 10 occurrences minimum
  * 1200 words = 12 occurrences minimum
- Count includes: Introduction, Prerequisites, Steps, Outline sections, Conclusion
- Does NOT count: Frontmatter, FAQs, Read More section
- Use naturally within sentences - avoid keyword stuffing
- Distribute evenly throughout content (not clustered in one section)
- Variations are acceptable but exact keyword should meet minimum count
- **NEVER surround primary keyword with asterisks or make it italic/bold**
- **NEVER use markdown formatting around the primary keyword**
- Primary keyword should appear as plain text in natural sentences

**SECONDARY KEYWORDS USAGE (MANDATORY):**
- MUST use ALL secondary keywords throughout the blog post
- Each secondary keyword should appear 2-4 times naturally
- Distribute across different sections (Introduction, Prerequisites, Steps, Outline, Conclusion)
- Use in context where they naturally fit
- Can use variations or related forms
- Should enhance content, not force awkward phrasing
- Secondary keywords support the primary keyword naturally

**KEYWORD DISTRIBUTION STRATEGY:**
- Introduction: 1-2 primary keyword uses, 1-2 secondary keywords
- Prerequisites: 1 primary keyword use, 1-2 secondary keywords
- Steps: 2-3 primary keyword uses (in explanations), 2-3 secondary keywords
- Outline Sections: Majority of primary keyword uses, most secondary keywords
- Conclusion: 1-2 primary keyword uses, 1-2 secondary keywords

**CORRECT examples:**
- "When working with {primary_keyword}, developers need to..."
- "The {primary_keyword} process involves several steps..."
- "To implement {primary_keyword} functionality..."
- "Best practices for {primary_keyword} include..."

**INCORRECT examples:**
- ❌ "When working with *{primary_keyword}*, developers..." (has asterisks)
- ❌ "The **{primary_keyword}** process involves..." (has bold)
- ❌ "To implement _{primary_keyword}_ functionality..." (has underscores)
- ❌ "Best practices for `{primary_keyword}` include..." (has backticks)
- ❌ Using same keyword 5 times in one paragraph (keyword stuffing)
- ❌ Forcing keywords awkwardly: "The {primary_keyword} is a {primary_keyword} solution for {primary_keyword}" (unnatural)

### TONE AND STYLE
- Professional but approachable
- Technical accuracy is paramount
- Clear, concise explanations
- Natural integration of all keywords (primary keyword at 1% density, all secondary keywords 2-4 times)
- **Primary keyword MUST appear as plain text without any markdown formatting (no asterisks, bold, italic, backticks)**
- **Secondary keywords must be distributed naturally across all sections**
- Avoid over-formatting (minimal bold/lists unless needed)
- Use complete paragraphs for most sections
- Lists/bullets only when explicitly needed
- NEVER use casual or promotional language about "free" offerings

### HUMAN-LIKE WRITING QUALITY (CRITICAL - NON-NEGOTIABLE)
**ELIMINATE ALL AI-GENERATED PATTERNS:**

**PROHIBITED PUNCTUATION (NEVER USE):**
❌ Em dashes (—) - Use single hyphen (-) instead
❌ En dashes (–) - Use single hyphen (-) instead
❌ Curly quotes (" " ' ') - Use straight quotes (" ') only
❌ Ellipsis character (…) - Use three periods (...) instead
❌ Bullet points (•) - Use hyphen (-) for lists
❌ Any Unicode punctuation - ASCII only

**CORRECT PUNCTUATION USAGE:**
✅ Single hyphen (-) for all dash uses
✅ Straight double quotes (") for quotations
✅ Straight single quotes (') for apostrophes
✅ Three periods (...) if trailing off
✅ Simple commas, periods, semicolons
✅ Standard ASCII punctuation throughout

**AVOID AI-TYPICAL PHRASES:**
Never use these overused AI phrases:
❌ "In today's digital landscape"
❌ "In the ever-evolving world of"
❌ "It's worth noting that"
❌ "It's important to remember"
❌ "Delve into"
❌ "Dive deep into"
❌ "Seamlessly integrate"
❌ "Robust solution"
❌ "Cutting-edge technology"
❌ "Game-changing"
❌ "Revolutionary approach"
❌ "Unlock the power of"
❌ "Harness the potential"
❌ "Elevate your"
❌ "Streamline your workflow"
❌ "Production-ready code" (code examples are demonstrative)
❌ "Production-grade solution"
❌ "Enterprise-ready"
❌ "Ready-to-run example"
❌ "Ready-to-use code"
❌ "Copy-paste ready"
❌ "Plug-and-play solution"
❌ "Out-of-the-box functionality"
❌ "Battle-tested"
❌ "Industry-standard"
❌ "In conclusion, it's clear that"
❌ "To sum up"
❌ "At the end of the day"
❌ "The bottom line is"

**USE NATURAL ALTERNATIVES:**
✅ "Modern applications require..."
✅ "Software developers need..."
✅ "This solution provides..."
✅ "The library offers..."
✅ "Remember to..."
✅ "Keep in mind..."
✅ "This approach works well for..."
✅ "Developers can use this to..."
✅ "This method handles..."

**SENTENCE STRUCTURE VARIETY:**
- Mix short and long sentences naturally
- Don't start multiple sentences the same way
- Vary sentence openings (avoid repetitive patterns)
- Use active voice primarily, passive occasionally
- Break up long technical explanations with shorter statements

**PARAGRAPH FLOW:**
- Each paragraph should have ONE main idea
- Use transition words naturally (however, therefore, additionally, also)
- Don't overuse transition phrases (avoid starting every paragraph with "Moreover" or "Furthermore")
- Connect ideas logically without forced connectors
- 3-5 sentences per paragraph typically

**NATURAL TECHNICAL WRITING:**
✅ "The Presentation class loads the PowerPoint file"
✅ "You can configure the output settings before saving"
✅ "This method returns the converted document"
✅ "Set the image format to PNG using the Save method"

❌ "Leverage the Presentation class to seamlessly load"
❌ "You can effortlessly configure cutting-edge output settings"
❌ "This robust method returns the converted document"
❌ "Harness the power of the Save method to unlock PNG format"

**CONVERSATIONAL BUT PROFESSIONAL:**
- Use "you" and "your" naturally (not "one's" or "the user's")
- Occasionally use contractions (it's, you're, don't) for natural flow
- Address the reader directly but professionally
- Explain complex concepts simply without being condescending

**EXAMPLES OF NATURAL WRITING:**

BAD (AI-like):
"In today's rapidly evolving digital landscape, it's worth noting that seamlessly converting PDF files to PNG images has become increasingly important. Let's delve into how you can leverage cutting-edge technology to unlock the power of efficient document conversion."

GOOD (Human-like):
"Converting PDF files to PNG images is a common requirement in modern applications. This guide shows you how to implement this conversion programmatically using a reliable SDK."

BAD (AI-like):
"It's important to remember that, when working with document conversion, the robust Aspose.PDF library offers a comprehensive suite of cutting-edge features that empower developers to seamlessly transform files."

GOOD (Human-like):
"Aspose.PDF for .NET provides extensive features for document conversion. The library handles various file formats and offers flexible configuration options."

BAD (AI-like):
"This production-ready, enterprise-grade solution delivers battle-tested code that seamlessly integrates into your workflow."

GOOD (Human-like):
"This code example demonstrates the conversion process. Test it in your development environment and adapt it to your specific requirements."

BAD (AI-like):
"Here's a ready-to-run, copy-paste ready example that provides out-of-the-box functionality for your production environment."

GOOD (Human-like):
"This example shows the implementation approach. You'll need to adjust file paths and test it with your specific setup."

**CONTENT AUTHENTICITY CHECKS:**
Before finalizing, verify:
□ No em dashes (—) or en dashes (–) anywhere
□ Only straight quotes (" '), no curly quotes
□ No overused AI phrases from the prohibited list
□ Sentence variety (not all starting the same way)
□ Natural transitions between paragraphs
□ Active voice used predominantly
□ Technical terms explained simply
□ No excessive adjectives (robust, seamless, cutting-edge, powerful)
□ No terms like "production-ready", "production-grade", "enterprise-ready"
□ No terms like "ready-to-run", "ready-to-use", "copy-paste ready", "plug-and-play"
□ Code examples described as demonstrative, requiring testing and adaptation
□ Contractions used occasionally for natural flow
□ Direct address to reader ("you can" not "one can")
□ Simple, clear language over complex phrasing

### CONTENT QUALITY
- Accurate technical information
- Practical, actionable guidance
- Real-world examples where helpful
- Clear progression from basic to advanced
- Address common use cases and challenges
- Focus on programmatic implementation, not web tools
- Ensure primary keyword density meets 1% requirement (Word Count / 100)
- Ensure all secondary keywords are used 2-4 times naturally

═══════════════════════════════════════════════════════════════════════════════
PART 7: VALIDATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

OUTPUT IS INVALID IF:
❌ **HUMAN-LIKE WRITING VIOLATIONS (CRITICAL)**:
  ❌ Em dashes (—) found anywhere in content
  ❌ En dashes (–) found anywhere in content
  ❌ Curly quotes (" " ' ') used instead of straight quotes
  ❌ Ellipsis character (…) used instead of three periods
  ❌ Prohibited AI phrases detected (delve, seamlessly, robust, cutting-edge, leverage, unlock, harness, revolutionary, game-changing)
  ❌ Repetitive sentence structures (multiple sentences starting the same way)
  ❌ Excessive adjectives or marketing language
  ❌ Unnatural phrasing that sounds AI-generated
  ❌ No contractions used (sounds too formal/robotic)
  ❌ Using "one" instead of "you" to address reader
❌ Title does NOT match title variable exactly
❌ SEO Title is NOT 50-60 characters (strict enforcement)
❌ SEO Title does NOT include primary keyword
❌ SEO Title contains brand/product names
❌ Title has been modified, shortened, or adjusted in any way
❌ PRIMARY keyword density is NOT 1% of word count (Word Count / 100 = minimum occurrences)
❌ PRIMARY keyword is surrounded by asterisks, underscores, or backticks anywhere
❌ PRIMARY keyword has any markdown formatting applied to it
❌ SECONDARY keywords are missing or not used throughout content
❌ SECONDARY keywords used fewer than 2 times each
❌ Keywords clustered unnaturally (keyword stuffing detected)
❌ Description NOT 140-160 characters
❌ Summary NOT 140-160 characters
❌ URL contains product/brand name
❌ URL missing "in" before language/platform
❌ Introduction has H2 heading
❌ **Product page URL (ProductURL) NOT linked in FIRST paragraph**
❌ **Product name link in FIRST paragraph missing platform (e.g., just "Aspose.PDF" instead of "Aspose.PDF for .NET")**
❌ **Product name link uses generic text instead of full product name (e.g., "[SDK](URL)" instead of "[Aspose.PDF for .NET](URL)")**
❌ **Product name link appears in second or third paragraph instead of FIRST paragraph**
❌ Prerequisites/Installation missing
❌ Download URL NOT linked in Prerequisites/Installation
❌ **Pricing URL (pricing_url) NOT linked in Conclusion or license FAQ**
❌ **Temporary License URL (license_url) NOT linked in Conclusion or license FAQ**
❌ **Conclusion has only pricing OR temporary license link (must have BOTH)**
❌ Documentation URL NOT linked anywhere in content
❌ Fewer than 5 total contextual links from provided resources
❌ Steps, Conclusion, or FAQs missing
❌ **COMPLETE CODE EXAMPLE SECTION MISSING (CRITICAL FAILURE)**
❌ **Complete Code Example intro text uses "ready-to-run", "ready-to-use", "production-ready", or "copy-paste ready"**
❌ **DISCLAIMER MISSING after Complete Code Example (CRITICAL FAILURE)**
❌ Disclaimer not in blockquote format (>)
❌ Disclaimer missing documentation or support links
❌ "Complete Code Example" heading without code content
❌ Multiple task title but sections for tasks without code
❌ **CODE QUALITY VIOLATIONS (CRITICAL)**:
  ❌ Code contains syntax errors (won't compile)
  ❌ Code has placeholder comments like "// ... rest of code"
  ❌ Code uses undefined variables or missing imports
  ❌ Code has incorrect method/class names
  ❌ Code would throw runtime exceptions
  ❌ Code lacks proper error handling
  ❌ Code has resource leaks (unclosed streams/connections)
  ❌ Installation commands are incorrect or incomplete
  ❌ Code uses wrong API or deprecated methods
  ❌ Code is pseudo-code or non-executable
  ❌ Code won't achieve stated purpose (logical errors)
  ❌ **Code includes license initialization (License class, SetLicense, ApplyLicense)**
  ❌ **Prerequisites section includes license setup steps**
  ❌ **License mentioned before Complete Code Example or Conclusion**
{'❌ Read More section missing' if formatted_related else '❌ Read More section present'}
❌ Steps not in frontmatter
❌ FAQs not in frontmatter
❌ Code snippet lacks wrapper tags
❌ **Complete Code Example uses wrong tags (must use COMPLETE_CODE_SNIPPET_START/END)**
❌ **Regular code snippets use COMPLETE_CODE_SNIPPET tags (should use CODE_SNIPPET_START/END)**
❌ Complete Code Example has placeholders
❌ Text before frontmatter or after {'Read More' if formatted_related else 'FAQs'}
❌ **Sections in wrong order (must be: Intro → Prerequisites and Setup → Steps → Outline → Complete Code → Conclusion → FAQs)**
❌ **Steps section is missing from the document**
❌ **Complete Code Example appears BEFORE Steps section (Steps MUST come before Complete Code)**
❌ **Outline sections include "Setting Up", "Installation", or "Configuration" topics (these belong in Prerequisites and Setup only)**
❌ **Prerequisites and Setup section is not comprehensive (must cover installation, setup, configuration)**
❌ **Headings use articles before product names (e.g., "a Aspose.ZIP", "an Aspose.Slides")**
❌ Outline sections skipped
❌ Wrong terminology for platform type
❌ **Platform is on-premises (not cloud) but content uses "library" instead of "SDK"**
❌ **Platform is cloud but content uses "SDK" instead of "library"**
❌ **Mixed usage of "SDK" and "library" for same platform (must be consistent)**
❌ "Framework" appears anywhere
❌ Product mentioned without product page URL link
❌ Product page URL uses generic anchor text
❌ Product URL missing platform in name
❌ Word count NOT {settings.NUMBER_OF_BLOG_WORDS} words
❌ Unicode/special chars in frontmatter
❌ Unquoted YAML values with colons
❌ Line breaks in YAML strings
❌ Fewer than 2 contextual links
❌ Links inside backticks/code literals
❌ API links for classes without URLs in context
❌ URLs not found in context
❌ No links in FAQ answers
❌ Content mentions "free SDK" or "free library"
❌ Content mentions "online tool" or "online app"
❌ Content mentions "production-ready" or "production-grade" code
❌ Content mentions "ready-to-run", "ready-to-use", "copy-paste ready", or "plug-and-play"
❌ Content implies code is ready for production use without testing
❌ Product name appears WITHOUT product page link

### PRE-SUBMISSION VERIFICATION
Before submitting, manually verify:
□ Title: EXACT match to title variable - NO modifications
□ SEO Title: 50-60 characters (count manually including spaces)
□ SEO Title: Includes primary keyword naturally
□ SEO Title: NO brand/product names included
□ SEO Title: Compelling and click-worthy
□ Title NOT modified, shortened, or adjusted
□ **HUMAN-LIKE WRITING QUALITY VERIFICATION (CRITICAL)**:
  □ NO em dashes (—) anywhere in content
  □ NO en dashes (–) anywhere in content
  □ ONLY straight quotes (" ') used, NO curly quotes (" " ' ')
  □ NO ellipsis character (…), use three periods (...) if needed
  □ NO prohibited AI phrases (delve, seamlessly, robust, cutting-edge, leverage, unlock, harness)
  □ Sentence structure varies (not all starting the same way)
  □ Natural transitions between paragraphs
  □ Active voice used predominantly
  □ Contractions used occasionally (it's, you're, don't) for natural flow
  □ Direct address to reader ("you" not "one")
  □ NO excessive adjectives or marketing language
  □ Technical explanations are clear and simple
  □ Content sounds like a professional human wrote it
□ **LICENSE MENTION VERIFICATION (CRITICAL)**:
  □ Conclusion section includes BOTH pricing and temporary license links
  □ Pricing link format: [pricing page](pricing_url) or [license](pricing_url)
  □ Temporary license link format: [temporary license](license_url)
  □ If license FAQ exists, it's NOT the first FAQ (should be 2nd, 3rd, or 4th)
  □ If license FAQ exists, it includes BOTH pricing_url and license_url
  □ License NOT mentioned in Prerequisites section
  □ No license code in any code examples
□ **KEYWORD DENSITY VERIFICATION (CRITICAL)**:
  □ Calculate word count of blog body (Intro + Prerequisites + Steps + Outline + Conclusion)
  □ Divide by 100 to get minimum primary keyword occurrences
  □ Example: 800 words / 100 = 8 minimum occurrences
  □ Count primary keyword uses in body (exclude frontmatter, FAQs, Read More)
  □ PRIMARY keyword meets 1% density requirement
  □ PRIMARY keyword distributed evenly (not clustered)
  □ ALL SECONDARY keywords used 2-4 times each
  □ Secondary keywords appear across multiple sections
  □ No keyword stuffing (natural usage throughout)
□ PRIMARY keyword appears as PLAIN TEXT (no asterisks, bold, italic, backticks)
□ Description: 140-160 chars
□ Summary: 140-160 chars
□ URL: Uses "in" before language, no brands (URL only - not title)
□ Brand/product names KEPT in title field only (not in seoTitle)
□ **CRITICAL: Product page URL (ProductURL) linked in FIRST paragraph**
□ **Product link format verification**:
  □ Uses FULL product name with platform: [BrandName.ProductName for Platform](URL)
  □ Example format: [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)
  □ NOT just product name: ❌ [Aspose.PDF](URL)
  □ NOT generic text: ❌ [this SDK](URL) or [the library](URL)
  □ Link appears in FIRST paragraph (not second or third)
  □ Link includes platform designation (for .NET, for Java, for Python, etc.)
□ **RESOURCE LINKS VERIFICATION (CRITICAL)**:
  □ Product Page URL linked in FIRST paragraph (MANDATORY)
  □ Product Page URL linked at least 3 times total (intro, sections, conclusion, FAQs)
  □ Download URL linked in Prerequisites/Installation section
  □ License URL linked in Prerequisites or Conclusion
  □ Documentation URL linked at least once (Prerequisites, Steps, or Outline)
  □ API Reference URLs linked when mentioning classes/methods (if available)
  □ MINIMUM 5 total contextual links from provided resources
□ Introduction: No H2, has paragraph content
□ **Prerequisites and Setup: Comprehensive section covering installation, environment, configuration, license**
□ **Prerequisites and Setup: Included with ALL setup requirements - NO separate setup sections later**
□ **Steps section EXISTS and appears BEFORE Complete Code Example section**
□ **Section order verified: Intro → Prerequisites and Setup → Steps → Outline → Complete Code → Conclusion → FAQs**
□ **Outline sections do NOT contain "Setting Up", "Installation", or "Configuration" topics**
□ **Outline sections contain only Understanding, Advanced, Usage, Best Practices type content**
□ **No articles (a/an) used before product names in any headings**
□ **TERMINOLOGY VERIFICATION (CRITICAL):**
  □ Check platform value: {platform}
  □ If platform ≠ "cloud": Content uses "SDK" throughout (NOT "library")
  □ If platform = "cloud": Content uses "library" or "API" throughout (NOT "SDK")
  □ Terminology is CONSISTENT throughout entire blog (no mixing SDK and library)
  □ Search for "library" if platform is on-premises - should find ZERO instances
  □ Search for "SDK" if platform is cloud - should find ZERO instances
□ Correct terminology: SDK or library/API based on platform
□ "Framework" NEVER used
□ "free SDK/library/API" NEVER used
□ "online tool/app" NEVER used
□ **"production-ready" or "production-grade" NEVER used**
□ **"ready-to-run", "ready-to-use", "copy-paste ready", "plug-and-play" NEVER used**
□ **Code examples NOT described as ready for production without testing**
□ **Code examples described as demonstrative, requiring adaptation and testing**
□ Product page: Full name with platform as anchor
□ Product linked EVERY time it's mentioned
□ API links: Only if URLs in context
□ NO links in backticks/code literals
□ All URLs verified in context
□ Steps: Mention classes/methods (link if URL exists)
□ **COMPLETE CODE EXAMPLE SECTION VERIFICATION (CRITICAL)**:
  □ At least ONE Complete Code Example section EXISTS
  □ Section appears AFTER outline sections and BEFORE Conclusion
  □ If multiple tasks in title, section created for EACH demonstrable task
  □ Section is NOT empty (contains actual working code)
  □ **INTRO SENTENCE uses correct language (demonstrates/shows/illustrates)**
  □ **INTRO SENTENCE does NOT use: ready-to-run, ready-to-use, production-ready, copy-paste ready**
  □ **CRITICAL: Uses <!--[COMPLETE_CODE_SNIPPET_START]--> tags (NOT CODE_SNIPPET_START)**
  □ **CRITICAL: Uses <!--[COMPLETE_CODE_SNIPPET_END]--> tags (NOT CODE_SNIPPET_END)**
  □ **MANDATORY disclaimer included AFTER each code example**
  □ Disclaimer uses blockquote format (>)
  □ Disclaimer includes links to documentation and support
  □ Disclaimer mentions file paths and dependencies
  □ Code meets ALL quality requirements (see below)
□ **CODE QUALITY VERIFICATION (CRITICAL)**:
  □ ALL code snippets are syntactically correct (will compile)
  □ NO placeholder comments ("// ... rest of code", "// your code here")
  □ ALL variables declared and initialized before use
  □ ALL imports/includes present and correct
  □ Method/class names spelled correctly and match actual API
  □ Installation commands are valid and complete
  □ Code includes proper error handling (try-catch where needed)
  □ Resources properly closed/disposed (no leaks)
  □ Code is executable and produces stated results
  □ NO pseudo-code or non-working examples
  □ Code logic is sound and bug-free
  □ File paths are realistic and properly formatted
□ Complete Code: Only where actual WORKING code included
□ NO empty "Complete Code Example" headings
□ No em/en dashes, curly quotes, Unicode
□ YAML values with colons are quoted
□ All steps quoted in frontmatter
□ FAQs properly formatted in YAML
□ ALL code wrapped with snippet tags
□ Multiple tasks: Verified which have code
□ Each Complete Code: Full working code
□ 5-7+ contextual links included naturally (not just 2-3)
□ Links in intro, prerequisites, steps, outline, conclusion, FAQs
□ Product page URL in intro, conclusion, FAQs
□ Descriptive anchor text (not "click here")
□ Word count: word_count_target words (excluding frontmatter/steps/code/FAQs/read-more)
□ Content ends exactly after {'Read More' if formatted_related else 'FAQs'}

═══════════════════════════════════════════════════════════════════════════════
PART 8: EXECUTION INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════════

### STEP-BY-STEP PROCESS

**BEFORE YOU START - MEMORIZE THESE TAG RULES:**
1. Complete Code Examples (Section 5) MUST use: <!--[COMPLETE_CODE_SNIPPET_START]-->
2. Complete Code Examples (Section 5) MUST use: <!--[COMPLETE_CODE_SNIPPET_END]-->
3. Regular code snippets (Prerequisites, Steps, Outline) use: <!--[CODE_SNIPPET_START]-->
4. Regular code snippets (Prerequisites, Steps, Outline) use: <!--[CODE_SNIPPET_END]-->
5. The difference is the word "COMPLETE" - Complete Code Examples MUST include it

**NOW BEGIN THE WRITING PROCESS:**

1. Start with frontmatter:
   - USE EXACT title from variable for title field
   - CREATE compelling seoTitle using primary keyword (50-60 chars, NO brand names)
   - Verify seoTitle character count manually
2. Write introduction content:
   - **CRITICAL: FIRST paragraph MUST contain product page URL link**
   - **MANDATORY FORMAT: [Full Product Name with Platform](ProductURL)**
   - **EXACT EXAMPLES**:
     * [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)
     * [GroupDocs.Conversion for Java](https://products.groupdocs.com/conversion/java/)
     * [Aspose.Slides for Python via .NET](https://products.aspose.com/slides/python-net/)
   - **The link MUST be in the FIRST paragraph (not second or third)**
   - **MUST include platform designation (for .NET, for Java, for Python, etc.)**
   - **DO NOT use generic text like "[this SDK](URL)" or "[the library](URL)"**
   - Add 1-2 more paragraphs with natural flow
   - Include primary keyword 1-2 times and 1-2 secondary keywords
   - **CRITICAL: Check platform value {platform}**
   - **IF platform ≠ "cloud": Use "SDK" (e.g., "This SDK provides...", "The SDK enables...")**
   - **IF platform = "cloud": Use "library" or "API" (e.g., "This library provides...", "The API enables...")**
   - **NEVER mix SDK and library terminology**
   - **Use natural, human-like language - NO AI clichés**
   - **Use single hyphens (-) NOT em dashes (—)**
3. Create Prerequisites and Setup section (COMPREHENSIVE):
   - Include primary keyword 1 time, 1-2 secondary keywords
   - **Cover: installation, environment setup, configuration (NO LICENSE)**
   - **This section replaces any "Setting Up [Product]" sections from outline**
   - **CRITICAL: Use correct terminology based on platform {platform}**
   - **IF platform ≠ "cloud": "Install the SDK", "Download the SDK", "The SDK requires"**
   - **IF platform = "cloud": "Install the library", "Download the library", "The library requires"**
   - **DO NOT mention license setup or license code here**
   - **License will be mentioned later in Conclusion or FAQs**
   - **VERIFY installation commands are correct and working**
   - Test syntax of package manager commands
   - **Write naturally - avoid "seamlessly install" or "robust library"**
4. Write Steps section:
   - 4-6 actionable steps
   - Use primary keyword 2-3 times in explanations, use 2-3 secondary keywords
   - **IF including code snippets: VERIFY they are syntactically correct**
   - **Use clear, professional language - NO marketing speak**
5. Process outline sections with filtering:
   - **CRITICAL: SKIP any "Setting Up", "Installation", "Configuration" sections from outline**
   - **These topics are already covered in Prerequisites and Setup**
   - ONLY include Understanding, Advanced, Usage, Best Practices type sections
   - Integrate primary keyword naturally (majority of uses should be here)
   - Use most secondary keywords across these sections
   - Distribute keywords evenly, not clustered
   - **Arrange REMAINING outline sections logically:**
     1. First: Understanding/Conceptual sections
     2. Second: Advanced/Usage sections
   - **Example: Skip "Setting Up Aspose.ZIP", keep "Understanding Z Compression" and "Advanced Options"**
   - **NEVER use "a" or "an" before product names in headings**
   - **IF including code snippets: VERIFY they are complete and working**
   - **Vary sentence structure - don't start every sentence the same way**
   - **Use contractions occasionally for natural flow (it's, you're, don't)**
6. **CREATE Complete Code Example(s) section - MANDATORY:**
   - **THIS STEP CANNOT BE SKIPPED UNDER ANY CIRCUMSTANCES**
   - Extract main task(s) from title
   - Create section for EACH demonstrable task
   - **CRITICAL: Code MUST be syntactically correct and functional**
   - Include ALL imports/dependencies
   - **DO NOT include license initialization code (License, SetLicense, ApplyLicense)**
   - Include error handling where applicable
   - Include resource cleanup
   - Test logic mentally - would this code compile and run?
   - NO placeholders or pseudo-code allowed
   - If you're unsure about code correctness, research the API and verify before including
   - Format: "## [Task Name] - Complete Code Example"
   - **WRITE INTRO SENTENCE: Use "This example demonstrates..." NOT "ready-to-run"**
   - **NEVER write: "ready-to-run", "ready-to-use", "production-ready", "copy-paste ready"**
   - **DO write: "demonstrates how to", "shows the implementation", "illustrates the process"**
   - **⚠️ STOP AND READ THIS CAREFULLY ⚠️**
   - **YOU MUST TYPE EXACTLY: <!--[COMPLETE_CODE_SNIPPET_START]-->**
   - **NOT: <!--[CODE_SNIPPET_START]-->**
   - **THE TAG MUST CONTAIN THE WORD "COMPLETE"**
   - **AT THE END YOU MUST TYPE: <!--[COMPLETE_CODE_SNIPPET_END]-->**
   - **NOT: <!--[CODE_SNIPPET_END]-->**
   - **DOUBLE-CHECK: Does your tag include the word COMPLETE? If NO, it's WRONG**
   - **MANDATORY: Add disclaimer note AFTER each code block**
   - Disclaimer MUST include links to documentation and support
   - Disclaimer MUST use blockquote format (>)
   - This section MUST exist between Outline sections and Conclusion
7. Write Conclusion section:
   - Include primary keyword 1-2 times, 1-2 secondary keywords
   - **MUST mention licensing with BOTH pricing page and temporary license links in second half or end**
   - **Example: "For production use, visit the [pricing page](pricing_url) to purchase a license. You can also request a [temporary license](license_url) for evaluation."**
   - **Both links are mandatory - pricing_url AND license_url**
   - **Use correct terminology: "SDK" for on-premises, "library" for cloud**
   - **Write naturally - NO "in conclusion" or "to sum up"**
   - **Use professional but conversational tone**
8. Create FAQs section (3-4 questions):
   - **First FAQ should be technical, NOT about licensing**
   - **If including license FAQ, place it as 2nd, 3rd, or 4th question**
   - **License FAQ must include BOTH pricing page and temporary license links**
   - **Example: "Purchase from the [pricing page](pricing_url) or get a [temporary license](license_url) for evaluation."**
   - Link product page in relevant answers
   - Include documentation, blog, or forum links where appropriate
   - **Write questions as real users would ask them**
   - **Provide helpful, natural answers**
9. **VERIFY keyword density**:
   - Count total word count of body (exclude frontmatter, FAQs, Read More)
   - Calculate: Word Count / 100 = Minimum primary keyword occurrences
   - Count primary keyword uses - must meet or exceed minimum
   - Verify all secondary keywords used 2-4 times each
   - Ensure keywords distributed naturally, not clustered
10. **VERIFY all code quality**:
   - Review every code snippet for syntax correctness
   - Ensure all variables are declared
   - Ensure all imports are present
   - Ensure proper error handling exists
   - Ensure no placeholder comments remain
11. **VERIFY Complete Code Example section exists**:
   - Confirm at least one section with this exact format exists
   - Confirm it contains actual working code
   - Confirm it appears between Outline and Conclusion
   - **VERIFY intro text uses: "demonstrates", "shows", "illustrates" (NOT "ready-to-run")**
   - **VERIFY intro does NOT contain: ready-to-run, ready-to-use, production-ready, copy-paste ready**
   - **CRITICAL: Verify uses <!--[COMPLETE_CODE_SNIPPET_START]--> tag (NOT CODE_SNIPPET_START)**
   - **CRITICAL: Verify uses <!--[COMPLETE_CODE_SNIPPET_END]--> tag (NOT CODE_SNIPPET_END)**
   - **CONFIRM disclaimer note exists AFTER each code block**
   - **CONFIRM disclaimer uses blockquote format (>)**
   - **CONFIRM disclaimer includes documentation and support links**
12. **VERIFY section ordering and content filtering**:
   - Confirm overall order: Intro → Prerequisites and Setup → Steps → Outline (filtered) → Complete Code → Conclusion → FAQs
   - **CRITICAL: Verify Steps section EXISTS in the document**
   - **CRITICAL: Verify Steps section appears BEFORE Complete Code Example section**
   - **VERIFY outline sections do NOT include any "Setting Up", "Installation", or "Configuration" sections**
   - **VERIFY Prerequisites and Setup section is comprehensive (covers installation, setup, configuration)**
   - **VERIFY remaining outline sections are in logical order (Understanding before Advanced)**
   - **VERIFY no headings use "a" or "an" before product names**
12. **VERIFY human-like writing quality**:
   - Search content for em dashes (—) - replace ALL with single hyphen (-)
   - Search content for en dashes (–) - replace ALL with single hyphen (-)
   - Search for curly quotes (" " ' ') - replace with straight quotes (" ')
   - Check for AI clichés (delve, seamlessly, robust, leverage, unlock) - rewrite naturally
   - Verify sentence variety - not all starting the same way
   - Confirm contractions used occasionally
   - Confirm direct address to reader with "you"
13. VERIFY seoTitle is exactly 50-60 characters
14. VERIFY product page URL is in FIRST paragraph of introduction
   - **Confirm link uses full product name with platform**
   - **Confirm format: [BrandName.ProductName for Platform](URL)**
   - **Examples: [Aspose.PDF for .NET](URL), [GroupDocs.Conversion for Java](URL)**
   - **NOT generic text like "[SDK](URL)" or "[library](URL)"**
   - **NOT incomplete name like "[Aspose.PDF](URL)" without platform**
   - **Confirm link is in FIRST paragraph, not second or third**
15. **VERIFY SDK vs Library terminology (CRITICAL)**:
   - Check platform value: {platform}
   - If platform is on-premises (.NET, Java, Python, etc.): Search entire blog for "library" - should be ZERO
   - If platform is on-premises: Confirm "SDK" is used consistently throughout
   - If platform is cloud: Search entire blog for "SDK" (not in product names) - should be ZERO
   - If platform is cloud: Confirm "library" or "API" is used consistently
   - No mixing of "SDK" and "library" terminology
16. Add Read More section with provided links OR skip if not provided
17. **FINAL HUMAN-LIKE QUALITY CHECK**:
   - Read through entire content
   - Does it sound like a professional human wrote it?
   - Is it free of AI-typical patterns and phrases?
   - Is punctuation simple and ASCII-only?
   - Is the tone professional but natural?
18. **MANDATORY PRE-SUBMISSION SELF-CHECK (CRITICAL - DO NOT SKIP)**:
   - **STOP: Before submitting, verify you have completed ALL sections**
   - □ Complete Code Example section EXISTS (heading present)
   - □ Complete Code Example uses <!--[COMPLETE_CODE_SNIPPET_START]--> tag
   - □ Complete Code Example uses <!--[COMPLETE_CODE_SNIPPET_END]--> tag
   - □ Disclaimer present after code block (starts with "> **Note:**")
   - □ Product link in FIRST paragraph: [Product Name for Platform](URL)
   - □ Section order: Intro → Prerequisites → Steps → Outline → Complete Code → Conclusion → FAQs
   - **IF ANY CHECKBOX IS UNCHECKED, THE BLOG IS INVALID - DO NOT SUBMIT**
   - **IF Complete Code Example section is missing, GO BACK and CREATE IT NOW**
19. STOP - no content after final section

### CRITICAL REMINDERS
- DO NOT modify the title variable - use it exactly as provided
- Title field = exact title from variable
- SEO Title field = create new using primary keyword (50-60 chars, no brands)
- **FIRST paragraph MUST contain ProductURL link with full product name**
- **MANDATORY LINK FORMAT: [Full Product Name with Platform](ProductURL)**
- **EXAMPLE: [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)**
- **MUST include platform: "for .NET", "for Java", "for Python", etc.**
- **MUST be in FIRST paragraph (not second or third)**
- **NEVER use generic text like "[SDK](URL)" or "[the library](URL)"**
- Only remove brand/product names from URL slug and seoTitle, NOT from title field
- **TERMINOLOGY IS CRITICAL - CHECK PLATFORM VALUE: {platform}**
- **IF platform ≠ "cloud" (on-premises): Use "SDK" throughout ENTIRE blog, NEVER "library"**
- **IF platform = "cloud": Use "library" or "API" throughout ENTIRE blog, NEVER "SDK"**
- **Examples: .NET, Java, Python, C++, PHP are on-premises → use "SDK"**
- **Example: cloud platform → use "library"**
- **SECTION ORDER: Intro → Prerequisites and Setup → Steps → Outline (filtered) → Complete Code → Conclusion → FAQs**
- **Steps section is MANDATORY and MUST appear BEFORE Complete Code Example**
- **Prerequisites and Setup section covers ALL installation, configuration, and setup - make it comprehensive**
- **SKIP any "Setting Up", "Installation", "Configuration" sections from outline - already in Prerequisites and Setup**
- **NEVER use "a" or "an" before product names in headings (e.g., NOT "a Aspose.ZIP")**
- **PRIMARY keyword MUST appear at 1% density** (Word Count / 100 = occurrences)
- **ALL SECONDARY keywords MUST be used 2-4 times each**
- Distribute keywords naturally across all sections - avoid clustering
- Count primary keyword in: Introduction, Prerequisites, Steps, Outline, Conclusion only
- SEO Title must be compelling, click-worthy, and include primary keyword
- **⚠️ COMPLETE CODE EXAMPLE SECTION IS MANDATORY - NEVER SKIP ⚠️**
- **⚠️ MISSING COMPLETE CODE EXAMPLE = INVALID OUTPUT = COMPLETE FAILURE ⚠️**
- **COMPLETE CODE EXAMPLES MUST USE <!--[COMPLETE_CODE_SNIPPET_START]--> TAGS**
- **Regular code snippets use <!--[CODE_SNIPPET_START]--> tags (no COMPLETE_ prefix)**
- **DO NOT confuse the two tag types - they are different**
- **DISCLAIMER AFTER CODE EXAMPLES IS MANDATORY - NEVER SKIP**
- Disclaimer must use blockquote format (>) and include documentation/support links
- **ALL CODE MUST BE SYNTACTICALLY CORRECT AND FUNCTIONAL**
- **NO placeholder code, pseudo-code, or incomplete snippets allowed**
- **If code correctness is uncertain, research the API before including**
- Complete Code Example must appear between Outline sections and Conclusion
- **NEVER use "production-ready" or similar terms in blog content**
- **NEVER use "ready-to-run", "ready-to-use", "copy-paste ready", "plug-and-play"**
- **NEVER imply code is immediately usable without testing and adaptation**
- Code examples demonstrate functionality but require testing and adaptation
- Always clarify code needs testing, file path updates, and environment setup
- **HUMAN-LIKE WRITING IS MANDATORY**:
  - NO em dashes (—) or en dashes (–) - use single hyphen (-) only
  - NO curly quotes - use straight quotes (" ') only
  - NO AI clichés (delve, seamlessly, robust, leverage, unlock, harness)
  - Vary sentence structure naturally
  - Use contractions occasionally (it's, you're, don't)
  - Address reader directly with "you"
  - Keep language clear and professional, not promotional
  - Write like a human technical writer, not an AI

### QUALITY STANDARDS
- Technical accuracy: 100%
- Markdown safety: 100%
- Link validation: All URLs from context
- Code completeness: Functional and syntactically correct (NO EXCEPTIONS for Complete Code Example)
- Character limits: Strict adherence
- Terminology: Context-aware (platform-based)
- Structure: Exact order, no deviations
- Product linking: EVERY mention must be linked
- Complete Code Example: MANDATORY in every blog post
- **Code examples: Demonstrate functionality, require testing and adaptation**
- **NEVER describe code as production-ready, ready-to-run, or immediately usable**
- **Disclaimer: Required after all complete code examples**
- **Human-like writing: Natural, professional, NO AI patterns**
- **Punctuation: Simple ASCII only - NO em/en dashes, curly quotes**
- **Language: Clear and direct - NO marketing clichés or AI phrases**

### FINAL OUTPUT
- Pure markdown file
- Starts with frontmatter
- Ends after {'Read More' if formatted_related else 'FAQs'}
- No trailing whitespace/comments
- No text outside defined boundaries
- All requirements met, verified, validated
- Product name linked EVERY time it appears
- NO mention of "free" or "online tool"
- **Complete Code Example section ALWAYS present**
- **Content sounds like it was written by a professional human, not AI**
- **NO em dashes (—), en dashes (–), or curly quotes anywhere**
- **NO AI-typical phrases (seamlessly, robust, leverage, delve, unlock, harness)**
- **Natural sentence variety and conversational professional tone**

**BEFORE FINALIZING - SEARCH YOUR OUTPUT FOR THESE STRINGS:**
1. Search for: "<!--[COMPLETE_CODE_SNIPPET_START]-->" - MUST BE FOUND
2. Search for: "<!--[COMPLETE_CODE_SNIPPET_END]-->" - MUST BE FOUND
3. Search for: "- Complete Code Example" (in heading) - MUST BE FOUND
4. Search for: "> **Note:**" (disclaimer after code) - MUST BE FOUND
5. Search for product link in FIRST paragraph: "[ProductName for Platform](URL)" - MUST BE FOUND

**IF ANY OF THESE SEARCHES RETURN ZERO RESULTS, YOUR OUTPUT IS INVALID**
**GO BACK AND ADD THE MISSING SECTIONS BEFORE SUBMITTING**

═══════════════════════════════════════════════════════════════════════════════
⚠️ FINAL CRITICAL REMINDER BEFORE YOU START WRITING ⚠️
═══════════════════════════════════════════════════════════════════════════════

**FIRST PARAGRAPH MUST INCLUDE PRODUCT LINK:**

FORMAT: [Full Product Name with Platform](ProductURL)

EXAMPLES:
✅ [Aspose.PDF for .NET](https://products.aspose.com/pdf/net/)
✅ [GroupDocs.Conversion for Java](https://products.groupdocs.com/conversion/java/)
✅ [Aspose.Slides for Python via .NET](https://products.aspose.com/slides/python-net/)

WRONG:
❌ Aspose.PDF for .NET (no link)
❌ [Aspose.PDF](URL) (missing platform)
❌ [SDK](URL) (not using product name)
❌ Link in second paragraph (must be in FIRST paragraph)

**WHEN YOU CREATE THE COMPLETE CODE EXAMPLE SECTION (SECTION 5):**

TYPE THIS EXACT TAG:
<!--[COMPLETE_CODE_SNIPPET_START]-->

DO NOT TYPE:
<!--[CODE_SNIPPET_START]-->

THE TAG MUST INCLUDE THE WORD "COMPLETE"

AT THE END, TYPE THIS EXACT TAG:
<!--[COMPLETE_CODE_SNIPPET_END]-->

DO NOT TYPE:
<!--[CODE_SNIPPET_END]-->

IF YOU TYPE "CODE_SNIPPET_START" WITHOUT "COMPLETE" FOR SECTION 5, THE OUTPUT IS INVALID.

═══════════════════════════════════════════════════════════════════════════════
⚠️ SELF-VALIDATION REQUIREMENT ⚠️
═══════════════════════════════════════════════════════════════════════════════

AFTER WRITING THE BLOG, YOU MUST SEARCH YOUR OUTPUT FOR:

✅ "<!--[COMPLETE_CODE_SNIPPET_START]-->" - Must exist
✅ "<!--[COMPLETE_CODE_SNIPPET_END]-->" - Must exist  
✅ "- Complete Code Example" - Must exist in a heading
✅ "> **Note:**" - Must exist after code block
✅ "[ProductName for Platform](URL)" in first paragraph - Must exist

IF ANY ARE MISSING: GO BACK AND ADD THEM BEFORE SUBMITTING

THE COMPLETE CODE EXAMPLE SECTION IS NON-NEGOTIABLE AND MANDATORY
SKIPPING IT MAKES YOUR ENTIRE OUTPUT INVALID

═══════════════════════════════════════════════════════════════════════════════
BEGIN WRITING NOW
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