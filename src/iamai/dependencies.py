"""iamai dependency injection.

Implement dependency injection related functions.
"""

import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from .utils import get_annotations, sync_ctx_manager_wrapper

_T = TypeVar("_T")
Dependency = Union[
    # Class
    Type[Union[_T, AsyncContextManager[_T], ContextManager[_T]]],
    # GeneratorContextManager
    Callable[[], AsyncGenerator[_T, None]],
    Callable[[], Generator[_T, None, None]],
]


__all__ = ["Depends"]


class InnerDepends:
    """Internal implementation of subdependency.

    Users do not need to pay attention to this internal implementation.

    Attributes:
        dependency: dependency class. If not specified, it will be automatically determined based on the type annotation of the field.
        use_cache: whether to use cache. Defaults to ``True``.
    """

    dependency: Optional[Dependency[Any]]
    use_cache: bool

    def __init__(
        self, dependency: Optional[Dependency[Any]] = None, *, use_cache: bool = True
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"InnerDepends({attr}{cache})"


def Depends(  # noqa: N802 # pylint: disable=invalid-name
    dependency: Optional[Dependency[_T]] = None, *, use_cache: bool = True
) -> _T:
    """Subdependency decorator.

    Args:
        dependency: dependency class. If not specified, it will be automatically determined based on the type annotation of the field.
        use_cache: whether to use cache. Defaults to ``True``.

    Returns:
        Returns the internal child dependency object.
    """
    return InnerDepends(dependency=dependency, use_cache=use_cache)  # type: ignore


async def solve_dependencies(
    dependent: Dependency[_T],
    *,
    use_cache: bool,
    stack: AsyncExitStack,
    dependency_cache: Dict[Dependency[Any], Any],
) -> _T:
    """Resolve subdependencies.

    Args:
        dependent: dependent class.
        use_cache: whether to use cache.
        stack: ``AsyncExitStack`` object.
        dependency_cache: dependency cache.

    Raises:
        TypeError: Parsing error.

    Returns:
        Object that resolves sub-dependencies.
    """
    if use_cache and dependent in dependency_cache:
        return dependency_cache[dependent]

    if isinstance(dependent, type):
        # type of dependent is Type[T]
        values: Dict[str, Any] = {}
        ann = get_annotations(dependent)
        for name, sub_dependent in inspect.getmembers(
            dependent, lambda x: isinstance(x, InnerDepends)
        ):
            assert isinstance(sub_dependent, InnerDepends)
            if sub_dependent.dependency is None:
                dependent_ann = ann.get(name, None)
                if dependent_ann is None:
                    raise TypeError("can not solve dependent")
                sub_dependent.dependency = dependent_ann
            values[name] = await solve_dependencies(
                sub_dependent.dependency,
                use_cache=sub_dependent.use_cache,
                stack=stack,
                dependency_cache=dependency_cache,
            )
        depend_obj = cast(
            Union[_T, AsyncContextManager[_T], ContextManager[_T]],
            dependent.__new__(dependent),  # pyright: ignore[reportGeneralTypeIssues]
        )
        for key, value in values.items():
            setattr(depend_obj, key, value)
        depend_obj.__init__()  # type: ignore[misc] # pylint: disable=unnecessary-dunder-call

        if isinstance(depend_obj, AsyncContextManager):
            depend = await stack.enter_async_context(
                depend_obj  # pyright: ignore[reportUnknownArgumentType]
            )
        elif isinstance(depend_obj, ContextManager):
            depend = await stack.enter_async_context(
                sync_ctx_manager_wrapper(
                    depend_obj  # pyright: ignore[reportUnknownArgumentType]
                )
            )
        else:
            depend = depend_obj
    elif inspect.isasyncgenfunction(dependent):
        # type of dependent is Callable[[], AsyncGenerator[T, None]]
        cm = asynccontextmanager(dependent)()
        depend = cast(_T, await stack.enter_async_context(cm))
    elif inspect.isgeneratorfunction(dependent):
        # type of dependent is Callable[[], Generator[T, None, None]]
        cm = sync_ctx_manager_wrapper(contextmanager(dependent)())
        depend = cast(_T, await stack.enter_async_context(cm))
    else:
        raise TypeError("dependent is not a class or generator function")

    dependency_cache[dependent] = depend
    return depend
