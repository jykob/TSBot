from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tsbot.extensions.command_handler import TSCommand
from tsbot.extensions.event_handler import TSEventHandler

if TYPE_CHECKING:
    from tsbot.bot import TSBotBase
    from tsbot.extensions.command_handler import T_CommandHandler
    from tsbot.extensions.event_handler import T_EventHandler


class TSPlugin:
    bot: TSBotBase

    @classmethod
    def on(cls, event_type: str):
        """Decorator to register coroutines on events"""

        def event_decorator(func: T_EventHandler) -> TSEventHandler:
            handler = TSEventHandler(event_type, func)
            return handler

        return event_decorator

    @classmethod
    def command(cls, *commands: str):
        """Decorator to register coroutines on commands"""

        def command_decorator(func: T_CommandHandler) -> TSCommand:
            handler = TSCommand(commands, func)
            return handler

        return command_decorator
