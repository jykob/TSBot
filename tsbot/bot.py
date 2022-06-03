from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tsbot import enums
from tsbot.cache import Cache
from tsbot.commands.handler import CommandHandler
from tsbot.commands.tscommand import TSCommand
from tsbot.connection import TSConnection
from tsbot.default_plugins.help import Help
from tsbot.default_plugins.keepalive import KeepAlive
from tsbot.events.handler import EventHanlder
from tsbot.events.tsevent import TSEvent
from tsbot.events.tsevent_handler import TSEventHandler
from tsbot.exceptions import TSResponseError
from tsbot.query import TSQuery
from tsbot.ratelimiter import RateLimiter
from tsbot.response import TSResponse

if TYPE_CHECKING:
    from tsbot.plugin import TSPlugin
    from tsbot.typealiases import TBackgroundTask, TCommandHandler, TEventHandler

logger = logging.getLogger(__name__)


@dataclass
class TSBotInfo:
    clid: str = field(init=False)
    database_id: str = field(init=False)
    login_name: str = field(init=False)
    nickname: str = field(init=False)
    unique_identifier: str = field(init=False)

    async def update(self, bot: TSBot):
        response = await bot.send_raw("whoami")

        self.clid = response.first["client_id"]
        self.database_id = response.first["client_database_id"]
        self.login_name = response.first["client_login_name"]
        self.nickname = response.first["client_nickname"]
        self.unique_identifier = response.first["client_unique_identifier"]


