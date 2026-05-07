"""Networking and outbound URL safety helpers."""

from __future__ import annotations

import hmac
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit


def compare_secret(expected: str, candidate: str) -> bool:
    """Compare two secret strings using constant-time comparison."""
    return hmac.compare_digest(str(expected), str(candidate))


def is_loopback_host(host: str) -> bool:
    """Return whether a host string is clearly loopback without DNS resolution."""
    normalized = host.strip().lower()
    if not normalized:
        return False
    if normalized in {"localhost", "::1"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class OutboundUrlPolicy:
    """Policy used to validate adapter-controlled outbound URLs."""

    allowed_schemes: tuple[str, ...] = ("https",)
    allowed_hosts: tuple[str, ...] = ()
    allow_private_hosts: bool = False
    allow_redirects: bool = False


def validate_outbound_url(url: str, *, policy: OutboundUrlPolicy) -> None:
    """Validate a URL against scheme, host, private-address, and redirect policy."""
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").strip().lower()

    if scheme not in policy.allowed_schemes:
        raise ValueError(f"unsupported URL scheme: {scheme or '<empty>'}")
    if not hostname:
        raise ValueError("URL hostname is required")
    if parsed.username or parsed.password:
        raise ValueError("userinfo in URL is not allowed")
    if policy.allowed_hosts and not any(_host_matches(hostname, pattern) for pattern in policy.allowed_hosts):
        raise ValueError(f"hostname {hostname!r} is not in the allowlist")
    if policy.allow_private_hosts:
        return

    for address in _resolve_host_ips(hostname):
        if not address.is_global:
            raise ValueError(f"hostname {hostname!r} resolves to a non-public address")


def _host_matches(hostname: str, pattern: str) -> bool:
    normalized = pattern.strip().lower()
    if not normalized:
        return False
    if normalized.startswith("*."):
        suffix = normalized[1:]
        return hostname.endswith(suffix) and hostname != suffix[1:]
    return hostname == normalized


def _resolve_host_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return [ipaddress.ip_address(hostname)]
    except ValueError:
        pass

    results: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM):
        if family not in {socket.AF_INET, socket.AF_INET6}:
            continue
        address = ipaddress.ip_address(sockaddr[0])
        if address not in results:
            results.append(address)
    if not results:
        raise ValueError(f"unable to resolve hostname {hostname!r}")
    return results
