"""Provider-aware webhook signature verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from .httpio import HttpRequest
from .net import compare_secret

SUPPORTED_SIGNATURE_PROVIDERS = ("generic", "github", "stripe")


@dataclass(frozen=True, slots=True)
class SignatureVerificationResult:
    """Result object returned by webhook signature verifiers."""

    ok: bool
    provider: str
    reason: str = "ok"


class WebhookSignatureVerifier(ABC):
    """Base class for provider-specific webhook signature verification."""

    provider = "generic"

    def __init__(self, secret: str) -> None:
        self.secret = str(secret)
        self._seen_signatures: dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        """Return whether verification is active for this verifier."""
        return bool(self.secret)

    def verify(self, request: HttpRequest) -> SignatureVerificationResult:
        """Verify a request and return a structured success or failure."""

        if not self.enabled:
            return SignatureVerificationResult(True, provider=self.provider, reason="disabled")
        return self._verify(request, now=time.time())

    @abstractmethod
    def _verify(self, request: HttpRequest, *, now: float) -> SignatureVerificationResult:
        raise NotImplementedError

    def _check_and_remember_replay(self, key: str | None, *, now: float, ttl: int) -> bool:
        if not key or ttl <= 0:
            return True
        cutoff = now - ttl
        stale = [item for item, seen_at in self._seen_signatures.items() if seen_at < cutoff]
        for item in stale:
            self._seen_signatures.pop(item, None)
        if key in self._seen_signatures:
            return False
        self._seen_signatures[key] = now
        return True


class GenericWebhookSignatureVerifier(WebhookSignatureVerifier):
    """Verify HMAC-SHA256 signatures carried by configurable headers."""

    provider = "generic"

    def __init__(
        self,
        secret: str,
        *,
        header: str,
        prefix: str,
        timestamp_header: str,
        tolerance_seconds: int,
    ) -> None:
        super().__init__(secret)
        self.header = str(header).strip().lower()
        self.prefix = str(prefix)
        self.timestamp_header = str(timestamp_header).strip().lower()
        self.tolerance_seconds = int(tolerance_seconds)

    def _verify(self, request: HttpRequest, *, now: float) -> SignatureVerificationResult:
        provided = request.headers.get(self.header, "").strip()
        if not provided:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="missing_signature"
            )
        if self.prefix:
            if not provided.startswith(self.prefix):
                return SignatureVerificationResult(
                    False, provider=self.provider, reason="invalid_signature_prefix"
                )
            provided = provided[len(self.prefix) :]

        signed_payload = request.body
        replay_key: str | None = None
        if self.timestamp_header:
            timestamp = request.headers.get(self.timestamp_header, "").strip()
            if not timestamp:
                return SignatureVerificationResult(
                    False, provider=self.provider, reason="missing_timestamp"
                )
            try:
                timestamp_value = int(timestamp)
            except ValueError:
                return SignatureVerificationResult(
                    False, provider=self.provider, reason="invalid_timestamp"
                )
            if abs(now - timestamp_value) > self.tolerance_seconds:
                return SignatureVerificationResult(
                    False, provider=self.provider, reason="expired_timestamp"
                )
            replay_key = f"{timestamp}:{provided}"
            signed_payload = f"{timestamp}.".encode("utf-8") + request.body

        expected = hmac.new(
            self.secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not compare_secret(expected, provided):
            return SignatureVerificationResult(
                False, provider=self.provider, reason="invalid_signature"
            )
        if not self._check_and_remember_replay(replay_key, now=now, ttl=self.tolerance_seconds):
            return SignatureVerificationResult(
                False, provider=self.provider, reason="replayed_signature"
            )
        return SignatureVerificationResult(True, provider=self.provider)


class GitHubWebhookSignatureVerifier(GenericWebhookSignatureVerifier):
    """Verify GitHub ``X-Hub-Signature-256`` webhook signatures."""

    provider = "github"

    def __init__(self, secret: str) -> None:
        super().__init__(
            secret,
            header="x-hub-signature-256",
            prefix="sha256=",
            timestamp_header="",
            tolerance_seconds=0,
        )


class StripeWebhookSignatureVerifier(WebhookSignatureVerifier):
    """Verify Stripe-style timestamped ``Stripe-Signature`` headers."""

    provider = "stripe"

    def __init__(self, secret: str, *, tolerance_seconds: int) -> None:
        super().__init__(secret)
        self.tolerance_seconds = int(tolerance_seconds)

    def _verify(self, request: HttpRequest, *, now: float) -> SignatureVerificationResult:
        header_value = request.headers.get("stripe-signature", "").strip()
        if not header_value:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="missing_signature"
            )
        parts = _parse_signature_header(header_value)
        timestamps = parts.get("t", [])
        signatures = parts.get("v1", [])
        if not timestamps:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="missing_timestamp"
            )
        if not signatures:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="missing_signature"
            )
        try:
            timestamp_value = int(timestamps[-1])
        except ValueError:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="invalid_timestamp"
            )
        if abs(now - timestamp_value) > self.tolerance_seconds:
            return SignatureVerificationResult(
                False, provider=self.provider, reason="expired_timestamp"
            )

        signed_payload = f"{timestamp_value}.".encode("utf-8") + request.body
        expected = hmac.new(
            self.secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not any(compare_secret(expected, candidate) for candidate in signatures):
            return SignatureVerificationResult(
                False, provider=self.provider, reason="invalid_signature"
            )

        replay_key = f"{timestamp_value}:{expected}"
        if not self._check_and_remember_replay(replay_key, now=now, ttl=self.tolerance_seconds):
            return SignatureVerificationResult(
                False, provider=self.provider, reason="replayed_signature"
            )
        return SignatureVerificationResult(True, provider=self.provider)


def build_webhook_signature_verifier(
    config: Mapping[str, Any],
) -> WebhookSignatureVerifier:
    """Create a webhook signature verifier from adapter configuration."""

    provider = str(config.get("signature_provider", "generic")).strip().lower() or "generic"
    secret = str(config.get("signature_secret", ""))
    if provider == "generic":
        return GenericWebhookSignatureVerifier(
            secret,
            header=str(config.get("signature_header", "x-iamai-signature")),
            prefix=str(config.get("signature_prefix", "sha256=")),
            timestamp_header=str(config.get("timestamp_header", "x-iamai-timestamp")),
            tolerance_seconds=int(config.get("timestamp_tolerance_seconds", 300)),
        )
    if provider == "github":
        return GitHubWebhookSignatureVerifier(secret)
    if provider == "stripe":
        return StripeWebhookSignatureVerifier(
            secret,
            tolerance_seconds=int(config.get("timestamp_tolerance_seconds", 300)),
        )
    raise ValueError(f"unsupported webhook signature provider: {provider!r}")


def _parse_signature_header(value: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for part in value.split(","):
        key, sep, item = part.strip().partition("=")
        if not sep:
            continue
        normalized_key = key.strip().lower()
        normalized_item = item.strip()
        if not normalized_key or not normalized_item:
            continue
        result.setdefault(normalized_key, []).append(normalized_item)
    return result
