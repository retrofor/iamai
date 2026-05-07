"""Minimal HTTP server and JSON client helpers used by adapters."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Awaitable, Callable
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import parse_qs, urlsplit

from .net import OutboundUrlPolicy, validate_outbound_url

LOGGER = logging.getLogger("iamai.http")


class HttpError(ValueError):
    """HTTP protocol or payload error with a response status code."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(slots=True)
class HttpRequest:
    """Parsed HTTP request passed to ``SimpleHttpServer`` route handlers."""

    method: str
    path: str
    query_string: str
    headers: dict[str, str]
    body: bytes
    client: tuple[str, int] | None = None

    @property
    def query(self) -> dict[str, list[str]]:
        """Return parsed query parameters."""
        return parse_qs(self.query_string)

    @property
    def content_type(self) -> str:
        """Return the normalized media type without parameters."""
        return self.headers.get("content-type", "").split(";", 1)[0].strip().lower()

    def has_json_content_type(self) -> bool:
        """Return whether the request declares a JSON-compatible content type."""
        content_type = self.content_type
        if not content_type:
            return True
        if content_type == "application/json":
            return True
        return content_type.startswith("application/") and content_type.endswith("+json")

    def text(self, encoding: str = "utf-8") -> str:
        """Decode the request body as text."""
        return self.body.decode(encoding)

    def json(self) -> Any:
        """Decode the request body as JSON."""
        if not self.body:
            return None
        try:
            return json.loads(self.text())
        except json.JSONDecodeError as exc:
            raise HttpError(400, "invalid JSON payload") from exc


@dataclass(slots=True)
class HttpResponse:
    """HTTP response returned by route handlers."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @classmethod
    def json(
        cls,
        payload: Any,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> "HttpResponse":
        """Create a JSON response."""
        base_headers = {"Content-Type": "application/json; charset=utf-8"}
        if headers:
            base_headers.update(headers)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return cls(status=status, headers=base_headers, body=body)

    @classmethod
    def text(
        cls,
        payload: str,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> "HttpResponse":
        """Create a plain text response."""
        base_headers = {"Content-Type": "text/plain; charset=utf-8"}
        if headers:
            base_headers.update(headers)
        return cls(status=status, headers=base_headers, body=payload.encode("utf-8"))


class SimpleHttpServer:
    """Small asyncio HTTP/1.1 server for adapter webhook endpoints."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        read_timeout: float = 10.0,
        max_header_bytes: int = 16_384,
        max_body_bytes: int = 1_048_576,
    ) -> None:
        self.host = host
        self.port = port
        self.read_timeout = float(read_timeout)
        self.max_header_bytes = int(max_header_bytes)
        self.max_body_bytes = int(max_body_bytes)
        self._routes: dict[
            tuple[str, str],
            Callable[[HttpRequest], Awaitable[HttpResponse] | HttpResponse],
        ] = {}
        self._server: asyncio.AbstractServer | None = None

    def route(
        self,
        method: str,
        path: str,
        handler: Callable[[HttpRequest], Awaitable[HttpResponse] | HttpResponse],
    ) -> None:
        """Register a route handler for one method and path."""
        self._routes[(method.upper(), path)] = handler

    async def start(self) -> None:
        """Start accepting HTTP connections."""
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port,
            limit=self.max_header_bytes,
        )

    async def close(self) -> None:
        """Stop accepting HTTP connections."""
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        response = HttpResponse.text("bad request", status=400)
        try:
            request = await self._read_request(reader, writer)
            handler = self._routes.get((request.method.upper(), request.path))
            if handler is None:
                response = HttpResponse.json({"error": "not found"}, status=404)
            else:
                result = handler(request)
                if isinstance(result, HttpResponse):
                    response = result
                else:
                    response = await result
        except HttpError as exc:
            response = HttpResponse.json({"error": exc.message}, status=exc.status)
        except Exception:
            LOGGER.exception("HTTP handler failed")
            response = HttpResponse.json({"error": "internal server error"}, status=500)
        finally:
            await self._write_response(writer, response)

    async def _read_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> HttpRequest:
        try:
            header_bytes = await asyncio.wait_for(
                reader.readuntil(b"\r\n\r\n"),
                timeout=self.read_timeout,
            )
        except asyncio.LimitOverrunError as exc:
            raise HttpError(431, "request headers too large") from exc
        except asyncio.IncompleteReadError as exc:
            raise HttpError(400, "incomplete request headers") from exc
        except asyncio.TimeoutError as exc:
            raise HttpError(408, "request read timeout") from exc

        if len(header_bytes) > self.max_header_bytes:
            raise HttpError(431, "request headers too large")

        header_text = header_bytes.decode("latin1")
        lines = header_text.split("\r\n")
        request_line = lines[0]
        try:
            method, target, _ = request_line.split(" ", 2)
        except ValueError as exc:
            raise HttpError(400, "invalid request line") from exc

        headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        try:
            length = int(headers.get("content-length", "0") or "0")
        except ValueError as exc:
            raise HttpError(400, "invalid content-length") from exc
        if length < 0:
            raise HttpError(400, "invalid content-length")
        if length > self.max_body_bytes:
            raise HttpError(413, "request body too large")

        try:
            body = (
                await asyncio.wait_for(reader.readexactly(length), timeout=self.read_timeout)
                if length
                else b""
            )
        except asyncio.IncompleteReadError as exc:
            raise HttpError(400, "incomplete request body") from exc
        except asyncio.TimeoutError as exc:
            raise HttpError(408, "request body read timeout") from exc

        parsed = urlsplit(target)
        client = writer.get_extra_info("peername")
        return HttpRequest(
            method=method,
            path=parsed.path,
            query_string=parsed.query,
            headers=headers,
            body=body,
            client=client,
        )

    async def _write_response(self, writer: asyncio.StreamWriter, response: HttpResponse) -> None:
        reason = HTTPStatus(response.status).phrase
        headers = dict(response.headers)
        headers.setdefault("Content-Length", str(len(response.body)))
        headers.setdefault("Connection", "close")
        header_lines = [f"HTTP/1.1 {response.status} {reason}\r\n"]
        header_lines.extend(f"{key}: {value}\r\n" for key, value in headers.items())
        header_lines.append("\r\n")
        writer.write("".join(header_lines).encode("latin1"))
        writer.write(response.body)
        await writer.drain()
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


class _NoRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise urllib_error.HTTPError(newurl, code, "redirects are disabled", headers, fp)


async def request_json(
    url: str,
    *,
    method: str = "POST",
    json_body: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
    policy: OutboundUrlPolicy | None = None,
) -> Any:
    """Send a JSON HTTP request and parse a JSON response body."""
    payload = (
        None if json_body is None else json.dumps(json_body, ensure_ascii=False).encode("utf-8")
    )
    request_headers = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        request_headers.update(headers)

    def _run() -> Any:
        if policy is not None:
            validate_outbound_url(url, policy=policy)
        req = urllib_request.Request(
            url=url, data=payload, headers=request_headers, method=method.upper()
        )
        opener = (
            urllib_request.build_opener()
            if policy is None or policy.allow_redirects
            else urllib_request.build_opener(_NoRedirectHandler())
        )
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read()
            if not body:
                return None
            return json.loads(body.decode("utf-8"))

    return await asyncio.to_thread(_run)
