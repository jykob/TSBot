from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Coroutine

from tsbot import enums
from tsbot.connection import TSConnection
from tsbot.exceptions import TSResponseError
from tsbot.extensions.commands import CommandHandler, TSCommand
from tsbot.extensions.events import EventHanlder, TSEvent, TSEventHandler
from tsbot.extensions.keepalive import KeepAlive
from tsbot.extensions.self import Self
from tsbot.query import TSQuery
from tsbot.response import TSResponse

if TYPE_CHECKING:
    from tsbot.extensions.commands import T_CommandHandler
    from tsbot.extensions.events import T_EventHandler
    from tsbot.plugin import TSPlugin


logger = logging.getLogger(__name__)


class TSBot:
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
        self.server_id = server_id

        self.plugins: dict[str, TSPlugin] = {}

        self._connection = TSConnection(
            username=username,
            password=password,
            address=address,
            port=port,
        )
        self._event_handler = EventHanlder(self)
        self._command_handler = CommandHandler(self, invoker=invoker)
        self._keep_alive = KeepAlive(self)
        self.self = Self(self)

        self._reader_ready_event = asyncio.Event()

        self._background_tasks: list[asyncio.Task[None]] = []

        self._response: asyncio.Future[TSResponse]
        self._response_lock = asyncio.Lock()

    async def _select_server(self) -> None:
        """Set current virtual server"""
        await self.send(TSQuery("use").params(sid=self.server_id))

    async def _register_notifies(self) -> None:
        """Coroutine to register server to send events to the bot"""

        await self.send(TSQuery("servernotifyregister").params(event="channel", id=0))
        for event in ("server", "textserver", "textchannel", "textprivate"):
            await self.send(TSQuery("servernotifyregister").params(event=event))

    async def _reader_task(self) -> None:
        """Task to read messages from the server"""

        async for data in self._connection.read_lines(self.SKIP_WELCOME_MESSAGE):
            pass
        logger.debug("Skipped welcome message")

        self._reader_ready_event.set()

        response_buffer: list[str] = []

        async for data in self._connection.read():
            logger.debug(f"Got data: %r", data)

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

    def emit(self, event: TSEvent) -> None:
        """Emits an event to be handled"""
        self._event_handler.event_queue.put_nowait(event)

    def on(self, event_type: str) -> TSEventHandler:
        """Decorator to register coroutines on events"""

        def event_decorator(func: T_EventHandler) -> TSEventHandler:
            return self.register_event_handler(event_type, func)

        return event_decorator  # type: ignore

    def register_event_handler(self, event_type: str, handler: T_EventHandler) -> TSEventHandler:
        """
        Register Coroutines to be ran on events

        Returns the event handler.
        """

        event_handler = TSEventHandler(event_type, handler)
        self._event_handler.register_event_handler(event_handler)
        return event_handler

    def command(self, *commands: str) -> TSCommand:
        """Decorator to register coroutines on command"""

        def command_decorator(func: T_CommandHandler) -> TSCommand:
            return self.register_command(commands, func)

        return command_decorator  # type: ignore

    def register_command(self, commands: tuple[str, ...], handler: T_CommandHandler) -> TSCommand:
        """
        Register Coroutines to be ran on specific command

        Returns the command handler.
        """
        command_handler = TSCommand(commands, handler)
        self._command_handler.register_command(command_handler)
        return command_handler

    def register_background_task(
        self, background_handler: Callable[..., Coroutine[None, None, None]], name: str | None = None
    ):
        """Registers a coroutine as background task"""
        self._background_tasks.append(asyncio.create_task(background_handler(), name=name))
        logger.debug("Registered %r as a background task", background_handler.__qualname__)

    async def send(self, query: TSQuery):
        """
        Sends queries to the server, assuring only one of them gets sent at a time

        Because theres no way to distinguish between requests/responses,
        queries have to be sent to the server one at a time.
        """
        return await self.send_raw(query.compile())

    async def send_raw(self, command: str) -> TSResponse:
        """
        Send raw commands to the server

        Not recommended to use this if you don't know what you are doing.
        Use send() method instead.
        """
        return await asyncio.shield(self._send(command))

    async def _send(self, command: str) -> TSResponse:
        """
        Method responsibe for actually sending the data

        This method should't be ever cancalled!
        """
        async with self._response_lock:
            logger.debug(f"Sending command: %s", command)
            # tell _keep_alive that command has been sent
            self._keep_alive.command_sent_event.set()

            self._response = asyncio.Future()
            await self._connection.write(command)
            response: TSResponse = await self._response

            logger.debug(f"Got a response: %s", response)

        if response.error_id != 0:
            raise TSResponseError(f"{response.msg}", error_id=int(response.error_id))

        return response

    async def close(self) -> None:
        """
        Coroutine to handle closing the bot

        Will emit TSEvent(event="close") to notify client closing, cancel background tasks
        and wait for the connection to be closed.
        """
        if not self._connection.writer or self._connection.writer.is_closing():
            return

        logger.info("Closing")
        self.emit(TSEvent(event="close"))

        for task in self._background_tasks:
            task.cancel()
            await task

        await self._connection.close()
        logger.info("Connection closed")

    async def run(self) -> None:
        """
        Run the bot.

        Connects to the server, registers the server to send events to the bot and schedules
        background tasks.

        Awaits until the bot disconnects.
        """
        logger.info("Setting up connection")
        await self._connection.connect()

        reader = asyncio.create_task(self._reader_task())

        await self._reader_ready_event.wait()
        logger.info("Connected")

        await self._select_server()
        await self._register_notifies()

        for extension in (self._event_handler, self._command_handler, self._keep_alive, self.self):
            await extension.run()

        self.emit(TSEvent(event="ready"))

        await reader

    def load_plugin(self, *plugins: TSPlugin) -> None:
        """
        Loads all the events and commands from plugin into bot instance

        If TSEventHandler and TSCommand are in a plugin instance, they need to know about it.
        This method sets the plugin instance on these objects.
        """

        for plugin in plugins:
            for member in plugin.__class__.__dict__.values():
                if isinstance(member, TSEventHandler):
                    member.plugin_instance = plugin
                    self._event_handler.register_event_handler(member)

                elif isinstance(member, TSCommand):
                    member.plugin_instance = plugin
                    self._command_handler.register_command(member)

            self.plugins[plugin.__class__.__name__] = plugin

    async def respond(self, ctx: dict[str, str], message: str, in_dms: bool = False):
        """
        Respond in text channel

        Will respond in same text channel where 'ctx' was made, unless 'in_dms' flag given.
        """
        target = 0
        target_mode = enums.TextMessageTargetMode(int(ctx["targetmode"]))

        if in_dms or target_mode == enums.TextMessageTargetMode.CLIENT:
            target, target_mode = ctx["invokerid"], enums.TextMessageTargetMode.CLIENT

        await self.send(TSQuery("sendtextmessage").params(targetmode=target_mode.value, target=target, msg=message))
