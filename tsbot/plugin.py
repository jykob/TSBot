from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Concatenate, ParamSpec, TypeVar, TypedDict

from tsbot import events


if TYPE_CHECKING:
    from tsbot import typealiases, bot

    T = TypeVar("T", bound="TSPlugin")
    P = ParamSpec("P")


class TSPlugin:
    """Base class for plugins"""


class PluginCommandArgs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: list[Callable[..., Awaitable[None]]]


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: list[Callable[..., Awaitable[None]]] | None = None,
):
    """Decorator to register coroutines on commands"""

    def command_decorator(
        func: Callable[Concatenate[T, bot.TSBot, typealiases.TCtx, P], Awaitable[None]]
    ) -> Callable[Concatenate[T, bot.TSBot, typealiases.TCtx, P], Awaitable[None]]:
        func.__ts_command__ = PluginCommandArgs(  # type: ignore
            command=command, help_text=help_text, raw=raw, hidden=hidden, checks=checks or []
        )
        return func

    return command_decorator


def on(event_type: str):
    """Decorator to register coroutines on events"""

    def event_decorator(
        func: Callable[[T, bot.TSBot, events.TSEvent], Awaitable[None]]
    ) -> Callable[[T, bot.TSBot, events.TSEvent], Awaitable[None]]:
        func.__ts_event__ = event_type  # type: ignore
        return func

    return event_decorator
