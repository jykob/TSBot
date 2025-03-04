from __future__ import annotations

import asyncio
import contextlib
import inspect
from collections.abc import Callable, Iterable, Sequence
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, cast, overload

from typing_extensions import TypeVarTuple, Unpack

from tsbot import (
    commands,
    connection,
    context,
    default_plugins,
    enums,
    events,
    plugin,
    query_builder,
    ratelimiter,
    response,
    tasks,
)

if TYPE_CHECKING:
    from tsbot.commands import CommandHandler, RawCommandHandler
    from tsbot.events import EventHandler, event_types

_Ts = TypeVarTuple("_Ts")

_DEFAULT_PORTS = {"ssh": 10022, "raw": 10011}


class BotInfo(NamedTuple):
    uid: str = ""
    clid: str = ""
    cldbid: str = ""


class TSBot:
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int | None = None,
        *,
        protocol: Literal["ssh", "raw"] = "ssh",
        server_id: int = 1,
        nickname: str | None = None,
        invoker: str = "!",
        connection_retries: int = 3,
        connection_retry_timeout: float = 10,
        ratelimited: bool = False,
        ratelimit_calls: int = 10,
        ratelimit_period: float = 3,
        query_timeout: float = 5,
    ) -> None:
        """
        :param username: Login name of the query account.
        :param password: Generated password for the query account.
        :param address: Address of the TeamSpeak server.
        :param port: Port for the connection.
        :param protocol: Type of the connection.
        :param server_id: Id of the virtual server.
        :param nickname: Display name for the bot client.
        :param invoker: Command indicator.
        :param connection_retries: The amount of connection attempts on each connection.
        :param connection_retry_timeout: The period between each connection attempt in seconds.
        :param ratelimited: If the connection should be ratelimited.
        :param ratelimit_calls: Calls per period.
        :param ratelimit_period: Period interval.
        :param query_timeout: Timeout for each query command in seconds.
        """

        if nickname is not None and not nickname:
            raise TypeError("Bot nickname cannot be empty")

        port = _DEFAULT_PORTS[protocol] if port is None else port

        connection_type = (
            connection.RawConnection(username, password, address, port)
            if protocol == "raw"
            else connection.SSHConnection(username, password, address, port)
        )
        connection_ratelimiter = (
            ratelimiter.RateLimiter(ratelimit_calls, ratelimit_period) if ratelimited else None
        )

        self._connection = connection.TSConnection(
            event_emitter=self.emit_event,
            connection=connection_type,
            server_id=server_id,
            nickname=nickname,
            query_timeout=query_timeout,
            connection_retries=connection_retries,
            connection_retry_interval=connection_retry_timeout,
            ratelimiter=connection_ratelimiter,
        )

        self._task_manager = tasks.TaskManager()
        self._event_manager = events.EventManager()
        self._command_manager = commands.CommandManager(invoker)

        self.plugins: dict[str, plugin.TSPlugin] = {}

        self._bot_info = BotInfo()
        self._closing = asyncio.Event()
        self._init()

    @property
    def uid(self) -> str:
        """Bots UID"""
        return self._bot_info.uid

    @property
    def clid(self) -> str:
        """Bots current client id"""
        return self._bot_info.clid

    @property
    def cldbid(self) -> str:
        """Bots client database id"""
        return self._bot_info.cldbid

    @property
    def connected(self) -> bool:
        """Is the bot currently connected to a server"""
        return self._connection.connected

    def _init(self) -> None:
        self.register_event_handler("connect", self._on_connect)
        self.register_event_handler("textmessage", self._command_manager.handle_command_event)

        self.load_plugin(default_plugins.Help(), default_plugins.KeepAlive())

    def emit(self, event_name: str, ctx: Any | None = None) -> None:
        """
        Creates :class:`~tsbot.events.TSEvent` instance and emits it.

        This event is passed to the event system and all the handlers
        registered for the event are called with the given context.

        :param event_name: Name of the event being emitted.
        :param ctx: Additional context for the event.
        """
        event = events.TSEvent(event=event_name, ctx=ctx)
        self.emit_event(event)

    def emit_event(self, event: events.TSEvent) -> None:
        """
        Emits an event to be handled.

        Given event is passed to the event system and all the handlers
        registered for the event are called with the given context
        defined in the event.

        :param event: Event to be emitted.
        """
        self._event_manager.add_event(event)

    @overload
    def on(
        self, event_type: event_types.BUILTIN_EVENTS
    ) -> Callable[[EventHandler[context.TSCtx]], EventHandler[context.TSCtx]]: ...

    @overload
    def on(
        self, event_type: event_types.BUILTIN_NO_CTX_EVENTS
    ) -> Callable[[EventHandler[None]], EventHandler[None]]: ...

    @overload
    def on(
        self, event_type: event_types.TS_EVENTS
    ) -> Callable[[EventHandler[context.TSCtx]], EventHandler[context.TSCtx]]: ...

    @overload
    def on(self, event_type: str) -> Callable[[EventHandler[Any]], EventHandler[Any]]: ...

    def on(self, event_type: str) -> Callable[[EventHandler[Any]], EventHandler[Any]]:
        """
        Decorator to register event handlers.

        This decorator factory method registers async functions as an event handler.

        When an event is emitted with the `event_type` name, the decorated async function
        is called with the bot instance and the event context.

        :param event_type: Name of the event.
        """

        def event_decorator(func: EventHandler[Any]) -> EventHandler[Any]:
            self.register_event_handler(event_type, func)
            return func

        return event_decorator

    @overload
    def register_event_handler(
        self, event_type: event_types.BUILTIN_EVENTS, handler: EventHandler[context.TSCtx]
    ) -> events.TSEventHandler: ...

    @overload
    def register_event_handler(
        self, event_type: event_types.BUILTIN_NO_CTX_EVENTS, handler: EventHandler[None]
    ) -> events.TSEventHandler: ...

    @overload
    def register_event_handler(
        self, event_type: event_types.TS_EVENTS, handler: EventHandler[context.TSCtx]
    ) -> events.TSEventHandler: ...

    @overload
    def register_event_handler(
        self, event_type: str, handler: EventHandler[Any]
    ) -> events.TSEventHandler: ...

    def register_event_handler(
        self, event_type: str, handler: EventHandler[Any]
    ) -> events.TSEventHandler:
        """
        Register an event handler.

        This method registers async functions as an event handler.

        When an event is emitted with the `event_type` name, the decorated async function
        is called with the bot instance and the event context.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`~tsbot.events.TSEventHandler` created.
        """

        event_handler = events.TSEventHandler(event_type, handler)
        self._event_manager.register_event_handler(event_handler)
        return event_handler

    @overload
    def once(
        self, event_type: event_types.BUILTIN_EVENTS
    ) -> Callable[[EventHandler[context.TSCtx]], EventHandler[context.TSCtx]]: ...

    @overload
    def once(
        self, event_type: event_types.BUILTIN_NO_CTX_EVENTS
    ) -> Callable[[EventHandler[None]], EventHandler[None]]: ...

    @overload
    def once(
        self, event_type: event_types.TS_EVENTS
    ) -> Callable[[EventHandler[context.TSCtx]], EventHandler[context.TSCtx]]: ...

    @overload
    def once(self, event_type: str) -> Callable[[EventHandler[Any]], EventHandler[Any]]: ...

    def once(self, event_type: str) -> Callable[[EventHandler[Any]], EventHandler[Any]]:
        """
        Decorator to register once event handlers.

        This decorator factory method registers async functions as an event handler.

        When an event is emitted with the `event_type` name, the decorated async function
        is called with the bot instance and the event context.

        The registered event handler will be removed after it is ran once.

        :param event_type: Name of the event.
        """

        def once_decorator(func: EventHandler[Any]) -> EventHandler[Any]:
            self.register_once_handler(event_type, func)
            return func

        return once_decorator

    @overload
    def register_once_handler(
        self, event_type: event_types.BUILTIN_EVENTS, handler: EventHandler[context.TSCtx]
    ) -> events.TSEventOnceHandler: ...

    @overload
    def register_once_handler(
        self, event_type: event_types.BUILTIN_NO_CTX_EVENTS, handler: EventHandler[None]
    ) -> events.TSEventOnceHandler: ...

    @overload
    def register_once_handler(
        self, event_type: event_types.TS_EVENTS, handler: EventHandler[context.TSCtx]
    ) -> events.TSEventOnceHandler: ...

    @overload
    def register_once_handler(
        self, event_type: str, handler: EventHandler[Any]
    ) -> events.TSEventOnceHandler: ...

    def register_once_handler(
        self, event_type: str, handler: EventHandler[Any]
    ) -> events.TSEventOnceHandler:
        """
        Register an event handler to be ran once on an event, and remove it afterwards.

        This method registers async functions as an event handler.
        When an event is emitted with the `event_type` name, the decorated async function
        is called with the bot instance and the event context.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`~tsbot.events.TSEventOnceHandler` created.
        """

        event_handler = events.TSEventOnceHandler(event_type, handler, self.remove_event_handler)
        self._event_manager.register_event_handler(event_handler)
        return event_handler

    def remove_event_handler(self, event_handler: events.TSEventHandler) -> None:
        """
        Remove an event handler.

        This method removes an event handler from the event system.

        The `event_handler` argument is an instance of :class:`~tsbot.events.TSEventHandler`
        returned by the :meth:`~tsbot.bot.TSBot.register_event_handler()` and
        :meth:`~tsbot.bot.TSBot.register_once_handler()` methods.

        :param event_handler: Instance of the :class:`~tsbot.events.TSEventHandler` to be removed.
        """

        self._event_manager.remove_event_handler(event_handler)

    @overload
    def command(
        self,
        *command: str,
        help_text: str = "",
        raw: Literal[True],
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> Callable[[RawCommandHandler], RawCommandHandler]: ...

    @overload
    def command(
        self,
        *command: str,
        help_text: str = "",
        raw: Literal[False] = False,
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> Callable[[CommandHandler], CommandHandler]: ...

    def command(
        self,
        *command: str,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> Callable[[CommandHandler], CommandHandler]:
        """
        Decorator to register command handlers.

        This decorator factory method registers async functions as a command handler.

        When invoked in a text channel, the decorated async function
        is called with the bot instance, the `textmessage` event context
        and parsed arguments from the message.

        :param command: Name(s) of the command.
        :param help_text: Text to be displayed when using **!help**.
        :param raw: Skip message parsing and pass the rest of the message as the sole argument.
        :param hidden: Hide this command from **!help**.
        :param checks: List of async functions to be called before the command is executed.
        """

        def command_decorator(func: CommandHandler) -> CommandHandler:
            self.register_command(
                command=command,
                handler=func,
                help_text=help_text,
                raw=raw,  # type: ignore
                hidden=hidden,
                checks=checks,
            )
            return func

        return command_decorator

    @overload
    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: RawCommandHandler,
        *,
        help_text: str = "",
        raw: Literal[True],
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> commands.TSCommand: ...

    @overload
    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: CommandHandler,
        *,
        help_text: str = "",
        raw: Literal[False] = False,
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> commands.TSCommand: ...

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: CommandHandler | RawCommandHandler,
        *,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: Sequence[CommandHandler] = (),
    ) -> commands.TSCommand:
        """
        Register a command.

        This method registers async functions as a command handler.

        When invoked in a text channel, the decorated async function
        is called with the bot instance, the `textmessage` event context
        and parsed arguments from the message.

        :param command: Name(s) of the command.
        :param handler: Async function to be called when invoked.
        :param help_text: Text to be displayed when using **!help**.
        :param raw: Skip message parsing and pass the rest of the message as the sole argument.
        :param hidden: Hide this command from **!help**.
        :param checks: List of async functions to be called before the command is executed.
        :return: The instance of :class:`~tsbot.commands.TSCommand` created.
        """
        if isinstance(command, str):
            command = (command,)

        command_handler = commands.TSCommand(
            commands=command,
            handler=handler,
            help_text=help_text,
            raw=raw,
            hidden=hidden,
            checks=tuple(checks),
        )
        self._command_manager.register_command(command_handler)
        return command_handler

    def remove_command(self, command: commands.TSCommand) -> None:
        """
        Remove a command handler.

        This method removes a command handler from the command system.

        The `command` argument is an instance of :class:`~tsbot.commands.TSCommand`
        returned by the :meth:`~tsbot.bot.TSBot.register_command()` and
        :meth:`~tsbot.bot.TSBot.get_command_handler()` methods.

        :param command: Instance of the :class:`~tsbot.commands.TSCommand` to be removed.
        """
        self._command_manager.remove_command(command)

    def get_command_handler(self, command: str) -> commands.TSCommand | None:
        """
        Get :class:`~tsbot.commands.TSCommand` instance associated with a given `command`

        :param command: Command that invokes :class:`~tsbot.commands.TSCommand`
        :return: :class:`~tsbot.commands.TSCommand` associated with `command` if found.
        """
        return self._command_manager.get_command(command)

    def register_task(
        self,
        handler: tasks.TaskHandler[Unpack[_Ts]],
        *args: Unpack[_Ts],
        name: str | None = None,
    ) -> tasks.TSTask:
        """
        Register a background task.

        This method registers an async functions as a background task.

        Tasks are started as soon as the bots :meth:`~tsbot.bot.TSBot.run()` method is called.
        If the bot is already running, the task is started immediately.

        The handler is called with the bot instance and optional arguments,
        and wrapped with :func:`asyncio.create_task()`.

        Once the handler returns or raises an exception, the task is removed from the task system.

        :param handler: Async function to be called when the task is started.
        :param args: Optional arguments to be passed to the handler.
        :param name: Name of the task.
        :return: Instance of :class:`~tsbot.tasks.TSTask` created.
        """

        task = tasks.TSTask(
            handler=handler,  # type: ignore
            args=args,
            name=name,
        )
        self._task_manager.register_task(self, task)
        return task

    def register_every_task(
        self,
        seconds: float,
        handler: tasks.TaskHandler[Unpack[_Ts]],
        *args: Unpack[_Ts],
        name: str | None = None,
    ) -> tasks.TSTask:
        """
        Register a background task.

        This method works similar to :meth:`~tsbot.bot.TSBot.register_task()`,
        but the handler is called every `seconds` seconds.

        Tasks are started as soon as the bots :meth:`~tsbot.bot.TSBot.run()` method is called.
        If the bot is already running, the task is started immediately.

        The handler is called with the bot instance and optional arguments,

        If the handler raises an exception or the task is cancelled,
        the task is removed from the task system.

        :param seconds: How often the task is executed.
        :param handler: Async function to be called when the task is executed.
        :param args: Optional arguments to be passed to the handler.
        :param name: Name of the task.
        :return: Instance of :class:`~tsbot.tasks.TSTask` created.
        """
        task = tasks.TSTask(
            handler=tasks.every(handler, seconds),  # type: ignore
            args=args,
            name=name,
        )
        self._task_manager.register_task(self, task)
        return task

    def remove_task(self, task: tasks.TSTask) -> None:
        """
        Remove a background task.

        This method removes a background task from the task system.
        If the task is still running, it is cancelled.

        :param task: Instance of the :class:`~tsbot.tasks.TSTask` to be removed.
        """
        self._task_manager.remove_task(task)

    async def send(self, query: query_builder.TSQuery) -> response.TSResponse:
        """
        Send a query to the server.

        This method sends a query to the server and returns the response.

        If the server responds with an error, a :class:`~tsbot.exceptions.TSResponseError` is raised.

        :param query: Instance of :class:`~tsbot.query_builder.TSQuery` to be send to the server.
        :return: Response from the server as a :class:`~tsbot.response.TSResponse` instance.
        """
        return await self._connection.send(query)

    async def send_raw(self, raw_query: str) -> response.TSResponse:
        """
        Send raw commands to the server.

        this method sends a raw query to the server and returns the response.

        If the server responds with an error, a :class:`~tsbot.exceptions.TSResponseError` is raised.

        :param raw_query: Raw query command to be send to the server.
        :return: Response from the server as a :class:`~tsbot.response.TSResponse` instance.
        """
        return await self._connection.send_raw(raw_query)

    async def send_batched(self, queries: Iterable[query_builder.TSQuery]) -> None:
        """
        Send multiple queries to the server.

        This method sends multiple queries to the server without waiting for the response.

        If the server responds with an error, it is ignored.

        :param queries: Iterable of :class:`~tsbot.query_builder.TSQuery` instances to be send to the server.
        """

        await self._connection.send_batched(queries)

    async def send_batched_raw(self, raw_queries: Iterable[str]) -> None:
        """
        Send multiple raw queries to the server.

        This method sends multiple raw queries to the server without waiting for the response.

        If the server responds with an error, it is ignored.

        :param raw_queries: Iterable of raw query commands to be send to the server.
        """

        await self._connection.send_batched_raw(raw_queries)

    def close(self) -> None:
        """
        Close the bot.

        This method closes the bot gracefully.

        - The bot will emit `close` event to notify that it is closing.
        - The bot will cancel all the background tasks and wait until they are finished.
        - The bot will handle all the events still in the queue.
        - If the connection is still open, the bot will send a quit command.
        """

        self._closing.set()

    async def _wait_closed(self) -> None:
        await self._closing.wait()

        self.emit_event(events.TSEvent("close"))
        await self._task_manager.close()
        await self._event_manager.run_till_empty(self)

        if self._connection.connected:
            await self.send_raw("quit")

        self._connection.close()

    async def _on_connect(self, bot: TSBot, ctx: None) -> None:
        await self._update_bot_info()

    async def _update_bot_info(self) -> None:
        """Update useful information about the bot instance"""
        info = await self.send_raw("whoami")

        self._bot_info = BotInfo(
            uid=info["client_unique_identifier"],
            clid=info["client_id"],
            cldbid=info["client_database_id"],
        )

    async def run(self) -> None:
        """
        Run the bot.

        This method starts the bot.
        - Connects the bot to the server.
        - Schedules background tasks.
        - Registers the server to send events to the bot.

        Awaits until the bot is closed or the connection is lost.
        """

        self._closing.clear()
        self._task_manager.start(self)

        self.register_task(self._event_manager.handle_events_task, name="HandleEvents-Task")
        await self._event_manager.await_running()
        self.emit_event(events.TSEvent("run"))

        with contextlib.closing(self), self._connection:
            tasks = [
                asyncio.create_task(self._wait_closed(), name="Bot-Task"),
                asyncio.create_task(self._connection.wait_closed(), name="Connection-Task"),
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for task in pending:
            await task

        for task in done:
            if exception := task.exception():
                raise exception

    def load_plugin(self, *plugins: plugin.TSPlugin) -> None:
        """
        Loads :class:`~tsbot.plugins.TSPlugin` instances into the bot.

        :param plugins: Instances of :class:`~tsbot.plugins.TSPlugin` to be loaded.
        """

        for plugin_to_be_loaded in plugins:
            for _, member in inspect.getmembers(plugin_to_be_loaded):
                if command_kwargs := cast(
                    plugin.CommandKwargs | None, getattr(member, plugin.COMMAND_ATTR, None)
                ):
                    self.register_command(
                        command=command_kwargs["command"],
                        handler=member,
                        help_text=command_kwargs["help_text"],
                        raw=command_kwargs["raw"],  # type: ignore
                        hidden=command_kwargs["hidden"],
                        checks=command_kwargs["checks"],
                    )

                elif event_kwargs := getattr(member, plugin.EVENT_ATTR, None):
                    self.register_event_handler(
                        handler=member, **cast(plugin.EventKwargs, event_kwargs)
                    )

                elif once_kwargs := getattr(member, plugin.ONCE_ATTR, None):
                    self.register_once_handler(
                        handler=member, **cast(plugin.EventKwargs, once_kwargs)
                    )

            self.plugins[plugin_to_be_loaded.__class__.__name__] = plugin_to_be_loaded

    async def respond(self, ctx: context.TSCtx, message: str) -> None:
        """
        Sends a message to the same text channel where the `ctx` was created.

        This method can be used to respond to command invocations.
        The context has to be from a `textmessage` event (eg. command invocation).

        .. code-block:: python

            @bot.command("hello")
            async def greet(bot: TSBot, ctx: TSCtx):
                await bot.respond(ctx, f"Hello, {ctx['invokername']}!")

        :param ctx: Context of the `textmessage` event.
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
        Sends a message to the client that invoked the message.
        The message will be sent to the client with a direct message.

        This method can be used to respond to command invocations.
        The context has to be from a `textmessage` event (eg. command invocation).

        .. code-block:: python

            @bot.command("hello")
            async def greet(bot: TSBot, ctx: TSCtx):
                await bot.respond_to_client(ctx, f"Hello, {ctx['invokername']}!")

        :param ctx: Context of the `textmessage` event.
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
