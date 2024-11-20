from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot import context, enums, exceptions, logging, parsers

if TYPE_CHECKING:
    from tsbot import bot, commands


logger = logging.get_logger(__name__)


_ERROR_EVENT_MAP: dict[type[exceptions.TSException], str] = {
    exceptions.TSCommandError: "command_error",
    exceptions.TSPermissionError: "permission_error",
    exceptions.TSInvalidParameterError: "parameter_error",
}


class CommandManager:
    def __init__(self, invoker: str = "!") -> None:
        self.invoker = invoker
        self._commands: dict[str, commands.TSCommand] = {}

    def register_command(self, command: commands.TSCommand) -> None:
        if already_registered := tuple(filter(lambda c: c in self._commands, command.commands)):
            logger.warning(
                "Command %s are already registered and will be overwritten",
                ", ".join(map(repr, already_registered)),
            )

        self._commands.update({c: command for c in command.commands})

        logger.debug(
            "Registered %s command to execute handler %r",
            ", ".join(map(repr, command.commands)),
            getattr(command.handler, "__name__", command.handler),
        )

    def get_command(self, command: str) -> commands.TSCommand | None:
        return self._commands.get(command)

    def remove_command(self, command: commands.TSCommand) -> None:
        for c in command.commands:
            del self._commands[c]

    async def handle_command_event(self, bot: bot.TSBot, ctx: context.TSCtx) -> None:
        """Logic to handle commands"""

        # If sender is the bot, return
        if ctx.get("invokerid") == bot.clid:
            return

        msg = ctx.get("msg", "").strip()
        if not msg:
            return

        target_mode_str = ctx.get("targetmode")
        if target_mode_str is None:
            return

        target_mode = enums.TextMessageTargetMode(target_mode_str)

        # Test if message in channel or server chat and starts with the invoker
        if target_mode in (
            enums.TextMessageTargetMode.CHANNEL,
            enums.TextMessageTargetMode.SERVER,
        ) and not msg.startswith(self.invoker):
            return

        # Remove invoker from the beginning
        msg = msg.removeprefix(self.invoker)

        command, args = parsers.split_ensure_splits(msg, maxsplit=1)
        command_handler = self._commands.get(command)

        if not command_handler:
            return

        # Create new context dict with useful entries
        ctx = context.TSCtx({"command": command, "raw_args": args, **ctx})

        logger.debug("%r executed command %r with args: %r", ctx.get("invokername"), command, args)

        try:
            await command_handler.run(bot, ctx, args)

        except exceptions.TSException as e:
            if error_event := _ERROR_EVENT_MAP.get(type(e)):
                bot.emit(error_event, {"exception": str(e), **ctx})
                return

            raise
