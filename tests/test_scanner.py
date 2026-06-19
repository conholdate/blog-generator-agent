from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.auditor import audit_content
from hugo_blog_audit_agent.hugo import detect_hugo_project
from hugo_blog_audit_agent.scanner import extract_front_matter_images, extract_headings, extract_images, extract_links, scan_markdown, split_front_matter
from tests.helpers import make_repo

def test_front_matter_parsing_yaml() -> None:
    fmt, data, _raw, body = split_front_matter("---\ntitle: Test\n---\n# Body")
    assert fmt == "yaml"
    assert data["title"] == "Test"
    assert "# Body" in body

def test_markdown_extractors() -> None:
    body = "# H1\n\n## H2\n[Docs](/docs/) ![Alt](img.png)\n{{< figure align=center src=\"images/output.png\" alt=\"Output image\" >}}\n{{< shortcode >}}"
    assert [h.level for h in extract_headings(body)] == [1, 2]
    assert extract_links(body)[0].target == "/docs/"
    images = extract_images(body)
    assert images[0].alt == "Alt"
    assert images[1].target == "images/output.png"
    assert images[1].alt == "Output image"
    assert extract_front_matter_images({"cover": "cover.png"}, "Cover Alt")[0].target == "cover.png"

def test_scanner_detects_metadata_and_shortcodes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    posts = scan_markdown(repo)
    assert len(posts) == 2
    en = next(p for p in posts if p.language == "en")
    assert en.title == "Create Word Documents in Python"
    assert en.code_blocks == 1
    assert en.code_samples[0].language == "python"
    assert "print" in en.code_samples[0].code
    assert en.shortcodes
    assert en.images[0].target == "images/missing.png"

def test_product_filter_accepts_forward_slashes_on_windows_paths(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    posts = scan_markdown(repo, product="Aspose.blog/words")
    assert len(posts) == 2

def test_post_date_filter_matches_front_matter_and_path(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    other_dir = repo / "content" / "Aspose.blog" / "words" / "2026-06-05-new-post"
    other_dir.mkdir(parents=True)
    (other_dir / "index.md").write_text(
        """---
title: "Convert DOCX Files in Python"
description: "Learn to convert DOCX files in Python."
date: 2026-06-04T10:00:00
---

Intro paragraph.
""",
        encoding="utf-8",
    )
    posts = scan_markdown(repo, product="Aspose.blog/words", post_date="2026-06-05", include_translations=False)
    assert len(posts) == 1
    assert "2026-06-05-new-post" in posts[0].relative_path

def test_front_matter_cover_counts_as_post_image(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    cover_dir = repo / "content" / "Aspose.blog" / "words" / "cover-only-post"
    cover_dir.mkdir(parents=True)
    (cover_dir / "index.md").write_text(
        """---
title: "Generate Word Document Preview in Python"
description: "Learn to generate Word document previews in Python."
cover: "cover.png"
---

Intro paragraph that explains the reader promise and outcome in enough detail to be useful for tests.

## Step One

Use the API to generate the preview.
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="cover-only-post", include_translations=False))
    issues = audit_content(post)
    issue_types = {issue.issue_type for issue in issues}
    assert post.images[0].target == "cover.png"
    assert "missing_post_image" not in issue_types
    assert "suggest_body_output_image" in issue_types

def test_body_figure_shortcode_counts_as_inline_output_image(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "body-figure-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Code 39 Barcode in Python"
description: "Learn to generate Code 39 barcodes in Python."
cover: "cover.png"
---

Intro paragraph that explains the reader promise and outcome in enough detail to be useful for tests.

## Generate the Barcode

```python
print("generate barcode")
```

{{< figure align=center src="images/code39_barcode.png" alt="Code 39 Barcode" >}}
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="body-figure-post", include_translations=False))
    issues = audit_content(post)
    issue_types = {issue.issue_type for issue in issues}
    assert any(image.target == "images/code39_barcode.png" and image.line > 0 for image in post.images)
    assert "missing_post_image" not in issue_types
    assert "suggest_body_output_image" not in issue_types

def test_scan_markdown_can_skip_translations_for_index_only(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    posts = scan_markdown(repo, include_translations=False)
    assert len(posts) == 1
    assert posts[0].path.name == "index.md"
    assert posts[0].language == "en"

def test_hugo_config_detection(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    detection = detect_hugo_project(repo)
    assert "hugo.yaml" in detection.config_files
    assert detection.directories["content"] is True
