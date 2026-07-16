"""Sphinx extension for rendering the iamai ecosystem store."""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
import re
from typing import Any, Literal
from urllib.parse import urlencode, urlsplit

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sphinx.application import Sphinx

ExtensionType = Literal[
    "plugin",
    "adapter",
    "ruleset",
    "permission",
    "state_backend",
    "agent_tool",
    "agent_skill",
    "middleware",
    "template",
    "example",
    "provider",
    "theme",
]
ExtensionStatus = Literal["active", "experimental", "deprecated"]
VerificationBadge = Literal[
    "community",
    "package_verified",
    "author_verified",
    "official",
    "security_reviewed",
    "deprecated",
]

STORE_VERSION = 1
STORE_INDEX_FILENAME = "iamai-store-index.json"
STORE_INDEX_JS_FILENAME = "iamai-store-index.js"
STORE_JS_FILENAME = "iamai-store.js"
STORE_CSS_FILENAME = "iamai-store.css"
DEFAULT_GITHUB_ISSUE_TEMPLATE = "ecosystem-submission.yml"
STORE_TYPES: tuple[str, ...] = (
    "plugin",
    "adapter",
    "ruleset",
    "permission",
    "state_backend",
    "agent_tool",
    "agent_skill",
    "middleware",
    "template",
    "example",
    "provider",
    "theme",
)
USER_SUBMITTABLE_BADGES = {"community", "deprecated"}


class StoreEntryPoint(BaseModel):
    """Python entry point advertised by one ecosystem package."""

    model_config = ConfigDict(extra="forbid")

    group: Literal["iamai.plugins", "iamai.adapters"]
    name: str = Field(min_length=1)
    value: str = Field(min_length=1)


