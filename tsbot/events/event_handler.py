from __future__ import annotations

from collections.abc import Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from tsbot import bot, events

_TC = TypeVar("_TC", contravariant=True)


class TEventHandler(Protocol[_TC]):
    def __call__(self, bot: bot.TSBot, ctx: _TC, /) -> Coroutine[None, None, None]: ...


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: TEventHandler[Any]

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event.ctx)


@dataclass(slots=True)
class TSEventOnceHandler(TSEventHandler):
    event_manager: events.EventManager

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        self.event_manager.remove_event_handler(self)
        await self.handler(bot, event.ctx)
