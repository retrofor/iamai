"""Installable reference plugin fixture."""

from iamai import Plugin


class ReferencePlugin(Plugin):
    """Minimal plugin exported through the ``iamai.plugins`` entry-point group."""

    name = "reference_plugin"
    description = "Installed reference plugin"
