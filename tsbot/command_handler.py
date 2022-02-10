from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from tsbot.event_handler import TSEvent
from tsbot.extension import Extension
from tsbot.plugin import TSPlugin

if TYPE_CHECKING:
    from tsbot.bot import TSBotBase


logger = logging.getLogger(__name__)


T_CommandHandler = Callable[..., Coroutine[dict[str, Any], Any, None]]


@dataclass
class TSCommand:
    commands: tuple[str, ...]
    handler: T_CommandHandler
    plugin: TSPlugin | None = None


class CommandHandler(Extension):
    def __init__(self, parent: TSBotBase, invoker: str = "!") -> None:
        super().__init__(parent)

        self.invoker = invoker

        self.commands: dict[str, TSCommand] = {}

    def register_command(self, command: TSCommand):

        # Check if no commands have been registered, register command handler as event handler
        if not self.commands:
            self.parent.register_event_handler("textmessage", self._handle_command_event)

        for command_name in command.commands:
            self.commands[command_name] = command

        logger.debug(
            f"Registered '{', '.join(command.commands)}' command"
            f"""{f" from '{command.plugin}'" if command.plugin else ''}"""
        )

    async def _handle_command_event(self, event: TSEvent) -> None:
        """
        Logic to handle commands
        """
        # TODO: WRITE

        logger.info("HANDLE COMMAND")
