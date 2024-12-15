from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from tsbot import logging

if TYPE_CHECKING:
    from tsbot import connection, ratelimiter


logger = logging.get_logger(__name__)


class Writer:
    def __init__(
        self,
        connection: connection.abc.Connection,
        ratelimiter: ratelimiter.RateLimiter | None,
        ready_to_write: asyncio.Event,
        on_send: Callable[[str], None],
    ) -> None:
        self._connection = connection

        self._on_send = on_send

        self._ratelimiter = ratelimiter
        self._ready_to_write = ready_to_write

    async def write(self, raw_query: str) -> None:
        await self._ready_to_write.wait()

        if self._ratelimiter:
            await self._ratelimiter.wait()

        logger.debug("Sending data: %r", raw_query)
        await self._connection.write(raw_query)
        self._on_send(raw_query)
