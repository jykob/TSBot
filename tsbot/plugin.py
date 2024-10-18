from __future__ import annotations

import warnings
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


def on(
    event_type: str,
) -> Callable[
    [Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]],
    Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
]:
    """Decorator to register plugin events"""

    if event_type == "ready":  # TODO: remove when 'ready' event deprecated
        warnings.warn(
            "'ready' event is deprecated. Use 'connect' instead",
            DeprecationWarning,
            stacklevel=2,
        )

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

    if event_type == "ready":  # TODO: remove when 'ready' event deprecated
        warnings.warn(
            "'ready' event is deprecated. Use 'connect' instead",
            DeprecationWarning,
            stacklevel=2,
        )

    def once_decorator(
        func: Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]],
    ) -> Callable[[_T, bot.TSBot, Any], Coroutine[None, None, None]]:
        setattr(func, "__ts_once__", {"event_type": event_type})
        return func

    return once_decorator