class StoreEntry(BaseModel):
    """Validated registry entry for one ecosystem item."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    name: str = Field(min_length=1)
    type: ExtensionType
    summary: str = Field(min_length=1, max_length=180)
    package: str | None = None
    repository: str | None = None
    license: str = Field(min_length=1)
    status: ExtensionStatus = "active"
    verification: list[VerificationBadge] = Field(default_factory=lambda: ["community"])
    entry_points: list[StoreEntryPoint] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    iamai_requires: str | None = None
    conformance_evidence: list[str] = Field(default_factory=list)
    runtime_capabilities: list[str] = Field(default_factory=list)
    install_command: str | None = None
    docs_url: str | None = None
    source_url: str | None = None
    homepage_url: str | None = None
    config_example: str | None = None
    security_notes: str | None = None
    permission_notes: str | None = None
    updated_at: str | None = None

    @field_validator(
        "docs_url",
        "source_url",
        "homepage_url",
        "repository",
    )
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must be absolute http(s)")
        return value

    @field_validator(
        "tags",
        "platforms",
        "requires",
        "conformance_evidence",
        "runtime_capabilities",
        "verification",
        mode="before",
    )
    @classmethod
    def _normalize_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("value must be a list")
        return [str(item).strip() for item in value if str(item).strip()]

    @field_validator("iamai_requires")
    @classmethod
    def _normalize_iamai_requires(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("iamai_requires must not be blank")
        return normalized

    @field_validator("conformance_evidence")
    @classmethod
    def _validate_conformance_evidence(cls, value: list[str]) -> list[str]:
        for evidence_url in value:
            cls._validate_public_url(evidence_url)
        return value

    @classmethod
    def _validate_public_url(cls, value: str) -> None:
        if any(character.isspace() for character in value):
            raise ValueError("evidence URL must not contain whitespace")
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
            parsed.port
        except ValueError as exc:
            raise ValueError("evidence URL must be a valid public http(s) URL") from exc
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or hostname is None:
            raise ValueError("evidence URL must be a valid public http(s) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("evidence URL must not contain credentials")

        normalized_host = hostname.rstrip(".").lower()
        try:
            ipaddress.ip_address(normalized_host)
        except ValueError:
            try:
                ascii_host = normalized_host.encode("idna").decode("ascii")
            except UnicodeError as exc:
                raise ValueError("evidence URL host must be valid DNS") from exc
            labels = ascii_host.split(".")
            valid_label = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
            numeric_label = re.compile(r"^(?:[0-9]+|0x[0-9a-f]+)$")
            if (
                len(ascii_host) > 253
                or len(labels) < 2
                or any(not valid_label.fullmatch(label) for label in labels)
                or all(numeric_label.fullmatch(label) for label in labels)
                or ascii_host.endswith((".local", ".localhost", ".invalid", ".test", ".example"))
            ):
                raise ValueError("evidence URL host must be valid public DNS") from None
        else:
            raise ValueError("evidence URL host must use a public DNS name")

    @model_validator(mode="after")
    def _validate_package_or_repository(self) -> "StoreEntry":
        if not self.package and not self.repository:
            raise ValueError("package or repository is required")
        badges = set(self.verification)
        if self.status == "deprecated" and "deprecated" not in badges:
            self.verification.append("deprecated")
        return self

    def to_index_item(self) -> dict[str, Any]:
        """Return the JSON shape consumed by the browser UI."""

        payload = self.model_dump(mode="json")
        search_parts = [
            self.id,
            self.name,
            self.type,
            self.summary,
            self.package or "",
            self.repository or "",
            " ".join(self.tags),
            " ".join(self.platforms),
            " ".join(self.verification),
        ]
        payload["search_text"] = " ".join(search_parts).casefold()
        payload["sort_rank"] = _sort_rank(self)
        if payload.get("install_command") is None and self.package:
            payload["install_command"] = f"uv add {self.package}"
        return payload


class StoreIndex(BaseModel):
    """Build artifact for all ecosystem entries."""

    model_config = ConfigDict(extra="forbid")

    version: int = STORE_VERSION
    entries: list[StoreEntry]

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "StoreIndex":
        seen: dict[str, str] = {}
        for entry in self.entries:
            previous = seen.get(entry.id)
            if previous is not None:
                raise ValueError(f"duplicate store entry id: {entry.id}")
            seen[entry.id] = entry.name
        return self

    def to_json_payload(self) -> dict[str, Any]:
        """Return the serialized index payload."""

        return {
            "version": self.version,
            "types": list(STORE_TYPES),
            "entries": [entry.to_index_item() for entry in self.entries],
        }


class StoreSubmission(BaseModel):
    """User-submitted ecosystem entry draft."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    name: str = Field(min_length=1)
    type: ExtensionType
    summary: str = Field(min_length=1, max_length=180)
    package: str | None = None
    repository: str | None = None
    license: str = Field(min_length=1)
    status: ExtensionStatus = "active"
    entry_points: list[StoreEntryPoint] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    iamai_requires: str | None = None
    conformance_evidence: list[str] = Field(default_factory=list)
    runtime_capabilities: list[str] = Field(default_factory=list)
    docs_url: str | None = None
    source_url: str | None = None
    homepage_url: str | None = None
    config_example: str | None = None
    security_notes: str | None = None
    permission_notes: str | None = None
    verification: list[VerificationBadge] = Field(default_factory=lambda: ["community"])

    @field_validator(
        "docs_url",
        "source_url",
        "homepage_url",
        "repository",
    )
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        return StoreEntry._validate_url(value)

    @field_validator(
        "tags",
        "platforms",
        "requires",
        "conformance_evidence",
        "runtime_capabilities",
        "verification",
        mode="before",
    )
    @classmethod
    def _normalize_list(cls, value: Any) -> list[str]:
        return StoreEntry._normalize_list(value)

    @field_validator("iamai_requires")
    @classmethod
    def _normalize_iamai_requires(cls, value: str | None) -> str | None:
        return StoreEntry._normalize_iamai_requires(value)

    @field_validator("conformance_evidence")
    @classmethod
    def _validate_conformance_evidence(cls, value: list[str]) -> list[str]:
        return StoreEntry._validate_conformance_evidence(value)

    @model_validator(mode="after")
    def _validate_user_submission(self) -> "StoreSubmission":
        if not self.package and not self.repository:
            raise ValueError("package or repository is required")
        if self.type in {"plugin", "adapter", "agent_tool"} and not self.security_notes:
            raise ValueError(
                "security_notes is required for plugin, adapter, and agent_tool entries"
            )
        if self.type in {"plugin", "adapter"}:
            if self.iamai_requires is None:
                raise ValueError("iamai_requires is required for plugin and adapter entries")
            if not self.conformance_evidence:
                raise ValueError("conformance_evidence is required for plugin and adapter entries")
        if self.type == "agent_tool" and not self.permission_notes:
            raise ValueError("permission_notes is required for agent_tool entries")
        forbidden_badges = set(self.verification) - USER_SUBMITTABLE_BADGES
        if forbidden_badges:
            badges = ", ".join(sorted(forbidden_badges))
            raise ValueError(f"verification badges require maintainer review: {badges}")
        return self

    def to_store_entry(self) -> StoreEntry:
        """Return the registry entry shape maintainers can copy into the store."""

        payload = self.model_dump(mode="json", exclude_none=True)
        payload["status"] = self.status
        payload["verification"] = ["community"]
        return StoreEntry.model_validate(payload)


