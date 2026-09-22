"""
Section-aware editing for BlogOrchestrator.revise_blog_draft().

Locates frontmatter and markdown sections in an already-generated draft,
classifies a human instruction against them, and applies ONE scoped edit -
by slicing/splicing the ORIGINAL raw text, never by reparsing-and-redumping
the document.

Why raw slicing, not frontmatter.dumps() / a rebuilt document: confirmed
python-frontmatter's `post.content` silently drops the blank line Hugo's
convention puts between the closing '---' and the body, and a full
frontmatter.dumps() round-trip can reformat untouched YAML (e.g. an inline
list `["A"]` becomes a block list). Reassembling the file from any
parsed/re-serialized form would drift formatting on every single revision,
even ones nowhere near frontmatter - the same class of bug this feature
exists to close, one layer lower. So the parsers here (python-frontmatter,
markdown-it-py) are used ONLY to locate line ranges and validate
names/fields; every write happens as a line-range splice on the untouched
original text.

Line-indexing convention: every line number in this module indexes into
`raw.split('\\n')` (never `.splitlines()` - that also breaks on exotic
Unicode line separators markdown-it-py does not treat as line breaks,
which would silently desync the two side's line numbering). `'\\n'.join`
of that same list reproduces the original text exactly, for any string -
so splicing is always a plain list slice-and-join.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Optional

import frontmatter
from markdown_it import MarkdownIt

from services.LLMservice import llm_service
from utils.helpers import (
    clean_ai_generated_markdown,
    repair_code_fences,
    strip_snippet_markers,
    validate_markdown_links,
)

_FRONTMATTER_DELIM_RE = re.compile(r'^-{3}\s*$')  # matches utils/helpers.py's own convention
_HEADING_LINE_RE = re.compile(r'^(#{1,6})(\s+)(.*?)(\s*\{#[\w-]+\}\s*)?$')
_FOLDED_SCALAR_VALUES = {'', '|', '>', '|-', '>-', '|+', '>+'}

MAX_CLASSIFY_RETRIES = 3
_EMPTY_USAGE = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


class SectionEditError(Exception):
    """Raised for anything that should fail the revision closed rather than
    guess - an unmatched target, an ambiguous match, a frontmatter value
    that isn't a simple single-line scalar. Callers catch this and report it
    via revise_status.json instead of writing a partial/corrupted draft."""


@dataclass(frozen=True)
class FrontmatterBlock:
    open_line: int            # index of the opening '---'
    close_line: int           # index of the closing '---'
    body_start_line: int      # first line of the body (close_line + 1)
    metadata: dict            # parsed YAML, for lookups only - never re-dumped


@dataclass(frozen=True)
class Section:
    index: int                 # position in the returned list - the ONLY thing
                                # a classifier ever targets, never heading text,
                                # since heading text is not guaranteed unique
    heading_text: str          # "" for the synthetic "Intro" section
    level: int                 # 0 for Intro, 1-6 for h1-h6
    line_start: int            # inclusive - the heading line itself (0 for Intro)
    line_end: int              # exclusive - first line of the next section, or EOF


# ─────────────────────────────────────────────────────────────────────────
# Locating frontmatter and sections (read-only - never mutates `lines`)
# ─────────────────────────────────────────────────────────────────────────

def locate_frontmatter(lines: list[str]) -> FrontmatterBlock:
    """Find the opening/closing '---' delimiter lines by literal scan - a
    fixed 2-line format, not the kind of thing a hand-rolled search gets
    subtly wrong the way heading detection would. The YAML between them is
    parsed with python-frontmatter (reusing the existing dependency) purely
    for lookups - its `.content`/`.dumps()` output is never used here."""
    if not lines or not _FRONTMATTER_DELIM_RE.match(lines[0]):
        raise SectionEditError(
            "Draft does not start with a frontmatter '---' block - refusing to edit."
        )

    close_line = None
    for i in range(1, len(lines)):
        if _FRONTMATTER_DELIM_RE.match(lines[i]):
            close_line = i
            break
    if close_line is None:
        raise SectionEditError(
            "Draft's frontmatter block has no closing '---' - refusing to edit."
        )

    raw = "\n".join(lines)
    try:
        metadata = frontmatter.loads(raw).metadata
    except Exception as e:
        raise SectionEditError(f"Frontmatter failed to parse as YAML: {e}") from e

    return FrontmatterBlock(
        open_line=0,
        close_line=close_line,
        body_start_line=close_line + 1,
        metadata=metadata,
    )


_md = MarkdownIt()


def parse_sections(lines: list[str], body_start_line: int) -> list[Section]:
    """Parse the body (lines[body_start_line:]) into an ordered list of
    Sections using markdown-it-py's block tokenizer - NOT regex/string
    splitting, so a heading-looking line inside a fenced code block or a
    link/image title is never mistaken for a real heading (verified against
    markdown-it-py 4.2.0 with both cases, including a real generated draft
    whose sample code contains '# comment' lines).

    A section's end is the start of the next heading at the SAME OR
    SHALLOWER level, so a nested '###' is included in its parent '##'s
    range rather than treated as a sibling. Any non-blank text before the
    first heading becomes a synthetic "Intro" section so instructions like
    "rewrite the intro" have a real target.

    Returned line numbers are ABSOLUTE indices into the full-file `lines`
    list passed in (body_start_line is folded in here), so callers never
    have to remember to add an offset.
    """
    body_lines = lines[body_start_line:]
    body_text = "\n".join(body_lines)
    tokens = _md.parse(body_text)

    headings: list[tuple[int, int, str]] = []  # (local line, level, text)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.map:
            level = int(tok.tag[1])  # 'h2' -> 2
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            text = inline.content.strip() if inline is not None and inline.type == "inline" else ""
            headings.append((tok.map[0], level, text))

    sections: list[Section] = []

    first_heading_local = headings[0][0] if headings else len(body_lines)
    if any(ln.strip() for ln in body_lines[:first_heading_local]):
        sections.append(Section(
            index=0, heading_text="Intro", level=0,
            line_start=body_start_line, line_end=body_start_line + first_heading_local,
        ))

    for pos, (local_line, level, text) in enumerate(headings):
        local_end = len(body_lines)
        for nxt_local, nxt_level, _ in headings[pos + 1:]:
            if nxt_level <= level:
                local_end = nxt_local
                break
        sections.append(Section(
            index=len(sections), heading_text=text, level=level,
            line_start=body_start_line + local_line, line_end=body_start_line + local_end,
        ))

    return sections


def build_post_context(fm: FrontmatterBlock, sections: list[Section], lines: list[str]) -> str:
    """A short, READ-ONLY reference block handed to every generative rewrite
    (rewrite_section/rewrite_field/generate_new_heading) alongside the one
    section/field/heading they're actually allowed to touch. Those calls are
    deliberately scoped to see nothing else in the post - which closed one
    bug class (accidentally touching other sections) but opened another:
    the new content has nothing to stay on-topic or on-voice with. This
    gives just enough - title, meta description, summary, keywords, the
    intro, and the other section headings for structural orientation - to
    fix that, without handing over full section bodies (which would put us
    right back to "whole document sent to the LLM").

    Callers must frame this as reference-only in the prompt and make clear
    it must never be copied or repeated into the edited output."""

    def _field(name: str) -> Optional[str]:
        val = fm.metadata.get(name)
        if val is None:
            return None
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return str(val)

    parts = []
    if (title := _field("title")):
        parts.append(f"Title: {title}")
    if (description := _field("description")):
        parts.append(f"Meta description: {description}")
    if (summary := _field("summary")):
        parts.append(f"Summary: {summary}")
    if (tags := _field("tags") or _field("keywords")):
        parts.append(f"Keywords/tags: {tags}")

    intro = next((s for s in sections if s.level == 0), None)
    if intro is not None:
        intro_text = "\n".join(lines[intro.line_start:intro.line_end]).strip()
        if intro_text:
            parts.append(f"Intro paragraph: {intro_text}")

    other_headings = [s.heading_text for s in sections if s.level > 0]
    if other_headings:
        parts.append("Other section headings in this post, for structural orientation only: " + " | ".join(other_headings))

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────
# Classifying the instruction - one small, tightly-scoped LLM call that
# sees only the instruction, the heading list, and the frontmatter field
# names. NEVER the body. Follows this codebase's existing convention
# (code_retrieval/llm_judge.py) of a labeled plain-text response parsed by
# regex and an index instead of free-text targets, rather than asking for
# raw JSON - the same reasoning applies here: an integer either indexes a
# real section or it doesn't, it can't be a plausible-but-wrong paraphrase
# of a heading.
# ─────────────────────────────────────────────────────────────────────────

_KIND_RE = re.compile(r'KIND:\s*(DETERMINISTIC|GENERATIVE|REJECT)', re.IGNORECASE)
_OP_RE = re.compile(
    r'OPERATION:\s*(remove_section|rename_heading|replace_text|add_tag|remove_tag|set_field|rewrite_section|NONE)',
    re.IGNORECASE,
)
_SECTION_IDX_RE = re.compile(r'SECTION_INDEX:\s*(\d+|NONE)', re.IGNORECASE)
_FIELD_RE = re.compile(r'FIELD_NAME:\s*(.+)', re.IGNORECASE)
_OLD_TEXT_RE = re.compile(r'OLD_TEXT:\s*(.+)', re.IGNORECASE)
_NEW_TEXT_RE = re.compile(r'NEW_TEXT:\s*(.+)', re.IGNORECASE)
_REASON_RE = re.compile(r'REASON:\s*(.+)', re.IGNORECASE)


def _build_classify_prompt(instruction: str, sections: list[Section], fm_fields: list[str]) -> str:
    section_list = "\n".join(
        f"[{s.index}] ({'Intro' if s.level == 0 else 'H' + str(s.level)}) {s.heading_text}"
        for s in sections
    )
    field_list = ", ".join(fm_fields) if fm_fields else "(none)"
    return f"""You are routing a single human edit instruction for a blog post to the right automated handler. You do NOT see the post body - only its structure below. Be conservative: only pick DETERMINISTIC or GENERATIVE when the instruction clearly targets exactly ONE section or ONE frontmatter field from the lists below. Anything spanning multiple sections, multiple fields, or that doesn't map cleanly to one of the operations must be REJECT.

