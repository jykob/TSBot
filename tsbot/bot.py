from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec

from tsbot import (
    commands,
    connection,
    context,
    default_plugins,
    enums,
    events,
    exceptions,
    query_builder,
    ratelimiter,
    response,
    tasks,
    utils,
)

if TYPE_CHECKING:
    from tsbot import plugin

_P = ParamSpec("_P")


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
        nickname: str | None = None,
        invoker: str = "!",
        ratelimited: bool = False,
        ratelimit_calls: int = 10,
        ratelimit_period: float = 3,
        query_timeout: float = 5,
    ) -> None:
        """
        :param username: Login name of the query account.
        :param password: Generated password for the query account.
        :param address: Address of the TeamSpeak server.
        :param port: Port of the SSH connection.
        :param server_id: Id of the virtual server.
        :param nickname: Display name for the bot client.
        :param invoker: Command indicator.
        :param ratelimited: If the connection should be ratelimited.
        :param ratelimit_calls: Calls per period.
        :param ratelimit_period: Period interval.
        :param query_timeout: Timeout for query commands.
        """

        if nickname is not None and not nickname:
            raise TypeError("Bot nickname cannot be empty")

        self.nickname = nickname
        self.server_id = server_id
        self.uid: str = ""

        self.plugins: dict[str, plugin.TSPlugin] = {}

        self._connection = connection.TSConnection(username, password, address, port)

        self._tasks_handler = tasks.TasksHandler()
        self._event_handler = events.EventHandler()
        self._command_handler = commands.CommandHandler(invoker)

        self._ratelimited = ratelimited
        self._ratelimiter = ratelimiter.RateLimiter(
            max_calls=ratelimit_calls, period=ratelimit_period
        )

        self._closing = False

        self._response: asyncio.Future[response.TSResponse]
        self._sending_lock = asyncio.Lock()
        self._query_timeout = query_timeout

    def emit(self, event_name: str, ctx: Any | None = None) -> None:
        """
        Creates :class:`TSevent<tsbot.events.TSEvent>` instance and emits it.

        :param event_name: Name of the event being emitted.
        :param ctx: Additional context for the event.
        """
        event = events.TSEvent(event=event_name, ctx=ctx)
        self.emit_event(event)

    def emit_event(self, event: events.TSEvent) -> None:
        """
        Emits an event to be handled.

        :param event: Event to be emitted.
        """
        self._event_handler.add_event(event)

    def on(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]:
        """
        Decorator to register event handlers.

        :param event_type: Name of the event.
        """

        def event_decorator(func: events.TEventHandler) -> events.TEventHandler:
            self.register_event_handler(event_type, func)
            return func

        return event_decorator

    def register_event_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventHandler:
        """
        Register an event handler to be ran on an event.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`TSEventHandler<tsbot.events.TSEventHandler>` created.
        """

        event_handler = events.TSEventHandler(event_type, handler)
        self._event_handler.register_event_handler(event_handler)
        return event_handler

    def once(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]:
        """
        Decorator to register once handler.

        :param event_type: Name of the event.
        """

        def once_decorator(func: events.TEventHandler) -> events.TEventHandler:
            self.register_once_handler(event_type, func)
            return func

        return once_decorator

    def register_once_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventOnceHandler:
        """
        Register an event handler to be ran once on an event.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`TSEventOnceHandler<tsbot.events.TSEventOnceHandler>` created.
        """

        event_handler = events.TSEventOnceHandler(event_type, handler, self._event_handler)
        self._event_handler.register_event_handler(event_handler)
        return event_handler

    def remove_event_handler(self, event_handler: events.TSEventHandler) -> None:
        """
        Remove event handler from the event system.

        :param event_handler: Instance of the :class:`TSEventHandler<tsbot.events.TSEventHandler>` to be removed.
        """

        self._event_handler.remove_event_handler(event_handler)

    def command(
        self,
        *command: str,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
    ) -> Callable[
        [Callable[Concatenate[TSBot, context.TSCtx, _P], Coroutine[None, None, None]]],
        Callable[Concatenate[TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
    ]:
        """
        Decorator to register command handlers.

        :param command: Name(s) of the command.
        :param help_text: Text to be displayed when using **!help**.
        :param raw: Skip message parsing and pass the rest of the message as the sole argument.
        :param hidden: Hide this command from **!help**.
        :param checks: List of async functions to be called before the command is executed.
        """

        def command_decorator(
            func: Callable[Concatenate[TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
        ) -> Callable[Concatenate[TSBot, context.TSCtx, _P], Coroutine[None, None, None]]:
            self.register_command(
                command, func, help_text=help_text, raw=raw, hidden=hidden, checks=checks
            )
            return func

        return command_decorator

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: Callable[Concatenate[TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
        *,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
    ) -> commands.TSCommand:
        """
        Register command handler to be ran on specific command.

        :param command: Name(s) of the command.
        :param handler: Async function to be called when invoked.
        :param help_text: Text to be displayed when using **!help**.
        :param raw: Skip message parsing and pass the rest of the message as the sole argument.
        :param hidden: Hide this command from **!help**.
        :param checks: List of async functions to be called before the command is executed.
        :return: The instance of :class:`TSCommand<tsbot.commands.TSCommand>` created.
        """
        if isinstance(command, str):
            command = (command,)

        command_handler = commands.TSCommand(command, handler, help_text, raw, hidden, checks or [])
        self._command_handler.register_command(command_handler)
        return command_handler

    def remove_command(self, command: commands.TSCommand) -> None:
        """
        Remove command handler from the command system.

        :param command: Instance of the :class:`TSCommand<tsbot.commands.TSCommand>` to be removed.
        """
        self._command_handler.remove_command(command)

    def get_command_handler(self, command: str) -> commands.TSCommand | None:
        """
        Get :class:`TSCommand<tsbot.commands.TSCommand>` instance associated with a given `str`

        :param command: Command that invokes :class:`TSCommand<tsbot.commands.TSCommand>`
        :return: :class:`TSCommand<tsbot.commands.TSCommand>` associated with `command`
        """
        return self._command_handler.commands.get(command)

    def register_every_task(
        self,
        seconds: float,
        handler: tasks.TTaskHandler,
        *,
        name: str | None = None,
    ) -> tasks.TSTask:
        """
        Register task handler to be ran every given second.

        :param seconds: How often the task is executed.
        :param handler: Async function to be called when the task is executed.
        :param name: Name of the task.
        :return: Instance of :class:`TSTask<tsbot.tasks.TSTask>` created.
        """
        task = tasks.TSTask(handler=tasks.every(handler, seconds), name=name)
        self._tasks_handler.register_task(self, task)
        return task

    def register_task(
        self,
        handler: tasks.TTaskHandler,
        *,
        name: str | None = None,
    ) -> tasks.TSTask:
        """
        Register task handler as a background task.

        :param handler: Async function to be called when the task is executed.
        :param name: Name of the task.
        :return: Instance of :class:`TSTask<tsbot.tasks.TSTask>` created.
        """

        task = tasks.TSTask(handler=handler, name=name)
        self._tasks_handler.register_task(self, task)
        return task

    def remove_task(self, task: tasks.TSTask) -> None:
        """
        Remove a background task from tasks.

        :param task: Instance of the :class:`TSTask<tsbot.tasks.TSTask>` to be removed.
        """
        self._tasks_handler.remove_task(task)

    async def send(self, query: query_builder.TSQuery) -> response.TSResponse:
        """
        Sends queries to the server, assuring only one of them gets sent at a time.

        :param query: Instance of :class:`TSQuery<tsbot.query_builder.TSQuery>` to be send to the server.
        :return: Response from the server.
        """
        try:
            return await self.send_raw(query.compile())
        except exceptions.TSResponseError as response_error:
            raise utils.pop_traceback(response_error, 2)

    async def send_raw(self, raw_query: str) -> response.TSResponse:
        """
        Sends raw commands to the server.

        Its recommended to use built-in query builder and
        :func:`send()<tsbot.TSBot.send()>` method instead.

        :param raw_query: Raw query command to be send to the server.
        :return: Response from the server.
        """
        try:
            return await asyncio.shield(self._send(raw_query))
        except exceptions.TSResponseError as response_error:
            raise utils.pop_traceback(response_error, 2)

    async def _send(self, raw_query: str) -> response.TSResponse:
        """Method responsible for actually sending the data."""

        async with self._sending_lock:
            self._response = asyncio.Future()

            if self._ratelimited:
                await self._ratelimiter.wait()

            logger.debug("Sending query: %r", raw_query)
            self.emit(event_name="send", ctx={"query": raw_query})
            await self._connection.write(raw_query)

            server_response = await asyncio.wait_for(
                asyncio.shield(self._response), self._query_timeout
            )

            logger.debug("Got a response: %s", server_response)

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

    async def _reader_task(self, ready_event: asyncio.Event) -> None:
        """Task to read messages from the server."""

        WELCOME_MESSAGE_LENGTH = 2
        async for data in self._connection.read_lines(WELCOME_MESSAGE_LENGTH):
            pass

        logger.debug("Skipped welcome message")
        ready_event.set()

        response_buffer: list[str] = []

        async for data in self._connection.read():
            if data.startswith("notify"):
                self.emit_event(events.TSEvent.from_server_notification(data))

            elif data.startswith("error"):
                response_buffer.append(data)
                resp = response.TSResponse.from_server_response(response_buffer)
                self._response.set_result(resp)
                response_buffer.clear()

            else:
                response_buffer.append(data)

        logger.debug("Reader task done")

    def close(self) -> None:
        """
        Method to close the bot.

        Emits `close` event to notify that the client is closing,
        cancels background tasks and send quit command.
        """

        if not self._closing:
            self._closing = True
            asyncio.create_task(self._close())

    async def _close(self) -> None:
        logger.info("Closing bot")
        self.emit(event_name="close")
        await self._tasks_handler.close()
        await self._event_handler.run_till_empty(self)

        with contextlib.suppress(Exception):
            await self.send_raw("quit")

        logger.info("Closing done")

    async def run(self) -> None:
        """
        Run the bot.

        Connects to the server, registers the server to send events
        to the bot and schedules background tasks.

        Awaits until the bot disconnects.
        """

        async def get_reader_task() -> asyncio.Task[None]:
            reader_ready = asyncio.Event()
            reader = asyncio.create_task(self._reader_task(reader_ready))
            await reader_ready.wait()

            return reader

        async def select_server() -> None:
            """Set current virtual server and sets nickname if specified"""
            select_query = query_builder.TSQuery("use", parameters={"sid": self.server_id})

            if self.nickname is not None:
                select_query = select_query.params(client_nickname=self.nickname)

            await self.send(select_query)

        async def register_notifies() -> None:
            """Coroutine to register server to send events to the bot"""

            notify_query = query_builder.TSQuery("servernotifyregister")

            await self.send(notify_query.params(event="channel", id=0))
            for event in ("server", "textserver", "textchannel", "textprivate"):
                await self.send(notify_query.params(event=event))

        async def update_uid() -> None:
            """Gets the uid of the client"""
            resp = await self.send_raw("whoami")
            self.uid = resp.first["client_unique_identifier"]

        self.register_task(self._event_handler.handle_events_task, name="HandleEvents-Task")
        self.register_event_handler("textmessage", self._command_handler.handle_command_event)
        self.load_plugin(default_plugins.Help(), default_plugins.KeepAlive())

        self._tasks_handler.start(self)
        self.emit(event_name="run")

        logger.info("Setting up connection")

        try:
            await self._connection.connect()
            reader_task = await get_reader_task()

            logger.info("Connected")

            await select_server()
            await update_uid()
            await register_notifies()

            self.emit(event_name="ready")

            await reader_task

        finally:
            await self._close()
            await self._connection.close()

    def load_plugin(self, *plugins: plugin.TSPlugin) -> None:
        """
        Loads :class:`TSPlugin<tsbot.plugins.TSPlugin>` instances into the bot.

        :param plugins: Instances of :class:`TSPlugin<tsbot.plugins.TSPlugin>`
        """

        for plugin_to_be_loaded in plugins:
            for _, member in inspect.getmembers(plugin_to_be_loaded):
                if command_kwargs := getattr(member, "__ts_command__", None):
                    self.register_command(handler=member, **command_kwargs)

                elif event_kwargs := getattr(member, "__ts_event__", None):
                    self.register_event_handler(handler=member, **event_kwargs)

                elif once_kwargs := getattr(member, "__ts_once__", None):
                    self.register_once_handler(handler=member, **once_kwargs)

            self.plugins[plugin_to_be_loaded.__class__.__name__] = plugin_to_be_loaded

    async def respond(self, ctx: context.TSCtx, message: str) -> None:
        """
        Responds in the same text channel where 'ctx' was created.

        :param ctx: Context where it was called.
        :param message: Message to be sent.
        """
        target_mode = enums.TextMessageTargetMode(ctx["targetmode"])
        target = ctx["invokerid"] if target_mode == enums.TextMessageTargetMode.CLIENT else "0"

        await self.send(
            query_builder.TSQuery(
                "sendtextmessage",
                parameters={"targetmode": target_mode.value, "target": target, "msg": message},
            )
        )

    async def respond_to_client(self, ctx: context.TSCtx, message: str) -> None:
        """
        Responds to a client with a direct message.

        :param ctx: Context where it was called.
        :param message: Message to be sent.
        """

        if target := ctx.get("invokerid"):
            await self.send(
                query_builder.TSQuery(
                    "sendtextmessage",
                    parameters={
                        "targetmode": enums.TextMessageTargetMode.CLIENT.value,
                        "target": target,
                        "msg": message,
                    },
                )
            )
