from __future__ import annotations

from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Literal, TypedDict, TypeVar, overload

from typing_extensions import Concatenate, Self  # noqa: UP035

if TYPE_CHECKING:
    from tsbot import bot, commands, context, events
    from tsbot.events import event_types

_TP = TypeVar("_TP", bound="TSPlugin", contravariant=True)
_TC = TypeVar("_TC", contravariant=True)

PluginEventHandler = Callable[[_TP, "bot.TSBot", _TC], Coroutine[None, None, None]]
PluginRawCommandHandler = Callable[
    [_TP, "bot.TSBot", "context.TSCtx", str], Coroutine[None, None, None]
]
PluginCommandHandler = Callable[
    Concatenate[_TP, "bot.TSBot", "context.TSCtx", ...], Coroutine[None, None, None]
]


class CommandKwargs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: Sequence[commands.CommandHandler]


class EventKwargs(TypedDict):
    event_type: str


COMMAND_ATTR = "__ts_command__"
EVENT_ATTR = "__ts_event__"
ONCE_ATTR = "__ts_once__"


class TSPlugin:
    """Base class for plugins."""

    __ts_event_instances__: list[events.TSEventHandler]
    __ts_command_instances__: list[commands.TSCommand]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        instance = super().__new__(cls)
        instance.__ts_event_instances__ = []
        instance.__ts_command_instances__ = []

        return instance

    def on_load(self, bot: bot.TSBot) -> None:
        """
        Callback called when the plugin is loaded to the bot.

        This method can be overridden and used to do side effects when the plugin is loaded.
        For example, registering event handlers, commands, etc.

        :param bot: Instance of :class:`~tsbot.bot.TSBot` that loaded the plugin.
        """

    def on_unload(self, bot: bot.TSBot) -> None:
        """
        Callback called when the plugin is unloaded from the bot.

        This method can be overridden and used to clean up side effects when the plugin is unloaded.
        For example, removing event handlers, commands, etc.

        :param bot: Instance of :class:`~tsbot.bot.TSBot` that unloaded the plugin.
        """


@overload
def command(
    *command: str,
    help_text: str = "",
    raw: Literal[True],
    hidden: bool = False,
    checks: Sequence[commands.CommandHandler] = (),
) -> Callable[[PluginRawCommandHandler[_TP]], PluginRawCommandHandler[_TP]]: ...


@overload
def command(
    *command: str,
    help_text: str = "",
    raw: Literal[False] = False,
    hidden: bool = False,
    checks: Sequence[commands.CommandHandler] = (),
) -> Callable[[PluginCommandHandler[_TP]], PluginCommandHandler[_TP]]: ...


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: Sequence[commands.CommandHandler] = (),
) -> Callable[[PluginCommandHandler[_TP]], PluginCommandHandler[_TP]]:
    """
    Decorator to register plugin commands.

    :param command: Name(s) of the command.
    :param help_text: Text to be displayed when using **!help**.
    :param raw: Skip message parsing and pass the rest of the message as the sole argument.
    :param hidden: Hide this command from **!help**.
    :param checks: List of async functions to be called before the command is executed.
    """

    def command_decorator(func: PluginCommandHandler[_TP]) -> PluginCommandHandler[_TP]:
        setattr(
            func,
            COMMAND_ATTR,
            CommandKwargs(
                command=command,
                help_text=help_text,
                raw=raw,
                hidden=hidden,
                checks=checks,
            ),
        )
        return func

    return command_decorator


@overload
def on(
    event_type: event_types.BUILTIN_EVENTS,
) -> Callable[[PluginEventHandler[_TP, context.TSCtx]], PluginEventHandler[_TP, context.TSCtx]]: ...


@overload
def on(
    event_type: event_types.BUILTIN_NO_CTX_EVENTS,
) -> Callable[[PluginEventHandler[_TP, None]], PluginEventHandler[_TP, None]]: ...


@overload
def on(
    event_type: event_types.TS_EVENTS,
) -> Callable[[PluginEventHandler[_TP, context.TSCtx]], PluginEventHandler[_TP, context.TSCtx]]: ...


@overload
def on(
    event_type: str,
) -> Callable[[PluginEventHandler[_TP, Any]], PluginEventHandler[_TP, Any]]: ...


def on(
    event_type: str,
) -> Callable[[PluginEventHandler[_TP, Any]], PluginEventHandler[_TP, Any]]:
    """
    Decorator to register plugin events.

    :param event_type: Name of the event.
    """

    def event_decorator(func: PluginEventHandler[_TP, Any]) -> PluginEventHandler[_TP, Any]:
        setattr(func, EVENT_ATTR, EventKwargs(event_type=event_type))
        return func

    return event_decorator


@overload
def once(
    event_type: event_types.BUILTIN_EVENTS,
) -> Callable[[PluginEventHandler[_TP, context.TSCtx]], PluginEventHandler[_TP, context.TSCtx]]: ...


@overload
def once(
    event_type: event_types.BUILTIN_NO_CTX_EVENTS,
) -> Callable[[PluginEventHandler[_TP, None]], PluginEventHandler[_TP, None]]: ...


@overload
def once(
    event_type: event_types.TS_EVENTS,
) -> Callable[[PluginEventHandler[_TP, context.TSCtx]], PluginEventHandler[_TP, context.TSCtx]]: ...


@overload
def once(
    event_type: str,
) -> Callable[[PluginEventHandler[_TP, Any]], PluginEventHandler[_TP, Any]]: ...


def once(
    event_type: str,
) -> Callable[[PluginEventHandler[_TP, Any]], PluginEventHandler[_TP, Any]]:
    """
    Decorator to register plugin events to be ran only once.

    :param event_type: Name of the event.
    """

    def once_decorator(func: PluginEventHandler[_TP, Any]) -> PluginEventHandler[_TP, Any]:
        setattr(func, ONCE_ATTR, EventKwargs(event_type=event_type))
        return func

    return once_decorator