Sections (reference ONLY by the bracketed index, never by typing out the heading text yourself):
{section_list}

Frontmatter fields: {field_list}

Operations:
- remove_section: delete a named section entirely. Needs SECTION_INDEX.
- rename_heading: change only a section's heading title. Needs SECTION_INDEX. If the instruction gives (or clearly implies) the exact new title, also give NEW_TEXT and set KIND: DETERMINISTIC. If the instruction asks to reword/rewrite/improve/change the heading WITHOUT giving exact new wording, set NEW_TEXT: NONE and KIND: GENERATIVE - the system will generate an appropriate new heading itself. Do NOT reject just because exact wording is missing.
- replace_text: replace one EXACT quoted/specific piece of text with another, anywhere in the body. Needs OLD_TEXT and NEW_TEXT. Only use this when the instruction gives or clearly implies an exact string, not a vague description.
- add_tag / remove_tag: add or remove one tag from frontmatter tags. Needs NEW_TEXT (the tag).
- set_field: change ONE frontmatter field to an exact new value (short scalar values only - not the body, not a multi-line field). Needs FIELD_NAME and NEW_TEXT.
- rewrite_section: reword/shorten/expand/improve ONE section's content (not its heading). Needs SECTION_INDEX. If the instruction targets a frontmatter field's wording (e.g. "make the description catchier"), use FIELD_NAME instead of SECTION_INDEX.
- REJECT: use OPERATION: NONE. Use this whenever the instruction touches more than one section/field, asks for something structural like reordering sections, is too vague to map to exactly one target, or names a section/field that doesn't appear in the lists above.

