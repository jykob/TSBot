from __future__ import annotations

import asyncio
import collections
import contextlib
import logging
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING

from tsbot import events, response

if TYPE_CHECKING:
    from tsbot import connection


logger = logging.getLogger(__name__)


class _ReadBuffer:
    def __init__(self, *, maxlen: int | None = None) -> None:
        self._deque: collections.deque[str] = collections.deque(maxlen=maxlen)
        self._getters: collections.deque[asyncio.Future[None]] = collections.deque()

    def _wakeup_getters(self):
        while self._getters:
            getter = self._getters.popleft()
            if not getter.done():
                getter.set_result(None)
                break

    @property
    def empty(self) -> bool:
        return not self._deque

    def clear(self) -> None:
        self._deque.clear()

    async def _wakeup_on_available_item(self) -> None:
        while self.empty:
            getter = asyncio.get_event_loop().create_future()
            self._getters.append(getter)

            try:
                await getter

            except Exception:
                getter.cancel()

                with contextlib.suppress(ValueError):
                    self._getters.remove(getter)

                if not self.empty and not getter.cancelled():
                    self._wakeup_getters()

                raise

    async def pop(self) -> str:
        await self._wakeup_on_available_item()
        return self._deque.popleft()

    def put(self, item: str) -> None:
        self._deque.append(item)
        self._wakeup_getters()


class Reader:
    def __init__(
        self,
        connection: connection.abc.Connection,
        event_emitter: Callable[[events.TSEvent], None],
        ready_to_read: asyncio.Event,
    ) -> None:
        self._connection = connection
        self._ready_to_read = ready_to_read
        self._event_emitter = event_emitter

        self._read_buffer = _ReadBuffer()
        self._reader_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()

        self._reader_task = asyncio.create_task(self._task())

    async def _task(self) -> None:
        async def read_gen() -> AsyncGenerator[str, None]:
            while await self._ready_to_read.wait() and (data := await self._connection.readline()):
                logger.debug("Got data: %r", data)
                yield data.rstrip()

        async for data in read_gen():
            if data.startswith("notify"):
                self._event_emitter(events.TSEvent.from_server_notification(data))
            else:
                self._read_buffer.put(data)

    async def _get_response(self) -> AsyncGenerator[str, None]:
        data = await self._read_buffer.pop()
        yield data

        while not data.startswith("error"):
            data = await self._read_buffer.pop()
            yield data

    async def read_response(self, response_future: asyncio.Future[response.TSResponse]) -> None:
        # TODO: on connection reset, need a way to clear already received data
        response_future.set_result(
            response.TSResponse.from_server_response([line async for line in self._get_response()])
        )
