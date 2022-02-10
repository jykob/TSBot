from __future__ import annotations

import asyncio
import logging
from tsbot.command_handler import CommandHandler

from tsbot.connection import TSConnection
from tsbot.plugin import TSPlugin
from tsbot.response import TSResponse
from tsbot.event_handler import EventHanlder, TSEvent, TSEventHandler, T_EventHandler
from tsbot.command_handler import TSCommand, T_CommandHandler


logger = logging.getLogger(__name__)


class TSBotBase:
    SKIP_WELCOME_MESSAGE: int = 2
    KEEP_ALIVE_INTERVAL: int | float = 4 * 60  # 4 minutes
    KEEP_ALIVE_COMMAND: str = "bindinglist"

    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int = 10022,
        server_id: int = 1,
        invoker: str = "!",
    ) -> None:
        self.server_id = server_id

        self.plugins: dict[str, TSPlugin] = {}

        self.connection = TSConnection(
            username=username,
            password=password,
            address=address,
            port=port,
        )
        self._event_handler = EventHanlder(self)
        self._command_handler = CommandHandler(self, invoker=invoker)

        self._reader_ready_event = asyncio.Event()
        self._keep_alive_event = asyncio.Event()

        self._background_tasks: list[asyncio.Task[None]] = []

        self._response: asyncio.Future[TSResponse]
        self._response_lock = asyncio.Lock()

    async def _select_server(self) -> None:
        """
        set current virtual server
        """
        await self.send(f"use {self.server_id}")  # TODO: change static command to TSCommand version
        self.emit(TSEvent(event="ready"))

    async def _register_notifies(self) -> None:
        """
        Coroutine to register server to send events to the bot
        """
        for event in ("server", "textserver", "textchannel", "textprivate"):
            await self.send(f"servernotifyregister event={event}")
        await self.send(f"servernotifyregister event=channel id=0")

    async def _reader_task(self) -> None:
        """Task to read messages from the server"""

        async for data in self.connection.read_lines(self.SKIP_WELCOME_MESSAGE):
            pass
        logger.debug("Skipped welcome message")

        self._reader_ready_event.set()

        response_buffer: list[str] = []

        async for data in self.connection.read():
            logger.debug(f"Got data: {data!r}")

            if data.startswith("notify"):
                event = TSEvent.from_server_response(data)
                await self._event_handler.event_queue.put(event)

            elif data.startswith("error"):
                response_buffer.append(data)
                response = TSResponse.from_server_response(response_buffer)
                self._response.set_result(response)
                response_buffer.clear()

            else:
                response_buffer.append(data)

        self._reader_ready_event.clear()

    async def _keep_alive_task(self) -> None:
        """
        Task to keep connection alive with the TeamSpeak server

        Normally TeamSpeak server cuts the connection to the query client
        after 5 minutes of inactivity. If the bot doesn't send any commands
        to the server, this task a command to keep connection alive.
        """
        logger.debug("Keep-alive task started")

        try:
            while True:
                self._keep_alive_event.clear()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._keep_alive_event.wait()),
                        timeout=self.KEEP_ALIVE_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    await self.send(self.KEEP_ALIVE_COMMAND)

        except asyncio.CancelledError:
            pass

    def on(self, event_type: str) -> T_EventHandler:
        """
        Decorator to register coroutines on events
        """

        def event_decorator(func: T_EventHandler) -> T_EventHandler:
            self.register_event_handler(event_type, func)
            return func

        return event_decorator

    def register_event_handler(self, event_type: str, handler: T_EventHandler) -> None:
        self._event_handler.register_event_handler(TSEventHandler(event_type, handler))

    def emit(self, event: TSEvent) -> None:
        """
        Emits an event to be handled
        """
        self._event_handler.event_queue.put_nowait(event)

    def command(self, *commands: str) -> T_CommandHandler:
        """
        Decorator to register coroutines on command
        """

        def command_decorator(func: T_CommandHandler) -> T_CommandHandler:
            self.register_command(commands, func)
            return func

        return command_decorator

    def register_command(self, commands: tuple[str, ...], handler: T_CommandHandler) -> None:
        self._command_handler.register_command(TSCommand(commands, handler))

    async def send(self, command: str) -> TSResponse:
        """
        Sends commands to the server, assuring only one of them gets sent at a time

        Because theres no way to distinguish between requests/responses,
        you have to send requests to the server one at a time.
        """
        async with self._response_lock:
            logger.debug(f"Sending command: {command!r}")
            # tell _keep_alive_task that command has been sent
            self._keep_alive_event.set()

            self._response = asyncio.Future()
            await self.connection.write(command)
            response: TSResponse = await self._response

            logger.debug(f"Got a response: {response}")

        # TODO: check response error code, if non-zero, raise msg in exception

        return response

    async def close(self) -> None:
        """
        Coroutine to handle closing the bot

        Will emit TSEvent(event="close") to notify client closing, cancel background tasks
        and wait for the connection to be closed
        """
        self.emit(TSEvent(event="close"))

        for task in self._background_tasks:
            task.cancel()
            await task

        await self.connection.close()

    async def run(self) -> None:
        """
        Run the bot.

        Connects to the server, registers the server to send events to the bot and schedules
        background tasks.

        Awaits until the bot disconnects
        """
        await self.connection.connect()

        reader = asyncio.create_task(self._reader_task())
        await self._reader_ready_event.wait()

        await self._select_server()
        await self._register_notifies()

        self._background_tasks.extend(
            (
                asyncio.create_task(self._keep_alive_task(), name="KeepAlive-Task"),
                asyncio.create_task(self._event_handler.handle_events_task(), name="HandleEvent-Task"),
            )
        )

        await reader


class TSBot(TSBotBase):
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int = 10022,
        server_id: int = 1,
        invoker: str = "!",
        owner: str = "",
    ) -> None:
        super().__init__(username, password, address, port, server_id, invoker)
        self.owner = owner
