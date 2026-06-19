from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.auditor import run_audit
from hugo_blog_audit_agent.llm import api_key_for_config, chat_completions_url, env_first, llm_model_from_env, llm_retries, llm_timeout_seconds, load_dotenv
from hugo_blog_audit_agent.models import BlogConfig
from hugo_blog_audit_agent.reports import write_reports
from tests.helpers import make_repo

def test_llm_professionalize_env_defaults(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        """PROFESSIONALIZE_BASE_URL=https://professionalize.test/v1
PROFESSIONALIZE_API_KEY=professionalize-key
PROFESSIONALIZE_LLM_MODEL=professionalize-chat
PROFESSIONALIZE_EMBEDDING_MODEL=professionalize-embed
PROFESSIONALIZE_TIMEOUT_SECONDS=180
PROFESSIONALIZE_LLM_RETRIES=2
OPENAI_API_KEY=openai-key
""",
        encoding="utf-8",
    )
    for key in [
        "PROFESSIONALIZE_BASE_URL",
        "PROFESSIONALIZE_API_KEY",
        "PROFESSIONALIZE_LLM_MODEL",
        "PROFESSIONALIZE_EMBEDDING_MODEL",
        "PROFESSIONALIZE_TIMEOUT_SECONDS",
        "PROFESSIONALIZE_LLM_RETRIES",
        "OPENAI_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    load_dotenv(env_file)

    assert env_first("PROFESSIONALIZE_EMBEDDING_MODEL") == "professionalize-embed"
    assert llm_model_from_env() == "professionalize-chat"
    assert api_key_for_config({}) == "professionalize-key"
    assert chat_completions_url(env_first("PROFESSIONALIZE_BASE_URL")) == "https://professionalize.test/v1/chat/completions"
    assert llm_timeout_seconds({}) == 180
    assert llm_retries({}) == 2

def test_llm_mock_suggestions_are_cached_and_rendered(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    llm_config = {
        "enabled": True,
        "provider": "mock",
        "model": "mock-model",
        "max_posts": 1,
        "cache_dir": str(tmp_path / "llm-cache"),
    }
    config = BlogConfig("Test", str(repo), content_dir="content", expected_languages=["en", "fr"], llm=llm_config)
    result = run_audit(config, None, "report", None, True, False, tmp_path / "work")
    assert result.llm_metrics["enabled"] is True
    assert result.llm_metrics["attempted_posts"] == 1
    assert result.llm_metrics["generated_suggestions"] == 1
    assert result.llm_metrics["cache_misses"] == 1
    assert result.llm_metrics["errors"] == 0
    assert sum(len(post.llm_suggestions) for post in result.posts) == 1

    cached_result = run_audit(config, None, "report", None, True, False, tmp_path / "work")
    assert cached_result.llm_metrics["cache_hits"] == 1

    out = tmp_path / "output"
    write_reports(result, out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False)
    action_items = (out / "audit-action-items.md").read_text(encoding="utf-8")
    assert "## LLM Suggestions" in action_items
    assert "mock-model" in action_items
    assert "Verify all generated suggestions before publishing." in action_items
