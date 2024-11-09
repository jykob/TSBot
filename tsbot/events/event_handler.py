from __future__ import annotations

from collections.abc import Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from tsbot import bot, events


class TEventHandler(Protocol):
    def __call__(self, bot: bot.TSBot, ctx: Any, /) -> Coroutine[None, None, None]: ...


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: TEventHandler

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event.ctx)


@dataclass(slots=True)
class TSEventOnceHandler(TSEventHandler):
    event_handler: events.EventHandler

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        self.event_handler.remove_event_handler(self)
        await self.handler(bot, event.ctx)
