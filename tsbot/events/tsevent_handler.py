from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.events.tsevent import TSEvent
    from tsbot.plugin import TSPlugin
    from tsbot.typealiases import TEventHandler, TPluginEventHandler


@dataclass(slots=True)
class TSEventHandler:
    event: str
    handler: TEventHandler | TPluginEventHandler
    plugin_instance: TSPlugin | None = None

    async def run(self, bot: TSBot, event: TSEvent) -> None:
        event_args = (bot, event)

        if self.plugin_instance:
            event_args = (self.plugin_instance, *event_args)

        await self.handler(*event_args)

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)
