from __future__ import annotations

from collections import Counter
from pathlib import Path

from hugo_blog_audit_agent.auditor import audit_content, audit_product_context, run_audit
from hugo_blog_audit_agent.models import BlogConfig
from hugo_blog_audit_agent.policy.evaluator import build_post_facts
from hugo_blog_audit_agent.reports import write_reports
from hugo_blog_audit_agent.scanner import scan_markdown
from tests.helpers import make_repo

def test_developer_audience_audit_adds_fit_issues(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo) if p.language == "fr")
    issues = audit_content(post, BlogConfig("Test", str(repo), developer_audience=True))
    issue_types = {issue.issue_type for issue in issues}
    assert "missing_code_example_for_developers" in issue_types
    assert "missing_setup_context" in issue_types

def test_unverified_product_mentions_are_flagged(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    post.body += "\n\nUse Aspose.DICOM for medical images and Aspose.Imaging for image processing."
    issues = audit_content(post, BlogConfig("Test", str(repo), known_product_mentions=["Aspose.Words", "Aspose.Imaging"]))
    product_issue = next(issue for issue in issues if issue.issue_type == "unverified_product_mention")
    assert product_issue.severity == "High"
    assert "Aspose.DICOM" in product_issue.explanation
    assert "Aspose.Imaging" not in product_issue.explanation

def test_known_product_subnamespaces_are_not_unverified_mentions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    post.body += "\n\n```csharp\nusing Aspose.BarCode.Generation;\n```\n\nUse Aspose.DICOM for medical images."
    config = BlogConfig("Test", str(repo), known_product_mentions=["Aspose.BarCode"])

    issues = audit_content(post, config)
    product_issue = next(issue for issue in issues if issue.issue_type == "unverified_product_mention")
    facts = build_post_facts(post, Counter(), Counter(), None, config)

    assert "Aspose.DICOM" in product_issue.explanation
    assert "Aspose.BarCode.Generation" not in product_issue.explanation
    assert facts["unverified_product_names"] == "Aspose.DICOM"

def test_product_mentions_inside_code_blocks_are_not_editorial_findings(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    post.body += "\n\n```csharp\nusing Aspose.DICOM;\nusing Aspose.BarCode.Generation;\n```\n"
    config = BlogConfig("Test", str(repo), known_product_mentions=["Aspose.Words", "Aspose.BarCode"])

    issues = audit_content(post, config)
    facts = build_post_facts(post, Counter(), Counter(), None, config)

    assert not any(issue.issue_type == "unverified_product_mention" for issue in issues)
    assert facts["unverified_product_mentions"] == 0
    assert facts["unverified_product_names"] == ""

def test_product_config_display_names_are_verified_mentions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    post.body += "\n\nAspose.Medical integrates with Aspose.Imaging and Aspose.PDF for healthcare workflows."
    config = BlogConfig(
        "Test",
        str(repo),
        known_product_mentions=["Aspose.Words", "Aspose.Imaging", "Aspose.PDF"],
        product_configs={"medical": {"display_name": "Aspose.Medical"}},
    )

    issues = audit_content(post, config)
    facts = build_post_facts(post, Counter(), Counter(), None, config)

    assert not any(issue.issue_type == "unverified_product_mention" for issue in issues)
    assert facts["unverified_product_mentions"] == 0

def test_product_links_do_not_treat_aspose_domains_as_product_mentions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    post.body += (
        "\n\n[Aspose.BarCode for .NET](https://products.aspose.com/barcode/net/) "
        "works with [Aspose.Medical](https://products.aspose.com/medical/) for healthcare workflows."
    )
    config = BlogConfig(
        "Test",
        str(repo),
        known_product_mentions=["Aspose.Words", "Aspose.BarCode"],
        product_configs={"medical": {"display_name": "Aspose.Medical"}},
    )

    issues = audit_content(post, config)
    facts = build_post_facts(post, Counter(), Counter(), None, config)

    assert not any(issue.issue_type == "unverified_product_mention" for issue in issues)
    assert facts["unverified_product_mentions"] == 0
    assert "aspose.com" not in facts["unverified_product_names"]

def test_product_context_uses_formats_actions_and_links(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post = next(p for p in scan_markdown(repo, include_translations=False))
    product_config = {
        "display_name": "Aspose.BarCode",
        "formats": ["QR", "DataMatrix"],
        "actions": ["generate", "read"],
        "docs_pages": {"python_net": "https://docs.aspose.com/barcode/python-net/"},
        "money_pages": {"python_net": "https://products.aspose.com/barcode/python-net/"},
    }
    issues = audit_product_context(post, product_config)
    issue_types = {issue.issue_type for issue in issues}
    assert "missing_product_format_context" in issue_types
    assert "missing_product_action_context" in issue_types
    assert "missing_product_docs_link" in issue_types
    assert "missing_product_page_link" in issue_types

def test_policy_rules_ground_existing_issues(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """id: test-policy
segment: content_quality
intended_audiences:
  - Developers
rules:
  - rule_id: TEST-001
    id: missing_faq
    severity: Opportunity
    condition:
      faq_like_sections_eq: 0
    evidence: [faq_like_sections]
    explanation: Missing FAQ by policy.
    recommended_fix: Add FAQs.
""",
        encoding="utf-8",
    )
    result = run_audit(BlogConfig("Test", str(repo), content_dir="content", policy_files=[str(policy)]), None, "report", None, True, False, tmp_path / "work")
    fr = next(post for post in result.posts if post.language == "fr")
    faq_issue = next(issue for issue in fr.issues if issue.issue_type == "missing_faq")
    assert faq_issue.policy_id == "test-policy"
    assert faq_issue.rule_id == "TEST-001"
    assert faq_issue.evidence == "faq_like_sections=0"
    assert faq_issue.intended_audiences == ["Developers"]

def test_policy_created_internal_link_issue_uses_source_line(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = run_audit(
        BlogConfig("Test", str(repo), content_dir="content", policy_files=[str(Path("policies/internal-linking.yaml").resolve())]),
        None,
        "report",
        None,
        True,
        False,
        tmp_path / "work",
    )

    assert any(
        issue.issue_type == "too_few_outgoing_internal_links" and issue.line == 17 and issue.policy_id == "internal-linking"
        for post in result.posts
        for issue in post.issues
    )

def test_missing_internal_link_issues_do_not_point_to_first_body_line(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_path = repo / "content" / "Aspose.blog" / "words" / "sample-post" / "index.md"
    post_path.write_text(post_path.read_text(encoding="utf-8").replace("\n[Related](/words/related/)\n", "\n"), encoding="utf-8")
    result = run_audit(
        BlogConfig("Test", str(repo), content_dir="content", policy_files=[str(Path("policies/internal-linking.yaml").resolve())]),
        None,
        "report",
        None,
        True,
        False,
        tmp_path / "work",
    )

    aggregate_post_issues = [
        issue
        for post in result.posts
        for issue in post.issues
        if issue.issue_type in {"weak_internal_links", "too_few_outgoing_internal_links"}
    ]
    aggregate_link_issues = [
        issue
        for issue in result.internal_link_issues
        if issue.issue_type in {"too_few_outgoing_internal_links", "orphan_post"}
    ]

    assert aggregate_post_issues
    assert aggregate_link_issues
    assert all(issue.line == 0 for issue in aggregate_post_issues)
    assert all(issue.line == 0 for issue in aggregate_link_issues)
    out = tmp_path / "output"
    write_reports(result, out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False)
    action_items = (out / "audit-action-items.md").read_text(encoding="utf-8")
    assert "| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact |" in action_items
    assert "| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |" not in action_items
    assert "Post-level" in action_items
