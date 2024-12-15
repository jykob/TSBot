from __future__ import annotations

import asyncio
import contextlib
import functools
import logging
import time
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@contextlib.asynccontextmanager
async def time_coroutine(
    logger: logging.LoggerAdapter[logging.Logger], level: int, message: str
) -> AsyncGenerator[None, None]:
    if logger.isEnabledFor(level):
        start = time.monotonic()
        try:
            yield
        finally:
            logger.log(level, message, time.monotonic() - start)
    else:
        yield


@contextlib.contextmanager
def set_event(event: asyncio.Event) -> Generator[None, None, None]:
    event.set()
    try:
        yield
    finally:
        event.clear()


def async_run_once(
    func: Callable[P, Coroutine[None, None, R]],
) -> Callable[P, Coroutine[None, None, R | None]]:
    has_run = False

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        nonlocal has_run
        if has_run:
            return None

        has_run = True
        return await func(*args, **kwargs)

    return wrapper
