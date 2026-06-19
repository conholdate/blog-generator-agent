from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.auditor import merge_product_sdk_validation, product_config_for_filter
from hugo_blog_audit_agent.cli import blog_audit_dir, build_parser, build_report_run_context, product_display_name
from hugo_blog_audit_agent.config import load_blog_config
from hugo_blog_audit_agent.models import BlogConfig

def test_config_loading(tmp_path: Path) -> None:
    config = tmp_path / "blog.yaml"
    config.write_text("blog_name: Demo\nrepo_url: repo\ncontent_dir: content\nexpected_languages:\n  - en\n", encoding="utf-8")
    loaded = load_blog_config(config)
    assert loaded.blog_name == "Demo"
    assert loaded.expected_languages == ["en"]

def test_config_loading_explicit_local_repo_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = tmp_path / "blog.yaml"
    config.write_text("blog_name: Demo\nrepo_path: repo\ncontent_dir: content\n", encoding="utf-8")
    loaded = load_blog_config(config)
    assert loaded.repo_path == str(repo.resolve())
    assert loaded.repository_source == str(repo.resolve())

def test_config_loading_shared_aspose_schema(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    formats = tmp_path / "file_formats.json"
    formats.write_text('{"docx": {"upper": "DOCX", "aliases": ["word document"]}}', encoding="utf-8")
    config = tmp_path / "aspose.yaml"
    config.write_text(
        f"""key: aspose
display_name: Aspose
outputs_root: ../outputs
repositories:
  - repo_key: blog
    repo_type: blog
    repo_path: {repo.as_posix()}
    root_subdir: content/Aspose.Blog
audit:
  content_dir: content
  output_dir: outputs
  developer_audience: true
  file_formats_path: file_formats.json
  policy_files: []
""",
        encoding="utf-8",
    )
    loaded = load_blog_config(config)
    assert loaded.blog_name == "Aspose"
    assert loaded.website == ""
    assert loaded.repo_path == str(repo.resolve())
    assert loaded.content_dir == "content"
    assert loaded.output_dir == "outputs"
    assert "word document" in loaded.file_format_aliases

def test_config_loading_metrics_metadata(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = tmp_path / "blog.yaml"
    config.write_text(
        f"""blog_name: Demo
repo_path: {repo.as_posix()}
website: https://example.com/blog
""",
        encoding="utf-8",
    )
    loaded = load_blog_config(config)
    assert loaded.website == "https://example.com/blog"

def test_config_loading_product_config_dir(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    products = tmp_path / "aspose"
    products.mkdir()
    (products / "barcode.yaml").write_text(
        """key: barcode
display_name: Aspose.BarCode
api_repo: https://example.test/barcode-api.git
api_branch: main
platforms:
  - python_net:
      api_path: english/python-net
      enabled: true
formats: [QR, PNG]
actions: [generate, read]
""",
        encoding="utf-8",
    )
    config = tmp_path / "aspose.yaml"
    config.write_text(
        f"""key: aspose
repositories:
  - repo_key: blog
    repo_type: blog
    repo_path: {repo.as_posix()}
audit:
  product_config_dir: aspose
""",
        encoding="utf-8",
    )
    loaded = load_blog_config(config)
    product_config = product_config_for_filter(loaded, "Aspose.blog/barcode")
    assert product_config
    assert product_config["display_name"] == "Aspose.BarCode"
    sdk = merge_product_sdk_validation({}, product_config)
    assert sdk["api_reference_repositories"][0]["root_subdir"] == "english/python-net"

def test_config_loading_audience_fields(tmp_path: Path) -> None:
    config = tmp_path / "blog.yaml"
    config.write_text("blog_name: Demo\nrepo_url: repo\ndeveloper_audience: true\naudience_profile: Developers using APIs\n", encoding="utf-8")
    loaded = load_blog_config(config)
    assert loaded.developer_audience is True
    assert loaded.audience_profile == "Developers using APIs"

def test_config_loading_known_product_mentions(tmp_path: Path) -> None:
    config = tmp_path / "blog.yaml"
    config.write_text("blog_name: Demo\nrepo_url: repo\nknown_product_mentions:\n  - Aspose.Words\n  - Aspose.Imaging\n", encoding="utf-8")
    loaded = load_blog_config(config)
    assert loaded.known_product_mentions == ["Aspose.Words", "Aspose.Imaging"]

def test_config_loading_sdk_validation(tmp_path: Path) -> None:
    config = tmp_path / "blog.yaml"
    config.write_text(
        """blog_name: Demo
repo_url: repo
sdk_validation:
  enabled: true
  packages:
    - id: aspose-barcode
      namespaces: [aspose.barcode]
      known_symbols: [BarcodeGenerator]
""",
        encoding="utf-8",
    )
    loaded = load_blog_config(config)
    assert loaded.sdk_validation["enabled"] is True
    assert loaded.sdk_validation["packages"][0]["known_symbols"] == ["BarcodeGenerator"]

def test_config_loading_llm_settings(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = tmp_path / "blog.yaml"
    config.write_text(
        f"""blog_name: Demo
repo_path: {repo.as_posix()}
llm:
  enabled: true
  provider: mock
  model: mock-model
  max_posts: 3
  cache_dir: llm-cache
""",
        encoding="utf-8",
    )
    loaded = load_blog_config(config)
    assert loaded.llm["enabled"] is True
    assert loaded.llm["provider"] == "mock"
    assert loaded.llm["model"] == "mock-model"
    assert loaded.llm["max_posts"] == 3
    assert loaded.llm["cache_dir"] == str((tmp_path / "llm-cache").resolve())

def test_config_loading_policy_files(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("id: test\nrules: []\n", encoding="utf-8")
    config = tmp_path / "blog.yaml"
    config.write_text("blog_name: Demo\nrepo_url: repo\npolicy_files:\n  - policy.yaml\n", encoding="utf-8")
    loaded = load_blog_config(config)
    assert loaded.policy_files == [str(policy.resolve())]

def test_default_blog_audit_dir_uses_outputs_audit_slug() -> None:
    assert blog_audit_dir("outputs", "Aspose").as_posix() == "outputs/audit/aspose"

def test_send_metrics_flag_defaults_to_disabled() -> None:
    parser = build_parser()

    default_args = parser.parse_args(["--blog-config", "configs/aspose.yaml"])
    enabled_args = parser.parse_args(["--blog-config", "configs/aspose.yaml", "--send-metrics"])
    disabled_args = parser.parse_args(["--blog-config", "configs/aspose.yaml", "--send-metrics", "false"])

    assert default_args.send_metrics is False
    assert enabled_args.send_metrics is True
    assert disabled_args.send_metrics is False

def test_report_run_context_captures_cli_inputs(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([
        "--blog-config",
        "configs/aspose.yaml",
        "--product",
        "Aspose.blog/barcode",
        "--post-date",
        "2026-06-05",
        "--include-translations",
        "false",
        "--detailed-outputs",
        "true",
        "--llm-suggestions",
        "true",
        "--llm-model",
        "test-model",
        "--send-metrics",
        "true",
    ])
    config = BlogConfig("Aspose", "repo", product_configs={"barcode": {"display_name": "Aspose.BarCode"}})
    config.llm["enabled"] = True
    config.llm["model"] = "test-model"

    context = build_report_run_context(args, config, tmp_path / "out", ["en"], draft_fixes=False)

    assert context["product_name"] == "Aspose.BarCode"
    assert context["product_filter"] == "Aspose.blog/barcode"
    assert context["post_date_filter"] == "2026-06-05"
    assert context["language_filter"] == ["en"]
    assert context["include_translations"] is False
    assert context["detailed_outputs"] is True
    assert context["llm_suggestions"] is True
    assert context["llm_model"] == "test-model"
    assert context["send_metrics"] is True

def test_product_display_name_uses_product_config() -> None:
    config = BlogConfig(
        "Aspose",
        "repo",
        product_configs={"drawing": {"display_name": "Aspose.Drawing"}},
    )
    assert product_display_name(config, "Aspose.blog/drawing") == "Aspose.Drawing"
    assert product_display_name(config, None) == "Aspose"
