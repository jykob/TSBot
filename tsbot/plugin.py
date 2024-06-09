from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    ParamSpec,
    TypeVar,
)

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
        kwargs = {
            "command": command,
            "help_text": help_text,
            "raw": raw,
            "hidden": hidden,
            "checks": checks or [],
        }
        setattr(func, "__ts_command__", kwargs)
        return func

    return command_decorator


def on(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]:
    """Decorator to register plugin events"""

    def event_decorator(
        func: Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
    ) -> Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]:
        setattr(func, "__ts_event__", {"event_type": event_type})
        return func

    return event_decorator


def once(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]:
    """Decorator to register plugin events to be ran only once"""

    def once_decorator(
        func: Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
    ) -> Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]:
        setattr(func, "__ts_once__", {"event_type": event_type})
        return func

    return once_decorator
