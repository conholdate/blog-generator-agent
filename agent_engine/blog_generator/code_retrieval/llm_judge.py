"""
LLM-judgment retrieval: replaces normalizer.py/matcher.py's keyword-scoring
formula as the decision-maker (see retrieval_llm.py). Two stages -
pick a candidate from the full real file list, then verify it against its
actual content - using the same self-hosted LLM already wired into this
pipeline (services/LLMservice.py), not a new client.

Why this exists: keyword-scoring, however tuned, kept moving the failure
around rather than fixing it (confirmed against 53 real topics - see
memory/architecture notes). An LLM reading real filenames and real code
understands things a bag-of-words formula structurally can't: direction
("convert A to B" vs "convert B to A"), whether a "generic-sounding" file
is actually on-topic, and a genuine "none of these fit" judgment instead of
a numeric threshold.
"""
import difflib
import re
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.LLMservice import llm_service  # noqa: E402

_FILE_RE = re.compile(r"FILE:\s*(.+)", re.IGNORECASE)
_REASON_RE = re.compile(r"REASON:\s*(.+)", re.IGNORECASE)
_VERIFIED_RE = re.compile(r"VERIFIED:\s*(YES|NO)", re.IGNORECASE)

CLOSE_MATCH_CUTOFF = 0.9  # conservative - a near-miss typo/misremembering, not a different file


def _closest_match(raw_file: str, paths: list[str]) -> str | None:
    """Confirmed real case: the LLM correctly identified and described a file
    but misremembered its exact name by one word out of a ~1,800-file list
    it was reading from, not writing itself - exact string matching silently
    turned a correct pick into a false NO_MATCH. A high cutoff keeps this
    from ever accepting a genuinely different file, only a near-identical
    misremembering of the real one."""
    matches = difflib.get_close_matches(raw_file, paths, n=1, cutoff=CLOSE_MATCH_CUTOFF)
    return matches[0] if matches else None


def _build_pick_prompt(topic: str, primary_keyword: str, platform: str, product_name: str, paths: list[str]) -> str:
    keyword_line = f"\nPrimary keyword: {primary_keyword}" if primary_keyword else ""
    file_list = "\n".join(paths)
    return f"""You are selecting the single best-matching {platform} code example file for a blog post, from a real repository of {product_name} code examples.

Topic: {topic}{keyword_line}

Below is the complete list of available example files (relative paths, category/filename.cs - the filename itself describes what the example does). Pick the ONE file that most directly and specifically addresses the topic.

Judge carefully:
- Pay close attention to DIRECTION - "convert A to B" is NOT satisfied by a file that converts B to A.
- Pay close attention to WHAT is being acted on - a file about a chart, shape, or image is not the same as one about the whole document/presentation, unless the topic is specifically about that narrower thing.
- A file with generic-sounding words in common with the topic is not automatically a match - judge the actual described action, not just word overlap.
- If NONE of the files genuinely address this topic, say NONE. It is much better to say NONE than to force a weak or tangential match.

Files:
{file_list}

Respond in exactly this format and nothing else:
FILE: <exact path copied from the list above, or NONE>
REASON: <one sentence explaining your choice>"""


def _build_verify_prompt(topic: str, primary_keyword: str, platform: str, path: str, content: str) -> str:
    keyword_line = f"\nPrimary keyword: {primary_keyword}" if primary_keyword else ""
    return f"""You are verifying whether a specific {platform} code example genuinely satisfies a blog post topic. Be strict.

Topic: {topic}{keyword_line}

Candidate file: {path}

File content:
```
{content}
```

Does this file's actual code genuinely accomplish what the TOPIC asks for? Reject it if it is only tangentially related, does something similar but not the same thing, acts on the wrong target (e.g. a chart/shape instead of the whole document), or goes in the wrong direction (e.g. converts B to A when the topic asks for A to B).

Judge the code's real behavior against the topic - not against the file's own header comment. A comment can overstate what the code does (e.g. claiming "with header row" when the code only adds plain data rows); that's a mismatch between the comment and the code, not a reason to reject the code for failing to satisfy something the topic never asked for in the first place.

Do NOT judge whether the code is correct, whether it compiles, whether it calls the SDK's API "properly," or whether it would work as written - that is explicitly out of scope here and none of this repo's files have been executed to confirm. Your only job is topical relevance: does this code's evident intent and operation - reading it as any developer would - address what the topic is asking for. If it clearly attempts the right operation (e.g. calling a converter method with the right source and target format), that is a match even if you're not certain the exact API call is used with textbook precision.

If the topic names multiple near-synonymous variants of the same underlying thing (e.g. "PPT/PPTX", "JPG/JPEG"), treat an example handling any one of them as satisfying all of them - these SDKs load/save format variants through the same API, so a file hardcoding one variant's extension in a path string is not a real capability gap. Only reject on this basis if there's a genuine, substantive difference the topic specifically calls out (e.g. two formats that require different conversion logic, not just a different file extension).

Respond in exactly this format and nothing else:
VERIFIED: <YES or NO>
REASON: <one sentence explaining your judgment>"""


