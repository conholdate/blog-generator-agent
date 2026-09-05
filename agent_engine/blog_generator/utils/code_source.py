"""
Code-source selector for the single source-of-truth snippet.

Tries to retrieve a real, LLM-verified example from the product's
Example-Agent repo first; falls back to LLM-generated code whenever there
is no registered repo, no verified match, or retrieval errors out.

Strictly additive over ``generate_code_snippet()``: a retrieval failure
must NEVER abort a run - it degrades to generation, exactly as if this
module did not exist. Only a generation failure (``None`` returned here)
still aborts, same as before.
"""
from __future__ import annotations

import re
import traceback
from typing import Dict, List, Optional

from config import settings
from utils.code_snippet import generate_code_snippet


# ── Retrieved-code sanitizer ──────────────────────────────────────────────────
# The Example-Agent repos carry machine-generated metadata inside the file's
# leading comment block (Title / Keywords / Common Searches / Developer Intent /
# Use Cases) and `(lifecycle rule: ...)` annotations inside inline comments -
# scaffolding for the code-generation tooling, not for a blog reader. Strip it,
# but NEVER touch a line of actual code: only pure `//` comment lines are ever
# dropped or edited, and a final guard discards the whole result if the set of
# non-comment code lines changed at all.
_COMMENT_LINE_RE = re.compile(r"^\s*//")
_JUNK_LABEL_RE = re.compile(
    r"^\s*//\s*(?:Title|Keywords|Common Searches|Developer Intent|Use Cases)\b\s*:",
    re.IGNORECASE,
)
_DESC_RE = re.compile(r"^\s*//\s*Description\s*:\s*(.+?)\s*$", re.IGNORECASE)
# Matches `(rule: ...)` / `(lifecycle rule: ...)` allowing one level of nested
# parens, e.g. `(lifecycle rule: Workbook.Save(string, SaveOptions))`.
_RULE_PAREN_RE = re.compile(
    r"\s*\((?:lifecycle\s+)?rule:\s*[^()]*(?:\([^()]*\)[^()]*)*\)",
    re.IGNORECASE,
)


def _code_lines(text: str) -> List[str]:
    """The actual code: non-blank lines that are not pure `//` comment lines."""
    return [
        s
        for s in (ln.strip() for ln in text.splitlines())
        if s and not s.startswith("//")
    ]


def _sanitize_retrieved_code(code: str) -> str:
    """Remove repo-internal metadata noise from a retrieved example without
    ever altering a line of real code.

    Kept: `// Description:` and every ordinary inline comment.
    Removed: leading `// Title/Keywords/Common Searches/Developer Intent/
    Use Cases:` lines, `(lifecycle rule: ...)` parentheticals inside comments,
    and an in-body comment that only repeats the Description text.

    Hard guarantee: if `_code_lines()` would differ from the input in any way,
    the original string is returned unchanged.
    """
    if not code or "//" not in code:
        return code

    original = code
    description_norm: Optional[str] = None
    seen_code = False
    out: List[str] = []

    for ln in code.splitlines():
        is_comment = bool(_COMMENT_LINE_RE.match(ln))
        stripped = ln.strip()

        if not seen_code and stripped and not is_comment:
            seen_code = True

        # Non-comment line (or a comment after code has started elsewhere):
        # never modified, only comment lines below this point are.
        if not is_comment:
            out.append(ln)
            continue

        # 1. Drop junk metadata labels - only inside the leading comment block.
        if not seen_code and _JUNK_LABEL_RE.match(ln):
            continue

        # Remember the Description value (which we keep) to catch its later echo.
        if not seen_code:
            m = _DESC_RE.match(ln)
            if m:
                description_norm = re.sub(r"\s+", " ", m.group(1)).strip().lower()

        # 2. Drop an in-body comment that just repeats the Description verbatim.
        if description_norm is not None:
            body = re.sub(r"^\s*//\s*", "", ln)
            if re.sub(r"\s+", " ", body).strip().lower() == description_norm:
                continue

        # 3. Strip `(lifecycle rule: ...)` annotations from the comment.
        out.append(_RULE_PAREN_RE.sub("", ln).rstrip())

    result = "\n".join(out).lstrip("\n")

    if _code_lines(result) != _code_lines(original):
        print(
            "⚠️  Code sanitizer would have altered a code line - keeping the "
            "original snippet unchanged.",
            flush=True,
        )
        return original
    return result


