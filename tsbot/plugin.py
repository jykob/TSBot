from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot import commands, events

if TYPE_CHECKING:
    from tsbot import typealiases


class TSPlugin:
    """Base class for plugins"""


def command(
    *command: str,
    help_text: str | None = None,
    raw: bool = False,
    hidden: bool = False,
) -> commands.TSCommand:
    """Decorator to register coroutines on commands"""

    def command_decorator(func: typealiases.TCommandHandler) -> commands.TSCommand:
        return commands.TSCommand(command, func, help_text=help_text, raw=raw, hidden=hidden)

    return command_decorator  # type: ignore


def on(event_type: str) -> events.TSEventHandler:
    """Decorator to register coroutines on events"""

    def event_decorator(func: typealiases.TEventHandler) -> events.TSEventHandler:
        return events.TSEventHandler(event_type, func)

    return event_decorator  # type: ignore
