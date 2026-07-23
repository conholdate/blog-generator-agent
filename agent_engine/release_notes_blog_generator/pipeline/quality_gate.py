from __future__ import annotations

from ..models.article import BlogPost
from ..models.quality import PublicationStatus, QualityAssessment, QualityScores
from . import content_metrics


def assess(post: BlogPost, seo_issues: list[str]) -> QualityAssessment:
    """Quality scoring layer (instructions.md step 9) combined with the
    publish gating logic (Engineering-signals.md).

    Every score here is computed from the actual post (see
    content_metrics.py) rather than a fixed constant — readability from a
    real Flesch Reading Ease pass, duplication_risk from intra-article
    near-duplicate paragraph detection, original_value from elaboration
    beyond the writer's fixed section skeleton, source_faithfulness/
    technical_accuracy from the code_verifier.py signals plus fact-pack
    concept coverage. None of these substitute for human editorial judgment,
    but they're honest measurements of the text, not decoration.

    Code samples here come from Aspose's own product team, not an LLM, and
    can't realistically be sandbox-executed (proprietary licensed SDK,
    missing input files/credentials — see code_verifier.py). So the gate on
    code quality is `source_verified` (does the sample still match what the
    product team actually published, or did extraction alter it) and
    `syntax_valid` (a lightweight corruption check), not the `tested` flag,
    which stays honestly False for every post.
    """
    fact_pack = post.fact_pack
    verification = fact_pack.code_verification
    body = post.body_markdown
    unsupported_claims = bool(fact_pack.facts_needing_verification)
    missing_citations = not fact_pack.facts_confirmed_from_source

    scores = QualityScores(
        technical_accuracy=content_metrics.technical_accuracy_score(unsupported_claims, verification),
        code_correctness=content_metrics.code_correctness_score(verification),
        original_value=content_metrics.original_value_score(body),
        source_faithfulness=content_metrics.source_faithfulness_score(body, fact_pack),
        seo_readiness=max(0, 9 - len(seo_issues)),
        readability=content_metrics.readability_score(body),
        duplication_risk=content_metrics.duplication_risk_score(body),
        missing_citations=missing_citations,
        unsupported_claims=unsupported_claims,
    )

    reasons = list(seo_issues)
    if not verification.source_verified:
        reasons.append("Code sample could not be matched verbatim to the product team's release notes page")
    if not verification.syntax_valid:
        reasons.append("Code sample failed a static syntax sanity check (unbalanced brackets/quotes)")
    if not verification.tested:
        reasons.append("Code sample has not been executed in a sandbox (not feasible: proprietary SDK/license/input files)")
    if unsupported_claims:
        reasons.append("Fact pack lists details needing verification")
    if scores.duplication_risk >= 6:
        reasons.append("Body contains near-duplicate paragraphs")

    needs_code_review = not verification.source_verified or not verification.syntax_valid
    if needs_code_review:
        status = PublicationStatus.NEEDS_CODE_REVIEW
    elif unsupported_claims:
        status = PublicationStatus.NEEDS_FACT_CHECK
    elif seo_issues:
        status = PublicationStatus.READY_FOR_EDITOR
    else:
        status = PublicationStatus.DRAFT_GENERATED

    return QualityAssessment(scores=scores, publication_status=status, reasons=reasons)
