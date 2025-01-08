from __future__ import annotations

from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Literal, TypedDict, TypeVar, overload

if TYPE_CHECKING:
    from tsbot import bot, context
    from tsbot.commands import CommandHandler
    from tsbot.events import event_types

_TP = TypeVar("_TP", bound="TSPlugin", contravariant=True)
_TC = TypeVar("_TC", contravariant=True)

PluginEventHandler = Callable[[_TP, "bot.TSBot", _TC], Coroutine[None, None, None]]
PluginRawCommandHandler = Callable[
    [_TP, "bot.TSBot", "context.TSCtx", str], Coroutine[None, None, None]
]
PluginCommandHandler = Callable[..., Coroutine[None, None, None]]

# TODO: Use after 'typing_extensions' releases support for Python 3.10 'Concatenate[...]'
# PluginCommandHandler = Callable[
#     Concatenate[_TP, "bot.TSBot", "context.TSCtx", ...], Coroutine[None, None, None]
# ]


class CommandKwargs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: Sequence[CommandHandler]


class EventKwargs(TypedDict):
    event_type: str


COMMAND_ATTR = "__ts_command__"
EVENT_ATTR = "__ts_event__"
ONCE_ATTR = "__ts_once__"


class TSPlugin:
    """Base class for plugins"""


@overload
def command(
    *command: str,
    help_text: str = "",
    raw: Literal[True],
    hidden: bool = False,
    checks: Sequence[CommandHandler] = (),
) -> Callable[[PluginRawCommandHandler[_TP]], PluginRawCommandHandler[_TP]]: ...


@overload
def command(
    *command: str,
    help_text: str = "",
    raw: Literal[False] = False,
    hidden: bool = False,
    checks: Sequence[CommandHandler] = (),
) -> Callable[[PluginCommandHandler], PluginCommandHandler]: ...


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: Sequence[CommandHandler] = (),
) -> Callable[[PluginCommandHandler], PluginCommandHandler]:
    """
    Decorator to register plugin commands

    :param command: Name(s) of the command.
    :param help_text: Text to be displayed when using **!help**.
    :param raw: Skip message parsing and pass the rest of the message as the sole argument.
    :param hidden: Hide this command from **!help**.
    :param checks: List of async functions to be called before the command is executed.
    """

    def command_decorator(func: PluginCommandHandler) -> PluginCommandHandler:
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
    Decorator to register plugin events

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
    Decorator to register plugin events to be ran only once

    :param event_type: Name of the event.
    """

    def once_decorator(func: PluginEventHandler[_TP, Any]) -> PluginEventHandler[_TP, Any]:
        setattr(func, ONCE_ATTR, EventKwargs(event_type=event_type))
        return func

    return once_decorator
