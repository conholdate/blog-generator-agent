import re
from services.LLMservice import llm_service  # Use centralized service

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


async def fix_meta_description_with_llm(bad_description: str) -> str | None:
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

        # ═══════════════════════════════════════════════════════════════════
        # USING AGENT-BASED APPROACH (works with self-hosted LLM)
        # ═══════════════════════════════════════════════════════════════════
        try:
            result = await llm_service.run_agent(
                instructions=instructions,
                context="Rewrite the meta description above.",
                agent_name="meta-description-fixer",
                temperature=0.7,
                max_turns=1
            )
            
            candidate = result.final_output.strip().strip('"').strip("'")
            
            # Validate response
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
        # ═══════════════════════════════════════════════════════════════════

        print(f"  [Attempt {attempt}/{MAX_RETRIES}] New length: {len(candidate)} — '{candidate[:60]}...'")

        if is_valid_meta_description(candidate):
            print(f"  ✅ Valid meta description on attempt {attempt}.")
            return candidate

        # Feed the latest attempt back for the next retry
        current = candidate

    print(f"  ❌ Could not fix meta description after {MAX_RETRIES} attempts.")
    return None


# ── Main public function ──────────────────────────────────────────────────────

async def validate_and_fix_meta_description(blog_content: str) -> tuple[str, bool]:
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

    fixed_description = await fix_meta_description_with_llm(description)

    if fixed_description is None:
        print("❌ Fix failed. Returning original content unchanged.")
        return blog_content, False

    updated_content = replace_meta_description(blog_content, fixed_description)
    print(f"✅ Meta description fixed: {len(fixed_description)} chars.")
    return updated_content, True

