from __future__ import annotations

import inspect
import itertools
from typing import TYPE_CHECKING, Protocol

import tsformatter as tsf

from tsbot import exceptions, plugin

if TYPE_CHECKING:
    from tsbot import bot, commands, context


class Formatter(Protocol):
    def format(self, command: commands.TSCommand) -> str: ...


class BriefFormatter(Formatter):
    @staticmethod
    def format_default_value(param: inspect.Parameter) -> str:
        return f"={param.default}" if param.default not in (param.empty, None) else ""

    def format_param(self, param: inspect.Parameter) -> str:
        match param.kind:
            case inspect.Parameter.VAR_POSITIONAL:
                return f"[{tsf.italic(param.name)}, ...]"
            case inspect.Parameter.VAR_KEYWORD:
                return f"[-{tsf.italic(param.name)} value, ...]"
            case inspect.Parameter.KEYWORD_ONLY:
                return (
                    f"-{param.name}"
                    f"""{f" {tsf.underline('value')}" if param.default is param.empty else ''}"""
                    f"{self.format_default_value(param)}"
                )
            case _:
                return (
                    f"{tsf.italic(tsf.underline(param.name) if param.default is param.empty else param.name)}"
                    f"{self.format_default_value(param)}"
                )

    def format(self, command: commands.TSCommand) -> str:
        help_text = f"{command.help_text}\n" if command.help_text else None
        usage_text = f"Usage: {' | '.join(map(tsf.bold, command.commands))}"

        params = tuple(itertools.islice(command.call_signature.parameters.values(), 2, None))
        args_text = f" {'  '.join(map(self.format_param, params))}" if params else None

        return "".join(text for text in (help_text, usage_text, args_text) if text is not None)


class DetailedFormatter(Formatter):
    @staticmethod
    def tabulate(input_str: str) -> str:
        return f"\t{input_str}"

    @staticmethod
    def format_description(param: inspect.Parameter) -> str:
        match param.kind:
            case inspect.Parameter.VAR_POSITIONAL:
                return "any amount of positional arguments"
            case inspect.Parameter.VAR_KEYWORD:
                return "any amount of keyword arguments"
            case _:
                return "{description} argument {default}".format(
                    description=param.kind.description,
                    default=(
                        f"with a default value of {param.default!r}"
                        if param.default is not param.empty
                        else "that has to be specified"
                    ),
                )

    def format_param(self, param: inspect.Parameter, raw: bool = False) -> str:
        description_text = (
            "argument where the rest of the invocation message is passed after the command"
            if raw
            else self.format_description(param)
        )

        return f"{tsf.bold(param.name)}: {description_text}."

    def format(self, command: commands.TSCommand) -> str:
        help_text = f"Help text: {command.help_text}" if command.help_text else None
        command_text = f"Command: {tsf.bold(command.commands[0])}"
        aliases_text = (
            f"Aliases: {', '.join(map(tsf.bold, command.commands[1:]))}"
            if len(command.commands) > 1
            else None
        )

        if params := tuple(itertools.islice(command.call_signature.parameters.values(), 2, None)):
            params = (params[0],) if command.raw else params
            args = (self.format_param(param, command.raw) for param in params)

            args_text = "Arguments:\n{args}".format(args="\n".join(map(self.tabulate, args)))
        else:
            args_text = None

        return "\n{formatted_help}".format(
            formatted_help="\n".join(
                text
                for text in (help_text, command_text, aliases_text, args_text)
                if text is not None
            )
        )


class Help(plugin.TSPlugin):
    def __init__(self) -> None:
        self.formatters: dict[str, Formatter] = {
            "brief": BriefFormatter(),
            "detailed": DetailedFormatter(),
        }

    @plugin.command("help", help_text="Prints out the help text of a given command and usage")
    async def help_command(
        self,
        bot: bot.TSBot,
        ctx: context.TSCtx,
        command: str,
        *,
        detailed: str = "false",
        format: str = "brief",
    ) -> None:
        command_handler = bot.get_command_handler(command)

        if not command_handler or command_handler.hidden:
            raise exceptions.TSCommandError("Command not found")

        formatter = self.formatters.get("detailed" if detailed != "false" else format)

        if not formatter:
            raise exceptions.TSCommandError("Invalid formatter")

        await bot.respond(ctx, formatter.format(command_handler))
