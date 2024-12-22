from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import override

if TYPE_CHECKING:
    from tsbot import bot, events

_TC = TypeVar("_TC", contravariant=True)


EventHandler = Callable[["bot.TSBot", _TC], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: EventHandler[Any]

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event.ctx)


@dataclass(slots=True)
class TSEventOnceHandler(TSEventHandler):
    remove_event_handler_func: Callable[[TSEventHandler], None]
    _has_run: bool = False

    @override
    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        if self._has_run:
            return

        self._has_run = True
        self.remove_event_handler_func(self)

        await self.handler(bot, event.ctx)
