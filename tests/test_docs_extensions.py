from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_EXT = ROOT / "docs" / "_ext"
sys.path.insert(0, str(DOCS_EXT))

from iamai_blog import BlogEntry, load_blog_entries  # noqa: E402
from iamai_mermaid import MermaidDirective  # noqa: E402


def test_blog_entries_are_validated_and_sorted_by_publish_date(tmp_path: Path) -> None:
    posts = tmp_path / "posts"
    posts.mkdir()
    (posts / "regular.rst").write_text(
        """---
id: regular
title: Regular
summary: Regular article.
author: iamai
published_at: 2026-04-26
tags: [runtime]
---

Regular
=======
""",
        encoding="utf-8",
    )
    (posts / "featured.rst").write_text(
        """---
id: featured
title: Featured
summary: Featured article.
author: iamai
published_at: 2026-04-25
tags:
  - community
featured: true
---

Featured
========
""",
        encoding="utf-8",
    )

    loaded = load_blog_entries(tmp_path, ["posts"])

    assert [entry.id for entry in loaded] == ["regular", "featured"]
    assert isinstance(loaded[0], BlogEntry)
    assert loaded[0].doc == "posts/regular.html"


def test_mermaid_directive_renders_mermaid_pre_block() -> None:
    directive = MermaidDirective.__new__(MermaidDirective)
    directive.content = ["flowchart LR", "  A --> B"]
    directive.options = {"caption": "Workflow"}
    directive.arguments = []

    nodes = directive.run()
    html = nodes[0].astext()

    assert '<pre class="mermaid">' in html
    assert "flowchart LR" in html
    assert "<figcaption>Workflow</figcaption>" in html
