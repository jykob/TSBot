from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot.extensions.commands import TSCommand
from tsbot.extensions.events import TSEventHandler

if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.extensions.commands import T_CommandHandler
    from tsbot.extensions.events import T_EventHandler


class TSPlugin:
    """Base class for plugins"""

    bot: TSBot


def command(*commands: str):
    """Decorator to register coroutines on commands"""

    def command_decorator(func: T_CommandHandler) -> TSCommand:
        handler = TSCommand(commands, func)
        return handler

    return command_decorator


def on(event_type: str):
    """Decorator to register coroutines on events"""

    def event_decorator(func: T_EventHandler) -> TSEventHandler:
        handler = TSEventHandler(event_type, func)
        return handler

    return event_decorator
