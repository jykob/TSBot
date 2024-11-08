from __future__ import annotations

from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, Protocol, TypedDict, TypeVar, overload

from typing_extensions import deprecated

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot, context
    from tsbot.commands import TCommandHandler


_T = TypeVar("_T", bound="TSPlugin", contravariant=True)
_TC = TypeVar("_TC", contravariant=True)
_P = ParamSpec("_P")


class TPluginCommandHandler(Protocol[_T, _P]):
    def __call__(
        self,
        inst: _T,
        bot: bot.TSBot,
        ctx: context.TSCtx,
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> Coroutine[None, None, None]: ...


class TPluginEventHandler(Protocol[_T, _TC]):
    def __call__(self, inst: _T, bot: bot.TSBot, ctx: _TC, /) -> Coroutine[None, None, None]: ...


COMMAND_ATTR = "__ts_command__"
EVENT_ATTR = "__ts_event__"
ONCE_ATTR = "__ts_once__"


class TSPlugin:
    """Base class for plugins"""


class TCommandKwargs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: tuple[TCommandHandler[...], ...]


class TEventKwargs(TypedDict):
    event_type: str


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: Sequence[TCommandHandler[_P]] = (),
) -> Callable[[TPluginCommandHandler[_T, _P]], TPluginCommandHandler[_T, _P]]:
    """Decorator to register plugin commands"""

    def command_decorator(func: TPluginCommandHandler[_T, _P]) -> TPluginCommandHandler[_T, _P]:
        setattr(
            func,
            COMMAND_ATTR,
            TCommandKwargs(
                command=command,
                help_text=help_text,
                raw=raw,
                hidden=hidden,
                checks=tuple(checks),
            ),
        )
        return func

    return command_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def on(
    event_type: Literal["ready"],
) -> Callable[[TPluginEventHandler[_T, None]], TPluginEventHandler[_T, None]]: ...


@overload
def on(
    event_type: Literal["run", "connect", "disconnect", "reconnect", "close"],
) -> Callable[[TPluginEventHandler[_T, None]], TPluginEventHandler[_T, None]]: ...


@overload
def on(
    event_type: Literal["send", "command_error", "permission_error", "parameter_error"],
) -> Callable[[TPluginEventHandler[_T, context.TSCtx]], TPluginEventHandler[_T, context.TSCtx]]: ...


def on(event_type: str) -> Callable[[TPluginEventHandler[_T, Any]], TPluginEventHandler[_T, Any]]:
    """Decorator to register plugin events"""

    utils.check_for_deprecated_event(event_type)

    def event_decorator(func: TPluginEventHandler[_T, Any]) -> TPluginEventHandler[_T, Any]:
        setattr(func, EVENT_ATTR, TEventKwargs(event_type=event_type))
        return func

    return event_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def once(
    event_type: Literal["ready"],
) -> Callable[[TPluginEventHandler[_T, None]], TPluginEventHandler[_T, None]]: ...


@overload
def once(
    event_type: Literal["run", "connect", "disconnect", "reconnect", "close"],
) -> Callable[[TPluginEventHandler[_T, None]], TPluginEventHandler[_T, None]]: ...


@overload
def once(
    event_type: Literal["send", "command_error", "permission_error", "parameter_error"],
) -> Callable[[TPluginEventHandler[_T, context.TSCtx]], TPluginEventHandler[_T, context.TSCtx]]: ...


def once(event_type: str) -> Callable[[TPluginEventHandler[_T, Any]], TPluginEventHandler[_T, Any]]:
    """Decorator to register plugin events to be ran only once"""

    utils.check_for_deprecated_event(event_type)

    def once_decorator(func: TPluginEventHandler[_T, Any]) -> TPluginEventHandler[_T, Any]:
        setattr(func, ONCE_ATTR, TEventKwargs(event_type=event_type))
        return func

    return once_decorator
