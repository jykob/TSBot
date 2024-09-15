from __future__ import annotations

import asyncio
import itertools
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from tsbot import context, events, exceptions, query_builder, response

if TYPE_CHECKING:
    from tsbot import bot, connection, ratelimiter


logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(
        self,
        bot: bot.TSBot,
        connection: connection.ConnectionABC,
        *,
        server_id: int = 0,
        nickname: str | None = None,
        connection_retries: int = 3,
        connection_retry_interval: float = 10,
        query_timeout: float = 5,
        ratelimiter: ratelimiter.RateLimiter | None = None,
    ) -> None:
        self._bot = bot

        self._server_id = server_id
        self._nickname = nickname
        self._query_timeout = query_timeout

        self._connection = connection
        self._connection_retries = connection_retries
        self._connection_retry_interval = connection_retry_interval

        self._ratelimiter = ratelimiter

        self._connection_task: asyncio.Task[None] | None = None
        self._connected_event = asyncio.Event()
        self._is_first_connection = True

        self._write_lock = asyncio.Lock()
        self._response: asyncio.Future[response.TSResponse]

        self._closed = False

    async def connect(self) -> None:
        self._connection_task = asyncio.create_task(
            self._connection_handler(), name="Connection-Task"
        )

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._connection.close()

    async def wait_closed(self) -> None:
        if not self._connection_task:
            raise ConnectionError("Trying to wait on uninitialized connection")

        await self._connection_task

    async def _reader(self) -> None:
        async def read_gen() -> AsyncGenerator[str, None]:
            while data := await self._connection.readline():
                logger.debug("Got data: %r", data)
                yield data.rstrip()

        response_buffer: list[str] = []

        async for data in read_gen():
            if data.startswith("notify"):
                self._bot.emit_event(
                    events.TSEvent.from_server_notification(data),
                )

            elif data.startswith("error"):
                response_buffer.append(data)
                self._response.set_result(
                    response.TSResponse.from_server_response(response_buffer),
                )
                response_buffer.clear()

            else:
                response_buffer.append(data)

        logger.debug("Reader done")

    async def _connection_handler(self) -> None:
        """
        Task to handle connection.

        Will try to upkeep connection specified by the config.
        """

        async def connect():
            for attempt in itertools.count(1):
                logger.info(
                    "Attempting to establish connection [%d/%d]",
                    attempt,
                    self._connection_retries,
                )
                try:
                    await self._connection.connect()
                    return

                except Exception as e:
                    logger.warning(
                        "Connection [%d/%d] failed: %s", attempt, self._connection_retries, e
                    )

                if attempt >= self._connection_retries:
                    break

                logger.info(
                    "Trying to establish connection after %ss", self._connection_retry_interval
                )
                await asyncio.sleep(self._connection_retry_interval)

            raise ConnectionAbortedError(
                f"Failed to connect to the server after {self._connection_retries} tries"
            )

        async def select_server():
            """Set current virtual server and sets nickname if specified"""
            select_query = query_builder.TSQuery("use", parameters={"sid": self._server_id})

            if self._nickname is not None:
                select_query = select_query.params(client_nickname=self._nickname)

            await self.send(select_query)

        async def register_notifications():
            """Register server to send events to the bot"""
            notify_query = query_builder.TSQuery("servernotifyregister")

            await self.send(notify_query.params(event="channel", id=0))
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(notify_query.params(event=event))

        while not self._closed:
            await connect()
            await self._connection.validate_header()
            self._connected_event.set()

            asyncio.create_task(self._reader(), name="ConnectionReader-Task")

            await self._connection.authenticate()

            await select_server()
            await register_notifications()

            if not self._is_first_connection:
                self._bot.emit("reconnect")
            self._is_first_connection = False

            self._bot.emit("connect")
            self._bot.emit("ready")  # TODO: deprecated, remove when appropriate

            await self._connection.wait_closed()

            self._connected_event.clear()
            self._bot.emit("disconnect")

    async def send(self, query: query_builder.TSQuery) -> response.TSResponse:
        return await self.send_raw(query.compile())

    async def send_raw(self, raw_query: str) -> response.TSResponse:
        async with self._write_lock:
            await self._connected_event.wait()

            # TODO: if connection fails at this point, retry sending
            #       query when the next connection is established
            self._response = asyncio.Future()

            if self._ratelimiter:
                await self._ratelimiter.wait()

            self._bot.emit_event(events.TSEvent("send", context.TSCtx({"query": raw_query})))
            await self._connection.write(f"{raw_query}\n\r")

            server_response = await asyncio.wait_for(
                asyncio.shield(self._response), self._query_timeout
            )

        if server_response.error_id == 2568:
            raise exceptions.TSResponsePermissionError(
                msg=server_response.msg,
                error_id=server_response.error_id,
                perm_id=int(server_response.last["failed_permid"]),
            )

        if server_response.error_id != 0:
            raise exceptions.TSResponseError(
                msg=server_response.msg,
                error_id=int(server_response.error_id),
            )

        return server_response
