"""Testing helpers for iamai extension authors."""

from .adapters import (
    AdapterConformanceError,
    assert_adapter_api_result,
    assert_adapter_can_close,
    assert_adapter_cancellation,
    assert_adapter_config,
    assert_adapter_error,
    assert_adapter_event,
    assert_adapter_lifecycle,
    assert_adapter_send_result,
    assert_adapter_start_failure,
)
from .plugins import (
    PluginConformanceError,
    assert_plugin_config,
    assert_plugin_dependencies,
    assert_plugin_handler,
    assert_plugin_lifecycle,
    assert_plugin_metadata,
    assert_plugin_permission,
    assert_plugin_startup_failure_cleanup,
)

__all__ = [
    "AdapterConformanceError",
    "PluginConformanceError",
    "assert_adapter_api_result",
    "assert_adapter_can_close",
    "assert_adapter_cancellation",
    "assert_adapter_config",
    "assert_adapter_error",
    "assert_adapter_event",
    "assert_adapter_lifecycle",
    "assert_adapter_send_result",
    "assert_adapter_start_failure",
    "assert_plugin_config",
    "assert_plugin_dependencies",
    "assert_plugin_handler",
    "assert_plugin_lifecycle",
    "assert_plugin_metadata",
    "assert_plugin_permission",
    "assert_plugin_startup_failure_cleanup",
]
