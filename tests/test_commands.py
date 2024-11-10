from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Final
from unittest import mock

import pytest

from tsbot import commands, context, exceptions

if TYPE_CHECKING:
    from tsbot import bot

# pyright: reportPrivateUsage=false


async def noop1(bot: bot.TSBot, ctx: context.TSCtx): ...
async def noop2(bot: bot.TSBot, ctx: context.TSCtx, arg: str): ...


INVOKER: Final = "!"


@pytest.fixture
def command():
    return commands.TSCommand(("a",), noop1)


@pytest.fixture
def command_with_args():
    return commands.TSCommand(("b",), noop2)


@pytest.fixture
def command_with_raw_args():
    return commands.TSCommand(("c",), noop2, raw=True)


@pytest.fixture
def all_commands(
    command: commands.TSCommand,
    command_with_args: commands.TSCommand,
    command_with_raw_args: commands.TSCommand,
):
    return (command, command_with_args, command_with_raw_args)


@pytest.fixture
def command_manager():
    return commands.CommandManager(INVOKER)


@pytest.fixture
def command_manager_with_commands(
    command_manager: commands.CommandManager, all_commands: Sequence[commands.TSCommand]
):
    for command in all_commands:
        command_manager._commands.update((c, command) for c in command.commands)
    return command_manager


def test_register_command(command_manager: commands.CommandManager, command: commands.TSCommand):
    assert command_manager.get_command(command.commands[0]) is None
    command_manager.register_command(command)
    assert command_manager.get_command(command.commands[0]) is command


def test_remove_command(
    command_manager_with_commands: commands.CommandManager, command: commands.TSCommand
):
    assert command_manager_with_commands.get_command(command.commands[0]) is command
    command_manager_with_commands.remove_command(command)
    assert command_manager_with_commands.get_command(command.commands[0]) is None


@pytest.mark.asyncio
async def test_command_handling(
    monkeypatch: pytest.MonkeyPatch,
    command_manager: commands.CommandManager,
    command: commands.TSCommand,
    mock_bot: bot.TSBot,
):
    mock_handler = mock.AsyncMock()
    monkeypatch.setattr(command, "handler", mock_handler)

    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command.commands[0]}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_handler.assert_awaited_once_with(mock_bot, mock.ANY)


@pytest.mark.asyncio
async def test_argument_passing(
    monkeypatch: pytest.MonkeyPatch,
    command_manager: commands.CommandManager,
    command_with_args: commands.TSCommand,
    mock_bot: bot.TSBot,
):
    mock_handler = mock.AsyncMock()
    monkeypatch.setattr(command_with_args, "handler", mock_handler)

    command_args = "test"
    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command_with_args.commands[0]} {command_args}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command_with_args)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_handler.assert_awaited_once_with(mock_bot, mock.ANY, command_args)


@pytest.mark.asyncio
async def test_raw_argument_passing(
    monkeypatch: pytest.MonkeyPatch,
    command_manager: commands.CommandManager,
    command_with_raw_args: commands.TSCommand,
    mock_bot: bot.TSBot,
):
    mock_handler = mock.AsyncMock()
    monkeypatch.setattr(command_with_raw_args, "handler", mock_handler)

    command_args = "long test argument"
    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command_with_raw_args.commands[0]} {command_args}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command_with_raw_args)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_handler.assert_awaited_once_with(mock_bot, mock.ANY, command_args)


@pytest.mark.asyncio
async def test_checks(
    monkeypatch: pytest.MonkeyPatch,
    command_manager: commands.CommandManager,
    command: commands.TSCommand,
    mock_bot: bot.TSBot,
):
    mock_handler = mock.AsyncMock()
    monkeypatch.setattr(command, "handler", mock_handler)

    mock_check = mock.AsyncMock()
    command.checks = (mock_check,)

    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command.commands[0]}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_handler.assert_awaited_once()
    mock_check.assert_awaited_once()


@pytest.mark.asyncio
async def test_checks_failing(
    monkeypatch: pytest.MonkeyPatch,
    command_manager: commands.CommandManager,
    command: commands.TSCommand,
    mock_bot: bot.TSBot,
):
    async def check(bot: bot.TSBot, ctx: context.TSCtx, *args: str, **kwargs: str) -> None:
        raise exceptions.TSPermissionError("Test exception")

    mock_handler = mock.AsyncMock()
    monkeypatch.setattr(command, "handler", mock_handler)

    command.checks = (check,)

    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command.commands[0]}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_handler.assert_not_called()


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
    command_manager: commands.CommandManager,
    mock_bot: bot.TSBot,
    exception: exceptions.TSException,
    event_name: str,
):
    async def handler(bot: bot.TSBot, ctx: context.TSCtx):
        raise exception

    command = commands.TSCommand(("a",), handler)
    command_context = context.TSCtx(
        {
            "targetmode": "3",
            "msg": f"{INVOKER}{command.commands[0]}",
            "invokerid": "3",
            "invokername": "TestAccount",
        }
    )

    command_manager.register_command(command)
    await command_manager.handle_command_event(mock_bot, command_context)

    mock_bot.emit.assert_called_with(event_name, mock.ANY)  # type: ignore
