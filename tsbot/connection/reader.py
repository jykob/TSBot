from __future__ import annotations

import asyncio
import collections
import contextlib
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any

from tsbot import logging

if TYPE_CHECKING:
    from tsbot import connection


logger = logging.get_logger(__name__)


class _ResponseBuffer:
    def __init__(self) -> None:
        self._deque: collections.deque[tuple[str, ...]] = collections.deque()
        self._getters: collections.deque[asyncio.Future[None]] = collections.deque()

    def _wakeup_getters(self) -> None:
        while self._getters:
            getter = self._getters.popleft()
            if not getter.done():
                getter.set_result(None)
                break

    def __len__(self) -> int:
        return len(self._deque)

    def __bool__(self) -> bool:
        return bool(self._deque)

    def clear(self) -> None:
        self._deque.clear()

    async def discard(self, count: int = 1) -> None:
        for _ in range(count):
            await self.pop()

    async def _wakeup_on_available_item(self) -> None:
        while not self:
            getter = asyncio.get_running_loop().create_future()
            self._getters.append(getter)

            try:
                await getter

            except Exception:
                getter.cancel()

                with contextlib.suppress(ValueError):
                    self._getters.remove(getter)

                if self and not getter.cancelled():
                    self._wakeup_getters()

                raise

    async def pop(self) -> tuple[str, ...]:
        await self._wakeup_on_available_item()
        return self._deque.popleft()

    def put(self, item: tuple[str, ...]) -> None:
        self._deque.append(item)
        self._wakeup_getters()


class Reader:
    def __init__(
        self,
        connection: connection.abc.Connection,
        on_notify: Callable[[str], None],
        read_timeout: float,
        ready_to_read: asyncio.Event,
    ) -> None:
        self._connection = connection
        self._ready_to_read = ready_to_read
        self._on_notify = on_notify
        self._read_timeout = read_timeout

        self._skipped_responses = 0

        self._response_buffer = _ResponseBuffer()
        self._reader_task: asyncio.Task[None] | None = None

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def skip_response(self, count: int = 1) -> None:
        self._skipped_responses += count

    def start(self) -> None:
        self._reader_task = asyncio.create_task(self._task(), name="Reader-Task")

    def close(self) -> None:
        self._response_buffer.clear()

        if self._reader_task:
            self._reader_task.cancel()

        self._reader_task = None

    async def _task(self) -> None:
        async def read_gen() -> AsyncGenerator[str, None]:
            while await self._ready_to_read.wait() and (data := await self._connection.readline()):
                logger.debug("Received data: %r", data)
                yield data.rstrip()

        read_buffer: list[str] = []

        async with contextlib.aclosing(read_gen()) as g:
            async for data in g:
                if data.startswith("notify"):
                    self._on_notify(data)
                    continue

                read_buffer.append(data)

                if data.startswith("error"):
                    self._response_buffer.put(tuple(read_buffer))
                    read_buffer.clear()

    async def _get_response(self) -> tuple[str, ...]:
        return await self._response_buffer.pop()

    async def read_response(self) -> tuple[str, ...]:
        if self._skipped_responses > 0:
            await self._response_buffer.discard(self._skipped_responses)
            self._skipped_responses = 0

        try:
            response = await asyncio.wait_for(self._get_response(), timeout=self._read_timeout)
        except asyncio.TimeoutError:
            self.skip_response()
            raise

        return response
