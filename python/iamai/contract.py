"""Versioned public API compatibility metadata and deprecation support."""

from __future__ import annotations

import warnings
from typing import Literal

PUBLIC_API_CONTRACT_VERSION = "1"
PLUGIN_ENTRY_POINT_GROUP = "iamai.plugins"
ADAPTER_ENTRY_POINT_GROUP = "iamai.adapters"

DeprecationKind = Literal["symbol", "config_key", "entry_point", "serialized_field"]
_DEPRECATION_KINDS = frozenset({"symbol", "config_key", "entry_point", "serialized_field"})


class IamaiDeprecationWarning(FutureWarning):
    """Structured warning for a planned public API removal."""

    def __init__(
        self,
        *,
        code: str,
        kind: DeprecationKind,
        subject: str,
        since: str,
        remove_in: str,
        replacement: str | None = None,
    ) -> None:
        if not isinstance(kind, str) or kind not in _DEPRECATION_KINDS:
            allowed = ", ".join(sorted(_DEPRECATION_KINDS))
            raise ValueError(f"kind must be one of: {allowed}")
        _require_non_empty_trimmed(code, field="code")
        _require_non_empty_trimmed(subject, field="subject")
        _require_non_empty_trimmed(since, field="since")
        _require_non_empty_trimmed(remove_in, field="remove_in")
        if replacement is not None:
            _require_non_empty_trimmed(replacement, field="replacement")
        self.code = code
        self.kind = kind
        self.subject = subject
        self.since = since
        self.remove_in = remove_in
        self.replacement = replacement
        replacement_text = replacement if replacement is not None else "none"
        super().__init__(
            "iamai deprecation: "
            f"code={code}; kind={kind}; subject={subject}; since={since}; "
            f"remove_in={remove_in}; replacement={replacement_text}"
        )


def _warn_deprecated(
    *,
    code: str,
    kind: DeprecationKind,
    subject: str,
    since: str,
    remove_in: str,
    replacement: str | None = None,
    stacklevel: int = 1,
) -> None:
    """Emit a structured deprecation warning at the caller-selected frame."""
    warnings.warn(
        IamaiDeprecationWarning(
            code=code,
            kind=kind,
            subject=subject,
            since=since,
            remove_in=remove_in,
            replacement=replacement,
        ),
        stacklevel=stacklevel + 1,
    )


def _require_non_empty_trimmed(value: object, *, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be a non-empty trimmed string")