class iamaiStoreDirective(Directive):
    """Render a full interactive ecosystem store."""

    has_content = False
    option_spec = {
        "type": directives.unchanged,
        "title": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        type_filter = self.options.get("type", "")
        title = self.options.get("title", "社区商店")
        app = self.state.document.settings.env.app
        github_repo = str(getattr(app.config, "iamai_store_github_repo", ""))
        issue_template = str(
            getattr(app.config, "iamai_store_issue_template", DEFAULT_GITHUB_ISSUE_TEMPLATE)
        )
        submit_api_url = str(getattr(app.config, "iamai_store_submit_api_url", ""))
        html = (
            '<section class="iamai-store" '
            f'data-iamai-store data-default-type="{_escape_attr(type_filter)}" '
            f'data-github-repo="{_escape_attr(github_repo)}" '
            f'data-issue-template="{_escape_attr(issue_template)}" '
            f'data-submit-api-url="{_escape_attr(submit_api_url)}">'
            '<div class="iamai-store__header">'
            '<div class="iamai-store__header-text">'
            f"<h2>{_escape_html(title)}</h2>"
            "<p>搜索、筛选和查看 iamai 社区扩展。</p>"
            "</div>"
            '<div class="iamai-store-submit__mount">Loading submission form...</div>'
            "</div>"
            '<div class="iamai-store__loading">Loading community entries...</div>'
            "</section>"
        )
        return [nodes.raw("", html, format="html")]


class iamaiStoreCardDirective(Directive):
    """Render one ecosystem card by id."""

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        entry_id = self.arguments[0]
        html = (
            '<div class="iamai-store-card-slot" '
            f'data-iamai-store-card="{_escape_attr(entry_id)}">'
            f"Loading {_escape_html(entry_id)}..."
            "</div>"
        )
        return [nodes.raw("", html, format="html")]


class iamaiStoreSubmitDirective(Directive):
    """Render an ecosystem submission form."""

    has_content = False
    option_spec = {
        "title": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        title = self.options.get("title", "提交社区扩展")
        app = self.state.document.settings.env.app
        github_repo = str(getattr(app.config, "iamai_store_github_repo", ""))
        issue_template = str(
            getattr(app.config, "iamai_store_issue_template", DEFAULT_GITHUB_ISSUE_TEMPLATE)
        )
        submit_api_url = str(getattr(app.config, "iamai_store_submit_api_url", ""))
        html = (
            '<section class="iamai-store-submit" data-iamai-store-submit '
            f'data-github-repo="{_escape_attr(github_repo)}" '
            f'data-issue-template="{_escape_attr(issue_template)}" '
            f'data-submit-api-url="{_escape_attr(submit_api_url)}">'
            f"<h2>{_escape_html(title)}</h2>"
            "<p>填写表单后会生成一个 GitHub issue；维护者审核通过后再合入社区 registry。</p>"
            '<div class="iamai-store-submit__mount">Loading submission form...</div>'
            "</section>"
        )
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the iamai store extension."""

    app.add_config_value(
        "iamai_store_registry_paths",
        ["ecosystem/entries"],
        "env",
        types=frozenset({list, tuple}),
    )
    app.add_config_value("iamai_store_github_repo", "", "html", types=frozenset({str}))
    app.add_config_value(
        "iamai_store_issue_template",
        DEFAULT_GITHUB_ISSUE_TEMPLATE,
        "html",
        types=frozenset({str}),
    )
    app.add_config_value("iamai_store_submit_api_url", "", "html", types=frozenset({str}))
    app.add_directive("iamai-store", iamaiStoreDirective)
    app.add_directive("iamai-store-card", iamaiStoreCardDirective)
    app.add_directive("iamai-store-submit", iamaiStoreSubmitDirective)
    app.connect("builder-inited", _on_builder_inited)
    app.connect("build-finished", _on_build_finished)
    app.add_js_file(STORE_INDEX_JS_FILENAME, defer="defer")
    app.add_js_file(STORE_JS_FILENAME, defer="defer")
    app.add_css_file(STORE_CSS_FILENAME)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def load_store_index(
    source_dir: str | Path, registry_paths: list[str] | tuple[str, ...]
) -> StoreIndex:
    """Load and validate registry entries from configured paths."""

    root = Path(source_dir)
    entries: list[StoreEntry] = []
    for raw_path in registry_paths:
        path = (root / raw_path).resolve()
        if path.is_dir():
            files = sorted(path.glob("*.json"))
        elif path.is_file():
            files = [path]
        else:
            continue
        for file_path in files:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                entries.append(StoreEntry.model_validate(data))
            except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
                raise ValueError(f"invalid iamai store entry {file_path}: {exc}") from exc
    return StoreIndex(
        entries=sorted(entries, key=lambda item: (_sort_rank(item), item.name.casefold()))
    )


def build_submission_issue_body(submission: StoreSubmission) -> str:
    """Return a GitHub issue body containing the candidate registry entry."""

    entry = submission.to_store_entry()
    entry_json = json.dumps(
        entry.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2
    )
    return "\n".join(
        [
            "## Ecosystem submission",
            "",
            "Please review this iamai ecosystem entry.",
            "",
            "```json",
            entry_json,
            "```",
            "",
            "## Review checklist",
            "",
            "- [ ] Package or repository is reachable.",
            "- [ ] Entry points match the published package metadata when applicable.",
            "- [ ] iamai_requires matches the package's published Requires-Dist metadata.",
            "- [ ] Conformance evidence is public and reproducible when required.",
            "- [ ] No secrets, private endpoints, or unsafe install steps are included.",
            "- [ ] Verification badges are assigned by maintainers only.",
        ]
    )


def build_submission_issue_url(
    github_repo: str,
    submission: StoreSubmission,
    *,
    issue_template: str = DEFAULT_GITHUB_ISSUE_TEMPLATE,
) -> str:
    """Return a prefilled GitHub new issue URL for one submission."""

    title = f"[Ecosystem] {submission.name}"
    entry = submission.to_store_entry()
    registry_json = json.dumps(
        entry.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2
    )
    requires_conformance = submission.type in {"plugin", "adapter"}
    not_applicable = "Not applicable"
    query = urlencode(
        {
            "template": issue_template,
            "title": title,
            "extension_type": submission.type,
            "entry_id": submission.id,
            "display_name": submission.name,
            "summary": submission.summary,
            "package_name": submission.package or "",
            "repository_url": submission.repository or "",
            "iamai_requires": submission.iamai_requires
            or ("" if requires_conformance else not_applicable),
            "conformance_evidence": "\n".join(submission.conformance_evidence)
            or ("" if requires_conformance else not_applicable),
            "runtime_capabilities": ", ".join(submission.runtime_capabilities),
            "security_notes": submission.security_notes or "",
            "permission_notes": submission.permission_notes or "",
            "registry_json": registry_json,
            "body": build_submission_issue_body(submission),
        }
    )
    return f"https://github.com/{github_repo}/issues/new?{query}"


def _on_builder_inited(app: Sphinx) -> None:
    registry_paths = list(getattr(app.config, "iamai_store_registry_paths", []))
    index = load_store_index(app.srcdir, registry_paths)
    app.env.iamai_store_index = index.to_json_payload()


def _on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    if exception is not None:
        return
    static_dir = Path(app.outdir) / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)
    payload = getattr(app.env, "iamai_store_index", {"version": STORE_VERSION, "entries": []})
    (static_dir / STORE_INDEX_FILENAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (static_dir / STORE_INDEX_JS_FILENAME).write_text(
        "window.iamai_STORE_INDEX = "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )


def _sort_rank(entry: StoreEntry) -> int:
    badges = set(entry.verification)
    if "official" in badges:
        return 0
    if "security_reviewed" in badges:
        return 10
    if "author_verified" in badges:
        return 20
    if "package_verified" in badges:
        return 30
    if entry.status == "deprecated":
        return 90
    return 50


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _escape_attr(value: str) -> str:
    return _escape_html(value).replace("'", "&#x27;")