async def get_code_snippet(
    brand: str,
    topic: str,
    primary_keyword: str,
    platform: str,
    product_name: str,
    context: str,
    outline: Optional[List[str]] = None,
    is_cloud: bool = False,
    max_retries: int = 3,
    metrics=None,
) -> Optional[Dict[str, str]]:
    """
    Return ``{"language", "code"[, "source"]}`` for the post's code snippet,
    or ``None`` only when BOTH retrieval and generation fail.

    ``source`` (present only for retrieved code) carries provenance:
    ``{repository, category, file, brand, product, platform}``.
    """
    retrieved = await _try_retrieve(
        brand=brand,
        topic=topic,
        primary_keyword=primary_keyword,
        platform=platform,
        product_name=product_name,
        outline=outline,
        metrics=metrics,
    )
    if retrieved:
        return retrieved

    print("💻 Using LLM-generated code snippet...", flush=True)
    return await generate_code_snippet(
        topic=topic,
        primary_keyword=primary_keyword,
        platform=platform,
        context=context,
        outline=outline,
        is_cloud=is_cloud,
        max_retries=max_retries,
        metrics=metrics,
    )


async def _try_retrieve(
    brand: str,
    topic: str,
    primary_keyword: str,
    platform: str,
    product_name: str,
    outline: Optional[List[str]],
    metrics=None,
) -> Optional[Dict[str, str]]:
    """Best-effort retrieval. Any failure returns None so the caller falls back."""
    try:
        from code_retrieval.retrieval_llm import retrieve_example_llm
    except Exception as e:  # import-time failure must not break the pipeline
        print(f"⚠️  Code retrieval unavailable ({e}); using generation.", flush=True)
        return None

    print("🔎 Checking for a verified repo example...", flush=True)
    try:
        result = await retrieve_example_llm(
            brand=brand,
            product_name=product_name,
            platform=platform,
            topic=topic,
            primary_keyword=primary_keyword,
            outline=outline or [],
            token=settings.REPO_PAT,
        )
    except Exception as e:
        print(f"⚠️  Code retrieval errored ({e}); falling back to generation.", flush=True)
        traceback.print_exc()
        return None

    _record_retrieval_usage(result, metrics)

    selected = result.get("selected") or {}
    if result.get("confidence") == "LLM_VERIFIED" and selected.get("code"):
        src = selected.get("source", {})
        print(
            f"✅ Using verified repo example: {src.get('repository')}/{src.get('file')} "
            f"(category: {src.get('category')})",
            flush=True,
        )
        return {
            "language": selected.get("language", ""),
            "code": _sanitize_retrieved_code(selected["code"]),
            "source": src,
        }

    print(f"ℹ️  No verified repo example ({result.get('reason', 'n/a')}); using generation.", flush=True)
    return None


def _record_retrieval_usage(result: dict, metrics) -> None:
    """Fold the pick + verify LLM token usage into metrics when available.

    Only the final pick attempt's usage is exposed by retrieve_example_llm,
    so this can slightly undercount when the re-pick loop ran - acceptable
    for a best-effort side channel.
    """
    if metrics is None:
        return
    total_in = total_out = 0
    for key in ("pick", "verification"):
        usage = (result.get(key) or {}).get("token_usage") or {}
        total_in += usage.get("input_tokens", 0) or 0
        total_out += usage.get("output_tokens", 0) or 0
    if total_in or total_out:
        try:
            metrics.record_llm_usage(
                input_tokens=total_in,
                output_tokens=total_out,
                caller="code-retrieval",
            )
        except Exception as e:
            print(f"⚠️  Could not record retrieval token usage (non-fatal): {e}", flush=True)
