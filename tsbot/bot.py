from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tsbot import (
    cache,
    commands,
    connection,
    default_plugins,
    enums,
    events,
    exceptions,
    query_builder,
    ratelimiter,
    response,
)

if TYPE_CHECKING:
    from tsbot import plugin, typealiases

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TSClientInfo:
    client_id: str = field(compare=False)
    database_id: str = field(compare=False)
    login_name: str = field(compare=False)
    nickname: str = field(compare=False)
    unique_identifier: str = field(compare=True)

    @classmethod
    def from_client_info(cls, resp: response.TSResponse):
        return cls(
            client_id=resp.first["client_id"],
            database_id=resp.first["client_database_id"],
            login_name=resp.first["client_login_name"],
            nickname=resp.first["client_nickname"],
            unique_identifier=resp.first["client_unique_identifier"],
        )


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
        self.bot_info: TSClientInfo

        self.plugins: dict[str, plugin.TSPlugin] = {}
        self._background_tasks: set[asyncio.Task[None]] = set()

        self._connection = connection.TSConnection(
            username=username,
            password=password,
            address=address,
            port=port,
        )

        self.event_handler = events.EventHanlder()
        self.command_handler = commands.CommandHandler(invoker)
        self.cache = cache.Cache()

        self.is_ratelimited = ratelimited
        self.ratelimiter = ratelimiter.RateLimiter(max_calls=ratelimit_calls, period=ratelimit_period)

        self._reader_ready_event = asyncio.Event()
        self._closing_event = asyncio.Event()
        self.is_closing = False

        self._response: asyncio.Future[response.TSResponse]
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
                self.emit_event(events.TSEvent.from_server_response(data))

            elif data.startswith("error"):
                response_buffer.append(data)
                resp = response.TSResponse.from_server_response(response_buffer)
                self._response.set_result(resp)
                response_buffer.clear()

            else:
                response_buffer.append(data)

        logger.debug("Reader task done")

    def emit(self, event_name: str, msg: str | None = None, ctx: typealiases.TCtx | None = None) -> None:
        """Builds a TSEvent object and emits it"""
        event = events.TSEvent(event=event_name, msg=msg, ctx=ctx or {})
        self.emit_event(event)

    def emit_event(self, event: events.TSEvent) -> None:
        """Emits an event to be handled"""
        self.event_handler.event_queue.put_nowait(event)

    def on(self, event_type: str) -> events.TSEventHandler:
        """Decorator to register coroutines on events"""

        def event_decorator(func: typealiases.TEventHandler) -> events.TSEventHandler:
            return self.register_event_handler(event_type, func)

        return event_decorator  # type: ignore

    def register_event_handler(self, event_type: str, handler: typealiases.TEventHandler) -> events.TSEventHandler:
        """
        Register Coroutines to be ran on events

        Returns the event handler.
        """

        event_handler = events.TSEventHandler(event_type, handler)
        self.event_handler.register_event_handler(event_handler)
        return event_handler

    def command(
        self,
        *command: str,
        help_text: str | None = None,
        raw: bool = False,
        hidden: bool = False,
    ) -> commands.TSCommand:
        """Decorator to register coroutines on command"""

        def command_decorator(func: typealiases.TCommandHandler) -> commands.TSCommand:
            return self.register_command(command, func, help_text=help_text, raw=raw, hidden=hidden)

        return command_decorator  # type: ignore

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: typealiases.TCommandHandler,
        *,
        help_text: str | None = None,
        raw: bool = False,
        hidden: bool = False,
    ) -> commands.TSCommand:
        """
        Register Coroutines to be ran on specific command

        Returns the command handler.
        """
        if isinstance(command, str):
            command = (command,)

        command_handler = commands.TSCommand(command, handler, help_text=help_text, raw=raw, hidden=hidden)
        self.command_handler.register_command(command_handler)
        return command_handler

    def register_background_task(
        self,
        background_handler: typealiases.TBackgroundTask,
        *,
        name: str | None = None,
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

    async def send(self, query: query_builder.TSQuery, *, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Sends queries to the server, assuring only one of them gets sent at a time

        Because theres no way to distinguish between requests/responses,
        queries have to be sent to the server one at a time.
        """
        try:
            return await self.send_raw(query.compile(), max_cache_age=max_cache_age)
        except exceptions.TSResponseError as response_error:
            if (tb := sys.exc_info()[2]) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def send_raw(self, command: str, *, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Sends raw commands to the server.

        Its recommended to use builtin query builder and :func:`send()<tsbot.TSBot.send()>` instead of this
        """
        try:
            return await asyncio.shield(self._send(command, max_cache_age))
        except exceptions.TSResponseError as response_error:
            if (tb := sys.exc_info()[2]) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def _send(self, command: str, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Method responsibe for actually sending the data
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
            self.emit(event_name="send", ctx={"command": command})
            await self._connection.write(command)

            response: response.TSResponse = await asyncio.wait_for(asyncio.shield(self._response), 5.0)

            logger.debug("Got a response: %s", response)

        if response.error_id != 0:
            raise exceptions.TSResponseError(f"{response.msg}", error_id=int(response.error_id))

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
            self.event_handler.run_till_empty(self)

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
            await self.send(query_builder.TSQuery("use").params(sid=self.server_id))

        async def register_notifies() -> None:
            """Coroutine to register server to send events to the bot"""

            await self.send(query_builder.TSQuery("servernotifyregister").params(event="channel", id=0))
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(query_builder.TSQuery("servernotifyregister").params(event=event))

        self.register_background_task(self.event_handler.handle_events_task, name="HandleEvents-Task")
        self.register_background_task(self.cache.cache_cleanup_task, name="CacheCleanup-Task")
        self.register_event_handler("textmessage", self.command_handler.handle_command_event)

        self.load_plugin(default_plugins.Help(), default_plugins.KeepAlive())
        self.emit(event_name="run")

        logger.info("Setting up connection")

        async with self._connection:
            reader_task = asyncio.create_task(self._reader_task())
            await self._reader_ready_event.wait()
            logger.info("Connected")

            await select_server()
            await self.update_info()
            await register_notifies()

            self.emit(event_name="ready")
            await reader_task

    def load_plugin(self, *plugins: plugin.TSPlugin) -> None:
        """
        Loads TSPlugin instances into the bot instance

        If TSEventHandler and TSCommand are in a plugin instance, they need to know about it.
        This method sets the plugin instance on these objects.
        """

        for plugin in plugins:
            for member in plugin.__class__.__dict__.values():
                if isinstance(member, events.TSEventHandler):
                    member.plugin_instance = plugin
                    self.event_handler.register_event_handler(member)

                elif isinstance(member, commands.TSCommand):
                    member.plugin_instance = plugin
                    self.command_handler.register_command(member)

            self.plugins[plugin.__class__.__name__] = plugin

    async def update_info(self):
        """Update the bot_info instance"""
        resp = await self.send_raw("whoami")
        self.bot_info = TSClientInfo.from_client_info(resp)

    async def respond(self, ctx: typealiases.TCtx, message: str, *, in_dms: bool = False):
        """
        Respond in text channel

        Will respond in same text channel where 'ctx' was made, unless 'in_dms' flag given.
        """
        target = "0"
        target_mode = enums.TextMessageTargetMode(int(ctx["targetmode"]))

        if in_dms or target_mode == enums.TextMessageTargetMode.CLIENT:
            target, target_mode = ctx["invokerid"], enums.TextMessageTargetMode.CLIENT

        await self.send(
            query_builder.TSQuery("sendtextmessage").params(targetmode=target_mode.value, target=target, msg=message)
        )
