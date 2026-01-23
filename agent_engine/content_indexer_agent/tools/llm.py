from __future__ import annotations

import json
import logging
from typing import List, Tuple

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__name__)


class BlogClassifyOut(BaseModel):
    topic: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    sub_category: str = Field(..., min_length=1)
    platforms: List[str] = Field(default_factory=list)


def _extract_output_text(resp: object) -> str:
    """
    Works with openai-python Responses objects:
    - resp.output_text (helper) if present
    - else attempt to stitch output items
    """
    txt = getattr(resp, "output_text", None)
    if isinstance(txt, str) and txt.strip():
        return txt.strip()

    # Best-effort fallback for older/newer response shapes
    out = getattr(resp, "output", None)
    if isinstance(out, list):
        chunks: List[str] = []
        for item in out:
            content = getattr(item, "content", None)
            if isinstance(content, list):
                for c in content:
                    if getattr(c, "type", None) == "output_text":
                        chunks.append(getattr(c, "text", "") or "")
        joined = "".join(chunks).strip()
        if joined:
            return joined

    raise ValueError("Could not extract output text from response object")


def classify_blog_with_llm(
    *,
    client: OpenAI,
    model: str,
    title: str,
    excerpt: str,
    allowed_platforms: List[str],
    inferred_platforms: List[str],
) -> Tuple[str, str, str, List[str]]:
    """
    Returns: (topic, category, sub_category, platforms)

    Uses Responses API structured outputs via:
      1) client.responses.parse(..., text_format=BlogClassifyOut) if available
      2) client.responses.create(..., text.format json_schema)
      3) fallback: client.responses.create(..., text.format json_object) + JSON parse
    """
    sys = (
        "You are a taxonomy normalizer for product blog posts.\n"
        "Return a concise platform-agnostic topic (<= 12 words), category, sub_category, and platform list.\n"
        f"Allowed platforms: {allowed_platforms}\n"
        f"Inferred platforms (soft hint): {inferred_platforms}\n"
        "If no platform applies, return platforms=['general'].\n"
        "Use title case for category and sub_category."
    )
    user = f"TITLE:\n{title}\n\nEXCERPT:\n{excerpt}"

    input_msgs = [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]

    # 1) Preferred: responses.parse (Pydantic)
    try:
        parse_fn = getattr(getattr(client, "responses", None), "parse", None)
        if callable(parse_fn):
            resp = parse_fn(
                model=model,
                input=input_msgs,
                text_format=BlogClassifyOut,
            )
            parsed = getattr(resp, "output_parsed", None)
            if isinstance(parsed, BlogClassifyOut):
                platforms = parsed.platforms or []
                if not platforms:
                    platforms = ["general"]
                return parsed.topic, parsed.category, parsed.sub_category, platforms
    except Exception as e:
        log.debug("responses.parse not available or failed; falling back. err=%s", e)

    # 2) Structured Outputs with json_schema via text.format (Responses API)
    schema = BlogClassifyOut.model_json_schema()

    try:
        resp = client.responses.create(
            model=model,
            input=input_msgs,
            text={
                "format": {
                    "type": "json_schema",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        raw = _extract_output_text(resp)
        data = json.loads(raw)
        parsed = BlogClassifyOut.model_validate(data)
        platforms = parsed.platforms or ["general"]
        return parsed.topic, parsed.category, parsed.sub_category, platforms

    except Exception as e_schema:
        # 3) Fallback to JSON mode if model/provider doesn't support json_schema
        log.debug("json_schema failed; falling back to json_object. err=%s", e_schema)

        resp = client.responses.create(
            model=model,
            input=input_msgs,
            text={"format": {"type": "json_object"}},
        )
        raw = _extract_output_text(resp)

        # Try to parse JSON object
        try:
            data = json.loads(raw)
            parsed = BlogClassifyOut.model_validate(data)
            platforms = parsed.platforms or ["general"]
            return parsed.topic, parsed.category, parsed.sub_category, platforms
        except (json.JSONDecodeError, ValidationError) as e_json:
            # Last resort: heuristic fallback (no hard fail)
            log.warning("Could not parse structured output; using fallback. err=%s raw=%r", e_json, raw[:400])
            plats = inferred_platforms or ["general"]
            return title[:200], "General", "General", plats
