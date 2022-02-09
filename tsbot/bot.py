from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from tsbot.connection import TSConnection
from tsbot.plugin import TSPlugin
from tsbot.types_ import TSCommand, TSEvent, TSEventHandler, T_EventHandler, TSResponse
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
        self.username = username
        self.password = password
        self.address = address
        self.port = port
        self.server_id = server_id

        self.invoker = invoker

        self.commands: dict[str, TSCommand] = {}
        self.event_handlers: defaultdict[str, list[TSEventHandler]] = defaultdict(list)
        self.plugins: dict[str, TSPlugin] = {}

        self.connection = TSConnection()

        self._is_connected = asyncio.Event()
        self._keep_alive_event = asyncio.Event()

        self._event_queue: asyncio.Queue[TSEvent] = asyncio.Queue()
        self._background_tasks: list[asyncio.Task[None]] = []

        self._response: asyncio.Future[TSResponse]
        self._response_lock = asyncio.Lock()

    async def _select_server(self):
        await self._is_connected.wait()
        await self.send(f"use {self.server_id}")
        self.emit(TSEvent(event="ready"))

    async def _register_notifies(self):
        for event in ("server", "textserver", "textchannel", "textprivate"):
            await self.send(f"servernotifyregister event={event}")
        await self.send(f"servernotifyregister event=channel id=0")

    async def _reader_task(self):
        """Task to read messages from the server"""

        async for data in self.connection.read_lines(self.SKIP_WELCOME_MESSAGE):
            pass
        logger.debug("Skipped welcome message")

        self._is_connected.set()

        response_buffer: list[str] = []

        async for data in self.connection.read():
            logger.debug(f"Got data: {data!r}")

            if data.startswith("notify"):
                # TODO Parse data into TSEvent:
                #         - get event name from data
                #         - parse ctx
                await self._event_queue.put(TSEvent(data.removeprefix("notify").split(" ")[0]))

            elif data.startswith("error"):
                error_id, msg = parse_response_error(data)
                self._response.set_result(TSResponse("".join(response_buffer), error_id, msg))
                response_buffer.clear()

            else:
                response_buffer.append(data)

        self._is_connected.clear()

    @staticmethod
    async def _run_event_handler(handler: T_EventHandler, event: TSEvent, timeout: int | float | None = None):
        try:
            await asyncio.wait_for(handler(event), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        except Exception:
            logger.exception("Exception happend in event handler")

    def _handle_event(self, event: TSEvent, timeout: int | float | None = None):
        event_handlers = self.event_handlers.get(event.event)

        if not event_handlers:
            return

        for event_handlers in event_handlers:
            asyncio.create_task(self._run_event_handler(event_handlers.handler, event, timeout))

    async def _handle_events_task(self):
        """
        Task to run events put into the self._event_queue

        if task is cancelled, it will try to run all the events
        still in the queue with a timeout
        """

        try:
            while self._is_connected.is_set():
                event = await self._event_queue.get()

                logger.debug(f"Got event: {event}")
                self._handle_event(event)

                self._event_queue.task_done()

        except asyncio.CancelledError:
            while not self._event_queue.empty():
                event = await self._event_queue.get()

                self._handle_event(event, timeout=1.0)

                self._event_queue.task_done()

    async def _keep_alive_task(self):
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

    # TODO: Fix decorator hints
    def on(self, event_type: str) -> T_EventHandler:
        """
        Decorator to register coroutines to fire on specific events
        """

        def event_decorator(func: T_EventHandler) -> T_EventHandler:
            self._register_event_handler(TSEventHandler(event_type, func))
            return func

        return event_decorator

    def emit(self, event: TSEvent):
        """
        Emits an event to be handled
        """
        self._event_queue.put_nowait(event)

    def _register_event_handler(self, event_handler: TSEventHandler):
        """
        Registers event handlers that will be called when given event happens
        """
        self.event_handlers[event_handler.event].append(event_handler)
        logger.debug(
            f"Registered {event_handler.event!r} event to execute {event_handler.handler.__name__}"
            f"""{f" from '{event_handler.plugin}'" if event_handler.plugin else ''}"""
        )

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

    async def close(self):
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

    async def run(self):
        """
        Run the bot.

        Connects to the server, registers the server to send events to the bot and schedules
        background tasks.

        Awaits until the bot disconnects
        """
        await self.connection.connect(self.username, self.password, self.address, self.port)

        reader = asyncio.create_task(self._reader_task())

        await self._select_server()
        await self._register_notifies()

        self._background_tasks.extend(
            (
                asyncio.create_task(self._keep_alive_task()),
                asyncio.create_task(self._handle_events_task()),
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
