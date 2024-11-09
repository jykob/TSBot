from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Concatenate, Literal, ParamSpec, Protocol, TypeVar, overload

from typing_extensions import deprecated

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot, context

_TP = TypeVar("_TP", bound="TSPlugin", contravariant=True)
_TC = TypeVar("_TC", contravariant=True)
_P = ParamSpec("_P")


class TPluginEventHandler(Protocol[_TP]):
    def __call__(self, inst: _TP, bot: bot.TSBot, ctx: Any, /) -> Coroutine[None, None, None]: ...


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
            "__ts_command__",
            {
                "command": command,
                "help_text": help_text,
                "raw": raw,
                "hidden": hidden,
                "checks": checks or [],
            },
        )
        return func

    return command_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def on(
    event_type: Literal["ready"],
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]: ...


@overload
def on(
    event_type: str,
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]: ...


def on(
    event_type: str,
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]:
    """Decorator to register plugin events"""

    utils.check_for_deprecated_event(event_type)

    def event_decorator(func: TPluginEventHandler[_TP]) -> TPluginEventHandler[_TP]:
        setattr(func, "__ts_event__", {"event_type": event_type})
        return func

    return event_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def once(
    event_type: Literal["ready"],
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]: ...


@overload
def once(
    event_type: str,
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]: ...


def once(
    event_type: str,
) -> Callable[[TPluginEventHandler[_TP]], TPluginEventHandler[_TP]]:
    """Decorator to register plugin events to be ran only once"""

    utils.check_for_deprecated_event(event_type)

    def once_decorator(func: TPluginEventHandler[_TP]) -> TPluginEventHandler[_TP]:
        setattr(func, "__ts_once__", {"event_type": event_type})
        return func

    return once_decorator
