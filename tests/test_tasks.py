from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from tsbot import bot, tasks


@pytest_asyncio.fixture  # type: ignore
async def task_manager():
    handler = tasks.TaskManager()
    try:
        yield handler
    finally:
        await handler.close()


@pytest.fixture
def running_task_manager(task_manager: tasks.TaskManager, mock_bot: bot.TSBot):
    task_manager.start(mock_bot)
    return task_manager


@pytest.fixture
def tstask():
    async def task(bot: bot.TSBot) -> None:
        while True:
            await asyncio.sleep(0)

    return tasks.TSTask(task)  # type: ignore


@pytest.mark.asyncio
async def test_registered_task_has_remove_callback(
    running_task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_task_manager.register_task(mock_bot, tstask)
    assert tstask.task and tstask.task._callbacks


def test_register_task_on_not_started_handler(
    task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    task_manager.register_task(mock_bot, tstask)
    assert tstask.task is None


@pytest.mark.asyncio
async def test_removing_task_cancels_task(
    running_task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_task_manager.register_task(mock_bot, tstask)
    running_task_manager.remove_task(tstask)

    assert tstask.task
    with pytest.raises(asyncio.CancelledError):
        await tstask.task


@pytest.mark.asyncio
async def test_register_task_on_not_started_handler_start(
    task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    task_manager.register_task(mock_bot, tstask)
    assert tstask.task is None

    task_manager.start(mock_bot)
    assert tstask.task


@pytest.mark.asyncio
async def test_close_finishes_all_tasks(
    running_task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_task_manager.register_task(mock_bot, tstask)
    await running_task_manager.close()
    assert running_task_manager.empty is True


@pytest.mark.asyncio
async def test_empty_means_empty(
    running_task_manager: tasks.TaskManager, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    assert running_task_manager.empty is True
    running_task_manager.register_task(mock_bot, tstask)
    assert running_task_manager.empty is False
