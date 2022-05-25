from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Coroutine, TypeAlias

if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.events.tsevent import TSEvent
    from tsbot.plugin import TSPlugin

TCtx: TypeAlias = dict[str, str]

TCommandHandler: TypeAlias = Callable[[TSBot, TCtx], Awaitable[None]]
TPluginCommandHandler: TypeAlias = Callable[[TSPlugin, TSBot, TCtx], Awaitable[None]]

TEventHandler: TypeAlias = Callable[[TSBot, TSEvent], Awaitable[None]]
TPluginEventHandler: TypeAlias = Callable[[TSPlugin, TSBot, TSEvent], Awaitable[None]]

TBackgroundTask: TypeAlias = Callable[..., Coroutine[None, None, None]]
