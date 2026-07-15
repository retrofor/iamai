"""Installable reference plugin fixture."""

from iamai import Plugin
from pydantic import BaseModel, Field


class ReferencePluginConfig(BaseModel):
    """Schema-bearing configuration published by the reference plugin."""

    greeting: str = "hello from the installed plugin"
    credential: str = Field(default="", json_schema_extra={"writeOnly": True})
    max_tokens: int = 128


class ReferencePlugin(Plugin):
    """Minimal plugin exported through the ``iamai.plugins`` entry-point group."""

    name = "reference_plugin"
    description = "Installed reference plugin"
    config_model = ReferencePluginConfig
