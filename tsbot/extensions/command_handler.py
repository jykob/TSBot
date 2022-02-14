from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine


from tsbot.enums import TextMessageTargetMode
from tsbot.exceptions import TSCommandException, TSPermissionError
from tsbot.extensions.event_handler import TSEvent
from tsbot.extensions.extension import Extension

if TYPE_CHECKING:
    from tsbot.bot import TSBotBase
    from tsbot.plugin import TSPlugin


logger = logging.getLogger(__name__)


T_CommandHandler = Callable[..., Coroutine[dict[str, str], Any, None]]


class TSCommand:
    __slots__ = ["commands", "handler", "plugin_instance"]

    def __init__(
        self, commands: tuple[str, ...], handler: T_CommandHandler, plugin_instance: TSPlugin | None = None
    ) -> None:
        self.commands = commands
        self.handler = handler
        self.plugin_instance = plugin_instance

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(commands={self.commands!r}, "
            f"handler={self.handler.__name__!r}, "
            f"plugin={None if not self.plugin_instance else self.plugin_instance.__class__.__name__!r})"
        )

    async def run(self, ctx: dict[str, str], *args: Any, **kwargs: Any) -> None:
        if self.plugin_instance:
            await self.handler(self.plugin_instance, ctx, args, kwargs)
        else:
            await self.handler(ctx, args, kwargs)


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
            f"Registered '{', '.join(command.commands)}' command to execute {command.handler.__name__!r}"
            f"""{f" from {command.plugin_instance.__class__.__name__!r}" if command.plugin_instance else ''}"""
        )

    async def _handle_command_event(self, event: TSEvent) -> None:
        """
        Logic to handle commands
        """

        # TODO: Check that message wasn't sent by the bot
        # If sender is the bot, return:
        # if event.ctx.get("invokeruid") in (None, self.info.unique_id):
        #     return

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

        command, args, kwargs = parse_command(msg)

        # inject usefull information into ctx
        event.ctx["command"] = command
        event.ctx["invoker_removed"] = msg[len(f"{command} ") :]

        command_handler = self.commands.get(command)

        if not command_handler:
            return

        logger.debug(f"{event.ctx.get('invokername')} executed command {command}({args!r}, {kwargs!r})")

        try:
            await command_handler.run(event.ctx, *args, **kwargs)

        except TSCommandException as e:
            self.parent.emit(TSEvent(event="command_error", msg=f"{str(e)}", ctx=event.ctx))

        except TSPermissionError as e:
            self.parent.emit(TSEvent(event="permission_error", msg=f"{str(e)}", ctx=event.ctx))

        except Exception as e:
            logger.exception(f"{e.__class__.__qualname__} while running {command_handler.handler.__name__!r}: {e}")
            raise


def parse_command(msg: str) -> tuple[str, tuple[str, ...], dict[str, str]]:
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
