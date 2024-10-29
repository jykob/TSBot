from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from tsbot import context, events

if TYPE_CHECKING:
    from tsbot import connection, ratelimiter


class Writer:
    def __init__(
        self,
        connection: connection.abc.Connection,
        ratelimiter: ratelimiter.RateLimiter | None,
        ready_to_write: asyncio.Event,
        on_send: Callable[[events.TSEvent], None],
    ) -> None:
        self._connection = connection

        self._on_send = on_send

        self._ratelimiter = ratelimiter
        self._ready_to_write = ready_to_write

    async def write(self, raw_query: str) -> None:
        await self._ready_to_write.wait()

        if self._ratelimiter:
            await self._ratelimiter.wait()

        await self._connection.write(raw_query)
        self._on_send(events.TSEvent("send", context.TSCtx({"query": raw_query})))
