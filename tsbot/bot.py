from __future__ import annotations

import asyncio
import logging

from tsbot.connection import TSConnection
from tsbot.plugin import TSPlugin
from tsbot.types_ import TSCommand, T_CommandHandler, TSResponse
from tsbot.event_handler import EventHanlder, TSEvent, TSEventHandler, T_EventHandler
from tsbot.util import parse_response_error


logger = logging.getLogger(__name__)


class TSBotBase:
    SKIP_WELCOME_MESSAGE: int = 2
    KEEP_ALIVE_INTERVAL: int | float = 240  # 4 minutes

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

        self.invoker = invoker

        self.commands: dict[str, TSCommand] = {}
        self.plugins: dict[str, TSPlugin] = {}

        self.connection = TSConnection(
            username=username,
            password=password,
            address=address,
            port=port,
        )
        self._event_handler = EventHanlder()

        self._reader_ready_event = asyncio.Event()
        self._keep_alive_event = asyncio.Event()

        self._background_tasks: list[asyncio.Task[None]] = []

        self._response: asyncio.Future[TSResponse]
        self._response_lock = asyncio.Lock()

    async def _select_server(self) -> None:
        await self.send(f"use {self.server_id}")
        self.emit(TSEvent(event="ready"))

    async def _register_notifies(self) -> None:
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
                # TODO Parse data into TSEvent:
                #         - get event name from data
                #         - parse ctx
                await self._event_handler.event_queue.put(TSEvent(data.removeprefix("notify").split(" ")[0]))

            elif data.startswith("error"):
                error_id, msg = parse_response_error(data)
                self._response.set_result(TSResponse("".join(response_buffer), error_id, msg))
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
                    await self.send("version")

        except asyncio.CancelledError:
            pass

    def on(self, event_type: str) -> T_EventHandler:
        """
        Decorator to register coroutines on events
        """

        def event_decorator(func: T_EventHandler) -> T_EventHandler:
            self._event_handler.register_event_handler(TSEventHandler(event_type, func))
            return func

        return event_decorator

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
            self._register_command(TSCommand(commands, func))
            return func

        return command_decorator

    def _register_command(self, command: TSCommand):

        # Check if no commands have been registered, register command handler as event handler
        if not self.commands:
            event_handler = TSEventHandler("textmessage", self._handle_command_event)
            self._event_handler.register_event_handler(event_handler)

        for command_name in command.commands:
            self.commands[command_name] = command

        logger.debug(
            f"Registered '{', '.join(command.commands)}' command"
            f"""{f" from '{command.plugin}'" if command.plugin else ''}"""
        )

    async def _handle_command_event(self, event: TSEvent) -> None:
        """
        Logic to handle commands
        """
        # TODO: WRITE

        logger.info("HANDLE COMMAND")

    async def send(self, command: str) -> TSResponse:
        """
        Sends commands to the server, assuring only one of them gets sent at a time
        """
        async with self._response_lock:
            logger.debug(f"Sending command: {command!r}")
            # tell _keep_alive_task that command has been sent
            self._keep_alive_event.set()

            self._response = asyncio.Future()
            await self.connection.write(command)
            response: TSResponse = await self._response

            logger.debug(f"Got a response: {response}")

        # TODO: check Response error code, if non-zero, raise msg in exception

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
