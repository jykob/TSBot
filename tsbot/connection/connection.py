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

        self._server_id = server_id
        self._nickname = nickname

        self._connection = connection
        self._connection_retries = connection_retries
        self._connection_retry_interval = connection_retry_interval

        self._connection_task: asyncio.Task[None] | None = None
        self._connected_event = asyncio.Event()
        self._is_first_connection = True

        self._reader = reader.Reader(
            self._connection,
            event_emitter=self._handle_event,
            ready_to_read=self._connected_event,
        )
        self._writer = writer.Writer(
            self._connection,
            ratelimiter=ratelimiter,
            query_timeout=query_timeout,
            on_send=self._handle_event,
            ready_to_write=self._connected_event,
        )

        self._closed = False

    async def connect(self) -> None:
        self._connection_task = asyncio.create_task(
            self._connection_handler(), name="Connection-Task"
        )

        await self._connected_event.wait()

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._connection.close()

    async def wait_closed(self) -> None:
        if not self._connection_task:
            raise ConnectionError("Trying to wait on uninitialized connection")

        await self._connection_task

    def _handle_event(self, event: events.TSEvent):
        self._bot.emit_event(event)

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
                    break

                except Exception as e:
                    logger.warning(
                        "Connection [%d/%d] failed: %s", attempt, self._connection_retries, e
                    )

                if attempt >= self._connection_retries:
                    raise ConnectionAbortedError(
                        f"Failed to connect to the server after {self._connection_retries} attempts"
                    )

                logger.info(
                    "Trying to establish connection after %ss", self._connection_retry_interval
                )
                await asyncio.sleep(self._connection_retry_interval)

        async def select_server():
            """Set current virtual server and sets nickname if specified"""
            select_query = query_builder.TSQuery("use", parameters={"sid": self._server_id})

            if self._nickname is not None:
                select_query = select_query.params(client_nickname=self._nickname)

            await self.send(select_query, writer.QueryPriority.INTERNAL)

        async def register_notifications():
            """Register server to send events to the bot"""
            notify_query = query_builder.TSQuery("servernotifyregister")

            await self.send(
                notify_query.params(event="channel", id=0), writer.QueryPriority.INTERNAL
            )
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(notify_query.params(event=event), writer.QueryPriority.INTERNAL)

        self._writer.start()

        while not self._closed:
            await connect()
            await self._connection.validate_header()

            self._connected_event.set()
            self._reader.start()

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

    async def send(
        self, query: query_builder.TSQuery, priority: writer.QueryPriority
    ) -> response.TSResponse:
        return await self.send_raw(query.compile(), priority)

    async def send_raw(self, raw_query: str, priority: writer.QueryPriority) -> response.TSResponse:
        server_response = await self._send(raw_query, priority)

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

    async def _send(self, raw_query: str, priority: writer.QueryPriority) -> response.TSResponse:
        response_future: asyncio.Future[response.TSResponse] = asyncio.Future()
        self._writer.write(priority, writer.QueryItem(raw_query, response_future))
        await self._reader.read_response(response_future)
        return await response_future
