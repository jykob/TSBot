from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import IntEnum, auto
from typing import TYPE_CHECKING, NamedTuple

from tsbot import connection, context, events

if TYPE_CHECKING:
    from tsbot import ratelimiter, response


class QueryPriority(IntEnum):
    INTERNAL = auto()
    REDO = auto()
    NORMAL = auto()


class QueryItem(NamedTuple):
    raw_query: str
    response: asyncio.Future[response.TSResponse]


class Writer:
    def __init__(
        self,
        connection: connection.abc.Connection,
        ratelimiter: ratelimiter.RateLimiter | None,
        query_timeout: float,
        ready_to_write: asyncio.Event,
        on_send: Callable[[events.TSEvent], None],
    ) -> None:
        self._connection = connection

        self._on_send = on_send

        self._ratelimiter = ratelimiter
        self._ready_to_write = ready_to_write

        self._query_timeout = query_timeout
        self._query_queue: asyncio.PriorityQueue[tuple[QueryPriority, QueryItem]] = (
            asyncio.PriorityQueue()
        )

    def start(self) -> None:
        self._writer_task = asyncio.create_task(self._task())

    async def _task(self) -> None:
        while True:
            _, query = await self._query_queue.get()
            await self._ready_to_write.wait()

            if self._ratelimiter:
                await self._ratelimiter.wait()

            self._on_send(events.TSEvent("send", context.TSCtx({"query": query.raw_query})))

            # TODO: Can fail, no connection. try-catch-redo
            await self._connection.write(f"{query.raw_query}\n\r")

            try:
                await asyncio.wait_for(asyncio.shield(query.response), self._query_timeout)

                # TODO: handle disconnect situation (redo)
            except Exception as e:
                if not query.response.done():
                    query.response.set_exception(e)

            self._query_queue.task_done()

    def write(self, priority: QueryPriority, item: QueryItem):
        self._query_queue.put_nowait((priority, item))
