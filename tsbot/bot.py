from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from typing import TYPE_CHECKING, Callable, Concatenate, Coroutine, ParamSpec, TypeVar, overload

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
    tasks,
)

if TYPE_CHECKING:
    from tsbot import plugin

    T = TypeVar("T")
    P = ParamSpec("P")


logger = logging.getLogger(__name__)


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
        self.uid: str = ""

        self.plugins: dict[str, plugin.TSPlugin] = {}

        self._connection = connection.TSConnection(username, password, address, port)

        self.tasks_handler = tasks.TasksHandler()
        self.event_handler = events.EventHanlder()
        self.command_handler = commands.CommandHandler(invoker)
        self.cache = cache.Cache()

        self.is_ratelimited = ratelimited
        self.ratelimiter = ratelimiter.RateLimiter(max_calls=ratelimit_calls, period=ratelimit_period)

        self.is_closing = False

        self._response: asyncio.Future[response.TSResponse]
        self._sending_lock = asyncio.Lock()

    def emit(self, event_name: str, ctx: dict[str, str] | None = None) -> None:
        """Builds a TSEvent object and emits it"""
        event = events.TSEvent(event=event_name, ctx=ctx or {})
        self.emit_event(event)

    def emit_event(self, event: events.TSEvent) -> None:
        """Emits an event to be handled"""
        self.event_handler.event_queue.put_nowait(event)

    def on(self, event_type: str) -> Callable[[events.TEventH], events.TEventH]:
        """Decorator to register coroutines on events"""

        def event_decorator(func: events.TEventH) -> events.TEventH:
            self.register_event_handler(event_type, func)
            return func

        return event_decorator

    def once(self, event_type: str) -> Callable[[events.TEventH], events.TEventH]:
        """Decorator to register once handler"""

        def once_decorator(func: events.TEventH) -> events.TEventH:
            self.register_once_handler(event_type, func)
            return func

        return once_decorator

    def register_once_handler(self, event_type: str, handler: events.TEventH) -> events.TSEventOnceHandler:
        """Register a Coroutine to be ran exactly once on an event"""

        event_handler = events.TSEventOnceHandler(event_type, handler, self.event_handler)
        self.event_handler.register_event_handler(event_handler)
        return event_handler

    def register_event_handler(self, event_type: str, handler: events.TEventH) -> events.TSEventHandler:
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
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
    ) -> Callable[
        [Callable[Concatenate[TSBot, dict[str, str], P], Coroutine[None, None, None]]],
        Callable[Concatenate[TSBot, dict[str, str], P], Coroutine[None, None, None]],
    ]:
        """Decorator to register coroutines on commands"""

        def command_decorator(
            func: Callable[Concatenate[TSBot, dict[str, str], P], Coroutine[None, None, None]]
        ) -> Callable[Concatenate[TSBot, dict[str, str], P], Coroutine[None, None, None]]:
            self.register_command(command, func, help_text=help_text, raw=raw, hidden=hidden, checks=checks)
            return func

        return command_decorator

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: Callable[Concatenate[TSBot, dict[str, str], P], Coroutine[None, None, None]],
        *,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
    ) -> commands.TSCommand:
        """
        Register Coroutines to be ran on specific command

        Returns the command handler.
        """
        if isinstance(command, str):
            command = (command,)

        command_handler = commands.TSCommand(command, handler, help_text, raw, hidden, checks or [])
        self.command_handler.register_command(command_handler)
        return command_handler

    def every(self, seconds: int, name: str | None = None) -> Callable[[tasks.TTaskH], tasks.TTaskH]:
        """Decorator to register coroutine to be ran every given second"""

        def every_decorator(func: tasks.TTaskH) -> tasks.TTaskH:
            self.register_every_task(seconds, func, name=name)
            return func

        return every_decorator

    def register_every_task(
        self,
        seconds: int,
        handler: tasks.TTaskH,
        *,
        name: str | None = None,
    ) -> tasks.TSTask:

        task = tasks.TSTask(handler=tasks.every(handler, seconds), name=name)
        self.tasks_handler.register_task(self, task)
        return task

    @overload
    def task(self, *, name: str | None) -> Callable[[tasks.TTaskH], tasks.TTaskH]:
        ...

    @overload
    def task(self, func: tasks.TTaskH) -> tasks.TTaskH:
        ...

    def task(
        self, func: tasks.TTaskH | None = None, *, name: str | None = None
    ) -> tasks.TTaskH | Callable[[tasks.TTaskH], tasks.TTaskH]:
        """Decorator to register tasks"""

        def task_decorator(func: tasks.TTaskH) -> tasks.TTaskH:
            self.register_task(func, name=name)
            return func

        if func is None:
            return task_decorator

        return task_decorator(func)

    def register_task(
        self,
        handler: tasks.TTaskH,
        *,
        name: str | None = None,
    ) -> tasks.TSTask:
        """Registers a coroutine as background task"""

        task = tasks.TSTask(handler=handler, name=name)
        self.tasks_handler.register_task(self, task)
        return task

    def remove_task(self, task: tasks.TSTask) -> None:
        """Remove a background task from tasks"""
        self.tasks_handler.remove_task(task)

    async def send(self, query: query_builder.TSQuery, *, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Sends queries to the server, assuring only one of them gets sent at a time

        Because theres no way to distinguish between requests/responses,
        queries have to be sent to the server one at a time.
        """
        try:
            return await self.send_raw(query.compile(), max_cache_age=max_cache_age)
        except exceptions.TSResponseError as response_error:
            if (tb := response_error.__traceback__) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def send_raw(self, raw_query: str, *, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Sends raw commands to the server.

        Its recommended to use builtin query builder and :func:`send()<tsbot.TSBot.send()>` instead of this
        """
        try:
            return await asyncio.shield(self._send(raw_query, max_cache_age))
        except exceptions.TSResponseError as response_error:
            if (tb := response_error.__traceback__) and tb.tb_next:
                response_error = response_error.with_traceback(tb.tb_next.tb_next)

            raise response_error

    async def _send(self, raw_query: str, max_cache_age: int | float = 0) -> response.TSResponse:
        """
        Method responsibe for actually sending the data
        """

        cache_hash = hash(raw_query)

        if max_cache_age and (cached_response := self.cache.get_cache(cache_hash, max_cache_age)):
            logger.debug(
                "Got cache hit for %r. hash: %s",
                raw_query if len(raw_query) < 50 else f"{raw_query[:50]}...",
                cache_hash,
            )
            return cached_response

        async with self._sending_lock:
            # Check cache again to be sure if previous requests added something to the cache
            if max_cache_age and (cached_response := self.cache.get_cache(cache_hash, max_cache_age)):
                logger.debug(
                    "Got cache hit for %r. hash: %s",
                    raw_query if len(raw_query) < 50 else f"{raw_query[:50]}...",
                    cache_hash,
                )
                return cached_response

            self._response = asyncio.Future()

            if self.is_ratelimited:
                await self.ratelimiter.wait()

            logger.debug("Sending query: %s", raw_query)
            self.emit(event_name="send", ctx={"query": raw_query})
            await self._connection.write(raw_query)

            server_response = await asyncio.wait_for(asyncio.shield(self._response), 2.0)

            logger.debug("Got a response: %s", server_response)

        if server_response.error_id == 2568:
            raise exceptions.TSResponsePermissionsError(
                msg=server_response.msg,
                error_id=server_response.error_id,
                perm_id=int(server_response.last["failed_permid"]),
            )

        if server_response.error_id != 0:
            raise exceptions.TSResponseError(msg=server_response.msg, error_id=int(server_response.error_id))

        if server_response.data:
            self.cache.add_cache(cache_hash, server_response)
            logger.debug(
                "Added %r response to cache. Hash: %s",
                raw_query if len(raw_query) < 50 else f"{raw_query[:50]}...",
                cache_hash,
            )

        return server_response

    async def _reader_task(self, connection: connection.TSConnection, ready_event: asyncio.Event) -> None:
        """Task to read messages from the server"""

        WELCOME_MESSAGE_LENGTH = 2

        async for data in connection.read_lines(WELCOME_MESSAGE_LENGTH):
            pass

        logger.debug("Skipped welcome message")
        ready_event.set()

        response_buffer: list[str] = []

        async for data in connection.read():
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

    async def close(self) -> None:
        """
        Coroutine to handle closing the bot

        Will emit TSEvent(event="close") to notify client closing, cancel background tasks
        and send quit command.
        """

        if self.is_closing:
            return

        self.is_closing = True

        logger.info("Closing")
        self.emit(event_name="close")

        await self.tasks_handler.close()

        with contextlib.suppress(Exception):
            await self.send_raw("quit")

        self.event_handler.run_till_empty(self)
        await self.event_handler.event_queue.join()

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

        async def get_reader_task() -> asyncio.Task[None]:
            reader_ready = asyncio.Event()
            reader = asyncio.create_task(self._reader_task(self._connection, reader_ready))
            await reader_ready.wait()

            return reader

        self.register_task(self.event_handler.handle_events_task, name="HandleEvents-Task")
        self.register_task(self.cache.cache_cleanup_task, name="CacheCleanup-Task")
        self.register_event_handler("textmessage", self.command_handler.handle_command_event)
        self.load_plugin(default_plugins.Help(), default_plugins.KeepAlive())

        self.tasks_handler.start(self)
        self.emit(event_name="run")

        logger.info("Setting up connection")

        try:
            await self._connection.connect()
            reader_task = await get_reader_task()

            logger.info("Connected")

            await select_server()
            await self.update_uid()
            await register_notifies()

            self.emit(event_name="ready")

            await reader_task

        finally:
            await self.close()
            await self._connection.close()

    def load_plugin(self, *plugins: plugin.TSPlugin) -> None:
        """
        Loads TSPlugin instances into the bot instance

        Loops through every instance attribute and checks if its a TSEventHandler or TSCommand.
        If one is found, register them with the bot.

        Will also add a record of the instance in self.plugins dict
        """

        for plugin_to_be_loaded in plugins:
            for _, member in inspect.getmembers(plugin_to_be_loaded):

                if command_kwargs := getattr(member, "__ts_command__", None):
                    self.register_command(handler=member, **command_kwargs)

                elif event_kwargs := getattr(member, "__ts_event__", None):
                    self.register_event_handler(handler=member, **event_kwargs)

                elif once_kwargs := getattr(member, "__ts_once__", None):
                    self.register_once_handler(handler=member, **once_kwargs)

                elif every_kwargs := getattr(member, "__ts_every__", None):
                    self.register_every_task(handler=member, **every_kwargs)

                elif task_kwargs := getattr(member, "__ts_task__", None):
                    self.register_task(handler=member, **task_kwargs)

            self.plugins[plugin_to_be_loaded.__class__.__name__] = plugin_to_be_loaded

    async def update_uid(self) -> None:
        """Update bots uid instance"""
        resp = await self.send_raw("whoami")
        self.uid = resp.first["client_unique_identifier"]

    async def respond(self, ctx: dict[str, str], message: str, *, in_dms: bool = False) -> None:
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
