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
    platform: str = ""
    
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
 
    # FULL PROMPT.  /{data.get("urlPrefix")}/{url}/
    return f"""
You are an expert technical blog writer. Write a detailed, SEO-optimized blog post about "{title}" using keywords: {keywords}

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
- Em dash to hyphen
- En dash to hyphen
- Curly double quotes to straight quotes
- Curly single quotes to straight quotes
- Ellipsis to three periods
- Copyright to (c), Registered to (R), Trademark to (TM)
- Bullet to hyphen
- Degree symbol to "degrees"

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
2. Prerequisites/Installation (H2 heading - ALWAYS include)
3. Steps (H2 heading - ALWAYS include)
4. Outline Sections (Follow provided outline exactly)
5. Complete Code Example(s) (ONLY if you have actual code)
6. Conclusion (H2 heading - ALWAYS include)
7. FAQs (H2 heading - ALWAYS include)
{'8. Read More (H2 heading - ALWAYS include last)' if formatted_related else ''}

### 1. INTRODUCTION CONTENT (NO HEADING)
- Start directly with 2-3 paragraphs after frontmatter
- NO H2 heading
- **CRITICAL: The FIRST paragraph MUST contain the product page URL**
- **MANDATORY: Link format in first paragraph**: [Full Product Name with Platform](ProductURL)
- Example: "Using [Aspose.Slides for Java](https://products.aspose.com/slides/java/), developers can..."
- Example: "This guide demonstrates how [Aspose.PDF for .NET](ProductURL) enables..."
- Include at least 1 additional contextual link in subsequent paragraphs
- Use correct terminology based on platform (see Part 3)
- Natural flow, explain the topic and its value
- NEVER mention "free SDK" or "online tool"
- Clarify this is a programmatic SDK/library for local/server use
- Total: 2-3 paragraphs with product link in FIRST paragraph

### 2. PREREQUISITES/INSTALLATION (MANDATORY)
## Prerequisites
OR
## Installation

Content:
- System requirements (if applicable)
- **MUST link Download URL**: "Download the latest version from [this page](download_url)" or "Get it from the [releases page](download_url)"
- **MUST link License URL**: "Obtain a [temporary license](license_url) for evaluation" or "Get your [license](license_url)"
- Package manager command (NuGet, Maven, pip, npm, etc.)
- Installation code wrapped in tags:

<!--[CODE_SNIPPET_START]-->
```language
// Installation command
```
<!--[CODE_SNIPPET_END]-->

- **Optional: Link Documentation**: "See the [installation guide](documentation_url) for more details"
- Keep concise (2-4 paragraphs but MUST include download and license links)
- NEVER mention "free" or "online"

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
Follow the provided outline exactly:

{formatted_outline}

- Use H2/H3 headers as specified
- Include contextual links naturally
- May include code snippets with explanations
- Link classes/methods ONLY if URLs in context
- Link product name to product page URL: [Full Product Name](url)

### 5. COMPLETE CODE EXAMPLE(S) - CONDITIONAL
CRITICAL: Only create if you have actual, complete, working code

WHEN TO CREATE:
✅ You have full, working code for the task
✅ Code is copy-paste ready (no placeholders)
✅ Task can be demonstrated with code

WHEN TO SKIP:
❌ No complete code available
❌ Code would use "// ... rest of code" placeholders
❌ Task is purely conceptual

MULTIPLE TASKS HANDLING:
- Title: "Convert PDF to PNG and JPG"
  → Create sections ONLY for tasks with code:
  ## Convert PDF to PNG - Complete Code Example
  ## Convert PDF to JPG - Complete Code Example

- Title: "Convert PDF to PNG"
  → Create 1 section:
  ## Convert PDF to PNG - Complete Code Example

FORMAT (when included):
## [Specific Task] - Complete Code Example

[1-2 sentence intro]

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code
// All imports, initialization, implementation
// Production-ready, no placeholders
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

[Optional: Usage notes]

### 6. CONCLUSION (MANDATORY)
## Conclusion

- 2-3 paragraphs summarizing key points
- Include at least 1 contextual link
- MUST link product page URL with FULL product name: [Product Name](url)
- **MUST link License URL**: "Get your [license](license_url) to use in production"
- **Optional: Link Forums or Blogs**: "Explore more [tutorials](blogs_url)" or "Join our [community](forums_url)"
- Use correct terminology based on platform
- Natural closing, encourage next steps
- NEVER mention "free" or "online tool"

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
- **Suggested FAQ topics to include**:
  - "How do I get a license?" → Link License URL
  - "Where can I find more examples?" → Link Documentation or Blogs URL
  - "Where can I get support?" → Link Forums URL
  - Technical question → Link API Reference or Documentation
- Practical questions related to topic
- NEVER mention "free" or "online"

{'### 8. READ MORE (MANDATORY)' if formatted_related else '### NO READ MORE SECTION'}
{'## Read More' if formatted_related else 'Do NOT include - no related links provided.'}
{formatted_related if formatted_related else 'Blog MUST end after FAQs.'}
{'Use EXACT titles and URLs provided.' if formatted_related else ''}

═══════════════════════════════════════════════════════════════════════════════
PART 3: TERMINOLOGY RULES (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

### SDK vs LIBRARY/API TERMINOLOGY
PLATFORM-BASED DECISION:
- IF platform = "cloud" → Use "library" or "API"
- IF platform ≠ "cloud" → Use "SDK"

Platform variable: {platform}

Examples:
- Cloud: "Install the library", "The API provides"
- Non-cloud: "Install the SDK", "The SDK provides"

### PROHIBITED TERMINOLOGY
NEVER use anywhere in content:
❌ "Framework" - use "SDK", "library", "platform", "toolkit" instead
❌ "free SDK" or "free library" or "free API"
❌ "online tool" or "online app" or "web-based"
❌ "browser-based" or "no installation required"

ALWAYS use:
✅ "SDK" (if platform ≠ cloud)
✅ "library" or "API" (if platform = cloud)
✅ "programmatic solution"
✅ "install and integrate"

Apply to: introduction, prerequisites, steps, outline, code examples, conclusion, FAQs

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

### PRODUCT NAME LINKING (MANDATORY - CRITICAL)
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
ALL code snippets MUST use:

<!--[CODE_SNIPPET_START]-->
```language
// Your code here
```
<!--[CODE_SNIPPET_END]-->

### CODE SNIPPET TYPES
1. **Prerequisites/Installation**: Installation commands
2. **Steps Section**: Partial code illustrating specific actions
3. **Outline Sections**: Code chunks broken down for explanation
4. **Complete Code Examples**: FULL working code (copy-paste ready)

### COMPLETE CODE EXAMPLE REQUIREMENTS
- FULL working code for specific task
- Copy-paste ready (no "..." placeholders)
- All imports/dependencies included
- Proper initialization and error handling
- Well-commented for clarity
- Focus on ONE task per section
- Independent and standalone usable
- Use <!--[COMPLETE_CODE_SNIPPET_START]--> wrapper

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

**MANDATORY REQUIREMENT:**
- PRIMARY keyword MUST appear AT LEAST 5 TIMES in the blog post body
- Count includes: Introduction, Prerequisites, Steps, Outline sections, Conclusion
- Does NOT count: Frontmatter, FAQs, Read More section
- Use naturally within sentences - avoid keyword stuffing
- Variations are acceptable but exact keyword should appear 5+ times
- **NEVER surround primary keyword with asterisks or make it italic/bold**
- **NEVER use markdown formatting around the primary keyword**
- Primary keyword should appear as plain text in natural sentences

**CORRECT examples:**
- "When working with {primary_keyword}, developers need to..."
- "The {primary_keyword} process involves several steps..."
- "To implement {primary_keyword} functionality..."
- "Best practices for {primary_keyword} include..."
- "Common {primary_keyword} scenarios require..."

**INCORRECT examples:**
- ❌ "When working with *{primary_keyword}*, developers..." (has asterisks)
- ❌ "The **{primary_keyword}** process involves..." (has bold)
- ❌ "To implement _{primary_keyword}_ functionality..." (has underscores)
- ❌ "Best practices for `{primary_keyword}` include..." (has backticks)

### TONE AND STYLE
- Professional but approachable
- Technical accuracy is paramount
- Clear, concise explanations
- Natural integration of all keywords (primary keyword minimum 5 times)
- **Primary keyword MUST appear as plain text without any markdown formatting (no asterisks, bold, italic, backticks)**
- Avoid over-formatting (minimal bold/lists unless needed)
- Use complete paragraphs for most sections
- Lists/bullets only when explicitly needed
- NEVER use casual or promotional language about "free" offerings

### CONTENT QUALITY
- Accurate technical information
- Practical, actionable guidance
- Real-world examples where helpful
- Clear progression from basic to advanced
- Address common use cases and challenges
- Focus on programmatic implementation, not web tools
- Ensure primary keyword density meets 5+ occurrences requirement

═══════════════════════════════════════════════════════════════════════════════
PART 7: VALIDATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

OUTPUT IS INVALID IF:
❌ Title does NOT match title variable exactly
❌ SEO Title is NOT 50-60 characters (strict enforcement)
❌ SEO Title does NOT include primary keyword
❌ SEO Title contains brand/product names
❌ Title has been modified, shortened, or adjusted in any way
❌ PRIMARY keyword appears fewer than 5 times in blog body
❌ PRIMARY keyword is surrounded by asterisks, underscores, or backticks anywhere
❌ PRIMARY keyword has any markdown formatting applied to it
❌ Description NOT 140-160 characters
❌ Summary NOT 140-160 characters
❌ URL contains product/brand name
❌ URL missing "in" before language/platform
❌ Introduction has H2 heading
❌ Product page URL (ProductURL) NOT linked in FIRST paragraph
❌ Prerequisites/Installation missing
❌ Download URL NOT linked in Prerequisites/Installation
❌ License URL NOT linked anywhere (Prerequisites or Conclusion)
❌ Documentation URL NOT linked anywhere in content
❌ Fewer than 5 total contextual links from provided resources
❌ Steps, Conclusion, or FAQs missing
❌ "Complete Code Example" heading without code content
❌ Multiple task title but sections for tasks without code
{'❌ Read More section missing' if formatted_related else '❌ Read More section present'}
❌ Steps not in frontmatter
❌ FAQs not in frontmatter
❌ Code snippet lacks wrapper tags
❌ Complete Code Example has placeholders
❌ Text before frontmatter or after {'Read More' if formatted_related else 'FAQs'}
❌ Outline sections skipped
❌ Wrong terminology for platform type
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
❌ Product name appears WITHOUT product page link

### PRE-SUBMISSION VERIFICATION
Before submitting, manually verify:
□ Title: EXACT match to title variable - NO modifications
□ SEO Title: 50-60 characters (count manually including spaces)
□ SEO Title: Includes primary keyword naturally
□ SEO Title: NO brand/product names included
□ SEO Title: Compelling and click-worthy
□ Title NOT modified, shortened, or adjusted
□ PRIMARY keyword used at least 5 times in blog body
□ PRIMARY keyword appears as PLAIN TEXT (no asterisks, bold, italic, backticks)
□ Primary keyword counted in: Intro, Prerequisites, Steps (explanations), Outline, Conclusion
□ Description: 140-160 chars
□ Summary: 140-160 chars
□ URL: Uses "in" before language, no brands (URL only - not title)
□ Brand/product names KEPT in title field only (not in seoTitle)
□ **CRITICAL: Product page URL (ProductURL) linked in FIRST paragraph of introduction**
□ **RESOURCE LINKS VERIFICATION (CRITICAL)**:
  □ Product Page URL linked in FIRST paragraph (MANDATORY)
  □ Product Page URL linked at least 3 times total (intro, sections, conclusion, FAQs)
  □ Download URL linked in Prerequisites/Installation section
  □ License URL linked in Prerequisites or Conclusion
  □ Documentation URL linked at least once (Prerequisites, Steps, or Outline)
  □ API Reference URLs linked when mentioning classes/methods (if available)
  □ MINIMUM 5 total contextual links from provided resources
□ Introduction: No H2, has paragraph content
□ Prerequisites/Installation: Included with setup
□ Correct terminology: SDK or library/API based on platform
□ "Framework" NEVER used
□ "free SDK/library/API" NEVER used
□ "online tool/app" NEVER used
□ Product page: Full name with platform as anchor
□ Product linked EVERY time it's mentioned
□ API links: Only if URLs in context
□ NO links in backticks/code literals
□ All URLs verified in context
□ Steps: Mention classes/methods (link if URL exists)
□ Complete Code: Only where actual code included
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
1. Start with frontmatter:
   - USE EXACT title from variable for title field
   - CREATE compelling seoTitle using primary keyword (50-60 chars, NO brand names)
   - Verify seoTitle character count manually
2. Write introduction content:
   - **CRITICAL: FIRST paragraph MUST contain product page URL link**
   - Format: [Full Product Name with Platform](ProductURL) in first paragraph
   - Add 1-2 more paragraphs with natural flow
   - Include primary keyword naturally
3. Create Prerequisites/Installation section (include primary keyword naturally)
4. Write Steps section (4-6 actionable steps, use primary keyword in explanations)
5. Follow outline sections exactly as provided (integrate primary keyword naturally)
6. Add Complete Code Example(s) ONLY if you have code
7. Write Conclusion section (link product page, include primary keyword)
8. Create FAQs section (3-4 questions, link product page in answers)
9. VERIFY primary keyword appears at least 5 times in body (not counting FAQs/Read More)
10. VERIFY seoTitle is exactly 50-60 characters
11. VERIFY product page URL is in FIRST paragraph of introduction
12. Add Read More section with provided links OR skip if not provided
13. STOP - no content after final section

### CRITICAL REMINDERS
- DO NOT modify the title variable - use it exactly as provided
- Title field = exact title from variable
- SEO Title field = create new using primary keyword (50-60 chars, no brands)
- **FIRST paragraph MUST contain ProductURL link with full product name**
- Only remove brand/product names from URL slug and seoTitle, NOT from title field
- PRIMARY keyword MUST appear 5+ times in blog body naturally
- Count primary keyword in: Introduction, Prerequisites, Steps, Outline, Conclusion only
- SEO Title must be compelling, click-worthy, and include primary keyword

### QUALITY STANDARDS
- Technical accuracy: 100%
- Markdown safety: 100%
- Link validation: All URLs from context
- Code completeness: Production-ready or skip
- Character limits: Strict adherence
- Terminology: Context-aware (platform-based)
- Structure: Exact order, no deviations
- Product linking: EVERY mention must be linked

### FINAL OUTPUT
- Pure markdown file
- Starts with frontmatter
- Ends after {'Read More' if formatted_related else 'FAQs'}
- No trailing whitespace/comments
- No text outside defined boundaries
- All requirements met, verified, validated
- Product name linked EVERY time it appears
- NO mention of "free" or "online tool"

═══════════════════════════════════════════════════════════════════════════════
BEGIN WRITING NOW
═══════════════════════════════════════════════════════════════════════════════
"""

def get_title_prompt(topic: str, product: str, keywords: str ) -> str:
      
    return f"""
Generate one short, SEO-optimized blog title.
Topic: "{topic}"
Product: "{product}"
Keywords: {keywords}

CRITICAL RULES:
- Keep under 60 characters
- Sound natural and human-written
- Include 1-2 keywords if possible
- DO NOT change, modify, or alter the product name in any way
- Use the EXACT product name as provided: "{product}"
- Do NOT remove dots, hyphens, or any punctuation from the product name
- Do NOT use colons (:), slashes (/), pipes (|), quotes, or any special characters that might break Markdown
- Return ONLY the plain title text, with no commentary or formatting

PRODUCT NAME PROTECTION:
- Product name must appear exactly as: "{product}"
- No substitutions: ".NET" stays ".NET", not "dotnet" or "NET"
- No removals: "Aspose.CAD" stays "Aspose.CAD", not "Aspose CAD"
- No additions: Don't add extra words to the product name

Return ONLY the plain title text.
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