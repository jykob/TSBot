from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tsbot import enums, exceptions

if TYPE_CHECKING:
    from tsbot import bot, commands, events


logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, invoker: str = "!") -> None:
        self.invoker = invoker
        self.commands: dict[str, commands.TSCommand] = {}

    def register_command(self, command: commands.TSCommand) -> None:

        for command_name in command.commands:
            self.commands[command_name] = command

        logger.debug(f"Registered '{', '.join(command.commands)}' command to execute {command.handler.__qualname__!r}")

    async def handle_command_event(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        """Logic to handle commands"""

        # If sender is the bot, return
        if event.ctx.get("invokeruid") == bot.uid:
            return

        msg = event.ctx.get("msg", "").strip()
        target_mode = enums.TextMessageTargetMode(int(event.ctx.get("targetmode", 0)))

        # Test if message in channel or server chat and starts with the invoker
        if target_mode in (enums.TextMessageTargetMode.CHANNEL, enums.TextMessageTargetMode.SERVER):
            if not msg.startswith(self.invoker):
                return

        # Remove invoker from the beginning
        msg = msg.removeprefix(self.invoker)

        command, _, args = msg.partition(" ")
        command_handler = self.commands.get(command)

        if not command_handler:
            return

        # Create new context dict with useful entries
        ctx = {"command": command, "raw_args": args} | event.ctx

        logger.debug("%r executed command %r -> %r", event.ctx["invokername"], command, args)

        try:
            await command_handler.run(bot, ctx, args)

        except TypeError:
            await bot.respond(event.ctx, command_handler.usage)

        except exceptions.TSCommandError as e:
            bot.emit(
                event_name="command_error",
                ctx={"exception": type(e).__name__, "exception_msg": str(e)} | ctx,
            )

        except exceptions.TSPermissionError as e:
            bot.emit(
                event_name="permission_error",
                ctx={"exception": type(e).__name__, "exception_msg": str(e)} | ctx,
            )
