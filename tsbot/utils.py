from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import warnings
from collections.abc import AsyncGenerator, Generator


def check_for_deprecated_event(event_type: str) -> None:
    if event_type == "ready":
        warnings.warn(
            "'ready' event is deprecated. Use 'connect' instead",
            DeprecationWarning,
            stacklevel=3,
        )


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