class TSBot:
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int = 10022,
        *,
        server_id: int = 1,
        invoker: str = "!",
        ratelimited: bool = False,
        ratelimit_calls: int = 10,
        ratelimit_period: float = 3,
    ) -> None:
        self.server_id = server_id

        self.plugins: dict[str, TSPlugin] = {}
        self._background_tasks: set[asyncio.Task[None]] = set()

        self._connection = TSConnection(
            username=username,
            password=password,
            address=address,
            port=port,
        )

        self.event_handler = EventHanlder()
        self.command_handler = CommandHandler(invoker)
        self.cache = Cache()
        self.bot_info = TSBotInfo()

        self.is_ratelimited = ratelimited
        self.ratelimiter = RateLimiter(max_calls=ratelimit_calls, period=ratelimit_period)

        self._reader_ready_event = asyncio.Event()
        self._closing_event = asyncio.Event()
        self.is_closing = False

        self._response: asyncio.Future[TSResponse]
        self._response_lock = asyncio.Lock()

    async def _reader_task(self) -> None:
        """Task to read messages from the server"""

        WELCOME_MESSAGE_LENGTH = 2

        async for data in self._connection.read_lines(WELCOME_MESSAGE_LENGTH):
            pass
        logger.debug("Skipped welcome message")

        self._reader_ready_event.set()

        response_buffer: list[str] = []

        async for data in self._connection.read():
            if data.startswith("notify"):
                self.emit_event(TSEvent.from_server_response(data))

            elif data.startswith("error"):
                response_buffer.append(data)
                response = TSResponse.from_server_response(response_buffer)
                self._response.set_result(response)
                response_buffer.clear()

            else:
                response_buffer.append(data)

        logger.debug("Reader task done")

    def emit(self, event_name: str, msg: str | None = None, ctx: dict[str, str] | None = None) -> None:
        """Builds a TSEvent object and emits it"""
        event = TSEvent(event=event_name, msg=msg, ctx=ctx or {})
        self.emit_event(event)

    def emit_event(self, event: TSEvent) -> None:
        """Emits an event to be handled"""
        self.event_handler.event_queue.put_nowait(event)

    def on(self, event_type: str) -> TSEventHandler:
        """Decorator to register coroutines on events"""

        def event_decorator(func: TEventHandler) -> TSEventHandler:
            return self.register_event_handler(event_type, func)

        return event_decorator  # type: ignore

    def register_event_handler(self, event_type: str, handler: TEventHandler) -> TSEventHandler:
        """
        Register Coroutines to be ran on events

        Returns the event handler.
        """

        event_handler = TSEventHandler(event_type, handler)
        self.event_handler.register_event_handler(event_handler)
        return event_handler

    def command(
        self, *command: str, help_text: str | None = None, raw: bool = False, hidden: bool = False
    ) -> TSCommand:
        """Decorator to register coroutines on command"""

        def command_decorator(func: TCommandHandler) -> TSCommand:
            return self.register_command(command, func, help_text=help_text, raw=raw, hidden=hidden)

        return command_decorator  # type: ignore

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: TCommandHandler,
        *,
        help_text: str | None = None,
        raw: bool = False,
        hidden: bool = False,
    ) -> TSCommand:
        """
        Register Coroutines to be ran on specific command

        Returns the command handler.
        """
        if isinstance(command, str):
            command = (command,)

        command_handler = TSCommand(command, handler, help_text=help_text, raw=raw, hidden=hidden)
        self.command_handler.register_command(command_handler)
        return command_handler

    def register_background_task(
        self, background_handler: TBackgroundTask, *, name: str | None = None
    ) -> asyncio.Task[None]:
        """Registers a coroutine as background task"""
        task = asyncio.create_task(background_handler(self), name=name)
        task.add_done_callback(lambda task: self.remove_background_task(task))

        self._background_tasks.add(task)
        logger.debug("Registered %r as a background task", background_handler.__qualname__)

        return task

    def remove_background_task(self, background_task: asyncio.Task[None]) -> None:
        """Remove a background task from background tasks"""
        if not background_task.done():
            background_task.cancel()

        self._background_tasks.remove(background_task)

    async def send(self, query: TSQuery, *, max_cache_age: int | float = 0) -> TSResponse:
        """
        Sends queries to the server, assuring only one of them gets sent at a time

        Because theres no way to distinguish between requests/responses,
        queries have to be sent to the server one at a time.
        """
        try:
            return await self.send_raw(query.compile(), max_cache_age=max_cache_age)
        except TSResponseError as response_error:
            if (tb := sys.exc_info()[2]) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def send_raw(self, command: str, *, max_cache_age: int | float = 0) -> TSResponse:
        """
        Send raw commands to the server

        Not recommended to use this if you don't know what you are doing.
        Use send() method instead.
        """
        try:
            return await asyncio.shield(self._send(command, max_cache_age))
        except TSResponseError as response_error:
            if (tb := sys.exc_info()[2]) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def _send(self, command: str, max_cache_age: int | float = 0) -> TSResponse:
        """
        Method responsibe for actually sending the data

        This method should't be ever cancalled!
        """

        cache_hash = hash(command)

        if max_cache_age and (cached_response := self.cache.get_cache(cache_hash, max_cache_age)):
            logger.debug(
                "Got cache hit for %r. hash: %s",
                command if len(command) < 50 else f"{command[:50]}...",
                cache_hash,
            )
            return cached_response

        async with self._response_lock:
            # Check cache again to be sure if previous requests added something to the cache
            if max_cache_age and (cached_response := self.cache.get_cache(cache_hash, max_cache_age)):
                logger.debug(
                    "Got cache hit for %r. hash: %s",
                    command if len(command) < 50 else f"{command[:50]}...",
                    cache_hash,
                )
                return cached_response

            self._response = asyncio.Future()

            if self.is_ratelimited:
                await self.ratelimiter.wait()

            logger.debug("Sending command: %s", command)
            self.emit(event_name="send")
            await self._connection.write(command)

            response: TSResponse = await self._response

            logger.debug("Got a response: %s", response)

        if response.error_id != 0:
            raise TSResponseError(f"{response.msg}", error_id=int(response.error_id))

        if response.data:
            self.cache.add_cache(cache_hash, response)
            logger.debug(
                "Added %r response to cache. Hash: %s",
                command if len(command) < 50 else f"{command[:50]}...",
                cache_hash,
            )

        return response

    async def close(self) -> None:
        """
        Coroutine to handle closing the bot

        Will emit TSEvent(event="close") to notify client closing, cancel background tasks
        and send quit command.
        """

        if not self.is_closing:
            self.is_closing = True

            logger.info("Closing")
            self.emit(event_name="close")

            cancelled_tasks = asyncio.gather(*self._background_tasks)

            for task in list(self._background_tasks):
                task.cancel()

            await cancelled_tasks

            await self.send_raw("quit")
            await self.event_handler.run_till_empty(self)

            self._closing_event.set()
            logger.info("Closing done")

    async def run(self) -> None:
        """
        Run the bot.

        Connects to the server, registers the server to send events to the bot and schedules
        background tasks.

        Awaits until the bot disconnects.
        """

        async def select_server() -> None:
            """Set current virtual server"""
            await self.send(TSQuery("use").params(sid=self.server_id))

        async def register_notifies() -> None:
            """Coroutine to register server to send events to the bot"""

            await self.send(TSQuery("servernotifyregister").params(event="channel", id=0))
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(TSQuery("servernotifyregister").params(event=event))

        self.register_background_task(self.event_handler.handle_events_task, name="HandleEvents-Task")
        self.register_background_task(self.cache.cache_cleanup_task, name="CacheCleanup-Task")
        self.register_event_handler("textmessage", self.command_handler.handle_command_event)

        self.load_plugin(Help(), KeepAlive())
        self.emit(event_name="run")

        try:
            logger.info("Setting up connection")
            await self._connection.connect()

            reader_task = asyncio.create_task(self._reader_task())
            await self._reader_ready_event.wait()
            logger.info("Connected")

            await select_server()
            await register_notifies()
            await self.bot_info.update(self)

            self.emit(event_name="ready")
            await reader_task

        finally:
            await self._connection.close()

    def load_plugin(self, *plugins: TSPlugin) -> None:
        """
        Loads TSPlugin instances into the bot instance

        If TSEventHandler and TSCommand are in a plugin instance, they need to know about it.
        This method sets the plugin instance on these objects.
        """

        for plugin in plugins:
            for member in plugin.__class__.__dict__.values():
                if isinstance(member, TSEventHandler):
                    member.plugin_instance = plugin
                    self.event_handler.register_event_handler(member)

                elif isinstance(member, TSCommand):
                    member.plugin_instance = plugin
                    self.command_handler.register_command(member)

            self.plugins[plugin.__class__.__name__] = plugin

    async def respond(self, ctx: dict[str, str], message: str, *, in_dms: bool = False):
        """
        Respond in text channel

        Will respond in same text channel where 'ctx' was made, unless 'in_dms' flag given.
        """
        target = 0
        target_mode = enums.TextMessageTargetMode(int(ctx["targetmode"]))

        if in_dms or target_mode == enums.TextMessageTargetMode.CLIENT:
            target, target_mode = ctx["invokerid"], enums.TextMessageTargetMode.CLIENT

        await self.send(TSQuery("sendtextmessage").params(targetmode=target_mode.value, target=target, msg=message))
