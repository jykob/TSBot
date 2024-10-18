from __future__ import annotations

import asyncio
import itertools
import logging
from typing import TYPE_CHECKING

from tsbot import exceptions, query_builder
from tsbot.connection import reader, writer

if TYPE_CHECKING:
    from tsbot import bot, connection, events, ratelimiter, response


logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(
        self,
        bot: bot.TSBot,
        connection: connection.abc.Connection,
        *,
        server_id: int = 0,
        nickname: str | None = None,
        connection_retries: int = 3,
        connection_retry_interval: float = 10,
        query_timeout: float = 5,
        ratelimiter: ratelimiter.RateLimiter | None = None,
    ) -> None:
        self._bot = bot
        self._connection = connection

        self._server_id = server_id
        self._nickname = nickname

        self._retries = max(connection_retries, 1)
        self._retry_interval = connection_retry_interval

        self._connection_task: asyncio.Task[None] | None = None
        self._connected_event = asyncio.Event()
        self._is_first_connection = True

        self._reader = reader.Reader(
            self._connection,
            event_emitter=self._handle_event,
            ready_to_read=self._connected_event,
            read_timeout=query_timeout,
        )

        self._writer = writer.Writer(
            self._connection,
            ratelimiter=ratelimiter,
            on_send=self._handle_event,
            ready_to_write=self._connected_event,
        )

        self._closed = False

    def connect(self) -> None:
        self._connection_task = asyncio.create_task(
            self._connection_handler(), name="Connection-Task"
        )

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._connection.close()

    async def wait_closed(self) -> None:
        if not self._connection_task:
            raise ConnectionError("Trying to wait on uninitialized connection")

        await self._connection_task

    def _handle_event(self, event: events.TSEvent) -> None:
        self._bot.emit_event(event)

    def _on_connection_close(self) -> None:
        self._reader.close()

    async def _connection_handler(self) -> None:
        """
        Task to handle connection.

        Will try to upkeep connection specified by the config.
        """

        async def connect() -> None:
            for attempt in itertools.count(1):
                logger.info(
                    "Attempting to establish connection [%d/%d]",
                    attempt,
                    self._retries,
                )
                try:
                    await self._connection.connect()
                except Exception as e:
                    logger.warning("Connection [%d/%d] failed: %s", attempt, self._retries, e)
                else:
                    break

                if attempt >= self._retries:
                    raise ConnectionRefusedError(
                        f"Failed to connect after {self._retries} attempt"
                        f"{'' if self._retries == 1 else 's'}"
                    )

                logger.info("Trying to establish connection after %ss", self._retry_interval)
                await asyncio.sleep(self._retry_interval)

        async def select_server() -> None:
            """Set current virtual server and sets nickname if specified"""
            select_query = query_builder.TSQuery("use", parameters={"sid": self._server_id})

            if self._nickname is not None:
                select_query = select_query.params(client_nickname=self._nickname)

            await self.send(select_query)

        async def register_notifications() -> None:
            """Register server to send events to the bot"""
            notify_query = query_builder.TSQuery("servernotifyregister")

            await self.send(notify_query.params(event="channel", id=0))
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(notify_query.params(event=event))

        while not self._closed:
            await connect()
            await self._connection.validate_header()
            await self._connection.authenticate()

            self._connected_event.set()
            self._reader.start()

            await select_server()
            await register_notifications()

            if not self._is_first_connection:
                self._bot.emit("reconnect")
            self._is_first_connection = False

            self._bot.emit("connect")
            self._bot.emit("ready")  # TODO: deprecated, remove when appropriate

            await self._connection.wait_closed()

            self._connected_event.clear()
            self._on_connection_close()
            self._bot.emit("disconnect")

    async def send(self, query: query_builder.TSQuery) -> response.TSResponse:
        return await self.send_raw(query.compile())

    async def send_raw(self, raw_query: str) -> response.TSResponse:
        await self._writer.write(raw_query)
        response = await self._reader.read_response()

        if response.error_id == 2568:
            raise exceptions.TSResponsePermissionError(
                msg=response.msg,
                error_id=response.error_id,
                perm_id=int(response.last["failed_permid"]),
            )

        if response.error_id != 0:
            raise exceptions.TSResponseError(
                msg=response.msg,
                error_id=int(response.error_id),
            )

        return response