When REJECTing, your REASON must end with ONE concrete example instruction that WOULD be accepted instead - naming an exact heading or field from the lists above, not a placeholder. If the instruction named several targets, pick just the first one for the example (e.g. an instruction spanning three headings: "Try instead: apply this to one heading at a time, e.g. \\"Convert the heading '<exact heading from the list>' to title case.\\""). This is guidance text shown directly to the human who wrote the instruction, not something the system parses - it must be a plain, ready-to-paste instruction they could send right back.

Instruction: {instruction}

Respond in EXACTLY this format and nothing else, one line per field, using NONE for anything that doesn't apply:
KIND: DETERMINISTIC or GENERATIVE or REJECT
OPERATION: remove_section or rename_heading or replace_text or add_tag or remove_tag or set_field or rewrite_section or NONE
SECTION_INDEX: <integer from the list above, or NONE>
FIELD_NAME: <one field name from the list above, or NONE>
OLD_TEXT: <exact text for replace_text, or NONE>
NEW_TEXT: <replacement text / new heading / new field value / tag name, or NONE>
REASON: <one sentence explaining the decision; if REJECT, end with the concrete example described above>"""


def _parse_classification(text: str) -> dict:
    kind_m = _KIND_RE.search(text)
    op_m = _OP_RE.search(text)
    idx_m = _SECTION_IDX_RE.search(text)
    field_m = _FIELD_RE.search(text)
    old_m = _OLD_TEXT_RE.search(text)
    new_m = _NEW_TEXT_RE.search(text)
    reason_m = _REASON_RE.search(text)

    def _clean(m, none_ok=True):
        if not m:
            return None
        val = m.group(1).strip().strip('`"\'')
        if none_ok and val.upper() == "NONE":
            return None
        return val

    if not kind_m:
        return {"kind": "reject", "operation": None, "section_index": None,
                "field_name": None, "old_text": None, "new_text": None,
                "reason": "Classifier response could not be parsed."}

    idx_val = _clean(idx_m)
    return {
        "kind": kind_m.group(1).lower(),
        "operation": _clean(op_m),
        "section_index": int(idx_val) if idx_val is not None and idx_val.isdigit() else None,
        "field_name": _clean(field_m),
        # none_ok=True: the classify prompt explicitly instructs "NONE" as
        # the sentinel for "doesn't apply" on these fields (same as
        # SECTION_INDEX/FIELD_NAME above) - none_ok=False here was a latent
        # bug: it left the literal string "NONE" in place instead of `None`,
        # which is truthy, so `not cls["new_text"]` checks (the "was NEW_TEXT
        # given?" guards used by add_tag/remove_tag/set_field/rename_heading)
        # silently passed a real op through with the 4-character text "NONE".
        "old_text": _clean(old_m, none_ok=True) if old_m else None,
        "new_text": _clean(new_m, none_ok=True) if new_m else None,
        "reason": _clean(reason_m, none_ok=False) or "",
    }


async def _complete_with_retry(prompt: str, temperature: float, max_tokens: int, label: str):
    """Same retry shape as code_retrieval/llm_judge.py's helper: a call that
    keeps failing degrades to a REJECT-shaped failure rather than crashing
    the whole revise run."""
    last_error = None
    for attempt in range(1, MAX_CLASSIFY_RETRIES + 1):
        try:
            return await llm_service.complete(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ {label} attempt {attempt}/{MAX_CLASSIFY_RETRIES} failed: {last_error}", flush=True)
    print(f"❌ {label} failed after {MAX_CLASSIFY_RETRIES} attempts. Last error: {last_error}", flush=True)
    return None, {**_EMPTY_USAGE, "error": last_error}


async def classify_instruction(instruction: str, sections: list[Section], fm_fields: list[str]) -> tuple[dict, dict]:
    """Returns (classification_dict, token_usage_dict). Never raises - a
    failed/unparseable call comes back as a REJECT classification so the
    caller's normal reject path handles it uniformly."""
    prompt = _build_classify_prompt(instruction, sections, fm_fields)
    # 400 was enough for the ~7-line labeled answer alone, but the
    # self-hosted model is a reasoning model that spends tokens on hidden
    # chain-of-thought before writing it - at 400 it sometimes hit the cap
    # mid-thought (content: None, fell back to the incomplete reasoning
    # trace, which never reached a KIND: line -> "could not be parsed").
    # 1500 leaves headroom for reasoning + the answer.
    text, usage = await _complete_with_retry(prompt, temperature=0.0, max_tokens=1500, label="revise-classifier")
    if text is None:
        return ({"kind": "reject", "operation": None, "section_index": None,
                  "field_name": None, "old_text": None, "new_text": None,
                  "reason": f"Classifier call failed: {usage.get('error', 'unknown error')}"}, usage)
    return _parse_classification(text), usage


