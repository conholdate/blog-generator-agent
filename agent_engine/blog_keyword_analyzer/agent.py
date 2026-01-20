from __future__ import annotations

import json
import logging
import re
import time
from typing import List, Optional, Dict, Any

from openai import OpenAI

from .config import settings
from .schemas import Cluster, TopicIdea
from .tools.metrics import RunMetrics


logger = logging.getLogger(__name__)


class KeywordResearchAgent:
    """
    Agent responsible for turning scored clusters into topic ideas via LLM.

    Responsibilities:
      - Take clustered + scored keyword data
      - Apply platform / language constraints
      - Respect existing topics to avoid duplication
      - Call LLM and parse a strict JSON response into TopicIdea objects
    """

    def __init__(self, model: str | None = None) -> None:
        """
        Initialize the agent and choose which model / backend to use.
        """
        self.model = settings.PROFESSIONALIZE_LLM_MODEL

        # Decide which backend to use: custom (self-hosted) or OpenAI
        # Your self-hosted LLM (OpenAI-compatible)
        logger.info(
            "Initializing KeywordResearchAgent with custom LLM backend: base_url=%s model=%s",
            settings.PROFESSIONALIZE_BASE_URL,
            self.model,
        )

        try:
            # Client construction itself can throw (bad types, etc.)
            self.client = OpenAI(
                base_url=settings.PROFESSIONALIZE_BASE_URL,
                api_key=settings.PROFESSIONALIZE_API_KEY,
            )
        except Exception as e:
            logger.info(
                "Failed to initialize OpenAI client: error=%s",
                e,
            )

        # Many custom servers don't fully support response_format yet
        self._use_response_format = False

    @staticmethod
    def _extract_json_block(text: str) -> str | None:
        """
        Try to rescue a JSON object from a response that may contain
        extra text or markdown fences.

        This is used as a fallback when direct json.loads() fails.
        """
        text = text.strip()

        # Remove common markdown fences like ```json ... ```
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
            text = text.rstrip("`").strip()

        # Greedy match the first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def _platform_label(fw: Optional[str]) -> Optional[str]:
        """
        Map a canonical platform key -> human label to embed in titles.
        Keeps LLM prompt consistent and human-readable.
        """
        if not fw:
            return None
        f = fw.lower().strip()
        if f == "python":
            return "Python"
        if f == "java":
            return "Java"
        if f in {"csharp", "c#"}:
            return "C#"
        return fw  # fallback: echo as-is
    @staticmethod
    def _product_variants(product: str) -> List[str]:
        """
        Generate common textual variants of a product name for matching/removal.
        Example: "Aspose.Cells" -> ["Aspose.Cells", "Aspose Cells", "Cells", "aspose.cells", ...]
        """
        p = (product or "").strip()
        if not p:
            return []

        # Base variants
        variants = {p}

        # Normalize separators: dot <-> space
        variants.add(p.replace(".", " "))
        variants.add(p.replace(" ", "."))

        # Tokenize and add last token (e.g., "Cells")
        tokens = re.split(r"[.\s/\\_-]+", p)
        tokens = [t for t in tokens if t]
        if tokens:
            variants.add(tokens[-1])  # e.g., "Cells"

        # Add lowercase variants as well (for matching)
        out = set()
        for v in variants:
            v = v.strip()
            if not v:
                continue
            out.add(v)
            out.add(v.lower())

        # Prefer longer variants first for removal (avoid removing "Cells" too early)
        return sorted(out, key=len, reverse=True)

    @staticmethod
    def _contains_product(title: str, product_variants: List[str]) -> bool:
        t = (title or "").strip()
        if not t:
            return False
        for v in product_variants:
            if not v:
                continue
            # word-boundary-ish match, but allow dots
            pat = rf"(?i)(?<!\w){re.escape(v)}(?!\w)"
            if re.search(pat, t):
                return True
        return False

    @staticmethod
    def _ensure_product_in_title(title: str, product: str) -> str:
        """
        Ensure product appears in title. If missing, append "(<product>)".
        """
        t = (title or "").strip()
        p = (product or "").strip()
        if not t or not p:
            return t

        variants = KeywordResearchAgent._product_variants(p)
        if KeywordResearchAgent._contains_product(t, variants):
            return t

        # Append in a consistent, non-disruptive way
        return f"{t} ({p})"

    @staticmethod
    def _remove_product_from_title(title: str, product: str) -> str:
        """
        Ensure product does NOT appear in title.
        Removes product variants and cleans leftover punctuation/whitespace.
        """
        t = (title or "").strip()
        p = (product or "").strip()
        if not t or not p:
            return t

        variants = KeywordResearchAgent._product_variants(p)
        out = t

        # Remove variants (longest first)
        for v in variants:
            if not v:
                continue
            pat = rf"(?i)(?<!\w){re.escape(v)}(?!\w)"
            out = re.sub(pat, "", out)

        # Clean up empty parentheses/brackets caused by removal
        out = re.sub(r"\(\s*\)", "", out)
        out = re.sub(r"\[\s*\]", "", out)

        # Clean up duplicated punctuation / separators
        out = re.sub(r"\s{2,}", " ", out).strip()
        out = re.sub(r"\s+([:,\-–—])", r"\1", out)     # space before punctuation
        out = re.sub(r"([:,\-–—])\s{2,}", r"\1 ", out) # too many spaces after punctuation

        # Remove leading/trailing separators
        out = out.strip(" -–—,:;")

        return out

    def generate_topics(
        self,
        brand: str,
        product: str,
        locale: str,
        clusters: List[Cluster],
        top_n: int = 10,
        platform: Optional[str] = None,
        existing_topics: Optional[List[Dict[str, Any]]] = None,
        metrics: Optional[RunMetrics] = None,
        include_product_in_title: bool = True,
    ) -> List[TopicIdea]:
        """
        Generate topic ideas from the top N clusters.

        Args:
            brand: Brand name (e.g. "Aspose").
            product: Product name (e.g. "Aspose.Cells").
            locale: Locale string like "en-US".
            clusters: List of scored Cluster objects.
            top_n: How many top clusters to consider.
            platform: Optional canonical platform (e.g. "python", "csharp").
            existing_topics: Existing blog posts used for deduplication.

        Returns:
            List[TopicIdea] parsed from the LLM response. Empty list on failure.
        """
        if not clusters:
            logger.warning("generate_topics called with no clusters – returning empty list.")
            return []

        chosen = clusters[:top_n]
        logger.info(
            "Preparing to generate topics: brand=%s product=%s locale=%s clusters_used=%d "
            "top_n=%d platform=%s existing_topics=%d",
            brand,
            product,
            locale,
            len(chosen),
            top_n,
            platform,
            len(existing_topics or []),
        )

        # Compact payload for the LLM – keep it lightweight but informative
        payload = {
            "brand": brand,
            "product": product,
            "locale": locale,
            "clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "label": c.label,
                    "intent": c.metrics.intent,
                    "brand_fit": c.metrics.brand_fit,
                    "score": c.metrics.score,
                    "keywords": [m.keyword for m in c.members[:12]],
                }
                for c in chosen
            ],
        }

        if platform:
            payload["platform"] = platform

        if existing_topics:
            # Keep payload small: only title + url + slug + platforms
            compact: List[Dict[str, Any]] = []
            for e in existing_topics:
                compact.append(
                    {
                        "title": e.get("title"),
                        "url": e.get("url"),
                        "slug": e.get("slug"),
                        "platforms": e.get("platforms"),
                    }
                )
            payload["existing_topics"] = compact

        # Derive a human-readable label like "Python", "Java", "C#"
        fw_label = self._platform_label(platform)
        logger.debug("platform=%r -> fw_label=%r", platform, fw_label)

        if settings.DEBUG:
            logger.debug(
                "Payload sent to LLM (truncated): %s",
                json.dumps(payload, indent=2)[:2000],
            )

        system = (
            "You are a 'Blog Keyword Analyzer' agent.\n\n"
            "CONTEXT\n"
            "- You receive clustered keyword data (from Google Keyword Planner or similar).\n"
            "- Your job is to propose high-impact blog post topics based on these clusters.\n"
            "- You must return STRICT JSON with a single top-level key 'topics'.\n\n"
            "EACH topic object MUST include:\n"
            "- 'cluster_id': string/int, matching the cluster that inspired this topic.\n"
            "- 'title': SEO-optimized, compelling (but not clickbait) blog post title.\n"
            "- 'angle': ONE short sentence describing the unique hook/perspective.\n"
            "- 'outline': list of 3–7 bullets, each an H2/H3-style section.\n"
            "- 'target_persona': ONE short description of the ideal reader.\n"
            "- 'primary_keyword': ONE main keyword taken DIRECTLY from the input keywords.\n"
            "- 'supporting_keywords': 3–8 related keywords from the SAME cluster.\n"
            "- 'internal_links': list of 0–5 internal link targets as strings.\n\n"
            "TOPIC COUNT\n"
            "- Generate between 10 and 20 topics in total.\n"
            "- It is better to return fewer, higher-quality topics than many weak ones.\n\n"
            "CLUSTER & KEYWORD CONSISTENCY\n"
            "- 'cluster_id' MUST be taken directly from the input cluster identifier.\n"
            "- 'primary_keyword' MUST be an exact string match of one keyword from that cluster.\n"
            "- 'supporting_keywords' MUST be exact string matches of other keywords from the SAME cluster.\n"
            "- Do NOT invent new keywords or cluster IDs.\n\n"
            "DEDUPLICATION & EXISTING CONTENT RULES\n"
            "- The user payload may include 'existing_topics': a list of existing blog posts.\n"
            "- You MUST NOT propose any topic whose title or core idea substantially overlaps\n"
            "  with any 'existing_topics' entry.\n"
            "- Treat 'existing_topics' as a RESERVED set of angles; look for gaps and new angles.\n"
            "- If 'existing_topics' is missing or empty, ignore this rule and propose the best topics you can.\n\n"
            "INTERNAL LINKS\n"
            "- 'internal_links' should be 0–5 string slugs or titles of existing posts from 'existing_topics'\n"
            "  that would be relevant as internal links.\n"
            "- If there is no good internal link, use an empty list [].\n"
            "- Never invent posts that are not in 'existing_topics'.\n\n"
        )

        # Dynamic platform rules
        system += "platform / LANGUAGE RULES\n"
        if fw_label:
            system += (
                f"- For THIS run, the target programming language/platform is '{fw_label}'.\n"
                f"  1) EVERY topic MUST be written ONLY for '{fw_label}'.\n"
                f"  2) The word '{fw_label}' MUST appear in EVERY 'title'. If any title does NOT\n"
                f"     contain '{fw_label}', your response is INVALID.\n"
                "  3) Do NOT mention any other programming language or platform in titles or angles.\n"
                "  4) The outline MUST assume code examples and usage in this language/platform only.\n"
            )
        else:
            system += (
                "- 'platform' is NOT provided.\n"
                "- Propose language-agnostic topics or topics that are clearly relevant across languages.\n"
            )

        # Product title rules
        if include_product_in_title:
            system += (
                "\nPRODUCT TITLE RULE\n"
                f"- The product name '{product}' MUST appear in EVERY 'title'.\n"
                "- If any title does NOT contain the product name, the response is INVALID.\n"
            )
        else:
            system += (
                "\nPRODUCT TITLE RULE\n"
                f"- The product name '{product}' MUST NOT appear in ANY 'title'.\n"
                "- Do not mention the product name or close variants (e.g., with '.' or spaces).\n"
                "- If any title contains the product name, the response is INVALID.\n"
            )

        system += (
            "\nPRIORITIZATION\n"
            "- Prefer clusters/keywords with meaningful search volume and reasonable competition.\n"
            "- Prefer clear informational/commercial-intent queries suitable for blog content.\n"
            "- Ignore/de-prioritize very low-volume, extremely broad, or irrelevant terms.\n\n"
            "STRICT JSON RULES\n"
            "- Return ONLY JSON. No markdown, no commentary.\n"
            '- Use a single object: {\"topics\": [ ... ]}.\n'
            "- Use double quotes for all keys and string values.\n"
            "- No trailing commas.\n"
            "- Do not include any explanations or meta text outside the JSON object.\n"
        )

        if settings.DEBUG:
            logger.debug("System prompt for LLM:\n%s", system)

        # Build request kwargs
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
        }
        if self._use_response_format:
            request_kwargs["response_format"] = {"type": "json_object"}

        # Call LLM with timing
        logger.info("Calling LLM to generate topics...")
        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(**request_kwargs)
        dt = time.perf_counter() - t0
        logger.info("LLM call completed in %.3f seconds", dt)

        # 🔹 Token usage
        usage = getattr(resp, "usage", None)
        if usage is not None:
            # openai-python returns a CompletionUsage object
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = getattr(usage, "total_tokens", 0) or 0

            logger.info(
                "LLM token usage: prompt=%d completion=%d total=%d",
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )

            if metrics is not None:
                # accumulate in case you ever do multiple calls per run
                metrics.llm_prompt_tokens += prompt_tokens
                metrics.llm_completion_tokens += completion_tokens

        txt = resp.choices[0].message.content or ""
        logger.debug("Raw LLM response (truncated to 1200 chars): %s", txt[:1200])

        # Try to parse JSON strictly
        data_obj: Any = None
        try:
            data_obj = json.loads(txt)
        except json.JSONDecodeError:
            logger.warning("Failed direct JSON parse of LLM response; attempting to extract JSON block.")
            json_block = self._extract_json_block(txt)
            if json_block is not None:
                if settings.DEBUG:
                    logger.debug("Extracted JSON block (truncated): %s", json_block[:1200])
                try:
                    data_obj = json.loads(json_block)
                except json.JSONDecodeError as exc:
                    logger.error("Failed to parse extracted JSON block: %s", exc)
                    data_obj = None
            else:
                logger.error("No JSON object found in LLM output; returning no topics.")
                data_obj = None

        if not isinstance(data_obj, dict):
            logger.error("LLM JSON payload is not an object; returning no topics.")
            return []

        topics_raw = data_obj.get("topics", [])
        if not isinstance(topics_raw, list):
            logger.error("'topics' key missing or not a list in JSON; returning no topics.")
            return []

        out: List[TopicIdea] = []
        invalid_count = 0
        # Enforce product inclusion/exclusion deterministically after parsing.
        if product:
            if include_product_in_title:
                fixed = 0
                variants = self._product_variants(product)
                for topic in out:
                    original = (topic.title or "").strip()
                    if not self._contains_product(original, variants):
                        topic.title = self._ensure_product_in_title(original, product)
                        fixed += 1
                if fixed:
                    logger.info("Title enforcement: appended product to %d titles.", fixed)
            else:
                stripped = 0
                variants = self._product_variants(product)
                for topic in out:
                    original = (topic.title or "").strip()
                    if self._contains_product(original, variants):
                        topic.title = self._remove_product_from_title(original, product)
                        stripped += 1
                if stripped:
                    logger.info("Title enforcement: removed product from %d titles.", stripped)

        for t in topics_raw:
            if not isinstance(t, dict):
                invalid_count += 1
                continue
            try:
                out.append(TopicIdea(**t))
            except Exception as e:
                invalid_count += 1
                logger.debug("Failed to parse TopicIdea from entry %r: %s", t, e)

        logger.info(
            "Parsed %d valid topics from LLM (invalid_entries=%d, total=%d)",
            len(out),
            invalid_count,
            len(topics_raw),
        )

        return out
