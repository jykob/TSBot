from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncGenerator, Generator


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
