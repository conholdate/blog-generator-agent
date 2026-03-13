from __future__ import annotations

import json
import logging
import re
import time
from typing import List, Optional, Dict, Any, Iterable

from openai import OpenAI

from .config import settings
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    KeywordRefiner,
    canonical_platform_label,
    contains_platform_variant,
    platform_variant_pattern,
    strip_platform_mentions,
)
from .schemas import Cluster, TopicIdea
from .tools.metrics import RunMetrics
from .tools.seo_title_polisher import SeoTitlePolishRequest, polish_title

logger = logging.getLogger(__name__)
refiner = KeywordRefiner()


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
        return canonical_platform_label(fw) or None

    @staticmethod
    def _cluster_is_serp_derived(cluster: Cluster) -> bool:
        return any((m.source or "").lower() == "serpapi" for m in cluster.members)

    @staticmethod
    def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            value = " ".join((item or "").strip().split())
            key = value.lower()
            if not value or key in seen:
                continue
            seen.add(key)
            out.append(value)
        return out


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
    def _full_product_variants(product: str) -> List[str]:
        p = (product or "").strip()
        if not p:
            return []
        base = {p, p.replace(".", " "), p.replace(" ", ".")}
        out = set()
        for v in base:
            if v.strip():
                out.add(v.strip())
                out.add(v.strip().lower())
        return sorted(out, key=len, reverse=True)

    @staticmethod
    def _brand_variants(brand: str) -> List[str]:
        b = (brand or "").strip()
        if not b:
            return []
        variants = {b, b.replace(".", " "), b.replace(" ", ".")}
        tokens = [t for t in re.split(r"[.\s/\\_-]+", b) if t]
        if tokens:
            variants.add(tokens[-1])
        out = set()
        for v in variants:
            if v.strip():
                out.add(v.strip())
                out.add(v.strip().lower())
        return sorted(out, key=len, reverse=True)

    def _analyze_serp_keyword(
            self,
            keyword: str,
            *,
            brand: str,
            product: str,
            platform_label: Optional[str],
    ) -> str:
        s = " ".join((keyword or "").strip().split())
        if not s:
            return ""

        def _strip_platform_tokens(text: str, pl: Optional[str]) -> str:
            return strip_platform_mentions(text, pl)

        out = s
        removable_terms = self._full_product_variants(product) + self._brand_variants(brand)
        for term in removable_terms:
            out = re.sub(rf"(?i)(?<!\w){re.escape(term)}(?!\w)", " ", out)

        replacements = [
            (r"(?i)\bcloud\s+sdk\b", " "),
            (r"(?i)\bsdk\b", " "),
            (r"(?i)\bcloud\b", " "),
            (r"(?i)\bapi\b", " "),
            (r"(?i)\b(code\s+sample|sample|example|examples|tutorial|guide)\b", " "),
            (r"(?i)\bhow\s+to\b", " "),
            (r"(?i)\busing\b", " "),
            (r"(?i)\bvia\b", " "),
            (r"(?i)\bwith\b", " "),
            (r"(?i)\bfor\s+developers\b", " "),
            (r"(?i)\bdevelopers?\b", " "),
            (r"(?i)\bafter\s+update\b", "after editing"),
            (r"(?i)\bsave\s+changes\s+to\b", "save edited"),
            (r"(?i)\brender\s+(pptx|ppt)\s+slides\s+after\s+editing\b", r"render \1 slide previews after editing"),
            (r"(?i)\bediting\s+powerpoint\b", "edit PowerPoint presentations"),
            (r"(?i)\bedit\s+powerpoint\b", "edit PowerPoint presentations"),
            (r"(?i)\bnotes\s+section\b", "speaker notes"),
            (r"(?i)\bonedrive\b", "OneDrive"),
        ]
        for pattern, repl in replacements:
            out = re.sub(pattern, repl, out)

        out = _strip_platform_tokens(out, platform_label)

        for src, dst in {
            "editing": "edit",
            "saving": "save",
            "rendering": "render",
            "converting": "convert",
            "exporting": "export",
            "updating": "update",
            "replacing": "replace",
            "creating": "create",
            "managing": "manage",
        }.items():
            out = re.sub(rf"(?i)\b{src}\b", dst, out)

        out = re.sub(r"(?i)\btext replace\b", "replace text", out)
        out = re.sub(r"(?i)\bslide add\b", "add slide", out)
        out = re.sub(r"(?i)\bslides add\b", "add slides", out)
        out = re.sub(r"(?i)\bfile update\b", "update file", out)
        out = re.sub(r"(?i)\bpptx update\b", "update PPTX", out)
        out = re.sub(r"(?i)\bpptx edit\b", "edit PPTX", out)
        out = re.sub(r"\s*[:,-]\s*", " ", out)
        out = re.sub(r"(?i)\b(with|via|using|for|in)\s*$", "", out).strip()
        out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")
        out = refiner.to_sentence_case(out)

        out = re.sub(r"(?i)\b(with|via|using|for|in)\s*$", "", out).strip()
        if platform_label and not self._contains_platform_variant(out, platform_label):
            out = f"{out} in {platform_label}".strip()
        out = re.sub(r"(?i)\b(in|via)\s+\.net\s+(in|via)\s+\.net\b", "in .NET", out)
        out = re.sub(r"(?i)\s{2,}", " ", out).strip(" -,:;")

        return refiner.refine(out)

    def _normalize_primary_keyword_phrase(
            self,
            keyword: str,
            platform_label: Optional[str],
    ) -> str:
        out = " ".join((keyword or "").strip().split())
        if not out:
            return ""

        had_platform = self._contains_platform_variant(out, platform_label)
        platform_token_pattern = platform_variant_pattern(platform_label)

        out = re.sub(r"(?i)\s*:\s*", ": ", out)
        out = re.sub(r"(?i)\bprogrammatically\s+", "", out)
        out = re.sub(r"(?i)\b(with|via|using|for)\s+in\s+", " in ", out)

        if platform_token_pattern:
            out = re.sub(
                rf"(?i)\s+{platform_token_pattern}\s+(?:with|via|using|for|in)\s+in\s+{re.escape(platform_label)}\b",
                f" in {platform_label}",
                out,
            )
            out = re.sub(
                rf"(?i)\s+{platform_token_pattern}\s+(?:with|via|using|for|in)\b",
                "",
                out,
            )
            out = re.sub(
                rf"(?i)\b(?:with|via|using|for|in)\s+{platform_token_pattern}\b",
                f"in {platform_label}",
                out,
            )
            out = re.sub(rf"(?i)\b(in|via)\s+{re.escape(platform_label)}\s+(in|via)\s+{re.escape(platform_label)}\b", f"in {platform_label}", out)

        out = re.sub(r"(?i)\b(with|via|using|for|in)\s*$", "", out).strip()
        out = re.sub(r"(?i)\b([a-z0-9.+#]+)(?:\s+\1\b)+", r"\1", out)
        out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")

        if platform_label and had_platform and not self._contains_platform_variant(out, platform_label):
            out = f"{out} in {platform_label}".strip()

        out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")
        return refiner.refine(out)

    def _analyze_cluster_keywords(
            self,
            raw_keywords: List[str],
            *,
            brand: str,
            product: str,
            platform_label: Optional[str],
            limit: int = 12,
    ) -> List[str]:
        analyzed = [
            self._analyze_serp_keyword(
                kw,
                brand=brand,
                product=product,
                platform_label=platform_label,
            )
            for kw in raw_keywords
        ]
        analyzed = [kw for kw in analyzed if kw]
        return self._dedupe_keep_order(analyzed)[:limit]

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
    def _contains_platform_variant(text: str, platform_label: Optional[str]) -> bool:
        return contains_platform_variant(text, platform_label)

    @staticmethod
    def _keyword_intent_key(text: str) -> str:
        s = " ".join((text or "").strip().split()).lower()
        s = re.sub(r"(?i)^(tutorial|guide|example|examples|code sample|sample)\s*:\s*", "", s)
        s = re.sub(r"(?i)\b(how to|tutorial|guide|example|examples|code sample|sample)\b", " ", s)
        s = re.sub(r"[^a-z0-9.+#]+", " ", s)
        s = re.sub(r"\s{2,}", " ", s).strip()
        return s

    @staticmethod
    def _ensure_product_in_title(title: str, product: str) -> str:
        """
        Ensure product appears in title. If missing, append 'with <product>'.
        (Avoid parentheses because they blow up title length and look spammy.)
        """
        t = (title or "").strip()
        p = (product or "").strip()
        if not t or not p:
            return t

        variants = KeywordResearchAgent._product_variants(p)
        if KeywordResearchAgent._contains_product(t, variants):
            return t

        return f"{t} with {p}"

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
        out = re.sub(r"\s+([:,\-ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â])", r"\1", out)     # space before punctuation
        out = re.sub(r"([:,\-ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â])\s{2,}", r"\1 ", out) # too many spaces after punctuation

        # Remove leading/trailing separators
        out = out.strip(" -ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â,:;")

        return out

    def generate_topics(
            self,
            brand: str,
            product: str,
            locale: str,
            clusters: List[Cluster],
            top_n: int = 10,
            seed_topic: Optional[str] = None,
            platform: Optional[str] = None,
            existing_topics: Optional[List[Dict[str, Any]]] = None,
            metrics: Optional[RunMetrics] = None,
            include_product_in_title: bool = True,
    ) -> List[TopicIdea]:
        if not clusters:
            logger.warning("generate_topics called with no clusters ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ returning empty list.")
            return []

        seed_topic_clean = " ".join((seed_topic or "").strip().split())
        seed_stopwords = {
            "a", "an", "and", "api", "best", "by", "file", "files", "for", "from", "guide",
            "how", "in", "into", "of", "on", "or", "the", "to", "tutorial", "using", "with",
        }

        def _seed_anchor_tokens(text: str) -> set[str]:
            return {
                token for token in re.findall(r"[a-z0-9.+#]+", (text or "").lower())
                if len(token) > 1 and token not in seed_stopwords
            }

        def _seed_relevance(cluster: Cluster) -> float:
            anchors = _seed_anchor_tokens(seed_topic_clean)
            if not anchors:
                return 0.0
            best_overlap = 0.0
            for member in cluster.members:
                member_tokens = set(re.findall(r"[a-z0-9.+#]+", (member.keyword or "").lower()))
                overlap = len(member_tokens.intersection(anchors))
                if overlap:
                    best_overlap = max(best_overlap, overlap / max(len(anchors), 1))
            return best_overlap

        if seed_topic_clean:
            chosen = sorted(
                clusters,
                key=lambda c: (_seed_relevance(c), getattr(c.metrics, "score", 0.0)),
                reverse=True,
            )[:1]
        else:
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
            if re.search(r"(?i)\b(with|via|using|for|in)\s*$", low):
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

        def _best_allowed_primary_keyword(candidates: List[str]) -> str:
            cleaned = [" ".join((x or "").strip().split()) for x in candidates if isinstance(x, str) and x.strip()]
            cleaned = [x for x in cleaned if _kw_is_complete(x)]
            if not cleaned:
                return ""
            if seed_topic_clean:
                anchors = {
                    token for token in re.findall(r"[a-z0-9.+#]+", seed_topic_clean.lower())
                    if len(token) > 1 and token not in {"a", "an", "and", "api", "by", "for", "from", "how", "in", "of", "on", "or", "the", "to", "using", "with"}
                }
                if anchors:
                    cleaned = sorted(
                        cleaned,
                        key=lambda x: (
                            len(set(re.findall(r"[a-z0-9.+#]+", x.lower())).intersection(anchors)),
                            len(x),
                        ),
                        reverse=True,
                    )
            return cleaned[0]

        def _fallback_supporting_keywords(primary_kw: str, candidates: List[str]) -> List[str]:
            pk_key = self._keyword_intent_key(primary_kw)
            filtered = [
                refiner.refine(x) for x in candidates
                if isinstance(x, str) and x.strip() and self._keyword_intent_key(x) != pk_key
            ]
            filtered = [x for x in filtered if _kw_is_complete(x)]
            filtered = self._dedupe_keep_order(filtered)
            if len(filtered) >= 3:
                return filtered[:5]

            low = primary_kw.lower()
            variants: List[str] = []
            action_swaps = {
                "update ": "edit ",
                "edit ": "modify ",
                "delete ": "remove ",
                "add ": "insert ",
                "convert ": "export ",
                "render ": "preview ",
            }
            for src, dst in action_swaps.items():
                if low.startswith(src):
                    variants.append(refiner.refine(re.sub(rf"(?i)^{re.escape(src)}", dst, primary_kw, count=1)))
                    break

            if platform_label:
                variants.extend([
                    refiner.refine(f"{primary_kw} tutorial"),
                    refiner.refine(f"{primary_kw} example"),
                ])

            if "pptx" in low:
                if platform_label:
                    variants.extend([
                        f"PPTX editing in {platform_label}",
                        f"Edit PPTX files in {platform_label}",
                        f"Update PowerPoint files in {platform_label}",
                    ])
                else:
                    variants.extend([
                        "PPTX editing",
                        "Edit PPTX files",
                        "Update PowerPoint files",
                    ])

            if seed_topic_clean and self._keyword_intent_key(seed_topic_clean) != pk_key:
                variants.append(refiner.refine(seed_topic_clean))

            variants = filtered + [
                refiner.refine(v) for v in variants
                if v and self._keyword_intent_key(v) != pk_key
            ]
            return self._dedupe_keep_order(variants)[:5]

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

        def _mentions_platform_label(text: str, pl: Optional[str]) -> bool:
            return contains_platform_variant(text, pl)

        def _build_title_from_primary(primary_keyword: str, cluster_id: object) -> str:
            MIN_LEN = 40
            MAX_LEN = 60

            kw = " ".join((primary_keyword or "").strip().split())
            if not kw:
                return ""

            kw_low = kw.lower()
            kw_has_platform = _mentions_platform_label(kw, platform_label)
            idx = _stable_idx(cluster_id, kw)

            def _clean(s: str) -> str:
                s = re.sub(r"\s{2,}", " ", (s or "").strip())
                return s.strip(" -ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â,:;")

            def _in_range(s: str) -> bool:
                return MIN_LEN <= len(s) <= MAX_LEN

            # Detect if keyword is already phrased as an action ("Convert ...", "Create ...", etc.)
            verb_prefixes = (
                "convert ", "create ", "generate ", "merge ", "split ", "compress ",
                "extract ", "edit ", "render ", "export ", "import ", "watermark ",
                "sign ", "ocr ",
            )
            action_intent_re = re.compile(
                r"(?i)\b(convert|create|generate|merge|split|compress|extract|edit|render|export|import|watermark|sign|ocr|update|delete|remove|add|insert|replace|modify)\b"
            )
            if platform_label:
                if kw_low.startswith("how to "):
                    candidates = [
                        kw if kw_has_platform else f"{kw} in {platform_label}",
                        f"{kw}: A Complete Tutorial" if kw_has_platform else f"{kw}: A Complete Tutorial in {platform_label}",
                        f"{kw} Guide" if kw_has_platform else f"{kw} Guide in {platform_label}",
                    ]
                elif kw_low.startswith(verb_prefixes):
                    # Keyword already contains the verb -> do NOT add another action verb
                    candidates = [
                        f"How to {kw}" if kw_has_platform else f"How to {kw} in {platform_label}",
                        kw if kw_has_platform else f"{kw} in {platform_label}",
                        f"{kw}: A Complete Tutorial" if kw_has_platform else f"{kw}: A Complete Tutorial in {platform_label}",
                    ]
                else:
                    if action_intent_re.search(kw):
                        candidates = [
                            kw if kw_has_platform else f"{kw} in {platform_label}",
                            f"How to {kw}" if kw_has_platform else f"How to {kw} in {platform_label}",
                            f"{kw}: A Complete Tutorial" if kw_has_platform else f"{kw}: A Complete Tutorial in {platform_label}",
                        ]
                    else:
                        # Noun phrase keywords like "HTML to PDF Converter"
                        candidates = [
                            kw if kw_has_platform else f"{kw} in {platform_label}",
                            f"{kw}: A Complete Tutorial" if kw_has_platform else f"{kw}: A Complete Tutorial in {platform_label}",
                            f"How to Convert {kw}" if kw_has_platform else f"How to Convert {kw} in {platform_label}",
                        ]
            else:
                if kw_low.startswith("how to "):
                    candidates = [
                        kw,
                        f"{kw}: A Complete Tutorial",
                        f"{kw} Guide",
                    ]
                elif kw_low.startswith(verb_prefixes):
                    candidates = [
                        f"How to {kw}",
                        kw,
                        f"{kw}: A Complete Tutorial",
                    ]
                else:
                    if action_intent_re.search(kw):
                        candidates = [
                            kw,
                            f"How to {kw}",
                            f"{kw}: A Complete Tutorial",
                        ]
                    else:
                        candidates = [
                            kw,
                            f"{kw}: A Complete Tutorial",
                            f"How to Convert {kw}",
                        ]
            candidates = [_clean(c) for c in candidates]

            preferred = candidates[idx]
            if _in_range(preferred) and kw in preferred:
                return preferred

            in_range = [c for c in candidates if _in_range(c) and kw in c]
            if in_range:
                target = (MIN_LEN + MAX_LEN) // 2
                return min(in_range, key=lambda x: abs(len(x) - target))

            # Fallback shortening while preserving kw verbatim
            title = preferred
            title = re.sub(r"(?i)\s*:?\s*a\s+complete\s+tutorial\b", "", title)
            title = re.sub(r"(?i)\s*:?\s*tutorial\b", "", title)
            title = re.sub(r"(?i)\s*:?\s*guide\b", "", title)
            title = _clean(title)

            if len(title) > MAX_LEN:
                title = candidates[0]

            if len(title) > MAX_LEN:
                title = kw if kw_has_platform else (_clean(f"{kw} in {platform_label}") if platform_label else kw)

            if len(title) < MIN_LEN:
                pad = " Guide"
                if len(title) + len(pad) <= MAX_LEN:
                    title = _clean(title + pad)

            if kw not in title:
                title = kw if kw_has_platform else (_clean(f"{kw} in {platform_label}") if platform_label else kw)

            return title

        def normalize_title(
                title: str,
                primary_keyword: str,
                platform_label: Optional[str],
                product: str,
                include_product_in_title: bool,
                min_len: Optional[int] = None,
                max_len: Optional[int] = None
        ) -> str:
            t = " ".join((title or "").strip().split())
            kw = " ".join((primary_keyword or "").strip().split())
            pl = (platform_label or "").strip()
            prod = (product or "").strip()

            if not t:
                return t

            # 1) Fix spacing: "JPG:a" -> "JPG: a"
            t = re.sub(r"\s*:\s*", ": ", t)
            # Normalize Step-by-Step variations in TITLES too (not only outlines)
            t = re.sub(r"(?i)\bstep\s*-\s*by\s*-\s*step\b", "Step-by-Step", t)
            t = re.sub(r"(?i)\bstep\s+by\s+step\b", "Step-by-Step", t)

            # Ban "Libraries" phrasing in titles (preferred: "Using C#")
            t = re.sub(r"(?i)\busing\s+c#\s+libraries\b", "Using C#", t)
            t = re.sub(r"(?i)\bc#\s+libraries\b", "C#", t)

            # 2) Remove any parenthetical suffixes like "(GroupDocs.Conversion Cloud)"
            # (keeps the left part, which typically contains keyword)
            t = re.sub(r"\s*\([^)]*\)\s*$", "", t).strip()

            # Clean malformed platform/preposition fragments like ".NET with in .NET"
            if pl:
                platform_token_pattern = platform_variant_pattern(pl) or re.escape(pl)

                t = re.sub(
                    rf"(?i)\s+{platform_token_pattern}\s+(?:with|via|using|for|in)\s+in\s+{re.escape(pl)}\b",
                    f" in {pl}",
                    t,
                ).strip()
                t = re.sub(
                    rf"(?i)\b(?:with|via|using|for)\s+in\s+{re.escape(pl)}\b",
                    f"in {pl}",
                    t,
                ).strip()
                t = re.sub(
                    rf"(?i)\s+{platform_token_pattern}\s+(?:with|via|using|for|in)\b",
                    "",
                    t,
                ).strip()
                t = re.sub(r"\s{2,}", " ", t).strip(" -â€“â€”,:; ")

            # 3) Enforce platform label, with a .NET/C# exception:
            # If title already specifies C#, prefer "Using C#" (no trailing "in .NET").
            if pl:
                has_csharp = bool(re.search(r"(?i)\bC#\b", t))
                has_platform_already = _mentions_platform_label(t, pl)

                if pl == ".NET" and has_csharp:
                    # Remove a trailing "in .NET" if present
                    t = re.sub(r"(?i)\s*\bin\s+\.net\s*$", "", t).strip()
                else:
                    # Normal enforcement for other cases/platforms
                    t = re.sub(rf"(?i)\s+(?:in|via)\s+{re.escape(pl)}\s+(?:in|via)\s+{re.escape(pl)}\b", f" in {pl}", t).strip()
                    t = re.sub(r"(?i)\bin\s+[A-Za-z0-9\.\+#/ ]+$", f"in {pl}", t).strip()
                    if not has_platform_already and f"in {pl}" not in t:
                        t = f"{t} in {pl}".strip()

            # 4) Product mode (title only)
            if not include_product_in_title and prod:
                # Remove only the full product name variants, not tokens like "HTML"
                variants = {prod, prod.replace(".", " "), prod.replace(" ", ".")}
                for v in sorted(variants, key=len, reverse=True):
                    t = re.sub(rf"(?i)(?<!\w){re.escape(v)}(?!\w)", "", t)
                t = re.sub(r"\s{2,}", " ", t).strip(" -ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â,:; ")
            elif prod:
                variants = _safe_product_title_variants(prod)
                for v in variants:
                    t = re.sub(
                        rf"(?i)(?<!\w){re.escape(v)}(?!\w)",
                        prod,
                        t,
                    )
                    t = re.sub(rf"(?i)([A-Za-z0-9])(?={re.escape(v)})", r"\1 ", t)
                    if pl:
                        t = re.sub(
                            rf"(?i)\s+{re.escape(v)}\s+in\s+{re.escape(pl)}$",
                            f" in {pl}",
                            t,
                        )
                    t = re.sub(
                        rf"(?i)(?<!\w){re.escape(v)}(?!\w)\s+(?<!\w){re.escape(v)}(?!\w)",
                        prod,
                        t,
                    )

            # 5) Length clamp (40ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“60): remove filler first, keep kw verbatim
            def _clean(x: str) -> str:
                return re.sub(r"\s{2,}", " ", x).strip(" -ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â,:; ")

            t = _clean(t)

            # If too long, drop "A Complete Tutorial" phrase (case-insensitive)
            if len(t) > max_len:
                t2 = re.sub(r"(?i):?\s*a\s+complete\s+tutorial\b", "", t).strip()
                t2 = _clean(t2)
                # keep only if it still contains kw verbatim (if kw is expected)
                if (not kw) or (kw and kw in t2):
                    t = t2

            # If still too long, prefer shortest core: "<kw> in <pl>"
            if len(t) > max_len and kw and pl:
                core = _clean(f"{kw} in {pl}")
                t = core

            # If still too long (very long kw), last resort: keep kw + platform even if > max
            if max_len is not None and len(t) > max_len:
                if len(t) > max_len and kw:
                    t = _clean(f"{kw} in {pl}") if pl else kw

            # If too short, add a short suffix (if room)
            if min_len is not None and len(t) < min_len:
                if len(t) < min_len:
                    suffix = " Guide"
                    if len(t) + len(suffix) <= max_len:
                        t = _clean(t + suffix)

            return t

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
            out = out.strip(" -ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â,:;")
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
            selected_keywords = _select_keywords_for_cluster(raw_keywords, limit=12)
            serp_derived = self._cluster_is_serp_derived(c)
            analyzed_keywords = (
                self._analyze_cluster_keywords(
                    selected_keywords,
                    brand=brand,
                    product=product,
                    platform_label=platform_label,
                    limit=12,
                )
                if serp_derived
                else []
            )
            payload["clusters"].append(
                {
                    "cluster_id": c.cluster_id,
                    "label": c.label,
                    "intent": c.metrics.intent,
                    "brand_fit": c.metrics.brand_fit,
                    "score": c.metrics.score,
                    "keywords": selected_keywords,
                    "keyword_strategy": "analyzed_serp" if serp_derived else "exact_cluster",
                    "analyzed_keywords": analyzed_keywords,
                }
            )

        if platform:
            payload["platform"] = platform
        if seed_topic_clean:
            payload["seed_topic"] = seed_topic_clean

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
        cluster_analyzed_keywords_map: Dict[str, List[str]] = {
            str(c["cluster_id"]): [k for k in (c.get("analyzed_keywords") or []) if isinstance(k, str)]
            for c in payload.get("clusters", [])
        }
        cluster_strategy_map: Dict[str, str] = {
            str(c["cluster_id"]): str(c.get("keyword_strategy") or "exact_cluster")
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
            "- outline (6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“10 headings)\n"
            "- target_persona\n"
            "- primary_keyword (EXACT string from cluster)\n"
            "- supporting_keywords (3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“8 EXACT strings from same cluster)\n"
            "- internal_links (0ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“5 from existing_topics only)\n\n"
            "CLUSTER CONSISTENCY\n"
            "- Do not invent keywords.\n"
        )

        system += (
            "ADDITIONAL OUTPUT REQUIREMENTS\n"
            "- Include keyword_groups with keys core_seo_keywords, long_tail_keywords, context_keywords.\n"
            "- Include editorial_notes as a list of 3ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ6 practical SEO/content bullets.\n"
            "- For clusters with keyword_strategy='exact_cluster', primary_keyword must be an EXACT string from keywords.\n"
            "- For clusters with keyword_strategy='analyzed_serp', primary_keyword must be an EXACT string from analyzed_keywords.\n"
            "- Supporting keywords and keyword_groups must stay semantically grounded in the same cluster.\n\n"
        )

        if seed_topic_clean:
            system += (
                "SEED TOPIC RULES\n"
                f"- Seed topic is '{seed_topic_clean}'.\n"
                "- Return EXACTLY 1 topic.\n"
                "- Keep the topic tightly aligned to the seed topic, not an adjacent or broader area.\n"
                "- Choose the most relevant primary_keyword for the seed topic.\n"
                "- Supporting keywords must be directly relevant variations of the same seed topic.\n\n"
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

        system += (
            "\nSERP SEO STRATEGY\n"
            "- When keyword_strategy is 'analyzed_serp', do NOT copy awkward raw SERP phrasing.\n"
            "- Rewrite the keyword plan around the feature/topic first, so it attracts broad relevant visitors, especially platform developers and AI agents parsing the page.\n"
            "- Primary keyword should be feature-led and natural, not product-led marketing copy.\n"
            "- Secondary purpose: show that the product provides that feature.\n"
            "- Use keyword_groups as follows:\n"
            "  core_seo_keywords: direct feature/category phrases with platform or format intent.\n"
            "  long_tail_keywords: specific natural-language phrases helpful for AI visibility.\n"
            "  context_keywords: semantic entities, workflow terms, file types, and adjacent concepts.\n"
            "- editorial_notes must provide practical SEO/content guidance, not fluff.\n"
        )

        system += (
            "\nTITLE LENGTH RULE (HARD)\n"
            "- Each title MUST be between 40 and 60 characters (inclusive).\n"
            "- Avoid parentheses in titles unless necessary.\n"
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
                "- Outline MUST be 6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“10 items.\n"
                "- First 4 items MUST be exactly:\n"
                f"  1) 'Using {outline_library_name} in {platform_label}'\n"
                f"  2) '{outline_library_name} features that matter for this task'\n"
                f"  3) 'Installation and setup in {platform_label}'\n"
                f"  4) 'Step-by-step implementation in {platform_label}'\n"
                "- Then append 2ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6 practical SEO sections (config, performance, troubleshooting, etc.).\n"
            )
        else:
            system += (
                "OUTLINE STRUCTURE\n"
                "- Outline MUST be 6ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“10 items.\n"
                "- First 4 items MUST be exactly:\n"
                f"  1) 'Using {outline_library_name}'\n"
                f"  2) '{outline_library_name} features that matter for this task'\n"
                "  3) 'Installation and setup'\n"
                "  4) 'Step-by-step implementation'\n"
                "- Then append 2ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6 practical SEO sections.\n"
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
        if seed_topic_clean:
            topics_raw = topics_raw[:1]

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
            kw_has_product = self._contains_product(kw, self._product_variants(outline_library_name))

            if platform_label:
                base = [
                    f"{kw} for {platform_label}" if kw_has_product else f"{kw} with {outline_library_name} for {platform_label}",
                    f"Key Features of {outline_library_name} for {platform_label}",
                    f"Installation and Setup in {platform_label}",
                    f"Step-by-Step: {kw}",
                ]
            else:
                base = [
                    kw if kw_has_product else f"{kw} with {outline_library_name}",
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

            strategy = cluster_strategy_map.get(cid, "exact_cluster")
            cluster_kws = cluster_keywords_map.get(cid, [])
            analyzed_kws = cluster_analyzed_keywords_map.get(cid, [])
            allowed_primary_keywords = analyzed_kws if strategy == "analyzed_serp" and analyzed_kws else cluster_kws

            # HARD: primary_keyword must be from the allowed keyword pool for that cluster
            if pk not in allowed_primary_keywords:
                pk = _best_allowed_primary_keyword(allowed_primary_keywords)
                t["primary_keyword"] = pk
                if not pk:
                    invalid_count += 1
                    continue
            if not _kw_is_complete(pk):
                pk = _best_allowed_primary_keyword(allowed_primary_keywords)
                t["primary_keyword"] = pk
                if not pk:
                    invalid_count += 1
                    continue
            pk = self._normalize_primary_keyword_phrase(pk, platform_label)
            t["primary_keyword"] = pk
            if not pk or not _kw_is_complete(pk):
                pk = self._normalize_primary_keyword_phrase(_best_allowed_primary_keyword(allowed_primary_keywords), platform_label)
                t["primary_keyword"] = pk
                if not pk or not _kw_is_complete(pk):
                    invalid_count += 1
                    continue
            pk_intent_key = self._keyword_intent_key(pk)

            keyword_groups = t.get("keyword_groups") or {}
            if not isinstance(keyword_groups, dict):
                keyword_groups = {}
            product_variants = self._product_variants(product)
            for key in ("core_seo_keywords", "long_tail_keywords", "context_keywords"):
                vals = keyword_groups.get(key) or []
                if isinstance(vals, list):
                    refined_vals = [refiner.refine(v) for v in vals if isinstance(v, str)]
                    refined_vals = [
                        v for v in refined_vals
                        if v and _kw_is_complete(v) and self._keyword_intent_key(v) != pk_intent_key and not self._contains_product(v, product_variants)
                    ]
                    keyword_groups[key] = self._dedupe_keep_order(refined_vals)
                else:
                    keyword_groups[key] = []
            t["keyword_groups"] = keyword_groups

            supporting_keywords = t.get("supporting_keywords") or []
            if not isinstance(supporting_keywords, list):
                supporting_keywords = []
            supporting_keywords = [
                refiner.refine(v) for v in supporting_keywords if isinstance(v, str)
            ]
            supporting_keywords = [
                v for v in supporting_keywords
                if v and _kw_is_complete(v) and self._keyword_intent_key(v) != pk_intent_key and not self._contains_product(v, product_variants)
            ]
            supporting_keywords = self._dedupe_keep_order(supporting_keywords)
            if len(supporting_keywords) < 3:
                supporting_keywords = (
                    supporting_keywords
                    + keyword_groups.get("core_seo_keywords", [])
                    + keyword_groups.get("long_tail_keywords", [])
                )
                supporting_keywords = self._dedupe_keep_order(
                    [
                        v for v in supporting_keywords
                        if _kw_is_complete(v) and self._keyword_intent_key(v) != pk_intent_key and not self._contains_product(v, product_variants)
                    ]
                )
            if len(supporting_keywords) < 3:
                supporting_keywords = _fallback_supporting_keywords(pk, supporting_keywords + allowed_primary_keywords)
            t["supporting_keywords"] = supporting_keywords[:5]
            if not any(keyword_groups.get(key) for key in ("core_seo_keywords", "long_tail_keywords", "context_keywords")):
                keyword_groups["core_seo_keywords"] = supporting_keywords[:3]
                keyword_groups["long_tail_keywords"] = supporting_keywords[3:5]
                keyword_groups["context_keywords"] = []
                t["keyword_groups"] = keyword_groups

            editorial_notes = t.get("editorial_notes") or []
            if isinstance(editorial_notes, list):
                t["editorial_notes"] = [
                    refiner.to_sentence_case(v)
                    for v in editorial_notes
                    if isinstance(v, str) and v.strip()
                ][:6]
            else:
                t["editorial_notes"] = []

            # HARD: build title from primary keyword (guarantees pk appears verbatim)
            # 1) HARD: build title from primary keyword
            t["title"] = _build_title_from_primary(pk, cid)

            # 2) Apply product title mode (SAFE)
            if include_product_in_title:
                t["title"] = self._ensure_product_in_title(t["title"], product)
            else:
                t["title"] = _remove_product_safely(t["title"], product)

            # 3) FINAL: normalize AFTER all edits (fixes :a, removes any trailing (...), enforces platform + length)
            t["title"] = normalize_title(
                title=t.get("title", ""),
                primary_keyword=t.get("primary_keyword", ""),
                platform_label=platform_label,
                product=product,
                include_product_in_title=include_product_in_title,
                min_len=40,
                max_len=100,
            )
            if include_product_in_title:
                t["title"] = self._ensure_product_in_title(t["title"], product)
            # 4) OPTIONAL: LLM second-pass polish (Agents SDK) with hard fallback
            polished = polish_title(
                SeoTitlePolishRequest(
                    raw_title=t["title"],
                    primary_keyword=pk,
                    supporting_keywords=list(t.get("supporting_keywords") or []),
                    platform_label=platform_label,
                    product=product,
                    include_product_in_title=include_product_in_title,
                    min_len=40,
                    max_len=60,
                )
            )

            if polished:
                # Apply the polished title, then re-apply your deterministic normalizer
                t["title"] = polished

                # Re-apply safe product enforcement (keeps your existing behavior)
                if include_product_in_title:
                    t["title"] = self._ensure_product_in_title(t["title"], product)
                else:
                    t["title"] = _remove_product_safely(t["title"], product)

                # Re-normalize to enforce platform + length + colon spacing, etc.
                t["title"] = normalize_title(
                    title=t.get("title", ""),
                    primary_keyword=t.get("primary_keyword", ""),
                    platform_label=platform_label,
                    product=product,
                    include_product_in_title=include_product_in_title,
                    min_len=0,
                    max_len=100,
                )
                if include_product_in_title:
                    t["title"] = self._ensure_product_in_title(t["title"], product)

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
