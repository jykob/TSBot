from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tsbot import exceptions, plugin

if TYPE_CHECKING:
    from tsbot import bot


logger = logging.getLogger(__name__)


class Help(plugin.TSPlugin):
    @plugin.command("help", help_text="Prints out the help text of a given command and usage")
    async def help_command(self, bot: bot.TSBot, ctx: dict[str, str], command: str) -> None:
        command_handler = bot.command_handler.commands.get(command)

        if not command_handler or command_handler.hidden:
            raise exceptions.TSCommandError("Command not found")

        response_text = "\n"

        if help_text := command_handler.help_text:
            response_text += f"{help_text}\n"

        if usage := command_handler.usage:
            response_text += f"{usage}"

        await bot.respond(ctx, response_text)
