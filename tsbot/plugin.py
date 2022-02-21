from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot.extensions import commands
from tsbot.extensions import events

if TYPE_CHECKING:
    from tsbot.extensions.commands import T_CommandHandler
    from tsbot.extensions.events import T_EventHandler


class TSPlugin:
    """Base class for plugins"""


def command(*command: str, help_text: str | None = None, raw: bool = False):
    """Decorator to register coroutines on commands"""

    def command_decorator(func: T_CommandHandler) -> commands.TSCommand:
        return commands.TSCommand(command, func, help_text, raw)

    return command_decorator


def on(event_type: str):
    """Decorator to register coroutines on events"""

    def event_decorator(func: T_EventHandler) -> events.TSEventHandler:
        return events.TSEventHandler(event_type, func)

    return event_decorator
