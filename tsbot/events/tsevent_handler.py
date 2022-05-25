from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.events.tsevent import TSEvent
    from tsbot.plugin import TSPlugin
    from tsbot.typealiases import TEventHandler, TPluginEventHandler


class TSEventHandler:
    __slots__ = "event", "handler", "plugin_instance"

    def __init__(
        self,
        event: str,
        handler: TEventHandler | TPluginEventHandler,
        plugin_instance: TSPlugin | None = None,
    ) -> None:
        self.event = event
        self.handler = handler
        self.plugin_instance = plugin_instance

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(event={self.event!r}, "
            f"handler={self.handler.__qualname__!r}, "
            f"plugin={None if not self.plugin_instance else self.plugin_instance.__class__.__qualname__!r}"
            ")"
        )

    async def run(self, bot: TSBot, event: TSEvent) -> None:
        event_args = (bot, event)

        if self.plugin_instance:
            event_args = (self.plugin_instance, *event_args)

        await self.handler(*event_args)

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)
