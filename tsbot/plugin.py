from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Concatenate, Literal, ParamSpec, TypeVar, overload

from typing_extensions import deprecated

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot, context

_T = TypeVar("_T", bound="TSPlugin")
_P = ParamSpec("_P")


class TSPlugin:
    """Base class for plugins"""


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
) -> Callable[
    [Callable[Concatenate[_T, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]]],
    Callable[Concatenate[_T, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
]:
    """Decorator to register plugin commands"""

    def command_decorator(
        func: Callable[Concatenate[_T, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]],
    ) -> Callable[Concatenate[_T, bot.TSBot, context.TSCtx, _P], Coroutine[None, None, None]]:
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
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]: ...


@overload
def on(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]: ...


def on(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]:
    """Decorator to register plugin events"""

    utils.check_for_deprecated_event(event_type)

    def event_decorator(
        func: Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
    ) -> Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]:
        setattr(func, "__ts_event__", {"event_type": event_type})
        return func

    return event_decorator


@overload
@deprecated("'ready' event is deprecated. Use 'connect' instead")
def once(
    event_type: Literal["ready"],
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]: ...


@overload
def once(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]: ...


def once(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]:
    """Decorator to register plugin events to be ran only once"""

    utils.check_for_deprecated_event(event_type)

    def once_decorator(
        func: Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
    ) -> Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]:
        setattr(func, "__ts_once__", {"event_type": event_type})
        return func

    return once_decorator