def _validate_classification(cls: dict, sections: list[Section], fm_fields: list[str]) -> Optional[str]:
    """Re-checks the LLM's classification against the REAL section/field
    lists - the LLM's answer is a hint, never authority. Returns an error
    string if invalid, None if it checks out."""
    if cls["kind"] not in ("deterministic", "generative"):
        return None  # already reject / unparseable - nothing to validate

    op = cls["operation"]
    if op in ("remove_section", "rename_heading", "rewrite_section") or (op is None and cls["section_index"] is not None):
        idx = cls["section_index"]
        if idx is None:
            return f"Operation '{op}' requires a section but none was given."
        if not any(s.index == idx for s in sections):
            valid = ", ".join(str(s.index) for s in sections)
            return f"Section index {idx} does not exist (valid indices: {valid})."

    if op in ("set_field",) or (op == "rewrite_section" and cls["field_name"]):
        field = cls["field_name"]
        if not field:
            return f"Operation '{op}' requires a frontmatter field name but none was given."
        if field not in fm_fields:
            return f"Frontmatter field '{field}' does not exist (valid fields: {', '.join(fm_fields)})."

    if op == "replace_text" and not cls["old_text"]:
        return "replace_text requires OLD_TEXT but none was given."

    if op in ("add_tag", "remove_tag", "set_field") and not cls["new_text"]:
        return f"Operation '{op}' requires NEW_TEXT but none was given."

    # rename_heading is the one operation allowed to omit NEW_TEXT - but only
    # when the classifier flagged it GENERATIVE, meaning it deliberately left
    # the wording for the system to generate (see classify_and_apply). A
    # DETERMINISTIC rename_heading still must supply the exact new text.
    if op == "rename_heading" and cls["kind"] == "deterministic" and not cls["new_text"]:
        return "rename_heading (deterministic) requires NEW_TEXT but none was given."

    return None


# ─────────────────────────────────────────────────────────────────────────
# Deterministic operations - each fails loudly (SectionEditError) instead
# of guessing. Every function takes the full-file `lines` list and returns
# a NEW full-file `lines` list; nothing here touches text outside the
# range it's explicitly documented to change.
# ─────────────────────────────────────────────────────────────────────────

def remove_section(lines: list[str], section: Section) -> list[str]:
    # section.line_end is the next section's own line_start, which already
    # includes that section's leading blank-line separator - so slicing it
    # out leaves exactly one blank line at the seam, the same as between
    # any two ordinary sections. No special-case collapsing needed.
    return lines[:section.line_start] + lines[section.line_end:]


