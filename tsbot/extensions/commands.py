from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeAlias

from tsbot.enums import TextMessageTargetMode
from tsbot.exceptions import TSCommandError, TSPermissionError
from tsbot.extensions.events import TSEvent
from tsbot.extensions.extension import Extension

if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.plugin import TSPlugin

    T_CommandHandler: TypeAlias = Callable[..., Coroutine[None, None, None]]


logger = logging.getLogger(__name__)


class TSCommand:
    __slots__ = ["commands", "handler", "plugin_instance", "checks"]

    def __init__(
        self, commands: tuple[str, ...], handler: T_CommandHandler, plugin_instance: TSPlugin | None = None
    ) -> None:
        self.commands = commands
        self.handler = handler
        self.plugin_instance = plugin_instance
        self.checks: list[T_CommandHandler] = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(commands={self.commands!r}, "
            f"handler={self.handler.__qualname__!r}, "
            f"plugin={None if not self.plugin_instance else self.plugin_instance.__class__.__qualname__!r}, "
            f"checks=[{', '.join(check.__qualname__ for check in self.checks)}]"
            ")"
        )

    def add_check(self, func: T_CommandHandler) -> None:
        self.checks.append(func)

    async def run(self, bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str) -> None:
        if self.checks:
            done, pending = await asyncio.wait(
                [check(bot, ctx, *args, **kwargs) for check in self.checks],
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for pending_task in pending:
                pending_task.cancel()

            for done_task in done:
                if exception := done_task.exception():
                    raise exception

        if self.plugin_instance:
            await self.handler(self.plugin_instance, bot, ctx, *args, **kwargs)
        else:
            await self.handler(bot, ctx, *args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)


class CommandHandler(Extension):
    def __init__(self, parent: TSBot, invoker: str = "!") -> None:
        super().__init__(parent)

        self.invoker = invoker

        self.commands: dict[str, TSCommand] = {}

    def register_command(self, command: TSCommand):

        # Check if no commands have been registered, register command handler as event handler
        if not self.commands:
            self.parent.register_event_handler("textmessage", self._handle_command_event)

        for command_name in command.commands:
            self.commands[command_name] = command

        logger.debug(f"Registered '{', '.join(command.commands)}' command to execute {command.handler.__qualname__!r}")

    async def _handle_command_event(self, bot: TSBot, event: TSEvent) -> None:
        """
        Logic to handle commands
        """

        # If sender is the bot, return:
        if event.ctx.get("invokeruid") in (None, self.parent.bot_info.unique_identifier):
            return

        msg = event.ctx.get("msg", "").strip()
        target_mode = int(event.ctx.get("targetmode", 0))

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

        command, args, kwargs = _parse_command(msg)

        # inject usefull information into ctx
        event.ctx["command"] = command
        event.ctx["invoker_removed"] = msg[len(f"{command} ") :]

        command_handler = self.commands.get(command)

        if not command_handler:
            return

        logger.debug(f"%s executed command %s(%r, %r)", event.ctx.get("invokername"), command, args, kwargs)

        try:
            await command_handler.run(bot, event.ctx, *args, **kwargs)

        except TSCommandError as e:
            self.parent.emit(TSEvent(event="command_error", msg=f"{str(e)}", ctx=event.ctx))

        except TSPermissionError as e:
            self.parent.emit(TSEvent(event="permission_error", msg=f"{str(e)}", ctx=event.ctx))

        except Exception as e:
            logger.exception(
                f"%s while running %r: %s", e.__class__.__qualname__, command_handler.handler.__qualname__, e
            )
            raise


def _parse_command(msg: str) -> tuple[str, tuple[str, ...], dict[str, str]]:
    """
    Parses message in to given command, its arguments and keyword arguments
    """
    msg_list = msg.split(" ")
    cmd = msg_list.pop(0).lower()
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

    return cmd, tuple(args), kwargs


def add_check(func: T_CommandHandler) -> TSCommand:
    def check_decorator(command_handler: TSCommand) -> TSCommand:
        command_handler.add_check(func)
        return command_handler

    return check_decorator
