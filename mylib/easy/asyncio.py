#!/usr/bin/env python3
import sys as _sys
from asyncio import *

__REF = get_event_loop

if _sys.version_info < (3, 9):
    async def to_thread(func, *args, **kwargs):
        """Asynchronously run function *func* in a separate thread.
        Any *args and **kwargs supplied for this function are directly passed
        to *func*. Also, the current :class:`contextvars.Context` is propogated,
        allowing context variables from the main thread to be accessed in the
        separate thread.
        Return a coroutine that can be awaited to get the eventual result of *func*.
        """
        import contextvars
        import functools
        from asyncio import events
        loop = events._get_running_loop()
        ctx = contextvars.copy_context()
        func_call = functools.partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)
