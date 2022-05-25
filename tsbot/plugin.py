from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot.commands.tscommand import TSCommand
from tsbot.events.tsevent_handler import TSEventHandler

if TYPE_CHECKING:
    from tsbot.typealiases import TCommandHandler, TEventHandler


class TSPlugin:
    """Base class for plugins"""


def command(*command: str, help_text: str | None = None, raw: bool = False, hidden: bool = False) -> TSCommand:
    """Decorator to register coroutines on commands"""

    def command_decorator(func: TCommandHandler) -> TSCommand:
        return TSCommand(command, func, help_text=help_text, raw=raw, hidden=hidden)

    return command_decorator  # type: ignore


def on(event_type: str) -> TSEventHandler:
    """Decorator to register coroutines on events"""

    def event_decorator(func: TEventHandler) -> TSEventHandler:
        return TSEventHandler(event_type, func)

    return event_decorator  # type: ignore
