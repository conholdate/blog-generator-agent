from __future__ import annotations

from pathlib import Path

def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    post_dir = repo / "content" / "Aspose.blog" / "words" / "sample-post"
    post_dir.mkdir(parents=True)
    (repo / "hugo.yaml").write_text("languages:\n  en:\n  fr:\n", encoding="utf-8")
    (repo / "layouts").mkdir()
    (repo / "layouts" / "baseof.html").write_text("<link rel=\"canonical\" href=\"x\"><meta property=\"og:title\"><script type=\"application/ld+json\"></script>", encoding="utf-8")
    (post_dir / "index.md").write_text(
        """---
title: "Create Word Documents in Python"
description: "Learn to create Word documents in Python with examples."
date: 2026-01-01
draft: false
url: /words/create-word-documents-in-python/
tags: ["python"]
categories: ["Aspose.Words"]
---

Intro paragraph that explains the reader promise and outcome in enough detail to be useful for tests.

## Step One

![Diagram](images/missing.png)

[Related](/words/related/)

{{< gist user id >}}

```python
print("hello")
```

## FAQ
""",
        encoding="utf-8",
    )
    (post_dir / "index.fr.md").write_text(
        """---
title: "Create Word Documents in Python"
description: "Learn to create Word documents in Python with examples."
url: /fr/words/create-word-documents-in-python/
---

Bonjour.
""",
        encoding="utf-8",
    )
    return repo
