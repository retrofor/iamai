"""Sphinx extension for Mermaid diagrams."""

from __future__ import annotations

from hashlib import sha1
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.application import Sphinx


class MermaidDirective(Directive):
    """Render a Mermaid diagram block."""

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "caption": directives.unchanged,
        "class": directives.class_option,
    }

    def run(self) -> list[nodes.Node]:
        source = "\n".join(self.content).strip()
        if not source:
            message = self.state_machine.reporter.warning(
                "mermaid directive requires diagram content",
                line=self.lineno,
            )
            return [message]
        caption = self.options.get("caption") or (self.arguments[0] if self.arguments else "")
        classes = ["iamai-mermaid", *self.options.get("class", [])]
        diagram_id = "iamai-mermaid-" + sha1(source.encode("utf-8")).hexdigest()[:12]
        html = (
            f'<figure class="{" ".join(_escape_attr(item) for item in classes)}" '
            f'id="{diagram_id}">'
            f'<pre class="mermaid">{_escape_html(source)}</pre>'
        )
        if caption:
            html += f"<figcaption>{_escape_html(caption)}</figcaption>"
        html += "</figure>"
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict[str, Any]:
    """Register Mermaid directives and assets."""

    app.add_directive("mermaid", MermaidDirective)
    app.add_directive("iamai-mermaid", MermaidDirective)
    app.add_js_file("iamai-mermaid.js", defer="defer")
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _escape_attr(value: str) -> str:
    return _escape_html(value).replace("'", "&#x27;")
