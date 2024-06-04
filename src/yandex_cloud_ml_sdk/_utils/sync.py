from __future__ import annotations

import asyncio
import atexit
import inspect
import sys
import threading
from collections.abc import AsyncIterator, Coroutine, Iterator
from contextvars import ContextVar
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


class _TaskRunner:
    """A task runner that runs an asyncio event loop on a background thread."""

    def __init__(self) -> None:
        self.__io_loop: asyncio.AbstractEventLoop | None = None
        self.__runner_thread: threading.Thread | None = None
        self.__lock = threading.Lock()
        atexit.register(self._close)

    def _close(self) -> None:
        if self.__io_loop:
            self.__io_loop.stop()

    def _runner(self) -> None:
        loop = self.__io_loop
        assert loop is not None
        try:
            loop.run_forever()
        finally:
            loop.close()

    def run(self, coro: Any) -> Any:
        """Synchronously runs a coroutine on a background thread."""
        with self.__lock:
            name = f"{threading.current_thread().name} - runner"
            if self.__io_loop is None:
                self.__io_loop = asyncio.new_event_loop()
                self.__runner_thread = threading.Thread(target=self._runner, daemon=True, name=name)
                self.__runner_thread.start()
        fut = asyncio.run_coroutine_threadsafe(coro, self.__io_loop)
        return fut.result(None)


_runner_map: dict[str, _TaskRunner] = {}
_loop: ContextVar[asyncio.AbstractEventLoop | None] = ContextVar("_loop", default=None)


def run_sync(coro: Callable[P, Awaitable[T]]) -> Callable[P, T]:
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
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        result: T
        name = threading.current_thread().name
        inner: Awaitable[T] = coro(*args, **kwargs)
        try:
            # If a loop is currently running in this thread,
            # use a task runner.
            asyncio.get_running_loop()
            if name not in _runner_map:
                _runner_map[name] = _TaskRunner()
            result = _runner_map[name].run(inner)
            return result
        except RuntimeError:
            pass

        # Run the loop for this thread.
        loop = ensure_event_loop()
        result = loop.run_until_complete(inner)
        return result

    return wrapped


def run_sync_generator(coro: Callable[..., AsyncIterator[T]]) -> Callable[..., Iterator[T]]:
    """Wraps async iterator function into a usual iterator function that blocks on every cycle.
    """
    if not inspect.isasyncgenfunction(coro):
        raise AssertionError

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        name = threading.current_thread().name
        inner = coro(*args, **kwargs)

        def run_from(runner: Callable[[Coroutine], Any]):
            while True:
                try:
                    yield runner(inner.__anext__())  # pylint: disable=unnecessary-dunder-call
                except StopAsyncIteration:
                    break

        try:
            # If a loop is currently running in this thread,
            # use a task runner.
            asyncio.get_running_loop()
            if name not in _runner_map:
                _runner_map[name] = _TaskRunner()

            yield from run_from(_runner_map[name].run)
        except RuntimeError:
            pass

        # Run the loop for this thread.
        loop = ensure_event_loop()
        yield from run_from(loop.run_until_complete)

    wrapped.__doc__ = coro.__doc__
    return wrapped


def ensure_event_loop(prefer_selector_loop: bool = False) -> asyncio.AbstractEventLoop:
    # Get the loop for this thread, or create a new one.
    loop = _loop.get()
    if loop is not None and not loop.is_closed():
        return loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        if sys.platform == "win32" and prefer_selector_loop:
            loop = asyncio.WindowsSelectorEventLoopPolicy().new_event_loop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _loop.set(loop)
    return loop
