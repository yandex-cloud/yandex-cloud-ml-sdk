from __future__ import annotations

import asyncio
import inspect
import threading
from functools import wraps
from typing import TYPE_CHECKING, Any, AsyncIterator, Awaitable, Callable, Iterator, TypeVar

from typing_extensions import Concatenate, ParamSpec

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

T = TypeVar("T")
P = ParamSpec("P")


class _TaskRunner:
    """A task runner that runs an asyncio event loop on a background thread."""

    def __init__(self, event_loop: asyncio.AbstractEventLoop) -> None:
        self.__io_loop = event_loop

    def run(self, coro: Any) -> Any:
        fut = asyncio.run_coroutine_threadsafe(coro, self.__io_loop)
        return fut.result(None)


_runner_map: dict[tuple[str, BaseSDK], _TaskRunner] = {}


def run_sync_impl(coro: Awaitable[T], sdk: BaseSDK) -> T:
    name = threading.current_thread().name
    key = (name, sdk)
    if key not in _runner_map:
        _runner_map[key] = _TaskRunner(sdk._get_event_loop())  # pylint: disable=protected-access

    result: T = _runner_map[key].run(coro)
    return result


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
        inner: Awaitable[T] = coro(self, *args, **kwargs)
        return run_sync_impl(inner, self._sdk)

    return wrapped


def run_sync_generator_impl(aiter_: AsyncIterator[T], sdk: BaseSDK) -> Iterator[T]:
    name = threading.current_thread().name
    key = (name, sdk)
    if key not in _runner_map:
        _runner_map[key] = _TaskRunner(sdk._get_event_loop())  # pylint: disable=protected-access

    def run_from(runner: Callable[[Awaitable[T]], Any]) -> Iterator[T]:
        while True:
            try:
                # anext function exists only in 3.9+, so we are using __anext__
                yield runner(aiter_.__anext__())  # pylint: disable=unnecessary-dunder-call
            except StopAsyncIteration:
                break
            except GeneratorExit:
                # for some reason mypy thinks AsyncIterator[T] have no aclose method
                runner(aiter_.aclose())  # type: ignore[attr-defined]
                raise

    yield from run_from(_runner_map[key].run)


def run_sync_generator(coro: Callable[..., AsyncIterator[T]]) -> Callable[..., Iterator[T]]:
    """Wraps async iterator function into a usual iterator function that blocks on every cycle.
    """
    assert inspect.isasyncgenfunction(coro)

    @wraps(coro)
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        inner: AsyncIterator[T] = coro(self, *args, **kwargs)
        return run_sync_generator_impl(inner, self._sdk)

    return wrapped
