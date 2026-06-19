from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.auditor import group_translations, run_audit, score_post
from hugo_blog_audit_agent.cli import build_run_metrics
from hugo_blog_audit_agent.models import BlogConfig
from hugo_blog_audit_agent.reports import write_reports
from hugo_blog_audit_agent.scanner import scan_markdown
from tests.helpers import make_repo

def test_translation_grouping_and_scoring(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    posts = scan_markdown(repo)
    groups = group_translations(posts, ["en", "fr", "de"])
    assert len(groups) == 1
    assert "de" in groups[0].missing_languages
    post = posts[0]
    post.scores = score_post(post)
    assert 0 <= post.scores["priority"] <= 100

def test_run_audit_index_only_does_not_report_missing_translation_gaps(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = run_audit(BlogConfig("Test", str(repo), content_dir="content", expected_languages=["en", "fr", "de"]), None, "report", None, False, False, tmp_path / "work")
    assert len(result.posts) == 1
    assert not any(group.missing_languages for group in result.groups)


def test_fixture_based_mini_hugo_repo_runs_end_to_end(sample_hugo_repo: Path, tmp_path: Path) -> None:
    config = BlogConfig("Fixture Blog", str(sample_hugo_repo), content_dir="content", expected_languages=["en", "fr", "de"])
    result = run_audit(config, None, "report", None, True, False, tmp_path / "work")
    out = tmp_path / "audit-output"

    write_reports(result, out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False, detailed_outputs=True)
    metrics = build_run_metrics(result, out, "report", None, None, None, True, 0, detailed_outputs=True, run_id="fixture-e2e")

    assert len(result.posts) == 2
    assert len(result.groups) == 1
    assert result.groups[0].missing_languages == ["de"]
    assert (out / "audit-action-items.md").exists()
    assert (out / "complete-seo-audit.md").exists()
    assert metrics["run_id"] == "fixture-e2e"
    assert metrics["markdown_files_scanned"] == 2
    assert metrics["translation_groups_with_missing_languages"] == 1
