"""Optional HTTP management API plugin."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from ..httpio import HttpRequest, HttpResponse, SimpleHttpServer
from ..plugin import Plugin

LOGGER = logging.getLogger("iamai.management_api")


class ManagementApiConfig(BaseModel):
    """Configuration for the optional HTTP management API."""

    host: str = "127.0.0.1"
    port: int = 8765
    token: str = Field(min_length=1)
    allow_unsafe_state: bool = False

    @field_validator("port")
    @classmethod
    def _positive_port(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("port must be greater than 0")
        return int(value)


class ManagementApiPlugin(Plugin):
    """Expose read-only runtime diagnostics over HTTP."""

    name = "management_api"
    description = "Optional HTTP management API for runtime diagnostics."
    config_model = ManagementApiConfig

    def __init__(self, runtime: "Runtime") -> None:
        super().__init__(runtime)
        self._server: SimpleHttpServer | None = None

    async def startup(self) -> None:
        config = self._settings()
        server = SimpleHttpServer(config.host, config.port)
        for path, handler in {
            "/health": self._health,
            "/metrics": self._metrics,
            "/adapters": self._adapters,
            "/plugins": self._plugins,
            "/handlers": self._handlers,
            "/sessions": self._sessions,
            "/schema": self._schema,
            "/state": self._state,
        }.items():
            server.route("GET", path, handler)
        await server.start()
        self._server = server
        self.runtime.audit("management_api.start", host=config.host, port=config.port)

    async def shutdown(self) -> None:
        if self._server is None:
            return
        await self._server.close()
        self._server = None
        self.runtime.audit("management_api.stop")

    def _settings(self) -> ManagementApiConfig:
        config = self.config_obj
        if isinstance(config, ManagementApiConfig):
            return config
        return ManagementApiConfig.model_validate(self.config)

    def _authorize(self, request: HttpRequest) -> HttpResponse | None:
        token = self._settings().token
        expected = f"Bearer {token}"
        if request.headers.get("authorization") != expected:
            self.runtime.audit("management_api.request", path=request.path, outcome="unauthorized")
            return HttpResponse.json({"error": "unauthorized"}, status=401)
        return None

    def _json(self, request: HttpRequest, payload: Any) -> HttpResponse:
        unauthorized = self._authorize(request)
        if unauthorized is not None:
            return unauthorized
        self.runtime.audit("management_api.request", path=request.path)
        return HttpResponse.json(payload)

    def _health(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.health())

    def _metrics(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.list_metrics())

    def _adapters(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.list_adapters())

    def _plugins(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.list_plugins())

    def _handlers(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.list_handlers())

    def _sessions(self, request: HttpRequest) -> HttpResponse:
        return self._json(request, self.runtime.list_sessions())

    def _schema(self, request: HttpRequest) -> HttpResponse:
        schemas = {
            plugin["name"]: schema
            for plugin in self.runtime.list_plugins()
            if (schema := self.runtime.get_plugin_schema(plugin["name"])) is not None
        }
        return self._json(request, schemas)

    def _state(self, request: HttpRequest) -> HttpResponse:
        payload: dict[str, Any] = {"backend": self.runtime.state_store.__class__.__name__}
        if self._settings().allow_unsafe_state:
            payload["keys"] = sorted(str(key) for key in self.runtime.state)
        return self._json(request, payload)


if TYPE_CHECKING:
    from ..runtime import Runtime
