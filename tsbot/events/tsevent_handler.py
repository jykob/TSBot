from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Coroutine


if TYPE_CHECKING:
    from tsbot import bot, events


TEventH = Callable[["bot.TSBot", "events.TSEvent"], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: TEventH

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event)


@dataclass(slots=True)
class TSEventOnceHandler(TSEventHandler):
    event_handler: events.EventHanlder

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        self.event_handler.remove_event_handler(self)
        await self.handler(bot, event)
