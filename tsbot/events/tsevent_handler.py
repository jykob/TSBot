from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsbot import bot, events, typealiases


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: typealiases.TEventHandler

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event)
