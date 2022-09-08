from __future__ import annotations

from typing import Awaitable, Callable, Coroutine, TypeAlias

from tsbot import bot, events, plugin

TCtx: TypeAlias = dict[str, str]

TCommandHandler: TypeAlias = Callable[[bot.TSBot, TCtx], Awaitable[None]]
TPluginCommandHandler: TypeAlias = Callable[[plugin.TSPlugin, bot.TSBot, TCtx], Awaitable[None]]

TEventHandler: TypeAlias = Callable[[bot.TSBot, events.TSEvent], Awaitable[None]]
TPluginEventHandler: TypeAlias = Callable[[plugin.TSPlugin, bot.TSBot, events.TSEvent], Awaitable[None]]

TBackgroundTask: TypeAlias = Callable[[bot.TSBot], Coroutine[None, None, None]]
