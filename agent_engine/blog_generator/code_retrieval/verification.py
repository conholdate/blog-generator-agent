"""
Verification Gate: cheap, static checks only - no compiling/running code.
That's intentionally out of scope for Phase 1 (and belongs in the separate,
later "sandbox validation" phase per the architecture, not mixed into
matching). This gate exists to catch the case filename similarity alone
can't: a plausible-looking filename whose actual content is off-topic or,
per the reviewed architecture's hard-constraint requirement, the wrong
product.

The header-comment format (// Title: ... / // Description: ... etc.) was
only confirmed present on one file in one repo (aspose-cells) as of the
architecture writeup - so header-based checks degrade gracefully to "not
available" rather than failing when a repo doesn't use that convention.
"""
import re
from dataclasses import dataclass, field

from .normalizer import candidate_terms

HEADER_FIELD_RE = re.compile(r"^//\s*(Title|Description|Keywords|Developer Intent)\s*:\s*(.+)$", re.MULTILINE)

MIN_CODE_LENGTH = 200  # chars; filters out stub/placeholder files


@dataclass
class VerificationResult:
    header_present: bool
    header_topic_score: float
    namespace_match: bool
    non_trivial_length: bool
    checks: dict = field(default_factory=dict)
    passed: bool = False
    score: float = 0.0


def parse_header(file_content: str) -> dict[str, str]:
    fields = {}
    for match in HEADER_FIELD_RE.finditer(file_content):
        fields[match.group(1)] = match.group(2).strip()
    return fields


def verify(file_content: str, query_terms: set[str], url_prefix: str) -> VerificationResult:
    header = parse_header(file_content)
    header_present = bool(header)
    header_text = " ".join(header.values())
    header_topic_score = (
        len(query_terms & candidate_terms(header_text)) / len(query_terms)
        if header_present and query_terms
        else 0.0
    )

    namespace_match = f"aspose.{url_prefix}".lower() in file_content.lower()
    non_trivial_length = len(file_content.strip()) >= MIN_CODE_LENGTH

    # Hard constraint (per reviewed architecture): reject if nothing ties this
    # file to the requested product - neither the namespace nor the header
    # mentions it. A repo is already scoped to one product by construction,
    # so this is a data-quality safety net, not the primary mechanism.
    header_mentions_product = url_prefix.lower() in header_text.lower()
    passed = (namespace_match or header_mentions_product) and non_trivial_length

    checks = {
        "header_present": header_present,
        "namespace_match": namespace_match,
        "non_trivial_length": non_trivial_length,
        "header_topic_relevant": header_topic_score > 0,
    }

    signals = [namespace_match, non_trivial_length]
    if header_present:
        signals.append(header_topic_score > 0.3)
    score = sum(1 for s in signals if s) / len(signals)

    return VerificationResult(
        header_present=header_present,
        header_topic_score=round(header_topic_score, 4),
        namespace_match=namespace_match,
        non_trivial_length=non_trivial_length,
        checks=checks,
        passed=passed,
        score=round(score, 4),
    )
