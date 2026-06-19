from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.auditor import audit_content, run_audit, score_post
from hugo_blog_audit_agent.hugo import detect_hugo_project
from hugo_blog_audit_agent.models import AuditResult, BlogConfig
from hugo_blog_audit_agent.reports import write_reports
from hugo_blog_audit_agent.scanner import scan_markdown
from tests.helpers import make_repo

def test_report_generation_and_draft_disabled_by_default(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = run_audit(BlogConfig("Test", str(repo), content_dir="content", expected_languages=["en", "fr", "de"]), None, "report", None, True, False, tmp_path / "work")
    assert any(issue.issue_type == "weak_internal_links" and issue.line == 17 for post in result.posts for issue in post.issues)
    assert any(issue.issue_type == "too_few_outgoing_internal_links" and issue.line == 17 for issue in result.internal_link_issues)
    assert any(issue.issue_type == "orphan_post" and issue.line == 0 for issue in result.internal_link_issues)
    out = tmp_path / "output"
    write_reports(result, out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False)
    assert (out / "audit-action-items.md").exists()
    assert not (out / "complete-seo-audit.md").exists()
    assert not (out / "audit-summary.md").exists()
    assert not (out / "code-audit.md").exists()
    assert not (out / "post-audit.csv").exists()
    assert not (out / "translation-audit.md").exists()
    assert not (out / "draft-fixes").exists()
    action_items = (out / "audit-action-items.md").read_text(encoding="utf-8")
    assert "# Audit Action Items" in action_items
    assert "## Audit Run" in action_items
    assert "| Blog | Test |" in action_items
    assert "| Product | All products |" in action_items
    assert "| Mode | report |" in action_items
    assert "| Total scanned blog posts | 2 |" in action_items
    assert "### Create Word Documents in Python" in action_items
    assert "File: `content/Aspose.blog/words/sample-post/index.md`" in action_items
    assert "### Sitewide / Technical" in action_items
    assert "| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact |" in action_items
    assert "| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |" not in action_items
    assert "| ID | Priority | Severity | Area | Issue | File | Line | Post Priority | Recommended Action | Effort | Impact | Source |" not in action_items
    assert "## Quick-Win Queue" not in action_items
    assert "broken_internal_link" in action_items
    assert "| 17 |" in action_items
    assert "Detailed reports are generated only when `--detailed-outputs true` is passed." in action_items

    detailed_out = tmp_path / "detailed-output"
    write_reports(result, detailed_out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False, detailed_outputs=True)
    assert (detailed_out / "complete-seo-audit.md").exists()
    assert (detailed_out / "audit-summary.md").exists()
    assert (detailed_out / "code-audit.md").exists()
    assert (detailed_out / "audit-action-items.md").exists()
    assert (detailed_out / "post-audit.csv").exists()
    summary = (detailed_out / "audit-summary.md").read_text(encoding="utf-8")
    assert "## Audit Segment Summary" in summary
    assert "| Segment | Scope | Key Metric | Issues | Status | Detailed Report |" in summary
    assert "Code/API Audit" in summary
    assert "| Severity | Issue | Policy | Rule | Evidence | Audience | File | Explanation | Recommended Fix | Effort | Impact |" in (detailed_out / "internal-linking-audit.md").read_text(encoding="utf-8")
    assert "| Severity | Issue | Policy | Rule | Evidence | Audience | File | Explanation | Recommended Fix | Effort | Impact |" in (detailed_out / "quick-wins.md").read_text(encoding="utf-8")
    complete = (detailed_out / "complete-seo-audit.md").read_text(encoding="utf-8")
    assert "## SEO Scorecard" in complete
    assert "## Per-Post SEO Segment Score Table" in complete
    assert "| Blog Post | Title | Language | Content Quality | On-Page SEO | Technical SEO | Internal Linking | Translation SEO | Developer Audience Fit | Growth Opportunity | Priority | Issues | Top Issues |" in complete
    assert "## Priority Roadmap" in complete
    code_audit = (detailed_out / "code-audit.md").read_text(encoding="utf-8")
    assert "# Code Audit" in code_audit
    assert "## API Reference Sources" in code_audit
    assert "## Per-Post Code Coverage" in code_audit
    assert "## Class/Member Resolution Details" in code_audit
    detailed_action_items = (detailed_out / "audit-action-items.md").read_text(encoding="utf-8")
    assert "| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |" in detailed_action_items
    assert "internal-linking-audit.md" in detailed_action_items

def test_draft_fix_generation_enabled_by_flag(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = run_audit(BlogConfig("Test", str(repo), content_dir="content", expected_languages=["en", "fr"]), None, "report-with-draft-fixes", None, True, False, tmp_path / "work")
    out = tmp_path / "output"
    write_reports(result, out, include_suggestions=True, draft_fixes=True, max_draft_fixes=1, priority_only=False)
    assert (out / "draft-fixes" / "index.csv").exists()

def test_draft_fix_rewrites_unresolved_python_api_module(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "generate-code-39-barcode-in-python"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Code 39 Barcode in Python"
description: "Learn to generate Code 39 barcodes in Python."
---

Aspose.BarCode supports barcode generation and recognition APIs for Python developers.

```python
import asposebarcode as barcode

generator = barcode.BarCodeGenerator()
generator.encode_type = barcode.EncodeTypes.CODE_39_STANDARD
generator.code_text = "ABC123"
generator.save("code39.png", barcode.BarCodeImageFormat.PNG)
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        content_dir="content",
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode", "Aspose.BarCode", "com.aspose.barcode"],
                    "known_symbols": ["BarcodeGenerator", "EncodeTypes", "BarCodeImageFormat"],
                }
            ],
        },
    )
    post.issues = audit_content(post, config)
    post.scores = score_post(post)
    assert any(issue.issue_type == "unresolved_api_module" for issue in post.issues)

    out = tmp_path / "output"
    result = AuditResult(config, repo, detect_hugo_project(repo), [post], [], [], [])
    write_reports(result, out, include_suggestions=True, draft_fixes=True, max_draft_fixes=None, priority_only=False)

    draft = (out / "draft-fixes" / post.relative_path).read_text(encoding="utf-8")
    assert "import asposebarcode as barcode" not in draft
    assert "import aspose.barcode.generation as barcode" in draft
    assert "Applied fixes: unresolved_api_module: asposebarcode -> aspose.barcode.generation" in draft
