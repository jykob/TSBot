from __future__ import annotations

import contextlib
import logging
import time
import warnings
from collections.abc import AsyncGenerator


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