def rename_heading(lines: list[str], section: Section, new_title: str) -> list[str]:
    old_line = lines[section.line_start]
    m = _HEADING_LINE_RE.match(old_line)
    if not m:
        raise SectionEditError(f"Line {section.line_start} does not look like a heading: {old_line!r}")
    hashes, spacing, _old_title, anchor = m.groups()
    new_lines = list(lines)
    new_lines[section.line_start] = f"{hashes}{spacing}{new_title}{anchor or ''}"
    return new_lines


def replace_exact_text(lines: list[str], body_start_line: int, old_text: str, new_text: str) -> list[str]:
    """Exact-match replace over the WHOLE body (not just the classifier's
    guessed section) - the safety here comes from requiring exactly one
    match in the entire document, not from trusting the section guess."""
    body = "\n".join(lines[body_start_line:])
    count = body.count(old_text)
    if count == 0:
        raise SectionEditError(f"Text not found in the post body: {old_text!r}")
    if count > 1:
        raise SectionEditError(f"Text appears {count} times in the post body - ambiguous, refusing to guess which: {old_text!r}")
    new_body = body.replace(old_text, new_text, 1)
    return lines[:body_start_line] + new_body.split("\n")


def _find_field_line(lines: list[str], fm: FrontmatterBlock, field: str) -> int:
    key_re = re.compile(rf'^{re.escape(field)}\s*:', re.IGNORECASE)
    matches = [i for i in range(fm.open_line + 1, fm.close_line) if key_re.match(lines[i])]
    if not matches:
        raise SectionEditError(f"Frontmatter field '{field}' not found in the draft.")
    if len(matches) > 1:
        raise SectionEditError(f"Frontmatter field '{field}' appears more than once - refusing to guess which.")
    return matches[0]


def set_field(lines: list[str], fm: FrontmatterBlock, field: str, new_value: str) -> list[str]:
    i = _find_field_line(lines, fm, field)
    m = re.match(rf'^({re.escape(field)}\s*:\s*)(.*)$', lines[i], re.IGNORECASE)
    prefix, old_value = m.groups()
    old_value = old_value.strip()
    if old_value in _FOLDED_SCALAR_VALUES:
        raise SectionEditError(
            f"Frontmatter field '{field}' is a multi-line YAML value - not supported yet, refusing to risk corrupting it."
        )
    if old_value.startswith('"') and old_value.endswith('"'):
        rendered = f'"{new_value}"'
    elif old_value.startswith("'") and old_value.endswith("'"):
        rendered = f"'{new_value}'"
    else:
        rendered = str(new_value)
    new_lines = list(lines)
    new_lines[i] = f"{prefix}{rendered}"
    return new_lines


_INLINE_LIST_RE = re.compile(r'^(\w+\s*:\s*)\[(.*)\]\s*$')
_BLOCK_LIST_ITEM_RE = re.compile(r'^(\s*)-\s*(.*)$')


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def add_tag(lines: list[str], fm: FrontmatterBlock, tag: str) -> list[str]:
    i = _find_field_line(lines, fm, "tags")
    line = lines[i]

    m = _INLINE_LIST_RE.match(line)
    if m:
        prefix, inner = m.groups()
        items = [it.strip() for it in inner.split(",")] if inner.strip() else []
        if any(_strip_quotes(it) == tag for it in items):
            raise SectionEditError(f"Tag '{tag}' is already present.")
        quote = '"'
        if items and items[0].strip().startswith("'"):
            quote = "'"
        items.append(f"{quote}{tag}{quote}")
        new_lines = list(lines)
        new_lines[i] = f"{prefix}[{', '.join(items)}]"
        return new_lines

    if re.match(r'^\w+\s*:\s*$', line):
        j = i + 1
        block_end = j
        while block_end < fm.close_line and _BLOCK_LIST_ITEM_RE.match(lines[block_end]):
            block_end += 1
        existing = [_BLOCK_LIST_ITEM_RE.match(lines[k]).group(2) for k in range(j, block_end)]
        if any(_strip_quotes(e) == tag for e in existing):
            raise SectionEditError(f"Tag '{tag}' is already present.")
        indent = _BLOCK_LIST_ITEM_RE.match(lines[j]).group(1) if block_end > j else "  "
        new_lines = list(lines)
        new_lines[block_end:block_end] = [f"{indent}- {tag}"]
        return new_lines

    raise SectionEditError("Could not recognize the 'tags' field's format - refusing to risk corrupting frontmatter.")


