from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsbot import bot, events, plugin, typealiases


class TSEventHandler:
    __slots__ = "event", "handler", "plugin_instance"

    def __init__(self, event: str, handler: typealiases.TEventHandler | typealiases.TPluginEventHandler) -> None:
        self.event = event
        self.handler = handler
        self.plugin_instance: plugin.TSPlugin | None = None

    async def run(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        event_args = (bot, event) if not self.plugin_instance else (self.plugin_instance, bot, event)

        await self.handler(*event_args)  # type: ignore

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(event={self.event!r}, handler={self.handler.__qualname__!r})"
