from __future__ import annotations

import asyncio
import inspect
import itertools
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeAlias

from tsbot import plugin
from tsbot.enums import TextMessageTargetMode
from tsbot.exceptions import TSCommandError, TSPermissionError
from tsbot.extensions import events, extension

if TYPE_CHECKING:
    from tsbot.bot import TSBot


T_CommandHandler: TypeAlias = Callable[..., Coroutine[None, None, None]]


logger = logging.getLogger(__name__)


class TSCommand:
    def __init__(
        self,
        commands: tuple[str, ...],
        handler: T_CommandHandler,
        *,
        help_text: str | None = None,
        raw: bool = False,
        hidden: bool = False,
    ) -> None:
        self.commands = commands
        self.handler = handler

        self.help_text = help_text
        self.raw = raw
        self.hidden = hidden

        self.plugin_instance: plugin.TSPlugin | None = None
        self.checks: list[T_CommandHandler] = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(commands={self.commands!r}, "
            f"handler={self.handler.__qualname__!r}, "
            f"plugin={self.plugin_instance.__class__.__qualname__ if self.plugin_instance else None!r}"
            ")"
        )

    def add_check(self, func: T_CommandHandler) -> None:
        self.checks.append(func)

    @property
    def call_signature(self) -> tuple[inspect.Parameter, ...]:
        signature = inspect.signature(self.handler)
        params_to_discard = 3 if self.plugin_instance else 2

        return tuple(itertools.islice(signature.parameters.values(), params_to_discard, None))

    @property
    def usage(self) -> str:
        usage: list[str] = []

        for param in self.call_signature:
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                usage.append(f"[{param.name!r}, ...]")

            elif param.kind is inspect.Parameter.KEYWORD_ONLY:
                usage.append(
                    f"-{param.name} {'[!]' if param.default is param.empty else '[?]'}"
                    f"{f' ({param.default!r})' if param.default not in (param.empty, None) else ''}"
                )

            else:
                usage.append(
                    f"{param.name!r}"
                    f"""{f" ({param.default or '?'!r})" if param.default is not param.empty else ''}"""
                )

        return f"Usage: {' | '.join(self.commands)}  {' '.join(usage)}"

    async def run_checks(self, bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str):
        done, pending = await asyncio.wait(
            [check(bot, ctx, *args, **kwargs) for check in self.checks],
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for pending_task in pending:
            pending_task.cancel()

        for done_task in done:
            if exception := done_task.exception():
                raise exception

    async def run(self, bot: TSBot, ctx: dict[str, str], msg: str) -> None:

        if self.raw:
            args, kwargs = (msg,), {}
        else:
            args, kwargs = _parse_args_kwargs(msg)

        if self.checks:
            await self.run_checks(bot, ctx, *args, **kwargs)

        command_args = (bot, ctx)
        if self.plugin_instance:
            command_args = (self.plugin_instance, *command_args)

        await self.handler(*command_args, *args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)


class CommandHandler(extension.Extension):
    def __init__(self, parent: TSBot, invoker: str = "!") -> None:
        super().__init__(parent)

        self.commands: dict[str, TSCommand] = {}

    def register_command(self, command: TSCommand):

        for command_name in command.commands:
            self.commands[command_name] = command

        logger.debug(f"Registered '{', '.join(command.commands)}' command to execute {command.handler.__qualname__!r}")

    async def _handle_command_event(self, bot: TSBot, event: events.TSEvent) -> None:
        """Logic to handle commands"""

        # If sender is the bot, return:
        if event.ctx.get("invokeruid") in (None, self.parent.bot_info.unique_identifier):
            return

        msg = event.ctx.get("msg", "").strip()
        target_mode = int(event.ctx.get("targetmode", 0))

        # Test if message in channel or server chat and starts with the invoker
        # If these conditions are met, omit the invoker from the beginning
        if target_mode in (TextMessageTargetMode.CHANNEL, TextMessageTargetMode.SERVER):
            if not msg.startswith(bot.invoker):
                return
            msg = msg.removeprefix(bot.invoker)

        # Check if DM and if msg starts with invoker, omit it
        elif target_mode == TextMessageTargetMode.CLIENT:
            if msg.startswith(bot.invoker):
                msg = msg.removeprefix(bot.invoker)

        command: str
        msg: str

        command, msg = (v or d for v, d in itertools.zip_longest(msg.split(" ", maxsplit=1), ("", "")))
        command_handler = self.commands.get(command)

        if not command_handler:
            return

        # inject usefull information into ctx
        event.ctx["command"] = command
        event.ctx["raw_msg"] = msg

        logger.debug("%s executed command %s(%r)", event.ctx["invokername"], command, msg)

        try:
            await command_handler.run(bot, event.ctx, msg)

        except TypeError:
            await bot.respond(event.ctx, command_handler.usage)

        except TSCommandError as e:
            bot.emit(events.TSEvent(event="command_error", msg=f"{str(e)}", ctx=event.ctx))

        except TSPermissionError as e:
            bot.emit(events.TSEvent(event="permission_error", msg=f"{str(e)}", ctx=event.ctx))

    async def run(self):
        self.parent.register_event_handler("textmessage", self._handle_command_event)
        self.register_command(TSCommand(("help",), _help_handler, help_text="Print help of a command"))


async def _help_handler(bot: TSBot, ctx: dict[str, str], command: str):
    command_handler = bot.extensions.command_handler.commands.get(command)

    if not command_handler or command_handler.hidden:
        raise TSCommandError("Command not found")

    response_text = "\n"

    if help_text := command_handler.help_text:
        response_text += f"{help_text}\n"

    if usage := command_handler.usage:
        response_text += f" {usage}"

    await bot.respond(ctx, response_text)


def _parse_args_kwargs(msg: str) -> tuple[tuple[str, ...], dict[str, str]]:
    """Parses message in to given command, its arguments and keyword arguments"""
    msg_list = msg.split()

    args: list[str] = []
    kwargs: dict[str, str] = {}

    while msg_list:
        item = msg_list.pop(0)

        if item.startswith("-"):
            key = item.removeprefix("-")
            value = ""
            if len(msg_list) and not msg_list[0].startswith("-"):
                value = msg_list.pop(0)

            kwargs[key] = value
        else:
            args.append(item)

    return tuple(args), kwargs


def add_check(func: T_CommandHandler) -> TSCommand:
    def check_decorator(command_handler: TSCommand) -> TSCommand:
        command_handler.add_check(func)
        return command_handler

    return check_decorator  # type: ignore