def remove_tag(lines: list[str], fm: FrontmatterBlock, tag: str) -> list[str]:
    i = _find_field_line(lines, fm, "tags")
    line = lines[i]

    m = _INLINE_LIST_RE.match(line)
    if m:
        prefix, inner = m.groups()
        items = [it.strip() for it in inner.split(",")] if inner.strip() else []
        kept = [it for it in items if _strip_quotes(it) != tag]
        if len(kept) == len(items):
            raise SectionEditError(f"Tag '{tag}' not found in frontmatter tags.")
        new_lines = list(lines)
        new_lines[i] = f"{prefix}[{', '.join(kept)}]"
        return new_lines

    if re.match(r'^\w+\s*:\s*$', line):
        j = i + 1
        block_end = j
        while block_end < fm.close_line and _BLOCK_LIST_ITEM_RE.match(lines[block_end]):
            block_end += 1
        keep_lines = [k for k in range(j, block_end) if _strip_quotes(_BLOCK_LIST_ITEM_RE.match(lines[k]).group(2)) != tag]
        if len(keep_lines) == block_end - j:
            raise SectionEditError(f"Tag '{tag}' not found in frontmatter tags.")
        new_lines = lines[:j] + [lines[k] for k in keep_lines] + lines[block_end:]
        return new_lines

    raise SectionEditError("Could not recognize the 'tags' field's format - refusing to risk corrupting frontmatter.")


# ─────────────────────────────────────────────────────────────────────────
# Generative operation - the LLM only ever sees ONE section's raw text (or
# one field's raw value), never the whole document, and its reply is
# spliced back at the exact same range. Post-processing runs on the
# returned fragment only, not the whole document.
# ─────────────────────────────────────────────────────────────────────────

async def rewrite_section(lines: list[str], section: Section, instruction: str, post_context: str = "") -> tuple[list[str], dict]:
    original_text = "\n".join(lines[section.line_start:section.line_end])

    if section.level == 0:
        heading_line, body_text = None, original_text
    else:
        heading_line = lines[section.line_start]
        body_text = "\n".join(lines[section.line_start + 1:section.line_end])

    context_block = (
        f"POST CONTEXT (reference only, to keep your edit on-topic and consistent "
        f"with the rest of the post's voice/terminology - do NOT copy, repeat, or "
        f"summarize this block into your output; it is not part of the section):\n"
        f"{post_context}\n\n"
    ) if post_context else ""

    prompt = (
        "You are editing ONE section of an existing published-quality blog post. "
        "You are shown ONLY this section's body text (its heading is handled "
        "separately and is not yours to change) - apply the requested edit to it "
        "completely and precisely. Return ONLY the edited section body: no "
        "heading, no preamble, no explanation, no code fences wrapping the "
        "output, no markdown horizontal rules added at the start or end. Keep "
        "any <!--more--> marker and existing markdown link/code formatting "
        "intact unless the instruction specifically asks to change them.\n\n"
        "**DO NOT DROP EXISTING INLINE LINKS**, including links to file-format "
        "reference pages (e.g. docs.fileformat.com). If the instruction asks you "
        "to shorten, condense, or hit a word/length target, you MUST still keep "
        "every existing markdown link `[text](url)` in the output - reword or "
        "trim the surrounding prose instead, never remove a link (or unlink its "
        "text) just to save words. A shortened result that is over the target by "
        "a few words but keeps all links is correct; one that hits the target by "
        "dropping a link is not.\n\n"
        f"{context_block}"
        f"REQUESTED CHANGE:\n{instruction}\n\n"
        f"SECTION BODY TO EDIT:\n{body_text}"
    )
    result_text, usage = await _complete_with_retry(prompt, temperature=0.3, max_tokens=4000, label="revise-section-rewrite")
    if result_text is None:
        raise SectionEditError(f"LLM call failed while rewriting the section: {usage.get('error', 'unknown error')}")

    cleaned = repair_code_fences(result_text)
    cleaned = clean_ai_generated_markdown(cleaned, verbose=False)
    cleaned = validate_markdown_links(cleaned, verbose=False)
    cleaned = strip_snippet_markers(cleaned)
    cleaned = cleaned.strip("\n")

    new_section_text = cleaned if heading_line is None else f"{heading_line}\n{cleaned}"
    new_lines = lines[:section.line_start] + new_section_text.split("\n") + lines[section.line_end:]
    return new_lines, usage


