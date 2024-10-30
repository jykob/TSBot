from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Final

import pytest

from tsbot import commands, context, exceptions

if TYPE_CHECKING:
    from tsbot import bot, context

# pyright: reportPrivateUsage=false


async def noop(bot: bot.TSBot, ctx: context.TSCtx): ...
async def noop2(bot: bot.TSBot, ctx: context.TSCtx, b: str): ...


INVOKER: Final = "!"
COMMANDS: Final = (commands.TSCommand(("a",), noop),)
COMMANDS_WITH_ARGS: Final = (commands.TSCommand(("b",), noop2),)


@pytest.fixture
def command_handler():
    return commands.CommandHandler(INVOKER)


@pytest.fixture
def command_handler_with_commands(command_handler: commands.CommandHandler):
    for command in itertools.chain(COMMANDS, COMMANDS_WITH_ARGS):
        command_handler._commands.update((c, command) for c in command.commands)
    return command_handler


def test_register_command(command_handler: commands.CommandHandler):
    command = COMMANDS[0]
    assert not command_handler.get_command(command.commands[0])
    command_handler.register_command(command)
    assert command_handler.get_command(command.commands[0])


def test_remove_command(command_handler_with_commands: commands.CommandHandler):
    command = command_handler_with_commands.get_command(COMMANDS[0].commands[0])
    assert command

    command_handler_with_commands.remove_command(command)
    assert not command_handler_with_commands.get_command(command.commands[0])


@pytest.mark.asyncio
async def test_command_handling(command_handler_with_commands: commands.CommandHandler):
    pass


@pytest.mark.asyncio
async def test_argument_passing(command_handler_with_commands: commands.CommandHandler):
    pass


@pytest.mark.asyncio
async def test_checks(command_handler_with_commands: commands.CommandHandler):
    pass


@pytest.mark.asyncio
async def test_checks_failing(command_handler_with_commands: commands.CommandHandler):
    pass


@pytest.mark.parametrize(
    ("exception", "event_name"),
    (
        pytest.param(
            exceptions.TSCommandError(),
            "command_error",
            id="test_command_error",
        ),
        pytest.param(
            exceptions.TSPermissionError(),
            "permission_error",
            id="test_permission_error",
        ),
        pytest.param(
            exceptions.TSInvalidParameterError(),
            "parameter_error",
            id="test_invalid_call_error",
        ),
    ),
)
@pytest.mark.asyncio
async def test_exceptions_emit_events(
    command_handler: commands.CommandHandler,
    mock_bot: bot.TSBot,
    exception: exceptions.TSException,
    event_name: str,
):
    async def handler(bot: bot.TSBot, ctx: context.TSCtx):
        raise exception

    command_handler.register_command(commands.TSCommand(("a",), handler))

    await command_handler.handle_command_event(
        mock_bot, context.TSCtx({"targetmode": "1", "msg": "a", "invokername": "TestAccount"})
    )

    assert mock_bot.emit.call_args[0][0] == event_name  # type: ignore