# Confirmed against a real repo: Aspose.Cells' 5,510-file list overflowed the
# model's context window outright ("max_tokens must be at least 1, got
# -17981") - the raw file-path text alone is ~124K tokens. Aspose.Slides'
# 2,272-file list (~51K tokens) worked fine in one call. Chosen conservatively
# below that confirmed-safe size, with margin, rather than computed from an
# exact token count (this deployment's real usable context isn't published).
CHUNK_SIZE = 1500


async def pick_file(topic: str, primary_keyword: str, platform: str, product_name: str, paths: list[str]) -> dict:
    """Chunks the file list when it's too large for one call - every file
    still gets read by the LLM, just across multiple calls instead of one,
    rather than pre-filtering candidates with a separate (unverified) scoring
    step. Each chunk's winner, if any, goes to one final tie-break call."""
    if len(paths) <= CHUNK_SIZE:
        return await _pick_from_list(topic, primary_keyword, platform, product_name, paths)

    chunks = [paths[i:i + CHUNK_SIZE] for i in range(0, len(paths), CHUNK_SIZE)]
    chunk_picks = []
    for chunk in chunks:
        result = await _pick_from_list(topic, primary_keyword, platform, product_name, chunk)
        if result["file"]:
            chunk_picks.append(result)

    if not chunk_picks:
        return {"file": None, "raw_file": None, "reason": "no candidate found in any chunk of the file list",
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}
    if len(chunk_picks) == 1:
        return chunk_picks[0]

    return await _pick_from_list(
        topic, primary_keyword, platform, product_name, [p["file"] for p in chunk_picks]
    )


async def _pick_from_list(topic: str, primary_keyword: str, platform: str, product_name: str, paths: list[str]) -> dict:
    prompt = _build_pick_prompt(topic, primary_keyword, platform, product_name, paths)
    # gpt-oss (this deployment's model) is a reasoning model that thinks out
    # loud before answering - confirmed against a real repo (~2,300 candidate
    # files) that a small max_tokens truncates it mid-reasoning, before it
    # reaches the FILE:/REASON: lines. That happened to still land on the
    # right answer once (truncation occurred after ruling out the wrong
    # candidates) but is not reliable - a real match found later in its
    # reasoning would get cut off before being reported.
    # temperature=0.1, not 0: tried temperature=0 for reproducibility (there
    # is real run-to-run non-determinism at 0.1) but measured it against the
    # 53-topic ground truth and it made things worse, not better - precision
    # barely moved (already ~95% either way) while recall dropped from 82%
    # to 73%, because greedy decoding pushed the model toward answering NONE
    # far more often even when a real match existed. The non-determinism is
    # real and unresolved, but costs less accuracy than "fixing" it did here.
    text, usage = await llm_service.complete(prompt=prompt, temperature=0.1, max_tokens=6000)

    file_match = _FILE_RE.search(text or "")
    reason_match = _REASON_RE.search(text or "")
    raw_file = file_match.group(1).strip() if file_match else None
    reason = reason_match.group(1).strip() if reason_match else (text or "").strip()

    picked = None
    if raw_file and raw_file.upper() != "NONE":
        cleaned = raw_file.strip("`\"'")
        picked = cleaned if cleaned in paths else _closest_match(cleaned, paths)

    return {"file": picked, "raw_file": raw_file, "reason": reason, "token_usage": usage}


async def verify_file(topic: str, primary_keyword: str, platform: str, path: str, content: str) -> dict:
    prompt = _build_verify_prompt(topic, primary_keyword, platform, path, content)
    # temperature=0.1 - see pick_file's comment; reverted from 0 for the same
    # measured reason (recall regression without a real precision gain).
    text, usage = await llm_service.complete(prompt=prompt, temperature=0.1, max_tokens=2000)

    verified_match = _VERIFIED_RE.search(text or "")
    reason_match = _REASON_RE.search(text or "")
    verified = bool(verified_match) and verified_match.group(1).upper() == "YES"
    reason = reason_match.group(1).strip() if reason_match else (text or "").strip()

    return {"verified": verified, "reason": reason, "token_usage": usage}
