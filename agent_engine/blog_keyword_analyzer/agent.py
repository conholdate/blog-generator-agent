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

        fw_label = self._platform_label(platform)
        platform_label: Optional[str] = fw_label

        # Outline ALWAYS uses product name (independent of title mode)
        outline_library_name: str = product.strip() if (product or "").strip() else "the library"

        # -------------------------
        # Keyword helpers
        # -------------------------
        def _kw_is_complete(kw: str) -> bool:
            """Reject fragments like 'to jpg', trailing 'to', etc."""
            if not kw or not isinstance(kw, str):
                return False
            s = " ".join(kw.strip().split())
            low = s.lower()

            if low.startswith("to "):
                return False
            if low.endswith(" to") or re.search(r"\bto\s*$", low):
                return False
            if low.startswith("how to "):
                return False

            # Reject "convert to jpg" missing source
            if re.search(r"\bconvert\s+to\s+\w+\b", low) and not re.search(
                    r"\bconvert\s+\w+(\s+\w+){0,6}\s+to\s+\w+", low
            ):
                return False

            # Accept "x to y" and "convert x to y"
            return (" to " in low and len(low.split()) >= 3) or (len(low.split()) >= 3)

        def _select_keywords_for_cluster(raw: List[str], limit: int = 12) -> List[str]:
            cleaned = [" ".join(k.strip().split()) for k in raw if isinstance(k, str) and k.strip()]
            if not cleaned:
                return []
            complete = [k for k in cleaned if _kw_is_complete(k)]
            ordered = complete + [k for k in cleaned if k not in complete]
            return ordered[:limit]

        # -------------------------
        # Deterministic SEO title builder (PRIMARY KEYWORD MUST APPEAR VERBATIM)
        # -------------------------
        def _stable_idx(cluster_id: object, kw: str) -> int:
            seed = f"{cluster_id}::{kw}"
            h = 0
            for ch in seed:
                h = (h * 33 + ord(ch)) % 10_000_000
            return h % 3

        def _build_title_from_primary(primary_keyword: str, cluster_id: object) -> str:
            """
            Build a grammatical SEO title, while ensuring primary_keyword appears verbatim.
            Works for both:
              - 'convert html to jpg'
              - 'html to jpg'
            """
            kw = " ".join((primary_keyword or "").strip().split())
            if not kw:
                return ""

            idx = _stable_idx(cluster_id, kw)

            # We do NOT rewrite kw; we only wrap around it.
            # Avoid "How to {kw}" (bad for noun phrase keywords). Use "How to Convert {kw}" instead.
            if platform_label:
                if idx == 0:
                    title = f"{kw} in {platform_label}"
                elif idx == 1:
                    title = f"How to Convert {kw} in {platform_label}"
                else:
                    title = f"{kw}: A Complete Tutorial in {platform_label}"
            else:
                if idx == 0:
                    title = kw
                elif idx == 1:
                    title = f"How to Convert {kw}"
                else:
                    title = f"{kw}: A Complete Tutorial"

            # HARD guarantee: kw must be present verbatim
            if kw not in title:
                title = f"{kw} in {platform_label}" if platform_label else kw

            return title

        # -------------------------
        # Safe product enforcement for titles
        # IMPORTANT: In "product NOT in title" mode, do NOT remove the last token (e.g., HTML).
        # -------------------------
        def _safe_product_title_variants(prod: str) -> List[str]:
            """
            Only variants that represent the full product name, not the last token.
            Example: Aspose.HTML -> ['Aspose.HTML', 'Aspose HTML', lowercase variants]
            """
            p = (prod or "").strip()
            if not p:
                return []
            base = {p, p.replace(".", " "), p.replace(" ", ".")}
            out = set()
            for v in base:
                if v.strip():
                    out.add(v.strip())
                    out.add(v.strip().lower())
            return sorted(out, key=len, reverse=True)

        def _remove_product_safely(title: str, prod: str) -> str:
            t = (title or "").strip()
            if not t or not prod:
                return t
            variants = _safe_product_title_variants(prod)
            out = t
            for v in variants:
                pat = rf"(?i)(?<!\w){re.escape(v)}(?!\w)"
                out = re.sub(pat, "", out)
            out = re.sub(r"\(\s*\)", "", out)
            out = re.sub(r"\[\s*\]", "", out)
            out = re.sub(r"\s{2,}", " ", out).strip()
            out = out.strip(" -–—,:;")
            return out

        # -------------------------
        # Build payload
        # -------------------------
        payload: Dict[str, Any] = {
            "brand": brand,
            "product": product,
            "locale": locale,
            "clusters": [],
        }

        for c in chosen:
            raw_keywords = [m.keyword for m in c.members]
            payload["clusters"].append(
                {
                    "cluster_id": c.cluster_id,
                    "label": c.label,
                    "intent": c.metrics.intent,
                    "brand_fit": c.metrics.brand_fit,
                    "score": c.metrics.score,
                    "keywords": _select_keywords_for_cluster(raw_keywords, limit=12),
                }
            )

        if platform:
            payload["platform"] = platform

        if existing_topics:
            payload["existing_topics"] = [
                {"title": e.get("title"), "url": e.get("url"), "slug": e.get("slug"), "platforms": e.get("platforms")}
                for e in existing_topics
            ]

        if settings.DEBUG:
            logger.debug("Payload sent to LLM (truncated): %s", json.dumps(payload, indent=2)[:2000])

        # Build cluster->keywords map for strict primary_keyword validation
        cluster_keywords_map: Dict[str, List[str]] = {
            str(c["cluster_id"]): [k for k in (c.get("keywords") or []) if isinstance(k, str)]
            for c in payload.get("clusters", [])
        }

        # -------------------------
        # Prompt
        # -------------------------
        system = (
            "You are a 'Blog Keyword Analyzer' agent.\n\n"
            "Return STRICT JSON with top-level key 'topics'.\n\n"
            "Each topic MUST include:\n"
            "- cluster_id\n"
            "- title\n"
            "- angle\n"
            "- outline (6–10 headings)\n"
            "- target_persona\n"
            "- primary_keyword (EXACT string from cluster)\n"
            "- supporting_keywords (3–8 EXACT strings from same cluster)\n"
            "- internal_links (0–5 from existing_topics only)\n\n"
            "CLUSTER CONSISTENCY\n"
            "- Do not invent keywords.\n"
        )

        system += "platform / LANGUAGE RULES\n"
        if platform_label:
            system += (
                f"- Target platform is '{platform_label}'.\n"
                f"- '{platform_label}' MUST appear in EVERY title.\n"
                "- Do NOT mention other platforms.\n"
            )

        system += (
            "\nTITLE RULES\n"
            "- The title MUST contain the exact primary_keyword verbatim.\n"
            "- The title MUST be grammatical.\n"
            "- Avoid incomplete titles like 'To PDF in .NET'.\n"
            "\n"
        )

        if include_product_in_title:
            system += (
                "\nPRODUCT TITLE RULE\n"
                f"- The product name '{product}' MUST appear in EVERY title.\n"
            )
        else:
            system += (
                "\nPRODUCT TITLE RULE\n"
                f"- The product name '{product}' MUST NOT appear in ANY title.\n"
            )

        system += (
            "\nOUTLINE RULES\n"
            f"- In the outline, ALWAYS refer to the library as '{outline_library_name}'.\n"
            "- NEVER use 'SDK', 'the SDK', or 'the library' in the outline.\n"
            "- Do NOT include 'Use Cases' and do NOT use the words 'Use Case'.\n"
            "\n"
        )

        if platform_label:
            system += (
                "OUTLINE STRUCTURE\n"
                "- Outline MUST be 6–10 items.\n"
                "- First 4 items MUST be exactly:\n"
                f"  1) 'Using {outline_library_name} in {platform_label}'\n"
                f"  2) '{outline_library_name} features that matter for this task'\n"
                f"  3) 'Installation and setup in {platform_label}'\n"
                f"  4) 'Step-by-step implementation in {platform_label}'\n"
                "- Then append 2–6 practical SEO sections (config, performance, troubleshooting, etc.).\n"
            )
        else:
            system += (
                "OUTLINE STRUCTURE\n"
                "- Outline MUST be 6–10 items.\n"
                "- First 4 items MUST be exactly:\n"
                f"  1) 'Using {outline_library_name}'\n"
                f"  2) '{outline_library_name} features that matter for this task'\n"
                "  3) 'Installation and setup'\n"
                "  4) 'Step-by-step implementation'\n"
                "- Then append 2–6 practical SEO sections.\n"
            )

        system += (
            "\nSTRICT JSON RULES\n"
            "- Return ONLY JSON.\n"
            '- Single object: {"topics":[...]}\n'
            "- Double quotes only.\n"
            "- No trailing commas.\n"
        )

        if settings.DEBUG:
            logger.debug("System prompt for LLM:\n%s", system)

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

        logger.info("Calling LLM to generate topics...")
        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(**request_kwargs)
        dt = time.perf_counter() - t0
        logger.info("LLM call completed in %.3f seconds", dt)

        usage = getattr(resp, "usage", None)
        if usage is not None and metrics is not None:
            metrics.llm_prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            metrics.llm_completion_tokens += getattr(usage, "completion_tokens", 0) or 0

        txt = resp.choices[0].message.content or ""
        logger.debug("Raw LLM response (truncated to 1200 chars): %s", txt[:1200])

        # Parse JSON
        try:
            data_obj: Any = json.loads(txt)
        except json.JSONDecodeError:
            json_block = self._extract_json_block(txt)
            if not json_block:
                logger.error("No JSON object found in LLM output; returning no topics.")
                return []
            data_obj = json.loads(json_block)

        if not isinstance(data_obj, dict):
            logger.error("LLM JSON payload is not an object; returning no topics.")
            return []

        topics_raw = data_obj.get("topics", [])
        if not isinstance(topics_raw, list):
            logger.error("'topics' key missing or not a list; returning no topics.")
            return []

        # -------------------------
        # Deterministic outline post-processing
        # -------------------------
        def _normalize_outline_items(items: Any) -> List[str]:
            if not isinstance(items, list):
                return []
            fixed: List[str] = []
            for s in items:
                if not isinstance(s, str):
                    continue
                s2 = " ".join(s.strip().split())
                s2 = re.sub(r"(?i)\bthe\s+sdk\b", outline_library_name, s2)
                s2 = re.sub(r"(?i)\bsdk\b", outline_library_name, s2)
                s2 = re.sub(r"(?i)\bthe\s+library\b", outline_library_name, s2)
                s2 = re.sub(r"(?i)\bthis\s+library\b", outline_library_name, s2)
                s2 = re.sub(r"(?i)\bstep\s*-\s*by\s*-\s*step\b", "Step-by-Step", s2)
                s2 = re.sub(r"(?i)\bstep\s*by\s*step\b", "Step-by-Step", s2)

                # NEW: enforce spacing after colon (fixes "Step-by-Step:Save" -> "Step-by-Step: Save")
                s2 = re.sub(r"\s*:\s*", ": ", s2)

                # NEW: collapse any double spaces introduced
                s2 = re.sub(r"\s{2,}", " ", s2).strip()
                if re.search(r"(?i)\buse\s+cases?\b", s2):
                    continue
                fixed.append(s2)
            return fixed

        def _force_first4_outline(outline: List[str], primary_kw: str) -> List[str]:
            kw = " ".join((primary_kw or "").strip().split())

            if platform_label:
                base = [
                    f"{kw} with {outline_library_name} for {platform_label}",
                    f"Key Features of {outline_library_name} for {platform_label}",
                    f"Installation and Setup in {platform_label}",
                    f"Step-by-Step: {kw}",
                ]
            else:
                base = [
                    f"{kw} with {outline_library_name}",
                    f"Key Features of {outline_library_name}",
                    "Installation and Setup",
                    f"Step-by-Step: {kw}",
                ]
            base = [s.replace("{PRIMARY_KEYWORD}", kw) for s in base]
            rest = outline[4:] if len(outline) > 4 else []
            outline2 = base + rest

            fillers = [
                "Configuration options and output quality",
                "Handling CSS, fonts, images, and layout fidelity",
                "Pagination, headers, footers, and page size control",
                "Batch processing and performance tuning",
                "Working with URLs, local files, and streams",
                "Error handling and troubleshooting",
                "Testing, validation, and regression checks",
                "Security, sandboxing, and safe inputs",
            ]
            seen = set(x.lower() for x in outline2)
            for f in fillers:
                if len(outline2) >= 6:
                    break
                if f.lower() not in seen:
                    outline2.append(f)
                    seen.add(f.lower())

            return outline2[:10]

        # -------------------------
        # Parse + HARD title enforcement
        # -------------------------
        out: List[TopicIdea] = []
        invalid_count = 0

        for t in topics_raw:
            if not isinstance(t, dict):
                invalid_count += 1
                continue

            cid = str(t.get("cluster_id", "")).strip()
            pk = " ".join((t.get("primary_keyword") or "").strip().split())

            # HARD: primary_keyword must be exact keyword from that cluster (prevents 'to jpg' fragments)
            cluster_kws = cluster_keywords_map.get(cid, [])
            if pk not in cluster_kws:
                invalid_count += 1
                continue
            if not _kw_is_complete(pk):
                invalid_count += 1
                continue

            # HARD: build title from primary keyword (guarantees pk appears verbatim)
            t["title"] = _build_title_from_primary(pk, cid)

            # Product title mode enforcement (SAFE)
            if include_product_in_title:
                t["title"] = self._ensure_product_in_title(t["title"], product)
            else:
                # Do NOT call self._remove_product_from_title (it removes 'HTML' for Aspose.HTML). :contentReference[oaicite:1]{index=1}
                t["title"] = _remove_product_safely(t["title"], product)

            # Outline enforcement
            if "outline" in t:
                t["outline"] = _force_first4_outline(_normalize_outline_items(t.get("outline")), pk)

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