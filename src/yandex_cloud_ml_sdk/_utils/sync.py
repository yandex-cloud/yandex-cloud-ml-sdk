from __future__ import annotations

import asyncio
import inspect
import threading
from collections.abc import AsyncIterator, Coroutine, Iterator
from functools import wraps
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

from typing_extensions import Concatenate, ParamSpec

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import YCloudML

T = TypeVar("T")
P = ParamSpec("P")


class _TaskRunner:
    """A task runner that runs an asyncio event loop on a background thread."""

    def __init__(self, event_loop: asyncio.AbstractEventLoop) -> None:
        self.__io_loop = event_loop

    def run(self, coro: Any) -> Any:
        fut = asyncio.run_coroutine_threadsafe(coro, self.__io_loop)
        return fut.result(None)


_runner_map: dict[tuple[str, YCloudML], _TaskRunner] = {}


def run_sync(coro: Callable[Concatenate[Any, P], Awaitable[T]]) -> Callable[Concatenate[Any, P], T]:
    """Wraps coroutine in a function that blocks until it has executed.

    Parameters
    ----------
    coro : coroutine-function
        The coroutine-function to be executed.

    Returns
    -------
    result :
        Whatever the coroutine-function returns.
    """
    if not inspect.iscoroutinefunction(coro):
        raise AssertionError

    @wraps(coro)
    def wrapped(self: Any, *args: P.args, **kwargs: P.kwargs) -> T:
        name = threading.current_thread().name
        inner: Awaitable[T] = coro(self, *args, **kwargs)
        key = (name, self._sdk)
        if key not in _runner_map:
            _runner_map[key] = _TaskRunner(self._sdk._event_loop)  # pylint: disable=protected-access

        result: T = _runner_map[key].run(inner)
        return result

    return wrapped


def run_sync_generator(coro: Callable[..., AsyncIterator[T]]) -> Callable[..., Iterator[T]]:
    """Wraps async iterator function into a usual iterator function that blocks on every cycle.
    """
    if not inspect.isasyncgenfunction(coro):
        raise AssertionError

    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        name = threading.current_thread().name
        inner = coro(self, *args, **kwargs)
        key = (name, self._sdk)
        if key not in _runner_map:
            _runner_map[key] = _TaskRunner(self._sdk._event_loop)  # pylint: disable=protected-access

        def run_from(runner: Callable[[Coroutine], Any]):
            while True:
                try:
                    yield runner(inner.__anext__())  # pylint: disable=unnecessary-dunder-call
                except StopAsyncIteration:
                    break
                except GeneratorExit:
                    runner(inner.aclose())
                    raise

        yield from run_from(_runner_map[key].run)

    wrapped.__doc__ = coro.__doc__
    return wrapped
