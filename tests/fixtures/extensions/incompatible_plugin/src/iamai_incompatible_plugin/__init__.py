"""Deliberately incompatible installable plugin fixture."""

from iamai import Plugin


class IncompatiblePlugin(Plugin):
    """Plugin whose distribution requires an unsupported iamai version."""

    name = "incompatible_plugin"
