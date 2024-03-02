"""A utility used internally by iamai."""

import asyncio
import importlib
import inspect
import json
import os
import os.path
import sys
import traceback
from abc import ABC
from contextlib import asynccontextmanager
from functools import partial
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder
from types import GetSetDescriptorType, ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    ClassVar,
    ContextManager,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import ParamSpec, TypeAlias, TypeGuard

from pydantic import BaseModel

from .config import ConfigModel
from .typing import EventT

if TYPE_CHECKING:
    from os import PathLike

__all__ = [
    "ModulePathFinder",
    "is_config_class",
    "get_classes_from_module",
    "get_classes_from_module_name",
    "PydanticEncoder",
    "samefile",
    "sync_func_wrapper",
    "sync_ctx_manager_wrapper",
    "wrap_get_func",
    "get_annotations",
]

_T = TypeVar("_T")
_P = ParamSpec("_P")
_R = TypeVar("_R")
_TypeT = TypeVar("_TypeT", bound=Type[Any])

StrOrBytesPath: TypeAlias = Union[str, bytes, "PathLike[str]", "PathLike[bytes]"]


class ModulePathFinder(MetaPathFinder):
    """Meta path finder for finding iamai components."""

    path: ClassVar[List[str]] = []

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]] = None,
        target: Optional[ModuleType] = None,
    ) -> Union[ModuleSpec, None]:
        """Used to find the ``spec`` of a specified module."""
        if path is None:
            path = []
        return PathFinder.find_spec(fullname, self.path + list(path), target)


def is_config_class(config_class: Any) -> TypeGuard[Type[ConfigModel]]:
    """Determine whether an object is a configuration class.

    Args:
        config_class: The object to be judged.

    Returns:
        Returns whether it is a configuration class.
    """
    return (
        inspect.isclass(config_class)
        and issubclass(config_class, ConfigModel)
        and isinstance(getattr(config_class, "__config_name__", None), str)
        and ABC not in config_class.__bases__
        and not inspect.isabstract(config_class)
    )


def get_classes_from_module(module: ModuleType, super_class: _TypeT) -> List[_TypeT]:
    """Find a class of the specified type from the module.

    Args:
        module: Python module.
        super_class: The superclass of the class to be found.

    Returns:
        Returns a list of classes that meet the criteria.
    """
    classes: List[_TypeT] = []
    for _, module_attr in inspect.getmembers(module, inspect.isclass):
        if (
            (inspect.getmodule(module_attr) or module) is module
            and issubclass(module_attr, super_class)
            and module_attr != super_class
            and ABC not in module_attr.__bases__
            and not inspect.isabstract(module_attr)
        ):
            classes.append(cast(_TypeT, module_attr))
    return classes


def get_classes_from_module_name(
    name: str, super_class: _TypeT, *, reload: bool = False
) -> List[Tuple[_TypeT, ModuleType]]:
    """Find a class of the specified type from the module with the specified name.

    Args:
        name: module name, the format is the same as the Python ``import`` statement.
        super_class: The superclass of the class to be found.
        reload: Whether to reload the module.

    Returns:
        Returns a list of tuples consisting of classes and modules that meet the criteria.

    Raises:
        ImportError: An error occurred while importing the module.
    """
    try:
        importlib.invalidate_caches()
        module = importlib.import_module(name)
        if reload:
            importlib.reload(module)
        return [(x, module) for x in get_classes_from_module(module, super_class)]
    except KeyboardInterrupt:
        # Do not capture KeyboardInterrupt
        # Catching KeyboardInterrupt will prevent the user from closing Python when the module being imported is stuck in an infinite loop
        raise
    except BaseException as e:
        raise ImportError(e, traceback.format_exc()) from e


class PydanticEncoder(json.JSONEncoder):
    """``JSONEncoder`` class for parsing ``pydantic.BaseModel``."""

    def default(self, o: Any) -> Any:
        """Returns a serializable object of ``o``."""
        if isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        return super().default(o)


