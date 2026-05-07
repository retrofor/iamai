from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ecosystem_comparison_contains_matrix_and_roadmap_link() -> None:
    content = _read("docs/guides/ecosystem-comparison.rst")

    assert "能力矩阵" in content
    assert "NoneBot" in content
    assert "Hermes Agent" in content
    assert "iamai-table-scroll" in content
    assert "差距到实现" in content
    assert ":doc:`roadmap`" in content


def test_extensions_reference_contains_public_extension_specs() -> None:
    content = _read("docs/reference/extensions.rst")

    assert "适配器兼容性规范草案" in content
    assert '[project.entry-points."iamai.adapters"]' in content
    assert "Agent tool 必须额外声明" in content
    assert "/schema" in content
    assert "iamai.testing.adapters" in content


def test_roadmap_contains_versioned_design_decisions() -> None:
    content = _read("docs/guides/roadmap.rst")

    assert "``0.1``" in content
    assert "``0.2``" in content
    assert "``0.3``" in content
    assert "``1.0``" in content
    assert "WebUI 不进入核心" in content


def test_community_page_contains_blog_and_store_sections() -> None:
    content = _read("docs/community/index.rst")

    assert "BLOG" in content
    assert ".. iamai-blog::" in content
    assert "社区商店" in content
    assert "blog/index" in content
    assert "store" in content


def test_blog_and_store_pages_are_split_under_community() -> None:
    blog = _read("docs/community/blog/index.rst")
    store = _read("docs/community/store.rst")

    assert ".. iamai-blog::" in blog
    assert ".. iamai-store::" in store
    assert ".. iamai-store-submit::" not in store
