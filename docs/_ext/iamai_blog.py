"""Sphinx extension for rendering community blog pages from frontmatter."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sphinx.application import Sphinx


class BlogEntry(BaseModel):
    """Validated metadata for one community blog item."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=260)
    author: str = Field(min_length=1)
    published_at: date
    category: str = "社区文章"
    tags: list[str] = Field(default_factory=list)
    url: str | None = None
    doc: str | None = None
    featured: bool = False

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be absolute http(s)")
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if not isinstance(value, list):
            raise TypeError("tags must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


class iamaiBlogDirective(Directive):
    """Render the full blog landing page or a compact card list."""

    has_content = False
    option_spec = {
        "title": directives.unchanged,
        "layout": directives.unchanged,
        "limit": directives.nonnegative_int,
    }

    def run(self) -> list[nodes.Node]:
        env = self.state.document.settings.env
        app = env.app
        entries = load_blog_entries(app.srcdir, list(app.config.iamai_blog_registry_paths))
        limit = self.options.get("limit")
        if limit is not None:
            entries = entries[: int(limit)]
        title = self.options.get("title", "iamai Blog")
        layout = str(self.options.get("layout", "index")).strip().lower()
        if layout == "cards":
            html = _render_cards_section(entries, title=title, app=app, current_doc=env.docname)
        else:
            html = _render_blog_index(entries, title=title, app=app, current_doc=env.docname)
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict[str, Any]:
    """Register blog directives and assets."""

    app.add_config_value(
        "iamai_blog_registry_paths",
        ["community/blog/posts"],
        "env",
        types=frozenset({list, tuple}),
    )
    app.add_directive("iamai-blog", iamaiBlogDirective)
    app.add_css_file("iamai-blog.css")
    app.connect("source-read", _strip_frontmatter_on_source_read)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def load_blog_entries(
    source_dir: str | Path, registry_paths: list[str] | tuple[str, ...]
) -> list[BlogEntry]:
    """Load community blog entries from RST or Markdown files with YAML frontmatter."""

    root = Path(source_dir).resolve()
    entries: list[BlogEntry] = []
    for raw_path in registry_paths:
        path = (root / raw_path).resolve()
        files: list[Path]
        if path.is_dir():
            files = sorted([*path.glob("*.rst"), *path.glob("*.md")])
        elif path.is_file():
            files = [path]
        else:
            continue
        for file_path in files:
            try:
                frontmatter, _ = parse_frontmatter(file_path.read_text(encoding="utf-8"))
                if not frontmatter:
                    raise ValueError("missing YAML frontmatter")
                payload = dict(frontmatter)
                payload.setdefault("id", file_path.stem.replace("_", "-"))
                payload.setdefault("doc", _doc_href(root, file_path))
                entries.append(BlogEntry.model_validate(payload))
            except (OSError, ValidationError, ValueError) as exc:
                raise ValueError(f"invalid iamai blog entry {file_path}: {exc}") from exc
    return sorted(entries, key=lambda entry: entry.published_at, reverse=True)


def parse_frontmatter(source: str) -> tuple[dict[str, Any], str]:
    """Parse a small YAML-frontmatter subset from one article source."""

    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, source
    try:
        end_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("unterminated frontmatter") from exc
    payload = _parse_yaml_subset(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return payload, body


def _parse_yaml_subset(lines: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not raw_value:
            items: list[str] = []
            while index < len(lines) and lines[index].lstrip().startswith("- "):
                items.append(_unquote(lines[index].split("- ", 1)[1].strip()))
                index += 1
            payload[key] = items
            continue
        if raw_value.startswith("[") and raw_value.endswith("]"):
            inner = raw_value[1:-1].strip()
            payload[key] = [_unquote(item.strip()) for item in inner.split(",") if item.strip()]
        elif raw_value.lower() in {"true", "false"}:
            payload[key] = raw_value.lower() == "true"
        else:
            payload[key] = _unquote(raw_value)
    return payload


def _strip_frontmatter_on_source_read(app: Sphinx, docname: str, source: list[str]) -> None:
    registry_paths = [str(path).rstrip("/") for path in app.config.iamai_blog_registry_paths]
    if not any(docname.startswith(path) for path in registry_paths):
        return
    frontmatter, body = parse_frontmatter(source[0])
    entry = BlogEntry.model_validate({**frontmatter, "doc": f"{docname}.html"})
    source[0] = _inject_article_header(body, entry)


def _render_blog_index(
    entries: list[BlogEntry], *, title: str, app: Sphinx, current_doc: str
) -> str:
    if not entries:
        return _render_cards_section(entries, title=title, app=app, current_doc=current_doc)
    latest = entries[0]
    featured_entries = [entry for entry in entries if entry.featured] or entries[:3]
    html = [
        '<section class="iamai-blog iamai-blog--index">',
        '<div class="iamai-blog-hero">',
        "<div>",
        '<span class="iamai-blog-hero__eyebrow">最新消息</span>',
        f"<h2>{_escape_html(latest.title)}</h2>",
        f"<p>{_escape_html(latest.summary)}</p>",
        '<div class="iamai-blog-card__meta">',
        f"<span>{_escape_html(latest.category)}</span>",
        f"<time>{latest.published_at.isoformat()}</time>",
        f"<span>{_escape_html(latest.author)}</span>",
        "</div>",
        "</div>",
        f'<a class="iamai-blog-hero__link" href="{_escape_attr(_href(latest, app, current_doc))}">阅读最新文章</a>',
        "</div>",
        '<div class="iamai-blog-index-layout">',
        '<section class="iamai-blog-intro">',
        "<h2>关于 iamai Blog</h2>",
        "<p>iamai Blog 用来沉淀运行时设计、插件与适配器开发经验、社区扩展发布记录、真实接入案例和路线图说明。这里的文章会尽量把背景、约束、权衡和可复用做法写清楚，而不只是发布短消息。</p>",
        "<h3>我们欢迎这些内容</h3>",
        "<ul>",
        "<li>插件、适配器、Agent Tool 或部署实践的复盘。</li>",
        "<li>围绕安全、权限、状态、审计、测试和运维的工程笔记。</li>",
        "<li>社区商店条目背后的设计说明、案例教程和版本迁移记录。</li>",
        "</ul>",
        "<h3>如何提交博客</h3>",
        "<p>在 <code>docs/community/blog/posts/</code> 新增一篇 <code>.rst</code> 或 <code>.md</code> 文章，并在文件顶部填写 YAML frontmatter：<code>id</code>、<code>title</code>、<code>summary</code>、<code>author</code>、<code>published_at</code>、<code>category</code>、<code>tags</code>。精选文章可以额外设置 <code>featured: true</code>。</p>",
        "<p>正文建议包含问题背景、适用版本、关键配置、风险提示和后续链接。提交 PR 后，维护者会检查元数据、链接、安全声明和文档构建结果。</p>",
        "</section>",
        '<aside class="iamai-blog-archive" aria-label="全部文章">',
        f"<h2>{_escape_html(title)}</h2>",
        "<p>按年度时间线浏览全部文章。</p>",
        _render_year_archive(entries, app, current_doc),
        "</aside>",
        "</div>",
        _render_cards_section(
            featured_entries,
            title="社区精选",
            app=app,
            current_doc=current_doc,
            carousel=True,
        ),
        "</section>",
    ]
    return "\n".join(html)


def _render_cards_section(
    entries: list[BlogEntry],
    *,
    title: str,
    app: Sphinx,
    current_doc: str,
    carousel: bool = False,
) -> str:
    grid_class = "iamai-blog__rail" if carousel else "iamai-blog__grid"
    html = [
        '<section class="iamai-blog">',
        '<div class="iamai-blog__header">',
        f"<h2>{_escape_html(title)}</h2>",
        "<p>来自维护者和社区的设计笔记、发布记录、接入经验与案例复盘。</p>",
        "</div>",
    ]
    if not entries:
        html.append('<p class="iamai-blog__empty">暂无文章。</p>')
    else:
        html.append(f'<div class="{grid_class}">')
        for entry in entries:
            html.append(_render_card(entry, app, current_doc))
        html.append("</div>")
    html.append("</section>")
    return "\n".join(html)


def _render_card(entry: BlogEntry, app: Sphinx, current_doc: str) -> str:
    tags = "".join(f"<span>#{_escape_html(tag)}</span>" for tag in entry.tags)
    featured = '<span class="iamai-blog-card__featured">精选</span>' if entry.featured else ""
    return (
        '<article class="iamai-blog-card">'
        '<div class="iamai-blog-card__meta">'
        f"<span>{_escape_html(entry.category)}</span>"
        f"<time>{entry.published_at.isoformat()}</time>"
        f"{featured}"
        "</div>"
        f'<h3><a href="{_escape_attr(_href(entry, app, current_doc))}">{_escape_html(entry.title)}</a></h3>'
        f"<p>{_escape_html(entry.summary)}</p>"
        f'<div class="iamai-blog-card__footer"><span>{_escape_html(entry.author)}</span>'
        f"<div>{tags}</div></div>"
        "</article>"
    )


def _render_list_item(entry: BlogEntry, app: Sphinx, current_doc: str) -> str:
    tags = " ".join(f"<span>#{_escape_html(tag)}</span>" for tag in entry.tags)
    return (
        '<article class="iamai-blog-list__item">'
        f"<time>{entry.published_at.isoformat()}</time>"
        "<div>"
        f'<h3><a href="{_escape_attr(_href(entry, app, current_doc))}">{_escape_html(entry.title)}</a></h3>'
        f"<p>{_escape_html(entry.summary)}</p>"
        f'<div class="iamai-blog-list__meta"><span>{_escape_html(entry.category)}</span>'
        f"<span>{_escape_html(entry.author)}</span>{tags}</div>"
        "</div>"
        "</article>"
    )


def _render_year_archive(entries: list[BlogEntry], app: Sphinx, current_doc: str) -> str:
    html: list[str] = ['<div class="iamai-blog-archive__years">']
    current_year: int | None = None
    for entry in entries:
        year = entry.published_at.year
        if year != current_year:
            if current_year is not None:
                html.append("</div>")
            current_year = year
            html.append('<div class="iamai-blog-archive__year">')
            html.append(f"<h3>{year}</h3>")
        html.append(
            '<a class="iamai-blog-archive__item" '
            f'href="{_escape_attr(_href(entry, app, current_doc))}">'
            f"<time>{entry.published_at.strftime('%m-%d')}</time>"
            "<span>"
            f"{_escape_html(entry.title)}"
            "</span>"
            "</a>"
        )
    if current_year is not None:
        html.append("</div>")
    html.append("</div>")
    return "\n".join(html)


def _inject_article_header(body: str, entry: BlogEntry) -> str:
    lines = body.splitlines()
    prefix: list[str] = []
    while lines and lines[0].startswith(":"):
        prefix.append(lines.pop(0))
        if lines and not lines[0].strip():
            prefix.append(lines.pop(0))
    insert_at = 0
    if (
        len(lines) >= 2
        and lines[0].strip()
        and set(lines[1].strip()) in ({"="}, {"-"}, {"~"}, {"^"})
    ):
        insert_at = 2
    article_header = [
        "",
        ".. raw:: html",
        "",
        f"   {_render_article_meta(entry)}",
        "",
    ]
    return "\n".join([*prefix, *lines[:insert_at], *article_header, *lines[insert_at:]]).lstrip(
        "\n"
    )


def _render_article_meta(entry: BlogEntry) -> str:
    tags = "".join(
        f'<span class="iamai-blog-article__tag">#{_escape_attr(tag)}</span>' for tag in entry.tags
    )
    featured = '<span class="iamai-blog-article__featured">精选</span>' if entry.featured else ""
    return (
        '<div class="iamai-blog-article__meta">'
        f"<span>作者：{_escape_html(entry.author)}</span>"
        f"<span>分类：{_escape_html(entry.category)}</span>"
        f'<time datetime="{entry.published_at.isoformat()}">时间：{entry.published_at.isoformat()}</time>'
        f"{featured}"
        f'<span class="iamai-blog-article__tags">{tags}</span>'
        "</div>"
    )


def _doc_href(root: Path, file_path: Path) -> str:
    return file_path.relative_to(root).with_suffix(".html").as_posix()


def _href(entry: BlogEntry, app: Sphinx, current_doc: str) -> str:
    if entry.url:
        return entry.url
    if not entry.doc:
        return "#"
    target_doc = entry.doc.removesuffix(".html")
    return app.builder.get_relative_uri(current_doc, target_doc)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _escape_attr(value: str) -> str:
    return _escape_html(value).replace("'", "&#x27;")