def samefile(path1: StrOrBytesPath, path2: StrOrBytesPath) -> bool:
    """A simple wrapper around ``os.path.samefile``.

    Args:
        path1: path1.
        path2: path 2.

    Returns:
        If two paths point to the same file or directory.
    """
    try:
        return path1 == path2 or os.path.samefile(path1, path2)  # noqa: PTH121
    except OSError:
        return False


def sync_func_wrapper(
    func: Callable[_P, _R], *, to_thread: bool = False
) -> Callable[_P, Coroutine[None, None, _R]]:
    """Wrap a synchronous function as an asynchronous function.

    Args:
        func: synchronous function to be packaged.
        to_thread: Whether to run the synchronization function in a separate thread. Defaults to ``False``.

    Returns:
        Asynchronous functions.
    """
    if to_thread:

        async def _wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            loop = asyncio.get_running_loop()
            func_call = partial(func, *args, **kwargs)
            return await loop.run_in_executor(None, func_call)

    else:

        async def _wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return func(*args, **kwargs)

    return _wrapper


@asynccontextmanager
async def sync_ctx_manager_wrapper(
    cm: ContextManager[_T], *, to_thread: bool = False
) -> AsyncGenerator[_T, None]:
    """Wrap a synchronous context manager into an asynchronous context manager.

    Args:
        cm: The synchronization context manager to be wrapped.
        to_thread: Whether to run the synchronization function in a separate thread. Defaults to ``False``.

    Returns:
        Asynchronous context manager.
    """
    try:
        yield await sync_func_wrapper(cm.__enter__, to_thread=to_thread)()
    except Exception as e:
        if not await sync_func_wrapper(cm.__exit__, to_thread=to_thread)(
            type(e), e, e.__traceback__
        ):
            raise
    else:
        await sync_func_wrapper(cm.__exit__, to_thread=to_thread)(None, None, None)


def wrap_get_func(
    func: Optional[Callable[[EventT], Union[bool, Awaitable[bool]]]],
) -> Callable[[EventT], Awaitable[bool]]:
    """Wrap the parameters accepted by the ``get()`` function into an asynchronous function.

    Args:
        func: The parameters accepted by the ``get()`` function.

    Returns:
        Asynchronous functions.
    """
    if func is None:
        return sync_func_wrapper(lambda _: True)
    if not asyncio.iscoroutinefunction(func):
        return sync_func_wrapper(func)  # type: ignore
    return func


if sys.version_info >= (3, 10):  # pragma: no cover
    from inspect import get_annotations
else:  # pragma: no cover

    def get_annotations(
        obj: Union[Callable[..., object], Type[Any], ModuleType],
    ) -> Dict[str, Any]:
        """Compute the annotation dictionary of an object.

        Args:
            obj: A callable object, class, or module.

        Raises:
            TypeError: ``obj`` is not a callable object, class or module.
            ValueError: Object's ``__annotations__`` is not a dictionary or ``None``.

        Returns:
            Annotation dictionary for objects.
        """
        ann: Union[Dict[str, Any], None]

        if isinstance(obj, type):
            # class
            obj_dict = getattr(obj, "__dict__", None)
            if obj_dict and hasattr(obj_dict, "get"):
                ann = obj_dict.get("__annotations__", None)
                if isinstance(ann, GetSetDescriptorType):
                    ann = None
            else:
                ann = None
        elif isinstance(obj, ModuleType) or callable(obj):
            # this includes types.ModuleType, types.Function, types.BuiltinFunctionType,
            # types.BuiltinMethodType, functools.partial, functools.singledispatch,
            # "class funclike" from Lib/test/test_inspect... on and on it goes.
            ann = getattr(obj, "__annotations__", None)
        else:
            raise TypeError(f"{obj!r} is not a module, class, or callable.")

        if ann is None:
            return {}

        if not isinstance(ann, dict):
            raise ValueError(  # noqa: TRY004
                f"{obj!r}.__annotations__ is neither a dict nor None"
            )

        if not ann:
            return {}

        return dict(ann)
