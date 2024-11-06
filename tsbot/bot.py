from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, ParamSpec, cast, overload

from typing_extensions import deprecated

from tsbot import (
    commands,
    connection,
    context,
    default_plugins,
    enums,
    events,
    query_builder,
    ratelimiter,
    response,
    tasks,
    utils,
)

if TYPE_CHECKING:
    from tsbot import plugin

_P = ParamSpec("_P")


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
        :param port: Port of the SSH connection.
        :param protocol: Type of connection to be used.
        :param server_id: Id of the virtual server.
        :param nickname: Display name for the bot client.
        :param invoker: Command indicator.
        :param connection_retries: The amount of attempts on each connection.
        :param connection_retry_timeout: The period between each connection attempt.
        :param ratelimited: If the connection should be ratelimited.
        :param ratelimit_calls: Calls per period.
        :param ratelimit_period: Period interval.
        :param query_timeout: Timeout for query commands.
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
            bot=self,
            connection=connection_type,
            server_id=server_id,
            nickname=nickname,
            query_timeout=query_timeout,
            connection_retries=connection_retries,
            connection_retry_interval=connection_retry_timeout,
            ratelimiter=connection_ratelimiter,
        )

        self._tasks_handler = tasks.TasksHandler()
        self._event_handler = events.EventHandler()
        self._command_handler = commands.CommandHandler(invoker)

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
        self.register_event_handler("textmessage", self._command_handler.handle_command_event)

        self.load_plugin(default_plugins.Help(), default_plugins.KeepAlive())

    def __enter__(self) -> Coroutine[None, None, None]:
        self._closing.clear()
        self._tasks_handler.start(self)

        self.register_task(self._event_handler.handle_events_task, name="HandleEvents-Task")
        self.emit(event_name="run")

        return self._wait_closed()

    def __exit__(self, *exc: Any) -> None:
        self.close()

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

    @overload
    @deprecated("'ready' event is deprecated. Use 'connect' instead")
    def on(
        self, event_type: Literal["ready"]
    ) -> Callable[[events.TEventHandler], events.TEventHandler]: ...

    @overload
    def on(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]: ...

    def on(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]:
        """
        Decorator to register event handlers.

        :param event_type: Name of the event.
        """

        utils.check_for_deprecated_event(event_type)

        def event_decorator(func: events.TEventHandler) -> events.TEventHandler:
            self.register_event_handler(event_type, func)
            return func

        return event_decorator

    @overload
    @deprecated("'ready' event is deprecated. Use 'connect' instead")
    def register_event_handler(
        self, event_type: Literal["ready"], handler: events.TEventHandler
    ) -> events.TSEventHandler: ...

    @overload
    def register_event_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventHandler: ...

    def register_event_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventHandler:
        """
        Register an event handler to be ran on an event.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`TSEventHandler<tsbot.events.TSEventHandler>` created.
        """

        utils.check_for_deprecated_event(event_type)

        event_handler = events.TSEventHandler(event_type, handler)
        self._event_handler.register_event_handler(event_handler)
        return event_handler

    @overload
    @deprecated("'ready' event is deprecated. Use 'connect' instead")
    def once(
        self, event_type: Literal["ready"]
    ) -> Callable[[events.TEventHandler], events.TEventHandler]: ...

    @overload
    def once(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]: ...

    def once(self, event_type: str) -> Callable[[events.TEventHandler], events.TEventHandler]:
        """
        Decorator to register once handler.

        :param event_type: Name of the event.
        """

        utils.check_for_deprecated_event(event_type)

        def once_decorator(func: events.TEventHandler) -> events.TEventHandler:
            self.register_once_handler(event_type, func)
            return func

        return once_decorator

    @overload
    @deprecated("'ready' event is deprecated. Use 'connect' instead")
    def register_once_handler(
        self, event_type: Literal["ready"], handler: events.TEventHandler
    ) -> events.TSEventOnceHandler: ...

    @overload
    def register_once_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventOnceHandler: ...

    def register_once_handler(
        self, event_type: str, handler: events.TEventHandler
    ) -> events.TSEventOnceHandler:
        """
        Register an event handler to be ran once on an event.

        :param event_type: Name of the event.
        :param handler: Async function to handle the event.
        :return: The instance of :class:`TSEventOnceHandler<tsbot.events.TSEventOnceHandler>` created.
        """

        utils.check_for_deprecated_event(event_type)

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
        checks: Sequence[commands.TCommandHandler[_P]] | None = None,
    ) -> Callable[[commands.TCommandHandler[_P]], commands.TCommandHandler[_P]]:
        """
        Decorator to register command handlers.

        :param command: Name(s) of the command.
        :param help_text: Text to be displayed when using **!help**.
        :param raw: Skip message parsing and pass the rest of the message as the sole argument.
        :param hidden: Hide this command from **!help**.
        :param checks: List of async functions to be called before the command is executed.
        """

        def command_decorator(func: commands.TCommandHandler[_P]) -> commands.TCommandHandler[_P]:
            self.register_command(
                command,
                func,
                help_text=help_text,
                raw=raw,
                hidden=hidden,
                checks=checks,
            )
            return func

        return command_decorator

    def register_command(
        self,
        command: str | tuple[str, ...],
        handler: commands.TCommandHandler[_P],
        *,
        help_text: str = "",
        raw: bool = False,
        hidden: bool = False,
        checks: Sequence[commands.TCommandHandler[_P]] | None = None,
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

        command_handler = commands.TSCommand(
            command,
            handler,
            help_text,
            raw,
            hidden,
            tuple(checks) if checks is not None else (),
        )
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
        return self._command_handler.get_command(command)

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
        return await self._connection.send(query)

    async def send_raw(self, raw_query: str) -> response.TSResponse:
        """
        Sends raw commands to the server.

        Its recommended to use built-in query builder and
        :func:`send()<tsbot.TSBot.send()>` method instead.

        :param raw_query: Raw query command to be send to the server.
        :return: Response from the server.
        """
        return await self._connection.send_raw(raw_query)

    def close(self) -> None:
        """
        Method to close the bot.

        Emits `close` event to notify that the client is closing,
        cancels background tasks and send quit command.
        """

        self._closing.set()

    async def _wait_closed(self) -> None:
        await self._closing.wait()

        self.emit(event_name="close")
        await self._tasks_handler.close()
        await self._event_handler.run_till_empty(self)

        if self._connection.connected:
            await self.send_raw("quit")

        self._connection.close()

    async def _on_connect(self, bot: TSBot, ctx: None) -> None:
        await self._update_bot_info()

    async def _update_bot_info(self) -> None:
        """Update useful information about the bot instance"""
        info = (await self.send_raw("whoami")).first

        self._bot_info = BotInfo(
            uid=info["client_unique_identifier"],
            clid=info["client_id"],
            cldbid=info["client_database_id"],
        )

    async def run(self) -> None:
        """
        Run the bot.

        Connects to the server, registers the server to send events
        to the bot and schedules background tasks.

        Awaits until the bot disconnects.
        """

        with self as self_wait, self._connection as connection_wait:
            tasks = list(map(asyncio.create_task, (self_wait, connection_wait)))
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for task in pending:
            await task

        for task in done:
            if exception := task.exception():
                raise exception

    def load_plugin(self, *plugins: plugin.TSPlugin) -> None:
        """
        Loads :class:`TSPlugin<tsbot.plugins.TSPlugin>` instances into the bot.

        :param plugins: Instances of :class:`TSPlugin<tsbot.plugins.TSPlugin>`
        """

        for plugin_to_be_loaded in plugins:
            for _, member in inspect.getmembers(plugin_to_be_loaded):
                if command_kwargs := getattr(member, plugin.COMMAND_ATTR, None):
                    self.register_command(
                        handler=member, **cast(plugin.TCommandKwargs, command_kwargs)
                    )

                elif event_kwargs := getattr(member, plugin.EVENT_ATTR, None):
                    self.register_event_handler(
                        handler=member, **cast(plugin.TEventKwargs, event_kwargs)
                    )

                elif once_kwargs := getattr(member, plugin.ONCE_ATTR, None):
                    self.register_once_handler(
                        handler=member, **cast(plugin.TEventKwargs, once_kwargs)
                    )

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
