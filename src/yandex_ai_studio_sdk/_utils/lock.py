from __future__ import annotations

import asyncio


class LazyLock:
    def __init__(self) -> None:
        self._inst: asyncio.Lock | None = None

    def __call__(self) -> asyncio.Lock:
        # NB: MUST BE CALLED INSIDE OF THE EVENT LOOP

        # Here is a big catch. We have two SDK: async and sync. Sync SDK is based on
        # the async one with some synchronization logic (look at .utils.sync module)
        # and it will run new event loop at separate thread with a first call of any
        # synchronized methods.

        # Also we need an async lock for our business logic: for authorization, for example.
        # But we can't just create this asyncio.Lock at any constructors,
        # because there may be no running event loop.
        # And in python3.9- lock instantiation outside any loop context will create new, unbound loop,
        # different from the loop we are using for synchronization.

        # We can't just create a lock in a constructor context, because there may be no event loop at all.
        # So we are postpone lock creating until it first usage in a client.
        # AFAIU because it all happens in one event loop, there should be no race on lazy lock creation.

        if self._inst is None:
            self._inst = asyncio.Lock()

        return self._inst
