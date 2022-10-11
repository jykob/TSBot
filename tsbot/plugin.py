from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Concatenate, Coroutine, ParamSpec, TypedDict, TypeVar

from tsbot import events

if TYPE_CHECKING:
    from tsbot import bot

    T = TypeVar("T", bound="TSPlugin")
    P = ParamSpec("P")


class TSPlugin:
    """Base class for plugins"""


class PluginCommandArgs(TypedDict):
    command: tuple[str, ...]
    help_text: str
    raw: bool
    hidden: bool
    checks: list[Callable[..., Coroutine[None, None, None]]]


def command(
    *command: str,
    help_text: str = "",
    raw: bool = False,
    hidden: bool = False,
    checks: list[Callable[..., Coroutine[None, None, None]]] | None = None,
) -> Callable[
    [Callable[Concatenate[T, bot.TSBot, dict[str, str], P], Coroutine[None, None, None]]],
    Callable[Concatenate[T, bot.TSBot, dict[str, str], P], Coroutine[None, None, None]],
]:
    """Decorator to register coroutines on commands"""

    def command_decorator(
        func: Callable[Concatenate[T, bot.TSBot, dict[str, str], P], Coroutine[None, None, None]]
    ) -> Callable[Concatenate[T, bot.TSBot, dict[str, str], P], Coroutine[None, None, None]]:
        func.__ts_command__ = PluginCommandArgs(  # type: ignore
            command=command, help_text=help_text, raw=raw, hidden=hidden, checks=checks or []
        )
        return func

    return command_decorator


def on(
    event_type: str,
) -> Callable[
    [Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]],
    Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]],
]:
    """Decorator to register coroutines on events"""

    def event_decorator(
        func: Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]
    ) -> Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]:
        func.__ts_event__ = event_type  # type: ignore
        return func

    return event_decorator


def once(
    event_type: str,
) -> Callable[
    [Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]],
    Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]],
]:
    def once_decorator(
        func: Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]
    ) -> Callable[[T, bot.TSBot, events.TSEvent], Coroutine[None, None, None]]:
        func.__ts_once__ = event_type  # type: ignore
        return func

    return once_decorator
