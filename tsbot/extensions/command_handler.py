from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from tsbot.extensions.event_handler import TSEvent
from tsbot.extensions.extension import Extension

if TYPE_CHECKING:
    from tsbot.bot import TSBotBase
    from tsbot.plugin import TSPlugin


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

        # If sender is the bot, return:
        if event.ctx.get("invokeruid") in (None, self.info.unique_id):
            return

        msg = event.ctx.get("msg", "").strip()
        target_mode = int(event.ctx.get("targetmode"))

        # Test if message in channel or server chat and starts with the invoker
        # If these conditions are met, omit the invoker from the beginning
        if target_mode in (TextMessageTargetMode.CHANNEL, TextMessageTargetMode.SERVER):
            if not msg.startswith(self.invoker):
                return
            msg = msg[len(self.invoker) :]

        # Check if DM and if msg starts with invoker, omit it
        elif target_mode == TextMessageTargetMode.CLIENT:
            if msg.startswith(self.invoker):
                msg = msg[len(self.invoker) :]

        command, args, kwargs = parse_command(msg)
        event.ctx["command"] = command
        event.ctx["invoker_removed"] = msg[len(f"{command} ") :]

        if command_handler := self.commands.get(command):
            try:
                _logger.debug(f"{event.ctx.get('invokername')} executed command {command}( {args}, {kwargs} )")

                # Check if command is from plugin, inject instance into the call if so
                if instance := self.plugins.get(command_handler.plugin):
                    command_handler(instance, event.ctx, *args, **kwargs)
                else:
                    command_handler(event.ctx, *args, **kwargs)

            except CommandError as e:
                self.emit(TSEvent(event="on_command_error", msg=f"Error: {str(e)}", ctx=event.ctx))

            except PermissionError as e:
                self.emit(TSEvent(event="on_permission_error", msg=f"Error: {str(e)}", ctx=event.ctx))

            except Exception as e:
                _logger.exception(
                    f"Exception in command handler '{command_handler.__name__}': {e}\n"
                    f"Message that caused the Exception: '{event.msg}'"
                )
