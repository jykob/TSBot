from __future__ import annotations

from typing import Awaitable, Callable, Coroutine, Protocol, TypeAlias

from tsbot import bot, events


class SupportsStr(Protocol):
    def __str__(self) -> str:
        ...


TCtx: TypeAlias = dict[str, str]

TEventHandler: TypeAlias = Callable[[bot.TSBot, events.TSEvent], Awaitable[None]]
TBackgroundTask: TypeAlias = Callable[[bot.TSBot], Coroutine[None, None, None]]
