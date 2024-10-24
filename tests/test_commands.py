from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Final

import pytest

from tsbot import commands

if TYPE_CHECKING:
    from tsbot import bot, context

INVOKER: Final = "!"


async def noop(bot: bot.TSBot, ctx: context.TSCtx): ...


async def noop2(bot: bot.TSBot, ctx: context.TSCtx, d: str): ...


COMMANDS: Final = (
    commands.TSCommand(("a",), noop),
    commands.TSCommand(("b",), noop),
    commands.TSCommand(("c",), noop),
)

COMMANDS_WITH_ARGS: Final = (commands.TSCommand(("d",), noop2),)


@pytest.fixture
def command_handler():
    return commands.CommandHandler(INVOKER)


@pytest.fixture
def command_handler_with_commands(command_handler: commands.CommandHandler):
    for command in itertools.chain(COMMANDS, COMMANDS_WITH_ARGS):
        command_handler.register_command(command)
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
async def test_exceptions_throwing(command_handler_with_commands: commands.CommandHandler):
    pass
