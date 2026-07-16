"""Installable reference plugin fixture."""

from iamai import Context, Plugin, Runtime, message_handler, user_in
from pydantic import BaseModel, Field


class ReferencePluginConfig(BaseModel):
    """Schema-bearing configuration published by the reference plugin."""

    greeting: str = "hello from the installed plugin"
    credential: str = Field(default="", json_schema_extra={"writeOnly": True})
    max_tokens: int = 128


class ReferencePlugin(Plugin):
    """Conforming plugin exported through the ``iamai.plugins`` entry-point group."""

    name = "reference_plugin"
    description = "Installed reference plugin"
    config_model = ReferencePluginConfig
    optional_requires = ("reference_optional",)

    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.active = False

    async def startup(self) -> None:
        self.active = True

    async def shutdown(self) -> None:
        self.active = False

    @message_handler(permission=user_in("allowed"))
    async def handle(self, ctx: Context) -> None:
        self.state["last_text"] = ctx.text


class ReferenceFailingPlugin(ReferencePlugin):
    """Reference plugin whose startup demonstrates self-cleanup."""

    name = "reference_failing_plugin"

    async def startup(self) -> None:
        self.active = True
        try:
            raise RuntimeError("forced reference plugin startup failure")
        finally:
            self.active = False
