from __future__ import annotations

from collections.abc import Callable, Coroutine, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypedDict,
    TypeVar,
    overload,
)

from typing_extensions import deprecated

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot, context
    from tsbot.commands import CommandHandler
    from tsbot.events import event_types

TP = TypeVar("TP", bound="TSPlugin", contravariant=True)
TC = TypeVar("TC", contravariant=True)


class PluginEventHandler(Protocol[TP, TC]):
    def __call__(self, inst: TP, bot: bot.TSBot, ctx: TC, /) -> Coroutine[None, None, None]: ...


class PluginRawCommandHandler(Protocol[TP]):
    def __call__(
        self, inst: TP, bot: bot.TSBot, ctx: context.TSCtx, arg: str, /
    ) -> Coroutine[None, None, None]: ...


class PluginCommandHandler(Protocol[TP]):
    def __call__(
        self,
        inst: TP,
        bot: bot.TSBot,
        ctx: context.TSCtx,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Coroutine[None, None, None]: ...


class CommandKwargs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: list[Callable[..., Coroutine[None, None, None]]]


class EventKwargs(TypedDict):
    event_type: str


COMMAND_ATTR = "__ts_command__"
EVENT_ATTR = "__ts_event__"
ONCE_ATTR = "__ts_once__"


class TSPlugin:
    """Base class for plugins"""


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
) -> Callable[
    [Callable[Concatenate[_TP, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]]],
    Callable[Concatenate[_TP, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
]:
    """Decorator to register plugin commands"""

    def command_decorator(
        func: Callable[Concatenate[_TP, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
    ) -> Callable[Concatenate[_TP, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]]:
        setattr(
            func,
            COMMAND_ATTR,
            CommandKwargs(
                command=command,
                help_text=help_text,
                raw=raw,
                hidden=hidden,
                checks=checks or [],
            ),
        )
        return func

    return command_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def on(
    event_type: Literal["ready"],
) -> Callable[[PluginEventHandler[_TP, None]], PluginEventHandler[_TP, None]]: ...


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
    """Decorator to register plugin events"""

    utils.check_for_deprecated_event(event_type)

    def event_decorator(func: PluginEventHandler[_TP, Any]) -> PluginEventHandler[_TP, Any]:
        setattr(func, EVENT_ATTR, EventKwargs(event_type=event_type))
        return func

    return event_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def once(
    event_type: Literal["ready"],
) -> Callable[[PluginEventHandler[_TP, None]], PluginEventHandler[_TP, None]]: ...


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
    """Decorator to register plugin events to be ran only once"""

    utils.check_for_deprecated_event(event_type)

    def once_decorator(func: PluginEventHandler[_TP, Any]) -> PluginEventHandler[_TP, Any]:
        setattr(func, ONCE_ATTR, EventKwargs(event_type=event_type))
        return func

    return once_decorator