async def rewrite_field(lines: list[str], fm: FrontmatterBlock, field: str, instruction: str, post_context: str = "") -> tuple[list[str], dict]:
    i = _find_field_line(lines, fm, field)
    m = re.match(rf'^({re.escape(field)}\s*:\s*)(.*)$', lines[i], re.IGNORECASE)
    prefix, old_value = m.groups()
    old_value_clean = _strip_quotes(old_value)
    if old_value.strip() in _FOLDED_SCALAR_VALUES:
        raise SectionEditError(f"Frontmatter field '{field}' is a multi-line YAML value - not supported yet.")

    context_block = (
        f"POST CONTEXT (reference only, to keep the new value on-topic and "
        f"consistent with the rest of the post - do NOT copy or repeat this "
        f"block, only the FIELD's value is wanted):\n{post_context}\n\n"
    ) if post_context else ""

    prompt = (
        f"Rewrite this single blog frontmatter field value per the instruction below. "
        f"Return ONLY the new value as plain text, on one line, no quotes, no field name, no explanation.\n\n"
        f"{context_block}"
        f"FIELD: {field}\nCURRENT VALUE: {old_value_clean}\nINSTRUCTION: {instruction}"
    )
    result_text, usage = await _complete_with_retry(prompt, temperature=0.3, max_tokens=300, label="revise-field-rewrite")
    if result_text is None:
        raise SectionEditError(f"LLM call failed while rewriting '{field}': {usage.get('error', 'unknown error')}")

    new_value = result_text.strip().strip("\n").splitlines()[0].strip()
    quote = '"' if old_value.strip().startswith('"') else ("'" if old_value.strip().startswith("'") else "")
    rendered = f"{quote}{new_value}{quote}" if quote else new_value
    new_lines = list(lines)
    new_lines[i] = f"{prefix}{rendered}"
    return new_lines, usage


async def generate_new_heading(section: Section, instruction: str, post_context: str = "") -> tuple[str, dict]:
    """Used by rename_heading when the instruction asks to reword/improve a
    heading without giving exact new wording (KIND: GENERATIVE, NEW_TEXT:
    NONE) - a single scoped LLM call proposes the new title text, which the
    caller then applies via the existing deterministic rename_heading()
    splice (same "LLM proposes content, code controls where it lands"
    split as rewrite_section/rewrite_field)."""
    context_block = (
        f"POST CONTEXT (reference only, to keep the new heading on-topic and "
        f"consistent with the rest of the post - do NOT copy or repeat this "
        f"block, only the new heading text is wanted):\n{post_context}\n\n"
    ) if post_context else ""

    prompt = (
        "You are proposing a NEW heading (title) for one section of an existing "
        "published-quality blog post, per the requested change below. Return ONLY "
        "the new heading text: one line, no leading '#', no surrounding quotes, "
        "no markdown formatting, no explanation.\n\n"
        f"{context_block}"
        f"CURRENT HEADING: {section.heading_text}\n\n"
        f"REQUESTED CHANGE:\n{instruction}"
    )
    result_text, usage = await _complete_with_retry(prompt, temperature=0.4, max_tokens=300, label="revise-heading-rewrite")
    if result_text is None:
        raise SectionEditError(f"LLM call failed while generating a new heading: {usage.get('error', 'unknown error')}")

    new_heading = result_text.strip().splitlines()[0].strip().strip("`\"'").lstrip("#").strip()
    if not new_heading:
        raise SectionEditError("LLM returned an empty heading.")
    return new_heading, usage


# ─────────────────────────────────────────────────────────────────────────
# Diffing - a visible flag for the human reviewer (step 5), not a hard
# gate. Reports how many lines changed OUTSIDE the range the edit claimed
# to touch.
# ─────────────────────────────────────────────────────────────────────────

def count_changed_lines_outside_range(old_lines: list[str], new_lines: list[str], protected_start: int, protected_end: int) -> int:
    """Counts inserted/deleted/replaced lines that fall outside
    [protected_start, protected_end) of the OLD document. A change entirely
    inside the target range contributes 0; the count is 0 for a
    correctly-scoped edit and the actual line-count for a leak."""
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    changed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_outside = max(0, min(i2, protected_start) - i1) + max(0, i2 - max(i1, protected_end))
        new_outside = max(0, min(j2, protected_start) - j1) + max(0, j2 - max(j1, protected_end))
        changed += max(old_outside, new_outside)
    return changed


# ─────────────────────────────────────────────────────────────────────────
# Top-level entry point used by orchestrator.revise_blog_draft()
# ─────────────────────────────────────────────────────────────────────────

