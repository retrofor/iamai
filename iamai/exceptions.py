"""iamai Exception.

The following are exceptions that may be thrown when iamai is running. Most of these exceptions do not require user handling, iamai will automatically catch and handle them.
For adapter developers, all exceptions thrown by adapters should inherit from `AdapterException`.
"""

__all__ = [
    "EventException",
    "SkipException",
    "StopException",
    "iamaiException",
    "GetEventTimeout",
    "AdapterException",
    "LoadModuleError",
]


class EventException(BaseException):
    """Exceptions thrown by plug-ins during event processing are used to control the propagation of events and will be automatically captured and processed by iamai."""


class SkipException(EventException):
    """Skip the current plugin and continue the current event propagation."""


class StopException(EventException):
    """Stop propagation of current events."""


class iamaiException(Exception):  # noqa: N818
    """Base class for all exceptions that occur with iamai."""


class GetEventTimeout(iamaiException):
    """Thrown when the get method times out."""


class AdapterException(iamaiException):
    """Base class for exceptions thrown by adapters. All exceptions thrown by adapters should inherit from this class."""


class LoadModuleError(iamaiException):
    """Loading module error, thrown when a class of a specific type cannot be found in the specified module or there are multiple qualifying classes in the module."""
