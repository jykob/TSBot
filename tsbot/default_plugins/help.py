from __future__ import annotations

import inspect
import itertools
from typing import TYPE_CHECKING

from tsbot import exceptions, plugin

if TYPE_CHECKING:
    from tsbot import bot, commands, context


class Help(plugin.TSPlugin):
    @plugin.command("help", help_text="Prints out the help text of a given command and usage")
    async def help_command(self, bot: bot.TSBot, ctx: context.TSCtx, command: str) -> None:
        command_handler = bot.get_command_handler(command)

        if not command_handler or command_handler.hidden:
            raise exceptions.TSCommandError("Command not found")

        response_text = "\n"

        if help_text := command_handler.help_text:
            response_text += f"{help_text}\n"

        if usage := self.command_usage(command_handler):
            response_text += f"{usage}"

        await bot.respond(ctx, response_text)

    @staticmethod
    def command_usage(command: commands.TSCommand) -> str:
        usage: list[str] = []

        for param in itertools.islice(command.call_signature.parameters.values(), 2, None):
            match param.kind:
                case inspect.Parameter.VAR_POSITIONAL:
                    usage.append(f"[{param.name!r}, ...]")
                case inspect.Parameter.KEYWORD_ONLY:
                    usage.append(
                        f"-{param.name} {'[!]' if param.default is param.empty else '[?]'}"
                        f"{f' ({param.default!r})' if param.default not in (param.empty, None) else ''}"
                    )
                case _:
                    usage.append(
                        f"{param.name!r}"
                        f"""{f" ({param.default or '?'!r})" if param.default is not param.empty else ''}"""
                    )

        return f"Usage: {' | '.join(command.commands)} {' '.join(usage)}"
