from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from tsbot.event_handler import EventHanlder, TSEvent, TSEventHandler
from tsbot.plugin import TSPlugin

logger = logging.getLogger(__name__)


T_CommandHandler = Callable[..., Coroutine[dict[str, Any], Any, None]]


@dataclass
class TSCommand:
    commands: tuple[str, ...]
    handler: T_CommandHandler
    plugin: TSPlugin | None = None


class CommandHandler:
    def __init__(self, event_handler: EventHanlder, invoker: str = "!") -> None:
        self.event_handler = event_handler

        self.invoker = invoker

        self.commands: dict[str, TSCommand] = {}

    def register_command(self, command: TSCommand):

        # Check if no commands have been registered, register command handler as event handler
        if not self.commands:
            event_handler = TSEventHandler("textmessage", self._handle_command_event)
            self.event_handler.register_event_handler(event_handler)

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
