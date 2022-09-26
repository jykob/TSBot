from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsbot import bot, events, typealiases


class TSEventHandler:
    __slots__ = "event", "handler"

    def __init__(self, event: str, handler: typealiases.TEventHandler) -> None:
        self.event = event
        self.handler = handler

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        await self.handler(bot, event)

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(event={self.event!r}, handler={self.handler.__qualname__!r})"
