from __future__ import annotations

import asyncio
import collections
import contextlib
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any

from tsbot import events, logging, response

if TYPE_CHECKING:
    from tsbot import connection


logger = logging.get_logger(__name__)


class _ReadBuffer:
    def __init__(self) -> None:
        self._deque: collections.deque[str] = collections.deque()
        self._getters: collections.deque[asyncio.Future[None]] = collections.deque()

    def _wakeup_getters(self) -> None:
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
            getter = asyncio.get_running_loop().create_future()
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
        read_timeout: float,
        ready_to_read: asyncio.Event,
    ) -> None:
        self._connection = connection
        self._ready_to_read = ready_to_read
        self._event_emitter = event_emitter
        self._read_timeout = read_timeout

        self._read_buffer = _ReadBuffer()
        self._reader_task: asyncio.Task[None] | None = None

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def start(self) -> None:
        self._reader_task = asyncio.create_task(self._task(), name="Reader-Task")

    def close(self) -> None:
        self._read_buffer.clear()

        if self._reader_task:
            self._reader_task.cancel()

        self._reader_task = None

    async def _task(self) -> None:
        async def read_gen() -> AsyncGenerator[str, None]:
            while await self._ready_to_read.wait() and (data := await self._connection.readline()):
                logger.debug("Got data: %r", data)
                yield data.rstrip()

        async with contextlib.aclosing(read_gen()) as g:
            async for data in g:
                if data.startswith("notify"):
                    self._event_emitter(events.TSEvent.from_server_notification(data))
                else:
                    self._read_buffer.put(data)

    async def _pop_till_error_line(self) -> AsyncGenerator[str, None]:
        data = await self._read_buffer.pop()
        yield data

        while not data.startswith("error"):
            data = await self._read_buffer.pop()
            yield data

    async def _get_response(self) -> tuple[str, ...]:
        async with contextlib.aclosing(self._pop_till_error_line()) as g:
            return tuple([line async for line in g])

    async def read_response(self) -> response.TSResponse:
        return response.TSResponse.from_server_response(
            await asyncio.wait_for(self._get_response(), timeout=self._read_timeout)
        )
