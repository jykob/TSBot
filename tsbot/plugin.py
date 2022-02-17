from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot.extensions.commands import TSCommand
from tsbot.extensions.events import TSEventHandler

if TYPE_CHECKING:
    from tsbot.extensions.commands import T_CommandHandler
    from tsbot.extensions.events import T_EventHandler


class TSPlugin:
    """Base class for plugins"""


def command(*commands: str):
    """Decorator to register coroutines on commands"""

    def command_decorator(func: T_CommandHandler) -> TSCommand:
        return TSCommand(commands, func)

    return command_decorator


def on(event_type: str):
    """Decorator to register coroutines on events"""

    def event_decorator(func: T_EventHandler) -> TSEventHandler:
        return TSEventHandler(event_type, func)

    return event_decorator