async def classify_and_apply(raw: str, instruction: str) -> dict:
    """Returns a report dict:
      {
        "content": <new full-file text, == raw unchanged if rejected/no-op>,
        "kind": "deterministic" | "generative" | "reject",
        "operation": str | None,
        "target": str,                       # human-readable, for the PR comment
        "changed": bool,
        "lines_changed_outside_section": int | None,
        "reason": str,                       # explanation, esp. for reject
        "token_usage": {"input_tokens", "output_tokens", "total_tokens"},
      }
    Raises SectionEditError only for conditions that make section-aware
    editing impossible at all (e.g. no frontmatter) - anything about the
    INSTRUCTION itself (ambiguous, multi-section, unmatched target) comes
    back as a normal "reject" report, never an exception, since that's an
    expected outcome the caller reports to the reviewer, not a bug.
    """
    if "\r" in raw:
        raise SectionEditError("Draft uses CR/CRLF line endings - not supported, refusing to risk misaligned edits.")

    lines = raw.split("\n")
    fm = locate_frontmatter(lines)
    sections = parse_sections(lines, fm.body_start_line)
    fm_fields = list(fm.metadata.keys())

    cls, classify_usage = await classify_instruction(instruction, sections, fm_fields)
    usage_total = dict(classify_usage) if isinstance(classify_usage, dict) else dict(_EMPTY_USAGE)

    if cls["kind"] == "reject":
        return {
            "content": raw, "kind": "reject", "operation": cls.get("operation"),
            "target": "", "changed": False, "lines_changed_outside_section": None,
            "reason": cls.get("reason") or "Instruction could not be mapped to a single section/field.",
            "token_usage": usage_total,
        }

    invalid_reason = _validate_classification(cls, sections, fm_fields)
    if invalid_reason:
        return {
            "content": raw, "kind": "reject", "operation": cls.get("operation"),
            "target": "", "changed": False, "lines_changed_outside_section": None,
            "reason": invalid_reason, "token_usage": usage_total,
        }

    op = cls["operation"]
    section = next((s for s in sections if s.index == cls["section_index"]), None)
    protected_start, protected_end = 0, 0
    target_desc = ""
    # Built once, reused by every generative call below (rewrite_section /
    # rewrite_field / generate_new_heading) - cheap (no LLM call), and gives
    # each of them the same read-only reference point.
    post_context = build_post_context(fm, sections, lines)

    try:
        if op == "remove_section":
            new_lines = remove_section(lines, section)
            # The whole removed range is the EXPECTED change (that's the
            # point of the operation) - it must count as "inside the
            # target", not as a leak. A zero-width range here would flag
            # every single removal as having leaked outside its section.
            protected_start, protected_end = section.line_start, section.line_end
            target_desc = f"section [{section.index}] {section.heading_text!r} (removed)"
        elif op == "rename_heading":
            if cls["new_text"]:
                new_heading = cls["new_text"]
            else:
                new_heading, call_usage = await generate_new_heading(section, instruction, post_context)
                for k in ("input_tokens", "output_tokens", "total_tokens"):
                    usage_total[k] = usage_total.get(k, 0) + call_usage.get(k, 0)
            new_lines = rename_heading(lines, section, new_heading)
            protected_start, protected_end = section.line_start, section.line_start + 1
            target_desc = f"heading of section [{section.index}]"
        elif op == "replace_text":
            new_lines = replace_exact_text(lines, fm.body_start_line, cls["old_text"], cls["new_text"])
            protected_start, protected_end = fm.body_start_line, len(lines)
            target_desc = f"exact text {cls['old_text']!r}"
        elif op == "add_tag":
            new_lines = add_tag(lines, fm, cls["new_text"])
            protected_start, protected_end = fm.open_line, fm.close_line + 1
            target_desc = f"add tag {cls['new_text']!r}"
        elif op == "remove_tag":
            new_lines = remove_tag(lines, fm, cls["new_text"])
            protected_start, protected_end = fm.open_line, fm.close_line + 1
            target_desc = f"remove tag {cls['new_text']!r}"
        elif op == "set_field":
            new_lines = set_field(lines, fm, cls["field_name"], cls["new_text"])
            protected_start, protected_end = fm.open_line, fm.close_line + 1
            target_desc = f"frontmatter field {cls['field_name']!r}"
        elif op == "rewrite_section" and cls["field_name"]:
            new_lines, call_usage = await rewrite_field(lines, fm, cls["field_name"], instruction, post_context)
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                usage_total[k] = usage_total.get(k, 0) + call_usage.get(k, 0)
            protected_start, protected_end = fm.open_line, fm.close_line + 1
            target_desc = f"frontmatter field {cls['field_name']!r} (rewritten)"
        elif op == "rewrite_section":
            new_lines, call_usage = await rewrite_section(lines, section, instruction, post_context)
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                usage_total[k] = usage_total.get(k, 0) + call_usage.get(k, 0)
            protected_start, protected_end = section.line_start, section.line_end
            target_desc = f"section [{section.index}] {section.heading_text!r}"
        else:
            return {
                "content": raw, "kind": "reject", "operation": op, "target": "",
                "changed": False, "lines_changed_outside_section": None,
                "reason": f"Unrecognized or incomplete operation: {op!r}.",
                "token_usage": usage_total,
            }
    except SectionEditError as e:
        return {
            "content": raw, "kind": "reject", "operation": op, "target": "",
            "changed": False, "lines_changed_outside_section": None,
            "reason": str(e), "token_usage": usage_total,
        }

    outside = count_changed_lines_outside_range(lines, new_lines, protected_start, protected_end)
    new_content = "\n".join(new_lines)
    return {
        "content": new_content, "kind": cls["kind"], "operation": op,
        "target": target_desc, "changed": new_content != raw,
        "lines_changed_outside_section": outside,
        "reason": cls.get("reason") or "", "token_usage": usage_total,
    }
