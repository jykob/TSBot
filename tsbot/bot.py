from __future__ import annotations

import asyncio
import logging

from tsbot.connection import TSConnection
from tsbot.plugin import TSPlugin
from tsbot.types_ import TSCommand, TSEvent, TSEventHandler, TSResponse
from tsbot.util import parse_response_error


logger = logging.getLogger(__name__)


class TSBotBase:
    SKIP_WELCOME_MESSAGE: int = 2

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
        self.event_handlers: dict[str, list[TSEventHandler]] = {}
        self.plugins: dict[str, TSPlugin] = {}

        self.connection = TSConnection()

        self.is_connected = asyncio.Event()
        self.is_ready = asyncio.Event()

        self.event_queue: asyncio.Queue[TSEvent] = asyncio.Queue()
        self.background_tasks: list[asyncio.Task[None]] = []

        self.response: asyncio.Future[TSResponse]
        self.response_lock = asyncio.Lock()

    async def _select_server(self):
        await self.is_connected.wait()
        await self.send(f"use {self.server_id}")
        self.is_ready.set()
        await self.event_queue.put(TSEvent(event="ready"))

    async def _register_notifies(self):
        for event in ("server", "textserver", "textchannel", "textprivate"):
            await self.send(f"servernotifyregister event={event}")
        await self.send(f"servernotifyregister event=channel id=0")

    async def _reader_task(self):
        """Task to read messages from the server"""

        async for data in self.connection.read_lines(self.SKIP_WELCOME_MESSAGE):
            pass
        logger.debug("Skipped welcome message")

        self.is_connected.set()

        response_buffer: list[str] = []

        async for data in self.connection.read():
            logger.debug(f"Got data: {data!r}")

            if data.startswith("notify"):
                # TODO Parse data into TSEvent:
                #         - get event name from data
                #         - parse ctx
                await self.event_queue.put(TSEvent(data.removeprefix("notify")))

            elif data.startswith("error"):
                error_id, msg = parse_response_error(data)
                self.response.set_result(TSResponse("".join(response_buffer), error_id, msg))
                response_buffer.clear()

            else:
                response_buffer.append(data)

        self.is_connected.clear()

    async def _handle_events_task(self):
        try:
            while self.is_connected.is_set():
                event = await self.event_queue.get()

                # TODO: Handle events
                #          - fire all the coroutines on given event
                logger.debug(f"Got event: {event}")

                self.event_queue.task_done()

        except asyncio.CancelledError:
            # TODO: handle all the events before cancelling
            while not self.event_queue.empty():
                event = await self.event_queue.get()

                # TODO: insert event handling code here
                # make it run in asyncio.wait_for() for timing out coroutines

                self.event_queue.task_done()

    async def _keep_alive_task(self):
        # TODO: make this smart. if no self.send called for X amount of time, only then send keep-alive
        await self.is_ready.wait()
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

    async def send(self, command: str) -> TSResponse:
        """
        Sends commands to the server, assuring only one of them gets sent at a time
        """
        async with self.response_lock:
            logger.debug(f"Sending command: {command!r}")
            # tell _keep_alive_task that command has been sent
            self._keep_alive_event.set()

            self.response = asyncio.get_running_loop().create_future()
            await self.connection.write(command)
            response: TSResponse = await self.response

            logger.debug(f"Got a response: {response}")

        # TODO: check Response error code, if non-zero, raise msg in exception

        return response

    async def close(self):
        await self.event_queue.put(TSEvent(event="close"))

        for task in self.background_tasks:
            task.cancel()
            await task

        await self.connection.close()

    async def run(self):
        await self.connection.connect(self.username, self.password, self.address, self.port)

        asyncio.create_task(self._reader_task())

        await self._select_server()
        await self._register_notifies()

        self.background_tasks.extend(
            (
                asyncio.create_task(self._keep_alive_task()),
                asyncio.create_task(self._handle_events_task()),
            )
        )

        await self.connection.writer.wait_closed()


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
